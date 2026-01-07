# dify_file_tool.py
import requests

class DifyFileTool:
    def __init__(self):
        self.file_api_url = "http://localhost:5002"
    
    def open_file_by_description(self, user_description: str) -> str:
        """
        根据模糊描述打开文件
        
        Args:
            user_description: 用户描述，如"帮我打开昨天还在完成的文档"
        
        Returns:
            str: 操作结果
        """
        try:
            response = requests.get(
                f"{self.file_api_url}/smart-open",
                params={"query": user_description},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("结果", "操作完成")
            else:
                return f"API调用失败: {response.status_code}"
                
        except Exception as e:
            return f"打开文件失败: {str(e)}"
    
    def search_files(self, query: str) -> str:
        """
        搜索文件（不打开）
        
        Args:
            query: 搜索查询
            
        Returns:
            str: 搜索结果
        """
        try:
            response = requests.get(
                f"{self.file_api_url}/search-files",
                params={"query": query},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                files = result.get("最佳匹配", [])
                
                if not files:
                    return "没有找到匹配的文件"
                
                response_text = f"找到 {result.get('结果数量', 0)} 个匹配文件:\n\n"
                for i, file_info in enumerate(files, 1):
                    response_text += f"{i}. {file_info['文件名']} (匹配度: {file_info['匹配度']})\n"
                
                return response_text
            else:
                return f"搜索失败: {response.status_code}"
                
        except Exception as e:
            return f"搜索异常: {str(e)}"

# 创建工具实例
file_tool = DifyFileTool()

# Dify工具函数
def open_file_by_description(user_description: str) -> str:
    return file_tool.open_file_by_description(user_description)

def search_files(query: str) -> str:
    return file_tool.search_files(query)