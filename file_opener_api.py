# file_opener_api.py - 增强版
import os
import json
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import threading
import webbrowser

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

class FileOpener:
    """文件打开器"""
    
    @staticmethod
    def open_file(file_path):
        """使用系统默认程序打开文件"""
        try:
            if not os.path.exists(file_path):
                return {"code": 404, "message": f"文件不存在: {file_path}"}
            
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['xdg-open', file_path], check=True)
            else:
                return {"code": 400, "message": "不支持的操作系统"}
            
            logger.info(f"✅ 文件已打开: {file_path}")
            return {"code": 200, "message": f"文件已成功打开: {file_path}"}
            
        except Exception as e:
            logger.error(f"❌ 打开文件失败: {str(e)}")
            return {"code": 500, "message": f"打开文件失败: {str(e)}"}

@app.route('/')
def index():
    """主页面"""
    return send_from_directory('.', 'index.html')

@app.route('/open-file', methods=['GET'])
def open_file_api():
    """打开文件API接口"""
    file_name = request.args.get('file_name')
    file_path = request.args.get('file_path')
    
    if not file_name and not file_path:
        return jsonify({"code": 400, "message": "请提供文件名或文件路径"})
    
    if file_name and not file_path:
        monitor_dir = os.getenv('MONITOR_DIR', 'D:/code/python/ALLOWED_FILE_DIR')
        file_path = os.path.join(monitor_dir, file_name)
    
    result = FileOpener.open_file(file_path)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"code": 200, "message": "文件打开服务运行正常"})

def open_browser():
    """启动后自动打开浏览器"""
    webbrowser.open('http://localhost:5002/')

if __name__ == '__main__':
    # 延迟2秒打开浏览器
    timer = threading.Timer(2, open_browser)
    timer.start()
    
    app.run(host='0.0.0.0', port=5002, debug=False)