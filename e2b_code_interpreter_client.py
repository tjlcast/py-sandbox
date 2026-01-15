import asyncio
import os
import shlex
from urllib.parse import urlparse
import aiohttp
from typing import Dict, Any, Optional

# API配置
DEFAULT_API_BASE_URL = os.environ.get("SANDBOX_API_BASE_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 600  # seconds
# Maximum number of tokens that can be returned by the Python tool
MAX_RESULT_LEN = 20_000
# Maximum number of tokens allowed in an error message
MAX_ERROR_LEN = 4_000
# Invalid sandbox IDs that are not allowed to be used
INVALID_SANDBOX_IDS = {
    "default",
    "sandbox1",
    "sandbox",
    "some_id",
    "new_sandbox",
    "python",
    "create_sandbox",
    "sandbox123",
    "temp",
    "sandbox-0",
    "sandbox-1",
    "sandbox_0",
    "sandbox_1",
    "new",
    "0",
    "auto",
    "default_sandbox",
    "none",
    "sandbox_12345",
    "dummy",
    "sandbox_01",
}

class SandboxClient:
    """客户端类，用于与本地sandbox API交互"""
    
    def __init__(self, base_url: str = DEFAULT_API_BASE_URL):
        self.base_url = base_url
        self.http_client = aiohttp.ClientSession()
        
    async def close(self):
        await self.http_client.close()
        
    async def execute_code(self, code: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """执行Python代码"""
        payload = {"code": code}
        if session_id:
            payload["session_id"] = session_id
            
        try:
            async with self.http_client.post(f"{self.base_url}/execute/pycode", json=payload) as resp:
                result = await resp.json()
                return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to execute code: {str(e)}",
                "data": {
                    "output": "",
                    "errors": str(e),
                    "session": {"id": session_id}
                }
            }
            
    async def execute_command(self, command: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """执行命令"""
        payload = {"command": command}
        if session_id:
            payload["session_id"] = session_id
            
        try:
            async with self.http_client.post(f"{self.base_url}/execute/command", json=payload) as resp:
                result = await resp.json()
                return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to execute command: {str(e)}",
                "data": {
                    "output": "",
                    "errors": str(e),
                    "session": {"id": session_id}
                }
            }

    async def create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """创建新会话"""
        payload = {"session_id": session_id} if session_id else {"session_id": "jialtang-test"}
        
        try:
            async with self.http_client.post(f"{self.base_url}/sessions", json=payload) as resp:
                result = await resp.json()
                return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to create session: {str(e)}",
                "data": {
                    "output": "",
                    "errors": str(e),
                }
            }

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        try:
            async with self.http_client.get(f"{self.base_url}/sessions/{session_id}") as resp:
                result = await resp.json()
                return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get session: {str(e)}",
                "data": {
                    "output": "",
                    "errors": str(e),
                }
            }

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """删除会话"""
        try:
            async with self.http_client.delete(f"{self.base_url}/sessions/{session_id}") as resp:
                result = await resp.json()
                return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to delete session: {str(e)}",
                "data": {
                    "output": "",
                    "errors": str(e),
                }
            }


class Sandbox:
    """模拟原始e2b_code_interpreter.Sandbox类的接口"""
    
    def __init__(self, template: str = None, timeout: int = DEFAULT_TIMEOUT, api_key: str = None):
        self.client = SandboxClient()
        self.timeout = timeout
        self._session_id = None
        
    @classmethod
    async def connect(cls, session_id: str, api_key: str = None):
        """连接到现有的沙箱会话"""
        instance = cls()
        instance._session_id = session_id
        return instance
        
    async def get_info(self):
        """获取沙箱信息"""
        if not self._session_id:
            # 创建新会话
            result = await self.client.create_session()
            if result.get("session_id"):
                self._session_id = result.get("session_id")
            else:
                raise Exception(f"Failed to create sandbox: {result}")
                
        # 返回一个模拟对象
        class MockInfo:
            def __init__(self, session_id):
                self.sandbox_id = session_id
                
        return MockInfo(self._session_id)
    
    async def commands(self):
        """返回命令执行对象"""
        class Commands:
            def __init__(self, client, session_id):
                self.client = client
                self.session_id = session_id
                
            async def run(self, command: str):
                """运行命令"""
                result = await self.client.execute_command(command, self.session_id)
                
                class CommandResult:
                    def __init__(self, result):
                        self.stdout = result.get("data", {}).get("output", "")
                        self.stderr = result.get("data", {}).get("errors", "")
                        self.exit_code = 0 if result.get("status") == "success" else 1
                        self.error = result.get("data", {}).get("errors", "")
                        
                    def __str__(self):
                        return f"CommandResult(stdout='{self.stdout}', stderr='{self.stderr}', exit_code={self.exit_code})"
                        
                return CommandResult(result)
                
        return Commands(self.client, self._session_id)
    
    @property
    def commands(self):
        """直接访问命令执行接口"""
        class Commands:
            def __init__(self, client, session_id):
                self.client = client
                self._session_id = session_id
                
            async def run(self, command: str):
                """运行命令"""
                result = await self.client.execute_command(command, self._session_id)
                
                class CommandResult:
                    def __init__(self, result):
                        self.stdout = result.get("data", {}).get("output", "")
                        self.stderr = result.get("data", {}).get("errors", "")
                        self.exit_code = 0 if result.get("status") == "success" else 1
                        self.error = result.get("data", {}).get("errors", "")
                        
                    def __str__(self):
                        return f"CommandResult(stdout='{self.stdout}', stderr='{self.stderr}', exit_code={self.exit_code}, error='{self.error}')"
                        
                return CommandResult(result)
                
        return Commands(self.client, self._session_id)
    
    async def run_code(self, code_block: str):
        """运行Python代码块"""
        result = await self.client.execute_code(code_block, self._session_id)
        
        class ExecutionResult:
            def __init__(self, result):
                self.stdout = result.get("data", {}).get("output", "")
                self.stderr = result.get("data", {}).get("errors", "")
                self.exit_code = 0 if result.get("status") == "success" else 1
                self.error = result.get("data", {}).get("errors", "")
                
            def __str__(self):
                return f"ExecutionResult(stdout='{self.stdout}', stderr='{self.stderr}', exit_code={self.exit_code}, error='{self.error}')"
                
        return ExecutionResult(result)
    
    async def files(self):
        """返回文件操作对象"""
        class Files:
            def __init__(self, client, session_id):
                self.client = client
                self.session_id = session_id
                
            async def write(self, path, content):
                """写入文件（目前暂不实现，因为API中没有此功能）"""
                pass
                
            async def read(self, path, format="text"):
                """读取文件（目前暂不实现，因为API中没有此功能）"""
                pass
                
        return Files(self.client, self._session_id)
    
    @property
    def files(self):
        """直接访问文件操作接口"""
        class Files:
            def __init__(self, client, session_id):
                self.client = client
                self.session_id = session_id
                
            async def write(self, path, content):
                """写入文件（目前暂不实现，因为API中没有此功能）"""
                pass
                
            async def read(self, path, format="text"):
                """读取文件（目前暂不实现，因为API中没有此功能）"""
                pass
                
        return Files(self.client, self._session_id)
    
    def set_timeout(self, timeout: int):
        """设置超时"""
        self.timeout = timeout


def looks_like_dir(path: str) -> bool:
    """
    Return True if the given path either:
      - exists and is a directory, OR
      - does not exist but looks like a directory (e.g., ends with '/', or has no file extension)
    """
    # Since we're working with a remote API, we can't check actual filesystem
    # So we'll just infer from the path format
    if path.endswith('/') or not os.path.splitext(path)[1]:
        return True

    return False


def truncate_result(result: str) -> str:
    """
    Truncate result to MAX_RESULT_LEN.

    Args:
        result: The full result string to potentially truncate

    Returns:
        Truncated result string
    """
    if len(result) > MAX_RESULT_LEN:
        result = result[:MAX_RESULT_LEN] + " [Result truncated due to length limit]"

    return result


# Global client instance
_global_client = None


async def get_global_client():
    global _global_client
    if _global_client is None:
        _global_client = SandboxClient()
    return _global_client


async def create_sandbox(timeout: int = DEFAULT_TIMEOUT) -> str:
    """Create a linux sandbox.

    Args:
        timeout: Time in seconds before the sandbox is automatically shutdown. The default is 600 seconds.

    Returns:
        The sandbox_id of the newly created sandbox. You should use this sandbox_id to run other tools in the sandbox.
    """
    max_retries = 5
    timeout = min(timeout, DEFAULT_TIMEOUT)
    for attempt in range(1, max_retries + 1):
        sandbox = None
        try:
            sandbox = Sandbox()
            info = await sandbox.get_info()

            return f"Sandbox created with sandbox_id: {info.sandbox_id}"
        except Exception as e:
            if attempt == max_retries:
                error_details = str(e)[:MAX_ERROR_LEN]
                return f"[ERROR]: Failed to create sandbox after {max_retries} attempts: {error_details}, please retry later."
            await asyncio.sleep(attempt**2)  # Exponential backoff
        finally:
            # Set timeout before exit to prevent timeout after function exits
            try:
                if sandbox:
                    sandbox.set_timeout(timeout)
            except Exception:
                pass  # Ignore timeout setting errors


async def run_command(command: str, sandbox_id: str) -> str:
    """Execute a lightweight shell command in the linux sandbox (no long-running, blocking, or resource-heavy processes).

    Args:
        command: The command to execute.
        sandbox_id: The id of the sandbox to execute the command in. To create a new sandbox, use tool `create_sandbox`.

    Returns:
        A CommandResult object containing the result of the command execution, format like CommandResult(stderr=..., stdout=..., exit_code=..., error=...)
    """
    if sandbox_id in INVALID_SANDBOX_IDS:
        return f"[ERROR]: '{sandbox_id}' is not a valid sandbox_id. Please create a real sandbox first using the create_sandbox tool."

    try:
        sandbox = await Sandbox.connect(sandbox_id)
    except Exception:
        return f"[ERROR]: Failed to connect to sandbox {sandbox_id}. Make sure the sandbox is created and the sandbox_id is correct."

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            sandbox.set_timeout(
                DEFAULT_TIMEOUT
            )  # refresh the timeout for each command execution
            result = await sandbox.commands.run(command)

            result_str = str(result)
            return truncate_result(result_str)
        except Exception as e:
            if attempt == max_retries:
                # Build error message
                error_details = str(e)[:MAX_ERROR_LEN]
                error_msg = f"[ERROR]: Failed to run command after {max_retries} attempts.\n\nException type: {type(e).__name__}\nDetails: {error_details}"
                return error_msg
            await asyncio.sleep(attempt**2)  # Exponential backoff
        finally:
            # Set timeout before exit to prevent timeout after function exits
            try:
                sandbox.set_timeout(DEFAULT_TIMEOUT)
            except Exception:
                pass  # Ignore timeout setting errors


async def run_python_code(code_block: str, sandbox_id: str) -> str:
    """Run short, safe python code in a sandbox and return the execution result (avoid long loops or heavy tasks; must finish quickly).

    Args:
        code_block: The python code to run.
        sandbox_id: The id of the sandbox to run the code in. Reuse existing sandboxes whenever possible. To create a new sandbox, use tool `create_sandbox`.

    Returns:
        A CommandResult object containing the result of the command execution, format like CommandResult(stderr=..., stdout=..., exit_code=..., error=...)
    """
    if sandbox_id in INVALID_SANDBOX_IDS:
        return f"[ERROR]: '{sandbox_id}' is not a valid sandbox_id. Please create a real sandbox first using the create_sandbox tool."

    try:
        sandbox = await Sandbox.connect(sandbox_id)
    except Exception:
        return f"[ERROR]: Failed to connect to sandbox {sandbox_id}. Make sure the sandbox is created and the sandbox_id is correct."

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            sandbox.set_timeout(
                DEFAULT_TIMEOUT
            )  # refresh the timeout for each command execution

            execution = await sandbox.run_code(code_block)
            result_str = str(execution)
            return truncate_result(result_str)
        except Exception as e:
            if attempt == max_retries:
                error_details = str(e)[:MAX_ERROR_LEN]
                error_msg = f"[ERROR]: Failed to run code in sandbox {sandbox_id} after {max_retries} attempts. Exception type: {type(e).__name__}, Details: {error_details}"
                return error_msg
            await asyncio.sleep(attempt**2)  # Exponential backoff
        finally:
            # Set timeout before exit to prevent timeout after function exits
            try:
                sandbox.set_timeout(DEFAULT_TIMEOUT)
            except Exception:
                pass  # Ignore timeout setting errors