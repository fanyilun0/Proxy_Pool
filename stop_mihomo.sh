#!/bin/bash

# 停止所有mihomo相关服务的脚本
echo "🛑 开始停止所有mihomo代理服务..."

# 找到所有mihomo相关的LaunchAgent
launch_agents=$(ls ~/Library/LaunchAgents/com.proxypool.*.plist 2>/dev/null)

if [ -z "$launch_agents" ]; then
    echo "⚠️  未找到任何mihomo代理服务"
else
    # 卸载所有服务
    for agent in $launch_agents; do
        echo "正在卸载服务: $(basename $agent)"
        launchctl unload "$agent"
    done
    echo "✅ 所有服务已卸载"
fi

# 查找并终止所有mihomo进程
mihomo_pids=$(pgrep -f mihomo)
if [ -n "$mihomo_pids" ]; then
    echo "找到mihomo进程: $mihomo_pids"
    echo "正在终止mihomo进程..."
    kill -9 $mihomo_pids 2>/dev/null
    echo "✅ 所有mihomo进程已终止"
else
    echo "⚠️  未找到任何运行中的mihomo进程"
fi

# 查找并清理服务注册
registered_services=$(launchctl list | grep com.proxypool)
if [ -n "$registered_services" ]; then
    echo "找到已注册服务，正在清理..."
    launchctl list | grep com.proxypool | awk '{print $3}' | while read service; do
        echo "正在移除服务注册: $service"
        launchctl remove "$service" 2>/dev/null
    done
    echo "✅ 所有服务注册已清理"
fi

echo "🎉 清理完成！所有mihomo代理服务已停止"
