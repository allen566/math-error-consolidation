#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import time
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 导入自定义模块
from math_analyzer import MathAnalyzer
from question_generator import QuestionGenerator

# 初始化模块
analyzer = MathAnalyzer()
generator = QuestionGenerator()

# 数据目录
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

# 确保数据目录存在
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def hash_password(password):
    """简单的密码哈希"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def load_users():
    """加载用户数据"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_users(users):
    """保存用户数据"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user_mistakes_file(username):
    """获取用户的错题本文件路径"""
    return os.path.join(DATA_DIR, f'mistakes_{username}.json')

def load_mistakes(username):
    """加载用户的错题"""
    mistakes_file = get_user_mistakes_file(username)
    if os.path.exists(mistakes_file):
        try:
            with open(mistakes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def save_mistakes(username, mistakes):
    """保存用户的错题"""
    mistakes_file = get_user_mistakes_file(username)
    with open(mistakes_file, 'w', encoding='utf-8') as f:
        json.dump(mistakes, f, ensure_ascii=False, indent=2)

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
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        try:
            body_str = body.decode('utf-8')
        except UnicodeDecodeError:
            body_str = body.decode('latin-1')
        
        data = json.loads(body_str)
        
        if self.path == '/register':
            self.handle_register(data)
        elif self.path == '/login':
            self.handle_login(data)
        elif self.path == '/analyze':
            self.handle_analyze(data)
        elif self.path == '/mistakes':
            self.handle_add_mistake(data)
        elif self.path == '/mistakes/list':
            self.handle_get_mistakes(data)
        elif self.path == '/mistakes/delete':
            self.handle_delete_mistake(data)
        elif self.path == '/mistakes/stars':
            self.handle_update_stars(data)
        else:
            self.send_json_response({'error': '接口不存在'}, 404)
    
    def handle_register(self, data):
        """处理注册请求"""
        try:
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not password:
                self.send_json_response({'error': '用户名和密码不能为空'}, 400)
                return
            
            if len(username) < 3:
                self.send_json_response({'error': '用户名至少3个字符'}, 400)
                return
            
            if len(password) < 4:
                self.send_json_response({'error': '密码至少4个字符'}, 400)
                return
            
            users = load_users()
            
            if username in users:
                self.send_json_response({'error': '用户名已存在'}, 400)
                return
            
            users[username] = {
                'password': hash_password(password),
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            save_users(users)
            
            self.send_json_response({'success': True, 'message': '注册成功，请登录'})
        except Exception as e:
            print(f'注册错误: {e}')
            self.send_json_response({'error': f'注册失败: {str(e)}'}, 500)
    
    def handle_login(self, data):
        """处理登录请求"""
        try:
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not password:
                self.send_json_response({'error': '用户名和密码不能为空'}, 400)
                return
            
            users = load_users()
            
            if username not in users:
                self.send_json_response({'error': '用户名不存在'}, 400)
                return
            
            if users[username]['password'] != hash_password(password):
                self.send_json_response({'error': '密码错误'}, 400)
                return
            
            self.send_json_response({'success': True, 'username': username})
        except Exception as e:
            print(f'登录错误: {e}')
            self.send_json_response({'error': f'登录失败: {str(e)}'}, 500)
    
    def handle_analyze(self, data):
        """处理文本分析请求"""
        try:
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
            print(f'分析错误: {e}')
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': f'分析失败: {str(e)}'}, 500)
    
    def handle_get_mistakes(self, data):
        """获取错题列表"""
        try:
            username = data.get('username', '')
            if not username:
                self.send_json_response({'error': '请先登录'}, 400)
                return
            
            mistakes = load_mistakes(username)
            self.send_json_response({'mistakes': mistakes})
        except Exception as e:
            print(f'获取错题错误: {e}')
            self.send_json_response({'error': f'获取错题失败: {str(e)}'}, 500)
    
    def handle_add_mistake(self, data):
        """添加错题"""
        try:
            username = data.get('username', '')
            if not username:
                self.send_json_response({'error': '请先登录'}, 400)
                return
            
            mistake = {
                'id': str(int(time.time() * 1000)),
                'question': data.get('question', ''),
                'analysis': data.get('analysis', {}),
                'related_questions': data.get('related_questions', []),
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'stars': 0  # 默认0星
            }
            
            mistakes = load_mistakes(username)
            mistakes.insert(0, mistake)
            save_mistakes(username, mistakes)
            
            self.send_json_response({'success': True, 'mistake': mistake})
        except Exception as e:
            print(f'添加错题错误: {e}')
            self.send_json_response({'error': f'添加错题失败: {str(e)}'}, 500)
    
    def handle_update_stars(self, data):
        """更新星级"""
        try:
            username = data.get('username', '')
            if not username:
                self.send_json_response({'error': '请先登录'}, 400)
                return
            
            mistake_id = data.get('id', '')
            if not mistake_id:
                self.send_json_response({'error': '请指定要更新的错题'}, 400)
                return
            
            stars = data.get('stars', 0)
            if not isinstance(stars, int) or stars < 0 or stars > 5:
                self.send_json_response({'error': '星级必须是0-5之间的整数'}, 400)
                return
            
            mistakes = load_mistakes(username)
            for mistake in mistakes:
                if mistake.get('id') == mistake_id:
                    mistake['stars'] = stars
                    break
            
            save_mistakes(username, mistakes)
            
            self.send_json_response({'success': True})
        except Exception as e:
            print(f'更新星级错误: {e}')
            self.send_json_response({'error': f'更新星级失败: {str(e)}'}, 500)
    
    def handle_delete_mistake(self, data):
        """删除错题"""
        try:
            username = data.get('username', '')
            if not username:
                self.send_json_response({'error': '请先登录'}, 400)
                return
            
            mistake_id = data.get('id', '')
            if not mistake_id:
                self.send_json_response({'error': '请指定要删除的错题'}, 400)
                return
            
            mistakes = load_mistakes(username)
            mistakes = [m for m in mistakes if m.get('id') != mistake_id]
            save_mistakes(username, mistakes)
            
            self.send_json_response({'success': True})
        except Exception as e:
            print(f'删除错题错误: {e}')
            self.send_json_response({'error': f'删除错题失败: {str(e)}'}, 500)


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
    
    print(f'服务器已启动！')
    print(f'本机访问：http://localhost:{port}')
    print(f'手机访问：http://{local_ip}:{port}')
    print('(手机和电脑需连接同一WiFi)')
    print('按 Ctrl+C 停止服务器')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n服务器已停止')
        httpd.server_close()


if __name__ == '__main__':
    run_server()
