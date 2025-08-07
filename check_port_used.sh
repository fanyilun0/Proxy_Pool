#!/bin/bash
#
# 检查代理服务使用的端口
# 作者: Proxy_Pool
# 用途: 检查当前系统中代理服务占用的端口

# 定义颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 加载全局端口配置
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
if [ -f "$SCRIPT_DIR/port_config.sh" ]; then
    source "$SCRIPT_DIR/port_config.sh"
else
    # 默认起始端口（如果找不到配置文件）
    DEFAULT_START_PORT=9000
fi

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

# 获取当前脚本所在目录
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SERVICES_FILE="${SCRIPT_DIR}/services.json"

# 解析命令行参数
parse_arguments() {
    # 默认值
    START_PORT=$DEFAULT_START_PORT
    PORT_COUNT=100
    SCAN_RANGE=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        key="$1"
        case $key in
            -p|--port)
                START_PORT="$2"
                shift
                shift
                ;;
            -c|--count)
                PORT_COUNT="$2"
                shift
                shift
                ;;
            -r|--range)
                SCAN_RANGE=true
                shift
                ;;
            *)
                # 未知参数
                shift
                ;;
        esac
    done
}

# 检查services.json文件是否存在
check_services_file() {
    if [ ! -f "$SERVICES_FILE" ]; then
        warn "未找到服务配置文件: $SERVICES_FILE"
        warn "将使用端口范围扫描模式"
        SCAN_RANGE=true
    fi
}

# 检查是否安装了jq
check_jq() {
    if ! command -v jq &> /dev/null; then
        warn "未安装jq工具，尝试安装中..."
        if command -v brew &> /dev/null; then
            brew install jq
        elif command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y jq
        elif command -v yum &> /dev/null; then
            sudo yum install -y jq
        else
            error "无法安装jq，请手动安装后再运行"
            if [ "$SCAN_RANGE" = false ]; then
                warn "切换到端口范围扫描模式"
                SCAN_RANGE=true
            fi
        fi
    fi
    
    if command -v jq &> /dev/null; then
        success "jq工具已安装"
    fi
}

# 检查mihomo相关进程
check_mihomo_processes() {
    info "检查mihomo相关进程端口使用情况..."
    
    echo ""
    echo "端口使用说明:"
    echo "  HTTP端口:     用于HTTP代理访问"
    echo "  SOCKS5端口:   用于SOCKS5代理访问（通常是HTTP端口+1）"
    echo "  控制面板端口: 用于访问Web控制界面（通常是HTTP端口+2）"
    echo "  DNS端口:     用于DNS解析（通常是控制面板端口+1000）"
    echo ""
    
    echo "=============================================================================================================="
    echo -e "${YELLOW}HTTP端口\tSOCKS5端口\t控制面板端口\tDNS端口\t服务名${NC}"
    echo "=============================================================================================================="
    
    # 临时文件存储所有服务信息
    temp_file=$(mktemp)
    
    ps aux | grep -i mihomo | grep -v grep | while read line; do
        pid=$(echo "$line" | awk '{print $2}')
        
        # 提取服务名，只显示配置文件名而不是完整路径
        cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i}')
        config_file=$(echo "$cmd" | grep -o 'proxy_[0-9]*_.*\.yaml' | head -1)
        
        if [ -z "$config_file" ]; then
            config_file="未知服务"
        fi
        
        # 提取服务编号用于排序
        service_num=$(echo "$config_file" | grep -o "proxy_[0-9]*" | sed 's/proxy_//' | sed 's/^0*//')
        if [ -z "$service_num" ]; then
            service_num=9999  # 对于未知服务，给一个较大的编号
        fi
        
        # 查找该进程使用的所有端口（TCP和UDP）
        all_ports=$(lsof -Pan -p $pid -i | grep LISTEN | awk '{print $9}' | awk -F: '{print $2}' | sort -n)
        
        # 如果没有找到端口，继续下一个进程
        if [ -z "$all_ports" ]; then
            continue
        fi
        
        # 解析各类端口
        # 获取端口数组
        ports_array=($all_ports)
        
        # 根据端口数量确定端口类型
        port_count=${#ports_array[@]}
        
        if [ $port_count -ge 4 ]; then
            # 按端口大小排序
            sorted_ports=($(printf '%s\n' "${ports_array[@]}" | sort -n))
            
            # 假设端口配置为HTTP、SOCKS5、控制面板、DNS
            http_port=${sorted_ports[0]}
            socks_port=${sorted_ports[1]}
            control_port=${sorted_ports[2]}
            dns_port=${sorted_ports[3]}
            
            # 验证端口关系
            if [ $((socks_port - http_port)) -ne 1 ] || [ $((control_port - http_port)) -ne 2 ]; then
                # 如果端口关系不符合预期，按规则重新分配
                http_port=${sorted_ports[0]}
                sorted_rest=($(printf '%s\n' "${sorted_ports[@]:1}" | sort -n))
                
                for port in "${sorted_rest[@]}"; do
                    if [ $((port - http_port)) -eq 1 ]; then
                        socks_port=$port
                    elif [ $((port - http_port)) -eq 2 ]; then
                        control_port=$port
                    elif [ $port -gt $((http_port + 100)) ]; then
                        # 大于HTTP端口100的可能是DNS端口
                        dns_port=$port
                    fi
                done
            fi
        elif [ $port_count -eq 3 ]; then
            sorted_ports=($(printf '%s\n' "${ports_array[@]}" | sort -n))
            http_port=${sorted_ports[0]}
            socks_port=${sorted_ports[1]}
            control_port=${sorted_ports[2]}
            dns_port="-"
        elif [ $port_count -eq 2 ]; then
            sorted_ports=($(printf '%s\n' "${ports_array[@]}" | sort -n))
            http_port=${sorted_ports[0]}
            socks_port=${sorted_ports[1]}
            control_port="-" 
            dns_port="-"
        elif [ $port_count -eq 1 ]; then
            http_port=${ports_array[0]}
            socks_port="-"
            control_port="-"
            dns_port="-"
        else
            # 没有端口
            continue
        fi
        
        # 输出到临时文件，包含HTTP端口和服务编号方便排序
        echo -e "$http_port\t$service_num\t$http_port\t$socks_port\t$control_port\t$dns_port\t$config_file" >> $temp_file
    done
    
    # 按HTTP端口排序并显示结果（删除临时的排序列）
    sort -n $temp_file | awk '{print $3 "\t\t" $4 "\t\t" $5 "\t\t" $6 "\t\t" $7}' | while read line; do
        echo -e "$line"
    done
    
    # 删除临时文件
    rm -f $temp_file
}

# 显示使用帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -p, --port PORT    起始端口号 (默认: $DEFAULT_START_PORT)"
    echo "  -c, --count COUNT  要检查的服务数量 (默认: 100)"
    echo "  -r, --range        使用端口范围扫描模式，忽略services.json"
    echo "  -h, --help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -p 9000 -c 20   # 检查从9000开始的20个服务的端口"
    echo "  $0 -r              # 使用端口范围扫描模式"
}

# 主函数
main() {
    # 解析命令行参数
    parse_arguments "$@"
    
    echo "=============================================="
    echo "       代理服务端口使用情况检查工具 v1.2      "
    echo "=============================================="
    echo "起始端口: $START_PORT"
    echo "=============================================="
    
    # 检查services.json文件是否存在
    check_services_file
    
    # 检查jq是否安装
    check_jq
    
    # 直接检查mihomo进程的端口使用情况
    check_mihomo_processes
    
    echo -e "\n"
    success "检查完成!"
}

# 如果带-h或--help参数，显示帮助
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# 执行主函数
main "$@"