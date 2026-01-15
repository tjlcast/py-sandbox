#!/usr/bin/env python3
"""
这是一个使用MCP ClientSession与本地sandbox API交互的示例客户端
展示了如何使用ClientSession和call_tool来调用工具函数
"""

import asyncio
import sys
from mcp.client.stdio import stdio_client
# (already imported in config.py)
from mcp import ClientSession, StdioServerParameters


async def run_client_with_session():
    """
    展示如何使用ClientSession和call_tool来调用工具
    """
    print("=== MCP ClientSession Example ===")

    # 模拟MCP服务器参数
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_utils.python_mcp_server"],
        env={"E2B_API_KEY": "xxx"},
    )

    print("\n1. Establishing connection to MCP server...")
    # 使用stdio_client建立与MCP服务器的连接
    async with stdio_client(server_params) as (read, write):
        # 创建MCP客户端会话
        async with ClientSession(read, write) as session:
            # 初始化会话
            await session.initialize()
            print("✅ Session initialized successfully!")

            try:
                # 列出可用工具
                print("\n2. Listing available tools...")
                tools = await session.list_tools()
                print(f"Available tools:")
                for tool in tools.tools:
                    print(
                        f"FUNC_NAME:\n{tool.name}\nFUNC_DESC:\n{tool.description}")
                    print(
                        "============================================================================")

                # 调用create_sandbox_tool创建沙箱
                print("\n3. Calling create_sandbox_tool...")
                tool_result = await session.call_tool(
                    "create_sandbox_tool", arguments={"timeout": 600, "sandbox_id": "123"}
                )
                result_content = (
                    tool_result.content[-1].text
                    if tool_result.content
                    else ""
                )
                print(f"Sandbox creation result: {result_content}")

                # 提取sandbox ID
                if "Sandbox created with sandbox_id: " in result_content:
                    sandbox_id = result_content.replace(
                        "Sandbox created with sandbox_id: ", "").strip()
                    print(f"Extracted sandbox ID: {sandbox_id}")

                    # 调用run_python_code_tool执行Python代码
                    print("\n4. Calling run_python_code_tool...")
                    python_code = """
import numpy as np
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Mean: {np.mean(arr)}")
"""
                    code_result = await session.call_tool(
                        "run_python_code_tool",
                        arguments={
                            "code_block": python_code,
                            "sandbox_id": sandbox_id
                        }
                    )
                    code_result_content = (
                        code_result.content[-1].text
                        if code_result.content
                        else ""
                    )
                    print(
                        f"Python code execution result: {code_result_content}")

                    # 调用run_command_tool执行命令
                    print("\n5. Calling run_command_tool...")
                    command_result = await session.call_tool(
                        "run_command_tool",
                        arguments={
                            "command": "echo 'Hello from sandbox!'",
                            "sandbox_id": sandbox_id
                        }
                    )
                    command_result_content = (
                        command_result.content[-1].text
                        if command_result.content
                        else ""
                    )
                    print(
                        f"Command execution result: {command_result_content}")

            except Exception as e:
                print(f"❌ Error occurred during tool calls: {str(e)}")
            finally:
                # 使用DELETE请求清理sandbox
                import aiohttp
                async with aiohttp.ClientSession() as http_session:
                    if not 'sandbox_id' in locals():
                        print("⚠️ No sandbox_id found, skipping cleanup.")
                        return
                    else:
                        print(f"\n6. Cleaning up {sandbox_id} sandbox...")
                    try:
                        cleanup_url = f"http://localhost:8000/session/{sandbox_id}"
                        async with http_session.delete(cleanup_url, headers={'accept': 'application/json'}) as resp:
                            if resp.status == 200:
                                print(
                                    f"✅ Successfully cleaned up session {sandbox_id}")
                            else:
                                print(
                                    f"⚠️ Failed to clean up session {sandbox_id}, status code: {resp.status}")
                    except Exception as cleanup_error:
                        print(
                            f"❌ Error occurred during cleanup: {str(cleanup_error)}")


async def advanced_client_session_usage():
    """
    更高级的ClientSession使用示例，展示了错误处理和进度回调
    """
    print("\n=== Advanced MCP ClientSession Usage ===")

    server_params = {
        "command": sys.executable,
        "args": ["-c", """fastmcp_adapter"""]
    }

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            try:
                # 示例：带错误处理的工具调用
                print("\n1. Calling tool with error handling...")
                tool_result = await session.call_tool(
                    "calculate_sum", arguments={"a": 10, "b": 20}
                )
                result_content = (
                    tool_result.content[-1].text
                    if tool_result.content
                    else str(tool_result.structured_contents)
                )
                print(f"Calculation result: {result_content}")

                # 示例：处理可能的错误情况
                print("\n2. Testing error handling...")
                try:
                    # 调用一个不存在的工具，应该会引发异常
                    non_existent_result = await session.call_tool(
                        "non_existent_tool", arguments={}
                    )
                except Exception as e:
                    print(
                        f"Successfully caught expected error: {type(e).__name__}: {str(e)}")

            except Exception as tool_error:
                print(f"Tool execution error: {str(tool_error)}")


if __name__ == "__main__":
    print("Running basic ClientSession example...")
    asyncio.run(run_client_with_session())

    print("\nRunning advanced ClientSession example...")
    # asyncio.run(advanced_client_session_usage())

    print("\n✅ ClientSession examples completed!")
