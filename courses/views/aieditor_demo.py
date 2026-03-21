from django.shortcuts import render
from django.http import HttpResponse
import io
import urllib.parse

def formula_to_img(request):
    formula = request.GET.get('formula', '')
    if not formula:
        return HttpResponse('No formula provided', status=400)
    
    try:
        # 数学公式渲染已移除
        return HttpResponse("数学公式渲染功能已禁用", status=501)
        # 渲染公式
        parser = mathtext.MathTextParser('agg')
        parser.to_png(io.BytesIO(), formula, color='black', dpi=120)
        
        # 保存到内存缓冲区
        return HttpResponse("数学公式渲染功能已禁用", status=501)
        # 返回图片响应
        buf.seek(0)
        return HttpResponse(buf.getvalue(), content_type='image/png')
    except Exception as e:
        return HttpResponse(f'Error rendering formula: {str(e)}', status=500)

def aieditor_demo(request):
    return render(request, 'aieditor_demo.html')
