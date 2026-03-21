# 2. 如果本地没有记录，再调用外部API
            # 调用百度智能云词典查询服务
            # 这里需要替换为实际的API调用
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
            
            # 解析API响应
            result = api_result.get('result', {})
            trans_result = result.get('trans_result', [])
            
            if not trans_result:
                return Response({
                    'success': False,
                    'error': '未找到翻译结果'
                }, status=status.HTTP_404_NOT_FOUND)
            
            formatted_result = []
            for item in trans_result:
                formatted_item = {
                    'src': item.get('src', ''), # 源文本
                    'dst': item.get('dst', ''), # 目标文本
                    'src_tts': item.get('src_tts', ''), # 源文本的语音链接,要下载
                    'dst_tts': item.get('dst_tts', ''), # 目标文本的语音链接，也下载吧
                    'dict': self.format_dict(item.get('dict', '')) # 词典数据
                }
                formatted_result.append(formatted_item)
            
            for item in formatted_result:
                DictionaryLookupRecord.objects.create(
                    query_text=text,
                    src_text=item['src'],
                    dst_text=item['dst'],
                    src_tts=item['src_tts'],
                    dst_tts=item['dst_tts'],
                    dict_data=item['dict']
                )
            
            return Response({
                'success': True,
                'result': formatted_result
            })