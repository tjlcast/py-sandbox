# 使用官方 Python 运行时作为基础镜像
# FROM python:3.9-slim
# 使用阿里云镜像源的 Python 基础镜像
# FROM registry.cn-hangzhou.aliyuncs.com/aliyun-python/python:3.9-slim
FROM python:3.10.6

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件到工作目录
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录下的所有内容复制到容器中
COPY . .

# 暴露 FastAPI 运行的端口
EXPOSE 8000

# 设置容器启动时运行的命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
