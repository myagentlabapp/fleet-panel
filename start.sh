#!/usr/bin/env bash
# fleet-panel 启动脚本: 带 NGINX_BIND(专属 IP 443, 与 gitlab 共存) 拉起面板
cd "$(dirname "$0")/server"
# 确保 fleet-nginx 真实 nginx 在跑 (WAF/HTTPS 生效载体)
docker ps --format '{{.Names}}' | grep -qx fleet-nginx || {
  echo "[start] fleet-nginx 未运行, 启动..."
  docker run -d --name fleet-nginx --network host --restart unless-stopped \
    -v /home/yy/fleet-panel/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
    -v /home/yy/fleet-panel/server/data:/home/yy/fleet-panel/server/data:ro \
    nginx:alpine
}
# 精确匹配: pgrep -f 会匹配到引用了该字符串的其他进程(shell 包装/脚本自身), 造成自匹配假阳性
pgrep -f "^python3 app\.py --port 8890$" >/dev/null || {
  echo "[start] 启动面板"
  FLEET_NGINX_BIND=192.168.1.250 setsid nohup python3 app.py --port 8890 \
    > /tmp/fleet-panel.log 2>&1 < /dev/null & disown
}
echo "[start] 面板: http://127.0.0.1:8890 ; WAF 443: https://192.168.1.250"