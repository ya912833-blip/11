# ── 构建阶段 ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装依赖到独立目录，便于多阶段复制
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── 运行阶段 ──────────────────────────────────────────────
FROM python:3.12-slim

# 创建非 root 用户
RUN groupadd -r botuser && useradd -r -g botuser botuser

WORKDIR /app

# 从构建阶段复制已安装的依赖
COPY --from=builder /install /usr/local

# 复制项目代码
COPY --chown=botuser:botuser . .

# 创建数据目录并赋予权限
RUN mkdir -p /app/data && chown botuser:botuser /app/data

# 切换到非 root 用户
USER botuser

# 数据库持久化目录
VOLUME ["/app/data"]

# 健康检查：确认进程存活
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD pgrep -f "python.*main.py" > /dev/null || exit 1

# 启动命令
CMD ["python", "main.py"]
