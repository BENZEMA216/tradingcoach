# TradingCoach 部署指南

## 快速开始

### 本地 Docker 部署

```bash
# 1. 复制环境变量配置
cp .env.example .env
# 编辑 .env 填入你的 API Keys

# 2. 构建并启动
docker-compose up -d --build

# 3. 查看日志
docker-compose logs -f

# 4. 访问应用
# 前端: http://localhost
# 后端 API: http://localhost:8000/api/v1/docs
```

### 停止服务

```bash
docker-compose down
```

---

## 云平台部署

### 方案一：Railway（推荐）

Railway 支持直接从 GitHub 部署，最简单快捷。

1. **注册 Railway**: https://railway.app
2. **连接 GitHub 仓库**
3. **添加环境变量**: 在 Railway Dashboard 中配置 `.env` 中的变量
4. **部署**: Railway 会自动检测 `docker-compose.yml` 并部署

**注意**: Railway 支持持久卷，SQLite 数据会保留。

### 方案二：Fly.io

```bash
# 1. 安装 flyctl
brew install flyctl

# 2. 登录
fly auth login

# 3. 初始化（在项目根目录）
fly launch

# 4. 创建持久卷（保存 SQLite 数据）
fly volumes create tradingcoach_data --size 1

# 5. 部署
fly deploy

# 6. 查看状态
fly status
```

### 方案三：VPS 自建（阿里云/腾讯云）

```bash
# 1. SSH 登录服务器
ssh root@your-server-ip

# 2. 安装 Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# 3. 安装 Docker Compose
apt install docker-compose-plugin

# 4. 克隆代码
git clone https://github.com/your-username/tradingcoach.git
cd tradingcoach

# 5. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 6. 启动服务
docker compose up -d --build

# 7. 配置防火墙（开放 80 端口）
ufw allow 80
ufw allow 443
```

### 方案四：Vercel + Railway（前后端分离）

**前端部署到 Vercel:**
```bash
cd frontend
npx vercel --prod
```

**后端部署到 Railway:**
- 单独部署 backend 目录到 Railway

---

## 生产环境配置

### HTTPS 配置

使用 Caddy 自动获取 SSL 证书：

```bash
# docker-compose.prod.yml 中添加
caddy:
  image: caddy:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile
    - caddy_data:/data
```

**Caddyfile:**
```
your-domain.com {
    reverse_proxy frontend:80
}
```

### 数据备份

```bash
# 备份 SQLite 数据库
docker cp tradingcoach-backend:/app/data/tradingcoach.db ./backup/

# 定时备份（crontab）
0 2 * * * docker cp tradingcoach-backend:/app/data/tradingcoach.db /backup/tradingcoach-$(date +\%Y\%m\%d).db
```

### 日志管理

```bash
# 查看日志
docker-compose logs -f backend

# 日志轮转已在 docker-compose.prod.yml 中配置
```

---

## 常见问题

### Q: SQLite 性能够用吗？

对于个人交易分析（数千条记录），SQLite 完全够用。如需更高并发，可迁移到 PostgreSQL。

### Q: 如何迁移到 PostgreSQL？

1. 安装 PostgreSQL 客户端库
2. 修改 `DATABASE_URL` 为 PostgreSQL 连接串
3. 运行数据库迁移脚本

### Q: 如何更新部署？

```bash
git pull
docker-compose up -d --build
```

### Q: 数据存在哪里？

- Docker 部署：`./data/tradingcoach.db`（通过 volume 挂载）
- 容器内路径：`/app/data/tradingcoach.db`

---

## 文件结构

```
.
├── docker-compose.yml      # 开发/生产通用配置
├── docker-compose.prod.yml # 生产环境覆盖配置
├── .dockerignore           # Docker 构建忽略文件
├── .env.example            # 环境变量模板
├── backend/
│   └── Dockerfile          # 后端镜像构建
└── frontend/
    ├── Dockerfile          # 前端镜像构建
    └── nginx.conf          # Nginx 配置
```
