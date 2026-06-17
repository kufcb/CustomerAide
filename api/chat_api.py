# FastAPI 路由
from fastapi import APIRouter
# 请求体数据模型
from vo.chat_vo import ChatMsgVO
# SSE 流式响应
from fastapi.responses import StreamingResponse
# LangGraph 对话 Agent
from chat.agent_chat import stream_chat

# 创建聊天相关路由
router = APIRouter(tags=["chat"])


@router.post("/stream_chat")
async def stream_chat_api(user: ChatMsgVO):
    """
    流式聊天接口。
    接收用户消息，通过 LangGraph Agent 检索 RAG 知识库并调用 LLM，
    以 Server-Sent Events 格式流式返回回复内容。
    """
    return StreamingResponse(
        stream_chat(user.message),
        media_type="text/event-stream"
    )