"""复用线上检索 + Agent 管线，为评测产出每条问题的 answer 与 contexts。

为保证与线上一致，这里直接复用：
- chat.query_rewrite.rewrite_query  （检索前查询改写）
- hybrid_rag.get_engine().search    （BM25 + 向量 + RRF + 重排 的混合检索）
- chat.agent_chat 的 llm / system_prompt （同一套电商客服系统提示与模型）

与 agent_chat.call_rag + call_llm 的差异：这里只检索一次，并把实际用到的
检索片段（contexts）一并返回，供 RAGAS 计算检索类指标。
"""
from typing import Dict, List, TypedDict

from langchain_core.messages import HumanMessage

from logs.logging_server import logger
from chat.query_rewrite import rewrite_query
from hybrid_rag import get_engine
# 复用线上同一套 LLM 与系统提示词，保证评测与生产行为一致
from chat.agent_chat import llm, system_prompt


class EvalSample(TypedDict):
    """单条评测样本：交给 RAGAS 的最小字段集合。"""
    question: str          # 原始用户问题
    search_query: str      # 改写后的检索 query
    contexts: List[str]    # 实际检索到的参考片段
    answer: str            # Agent 生成的回复


def _build_rag_info(contexts: List[str]) -> str:
    """按 hybrid_rag.build_to_llm_hybrid_search_str 的格式拼接参考信息字符串。"""
    if not contexts:
        return (
            "[参考信息] \n"
            "非常抱歉，目前的知识库中暂未找到该问题的具体信息，建议您联系人工客服获取帮助。"
        )
    return "[参考信息] \n" + "".join(contexts)


def run_pipeline(question: str) -> EvalSample:
    """对单条问题执行：查询改写 -> 混合检索 -> LLM 生成，返回评测样本。"""
    search_query = rewrite_query(question)
    results = get_engine().search(search_query)
    contexts = [r["content"] for r in results]

    rag_info = _build_rag_info(contexts)
    llm_input = [system_prompt, rag_info, HumanMessage(content=question)]
    response = llm.invoke(llm_input)
    answer = response.content or ""

    logger.info(f"[eval] 问题: {question!r} -> 检索片段数: {len(contexts)}")
    return EvalSample(
        question=question,
        search_query=search_query,
        contexts=contexts,
        answer=answer,
    )


def run_pipeline_batch(questions: List[str]) -> List[EvalSample]:
    """批量执行管线，逐条返回评测样本。"""
    samples: List[EvalSample] = []
    for i, q in enumerate(questions, 1):
        logger.info(f"[eval] 运行管线 {i}/{len(questions)}")
        samples.append(run_pipeline(q))
    return samples
