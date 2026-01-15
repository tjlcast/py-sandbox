

# 创建sessions目录用于存储所有session
from threading import Thread
import time
import os
import shutil
import re
from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 创建一个 APIRouter 实例
router = APIRouter()


SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)


class CreateSessionRequest(BaseModel):
    session_id: str = None  # 可选的自定义 session_id


class SessionResponse(BaseModel):
    session_id: str
    message: str


class SessionsResponse(BaseModel):
    session_ids: List[str]
    message: str


def is_valid_session_id(session_id: str) -> bool:
    """
    验证 session_id 是否合法（作为 Linux 目录名）
    """
    if not session_id or '..' in session_id or '/' in session_id:
        return False

    # 检查是否包含非法字符
    # Linux 文件名不能包含 '/'，Windows 文件名还有更多限制
    invalid_chars = r'[<>:"|?*\\/\x00-\x1f]'
    if re.search(invalid_chars, session_id):
        return False

    # 检查是否是特殊名称
    if session_id in ['.', '..']:
        return False

    # 检查长度（ext4 文件系统中单个文件名最大长度为 255 字节）
    if len(session_id.encode('utf-8')) > 255:
        return False

    return True


@router.post("/sessions",
             summary="创建新session",
             description="创建一个新的执行session，返回session_id",
             response_model=SessionResponse)
async def create_new_session(request: CreateSessionRequest = None):
    if request is None:
        session_id = str(uuid.uuid4())
    else:
        custom_session_id = request.session_id

        # 如果没有提供自定义 session_id，则生成新的 UUID
        if not custom_session_id:
            session_id = str(uuid.uuid4())
        else:
            # 验证提供的 session_id 是否合法
            if not is_valid_session_id(custom_session_id):
                raise HTTPException(
                    status_code=400, detail="Invalid session_id: Contains forbidden characters or is too long")

            # 检查是否已经存在该 session
            session_path = os.path.join(SESSIONS_DIR, custom_session_id)
            if os.path.exists(session_path):
                raise HTTPException(
                    status_code=409, detail=f"Session {custom_session_id} already exists")

            session_id = custom_session_id

    create_session_directory(session_id)
    return SessionResponse(
        session_id=session_id,
        message=f"Session {session_id} 创建成功"
    )


@router.get("/sessions",
            summary="查询session列表",
            description="获取所有活跃session的列表",
            response_model=SessionsResponse)
async def list_sessions():
    active_sessions = get_active_sessions()
    return SessionsResponse(
        session_ids=active_sessions,
        message=f"找到 {len(active_sessions)} 个会话"
    )


@router.get("/sessions/{session_id}",
            summary="查询特定session",
            description="获取指定session的信息",
            response_model=SessionResponse)
async def get_session(session_id: str):
    # 验证 session_id 是否合法
    if not is_valid_session_id(session_id):
        raise HTTPException(
            status_code=400, detail="Invalid session_id: Contains forbidden characters or is too long")

    session_path = os.path.join(SESSIONS_DIR, session_id)
    if not os.path.exists(session_path):
        raise HTTPException(
            status_code=404, detail=f"Session {session_id} does not exist")

    return SessionResponse(
        session_id=session_id,
        message=f"Session {session_id} 存在"
    )


@router.delete("/sessions/{session_id}",
               summary="删除指定session",
               description="删除指定的session及其所有文件",
               response_model=SessionResponse)
async def delete_session(session_id: str):
    # 验证 session_id 是否合法
    if not is_valid_session_id(session_id):
        raise HTTPException(
            status_code=400, detail="Invalid session_id: Contains forbidden characters or is too long")

    session_path = os.path.join(SESSIONS_DIR, session_id)
    if not os.path.exists(session_path):
        raise HTTPException(
            status_code=404, detail=f"Session {session_id} does not exist")

    cleanup_session(session_id)
    return SessionResponse(
        session_id=session_id,
        message=f"Session {session_id} 已删除"
    )


@router.delete("/sessions",
               summary="删除所有的session",
               description="删除所有的session及其所有文件",
               response_model=SessionsResponse)
async def delete_all_sessions():
    deleted_sessions = cleanup_all_sessions()
    if not deleted_sessions:
        return SessionsResponse(
            session_ids=[],
            message="没有活动的session可删除"
        )

    return SessionsResponse(
        session_ids=deleted_sessions,
        message=f"已删除 {len(deleted_sessions)} 个sessions: {deleted_sessions}"
    )


# 创建session的函数
def create_session_directory(session_id):
    session_path = os.path.join(SESSIONS_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)
    return session_path

# 获取活跃session的函数


def get_active_sessions():
    """获取所有活跃的session列表"""
    active_sessions = []
    for item in os.listdir(SESSIONS_DIR):
        item_path = os.path.join(SESSIONS_DIR, item)
        if os.path.isdir(item_path):  # 检查是否为目录
            active_sessions.append(item)
    return active_sessions

# 清理session的函数


def cleanup_session(session_id):
    session_path = os.path.join(SESSIONS_DIR, session_id)
    if os.path.exists(session_path):
        shutil.rmtree(session_path)

# 清理所有的session的函数


def cleanup_all_sessions():
    deleted_sessions = []
    active_sessions = get_active_sessions()
    for session_id in active_sessions:
        session_path = os.path.join(SESSIONS_DIR, session_id)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
            deleted_sessions.append(session_id)

    return deleted_sessions


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
