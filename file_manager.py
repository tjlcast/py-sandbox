from threading import Thread
import time
import os
import shutil
import re
from typing import List, Optional, Dict
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sessions_manager import SESSIONS_DIR as SESSIONS_DIR_BASE
from sessions_manager import is_valid_session_id

# 创建一个 APIRouter 实例
router = APIRouter()

SESSIONS_DIR = SESSIONS_DIR_BASE


class SessionAwared(BaseModel):
    session_id: str = None


class UploadLocalFileRequest(BaseModel):
    fileName: str
    fileContent: str


class UploadLocalFileResposne(SessionAwared):
    fileName: str
    message: str


class DownloadFileRequest(BaseModel):
    fileName: str


class DownloadFileResposne(SessionAwared):
    fileName: str
    fileContent: str
    message: str


class FileDetail(BaseModel):
    fileName: str
    fileSize: int
    createdAt: float
    modifiedAt: float


class ListFilesResponse(SessionAwared):
    fileNames: Dict[str, FileDetail]
    fileNum: int
    message: str


@router.get("/files/{session_id}",
            summary="列出文件",
            description="列出当前session所有的文件",
            response_model=ListFilesResponse)
def list_files(session_id: str):
    # 验证 session_id
    if not session_id or not is_valid_session_id(session_id):
        raise HTTPException(
            status_code=400, detail="Invalid session_id: Contains forbidden characters or is too long")

    # 检查 session 目录是否存在
    session_path = os.path.join(SESSIONS_DIR, session_id)
    if not os.path.exists(session_path) or not os.path.isdir(session_path):
        raise HTTPException(
            status_code=404, detail=f"Session {session_id} does not exist")

    # 获取目录下所有文件的信息
    file_details = {}
    for file_name in os.listdir(session_path):
        file_path = os.path.join(session_path, file_name)
        if os.path.isfile(file_path):  # 只处理文件，忽略子目录
            stat_info = os.stat(file_path)
            file_detail = FileDetail(
                fileName=file_name,
                fileSize=stat_info.st_size,
                createdAt=stat_info.st_ctime,
                modifiedAt=stat_info.st_mtime
            )
            file_details[file_name] = file_detail

    file_num = len(file_details)
    return ListFilesResponse(
        session_id=session_id,
        fileNames=file_details,
        fileNum=file_num,
        message=f"Found {file_num} files in session {session_id}"
    )


@router.post("/files/{session_id}",
             summary="上传文件",
             description="上传文件到指定session",
             response_model=UploadLocalFileResposne)
def upload_file(session_id: str, req: UploadLocalFileRequest):
    # 验证 session_id
    if not session_id or not is_valid_session_id(session_id):
        raise HTTPException(
            status_code=400, detail="Invalid session_id: Contains forbidden characters or is too long")

    # 确保session_id与请求体中的session_id一致
    if not session_id:
        raise HTTPException(
            status_code=400, detail="Session ID in request body does not match URL")

    # 验证文件名
    if not req.fileName or '..' in req.fileName or '/' in req.fileName or '\\' in req.fileName:
        raise HTTPException(
            status_code=400, detail="Invalid filename: Contains forbidden characters")

    # 检查 session 目录是否存在
    session_path = os.path.join(SESSIONS_DIR, session_id)
    if not os.path.exists(session_path) or not os.path.isdir(session_path):
        raise HTTPException(
            status_code=404, detail=f"Session {session_id} does not exist")

    # 构建文件路径并写入文件
    file_path = os.path.join(session_path, req.fileName)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(req.fileContent)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to write file: {str(e)}")

    return UploadLocalFileResposne(
        session_id=session_id,
        fileName=req.fileName,
        message=f"File {req.fileName} uploaded successfully to session {session_id}"
    )


@router.get("/files/{session_id}/{file_name}",
            summary="下载文件",
            description="读取指定session的文件内容",
            response_model=DownloadFileResposne)
def download_file(session_id: str, file_name: str):
    # 验证 session_id
    if not session_id or not is_valid_session_id(session_id):
        raise HTTPException(
            status_code=400, detail="Invalid session_id: Contains forbidden characters or is too long")

    # 验证文件名
    if not file_name or '..' in file_name or '/' in file_name or '\\' in file_name:
        raise HTTPException(
            status_code=400, detail="Invalid filename: Contains forbidden characters")

    # 检查 session 目录是否存在
    session_path = os.path.join(SESSIONS_DIR, session_id)
    if not os.path.exists(session_path) or not os.path.isdir(session_path):
        raise HTTPException(
            status_code=404, detail=f"Session {session_id} does not exist")

    # 构建文件路径并读取文件
    file_path = os.path.join(session_path, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, detail=f"File {file_name} does not exist in session {session_id}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read file: {str(e)}")

    return DownloadFileResposne(
        session_id=session_id,
        fileName=file_name,
        fileContent=file_content,
        message=f"File {file_name} downloaded successfully from session {session_id}"
    )
