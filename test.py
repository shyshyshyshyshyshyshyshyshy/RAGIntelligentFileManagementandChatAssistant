import os
import re
import json
import configparser
from pathlib import Path

def find_dify_config():
    """
    查找Dify配置项的脚本
    会扫描环境变量、配置文件等常见位置
    """
    config_values = {
        'DIFY_URL': None,
        'API_KEY': None
    }
    
    print("🔍 开始查找Dify配置...")
    
    # 1. 检查环境变量
    print("\n1. 检查环境变量...")
    env_vars = [
        'DIFY_URL', 'DIFY_BASE_URL', 'DIFY_API_URL',
        'API_KEY', 'DIFY_API_KEY', 'DIFY_TOKEN'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ 找到环境变量 {var}: {value}")
            if 'URL' in var:
                config_values['DIFY_URL'] = value
            elif 'KEY' in var or 'TOKEN' in var:
                config_values['API_KEY'] = value
    
    # 2. 检查当前目录的配置文件
    print("\n2. 检查配置文件...")
    config_files = [
        '.env', 'config.py', 'config.json', 'settings.py',
        'configuration.py', 'dify_config.py'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   📁 找到配置文件: {config_file}")
            try:
                if config_file == '.env':
                    # 解析.env文件
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                if '=' in line:
                                    key, value = line.split('=', 1)
                                    key = key.strip()
                                    value = value.strip()
                                    
                                    if any(url_key in key.upper() for url_key in ['DIFY_URL', 'DIFY_BASE_URL']):
                                        config_values['DIFY_URL'] = value
                                        print(f"     ✅ 从.env找到DIFY_URL: {value}")
                                    elif any(key_key in key.upper() for key_key in ['API_KEY', 'DIFY_API_KEY']):
                                        config_values['API_KEY'] = value
                                        print(f"     ✅ 从.env找到API_KEY: {value}")
                
                elif config_file.endswith('.py'):
                    # 解析Python配置文件
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 查找URL配置
                        url_patterns = [
                            r"DIFY_URL\s*=\s*['\"]([^'\"]+)['\"]",
                            r"DIFY_BASE_URL\s*=\s*['\"]([^'\"]+)['\"]",
                            r"BASE_URL\s*=\s*['\"]([^'\"]+)['\"]"
                        ]
                        
                        for pattern in url_patterns:
                            match = re.search(pattern, content)
                            if match:
                                config_values['DIFY_URL'] = match.group(1)
                                print(f"     ✅ 从{config_file}找到DIFY_URL: {match.group(1)}")
                                break
                        
                        # 查找API密钥
                        key_patterns = [
                            r"API_KEY\s*=\s*['\"]([^'\"]+)['\"]",
                            r"DIFY_API_KEY\s*=\s*['\"]([^'\"]+)['\"]",
                            r"API_TOKEN\s*=\s*['\"]([^'\"]+)['\"]"
                        ]
                        
                        for pattern in key_patterns:
                            match = re.search(pattern, content)
                            if match:
                                config_values['API_KEY'] = match.group(1)
                                print(f"     ✅ 从{config_file}找到API_KEY: {match.group(1)}")
                                break
                
                elif config_file.endswith('.json'):
                    # 解析JSON配置文件
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        
                        # 尝试不同的键名
                        url_keys = ['dify_url', 'dify_base_url', 'base_url', 'api_url']
                        for key in url_keys:
                            if key in config_data:
                                config_values['DIFY_URL'] = config_data[key]
                                print(f"     ✅ 从{config_file}找到DIFY_URL: {config_data[key]}")
                                break
                        
                        key_keys = ['api_key', 'dify_api_key', 'api_token', 'token']
                        for key in key_keys:
                            if key in config_data:
                                config_values['API_KEY'] = config_data[key]
                                print(f"     ✅ 从{config_file}找到API_KEY: {config_data[key]}")
                                break
                            
            except Exception as e:
                print(f"     ❌ 读取配置文件{config_file}时出错: {e}")
    
    # 3. 检查项目根目录的上级目录（常见于大型项目）
    print("\n3. 检查项目结构...")
    current_dir = Path.cwd()
    parent_dirs = [current_dir] + list(current_dir.parents)[:3]  # 当前目录及向上3级
    
    for parent_dir in parent_dirs:
        for config_file in ['.env', 'config.py', 'config.json']:
            config_path = parent_dir / config_file
            if config_path.exists() and config_path not in [current_dir / f for f in config_files]:
                print(f"   📁 找到上级配置文件: {config_path}")
                # 这里可以添加解析逻辑，与上面类似
    
    # 4. 检查常见的Dify相关文件
    print("\n4. 检查Dify相关文件...")
    dify_files = [
        'knowledge_sync.py', 'dify_file_tool.py', 
        'file_opener_api.py', 'smart_file_searcher.py'
    ]
    
    for dify_file in dify_files:
        if os.path.exists(dify_file):
            print(f"   📁 扫描Dify相关文件: {dify_file}")
            try:
                with open(dify_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 在代码中查找硬编码的配置
                    url_matches = re.findall(r"['\"]http[^'\"]+5001[^'\"]*['\"]", content)
                    for match in url_matches:
                        print(f"     🔍 找到可能的Dify URL: {match}")
                        if not config_values['DIFY_URL']:
                            config_values['DIFY_URL'] = match.strip('"\'')
                    
                    # 查找API密钥模式（通常为长字符串）
                    key_pattern = r"['\"][a-fA-F0-9]{32,}['\"]"
                    key_matches = re.findall(key_pattern, content)
                    for match in key_matches:
                        if len(match) > 10:  # 过滤掉太短的匹配
                            print(f"     🔍 找到可能的API密钥: {match[:10]}...")
                            if not config_values['API_KEY']:
                                config_values['API_KEY'] = match.strip('"\'')
                                
            except Exception as e:
                print(f"     ❌ 读取文件{dify_file}时出错: {e}")
    
    # 5. 输出结果
    print("\n" + "="*50)
    print("🎯 查找结果:")
    print("="*50)
    
    if config_values['DIFY_URL']:
        print(f"✅ DIFY_URL: {config_values['DIFY_URL']}")
    else:
        print("❌ 未找到DIFY_URL配置")
        print("   建议检查: .env文件、环境变量、config.py等配置文件")
    
    if config_values['API_KEY']:
        # 显示部分密钥，保护敏感信息
        key_display = config_values['API_KEY'][:10] + "..." + config_values['API_KEY'][-10:]
        print(f"✅ API_KEY: {key_display}")
    else:
        print("❌ 未找到API_KEY配置")
        print("   建议检查: .env文件、环境变量、config.py等配置文件")
    
    # 6. 提供配置建议
    print("\n" + "="*50)
    print("💡 配置建议:")
    print("="*50)
    
    if not config_values['DIFY_URL']:
        print("1. 创建.env文件并添加:")
        print("   DIFY_BASE_URL=http://localhost:5001")
    
    if not config_values['API_KEY']:
        print("2. 获取API密钥:")
        print("   - 登录Dify控制台")
        print('   - 进入"设置" -> "API密钥"')
        print("   - 创建新的API密钥")
        print("   - 在.env文件中添加: DIFY_API_KEY=你的API密钥")
    
    if not config_values['DIFY_URL'] or not config_values['API_KEY']:
        print("\3. 或者在代码中直接设置:")
        print("   const DIFY_URL = 'http://localhost:5001/v1/chat-messages';")
        print("   const API_KEY = '你的实际API密钥';")
    
    return config_values

if __name__ == "__main__":
    find_dify_config()