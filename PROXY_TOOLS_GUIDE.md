# 增强版代理池管理工具使用文档

## 工具概述

本项目提供两个强大的代理池管理工具：

- **`enhanced_proxy_manager.py`** - 增强版代理池管理器
- **`proxy_service_manager.py`** - 代理服务管理工具

## 功能特性

### 🚀 核心功能
- ✅ **智能端口检测** - 自动避开已占用端口（如Clash的7890）
- ✅ **代理有效性测试** - 并发测试所有代理节点的连通性
- ✅ **名称智能绑定** - 从代理配置中提取有意义的服务名
- ✅ **服务自动管理** - 基于macOS LaunchAgent的服务管理
- ✅ **浏览器集成** - 导出配置供浏览器插件使用

### 🎯 优势特点
- **与现有Clash共存** - 智能端口分配，互不冲突
- **代理质量保证** - 过滤无效节点，只使用可用代理
- **服务名语义化** - 如"香港标准_IEPL_中继_6"而非"proxy1"
- **完整生命周期管理** - 启动、停止、重启、监控

---

## 工具1: enhanced_proxy_manager.py

### 📖 功能说明

增强版代理池管理器，负责初始化和配置整个代理池系统。

### 🛠️ 基本用法

```bash
# 激活虚拟环境
source venv/bin/activate

# 基础使用 - 创建10个代理实例（默认）
python3 enhanced_proxy_manager.py

# 指定实例数量
python3 enhanced_proxy_manager.py --instances 5

# 跳过代理有效性测试（快速模式）
python3 enhanced_proxy_manager.py --no-test

# 指定自定义工作目录
python3 enhanced_proxy_manager.py --base-dir /path/to/custom/dir
```

### 📋 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--instances` | 10 | 创建的代理实例数量 |
| `--no-test` | False | 跳过代理有效性测试 |
| `--base-dir` | `~/proxy_pool` | 代理池工作目录 |

### 🔧 工作流程

1. **环境检查**
   - 验证mihomo是否存在
   - 检查代理文件目录

2. **代理测试**（可选）
   - 并发测试所有proxy_providers中的yaml文件
   - TCP连接测试验证代理可达性
   - 将有效代理复制到valid_providers目录

3. **端口分配**
   - 检测已占用端口（7890、1080等）
   - 智能分配可用端口段
   - 每个服务分配10个端口间隔（避免冲突，用户已优化）

4. **服务创建**
   - 根据代理名称生成服务名
   - 创建mihomo配置文件
   - 注册LaunchAgent服务
   - 自动启动服务

5. **信息保存**
   - 生成services.json配置文件
   - 保存所有服务信息供后续管理

### 📊 输出示例

```bash
🚀 增强版代理池设置
📁 工作目录: /Users/username/proxy_pool

🧪 开始测试 90 个代理文件...
✅ proxy_1_proxy_27.yaml: 连接成功 (ss)
✅ proxy_1_proxy_89.yaml: 连接成功 (ss)
...

📊 测试完成:
   ✅ 有效代理: 90
   ❌ 无效代理: 0

🔍 检测可用端口...
⚠️  检测到已占用端口: [7890]
✅ 将自动避开这些端口
✅ 找到 50 个可用端口 (起始: 8000)

🔧 开始创建 5 个代理服务...

📦 设置服务: proxy_01_香港标准_IEPL_中继_6
   📋 代理名称: 香港标准_IEPL_中继_6
   🌐 HTTP端口: 8000
   🧦 SOCKS端口: 8001
   🎛️  控制面板: http://127.0.0.1:8002/ui
   ✅ 服务启动成功

🎉 代理池设置完成!
📊 成功创建 5 个代理服务
📄 服务信息已保存到: /Users/username/proxy_pool/services.json
```

### 📁 目录结构

```
~/proxy_pool/
├── bin/
│   └── mihomo                 # mihomo可执行文件
├── config/
│   ├── proxy_01_香港标准_IEPL_中继_6.yaml
│   ├── proxy_02_埃及标准_IEPL_中继_1.yaml
│   └── ...                   # 各服务配置文件
├── proxy_providers/           # 原始代理文件
├── valid_providers/           # 验证有效的代理文件
├── services.json             # 服务信息文件
├── proxy_01_香港标准_IEPL_中继_6.log     # 服务日志
└── proxy_01_香港标准_IEPL_中继_6.error.log  # 错误日志
```

---

## 工具2: proxy_service_manager.py

### 📖 功能说明

代理服务管理工具，提供对已创建代理服务的完整生命周期管理。

### 🛠️ 基本用法

#### 查看服务状态
```bash
# 列出所有代理服务及其状态
python3 proxy_service_manager.py list
```

#### 服务控制
```bash
# 启动所有服务
python3 proxy_service_manager.py start

# 停止所有服务
python3 proxy_service_manager.py stop

# 重启所有服务
python3 proxy_service_manager.py restart

# 管理单个服务（支持服务名或代理名）
python3 proxy_service_manager.py start "香港标准_IEPL_中继_6"
python3 proxy_service_manager.py stop proxy_01
python3 proxy_service_manager.py restart "美国标准_IEPL_中继_2"
```

#### 日志查看
```bash
# 查看所有服务的错误日志
python3 proxy_service_manager.py logs

# 查看特定服务日志
python3 proxy_service_manager.py logs "香港标准_IEPL_中继_6"

# 指定显示行数
python3 proxy_service_manager.py logs "香港标准_IEPL_中继_6" --lines 100
```

#### 配置导出
```bash
# 导出浏览器代理配置
python3 proxy_service_manager.py export
```

### 📋 命令参考

| 命令 | 语法 | 说明 |
|------|------|------|
| `list` | `list` | 显示所有服务状态 |
| `start` | `start [service]` | 启动服务（全部或指定） |
| `stop` | `stop [service]` | 停止服务（全部或指定） |
| `restart` | `restart [service]` | 重启服务（全部或指定） |
| `logs` | `logs [service] [--lines N]` | 查看日志 |
| `export` | `export` | 导出浏览器配置 |

### 🎛️ 通用参数

```bash
# 指定自定义工作目录
python3 proxy_service_manager.py --base-dir /path/to/custom/dir list
```

### 📊 输出示例

#### 服务列表
```bash
$ python3 proxy_service_manager.py list

📋 代理服务列表:
================================================================================
🟢 香港标准_IEPL_中继_6
   服务名: proxy_01_香港标准_IEPL_中继_6
   状态: 运行中 (87459)
   HTTP: 127.0.0.1:8000
   SOCKS5: 127.0.0.1:8001
   控制面板: http://127.0.0.1:8002/ui

🟢 埃及标准_IEPL_中继_1
   服务名: proxy_02_埃及标准_IEPL_中继_1
   状态: 运行中 (87461)
   HTTP: 127.0.0.1:8010
   SOCKS5: 127.0.0.1:8011
   控制面板: http://127.0.0.1:8012/ui
```

#### 服务操作
```bash
$ python3 proxy_service_manager.py restart

🔄 重启所有代理服务...
✅ 香港标准_IEPL_中继_6: 重启成功
✅ 埃及标准_IEPL_中继_1: 重启成功
✅ 台湾标准_IEPL_中继_1: 重启成功

📊 重启完成: 3/3 个服务
```

---

## 🌐 浏览器配置指南

### SwitchyOmega插件配置

1. **安装插件**
   - Chrome: [SwitchyOmega](https://chrome.google.com/webstore/detail/padekgcemlokbadohgkifijomclgjgif)

2. **导入配置**
   ```bash
   # 生成配置文件
   python3 proxy_service_manager.py export
   ```
   
3. **手动配置**
   - 新建情景模式 → 代理服务器
   - 代理协议：HTTP
   - 代理服务器：127.0.0.1
   - 代理端口：8000（第一个代理）

### 端口分配表

| 服务序号 | 代理名称示例 | HTTP端口 | SOCKS5端口 | 控制面板 |
|----------|--------------|----------|------------|----------|
| 1 | 香港标准_IEPL_中继_6 | 8000 | 8001 | :8002/ui |
| 2 | 埃及标准_IEPL_中继_1 | 8010 | 8011 | :8012/ui |
| 3 | 台湾标准_IEPL_中继_1 | 8020 | 8021 | :8022/ui |
| 4 | 美国标准_IEPL_中继_2 | 8030 | 8031 | :8032/ui |
| 5 | 日本标准_IEPL_中继_2 | 8040 | 8041 | :8042/ui |

---

## 🔧 高级使用技巧

### 1. 批量代理测试

```bash
# 快速创建大量实例（跳过测试）
python3 enhanced_proxy_manager.py --instances 20 --no-test

# 仅测试模式（不创建服务）
python3 enhanced_proxy_manager.py --instances 0
```

### 2. 服务名称模糊匹配

```bash
# 支持部分匹配
python3 proxy_service_manager.py start "香港"
python3 proxy_service_manager.py stop "proxy_01"
python3 proxy_service_manager.py restart "美国"
```

### 3. 日志监控

```bash
# 实时监控日志
tail -f ~/proxy_pool/proxy_01_*.log

# 错误日志检查
python3 proxy_service_manager.py logs
```

### 4. 服务重建

```bash
# 停止所有服务
python3 proxy_service_manager.py stop

# 重新创建（会覆盖现有配置）
python3 enhanced_proxy_manager.py --instances 10
```

---

## 🛠️ 故障排除

### 常见问题

#### 1. 端口冲突
**症状**: 服务启动失败，提示端口被占用
```bash
# 检查端口占用
lsof -i :8000

# 修改起始端口
# 编辑enhanced_proxy_manager.py中的start_port参数
```

#### 2. 代理连接失败
**症状**: 浏览器无法通过代理访问网站
```bash
# 检查服务状态
python3 proxy_service_manager.py list

# 查看服务日志
python3 proxy_service_manager.py logs "服务名"

# 重启服务
python3 proxy_service_manager.py restart "服务名"
```

#### 3. mihomo未找到
**症状**: `❌ mihomo未找到，请先运行基础安装脚本`
```bash
# 重新下载mihomo
curl -L -o ~/proxy_pool/bin/mihomo.gz "https://github.com/MetaCubeX/mihomo/releases/download/v1.19.11/mihomo-darwin-arm64-v1.19.11.gz"
cd ~/proxy_pool/bin && gunzip mihomo.gz && chmod +x mihomo
```

#### 4. 代理文件未找到
**症状**: `❌ 未找到代理文件`
```bash
# 检查代理文件目录
ls -la ~/proxy_pool/proxy_providers/

# 重新复制代理文件
cp -r proxy_providers ~/proxy_pool/
```

### 系统管理命令

```bash
# 查看所有代理服务状态
launchctl list | grep com.proxypool

# 手动启动/停止服务
launchctl load -w ~/Library/LaunchAgents/com.proxypool.proxy_01_*.plist
launchctl unload ~/Library/LaunchAgents/com.proxypool.proxy_01_*.plist

# 清理所有服务
launchctl unload ~/Library/LaunchAgents/com.proxypool.*.plist
rm ~/Library/LaunchAgents/com.proxypool.*.plist
```

---

## 📈 最佳实践

### 1. 代理池规模建议
- **轻度使用**: 3-5个代理实例
- **中度使用**: 10-15个代理实例  
- **重度使用**: 20-30个代理实例

### 2. 监控策略
- 定期检查服务状态：`python3 proxy_service_manager.py list`
- 关注错误日志：`python3 proxy_service_manager.py logs`
- 代理性能测试：访问控制面板查看延迟

### 3. 安全建议
- 代理仅监听本地地址（127.0.0.1）
- 定期更新mihomo版本
- 使用可信的机场服务
- 不要在公共网络暴露代理端口

### 4. 性能优化
- 根据实际需求调整实例数量
- 使用`--no-test`跳过测试加快部署
- 定期清理无效代理文件

---

## 📞 技术支持

### 文件位置
- 代理池目录: `/Users/username/proxy_pool/`
- 服务配置: `~/Library/LaunchAgents/com.proxypool.*.plist`

### 相关文档
- [mihomo官方文档](https://github.com/MetaCubeX/mihomo)
- [环境配置说明](config.example.env)

### 快速参考
```bash
# 完整部署流程
source venv/bin/activate
python3 enhanced_proxy_manager.py --instances 5
python3 proxy_service_manager.py list

# 日常管理
python3 proxy_service_manager.py list
python3 proxy_service_manager.py restart
python3 proxy_service_manager.py export
``` 