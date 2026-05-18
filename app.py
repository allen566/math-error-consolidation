#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 导入自定义模块
from math_analyzer import MathAnalyzer
from question_generator import QuestionGenerator
from ocr_processor import OCRProcessor

# 初始化模块
analyzer = MathAnalyzer()
generator = QuestionGenerator()
ocr_processor = OCRProcessor()

# 配置
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
        elif self.path.startswith('/uploads/'):
            self.serve_uploaded_file()
        else:
            self.send_json_response({'error': '页面未找到'}, 404)
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/upload':
            self.handle_upload()
        elif self.path == '/analyze':
            self.handle_analyze()
        else:
            self.send_json_response({'error': '接口不存在'}, 404)
    
    def serve_uploaded_file(self):
        """提供上传文件的服务"""
        try:
            filename = self.path.split('/')[-1]
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            if not os.path.exists(filepath):
                self.send_json_response({'error': '文件不存在'}, 404)
                return
            
            # 根据扩展名设置Content-Type
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            content_types = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
            }
            
            content_type = content_types.get(ext, 'application/octet-stream')
            
            with open(filepath, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            print(f"Error serving file: {e}")
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_upload(self):
        """处理文件上传"""
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            # 解析multipart/form-data
            boundary = self.headers.get('Content-Type').split('boundary=')[1] if 'boundary=' in self.headers.get('Content-Type', '') else None
            
            if boundary:
                parts = body.split(b'--' + boundary.encode())
                
                for part in parts:
                    if b'filename=' in part:
                        # 提取文件数据
                        header_end = part.find(b'\r\n\r\n')
                        file_data = part[header_end+4:].rstrip(b'\r\n--')
                        
                        # 提取原始文件名
                        header = part[:header_end].decode('utf-8', errors='ignore')
                        filename_start = header.find('filename="')
                        if filename_start != -1:
                            filename = header[filename_start+10:header.find('"', filename_start+10)]
                            
                            # 保存文件（使用UUID避免文件名冲突）
                            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'png'
                            unique_name = f"{uuid.uuid4().hex}.{ext}"
                            filepath = os.path.join(UPLOAD_FOLDER, unique_name)
                            
                            with open(filepath, 'wb') as f:
                                f.write(file_data)
                            
                            image_url = f"/uploads/{unique_name}"
                            
                            # OCR识别图片中的文字
                            if ocr_processor.is_available():
                                question_text = ocr_processor.extract_text(filepath)
                                if question_text == "__OCR_NOT_AVAILABLE__":
                                    question_text = "⚠️ OCR引擎不可用，请手动输入题目内容"
                                elif not question_text or len(question_text) < 5:
                                    question_text = "⚠️ 识别结果不清晰，请手动输入或编辑题目内容"
                            else:
                                question_text = "⚠️ 未安装Tesseract OCR，请手动输入题目内容（图片已保存）"
                            
                            # 分析题目
                            analysis = analyzer.analyze(question_text)
                            
                            # 生成类似题目
                            related_questions = generator.generate(
                                analysis['knowledge_points'],
                                count=3
                            )
                            
                            self.send_json_response({
                                'original_question': question_text,
                                'image_url': image_url,
                                'analysis': analysis,
                                'related_questions': related_questions
                            })
                            return
            
            self.send_json_response({'error': '无法解析上传的文件'}, 400)
            
        except Exception as e:
            print(f"Upload error: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': f'上传失败: {str(e)}'}, 500)
    
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
    import os
    
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
