import asyncio
import os
import shlex
from urllib.parse import urlparse
from e2b_code_interpreter_client import (
    create_sandbox,
    run_command,
    run_python_code,
    Sandbox,
    looks_like_dir,
    truncate_result
)

try:
    from fastmcp import FastMCP
except ImportError:
    # 如果没有安装FastMCP，我们创建一个模拟类
    class FastMCP:
        def __init__(self, name):
            self.name = name
            
        def tool(self):
            def decorator(func):
                return func
            return decorator
            
        def run(self, transport=None):
            print(f"FastMCP server {self.name} would run with transport {transport}")


# 初始化 FastMCP 服务器
mcp = FastMCP("local-python-interpreter")

# API keys
LOGS_DIR = os.environ.get(
    "LOGS_DIR", "../../logs"
)  # Directory where benchmark logs are stored

# DEFAULT CONFS
DEFAULT_TIMEOUT = 600  # seconds
# Maximum number of tokens that can be returned by the Python tool
MAX_RESULT_LEN = 20_000
# Maximum number of tokens allowed in an error message
MAX_ERROR_LEN = 4_000


@mcp.tool()
async def create_sandbox_tool(timeout: int = DEFAULT_TIMEOUT) -> str:
    """Create a linux sandbox.

    Args:
        timeout: Time in seconds before the sandbox is automatically shutdown. The default is 600 seconds.

    Returns:
        The sandbox_id of the newly created sandbox. You should use this sandbox_id to run other tools in the sandbox.
    """
    return await create_sandbox(timeout)


@mcp.tool()
async def run_command_tool(command: str, sandbox_id: str) -> str:
    """Execute a lightweight shell command in the linux sandbox (no long-running, blocking, or resource-heavy processes).

    Args:
        command: The command to execute.
        sandbox_id: The id of the sandbox to execute the command in. To create a new sandbox, use tool `create_sandbox`.

    Returns:
        A CommandResult object containing the result of the command execution, format like CommandResult(stderr=..., stdout=..., exit_code=..., error=...)
    """
    return await run_command(command, sandbox_id)


@mcp.tool()
async def run_python_code_tool(code_block: str, sandbox_id: str) -> str:
    """Run short, safe python code in a sandbox and return the execution result (avoid long loops or heavy tasks; must finish quickly).

    Args:
        code_block: The python code to run.
        sandbox_id: The id of the sandbox to run the code in. Reuse existing sandboxes whenever possible. To create a new sandbox, use tool `create_sandbox`.

    Returns:
        A CommandResult object containing the result of the command execution, format like CommandResult(stderr=..., stdout=..., exit_code=..., error=...)
    """
    return await run_python_code(code_block, sandbox_id)


@mcp.tool()
async def upload_file_from_local_to_sandbox(
    sandbox_id: str, local_file_path: str, sandbox_file_path: str = "./"
) -> str:
    """Upload a local file to the `/home/user` dir of the remote python interpreter.

    Args:
        sandbox_id: The id of the sandbox to run the code in. Reuse existing sandboxes whenever possible. To create a new sandbox, use tool `create_sandbox`.
        local_file_path: The path of the file on local machine to upload.
        sandbox_file_path: The path of directory to upload the file to in the sandbox. Default is `/home/user/`.

    Returns:
        The path of the uploaded file in the remote python interpreter if the upload is successful.
    """
    if sandbox_id in ["default", "sandbox1", "sandbox", "some_id", "new_sandbox", "python", 
                      "create_sandbox", "sandbox123", "temp", "sandbox-0", "sandbox-1", 
                      "sandbox_0", "sandbox_1", "new", "0", "auto", "default_sandbox", 
                      "none", "sandbox_12345", "dummy", "sandbox_01"]:
        return f"[ERROR]: '{sandbox_id}' is not a valid sandbox_id. Please create a real sandbox first using the create_sandbox tool."

    # 当前实现不支持文件上传，因为原API没有此功能
    return f"[ERROR]: Uploading files is not supported in this implementation. The current sandbox API does not support direct file uploads."


@mcp.tool()
async def download_file_from_internet_to_sandbox(
    sandbox_id: str, url: str, sandbox_file_path: str = "."
) -> str:
    """Download a file from the internet to the `/home/user` dir of the sandbox (avoid large or slow URLs).

    Args:
        sandbox_id: The id of the sandbox to run the code in. Reuse existing sandboxes whenever possible. To create a new sandbox, use tool `create_sandbox`.
        url: The URL of the file to download.
        sandbox_file_path: The path of directory to download the file to in the sandbox. Default is `/home/user/`.

    Returns:
        The path of the downloaded file in the sandbox if the download is successful.
    """
    if sandbox_id in ["default", "sandbox1", "sandbox", "some_id", "new_sandbox", "python", 
                      "create_sandbox", "sandbox123", "temp", "sandbox-0", "sandbox-1", 
                      "sandbox_0", "sandbox_1", "new", "0", "auto", "default_sandbox", 
                      "none", "sandbox_12345", "dummy", "sandbox_01"]:
        return f"[ERROR]: '{sandbox_id}' is not a valid sandbox_id. Please create a real sandbox first using the create_sandbox tool."

    # 对于从互联网下载文件，我们可以通过运行Python代码的方式实现
    try:
        # 解析URL获取文件名
        parsed_url = urlparse(url)
        basename = os.path.basename(parsed_url.path) or "downloaded_file"
        # 移除任何查询参数或片段
        if "?" in basename:
            basename = basename.split("?")[0]
        if "#" in basename:
            basename = basename.split("#")[0]

        # 确定下载路径
        if looks_like_dir(sandbox_file_path):
            downloaded_file_path = os.path.join(sandbox_file_path, basename)
        else:
            downloaded_file_path = sandbox_file_path

        # 使用Python代码下载文件
        python_code = f'''
import urllib.request
import os

url = "{url}"
download_path = "{downloaded_file_path}"

# 确保目录存在
os.makedirs(os.path.dirname(download_path), exist_ok=True) if os.path.dirname(download_path) else None

try:
    urllib.request.urlretrieve(url, download_path)
    print(f"File downloaded to {{download_path}}")
except Exception as e:
    print(f"Error: {{str(e)}}")
'''
        result = await run_python_code(python_code, sandbox_id)
        return result
    except Exception as e:
        error_details = str(e)[:MAX_ERROR_LEN]
        return f"[ERROR]: Failed to download file from {url}: {error_details}"


@mcp.tool()
async def download_file_from_sandbox_to_local(
    sandbox_id: str, sandbox_file_path: str, local_filename: str = None
) -> str:
    """Download a file from the sandbox to local system. Files in sandbox cannot be processed by tools from other servers - only local files and internet URLs can be processed by them.

    Args:
        sandbox_id: The id of the sandbox to download the file from. To have a sandbox, use tool `create_sandbox`.
        sandbox_file_path: The path of the file to download on the sandbox.
        local_filename: Optional filename to save as. If not provided, uses the original filename from sandbox_file_path.

    Returns:
        The local path of the downloaded file if successful, otherwise error message.
    """
    if sandbox_id in ["default", "sandbox1", "sandbox", "some_id", "new_sandbox", "python", 
                      "create_sandbox", "sandbox123", "temp", "sandbox-0", "sandbox-1", 
                      "sandbox_0", "sandbox_1", "new", "0", "auto", "default_sandbox", 
                      "none", "sandbox_12345", "dummy", "sandbox_01"]:
        return f"[ERROR]: '{sandbox_id}' is not a valid sandbox_id. Please create a real sandbox first using the create_sandbox tool."

    # 当前实现不支持文件下载，因为原API没有此功能
    return f"[ERROR]: Downloading files is not supported in this implementation. The current sandbox API does not support direct file downloads."

if __name__ == "__main__":
    mcp.run(transport="stdio")