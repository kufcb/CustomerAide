# Pydantic 数据模型
from pydantic import BaseModel


class ChatMsgVO(BaseModel):
    """聊天请求体模型，包含用户发送的消息文本"""
    message: str

