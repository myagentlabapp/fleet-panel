#!/usr/bin/env bash
# fleet-agent 安装脚本 —— 幂等, 可重复执行(只覆盖文件 + 重启服务)。
# 用法:  sudo bash install.sh http://fleet.myagentlab.internal:8890
set -u

SERVER="${1:?用法: install.sh <server-url like http://fleet.myagentlab.internal:8890>}"
SRC="$(cd "$(dirname "$0")" && pwd)/agent.py"
DEST_DIR="/opt/fleet-agent"
UNIT="/etc/systemd/system/fleet-agent.service"
TOKEN="${FLEET_TOKEN:-}"
[ -n "$TOKEN" ] || { echo "缺少 FLEET_TOKEN 环境变量(面板接入 token)"; exit 1; }

HOST="$(hostname)"
PY="$(command -v python3 || echo /usr/bin/python3)"

echo "==> 部署 fleet-agent 到 $HOST, server=$SERVER"
[ -f "$SRC" ] || { echo "缺少 $SRC"; exit 1; }
mkdir -p "$DEST_DIR"
install -m755 "$SRC" "$DEST_DIR/agent.py"

echo "==> 写 systemd unit"
cat > "$UNIT" <<EOF
[Unit]
Description=fleet-panel node agent
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=$PY $DEST_DIR/agent.py --server $SERVER --host $HOST --interval 30
Restart=always
RestartSec=10
Environment=FLEET_TOKEN=$TOKEN
WorkingDirectory=$DEST_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable fleet-agent >/dev/null 2>&1
systemctl restart fleet-agent

sleep 3
echo "==> is-active:    $(systemctl is-active fleet-agent)"
echo "==> is-enabled:   $(systemctl is-enabled fleet-agent)"
echo "==> 最近日志:"
journalctl -u fleet-agent -n 5 --no-pager 2>/dev/null | tail -5