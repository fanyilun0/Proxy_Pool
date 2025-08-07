# 🚀 代理池管理工具 - 快速参考

## ⚡ 快速开始

```bash
# 1. 激活环境
source venv/bin/activate

# 2. 创建代理池（默认开启所有代理实例）
python3 enhanced_proxy_manager.py

# 3. 查看服务状态
python3 proxy_service_manager.py list
```

---

## 📋 常用命令

### enhanced_proxy_manager.py (初始化)

```bash
# 基础创建（开启所有代理实例）
python3 enhanced_proxy_manager.py

# 指定实例数量限制
python3 enhanced_proxy_manager.py --instances 5

# 快速模式（跳过测试，开启所有实例）
python3 enhanced_proxy_manager.py --no-test
```

### proxy_service_manager.py (管理)

```bash
# 查看状态
python3 proxy_service_manager.py list

# 服务控制
python3 proxy_service_manager.py start    # 启动全部
python3 proxy_service_manager.py stop     # 停止全部  
python3 proxy_service_manager.py restart  # 重启全部

# 单个服务
python3 proxy_service_manager.py start "香港标准_IEPL_中继_6"
python3 proxy_service_manager.py stop proxy_01

# 日志查看
python3 proxy_service_manager.py logs
python3 proxy_service_manager.py logs "服务名" --lines 50

# 导出配置
python3 proxy_service_manager.py export
```

---

## 🌐 端口配置

| 服务 | HTTP端口 | SOCKS5端口 | 控制面板 |
|------|----------|------------|----------|
| 代理1 | 8000 | 8001 | :8002/ui |
| 代理2 | 8010 | 8011 | :8012/ui |
| 代理3 | 8020 | 8021 | :8022/ui |
| 代理4 | 8030 | 8031 | :8032/ui |
| 代理5 | 8040 | 8041 | :8042/ui |

---

## 🔧 故障排除

```bash
# 检查端口占用
lsof -i :8000

# 查看所有代理服务
launchctl list | grep com.proxypool

# 手动停止所有服务
launchctl unload ~/Library/LaunchAgents/com.proxypool.*.plist

# 检查mihomo
ls -la ~/proxy_pool/bin/mihomo

# 测试代理连接
curl -x http://127.0.0.1:8000 http://httpbin.org/ip
```

---

## 📁 重要文件位置

```
~/proxy_pool/
├── services.json           # 服务配置信息
├── bin/mihomo              # 代理核心程序
├── config/                 # 各服务配置文件
├── valid_providers/        # 有效代理文件
└── *.log                   # 服务日志文件

~/Library/LaunchAgents/
└── com.proxypool.*.plist   # 系统服务文件
```

---

## 🌍 浏览器设置

### Chrome + SwitchyOmega
1. 安装插件：[SwitchyOmega](https://chrome.google.com/webstore/detail/padekgcemlokbadohgkifijomclgjgif)
2. 新建代理服务器：HTTP, 127.0.0.1:8000
3. 或导入配置：`python3 proxy_service_manager.py export`

### 手动设置
- HTTP代理：127.0.0.1:8000
- SOCKS5代理：127.0.0.1:8001

---

## ⚠️ 注意事项

- ✅ 与Clash App完全兼容（自动避开7890端口）
- ✅ 服务名基于代理地区/名称，便于识别
- ✅ 支持部分匹配服务名进行管理
- ⚠️ 确保在虚拟环境中运行Python脚本
- ⚠️ 端口间隔为10，避免冲突

---

## 🎯 使用场景

### 多浏览器隔离
```
Chrome 1  → 香港代理 (8000)
Chrome 2  → 美国代理 (8010)  
Safari    → 日本代理 (8020)
```

### 任务分配
```
爬虫任务  → 台湾代理
流媒体    → 美国代理
常规浏览  → 香港代理
```

## 🔧 高级使用技巧

### 1. 批量代理测试

```bash
# 快速创建所有实例（跳过测试）
python3 enhanced_proxy_manager.py --no-test

# 限制创建数量（如只开启5个）
python3 enhanced_proxy_manager.py --instances 5

# 仅测试模式（不创建服务）
python3 enhanced_proxy_manager.py --instances 0
```

## 📈 最佳实践

### 1. 代理池规模建议
- **轻度使用**: 建议限制为3-5个代理实例 (--instances 5)
- **中度使用**: 建议限制为10-15个代理实例 (--instances 15)
- **重度使用**: 可使用全部代理实例（默认）或限制数量 (--instances 30)

### 快速参考
```bash
# 完整部署流程
source venv/bin/activate
python3 enhanced_proxy_manager.py  # 默认开启所有代理实例
python3 proxy_service_manager.py list

# 日常管理
python3 proxy_service_manager.py list
python3 proxy_service_manager.py restart
python3 proxy_service_manager.py export
``` 