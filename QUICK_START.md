# Proxy Pool 快速指南

## 概述

本代理池系统是一个基于 mihomo 代理内核的自动化管理工具，可以在 macOS 系统上轻松部署和管理多个代理实例。系统具有以下特点：

- 自动检测并避开已占用端口
- 测试代理有效性并过滤无效节点
- 为每个代理创建独立的系统服务
- 提供完整的服务管理功能
- 支持HTTP和SOCKS5代理模式

## 文件说明

该系统由以下几个关键文件组成：

1. **setup_proxy_pool.sh**：
   - 基础安装和初始化脚本
   - 负责创建目录结构、安装依赖、下载mihomo内核等
   - 设置代理提取和生成服务配置

2. **enhanced_proxy_manager.py**：
   - 代理池的核心管理工具
   - 自动分配端口、测试代理有效性
   - 生成服务配置、创建系统服务
   - 提供代理池的设置和管理功能

3. **proxy_service_manager.py**：
   - 代理服务的管理工具
   - 提供启动、停止、重启单个或所有服务的功能
   - 查看服务状态和日志
   - 导出代理配置

4. **stop_mihomo.sh**：
   - 一键停止所有mihomo相关服务
   - 清理系统中已注册的服务和进程

5. **check_port_used.sh**：
   - 检查代理服务使用的端口情况
   - 显示HTTP、SOCKS5、控制面板和DNS端口
   - 帮助排查端口冲突问题

## 端口说明

每个代理服务使用4个端口：

- **HTTP端口**：用于HTTP代理访问
- **SOCKS5端口**：用于SOCKS5代理访问（通常是HTTP端口+1）
- **控制面板端口**：用于访问Web控制界面（通常是HTTP端口+2）
- **DNS端口**：用于DNS解析（通常是控制面板端口+1000）

## 使用指南

### 初始安装

1. 下载或克隆代码库到本地目录

2. 执行安装脚本：
   ```bash
   chmod +x setup_proxy_pool.sh
   ./setup_proxy_pool.sh
   ```

3. 按照提示输入您的代理订阅链接
   - 如果您没有输入，将使用示例链接，您可以稍后在`tiqu.py`中修改

4. 设置代理池：
   - 设置起始端口（默认为9000）
   - 选择是否限制代理实例数量
   - 系统会自动检测端口可用性并配置服务

### 服务管理

使用`proxy_service_manager.py`管理代理服务：

1. 查看所有服务状态：
   ```bash
   python3 proxy_service_manager.py list
   ```

2. 启动所有服务：
   ```bash
   python3 proxy_service_manager.py start
   ```

3. 停止所有服务：
   ```bash
   python3 proxy_service_manager.py stop
   ```

4. 重启所有服务：
   ```bash
   python3 proxy_service_manager.py restart
   ```

5. 管理单个服务（使用服务名或代理名称）：
   ```bash
   python3 proxy_service_manager.py start 服务名
   python3 proxy_service_manager.py stop 服务名
   python3 proxy_service_manager.py restart 服务名
   ```

6. 查看服务日志：
   ```bash
   python3 proxy_service_manager.py logs [服务名]
   ```

7. 导出浏览器代理配置：
   ```bash
   python3 proxy_service_manager.py export
   ```

### 端口检查

查看代理服务的端口使用情况：

```bash
./check_port_used.sh
```

高级选项：
```bash
./check_port_used.sh -p 9000 -c 20   # 检查从9000开始的20个服务端口
./check_port_used.sh -r              # 使用端口范围扫描模式
```

### 一键停止

如需快速停止所有代理服务：

```bash
./stop_mihomo.sh
```

## 更新代理列表

当您需要更新代理列表时：

1. 修改`tiqu.py`中的订阅链接
2. 运行代理提取：
   ```bash
   python3 tiqu.py
   ```
3. 重新设置代理池：
   ```bash
   python3 enhanced_proxy_manager.py --start-port 9000
   ```

## 高级选项

### enhanced_proxy_manager.py 参数

```bash
python3 enhanced_proxy_manager.py [选项]

选项:
  --instances 数量    限制代理实例数量
  --no-test          跳过代理有效性测试
  --base-dir 路径     指定基础目录
  --start-port 端口   设置起始端口号(默认9000)
  --debug            显示调试信息
```

### proxy_service_manager.py 命令

```
python3 proxy_service_manager.py [命令] [选项]

命令:
  list                列出所有代理服务
  start [服务名]       启动服务
  stop [服务名]        停止服务
  restart [服务名]     重启服务
  logs [服务名]        查看服务日志
  export              导出浏览器代理配置
```

## 常见问题

1. **服务无法启动**
   - 检查端口是否已被占用：`./check_port_used.sh`
   - 查看错误日志：`python3 proxy_service_manager.py logs`

2. **端口冲突**
   - 使用不同的起始端口：`python3 enhanced_proxy_manager.py --start-port 10000`

3. **服务意外停止**
   - 检查日志文件：`python3 proxy_service_manager.py logs`
   - 重启服务：`python3 proxy_service_manager.py restart`

4. **如何完全卸载**
   - 先停止所有服务：`./stop_mihomo.sh`
   - 然后删除整个目录

---

祝您使用愉快！如有问题，请查阅完整文档或提交问题。
