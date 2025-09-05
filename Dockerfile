# 多阶段构建 Dockerfile
# 阶段1: 前端构建
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖（需要包含开发依赖来构建）
RUN npm ci

# 复制前端源代码
COPY frontend/ ./

# 构建前端应用（跳过类型检查）
RUN npx vite build

# 阶段2: 后端运行环境
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖 (包括FFmpeg)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖文件
COPY requirements.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源代码
COPY src/ ./src/
COPY backend_server.py ./
COPY main.py ./

# 复制构建好的前端文件
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 创建必要的目录
RUN mkdir -p input output/clips output/collections output/metadata uploads data

# 复制配置文件
COPY data/settings.example.json ./data/settings.json

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "backend_server.py"]
