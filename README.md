# fleet-panel 自研自愈闭环（对标 1Panel 专业版多机能力，开源自建，不碰破解）
server : flask app  <- 各机 agent 上报 / 面板查询 / 指令下发，SQLite 落盘
agent  : 每台托管机常驻，自检 load/mem/disk/docker + 轮询自愈指令

## 一键起 server
    cd server && python3 app.py --port 8890
    # 页面 http://<IP>:8890  ;  API 见 app.py 头注释

## agent 装到某台机
    python3 agent/agent.py --server http://SERVER_IP:8890 --host <该机名> &
    # 自愈指令: POST /api/hosts/<host>/cmd  {"secret":"FIXME_SERVER_SECRET","proc":"service-restart","cmd":"rsyslog"}

## 阈值 / 通知
app.py 里 THRESH / NOTIFY 改。通知默认打 log，配 FLEET_WEBHOOK 走钉钉/webhook，FLEET_MAIL 走 smtp。

## 安全注意
- 上线换强 token：SERVER 端 FLEET_TOKEN、/api/hosts/<host>/cmd 的 secret
- agent 端 sudo 只放行白名单 service/container 名，不接受任意 shell