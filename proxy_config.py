#!/usr/bin/env python3
"""
代理池配置文件
这个文件定义了代理池使用的全局配置参数
"""

import os
import subprocess
from pathlib import Path

# 默认端口配置
DEFAULT_PORT_CONFIG = {
    'DEFAULT_START_PORT': 9000,
    'PORT_OFFSET': 1,
    'PORT_INCREMENT': 10
}

def load_port_config():
    """从port_config.sh加载端口配置"""
    config = DEFAULT_PORT_CONFIG.copy()
    
    # 获取当前脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    port_config_path = script_dir / "port_config.sh"
    
    if port_config_path.exists():
        try:
            # 使用bash解析port_config.sh并获取配置
            cmd = f'source {port_config_path} && get_port_config'
            result = subprocess.run(['bash', '-c', cmd], 
                                  capture_output=True, text=True, check=True)
            
            # 解析输出中的配置参数
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key in config and value.isdigit():
                        config[key] = int(value)
        except Exception as e:
            print(f"警告: 无法加载端口配置文件: {e}")
            # 使用默认配置
    
    return config

# 加载端口配置
PORT_CONFIG = load_port_config()

# 导出配置供其他Python模块使用
DEFAULT_START_PORT = PORT_CONFIG['DEFAULT_START_PORT']
PORT_OFFSET = PORT_CONFIG['PORT_OFFSET']
PORT_INCREMENT = PORT_CONFIG['PORT_INCREMENT']

if __name__ == "__main__":
    # 直接运行时显示当前配置
    print("代理池配置参数:")
    print(f"默认起始端口: {DEFAULT_START_PORT}")
    print(f"HTTP与SOCKS端口差值: {PORT_OFFSET}")
    print(f"服务端口递增值: {PORT_INCREMENT}")
