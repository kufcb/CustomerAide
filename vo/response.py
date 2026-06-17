# FastAPI JSON 响应
from fastapi.responses import JSONResponse


def res_body(code: int, message: str, data):
    """构造统一格式的响应体字典：包含状态码、消息和数据"""
    return {"code": code, "message": message, "data": data}


def error_response(code: int, message: str, data="") -> JSONResponse:
    """构造统一格式的错误 JSON 响应"""
    return JSONResponse(status_code=code, content=res_body(code, message, data))
