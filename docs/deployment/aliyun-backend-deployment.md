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

推荐放在当前用户目录下，权限最简单：

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

如果你希望放在 `/opt/apps` 这类系统目录，先用 `sudo` 创建目录，再把项目目录所有权交给运行服务的用户。下面以登录用户 `admin` 为例：

```bash
sudo mkdir -p /opt/apps
sudo chown -R admin:admin /opt/apps
cd /opt/apps
git clone https://github.com/zzy8226614/Stock2to3Selection.git
cd /opt/apps/Stock2to3Selection
sudo chown -R admin:admin /opt/apps/Stock2to3Selection
```

## 5. 创建虚拟环境并安装依赖

不要使用 `sudo python3 -m venv .venv` 创建虚拟环境。否则 `.venv` 会归 `root` 所有，后续普通用户执行 `pip install` 会出现 `Permission denied: '.venv/bin/pip'`。

```bash
cd /opt/apps/Stock2to3Selection
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

如果你的项目实际放在 `~/apps/Stock2to3Selection`，把上面的 `cd /opt/apps/Stock2to3Selection` 换成自己的路径即可。

如果之前已经误用 `sudo` 创建过 `.venv`，按下面方式重建：

```bash
cd /opt/apps/Stock2to3Selection
deactivate 2>/dev/null || true
sudo chown -R admin:admin /opt/apps/Stock2to3Selection
rm -rf .venv
hash -r
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

如果删除 `.venv` 后仍显示 `(.venv)`，说明当前 shell 还停留在已经失效的虚拟环境里。先执行：

```bash
deactivate 2>/dev/null || true
hash -r
which python3
python3 --version
```

确认 `python3` 指向 `/usr/bin/python3` 后，再重新执行 `python3 -m venv .venv`。

国内网络慢时可以使用清华源：

```bash
pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果 `python3 -m venv .venv` 提示缺少 venv 模块：

```bash
sudo apt update
sudo apt install -y python3-venv
python3 -m venv .venv
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
User=admin
WorkingDirectory=/opt/apps/Stock2to3Selection
Environment="PATH=/opt/apps/Stock2to3Selection/.venv/bin"
ExecStart=/opt/apps/Stock2to3Selection/.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5
TimeoutStopSec=20
KillSignal=SIGINT
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

如果你的登录用户不是 `admin`，或者项目不在 `/opt/apps/Stock2to3Selection`，把 `User`、`WorkingDirectory`、`PATH` 和 `ExecStart` 中的路径改成实际值。`User` 应该和 `.venv` 所属用户一致。

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

虚拟环境权限错误时，常见现象：

```text
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied: '.venv/bin/pip'
```

原因通常是用 `sudo python3 -m venv .venv` 创建了 root-owned 虚拟环境。修复方式是把项目目录所有权交给运行用户，并重新创建 `.venv`：

```bash
cd /opt/apps/Stock2to3Selection
deactivate 2>/dev/null || true
sudo chown -R admin:admin /opt/apps/Stock2to3Selection
rm -rf .venv
hash -r
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

如果执行 `python3 -m venv .venv` 时提示：

```text
-bash: /opt/apps/Stock2to3Selection/.venv/bin/python3: No such file or directory
```

说明当前 shell 还在使用已经被删除的旧虚拟环境。执行 `deactivate` 或 `hash -r` 后再重建。

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
