import sys
import os
# 强制解决ModuleNotFoundError，无需修改
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import docx
import logging
from config import config

# 配置日志，无需修改
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_file_content(file_path):
    """读取文件内容并截断，无需修改"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()
    content = ""
    
    try:
        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        elif file_ext == '.docx':
            doc = docx.Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

        if len(content) > config.CONTENT_TRUNCATE_LENGTH:
            content = content[:config.CONTENT_TRUNCATE_LENGTH] + "\n...（内容过长，已截断）"
        return content

    except Exception as e:
        raise Exception(f"文件读取失败: {str(e)}")

def generate_file_index(file_path, file_name, create_time, update_time):
    """本地生成标准化索引，无需调用Dify API，无需修改"""
    try:
        # 读取原文件内容
        file_content = read_file_content(file_path)
        
        # 自动提取关键词，支持模糊检索
        base_keywords = ["项目", "作业", "文档", "报告", "开发", "管理", "进度", "成本"]
        file_name_keywords = file_name.replace('.', ' ').replace('(', ' ').replace(')', ' ').split()
        all_keywords = list(set(base_keywords + file_name_keywords))
        all_keywords = [kw for kw in all_keywords if kw.strip() and len(kw) > 1]

        # 标准化索引格式
        index_content = f"""文件名：{file_name}
文件路径：{file_path}
创建时间：{create_time}
更新时间：{update_time}
内容总结：{file_content[:300]}...（完整内容请查阅原文件）
关键词：{','.join(all_keywords)}"""
        
        # 保存索引文件，避免重名
        file_name_no_ext = os.path.splitext(file_name)[0]
        index_txt_name = f"{file_name_no_ext}_index.txt"
        index_txt_path = os.path.join(config.TARGET_DIR, index_txt_name)
        
        with open(index_txt_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        logger.info(f"索引文件已生成: {index_txt_path}")
        return index_txt_path
        
    except Exception as e:
        logger.error(f"索引生成失败: {str(e)}", exc_info=True)
        raise