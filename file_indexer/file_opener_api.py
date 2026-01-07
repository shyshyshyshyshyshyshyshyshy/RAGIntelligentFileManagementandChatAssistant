# file_opener_api.py 增强版
from flask import Flask, jsonify, request
import os
from threading import Thread
from smart_file_searcher import SmartFileSearcher  # 导入智能搜索器

# ---------------------- 配置项 ----------------------
ALLOWED_FILE_DIR = "D:/code/python/ALLOWED_FILE_DIR"
ALLOWED_EXTENSIONS = {".docx", ".doc", ".txt", ".pdf", ".xlsx", ".jpg", ".png"}
FLASK_PORT = 5002

# ---------------------- 初始化Flask应用 ----------------------
app = Flask(__name__)

# ---------------------- 初始化智能搜索器 ----------------------
smart_searcher = SmartFileSearcher()

# ---------------------- 原有文件打开函数 ----------------------
def is_allowed_file(file_name):
    file_path = os.path.abspath(os.path.join(ALLOWED_FILE_DIR, file_name))
    return (
        file_path.startswith(os.path.abspath(ALLOWED_FILE_DIR))
        and os.path.exists(file_path)
        and os.path.splitext(file_name)[1].lower() in ALLOWED_EXTENSIONS
    )

@app.route("/open-file", methods=["GET"])
def open_file():
    try:
        file_name = request.args.get("file_name", "")
        if not file_name:
            return jsonify({"code": 400, "message": "错误：缺少文件名参数"}), 400
        
        if not is_allowed_file(file_name):
            return jsonify({"code": 403, "message": f"文件 {file_name} 不合法"}), 403
        
        file_path = os.path.join(ALLOWED_FILE_DIR, file_name)
        os.startfile(file_path)
        
        return jsonify({
            "code": 200,
            "message": f"成功打开文件 {file_name}",
            "路径": file_path
        }), 200
    
    except Exception as e:
        return jsonify({"code": 500, "message": f"打开文件失败: {str(e)}"}), 500

# ---------------------- 新增智能搜索端点 ----------------------
@app.route("/smart-open", methods=["GET"])
def smart_open():
    """智能搜索并打开文件"""
    try:
        query = request.args.get("query", "")
        if not query:
            return jsonify({"code": 400, "message": "错误：缺少查询参数query"}), 400
        
        # 使用智能搜索器处理查询
        result = smart_searcher.search_and_open(query)
        
        return jsonify({
            "code": 200,
            "message": "智能搜索完成",
            "结果": result,
            "查询": query
        }), 200
    
    except Exception as e:
        return jsonify({"code": 500, "message": f"智能搜索失败: {str(e)}"}), 500

@app.route("/search-files", methods=["GET"])
def search_files():
    """搜索文件（不打开）"""
    try:
        query = request.args.get("query", "")
        if not query:
            return jsonify({"code": 400, "message": "错误：缺少查询参数"}), 400
        
        # 搜索知识库
        kb_results = smart_searcher.search_knowledge_base(query)
        kb_files = []
        
        for doc in kb_results:
            file_info = smart_searcher.extract_file_info_from_kb(doc)
            if file_info:
                kb_files.append(file_info)
        
        # 搜索本地文件
        local_files = smart_searcher.search_local_files(query)
        
        # 合并结果
        all_files = kb_files + local_files
        
        # 去重和排序
        unique_files = []
        seen_paths = set()
        
        for file_info in all_files:
            if file_info['path'] not in seen_paths:
                seen_paths.add(file_info['path'])
                unique_files.append(file_info)
        
        ranked_files = smart_searcher.rank_files(unique_files, query)
        
        # 格式化结果
        formatted_results = []
        for file_info in ranked_files[:5]:  # 只返回前5个
            formatted_results.append({
                "文件名": file_info['name'],
                "路径": file_info['path'],
                "匹配度": f"{file_info.get('score', 0):.2f}",
                "来源": file_info.get('source', 'local')
            })
        
        return jsonify({
            "code": 200,
            "查询": query,
            "结果数量": len(ranked_files),
            "最佳匹配": formatted_results
        }), 200
    
    except Exception as e:
        return jsonify({"code": 500, "message": f"搜索失败: {str(e)}"}), 500

# ---------------------- 跨域配置 ----------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# ---------------------- 后台监控 ----------------------
try:
    from file_indexer.monitor import start_file_monitor
except ImportError:
    def start_file_monitor():
        print("提示：文件监控模块未找到")

def start_background_monitor():
    monitor_thread = Thread(target=start_file_monitor, daemon=True)
    monitor_thread.start()
    print("后台文件监控已启动")

# ---------------------- 启动服务 ----------------------
if __name__ == "__main__":
    start_background_monitor()
    print(f"🔧 智能文件服务已启动，端口：{FLASK_PORT}")
    print("📖 可用端点：")
    print("   /open-file?file_name=文件名 - 直接打开文件")
    print("   /smart-open?query=描述 - 智能搜索并打开")
    print("   /search-files?query=描述 - 只搜索不打开")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)