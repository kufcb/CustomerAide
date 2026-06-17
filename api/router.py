# FastAPI 路由聚合器
from fastapi import APIRouter

# 导入各子模块的路由
from api.chat_api import router as chat_router
from api.file_upload import router as file_router


# 创建全局 API 路由实例，统一挂载所有子路由
api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(file_router)