#!/bin/bash

# 1. 停止所有代理服务
echo "🛑 停止代理服务..."
python3 proxy_service_manager.py stop 2>/dev/null || echo "代理服务管理器未找到"

# 2. 卸载LaunchAgent服务
echo "🔧 卸载系统服务..."
launchctl unload ~/Library/LaunchAgents/com.proxypool.*.plist 2>/dev/null || echo "没有找到服务文件"

# 3. 强制杀死mihomo进程
echo "❌ 强制杀死mihomo进程..."
pkill -f mihomo 2>/dev/null || echo "没有找到mihomo进程"
pkill -9 -f mihomo 2>/dev/null || echo "没有找到mihomo进程"

# 4. 检查结果
echo "✅ 检查关闭结果..."
echo "📊 剩余服务:"
launchctl list | grep com.proxypool || echo "没有找到代理服务"

echo "📊 剩余进程:"
ps aux | grep mihomo | grep -v grep || echo "没有找到mihomo进程"

echo "📊 端口占用:"
lsof -i :7890 2>/dev/null || echo "端口7890未被占用"
lsof -i :8000 2>/dev/null || echo "端口8000未被占用"

echo "🎉 mihomo实例关闭完成！"
