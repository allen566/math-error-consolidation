#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 导入自定义模块
from math_analyzer import MathAnalyzer
from question_generator import QuestionGenerator

# 初始化模块
analyzer = MathAnalyzer()
generator = QuestionGenerator()

class MathRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass
    
    def send_json_response(self, data, status=200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_html_response(self, html_content, status=200):
        """发送HTML响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/' or self.path == '/index.html':
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    self.send_html_response(f.read())
            else:
                self.send_json_response({'error': '首页未找到'}, 404)
        else:
            self.send_json_response({'error': '页面未找到'}, 404)
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/analyze':
            self.handle_analyze()
        else:
            self.send_json_response({'error': '接口不存在'}, 404)
    
    def handle_analyze(self):
        """处理文本分析请求"""
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            try:
                body_str = body.decode('utf-8')
            except UnicodeDecodeError:
                body_str = body.decode('latin-1')
            
            data = json.loads(body_str)
            question_text = data.get('question', '')
            
            if not question_text:
                self.send_json_response({'error': '请输入题目内容'}, 400)
                return
            
            # 分析题目
            analysis = analyzer.analyze(question_text)
            
            # 生成类似题目
            related_questions = generator.generate(
                analysis['knowledge_points'],
                count=3
            )
            
            self.send_json_response({
                'original_question': question_text,
                'analysis': analysis,
                'related_questions': related_questions
            })
            
        except Exception as e:
            print(f"Analysis error: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': f'分析失败: {str(e)}'}, 500)


def run_server(port=None):
    """启动服务器"""
    import socket
    
    # 优先使用环境变量 PORT（用于部署平台如 Render）
    if port is None:
        port = int(os.environ.get('PORT', 5000))
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, MathRequestHandler)
    
    # 获取本机IP地址
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"服务器已启动！")
    print(f"本机访问：http://localhost:{port}")
    print(f"手机访问：http://{local_ip}:{port}")
    print("(手机和电脑需连接同一WiFi)")
    print("按 Ctrl+C 停止服务器")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        httpd.server_close()


if __name__ == '__main__':
    run_server()
