import requests
import yaml
import os
from dotenv import load_dotenv
import time
import sys

# 加载环境变量
load_dotenv()

def get_env_config():
    """从环境变量获取配置"""
    config = {
        'proxy_urls': os.getenv('PROXY_URLS', '').split(','),
        'output_directory': os.getenv('OUTPUT_DIRECTORY', './'),
        'input_directory': os.getenv('INPUT_DIRECTORY', './'),
        'proxy_providers_directory': os.getenv('PROXY_PROVIDERS_DIRECTORY', 'proxy_providers'),
        'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
        'max_retries': int(os.getenv('MAX_RETRIES', '3'))
    }
    
    # 清理空的URL
    config['proxy_urls'] = [url.strip() for url in config['proxy_urls'] if url.strip()]
    
    if not config['proxy_urls']:
        print("错误：未在环境变量中找到有效的代理URL")
        print("请创建.env文件并设置PROXY_URLS变量")
        print("参考config.example.env文件")
        sys.exit(1)
    
    return config

def download_proxy_config(url, timeout, max_retries):
    """下载代理配置，支持重试机制"""
    for attempt in range(max_retries):
        try:
            print(f"正在下载配置... (尝试 {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                raise

def main():
    """主函数"""
    print("=== 代理池配置提取工具 ===")
    print("支持平台: Ubuntu, macOS")
    print()
    
    # 获取配置
    config = get_env_config()
    
    # 创建输出目录
    os.makedirs(config['output_directory'], exist_ok=True)
    os.makedirs(config['proxy_providers_directory'], exist_ok=True)
    
    print(f"找到 {len(config['proxy_urls'])} 个代理URL")
    print(f"输出目录: {config['proxy_providers_directory']}")
    print()

    # 遍历 URL 列表并下载内容
    for index, url in enumerate(config['proxy_urls'], start=1):
        try:
            print(f"处理URL {index}: {url[:50]}...")
            
            # 下载文件内容
            content = download_proxy_config(url, config['request_timeout'], config['max_retries'])

            # 解析YAML内容
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                print(f"YAML解析错误: {e}")
                continue

            # 保存下载的内容为 YAML 文件
            output_file_name = f"proxy_{index}.yaml"
            output_file_path = os.path.join(config['output_directory'], output_file_name)
            with open(output_file_path, 'w', encoding='utf-8') as yaml_file:
                yaml.dump(data, yaml_file, allow_unicode=True, default_flow_style=False)

            print(f"✓ 已保存原始配置: {output_file_path}")
            
            # 统计代理数量
            if 'proxies' in data:
                proxy_count = len(data['proxies'])
                print(f"  发现 {proxy_count} 个代理节点")

        except Exception as e:
            print(f"✗ 处理URL {index} 失败: {e}")
            continue

    print()
    print("=== 分离代理配置 ===")
    
    # 遍历输入目录下的所有文件
    total_proxies = 0
    for file_name in os.listdir(config['input_directory']):
        # 检查文件是否以 .yaml 结尾
        if file_name.endswith('.yaml'):
            input_file_path = os.path.join(config['input_directory'], file_name)

            try:
                # 读取当前的 YAML 文件
                with open(input_file_path, 'r', encoding='utf-8') as file:
                    parsed_data = yaml.safe_load(file)

                # 检查是否有 'proxies' 键，避免解析出错
                if 'proxies' in parsed_data:
                    # 为每个代理创建一个 YAML 文件
                    for index, proxy in enumerate(parsed_data['proxies'], start=1):
                        # 构建新的代理字典，包装在一个列表下的字典中
                        formatted_proxy = {'proxies': [proxy]}

                        # 定义输出文件名，使用原始文件名加上代理索引
                        output_file_name = f"{os.path.splitext(file_name)[0]}_proxy_{index}.yaml"
                        output_file_path = os.path.join(config['proxy_providers_directory'], output_file_name)

                        # 将格式化的代理写入到单独的 YAML 文件，使用多行格式
                        with open(output_file_path, 'w', encoding='utf-8') as f:
                            yaml.dump(formatted_proxy, f, allow_unicode=True, default_flow_style=False)

                        total_proxies += 1
                        if total_proxies <= 5:  # 只显示前5个，避免输出过多
                            print(f"✓ 创建代理文件: {output_file_path}")
                        elif total_proxies == 6:
                            print("  ...")
                            
                else:
                    print(f"⚠ 文件 {file_name} 中未找到代理配置")
                    
            except Exception as e:
                print(f"✗ 处理文件 {file_name} 失败: {e}")

    print()
    print(f"=== 完成 ===")
    print(f"总共处理了 {total_proxies} 个代理节点")
    print(f"代理文件保存在: {config['proxy_providers_directory']}/")
    print()
    print("下一步:")
    print("1. 下载mihomo: https://github.com/MetaCubeX/mihomo/releases")
    print("2. 创建配置文件，每个代理使用不同端口")
    print("3. 启动多个mihomo实例")

if __name__ == "__main__":
    main()