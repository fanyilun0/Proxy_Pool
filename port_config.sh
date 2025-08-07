#!/bin/bash
#
# 代理池端口配置文件
# 这个文件定义了代理池使用的全局端口设置
# 其他脚本可以引用这个文件来保持一致的端口配置

# 定义默认起始端口
DEFAULT_START_PORT=9000

# HTTP和SOCKS端口之间的差值
PORT_OFFSET=1

# 每个新代理服务递增的端口数量
PORT_INCREMENT=10

# 获取配置变量
get_port_config() {
  echo "DEFAULT_START_PORT=$DEFAULT_START_PORT"
  echo "PORT_OFFSET=$PORT_OFFSET"
  echo "PORT_INCREMENT=$PORT_INCREMENT"
}

# 当直接执行此脚本时显示配置信息
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "代理池端口配置"
  echo "============="
  echo "默认起始端口: $DEFAULT_START_PORT"
  echo "HTTP与SOCKS端口差值: $PORT_OFFSET"
  echo "服务端口递增值: $PORT_INCREMENT"
  echo ""
  echo "使用方法:"
  echo "在其他脚本中加载此配置:"
  echo '  source $(dirname "$0")/port_config.sh'
fi
