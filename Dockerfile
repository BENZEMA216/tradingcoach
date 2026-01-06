# Backend Dockerfile for Railway
# 简化版本 - 不使用多阶段构建避免缓存问题

FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY config_template.py ./config.py
COPY backend/ ./backend/
COPY src/ ./src/

# 创建数据目录
RUN mkdir -p /app/data /app/logs /app/cache

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# 启动命令
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}
