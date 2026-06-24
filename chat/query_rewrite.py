"""检索前查询改写：口语化问题 → 更适合检索的表述"""
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from config import (
    ALI_MODEL_BASE_URL,
    ALI_MODEL_KEY,
    ALI_MODEL_NAME,
    QUERY_REWRITE_MODE,
    QUERY_REWRITE_TIMEOUT,
)
from logs.logging_server import logger

# 常见电商口语 → 检索关键词映射
_SYNONYMS = {
    "咋": "怎么",
    "啥": "什么",
    "啥时候": "什么时候",
    "几天": "多少天",
    "包邮吗": "是否包邮 运费",
    "能退吗": "退货 退款",
    "不想要了": "退货 退款",
    "坏了": "质量问题 售后",
    "没到": "物流 未送达",
    "查不到": "物流 查询",
}

_rewrite_llm: Optional[ChatOpenAI] = None
_rewrite_prompt_template: Optional[str] = None


def _get_rewrite_llm() -> ChatOpenAI:
    global _rewrite_llm
    if _rewrite_llm is None:
        _rewrite_llm = ChatOpenAI(
            api_key=ALI_MODEL_KEY,
            base_url=ALI_MODEL_BASE_URL,
            model=ALI_MODEL_NAME,
            temperature=0,
        )
    return _rewrite_llm


def _load_rewrite_prompt() -> str:
    global _rewrite_prompt_template
    if _rewrite_prompt_template is None:
        file_path = os.path.join("prompts", "query_rewrite_prompt.txt")
        with open(file_path, "r", encoding="utf-8") as f:
            _rewrite_prompt_template = f.read()
    return _rewrite_prompt_template


def rule_rewrite(query: str) -> str:
    """轻量规则改写，不依赖额外 LLM 调用。"""
    if not query.strip():
        return query

    text = query.strip()
    for src, dst in _SYNONYMS.items():
        text = text.replace(src, dst)

    text = re.sub(r"[？?！!。，,；;]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def llm_rewrite(query: str, history: Optional[list] = None) -> str:
    """使用 LLM 将查询改写为检索友好表述。history 预留多轮上下文扩展。"""
    del history  # 单轮场景暂未使用，保留参数供后续多轮改写
    prompt_template = _load_rewrite_prompt()
    prompt = prompt_template.format(query=query)
    llm = _get_rewrite_llm()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(llm.invoke, [HumanMessage(content=prompt)])
        try:
            response = future.result(timeout=QUERY_REWRITE_TIMEOUT)
        except FuturesTimeoutError as exc:
            raise TimeoutError(f"查询改写超时（{QUERY_REWRITE_TIMEOUT}s）") from exc

    rewritten = (response.content or "").strip()
    if not rewritten:
        raise ValueError("LLM 返回空改写结果")

    rewritten = rewritten.splitlines()[0].strip()
    return rewritten


def rewrite_query(query: str, history: Optional[list] = None) -> str:
    """统一入口：按 QUERY_REWRITE_MODE 选择策略，失败时回退。"""
    if not query or not query.strip():
        return query

    original = query.strip()
    mode = QUERY_REWRITE_MODE

    if mode == "off":
        return original

    rule_result = rule_rewrite(original)

    if mode == "rule":
        if rule_result != original:
            logger.info(f"查询改写: {original!r} -> {rule_result!r}")
        return rule_result

    if mode == "llm":
        try:
            rewritten = llm_rewrite(rule_result, history)
            if rewritten != original:
                logger.info(f"查询改写: {original!r} -> {rewritten!r}")
            return rewritten
        except Exception as exc:
            logger.warning(f"LLM 查询改写失败，回退规则结果: {exc}")
            if rule_result != original:
                logger.info(f"查询改写(规则回退): {original!r} -> {rule_result!r}")
            return rule_result

    logger.warning(f"未知 QUERY_REWRITE_MODE={mode!r}，跳过改写")
    return original
