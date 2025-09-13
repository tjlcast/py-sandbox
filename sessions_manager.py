

# 创建sessions目录用于存储所有session
from threading import Thread
import time
import os
import shutil
import uuid

from fastapi import APIRouter
from pydantic import BaseModel

# 创建一个 APIRouter 实例
router = APIRouter()


SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)


class SessionResponse(BaseModel):
    session_id: str
    message: str


@router.post("/session/new",
             summary="创建新session",
             description="创建一个新的执行session，返回session_id",
             response_model=SessionResponse)
async def create_new_session():
    session_id = str(uuid.uuid4())
    create_session_directory(session_id)
    return SessionResponse(
        session_id=session_id,
        message=f"Session {session_id} 创建成功"
    )


@router.delete("/session/{session_id}",
               summary="删除session",
               description="删除指定的session及其所有文件",
               response_model=SessionResponse)
async def delete_session(session_id: str):
    cleanup_session(session_id)
    return SessionResponse(
        session_id=session_id,
        message=f"Session {session_id} 已删除"
    )


# 创建session的函数


def create_session_directory(session_id):
    session_path = os.path.join(SESSIONS_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)
    return session_path

# 清理session的函数


def cleanup_session(session_id):
    session_path = os.path.join(SESSIONS_DIR, session_id)
    if os.path.exists(session_path):
        shutil.rmtree(session_path)


# 添加一个定时清理过期session的功能（可选）


def cleanup_old_sessions(max_age_hours=24):
    """清理超过指定时间的session"""
    while True:
        try:
            print("Cleaning up old sessions...")
            now = time.time()
            for session_id in os.listdir(SESSIONS_DIR):
                session_path = os.path.join(SESSIONS_DIR, session_id)
                if os.path.isdir(session_path):
                    # 检查目录最后修改时间
                    if now - os.path.getmtime(session_path) > max_age_hours * 3600:
                        cleanup_session(session_id)
                        print(f"Cleaned up old session: {session_id}")
            time.sleep(3600)  # 每小时检查一次
        except Exception as e:
            print(f"Error in cleanup thread: {e}")
            time.sleep(300)


# 启动清理线程
cleanup_thread = Thread(target=cleanup_old_sessions, daemon=True)
cleanup_thread.start()
