# LangGraph 状态图构建
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import Annotated, Literal, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import os
from logs.logging_server import logger
from hybrid_rag import build_to_llm_hybrid_search_str
from chat.query_rewrite import rewrite_query
from langchain_openai import ChatOpenAI
from config import (
    ALI_MODEL_KEY,
    ALI_MODEL_BASE_URL,
    ALI_MODEL_NAME,
    TOOL_CALLING_ENABLED,
    TOOL_CALLING_MAX_ITERATIONS,
)
from tools.ecommerce_tools import ECOMMERCE_TOOLS


class AgentState(TypedDict):
    """LangGraph Agent 的状态定义"""
    messages: Annotated[list, add_messages]
    rag_info: str
    tool_iterations: int


llm = ChatOpenAI(
    api_key=ALI_MODEL_KEY,
    base_url=ALI_MODEL_BASE_URL,
    model=ALI_MODEL_NAME,
)

llm_with_tools = llm.bind_tools(ECOMMERCE_TOOLS)
tool_node = ToolNode(ECOMMERCE_TOOLS)


def load_prompt_content(name: str) -> str:
    file_path = os.path.join("prompts", f"{name}.txt")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        logger.info(f"已加载 {name} 提示词，路径: {file_path}, 长度: {len(content)} 字符")
        return content


_prompt_name = "e_commerce_tool_calling" if TOOL_CALLING_ENABLED else "e_commerce_prompt_example"
system_content = load_prompt_content(_prompt_name)
system_prompt = SystemMessage(content=system_content)


def _build_llm_input(state: AgentState) -> list:
    rag_info = state.get("rag_info", "")
    llm_input = [system_prompt]
    if rag_info:
        llm_input.append(HumanMessage(content=rag_info))
    llm_input.extend(state["messages"])
    return llm_input


def call_rag(state: AgentState):
    last_msg = state["messages"][-1]
    query = last_msg.content
    search_query = rewrite_query(query)
    rag_info = build_to_llm_hybrid_search_str(search_query, None)
    logger.info("rag检索信息: %s", rag_info[:200] if rag_info else "")
    return {"rag_info": rag_info, "tool_iterations": 0}


def call_llm(state: AgentState):
    llm_input = _build_llm_input(state)
    logger.info("llm 请求（无 tools）")
    response = llm.invoke(llm_input)
    return {"messages": [response]}


def agent_with_tools(state: AgentState):
    llm_input = _build_llm_input(state)
    logger.info("agent 请求（含 tools）")
    response = llm_with_tools.invoke(llm_input)
    if response.tool_calls:
        logger.info("模型请求调用工具: %s", [t["name"] for t in response.tool_calls])
    return {"messages": [response]}


def run_tools(state: AgentState):
    result = tool_node.invoke(state)
    iterations = state.get("tool_iterations", 0) + 1
    return {**result, "tool_iterations": iterations}


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    last = state["messages"][-1]
    if not isinstance(last, AIMessage) or not last.tool_calls:
        return "end"
    if state.get("tool_iterations", 0) >= TOOL_CALLING_MAX_ITERATIONS:
        logger.warning("已达 Tool Calling 最大迭代次数 %s", TOOL_CALLING_MAX_ITERATIONS)
        return "end"
    return "tools"


def _build_graph():
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("call_rag", call_rag)

    if TOOL_CALLING_ENABLED:
        graph_builder.add_node("agent", agent_with_tools)
        graph_builder.add_node("tools", run_tools)
        graph_builder.set_entry_point("call_rag")
        graph_builder.add_edge("call_rag", "agent")
        graph_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
        graph_builder.add_edge("tools", "agent")
    else:
        graph_builder.add_node("call_llm", call_llm)
        graph_builder.set_entry_point("call_rag")
        graph_builder.add_edge("call_rag", "call_llm")
        graph_builder.add_edge("call_llm", END)

    return graph_builder.compile()


graph = _build_graph()


async def stream_chat(user_input: str):
    """异步生成器：执行 LangGraph 工作流并以流式方式产出 LLM 回复 Token。"""
    logger.info("用户输入: %s", user_input)
    output_info = ""
    for chunk, _ in graph.stream(
        {"messages": [HumanMessage(content=user_input)]},
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessage) and chunk.content:
            output_info += chunk.content
            yield chunk.content
    logger.info("AI回复: %s", output_info)
