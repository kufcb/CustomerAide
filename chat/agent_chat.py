# LangGraph 状态图构建
from langgraph.graph import StateGraph
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
# Ollama 大语言模型
from langchain_ollama import ChatOllama
# LangChain 消息类型
from langchain_core.messages import HumanMessage, SystemMessage
import os
from logs.logging_server import logger
# RAG 检索函数（纯向量 / 混合）
from hybrid_rag import build_to_llm_hybrid_search_str
from chat.query_rewrite import rewrite_query
from langchain_openai import ChatOpenAI
from config import ALI_MODEL_KEY,ALI_MODEL_BASE_URL,ALI_MODEL_NAME


class AgentState(TypedDict):
    """LangGraph Agent 的状态定义，消息列表使用 add_messages 注解实现增量合并"""
    messages: Annotated[list, add_messages]
    rag_info: str


# 创建 Ollama LLM 实例
# llm = ChatOllama(
#     model="qwen2.5:3b",
#     base_url="http://127.0.0.1:11434"
# )

llm = ChatOpenAI(
    api_key=ALI_MODEL_KEY,
    base_url=ALI_MODEL_BASE_URL,
    model=ALI_MODEL_NAME
)


def load_prompt_content(name: str) -> str:
    """加载提示词文件内容"""
    file_path = os.path.join("prompts", f"{name}.txt")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        logger.info(f"已加载 {name} 提示词，路径: {file_path}, 长度: {len(content)} 字符")
        return content


# 加载系统提示词
system_content = load_prompt_content("e_commerce_prompt_example")
system_prompt = SystemMessage(content=system_content)


def call_llm(state: AgentState):
    """LangGraph 节点：调用 LLM 生成回复"""
    rag_info = state.get("rag_info", "")
    llm_input_info = [system_prompt] + [rag_info] + list(state["messages"])
    logger.info("llm请求原文")
    logger.info(llm_input_info)
    response = llm.invoke(llm_input_info)
    return {"messages": [response]}


def call_rag(state: AgentState):
    """LangGraph 节点：执行 RAG 检索，获取参考信息"""
    last_msg = state["messages"][-1]
    query = last_msg.content
    search_query = rewrite_query(query)
    rag_info = build_to_llm_hybrid_search_str(search_query, None)
    logger.info("rag检索信息")
    logger.info(rag_info)
    return {"rag_info": rag_info}


# 构建 LangGraph 状态图
graph_builder = StateGraph(AgentState)
# 添加两个节点：RAG 检索 → LLM 生成
graph_builder.add_node("call_rag", call_rag)
graph_builder.add_node("call_llm", call_llm)
# 设置入口点：先执行 RAG 检索
graph_builder.set_entry_point("call_rag")
# RAG 检索完成后执行 LLM 生成
graph_builder.add_edge("call_rag", "call_llm")
# 编译图，生成可执行工作流
graph = graph_builder.compile()


async def stream_chat(user_input: str):
    """
    异步生成器：执行 LangGraph 工作流并以流式方式产出 LLM 回复 Token。
    使用 SSE 格式返回给前端。
    """
    logger.info(f"用户输入: {user_input}")
    output_info = ""
    for chunk, _ in graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            stream_mode="messages"
    ):
        if chunk.content:
            output_info += chunk.content
            yield chunk.content
    logger.info(f"AI回复: {output_info}")