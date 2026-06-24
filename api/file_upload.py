# FastAPI 路由及文件上传相关
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import os
import uuid
# 统一响应格式
from vo.response import res_body
# 混合检索引擎（上传后重建 BM25 索引）
from hybrid_rag import get_engine,vector_input_txt
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, EMBEDDING_MODEL

router = APIRouter(tags=["Knowledge Base"])

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), knowledge_base: str = Form("默认")):
    """
    文件上传接口：
    1. 校验文件扩展名和大小
    2. 保存文件到 对应 目录(UUID 防重名）
    3. 写入向量知识库（分块 + embedding)
    4. 重建 BM25 索引
    """

    if file is None or file.filename is None:
        raise HTTPException(status_code=400, detail=f"没有文件")
    # 校验文件扩展名
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，允许: {ALLOWED_EXTENSIONS}")

    # 校验文件大小（读取时校验）
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"文件过大，最大允许 {MAX_FILE_SIZE // 1024 // 1024}MB")

    # 保存文件（UUID 防重名）
    save_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    with open(save_path, "wb") as f:
        f.write(content)

    # 写入 RAG 知识库
    try:
        if ext == ".txt":
            vector_input_txt(save_path, knowledge_base)
        else:
            raise HTTPException(status_code=400, detail=f"暂时只支持txt")
        # 刷新 BM25 混合检索索引
        get_engine().rebuild_index()
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(
            status_code=503,
            detail=f"知识库写入失败，请确认 Ollama 已启动且已拉取嵌入模型 {EMBEDDING_MODEL}：{e}",
        ) from e
    return res_body(200, "上传成功", {"filename": save_name, "size": len(content)})