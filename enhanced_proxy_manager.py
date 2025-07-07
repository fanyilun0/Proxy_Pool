#!/usr/bin/env python3
"""
增强版代理池管理器
功能：
1. 自动检测并避开已占用端口
2. 测试代理有效性并过滤无效节点
3. 根据代理名称创建有意义的服务名
4. 提供完整的服务管理功能
"""

import os
import yaml
import json
import socket
import requests
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

class EnhancedProxyManager:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or Path.home() / "proxy_pool")
        self.config_dir = self.base_dir / "config"
        self.bin_dir = self.base_dir / "bin"
        self.providers_dir = self.base_dir / "proxy_providers"
        self.valid_dir = self.base_dir / "valid_providers"
        self.launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        
        # 创建目录
        for dir_path in [self.config_dir, self.bin_dir, self.providers_dir, self.valid_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def check_port_available(self, port):
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                return result != 0
        except:
            return False
    
    def find_available_ports(self, start_port=8000, count=50):
        """找到可用的端口段，避开已占用的端口"""
        available_ports = []
        port = start_port
        
        print("🔍 检测可用端口...")
        
        # 检查常见代理端口占用情况
        common_ports = [7890, 7891, 1080, 1081, 8080, 8081]
        occupied_ports = []
        for p in common_ports:
            if not self.check_port_available(p):
                occupied_ports.append(p)
        
        if occupied_ports:
            print(f"⚠️  检测到已占用端口: {occupied_ports}")
            print("✅ 将自动避开这些端口")
        
        while len(available_ports) < count * 10:  # 每服务10个端口间隔
            if self.check_port_available(port):
                available_ports.append(port)
            port += 1
            
            if port > start_port + 1000:  # 防止无限循环
                break
        
        print(f"✅ 找到 {len(available_ports)} 个可用端口 (起始: {available_ports[0]})")
        return available_ports
    
    def test_proxy_connection(self, proxy_config, timeout=10):
        """测试代理连接有效性"""
        try:
            # 解析代理配置
            if 'proxies' not in proxy_config or not proxy_config['proxies']:
                return False, "配置格式错误"
            
            proxy = proxy_config['proxies'][0]
            proxy_type = proxy.get('type', '').lower()
            server = proxy.get('server', '')
            port = proxy.get('port', 0)
            
            if not server or not port:
                return False, "缺少服务器或端口信息"
            
            # 尝试TCP连接测试
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(timeout)
                    result = s.connect_ex((server, int(port)))
                    if result == 0:
                        return True, f"连接成功 ({proxy_type})"
                    else:
                        return False, f"连接失败 ({proxy_type})"
            except Exception as e:
                return False, f"连接错误: {str(e)}"
                
        except Exception as e:
            return False, f"配置解析错误: {str(e)}"
    
    def validate_proxy_files(self, max_workers=10):
        """并发测试所有代理文件的有效性"""
        proxy_files = list(self.providers_dir.glob("*.yaml"))
        if not proxy_files:
            print("❌ 未找到代理文件")
            return []
        
        print(f"🧪 开始测试 {len(proxy_files)} 个代理文件...")
        valid_proxies = []
        invalid_proxies = []
        
        def test_single_proxy(proxy_file):
            try:
                with open(proxy_file, 'r', encoding='utf-8') as f:
                    proxy_config = yaml.safe_load(f)
                
                is_valid, message = self.test_proxy_connection(proxy_config, timeout=5)
                return proxy_file, is_valid, message, proxy_config
            except Exception as e:
                return proxy_file, False, f"文件读取错误: {str(e)}", None
        
        # 并发测试
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(test_single_proxy, pf): pf for pf in proxy_files}
            
            for future in as_completed(future_to_file):
                proxy_file, is_valid, message, proxy_config = future.result()
                
                if is_valid and proxy_config:
                    # 复制有效代理到valid_providers目录
                    new_file = self.valid_dir / proxy_file.name
                    with open(new_file, 'w', encoding='utf-8') as f:
                        yaml.dump(proxy_config, f, allow_unicode=True, default_flow_style=False)
                    
                    valid_proxies.append((new_file, proxy_config))
                    print(f"✅ {proxy_file.name}: {message}")
                else:
                    invalid_proxies.append((proxy_file, message))
                    print(f"❌ {proxy_file.name}: {message}")
        
        print(f"\n📊 测试完成:")
        print(f"   ✅ 有效代理: {len(valid_proxies)}")
        print(f"   ❌ 无效代理: {len(invalid_proxies)}")
        
        # 询问是否删除无效文件
        if invalid_proxies:
            print(f"\n🗑️  发现 {len(invalid_proxies)} 个无效代理文件")
            response = input("是否删除无效文件? (y/N): ").strip().lower()
            if response == 'y':
                for invalid_file, _ in invalid_proxies:
                    try:
                        invalid_file.unlink()
                        print(f"🗑️  已删除: {invalid_file.name}")
                    except Exception as e:
                        print(f"⚠️  删除失败 {invalid_file.name}: {e}")
        
        return valid_proxies
    
    def extract_proxy_name(self, proxy_config):
        """从代理配置中提取有意义的名称"""
        try:
            proxy = proxy_config['proxies'][0]
            name = proxy.get('name', '')
            
            if name:
                # 清理名称，移除特殊字符
                import re
                # 保留中文、英文、数字和基本符号
                clean_name = re.sub(r'[^\w\s\-\u4e00-\u9fff]', '', name)
                # 替换空格为下划线，限制长度
                clean_name = re.sub(r'\s+', '_', clean_name.strip())[:30]
                return clean_name
            
            # 如果没有名称，使用服务器信息
            server = proxy.get('server', 'unknown')
            proxy_type = proxy.get('type', 'proxy')
            return f"{proxy_type}_{server}".replace('.', '_')[:30]
            
        except:
            return "proxy_unknown"
    
    def generate_service_config(self, service_name, proxy_name, http_port, socks_port, 
                              controller_port, dns_port, provider_file):
        """生成mihomo服务配置"""
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
                    'proxies': [proxy_name, 'DIRECT']
                },
                {
                    'name': proxy_name,
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
                    'path': str(self.valid_dir / provider_file),
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
        
        return str(config_file)
    
    def create_launch_agent(self, service_name, config_file, mihomo_path):
        """创建LaunchAgent服务"""
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
        
        with open(plist_file, 'w') as f:
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
        
        return str(plist_file)
    
    def manage_service(self, service_name, action):
        """管理服务：start, stop, restart"""
        plist_file = self.launch_agents_dir / f"com.proxypool.{service_name}.plist"
        
        try:
            if action == 'stop' or action == 'restart':
                subprocess.run(['launchctl', 'unload', str(plist_file)], 
                             check=False, capture_output=True)
            
            if action == 'start' or action == 'restart':
                subprocess.run(['launchctl', 'load', '-w', str(plist_file)], 
                             check=True, capture_output=True)
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def setup_enhanced_proxy_pool(self, max_instances=20, test_proxies=True):
        """设置增强版代理池"""
        print("🚀 增强版代理池设置")
        print(f"📁 工作目录: {self.base_dir}")
        print()
        
        # 检查mihomo
        mihomo_path = self.bin_dir / "mihomo"
        if not mihomo_path.exists():
            print("❌ mihomo未找到，请先运行基础安装脚本")
            return False
        
        # 验证代理文件
        if test_proxies:
            valid_proxies = self.validate_proxy_files()
        else:
            # 直接使用所有文件
            proxy_files = list(self.providers_dir.glob("*.yaml"))
            valid_proxies = []
            for pf in proxy_files:
                try:
                    with open(pf, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    valid_proxies.append((pf, config))
                except:
                    continue
        
        if not valid_proxies:
            print("❌ 没有可用的代理文件")
            return False
        
        # 限制实例数量
        valid_proxies = valid_proxies[:max_instances]
        
        # 获取可用端口
        available_ports = self.find_available_ports(count=len(valid_proxies))
        if len(available_ports) < len(valid_proxies) * 10:
            print("❌ 可用端口不足")
            return False
        
        print(f"\n🔧 开始创建 {len(valid_proxies)} 个代理服务...")
        
        # 创建服务配置表
        services_info = []
        
        for i, (proxy_file, proxy_config) in enumerate(valid_proxies):
            # 提取代理名称
            proxy_name = self.extract_proxy_name(proxy_config)
            service_name = f"proxy_{i+1:02d}_{proxy_name}"[:50]  # 限制长度
            
            # 分配端口
            http_port = available_ports[i * 10]
            socks_port = available_ports[i * 10 + 1] 
            controller_port = available_ports[i * 10 + 2]
            dns_port = controller_port + 1000  # DNS端口偏移
            
            print(f"\n📦 设置服务: {service_name}")
            print(f"   📋 代理名称: {proxy_name}")
            print(f"   🌐 HTTP端口: {http_port}")
            print(f"   🧦 SOCKS端口: {socks_port}")
            print(f"   🎛️  控制面板: http://127.0.0.1:{controller_port}/ui")
            
            # 生成配置
            config_file = self.generate_service_config(
                service_name, proxy_name, http_port, socks_port,
                controller_port, dns_port, proxy_file.name
            )
            
            # 创建服务
            plist_file = self.create_launch_agent(service_name, config_file, mihomo_path)
            
            # 启动服务
            if self.manage_service(service_name, 'start'):
                print(f"   ✅ 服务启动成功")
                services_info.append({
                    'service_name': service_name,
                    'proxy_name': proxy_name,
                    'http_port': http_port,
                    'socks_port': socks_port,
                    'controller_port': controller_port,
                    'controller_url': f"http://127.0.0.1:{controller_port}/ui"
                })
            else:
                print(f"   ❌ 服务启动失败")
        
        # 保存服务信息
        services_file = self.base_dir / "services.json"
        with open(services_file, 'w', encoding='utf-8') as f:
            json.dump(services_info, f, ensure_ascii=False, indent=2)
        
        # 显示汇总信息
        print(f"\n🎉 代理池设置完成!")
        print(f"📊 成功创建 {len(services_info)} 个代理服务")
        print(f"📄 服务信息已保存到: {services_file}")
        
        return services_info

def main():
    import argparse
    parser = argparse.ArgumentParser(description='增强版代理池管理器')
    parser.add_argument('--instances', type=int, default=10, help='最大代理实例数')
    parser.add_argument('--no-test', action='store_true', help='跳过代理有效性测试')
    parser.add_argument('--base-dir', help='基础目录路径')
    
    args = parser.parse_args()
    
    manager = EnhancedProxyManager(args.base_dir)
    services = manager.setup_enhanced_proxy_pool(
        max_instances=args.instances, 
        test_proxies=not args.no_test
    )
    
    if services:
        print("\n" + "="*60)
        print("📋 代理服务列表:")
        print("="*60)
        for service in services:
            print(f"🔹 {service['proxy_name']}")
            print(f"   HTTP: 127.0.0.1:{service['http_port']}")
            print(f"   SOCKS5: 127.0.0.1:{service['socks_port']}")
            print(f"   控制面板: {service['controller_url']}")
            print()
        
        print("🔧 管理命令:")
        print("   查看状态: launchctl list | grep com.proxypool")
        print("   停止所有: launchctl unload ~/Library/LaunchAgents/com.proxypool.*.plist")
        print("   启动所有: launchctl load -w ~/Library/LaunchAgents/com.proxypool.*.plist")

if __name__ == "__main__":
    main() 