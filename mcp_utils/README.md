# MCP Utils

这是一个用于与 MCP (Model Context Protocol) 服务器交互的工具包，主要用于与本地 sandbox 环境进行交互，执行 Python 代码、运行命令等操作。

## 模块说明

### 1. code_interpreter_client.py

这是与本地 sandbox API 交互的核心客户端模块。提供了以下主要功能：

- **SandboxClient**: 与 sandbox API 交互的客户端类
  - 执行 Python 代码 (`execute_code`)
  - 执行系统命令 (`execute_command`)
  - 创建、获取和删除会话 (`create_session`, `get_session`, `delete_session`)

- **Sandbox**: 模拟原始 e2b_code_interpreter.Sandbox 类的接口
  - 连接到现有会话或创建新会话
  - 执行命令 (`commands.run`)
  - 运行 Python 代码 (`run_code`)
  - 文件操作 (虽然当前未实现)

- **核心工具函数**:
  - `create_sandbox`: 创建 Linux 沙箱环境
  - `run_command`: 在沙箱中执行轻量级 shell 命令
  - `run_python_code`: 在沙箱中安全地运行 Python 代码

### 2. mcp_client_session_example.py

这是一个使用 MCP ClientSession 与本地 sandbox API 交互的示例客户端。展示了如何：

- 建立与 MCP 服务器的连接
- 列出可用工具
- 调用工具函数（如创建沙箱、执行 Python 代码、执行命令）
- 错误处理和资源清理

### 3. python_mcp_server.py

这是 MCP 服务器的实现，将上述功能暴露为可调用的工具。提供了以下工具：

- `create_sandbox_tool`: 创建 Linux 沙箱环境
- `run_command_tool`: 在沙箱中执行命令
- `run_python_code_tool`: 在沙箱中运行 Python 代码
- `upload_file_from_local_to_sandbox`: 上传本地文件到沙箱（当前未实现）
- `download_file_from_internet_to_sandbox`: 从互联网下载文件到沙箱
- `download_file_from_sandbox_to_local`: 从沙箱下载文件到本地（当前未实现）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用示例

### 启动 MCP 服务器

```bash
python -m mcp_utils.python_mcp_server
```

### 使用示例客户端

```bash
python mcp_utils/mcp_client_session_example.py
```

### 直接使用客户端

```python
import asyncio
from mcp_utils.code_interpreter_client import Sandbox

async def example():
    # 创建沙箱
    sandbox = Sandbox(timeout=600)
    info = await sandbox.get_info()
    sandbox_id = info.sandbox_id
    
    # 在沙箱中运行 Python 代码
    result = await sandbox.run_code("print('Hello, World!')")
    print(f"Output: {result.stdout}")
    print(f"Errors: {result.stderr}")
    
    # 在沙箱中执行命令
    cmd_result = await sandbox.commands.run("ls -la")
    print(f"Command output: {cmd_result.stdout}")
    
    # 清理资源
    await sandbox.client.delete_session(sandbox_id)

# 运行示例
asyncio.run(example())
```

### 通过 MCP 服务器调用工具

```python
import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def call_mcp_tools():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_utils.python_mcp_server"],
        env={"E2B_API_KEY": "xxx"},
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 创建沙箱
            create_result = await session.call_tool(
                "create_sandbox_tool",
                arguments={"timeout": 600, "sandbox_id": "my-sandbox"}
            )
            print(f"Create sandbox result: {create_result.content[0].text}")
            
            # 运行 Python 代码
            code_result = await session.call_tool(
                "run_python_code_tool",
                arguments={
                    "code_block": "import math; print(math.sqrt(16))",
                    "sandbox_id": "my-sandbox"
                }
            )
            print(f"Code execution result: {code_result.content[0].text}")

# 运行示例
asyncio.run(call_mcp_tools())
```

## 功能特性

1. **异步操作**: 所有操作都是异步的，适合高并发场景
2. **错误处理**: 完善的错误处理机制，包括重试逻辑
3. **会话管理**: 支持创建、管理和清理沙箱会话
4. **超时控制**: 可配置的超时时间，防止长时间阻塞
5. **结果截断**: 防止过长的结果输出导致问题

## 环境变量

- `SANDBOX_API_BASE_URL`: sandbox API 的基础 URL，默认为 `http://localhost:8000`
- `LOGS_DIR`: 日志目录路径，默认为 `../../logs`

## 注意事项

1. 该模块依赖于本地运行的 sandbox API 服务
2. 文件上传/下载功能在当前实现中尚未完全支持
3. 所有代码执行都在沙箱环境中进行，确保安全性
4. 建议在使用前确认 sandbox API 服务已正确启动

## 最佳实践

1. **会话管理**: 尽可能重用沙箱会话以提高性能
2. **错误处理**: 始终处理工具调用可能返回的错误
3. **资源清理**: 使用完沙箱后及时清理资源
4. **超时设置**: 根据任务复杂度合理设置超时时间
5. **结果验证**: 对执行结果进行验证，特别是输出和错误信息

## 常见问题

1. **连接失败**: 确保 sandbox API 服务正在运行，并且端口正确
2. **权限问题**: 检查是否有足够的权限执行相关命令
3. **超时问题**: 对于耗时较长的操作，适当增加超时时间
4. **结果截断**: 大量输出会被自动截断，注意查看完整结果的方法

## 常见使用场景

### 场景1: 简单的 Python 代码执行
```python
from mcp_utils.code_interpreter_client import Sandbox

async def run_simple_code():
    sandbox = Sandbox()
    info = await sandbox.get_info()
    result = await sandbox.run_code("print('Hello, World!')")
    print(result.stdout)
    await sandbox.client.delete_session(info.sandbox_id)
```

### 场景2: 系统命令执行
```python
from mcp_utils.code_interpreter_client import Sandbox

async def run_system_commands():
    sandbox = Sandbox()
    info = await sandbox.get_info()
    result = await sandbox.commands.run("python --version")
    print(result.stdout)
    await sandbox.client.delete_session(info.sandbox_id)
```

### 场景3: 复杂任务处理
```python
from mcp_utils.code_interpreter_client import Sandbox

async def complex_task():
    # 创建沙箱
    sandbox = Sandbox(timeout=1200)  # 20分钟超时
    info = await sandbox.get_info()
    sandbox_id = info.sandbox_id
    
    try:
        # 执行多个任务
        result1 = await sandbox.run_code("import numpy as np; print(np.array([1,2,3]).sum())")
        result2 = await sandbox.commands.run("ls -la")
        
        # 处理结果
        print(f"计算结果: {result1.stdout}")
        print(f"目录列表: {result2.stdout}")
        
    finally:
        # 清理资源
        await sandbox.client.delete_session(sandbox_id)
```

## 许可证

MIT License