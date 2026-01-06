# Backend Dockerfile
# 构建上下文为项目根目录

FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn[standard] gunicorn pydantic-settings

# 生产镜像
FROM python:3.11-slim

WORKDIR /app

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

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

# 暴露端口（Railway 会覆盖）
EXPOSE ${PORT}

# 启动命令 - 使用 shell 形式以支持环境变量
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}
