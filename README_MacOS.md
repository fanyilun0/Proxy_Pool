# MacOS代理池搭建指南

本指南提供在MacOS系统上搭建代理池的完整解决方案。

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip3 install -r requirements.txt

# 创建配置文件
cp config.example.env .env
# 编辑.env文件，修改PROXY_URLS为你的机场链接
```

### 2. 提取代理配置

```bash
# 从机场链接提取代理配置
python3 tiqu.py
```

### 3. 设置MacOS代理池

```bash
# 自动设置代理池（创建5个代理实例）
python3 macos_setup.py

# 或指定实例数量
python3 macos_setup.py --instances 10
```

## 详细配置

### 环境变量配置(.env文件)

```env
# 机场订阅链接，多个链接用逗号分隔
PROXY_URLS=https://your-airport-url1,https://your-airport-url2

# 目录配置
OUTPUT_DIRECTORY=./
INPUT_DIRECTORY=./
PROXY_PROVIDERS_DIRECTORY=proxy_providers

# 请求配置
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

### 手动配置mihomo

如果需要手动配置：

1. 下载mihomo
```bash
# 创建目录
mkdir -p ~/proxy_pool/bin

# 下载适合你系统的版本
# Intel Mac: mihomo-darwin-amd64
# Apple Silicon Mac: mihomo-darwin-arm64
wget -O ~/proxy_pool/bin/mihomo https://github.com/MetaCubeX/mihomo/releases/download/v1.x.x/mihomo-darwin-amd64

# 添加执行权限
chmod +x ~/proxy_pool/bin/mihomo
```

2. 配置代理文件

代理文件会自动生成在`proxy_providers/`目录下，每个代理节点一个文件。

## 服务管理

### 自动管理（推荐）

```bash
# 查看服务状态
launchctl list | grep com.proxypool

# 启动所有代理服务
launchctl load -w ~/Library/LaunchAgents/com.proxypool.*.plist

# 停止所有代理服务
launchctl unload ~/Library/LaunchAgents/com.proxypool.*.plist

# 重启特定服务
launchctl unload ~/Library/LaunchAgents/com.proxypool.proxy1.plist
launchctl load -w ~/Library/LaunchAgents/com.proxypool.proxy1.plist
```

### 手动管理

```bash
# 进入代理池目录
cd ~/proxy_pool

# 启动单个mihomo实例
./bin/mihomo -f config/proxy1.yaml -d ~/proxy_pool
```

## 代理配置信息

默认端口配置：

| 服务名 | HTTP端口 | SOCKS5端口 | 控制面板 |
|--------|----------|------------|----------|
| proxy1 | 7890     | 7891       | http://127.0.0.1:9090/ui |
| proxy2 | 7900     | 7901       | http://127.0.0.1:9091/ui |
| proxy3 | 7910     | 7911       | http://127.0.0.1:9092/ui |
| proxy4 | 7920     | 7921       | http://127.0.0.1:9093/ui |
| proxy5 | 7930     | 7931       | http://127.0.0.1:9094/ui |

## 浏览器配置

### Chrome/Edge浏览器

1. 安装代理插件：[SwitchyOmega](https://chrome.google.com/webstore/detail/padekgcemlokbadohgkifijomclgjgif)

2. 创建代理配置：
   - 代理协议：HTTP
   - 代理服务器：127.0.0.1
   - 代理端口：7890 (第一个代理)

3. 为不同的浏览器实例配置不同的端口

### Safari

1. 系统偏好设置 → 网络 → 高级 → 代理
2. 选择"Web代理(HTTP)"
3. 输入：127.0.0.1:7890

## 故障排除

### 常见问题

1. **mihomo下载失败**
   - 手动从GitHub releases页面下载
   - 确保选择正确的架构版本

2. **端口冲突**
   - 检查端口是否被占用：`lsof -i :7890`
   - 修改配置文件中的端口号

3. **代理连接失败**
   - 检查机场链接是否有效
   - 查看mihomo日志：`tail -f ~/proxy_pool/proxy1.log`

4. **服务无法启动**
   - 检查权限：`chmod +x ~/proxy_pool/bin/mihomo`
   - 查看错误日志：`tail -f ~/proxy_pool/proxy1.error.log`

### 日志文件

- 服务日志：`~/proxy_pool/proxy1.log`
- 错误日志：`~/proxy_pool/proxy1.error.log`
- 系统日志：`tail -f /var/log/system.log | grep mihomo`

## 进阶配置

### 自定义规则

编辑配置文件`~/proxy_pool/config/proxy1.yaml`，在rules部分添加：

```yaml
rules:
  - DOMAIN-SUFFIX,apple.com,DIRECT
  - DOMAIN-SUFFIX,icloud.com,DIRECT
  - DOMAIN-KEYWORD,google,PROXY
  - GEOIP,CN,DIRECT
  - MATCH,PROXY
```

### 性能优化

1. 调整并发连接数
2. 配置DNS缓存
3. 启用连接复用

## 安全说明

1. 代理服务仅监听本地地址(127.0.0.1)
2. 定期更新mihomo版本
3. 使用可信的机场服务
4. 不要在公共网络上暴露代理端口

## 卸载

```bash
# 停止所有服务
launchctl unload ~/Library/LaunchAgents/com.proxypool.*.plist

# 删除LaunchAgent文件
rm ~/Library/LaunchAgents/com.proxypool.*.plist

# 删除代理池目录
rm -rf ~/proxy_pool
``` 