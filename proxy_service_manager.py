#!/usr/bin/env python3
"""
代理服务管理工具
提供代理服务的启动、停止、重启、状态查看等功能
"""

import json
import subprocess
import sys
from pathlib import Path
import argparse

class ProxyServiceManager:
    def __init__(self, base_dir=None):
        # 如果没有提供base_dir，优先使用当前目录，而非用户主目录
        if base_dir is None:
            current_dir = Path(__file__).parent.absolute()
            self.base_dir = current_dir
        else:
            self.base_dir = Path(base_dir)
        self.services_file = self.base_dir / "services.json"
        self.logs_dir = self.base_dir / "logs"
        self.launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    
    def load_services(self):
        """加载服务信息"""
        if not self.services_file.exists():
            print("❌ 未找到服务信息文件，请先运行代理池设置")
            return []
        
        try:
            with open(self.services_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 读取服务信息失败: {e}")
            return []
    
    def get_service_status(self, service_name):
        """获取服务运行状态"""
        try:
            result = subprocess.run(
                ['launchctl', 'list'], 
                capture_output=True, text=True, check=True
            )
            
            for line in result.stdout.split('\n'):
                if f"com.proxypool.{service_name}" in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        pid = parts[0]
                        exit_code = parts[1]
                        if pid != '-':
                            return "运行中", pid
                        elif exit_code != '0':
                            return "已停止(错误)", exit_code
                        else:
                            return "已停止", "0"
            
            return "未注册", "-"
        except:
            return "未知", "-"
    
    def manage_service(self, service_name, action):
        """管理单个服务"""
        plist_file = self.launch_agents_dir / f"com.proxypool.{service_name}.plist"
        
        if not plist_file.exists():
            return False, f"服务文件不存在: {plist_file}"
        
        try:
            if action in ['stop', 'restart']:
                subprocess.run(
                    ['launchctl', 'unload', str(plist_file)], 
                    check=False, capture_output=True
                )
            
            if action in ['start', 'restart']:
                result = subprocess.run(
                    ['launchctl', 'load', '-w', str(plist_file)], 
                    check=True, capture_output=True, text=True
                )
            
            return True, f"操作成功: {action}"
        except subprocess.CalledProcessError as e:
            return False, f"操作失败: {e.stderr}"
    
    def list_services(self):
        """列出所有代理服务"""
        services = self.load_services()
        if not services:
            return
        
        print("📋 代理服务列表:")
        print("=" * 80)
        
        for service in services:
            status, info = self.get_service_status(service['service_name'])
            status_icon = "🟢" if status == "运行中" else "🔴" if "错误" in status else "⚪"
            
            print(f"{status_icon} {service['proxy_name']}")
            print(f"   服务名: {service['service_name']}")
            print(f"   状态: {status} ({info})")
            print(f"   HTTP: 127.0.0.1:{service['http_port']}")
            print(f"   SOCKS5: 127.0.0.1:{service['socks_port']}")
            print(f"   控制面板: {service['controller_url']}")
            print()
    
    def start_all(self):
        """启动所有服务"""
        services = self.load_services()
        if not services:
            return
        
        print("🚀 启动所有代理服务...")
        success_count = 0
        
        for service in services:
            success, message = self.manage_service(service['service_name'], 'start')
            if success:
                print(f"✅ {service['proxy_name']}: 启动成功")
                success_count += 1
            else:
                print(f"❌ {service['proxy_name']}: {message}")
        
        print(f"\n📊 启动完成: {success_count}/{len(services)} 个服务")
    
    def stop_all(self):
        """停止所有服务"""
        services = self.load_services()
        if not services:
            return
        
        print("🛑 停止所有代理服务...")
        success_count = 0
        
        for service in services:
            success, message = self.manage_service(service['service_name'], 'stop')
            if success:
                print(f"✅ {service['proxy_name']}: 停止成功")
                success_count += 1
            else:
                print(f"❌ {service['proxy_name']}: {message}")
        
        # 额外的清理步骤
        print("\n🧹 执行额外清理...")
        
        # 强制杀死可能残留的mihomo进程
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'mihomo'], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                print(f"找到残留mihomo进程: {pids}")
                for pid in pids:
                    subprocess.run(['kill', '-9', pid], check=False)
                    print(f"已杀死进程: {pid}")
        except Exception as e:
            print(f"清理进程时出错: {e}")
        
        # 清理LaunchAgent注册
        try:
            result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'com.proxypool' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        service_id = parts[2]
                        subprocess.run(['launchctl', 'remove', service_id], check=False)
                        print(f"已清理服务注册: {service_id}")
        except Exception as e:
            print(f"清理服务注册时出错: {e}")
        
        print(f"\n📊 停止完成: {success_count}/{len(services)} 个服务")
    
    def restart_all(self):
        """重启所有服务"""
        services = self.load_services()
        if not services:
            return
        
        print("🔄 重启所有代理服务...")
        success_count = 0
        
        for service in services:
            success, message = self.manage_service(service['service_name'], 'restart')
            if success:
                print(f"✅ {service['proxy_name']}: 重启成功")
                success_count += 1
            else:
                print(f"❌ {service['proxy_name']}: {message}")
        
        print(f"\n📊 重启完成: {success_count}/{len(services)} 个服务")
    
    def manage_single(self, service_name, action):
        """管理单个服务"""
        services = self.load_services()
        service = None
        
        # 查找服务
        for s in services:
            if (s['service_name'] == service_name or 
                s['proxy_name'] == service_name or
                service_name in s['service_name']):
                service = s
                break
        
        if not service:
            print(f"❌ 未找到服务: {service_name}")
            print("可用服务:")
            for s in services:
                print(f"  - {s['service_name']} ({s['proxy_name']})")
            return
        
        success, message = self.manage_service(service['service_name'], action)
        if success:
            print(f"✅ {service['proxy_name']}: {action} 成功")
        else:
            print(f"❌ {service['proxy_name']}: {message}")
    
    def show_logs(self, service_name=None, lines=50):
        """显示服务日志"""
        services = self.load_services()
        
        if service_name:
            # 显示特定服务日志
            service = None
            for s in services:
                if (s['service_name'] == service_name or 
                    s['proxy_name'] == service_name or
                    service_name in s['service_name']):
                    service = s
                    break
            
            if not service:
                print(f"❌ 未找到服务: {service_name}")
                return
            
            log_file = self.logs_dir / f"{service['service_name']}.log"
            error_log_file = self.logs_dir / f"{service['service_name']}.error.log"
            
            print(f"📜 {service['proxy_name']} 日志:")
            print("=" * 60)
            
            if log_file.exists():
                try:
                    subprocess.run(['tail', '-n', str(lines), str(log_file)])
                except:
                    print("❌ 无法读取日志文件")
            else:
                print("❌ 日志文件不存在")
            
            if error_log_file.exists() and error_log_file.stat().st_size > 0:
                print(f"\n🚨 错误日志:")
                print("=" * 60)
                try:
                    subprocess.run(['tail', '-n', str(lines), str(error_log_file)])
                except:
                    print("❌ 无法读取错误日志文件")
        else:
            # 显示所有服务的错误日志
            print("🚨 所有服务错误日志:")
            print("=" * 60)
            
            for service in services:
                error_log_file = self.logs_dir / f"{service['service_name']}.error.log"
                if error_log_file.exists() and error_log_file.stat().st_size > 0:
                    print(f"\n--- {service['proxy_name']} ---")
                    try:
                        subprocess.run(['tail', '-n', '10', str(error_log_file)])
                    except:
                        print("❌ 无法读取错误日志")
    
    def export_config(self):
        """导出代理配置供浏览器插件使用"""
        services = self.load_services()
        if not services:
            return
        
        config_data = {
            "profiles": []
        }
        
        for service in services:
            profile = {
                "name": service['proxy_name'],
                "type": "fixed_servers",
                "servers": {
                    "scheme": "http",
                    "host": "127.0.0.1",
                    "port": service['http_port']
                }
            }
            config_data["profiles"].append(profile)
        
        export_file = self.base_dir / "browser_proxy_config.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        print(f"📋 代理配置已导出到: {export_file}")
        print("可以导入到浏览器代理插件中使用")

def main():
    parser = argparse.ArgumentParser(description='代理服务管理工具')
    parser.add_argument('--base-dir', help='代理池基础目录')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 列出服务
    subparsers.add_parser('list', help='列出所有代理服务')
    
    # 启动服务
    start_parser = subparsers.add_parser('start', help='启动服务')
    start_parser.add_argument('service', nargs='?', help='服务名称(可选，不指定则启动全部)')
    
    # 停止服务
    stop_parser = subparsers.add_parser('stop', help='停止服务')
    stop_parser.add_argument('service', nargs='?', help='服务名称(可选，不指定则停止全部)')
    
    # 重启服务
    restart_parser = subparsers.add_parser('restart', help='重启服务')
    restart_parser.add_argument('service', nargs='?', help='服务名称(可选，不指定则重启全部)')
    
    # 查看日志
    logs_parser = subparsers.add_parser('logs', help='查看服务日志')
    logs_parser.add_argument('service', nargs='?', help='服务名称(可选)')
    logs_parser.add_argument('--lines', type=int, default=50, help='显示行数')
    
    # 导出配置
    subparsers.add_parser('export', help='导出浏览器代理配置')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ProxyServiceManager(args.base_dir)
    
    if args.command == 'list':
        manager.list_services()
    elif args.command == 'start':
        if args.service:
            manager.manage_single(args.service, 'start')
        else:
            manager.start_all()
    elif args.command == 'stop':
        if args.service:
            manager.manage_single(args.service, 'stop')
        else:
            manager.stop_all()
    elif args.command == 'restart':
        if args.service:
            manager.manage_single(args.service, 'restart')
        else:
            manager.restart_all()
    elif args.command == 'logs':
        manager.show_logs(args.service, args.lines)
    elif args.command == 'export':
        manager.export_config()

if __name__ == "__main__":
    main() 