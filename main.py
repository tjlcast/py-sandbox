from sessions_manager import router as code_snippet_router
import os
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware
import subprocess
from sessions_manager import SESSIONS_DIR, create_session_directory
from utils import check_code_safety

app = FastAPI(docs_url=None, redoc_url=None)  # 禁用默认文档

# 挂载静态文件目录（用于离线资源）
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


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

# 导入其他模块中的路由

# 将路由添加到主应用
app.include_router(code_snippet_router)

# 定义数据模型


class CodeSnippet(BaseModel):
    code: str = Field(..., example="print('Hello, World!')",
                      description="要执行的Python代码片段")
    session_id: str = None  # 可选session_id，如果不提供则创建新session


# 执行代码的函数


def execute_code(code, session_path):
    check_code_safety(code)

    def run_in_sandbox():
        try:
            result = subprocess.run(
                ["python", "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=session_path,  # 设置工作目录为session目录
                timeout=30  # 设置超时时间为30秒
            )
            return result.stdout.decode("utf-8"), result.stderr.decode("utf-8")
        except Exception as e:
            return "", f"错误: {str(e)}"

    future = executor.submit(run_in_sandbox)
    try:
        output, errors = future.result(timeout=1)  # 设置超时时间
        print(f"output: {output}")
    except TimeoutError:
        return "", "运行时间超出限制"
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

        # 处理session
        if snippet.session_id:
            # 使用现有session
            session_id = snippet.session_id
            session_path = os.path.join(SESSIONS_DIR, session_id)
            if not os.path.exists(session_path):
                raise HTTPException(status_code=404, detail="Session不存在")
        else:
            # 创建新session
            session_id = str(uuid.uuid4())
            session_path = create_session_directory(session_id)

        print(f"Session Path: {session_path}")  # 打印请求体
        output, errors = execute_code(snippet.code, session_path)

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
