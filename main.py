from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware
import subprocess
from utils import check_code_safety

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许的HTTP方法
    allow_headers=["*"],  # 允许的HTTP头
)

# 定义全局线程池
executor = ThreadPoolExecutor(max_workers=10)

# 定义数据模型


class CodeSnippet(BaseModel):
    code: str

# 执行代码的函数


def execute_code(code):
    check_code_safety(code)

    def run_in_sandbox():
        try:
            result = subprocess.run(
                ["python3", "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return result.stdout.decode("utf-8"), result.stderr.decode("utf-8")
        except Exception as e:
            return "", f"错误: {str(e)}"

    future = executor.submit(run_in_sandbox)
    try:
        output, errors = future.result(timeout=1)  # 设置超时时间
    except TimeoutError:
        return "", "运行时间超出限制"
    except Exception as e:
        return output, errors


@app.post("/execute",
          summary="执行代码片段",
          description="在安全沙箱环境中执行提供的 Python 代码片段，并返回执行结果。",
          responses={
              200: {
                  "description": "代码执行结果",
                  "content": {
                      "application/json": {
                          "examples": {
                              "success": {
                                  "summary": "执行成功示例",
                                  "value": {
                                      "status": "success",
                                      "message": "代码执行成功",
                                      "data": {
                                          "output": "Hello, World!\n",
                                          "errors": ""
                                      }
                                  }
                              },
                              "error": {
                                  "summary": "执行出错示例",
                                  "value": {
                                      "status": "error",
                                      "message": "遇到执行错误",
                                      "data": {
                                          "output": "",
                                          "errors": "NameError: name 'undefined_var' is not defined"
                                      }
                                  }
                              }
                          }
                      }
                  }
              }
          })
async def execute_code_snippet(snippet: CodeSnippet, request: Request):
    try:
        print(f"Request Body: {await request.body()}")  # 打印请求体
        output, errors = execute_code(snippet.code)

        # 根据执行结果返回不同的响应
        if errors:
            return {
                "status": "error",
                "message": "遇到执行错误",
                "data": {
                    "output": output,
                    "errors": errors,
                }
            }
        else:
            return {
                "status": "success",
                "message": "代码执行成功",
                "data": {
                    "output": output,
                    "errors": errors,
                }
            }
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Security Error: {str(e)}")
    except Exception as e:
        # 发生未知错误时，返回 error 状态和详细信息
        return {
            "status": "error",
            "message": f"Execution failed: {str(e)}",
            "data": None
        }
