#!/bin/bash

# MacOS代理池安装和启动脚本
# 作者: Proxy_Pool
# 用途: 在当前目录下安装和启动代理池服务

set -e

# 定义颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 打印带颜色的信息
info() {
  echo -e "${BLUE}[信息]${NC} $1"
}

success() {
  echo -e "${GREEN}[成功]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[警告]${NC} $1"
}

error() {
  echo -e "${RED}[错误]${NC} $1"
}

# 获取当前目录的绝对路径
CURRENT_DIR=$(pwd)
BASE_DIR="${CURRENT_DIR}"

# 设置目录结构
DIRS=(
  "${BASE_DIR}/bin"
  "${BASE_DIR}/config"
  "${BASE_DIR}/proxy_providers"
  "${BASE_DIR}/valid_providers"
  "${BASE_DIR}/logs"
)

# 创建所需目录
create_directories() {
  info "创建目录结构..."
  for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
  done
  success "目录结构创建完成"
}

# 检查是否安装了必要的工具
check_requirements() {
  info "检查必要工具..."
  
  # 检查Python3
  if ! command -v python3 &> /dev/null; then
    error "未找到Python3，请安装Python3后重试"
    exit 1
  fi
  
  # 检查pip3
  if ! command -v pip3 &> /dev/null; then
    warn "未找到pip3，尝试安装..."
    python3 -m ensurepip || {
      error "pip3安装失败，请手动安装pip3后重试"
      exit 1
    }
  fi
  
  # 检查wget或curl
  if ! command -v wget &> /dev/null && ! command -v curl &> /dev/null; then
    error "未找到wget或curl，请安装wget或curl后重试"
    exit 1
  fi
  
  success "所需工具检查完成"
}

# 安装Python依赖
install_dependencies() {
  info "安装Python依赖..."
  pip3 install PyYAML requests --quiet
  success "Python依赖安装完成"
}

# 下载mihomo
download_mihomo() {
  info "下载mihomo代理内核..."
  local mihomo_path="${BASE_DIR}/bin/mihomo"
  local arch=$(uname -m)
  local download_url=""
  
  # 根据架构选择不同的下载URL
  if [[ "$arch" == "arm64" ]]; then
    download_url="https://github.com/MetaCubeX/mihomo/releases/download/Prerelease-Alpha/mihomo-darwin-arm64-alpha-e89af72.gz"
  elif [[ "$arch" == "x86_64" ]]; then
    download_url="https://github.com/MetaCubeX/mihomo/releases/download/Prerelease-Alpha/mihomo-darwin-amd64-alpha-e89af72.gz"
  else
    error "不支持的架构: $arch"
    exit 1
  fi
  
  # 使用wget或curl下载
  if command -v wget &> /dev/null; then
    wget -O "${mihomo_path}.gz" "$download_url" || {
      error "下载mihomo失败"
      exit 1
    }
  else
    curl -L -o "${mihomo_path}.gz" "$download_url" || {
      error "下载mihomo失败"
      exit 1
    }
  fi
  
  # 解压并设置权限
  gzip -d "${mihomo_path}.gz" || {
    # 如果失败，尝试手动解压
    gunzip -f "${mihomo_path}.gz" || {
      error "解压mihomo失败"
      exit 1
    }
  }
  
  chmod +x "$mihomo_path"
  success "mihomo下载并设置完成"
}

# 创建或更新tiqu.py
create_tiqu_script() {
  info "创建代理提取脚本..."
  local tiqu_script="${BASE_DIR}/tiqu.py"
  
  # 询问用户输入订阅URL
  echo "请输入你的代理机场Clash订阅链接(回车使用默认示例链接):"
  read -r subscription_url
  
  # 如果用户没有输入，使用默认示例链接
  if [[ -z "$subscription_url" ]]; then
    subscription_url="https://example.com/your-subscription-link"
    warn "使用示例链接，请稍后在tiqu.py中修改为你的真实订阅链接"
  fi
  
  # 创建tiqu.py脚本
  cat > "$tiqu_script" << EOF
#!/usr/bin/env python3
import requests
import yaml
import os

# 输出目录，存放下载的 YAML 文件
outputurl_directory = '${BASE_DIR}'
# 输入目录，存放原始的 proxies.yaml 文件
input_directory = '${BASE_DIR}'
# 输出目录，存放格式化后的 YAML 文件
output_directory = '${BASE_DIR}/proxy_providers'
os.makedirs(output_directory, exist_ok=True)

# 定义要访问的多个 URL
url_data = {
    'urls': [
        '$subscription_url',
        # 可以在这里添加更多订阅链接
    ]
}

os.makedirs(outputurl_directory, exist_ok=True)

# 遍历 URL 列表并下载内容
for index, url in enumerate(url_data['urls'], start=1):
    try:
        # 下载文件内容
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        # 假设下载的内容是 YAML 格式
        try:
            data = yaml.safe_load(response.text)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML from URL: {url}\\n{e}")
            continue

        # 保存下载的内容为 YAML 文件
        output_file_name = f"proxy_{index}.yaml"
        output_file_path = os.path.join(outputurl_directory, output_file_name)
        with open(output_file_path, 'w', encoding='utf-8') as yaml_file:
            yaml.dump(data, yaml_file, allow_unicode=True,
                      default_flow_style=False)

        print(
            f"Downloaded and saved content from URL {index} to {output_file_path}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download URL: {url}\\n{e}")

# 遍历输入目录下的所有文件
for file_name in os.listdir(input_directory):
    # 检查文件是否以 .yaml 结尾
    if file_name.endswith('.yaml') and file_name.startswith('proxy_'):
        input_file_path = os.path.join(input_directory, file_name)

        # 读取当前的 YAML 文件
        with open(input_file_path, 'r', encoding='utf-8') as file:
            parsed_data = yaml.safe_load(file)

        # 检查是否有 'proxies' 键，避免解析出错
        if 'proxies' in parsed_data:
            # 为每个代理创建一个 YAML 文件
            for index, proxy in enumerate(parsed_data['proxies'], start=1):
                # 构建新的代理字典，包装在一个列表下的字典中
                formatted_proxy = {'proxies': [proxy]}

                # 定义输出文件名，使用原始文件名加上代理索引
                output_file_name = f"{os.path.splitext(file_name)[0]}_proxy_{index}.yaml"
                output_file_path = os.path.join(
                    output_directory, output_file_name)

                # 将格式化的代理写入到单独的 YAML 文件，使用多行格式
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(formatted_proxy, f, allow_unicode=True,
                              default_flow_style=False)

                print(f"Created {output_file_path}")

# 显示路径信息，帮助调试
print(f"\\n脚本路径信息:")
print(f"当前脚本路径: {os.path.abspath(__file__)}")
print(f"当前工作目录: {os.path.abspath(os.getcwd())}")
print(f"基础目录: {base_directory}")
print(f"bin目录: {base_directory / 'bin'}")
print(f"mihomo路径: {base_directory / 'bin' / 'mihomo'}")
EOF
  
  chmod +x "$tiqu_script"
  success "代理提取脚本创建完成"
}

# 创建停止脚本
create_stop_script() {
  info "创建服务停止脚本..."
  local stop_script="${BASE_DIR}/stop_mihomo.sh"
  
  cat > "$stop_script" << EOF
#!/bin/bash

# 停止所有mihomo相关服务的脚本
echo "🛑 开始停止所有mihomo代理服务..."

# 找到所有mihomo相关的LaunchAgent
launch_agents=\$(ls ~/Library/LaunchAgents/com.proxypool.*.plist 2>/dev/null)

if [ -z "\$launch_agents" ]; then
    echo "⚠️  未找到任何mihomo代理服务"
else
    # 卸载所有服务
    for agent in \$launch_agents; do
        echo "正在卸载服务: \$(basename \$agent)"
        launchctl unload "\$agent"
    done
    echo "✅ 所有服务已卸载"
fi

# 查找并终止所有mihomo进程
mihomo_pids=\$(pgrep -f mihomo)
if [ -n "\$mihomo_pids" ]; then
    echo "找到mihomo进程: \$mihomo_pids"
    echo "正在终止mihomo进程..."
    kill -9 \$mihomo_pids 2>/dev/null
    echo "✅ 所有mihomo进程已终止"
else
    echo "⚠️  未找到任何运行中的mihomo进程"
fi

# 查找并清理服务注册
registered_services=\$(launchctl list | grep com.proxypool)
if [ -n "\$registered_services" ]; then
    echo "找到已注册服务，正在清理..."
    launchctl list | grep com.proxypool | awk '{print \$3}' | while read service; do
        echo "正在移除服务注册: \$service"
        launchctl remove "\$service" 2>/dev/null
    done
    echo "✅ 所有服务注册已清理"
fi

echo "🎉 清理完成！所有mihomo代理服务已停止"
EOF
  
  chmod +x "$stop_script"
  success "服务停止脚本创建完成"
}

# 主函数
main() {
  echo "============================================="
  echo "       macOS代理池安装和启动脚本 v1.0        "
  echo "============================================="
  
  # 检查是否已经安装
  if [ -f "${BASE_DIR}/bin/mihomo" ]; then
    warn "检测到已存在mihomo，是否重新安装? (y/N)"
    read -r reinstall
    if [[ ! "$reinstall" =~ ^[Yy]$ ]]; then
      info "跳过安装步骤，直接进行代理提取和配置"
      create_tiqu_script
    else
      check_requirements
      create_directories
      install_dependencies
      download_mihomo
      create_tiqu_script
      create_stop_script
    fi
  else
    check_requirements
    create_directories
    install_dependencies
    download_mihomo
    create_tiqu_script
    create_stop_script
  fi
  
  # 执行代理提取
  info "开始提取代理..."
  python3 "${BASE_DIR}/tiqu.py"
  
  # 询问是否设置代理池
  echo
  echo "是否要设置代理池? (Y/n)"
  read -r setup_pool
  if [[ ! "$setup_pool" =~ ^[Nn]$ ]]; then
    # 询问是否限制代理实例数
    echo "是否限制代理实例数量? (y/N)"
    read -r limit_instances
    
    # 加载全局端口配置
    if [ -f "${CURRENT_DIR}/port_config.sh" ]; then
      source "${CURRENT_DIR}/port_config.sh"
      info "已加载全局端口配置，默认起始端口: $DEFAULT_START_PORT"
    else
      DEFAULT_START_PORT=9000
      info "未找到端口配置文件，使用默认起始端口: $DEFAULT_START_PORT"
    fi
    
    # 询问起始端口
    echo "请设置起始端口(默认为${DEFAULT_START_PORT}):"
    read -r start_port
    
    # 验证端口输入，如果为空或者不是有效数字，则使用默认值
    if [[ ! "$start_port" =~ ^[0-9]+$ ]]; then
      start_port=$DEFAULT_START_PORT
      warn "使用默认起始端口: $start_port"
    fi
    
    if [[ "$limit_instances" =~ ^[Yy]$ ]]; then
      echo "请输入要使用的代理实例数量:"
      read -r instance_count
      
      if [[ "$instance_count" =~ ^[0-9]+$ ]]; then
        info "设置代理池，使用 $instance_count 个代理实例..."
        python3 "${CURRENT_DIR}/enhanced_proxy_manager.py" --base-dir "${BASE_DIR}" --instances "$instance_count" --start-port "$start_port"
      else
        error "输入无效，使用所有可用代理实例..."
        python3 "${CURRENT_DIR}/enhanced_proxy_manager.py" --base-dir "${BASE_DIR}" --start-port "$start_port"
      fi
    else
      info "设置代理池，使用所有可用代理实例..."
      python3 "${CURRENT_DIR}/enhanced_proxy_manager.py" --base-dir "${BASE_DIR}" --start-port "$start_port"
    fi
    
    # 显示服务状态
    echo
    info "代理服务状态:"
    python3 "${CURRENT_DIR}/proxy_service_manager.py" --base-dir "${BASE_DIR}" list
  fi
  
  echo
  success "===================================================="
  success "           代理池安装和配置完成！"
  success "===================================================="
  echo
  echo "使用以下命令管理代理服务:"
  echo "  查看所有服务: python3 proxy_service_manager.py --base-dir ${BASE_DIR} list"
  echo "  启动所有服务: python3 proxy_service_manager.py --base-dir ${BASE_DIR} start"
  echo "  停止所有服务: python3 proxy_service_manager.py --base-dir ${BASE_DIR} stop"
  echo "  查看服务日志: python3 proxy_service_manager.py --base-dir ${BASE_DIR} logs [服务名]"
  echo "  一键停止所有: bash ${BASE_DIR}/stop_mihomo.sh"
  echo
}

# 执行主函数
main