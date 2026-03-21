from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Chapter,DictionaryLookupRecord
import requests
import logging
import base64
import io
from PIL import Image, ImageEnhance
import numpy as np
import json
import re
from langdetect import detect, LangDetectException
from django.core.files.base import ContentFile
from django.db import transaction
from collections import defaultdict
from django.http import HttpResponse
import urllib.parse




logger = logging.getLogger(__name__)

_cv2 = None


def _get_cv2():
    """延迟加载 cv2，避免 migrate / 加载 urls 时在无 libGL 的服务器上 import 失败。"""
    global _cv2
    if _cv2 is None:
        import cv2 as _cv2_mod

        _cv2 = _cv2_mod
    return _cv2


from django.conf import settings
from django.core.cache import cache
import time
from .models import OCRUsageRecord



class OCRBaseAPI(APIView):
    """
    OCR基础API类，提供通用OCR功能
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = []
    _ocr_token_cache_key = "baidu_ocr_access_token"
    _ocr_token_expires_at_key = "baidu_ocr_token_expires_at"

    def _get_access_token(self):
        """获取百度OCR访问令牌，带缓存机制"""
        # 尝试从缓存获取
        token = cache.get(self._ocr_token_cache_key)
        expires_at = cache.get(self._ocr_token_expires_at_key)
        
        if token and expires_at and expires_at > time.time():
            return token
            
        # 重新获取token
        token_url = settings.OCR_CONFIG['BAIDU_OCR']['ACCESS_TOKEN_URL']
        params = {
            'grant_type': 'client_credentials',
            'client_id': settings.OCR_CONFIG['BAIDU_OCR']['API_KEY'],
            'client_secret': settings.OCR_CONFIG['BAIDU_OCR']['SECRET_KEY']
        }
        
        try:
            response = requests.post(token_url, params=params)
            response.raise_for_status()
            token_data = response.json()
            
            # 缓存token (提前5分钟过期)
            expires_in = token_data.get('expires_in', 2592000) - 300
            cache.set(self._ocr_token_cache_key, token_data['access_token'], expires_in)
            cache.set(
                self._ocr_token_expires_at_key, 
                time.time() + expires_in,
                expires_in
            )
            return token_data['access_token']
            
        except Exception as e:
            logger.error(f"获取OCR访问令牌失败: {str(e)}")
            raise Exception("OCR服务不可用")

    def _preprocess_image(self, image_file):
        """
        图片预处理
        1. 自动旋转校正
        2. 对比度增强
        3. 尺寸调整(最大宽度2000px)
        4. 转换为灰度图(可选)
        """
        try:
            # 读取图片
            img = Image.open(io.BytesIO(image_file.read()))
            
            # 自动旋转校正
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif:
                    orientation = exif.get(0x0112)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
            
            # 调整尺寸
            if img.width > 6000:
                ratio = 6000 / img.width
                new_height = int(img.height * ratio)
                img = img.resize((6000, new_height), Image.LANCZOS)
            
            # 增强对比度
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)

            cv2 = _get_cv2()
            # 转换为OpenCV格式进行进一步处理
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # 自适应阈值处理
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 转换回PIL格式
            img = Image.fromarray(img)
            
            # 保存处理后的图片
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=90)
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"图片预处理失败: {str(e)}")
            image_file.seek(0)  # 重置文件指针
            return image_file.read()

    def _call_ocr_service(self, image_file, ocr_type='general', user=None, chapter=None):
        """
        调用OCR服务核心方法
        :param image_file: 图片文件
        :param ocr_type: OCR类型
        :param user: 用户对象
        :param chapter: 章节对象
        :return: OCR识别结果
        """
        try:
            # 图片预处理
            processed_image = self._preprocess_image(image_file)
            
            access_token = self._get_access_token()
            url = f"{settings.OCR_CONFIG['BAIDU_OCR']['OCR_URL']}{ocr_type}_basic"
            
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            params = {
                "image": base64.b64encode(processed_image).decode(),
                "language_type": "CHN_ENG",
                "detect_direction": "true",
                "probability": "true"
            }
            
            response = requests.post(
                url,
                data=params,
                headers=headers,
                params={"access_token": access_token},
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            if 'error_code' in result:
                logger.error(f"OCR识别失败: {result.get('error_msg')}")
                raise Exception(result.get('error_msg', 'OCR识别失败'))
            
            # 记录使用情况
            char_count = sum(len(item['words']) for item in result.get('words_result', []))
            OCRUsageRecord.objects.create(
                user=user,
                chapter=chapter,
                image_size=len(processed_image) // 1024,
                char_count=char_count,
                ocr_type=ocr_type,
                status=True
            )
                
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OCR服务请求失败: {str(e)}")
            raise Exception("OCR服务请求失败，请稍后再试")
        except Exception as e:
            logger.error(f"OCR处理失败: {str(e)}")
            raise

class ChapterImportKnowledgeAPI(OCRBaseAPI):
    """
    章节知识点导入API
    通过OCR识别图片中的知识点并结构化
    """
    def post(self, request, chapter_id):
        chapter = get_object_or_404(Chapter, id=chapter_id)
        image_file = request.FILES.get('image')
        user = request.user if request.user.is_authenticated else None
        
        if not image_file:
            return Response(
                {'error': '未提供图片文件'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. 调用OCR服务
            ocr_result = self._call_ocr_service(
                image_file,
                user=user,
                chapter=chapter
            )
                       
            return Response({
                'chapter_id': chapter.id,
                'success': True,
                'ocr_result': ocr_result
            })
            
        except Exception as e:
            logger.error(f"导入知识点失败: {str(e)}")
            return Response(
                {'error': f'处理失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AIKnowledgeAPI(APIView):
    """
    DeepSeek AI知识问答API (使用官方SDK)
    """
    permission_classes = []
    
    def post(self, request):
        from django.conf import settings
        from openai import OpenAI
        import logging
        from openai import APIConnectionError, RateLimitError, APIStatusError
        
        logger = logging.getLogger(__name__)
        
        # 验证请求数据
        question = request.data.get('question')
        if not question:
            return Response(
                {'error': '问题内容不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 初始化DeepSeek客户端
            client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
            
            # 调用DeepSeek API
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个专业的计算机考研知识助手，请用中文回答用户问题"
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                stream=False
            )
            
            # 获取回答内容
            answer = response.choices[0].message.content
            if not answer:
                raise ValueError("AI返回内容为空")
                
            return Response({
                'success': True,
                'answer': answer,
                'question': question
            })
            
        except APIConnectionError as e:
            logger.error(f"DeepSeek API连接失败: {str(e)}")
            return Response(
                {'error': 'AI服务连接失败，请检查网络'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except RateLimitError as e:
            logger.error(f"DeepSeek API限流: {str(e)}")
            return Response(
                {'error': '请求过于频繁，请稍后再试'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        except APIStatusError as e:
            logger.error(f"DeepSeek API错误: {str(e)}")
            return Response(
                {'error': 'AI服务返回错误'},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.error(f"AI处理失败: {str(e)}")
            return Response(
                {'error': f'AI处理失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class DictionaryLookupAPI(APIView):
    """
    词典查询API
    调用百度智能云的词典查询服务
    """
    permission_classes = []
    
    def post(self, request):
        import logging
        
        logger = logging.getLogger(__name__)
        
        # 验证请求数据
        text = request.data.get('text')
        if not text:
            return Response(
                {'error': '查询文本不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # 去除开头空格
        text = text.lstrip()

        # 添加调试信息
        logger.debug(f"Received text for language detection: '{text}'")
        # 语言检测 - 只支持英语
        if not self.is_english(text):
            return Response(
                {'error': '只支持英语到汉语的翻译'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 1. 检查本地缓存
            local_record = DictionaryLookupRecord.objects.filter(query_text=text).first()
            if local_record:
                return self.format_cached_response(local_record)
            
            # 2. 调用API获取数据
            api_result = self.fetch_baidu_api(text)
            
            # 3. 解析并格式化结果
            formatted_result = self.parse_api_result(api_result)
            
            # 4. 创建记录（包含音频下载）
            return self.create_and_save_record(text, formatted_result)
            
        except Exception as e:
            logger.error(f"词典查询处理失败: {str(e)}")
            return Response(
                {'error': f'词典查询处理失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

    def format_cached_response(self, record):
        """格式化已缓存的响应"""
        return Response({
            'success': True,
            'result': [{
                'src': record.src_text,
                'dst': record.dst_text,
                'src_audio': record.src_audio.url if record.src_audio else None,
                'dst_audio': record.dst_audio.url if record.dst_audio else None,
                'dict': record.dict_data
            }]
        })
    
    def fetch_baidu_api(self, text):
        url="https://aip.baidubce.com/rpc/2.0/mt/texttrans-with-dict/v1?access_token=" + get_access_token()
        payload = json.dumps({
            "from": "en",
            "to": "zh",
            "q": text
        }, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))

        response.raise_for_status()
        api_result = response.json()

        return api_result
        


    def create_and_save_record(self, query_text, formatted_result):
        """创建并保存记录（包含音频下载）"""
        try:
            # 使用事务保证数据一致性
            with transaction.atomic():
                records = []
                for item in formatted_result:
                    record = DictionaryLookupRecord(
                        query_text=query_text,
                        src_text=item['src'],
                        dst_text=item['dst'],
                        src_tts_url=item.get('src_tts'),
                        dst_tts_url=item.get('dst_tts'),
                        dict_data=item['dict']
                    )
                    
                    # 保存音频文件（如果存在URL）
                    if item.get('src_tts'):
                        record.save_audio(item['src_tts'], 'src_audio')
                    if item.get('dst_tts'):
                        record.save_audio(item['dst_tts'], 'dst_audio')
                    
                    record.save()
                    records.append(record)
                
                return Response({
                    'success': True,
                    'result': [{
                        'src': r.src_text,
                        'dst': r.dst_text,
                        'src_audio': r.src_audio.url if r.src_audio else None,
                        'dst_audio': r.dst_audio.url if r.dst_audio else None,
                        'dict': r.dict_data
                    } for r in records]
                })
                
        except Exception as e:
            logger.error(f"保存记录失败: {str(e)}")
            raise
    
    def parse_api_result(self, api_result):
        """解析API响应并格式化数据"""
            # 解析API响应
        result = api_result.get('result', {})
        trans_result = result.get('trans_result', [])

        formatted_result = []
        for item in trans_result:
            formatted_item = {
                'src': item.get('src', ''),
                'dst': item.get('dst', ''),
                'src_tts': item.get('src_tts'),
                'dst_tts': item.get('dst_tts'),
                'dict': self.format_dict(item.get('dict', ''))
            }
            formatted_result.append(formatted_item)
        return formatted_result
    
    def is_english(self, text):
        """
        检测文本是否为英语
        :param text: 输入文本
        :return: 如果是英语返回True，否则返回False
        """
        try:
            detected_lang = detect(text)
            logger.debug(f"Detected language for text '{text}': {detected_lang}")
            if detected_lang == 'en':
                return True
            
            # 2. 如果langdetect不确定，添加更严格的检查
            # 只允许字母、空格和常见标点
            if re.match(r'^[a-zA-Z\s.,!?\'":;()-]+$', text):
                return True
            
            return False
        except LangDetectException:
            logger.debug(f"Language detection failed for text '{text}'")
            return False

    def format_dict(self, dict_str):
        try:
            # 使用更安全的json解析代替ast
            dict_data = json.loads(dict_str)
            
            # 初始化结构化数据容器
            formatted = {
                'word': dict_data.get('word_result', {}).get('word', ''),
                'pos': defaultdict(list),  # 使用defaultdict自动处理不同词性
                'means': [],
                'examples': [],
                'similar_words': [],
                'phonetic': {}
            }
            # 处理可能为空的edict字段
            edict_data = dict_data.get('word_result', {}).get('edict', {})
            if isinstance(edict_data, str) and not edict_data:
                # 空字符串情况
                edict_items = []
            elif isinstance(edict_data, dict):
                # 正常字典情况
                edict_items = edict_data.get('item', [])
            else:
                # 其他异常情况
                edict_items = []

            # 解析simple_means
            simple_means = dict_data.get('word_result', {}).get('simple_means', {}) or {}
            symbols = simple_means.get('symbols', [])

            # 处理音标数据
            if symbols := dict_data.get('simple_means', {}).get('symbols', []):
                first_symbol = symbols[0]
                formatted['phonetic'] = {
                    'en': first_symbol.get('ph_en'),
                    'am': first_symbol.get('ph_am')
                }

            # 解析词性和基础释义
            for symbol in dict_data.get('simple_means', {}).get('symbols', []):
                for part in symbol.get('parts', []):
                    pos = part.get('part', '')
                    if pos:
                        formatted['pos'][pos].extend(
                            [m for m in part.get('means', []) if not m.startswith('同')]
                        )

            # 解析详细词典数据
            edict_items = dict_data.get('word_result', {}).get('edict', {}).get('item', [])
            for item in edict_items:
                for tr_group in item.get('tr_group', []):
                    # 处理释义
                    formatted['means'].extend(tr_group.get('tr', []))
                    
                    # 处理例句（过滤空内容）
                    formatted['examples'].extend(
                        [ex for ex in tr_group.get('example', []) if ex]
                    )
                    
                    # 处理近义词（去重）
                    formatted['similar_words'].extend(
                        [sw for sw in tr_group.get('similar_word', []) 
                        if sw not in formatted['similar_words']]
                    )

            # 结构转换：将defaultdict转为普通dict
            formatted['pos'] = dict(formatted['pos'])
            
            # 数据清洗：去重和过滤
            formatted['means'] = list({m for m in formatted['means'] if m})
            formatted['examples'] = [e for e in formatted['examples'] if e.strip()]
            
            return formatted

        except Exception as e:
            logger.error(f"词典解析失败: {str(e)} | 原始数据: {dict_str[:200]}")  # 记录部分原始数据便于调试
            return {
                'error': '词典解析失败',
                'raw_data': dict_str[:200] + '...'  # 返回部分原始数据用于问题排查
            }

def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": settings.DICT_CONFIG['BAIDU_DICT']['API_KEY'], "client_secret": settings.DICT_CONFIG['BAIDU_DICT']['SECRET_KEY']}
    return str(requests.post(url, params=params).json().get("access_token"))

def is_valid_latex(formula):
    """
    简单校验 LaTeX 公式的格式
    :param formula: LaTeX 公式字符串
    :return: 如果公式格式有效返回 True，否则返回 False
    """
    # 简单的正则表达式校验，检查是否包含 $ 符号包裹的 LaTeX 命令
    latex_pattern = re.compile(r'^\$.+\$$')
    if not latex_pattern.match(formula):
        return False
    
    # 进一步检查常见的 LaTeX 命令格式（可选）
    # 例如，检查是否包含有效的数学模式命令
    valid_commands = re.compile(r'\\[a-zA-Z]+')
    if not valid_commands.search(formula):
        return False
    
    return True

def formula_to_img(request):
    formula = request.GET.get('formula', '')
    if not formula:
        return HttpResponse('No formula provided', status=400)
    
    # 校验公式格式--该校验很不准确
    # if not is_valid_latex(formula):
    #     return HttpResponse('Invalid LaTeX formula', status=400)
    
    try:
        # 数学公式渲染功能已禁用
        return HttpResponse("数学公式渲染功能已禁用", status=501)
        
        # 渲染公式
        ax.text(0.5, 0.5, f'${formula}$', fontsize=12, va='center', ha='center')
        
        # 保存到内存缓冲区
        return HttpResponse("数学公式渲染功能已禁用", status=501)
        # 返回图片响应
        buf.seek(0)
        return HttpResponse(buf.getvalue(), content_type='image/png')
    except Exception as e:
        logger.error(f"Error rendering formula: {str(e)}", exc_info=True)
        return HttpResponse(f'Error rendering formula: {str(e)}', status=500)