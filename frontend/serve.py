"""灵境同行 - 一键启动服务"""
import http.server
import webbrowser
import os
import sys
import threading

PORT = 8080
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')

if not os.path.isdir(DIR):
    print('[错误] 未找到 dist/ 目录，请先运行 npm run build')
    sys.exit(1)

# 切换到 dist 目录
os.chdir(DIR)

# 延迟打开浏览器（等服务器启动）
def open_browser():
    webbrowser.open(f'http://localhost:{PORT}')

threading.Timer(1.0, open_browser).start()

print('=' * 48)
print('  灵境同行 - AI 数字人景区导览系统')
print(f'  地址: http://localhost:{PORT}')
print('  按 Ctrl+C 停止服务')
print('=' * 48)

http.server.test(
    HandlerClass=http.server.SimpleHTTPRequestHandler,
    port=PORT,
)
