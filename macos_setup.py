#!/usr/bin/env python3
"""
MacOS代理池管理脚本
自动生成mihomo配置文件和LaunchAgent服务
"""

import os
import yaml
import json
import shutil
import subprocess
from pathlib import Path

class MacOSProxyPoolManager:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or Path.home() / "proxy_pool")
        self.config_dir = self.base_dir / "config"
        self.bin_dir = self.base_dir / "bin" 
        self.providers_dir = self.base_dir / "proxy_providers"
        self.launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        
        # 创建必要目录
        for dir_path in [self.config_dir, self.bin_dir, self.providers_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def check_mihomo(self):
        """检查并下载mihomo"""
        mihomo_path = self.bin_dir / "mihomo"
        if mihomo_path.exists():
            print(f"✓ mihomo已存在: {mihomo_path}")
            return str(mihomo_path)
        
        print("mihomo未找到，请手动下载:")
        print("1. 访问: https://github.com/MetaCubeX/mihomo/releases")
        print("2. 下载适合macOS的版本 (通常是 mihomo-darwin-amd64 或 mihomo-darwin-arm64)")
        print(f"3. 重命名为 mihomo 并放置到: {mihomo_path}")
        print("4. 运行: chmod +x {mihomo_path}")
        return None
    
    def generate_config(self, service_name, http_port, socks_port, controller_port, dns_port, provider_file):
        """生成mihomo配置文件"""
        config = {
            'port': http_port,
            'socks-port': socks_port,
            'allow-lan': True,
            'mode': 'Rule',
            'log-level': 'info',
            'tcp-concurrent': True,
            'external-controller': f':{controller_port}',
            'external-ui': './ui',
            'geodata-mode': True,
            'global-client-fingerprint': 'chrome',
            'profile': {'store-selected': True},
            
            'sniffer': {
                'enable': True,
                'force-dns-mapping': True,
                'parse-pure-ip': True,
                'force-domain': ['+.netflix.com', '+.nflxvideo.net', '+.amazonaws.com'],
                'skip-domain': ['+.apple.com', 'Mijia Cloud'],
                'sniff': {
                    'TLS': {},
                    'HTTP': {
                        'ports': ['80', '8080-8880'],
                        'override-destination': True
                    }
                }
            },
            
            'dns': {
                'enable': True,
                'listen': f':{dns_port}',
                'ipv6': True,
                'enhanced-mode': 'fake-ip',
                'fake-ip-range': '28.0.0.1/8',
                'fake-ip-filter': ['*', '+.lan', '+.local'],
                'default-nameserver': ['223.5.5.5', '119.29.29.29', '114.114.114.114'],
                'nameserver': ['tls://8.8.4.4#dns', 'tls://1.0.0.1#dns'],
                'proxy-server-nameserver': ['https://doh.pub/dns-query']
            },
            
            'experimental': {'ignore-resolve-fail': True},
            'unified-delay': True,
            
            'proxy-groups': [
                {
                    'name': 'PROXY',
                    'type': 'select',
                    'proxies': [service_name, 'DIRECT']
                },
                {
                    'name': service_name,
                    'type': 'url-test',
                    'use': ['provider1'],
                    'url': 'http://www.gstatic.com/generate_204',
                    'interval': 300,
                    'tolerance': 50
                }
            ],
            
            'proxy-providers': {
                'provider1': {
                    'type': 'file',
                    'path': str(self.providers_dir / provider_file),
                    'interval': 3600,
                    'health-check': {
                        'enable': True,
                        'url': 'https://www.gstatic.com/generate_204',
                        'interval': 300,
                        'timeout': 5000,
                        'expected-status': 204
                    },
                    'override': {'udp': True}
                }
            },
            
            'rules': [
                'DOMAIN-SUFFIX,apple.com,DIRECT',
                'DOMAIN-SUFFIX,icloud.com,DIRECT',
                'GEOIP,CN,DIRECT',
                'MATCH,PROXY'
            ]
        }
        
        config_file = self.config_dir / f"{service_name}.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"✓ 生成配置文件: {config_file}")
        return str(config_file)
    
    def create_launch_agent(self, service_name, config_file, mihomo_path):
        """创建LaunchAgent plist文件"""
        plist_content = {
            'Label': f'com.proxypool.{service_name}',
            'ProgramArguments': [
                str(mihomo_path),
                '-f', str(config_file),
                '-d', str(self.base_dir)
            ],
            'RunAtLoad': True,
            'KeepAlive': True,
            'StandardOutPath': str(self.base_dir / f"{service_name}.log"),
            'StandardErrorPath': str(self.base_dir / f"{service_name}.error.log"),
            'WorkingDirectory': str(self.base_dir)
        }
        
        plist_file = self.launch_agents_dir / f"com.proxypool.{service_name}.plist"
        
        # 写入plist文件
        with open(plist_file, 'w') as f:
            # 手动构建plist格式
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n')
            f.write('<plist version="1.0">\n<dict>\n')
            
            for key, value in plist_content.items():
                f.write(f'    <key>{key}</key>\n')
                if isinstance(value, str):
                    f.write(f'    <string>{value}</string>\n')
                elif isinstance(value, bool):
                    f.write(f'    <{str(value).lower()}/>\n')
                elif isinstance(value, list):
                    f.write('    <array>\n')
                    for item in value:
                        f.write(f'        <string>{item}</string>\n')
                    f.write('    </array>\n')
            
            f.write('</dict>\n</plist>\n')
        
        print(f"✓ 创建LaunchAgent: {plist_file}")
        return str(plist_file)
    
    def start_service(self, service_name):
        """启动服务"""
        try:
            subprocess.run(['launchctl', 'load', '-w', 
                          str(self.launch_agents_dir / f"com.proxypool.{service_name}.plist")],
                         check=True)
            print(f"✓ 启动服务: {service_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 启动服务失败: {e}")
            return False
    
    def stop_service(self, service_name):
        """停止服务"""
        try:
            subprocess.run(['launchctl', 'unload', 
                          str(self.launch_agents_dir / f"com.proxypool.{service_name}.plist")],
                         check=True)
            print(f"✓ 停止服务: {service_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 停止服务失败: {e}")
            return False
    
    def setup_proxy_pool(self, num_instances=5):
        """设置多个代理池实例"""
        print(f"=== MacOS代理池设置 ===")
        print(f"基础目录: {self.base_dir}")
        print()
        
        # 检查mihomo
        mihomo_path = self.check_mihomo()
        if not mihomo_path:
            return False
        
        # 检查代理文件
        proxy_files = list(self.providers_dir.glob("*.yaml"))
        if not proxy_files:
            print(f"⚠ 在 {self.providers_dir} 中未找到代理文件")
            print("请先运行 tiqu.py 生成代理配置")
            return False
        
        print(f"找到 {len(proxy_files)} 个代理文件")
        print()
        
        # 生成配置和服务
        base_http_port = 7890
        base_socks_port = 7891  
        base_controller_port = 9090
        base_dns_port = 1076
        
        for i in range(min(num_instances, len(proxy_files))):
            service_name = f"proxy{i+1}"
            provider_file = proxy_files[i].name
            
            # 计算端口
            http_port = base_http_port + i * 10
            socks_port = base_socks_port + i * 10
            controller_port = base_controller_port + i
            dns_port = base_dns_port + i
            
            print(f"设置服务 {service_name}:")
            print(f"  HTTP端口: {http_port}")
            print(f"  SOCKS端口: {socks_port}")
            print(f"  控制面板: http://127.0.0.1:{controller_port}/ui")
            print(f"  代理文件: {provider_file}")
            
            # 生成配置
            config_file = self.generate_config(
                service_name, http_port, socks_port, 
                controller_port, dns_port, provider_file
            )
            
            # 创建LaunchAgent
            plist_file = self.create_launch_agent(service_name, config_file, mihomo_path)
            
            # 启动服务
            self.start_service(service_name)
            print()
        
        print("=== 设置完成 ===")
        print("代理池已在后台运行，配置信息:")
        print()
        for i in range(min(num_instances, len(proxy_files))):
            http_port = base_http_port + i * 10
            socks_port = base_socks_port + i * 10
            controller_port = base_controller_port + i
            print(f"代理 {i+1}:")
            print(f"  HTTP: 127.0.0.1:{http_port}")
            print(f"  SOCKS5: 127.0.0.1:{socks_port}")
            print(f"  控制面板: http://127.0.0.1:{controller_port}/ui")
            print()
        
        return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='MacOS代理池管理工具')
    parser.add_argument('--instances', type=int, default=5, help='创建的代理实例数量')
    parser.add_argument('--base-dir', help='基础目录路径')
    
    args = parser.parse_args()
    
    manager = MacOSProxyPoolManager(args.base_dir)
    success = manager.setup_proxy_pool(args.instances)
    
    if success:
        print("使用方法:")
        print("1. 在浏览器中设置HTTP代理: 127.0.0.1:7890")
        print("2. 或设置SOCKS5代理: 127.0.0.1:7891") 
        print("3. 访问控制面板管理: http://127.0.0.1:9090/ui")
        print()
        print("管理命令:")
        print("  启动所有: launchctl load -w ~/Library/LaunchAgents/com.proxypool.*.plist")
        print("  停止所有: launchctl unload ~/Library/LaunchAgents/com.proxypool.*.plist")
        print("  查看状态: launchctl list | grep com.proxypool")

if __name__ == "__main__":
    main() 