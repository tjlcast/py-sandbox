# Python 代码沙箱执行环境

这是一个基于 FastAPI 和 Docker 构建的 Python 代码沙箱执行环境，提供安全的远程代码执行能力。

## 功能特性

- 🔒 安全的代码执行环境，包含多重安全限制
- 🚀 基于 FastAPI 构建的高性能 RESTful API
- 🐳 Docker 容器化部署，环境隔离
- ⚡ 支持异步处理和超时控制
- 📚 离线 Swagger UI 文档支持
- 🌐 完整的 CORS 支持，便于前端集成

## 安全机制

### 代码安全检查
- 语法验证：确保代码符合 Python 语法规范
- 禁止导入危险模块：`os`, `sys`, `subprocess`, `socket` 等
- 禁止使用危险函数：`exec`, `eval`, `open` 等
- 执行超时控制：默认 1 秒超时限制

### 环境隔离
- Docker 容器化运行，与主机环境隔离
- 只读文件系统（可根据需要配置）
- 资源限制（CPU、内存限制可选）

## 快速开始

### 前提条件
- Docker
- Python 3.10+ (仅用于本地开发)

### 构建和运行

1. **构建 Docker 镜像**
```bash
cd test
chmod +x docker.sh
./docker.sh
```

2. **或者手动构建运行**
```bash
# 构建镜像
docker build --no-cache -t py-sandbox .

# 运行容器
docker run -d -p 8000:8000 --name py-sandbox-container py-sandbox
```

### 验证部署

访问 API 文档：http://localhost:8000/docs

## API 使用说明

### 执行代码端点

**POST** `/execute`

curl命令示例：
```curl
curl -X POST "http://localhost:8000/execute" \
-H "Content-Type: application/json" \
-d '{
  "code": "for i in range(5):\n    print(f\"Number: {i}\")"
}'
```

请求体：
```json
{
  "code": "print('Hello, World!')"
}
```

响应示例：
```json
{
  "status": "success",
  "message": "代码执行成功",
  "data": {
    "output": "Hello, World!\n",
    "errors": ""
  }
}
```

### 错误响应

安全检测失败：
```json
{
  "status": "error",
  "message": "Security Error: 检测到禁止的模块：os"
}
```

执行超时：
```json
{
  "status": "error",
  "message": "遇到执行错误",
  "data": {
    "output": "",
    "errors": "运行时间超出限制"
  }
}
```

## 项目结构

```
.
├── Dockerfile          # Docker 构建配置
├── main.py            # FastAPI 主应用
├── utils.py           # 工具函数（安全检查）
├── requirements.txt   # Python 依赖
└── test/
    └── docker.sh      # 构建和运行脚本
```

## 开发指南

### 本地开发

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动开发服务器：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 自定义配置

- 修改 `Dockerfile` 中的基础镜像版本
- 调整 `requirements.txt` 中的依赖版本
- 在 `utils.py` 中自定义安全规则

## 生产部署建议

1. **启用资源限制**：
```bash
docker run -d -p 8000:8000 \
  --memory=512m \
  --cpus=1 \
  --name py-sandbox \
  py-sandbox
```

2. **使用反向代理**（如 Nginx）
3. **启用 HTTPS**
4. **配置监控和日志收集**

## 限制说明

- 最大执行时间：1秒
- 禁止文件系统操作
- 禁止网络访问
- 禁止系统调用
- 内存使用受限（需在 Docker 运行时配置）

## 故障排除

### 常见问题

1. **构建失败**：检查网络连接和 Docker 服务状态
2. **端口冲突**：更改宿主机的映射端口
3. **执行超时**：复杂计算可能需要更多时间（不建议放宽限制）

### 查看日志

```bash
docker logs py-sandbox-container
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 安全建议

虽然已经实施了多重安全措施，但在生产环境中使用时仍建议：
- 定期更新基础镜像和安全补丁
- 监控异常执行模式
- 考虑添加额外的认证和授权层
- 限制 API 访问频率

---

**注意**：此沙箱环境旨在提供基本的安全保障，但对于高度敏感的环境，建议使用更专业的沙箱解决方案。