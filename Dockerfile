# 安装 Python 依赖
RUN pip install -r requirements.txt

# 设置工作目录
WORKDIR /app

# 将当前目录下的所有内容复制到容器中
COPY . /app

# 暴露 FastAPI 运行的端口
EXPOSE 8000

# 设置容器启动时运行的命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]