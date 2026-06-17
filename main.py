# FastAPI / UVicorn 相关依赖
from fastapi import FastAPI, Request
import uvicorn
# 引入全局 API 路由聚合器
from api.router import api_router
# CORS 中间件，允许跨域请求
from fastapi.middleware.cors import CORSMiddleware
import time
from logs.logging_server import logger
from dotenv import load_dotenv


# 创建 FastAPI 应用实例
app = FastAPI()
# 放行路径集合（无需 JWT 校验）
PUBLIC_PATHS = {"/register", "/login"}

# 注册全局 HTTP 中间件 所有进入项目的 HTTP 请求，都会先走这个中间件
@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    # OPTIONS 预检请求和公开路径直接放行
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    # 其余请求暂不校验，直接放行（占位）
    return await call_next(request)


@app.middleware("http")
async def log_cost(request: Request, call_next):
    start = time.time()
    # 处理请求
    resp = await call_next(request)
    # 响应后计算耗时
    cost = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url} 耗时 {cost}ms")
    return resp


# 注册 CORS 中间件，允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 挂载所有 API 路由
app.include_router(api_router)


# 启动入口
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=False)

