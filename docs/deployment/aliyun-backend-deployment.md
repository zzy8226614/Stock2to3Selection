# 阿里云后端部署说明书

本文用于把 `Stock2to3Selection` 后端从 GitHub 拉取到阿里云 ECS，并以 `systemd` 常驻运行。

GitHub 仓库：

```text
https://github.com/zzy8226614/Stock2to3Selection.git
```

默认对外服务地址：

```text
http://47.107.125.248:8080/
```

## 1. 服务器要求

| 项 | 建议值 |
| :--- | :--- |
| 系统 | Ubuntu 22.04 LTS |
| Python | 3.10 至 3.12 |
| 内存 | 2 GB 起，推荐 4 GB |
| 端口 | `TCP 8080` |
| 进程托管 | `systemd` |

## 2. 安全组和防火墙

在 ECS 控制台安全组入方向放通：

| 协议 | 端口 | 来源 | 用途 |
| :--- | :--- | :--- | :--- |
| TCP | 22 | 你的公网 IP | SSH 登录 |
| TCP | 8080 | `0.0.0.0/0` | FastAPI 后端访问 |

如果服务器启用了 `ufw`：

```bash
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
sudo ufw status
```

## 3. 安装系统依赖

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip curl
python3 --version
```

## 4. 拉取项目代码

```bash
mkdir -p ~/apps
cd ~/apps
git clone https://github.com/zzy8226614/Stock2to3Selection.git
cd ~/apps/Stock2to3Selection
```

如果目录已存在：

```bash
cd ~/apps/Stock2to3Selection
git pull
```

## 5. 创建虚拟环境并安装依赖

```bash
cd ~/apps/Stock2to3Selection
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

国内网络慢时可以使用清华源：

```bash
pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 6. 临时启动验证

```bash
cd ~/apps/Stock2to3Selection
source .venv/bin/activate
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
```

另开一个 SSH 窗口检查：

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/api/v1/health
curl "http://127.0.0.1:8080/debug/upstream-check?timeout_seconds=12"
```

公网检查：

```bash
curl http://47.107.125.248:8080/health
curl http://47.107.125.248:8080/api/v1/health
```

## 7. 配置 systemd 常驻服务

创建服务文件：

```bash
sudo nano /etc/systemd/system/stock2to3.service
```

写入：

```ini
[Unit]
Description=Stock2to3Selection FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/apps/Stock2to3Selection
Environment="PATH=/home/ubuntu/apps/Stock2to3Selection/.venv/bin"
ExecStart=/home/ubuntu/apps/Stock2to3Selection/.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5
TimeoutStopSec=20
KillSignal=SIGINT
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

如果你的登录用户不是 `ubuntu`，把 `User`、`WorkingDirectory`、`PATH` 和 `ExecStart` 中的路径改成实际路径。

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable stock2to3
sudo systemctl start stock2to3
sudo systemctl status stock2to3
```

## 8. 接口预热

部署后建议预热三个核心接口：

```bash
curl -X POST http://127.0.0.1:8080/api/v1/screen/market-signal \
  -H "Content-Type: application/json" \
  -d '{"trade_date":null,"use_demo_on_failure":true,"force_refresh":false}'

curl -X POST http://127.0.0.1:8080/api/v1/screen/second-board-analysis \
  -H "Content-Type: application/json" \
  -d '{"trade_date":null,"use_demo_on_failure":true,"force_refresh":false}'

curl -X POST http://127.0.0.1:8080/api/v1/screen/board-top10-limit-up \
  -H "Content-Type: application/json" \
  -d '{"trade_date":null,"use_demo_on_failure":true,"force_refresh":false}'
```

## 9. 日常更新

```bash
cd ~/apps/Stock2to3Selection
git pull
source .venv/bin/activate
pip install -r backend/requirements.txt
sudo systemctl restart stock2to3
sudo systemctl status stock2to3
```

查看日志：

```bash
sudo journalctl -u stock2to3 -f
```

## 10. 常见问题

公网访问失败时依次检查：

```bash
sudo systemctl status stock2to3
curl http://127.0.0.1:8080/health
sudo ss -lntp | grep 8080
```

如果本机正常但公网失败，优先检查阿里云安全组和服务器防火墙。

上游行情不稳定时检查：

```bash
curl "http://127.0.0.1:8080/debug/upstream-check?timeout_seconds=12"
```

系统会优先使用 Akshare，必要时使用本地缓存和腾讯行情后备源。`runtime_env` 会清理失效的本机代理环境变量，避免服务因为错误代理无法访问上游。

服务反复重启时查看：

```bash
sudo journalctl -u stock2to3 --since "2 hours ago" --no-pager
dmesg -T | grep -i -E "killed process|out of memory|oom"
```

## 11. 验收清单

部署完成后至少确认：

```bash
curl http://47.107.125.248:8080/health
curl http://47.107.125.248:8080/api/v1/health
curl -X POST http://47.107.125.248:8080/api/v1/screen/second-board-analysis \
  -H "Content-Type: application/json" \
  -d '{"trade_date":null,"use_demo_on_failure":true,"force_refresh":false}'
```

验收标准：

1. `/health` 返回 `{"status":"ok"}`。
2. `/api/v1/health` 返回 `success=true`。
3. `second-board-analysis` 返回 `success=true`，且 `data.items` 为数组。
4. Android 和 PC 桌面端能用服务器地址访问后端。
