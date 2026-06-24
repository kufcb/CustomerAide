"""RAGAS 评估封装：配置裁判 LLM / embedding 与指标，并执行评估。

裁判 LLM 复用 config.py 的阿里模型，embedding 复用 Ollama bge-m3，
不引入新的模型服务。

指标（同时覆盖检索层与生成层）：
- Faithfulness                     生成层：答案是否忠于参考信息（防幻觉）
- ResponseRelevancy                生成层：答案与问题的相关性
- LLMContextPrecisionWithReference 检索层：检索到的片段是否相关（对照标准答案）
- LLMContextRecall                 检索层：标准答案信息是否被检索覆盖
"""
import warnings
from typing import List

# 必须在 import ragas 之前打补丁（ragas 0.4 硬导入已下线的 Vertex 模块）
from eval._compat import patch_langchain_vertex

patch_langchain_vertex()

from langchain_openai import ChatOpenAI  # noqa: E402
from langchain_ollama import OllamaEmbeddings  # noqa: E402

from ragas import EvaluationDataset, SingleTurnSample, evaluate  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import (  # noqa: E402
        Faithfulness,
        ResponseRelevancy,
        LLMContextPrecisionWithReference,
        LLMContextRecall,
    )

from config import (  # noqa: E402
    ALI_MODEL_KEY,
    ALI_MODEL_BASE_URL,
    ALI_MODEL_NAME,
    EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
)
from eval.pipeline_runner import EvalSample  # noqa: E402


# 指标中文名映射，便于报告展示
METRIC_LABELS = {
    "faithfulness": "忠实度(Faithfulness)",
    "answer_relevancy": "答案相关性(ResponseRelevancy)",
    "llm_context_precision_with_reference": "上下文精确率(ContextPrecision)",
    "context_recall": "上下文召回率(ContextRecall)",
}


def get_ragas_llm() -> LangchainLLMWrapper:
    """构造 RAGAS 裁判 LLM（复用阿里模型，temperature=0 保证评分稳定）。"""
    chat = ChatOpenAI(
        api_key=ALI_MODEL_KEY,
        base_url=ALI_MODEL_BASE_URL,
        model=ALI_MODEL_NAME,
        temperature=0,
    )
    return LangchainLLMWrapper(chat)


def get_ragas_embeddings() -> LangchainEmbeddingsWrapper:
    """构造 RAGAS embedding（复用 Ollama bge-m3）。"""
    emb = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
    return LangchainEmbeddingsWrapper(emb)


def build_metrics() -> list:
    """构造四个评估指标实例。"""
    return [
        Faithfulness(),
        ResponseRelevancy(),
        LLMContextPrecisionWithReference(),
        LLMContextRecall(),
    ]


def build_dataset(samples: List[EvalSample], ground_truths: List[str]) -> EvaluationDataset:
    """把管线产出的样本 + 标准答案，转换为 RAGAS 评估数据集。"""
    sts: List[SingleTurnSample] = []
    for sample, reference in zip(samples, ground_truths):
        sts.append(
            SingleTurnSample(
                user_input=sample["question"],
                retrieved_contexts=sample["contexts"] or [""],
                response=sample["answer"],
                reference=reference,
            )
        )
    return EvaluationDataset(samples=sts)


def evaluate_samples(samples: List[EvalSample], ground_truths: List[str]):
    """执行 RAGAS 评估，返回 EvaluationResult。"""
    dataset = build_dataset(samples, ground_truths)
    ragas_llm = get_ragas_llm()
    ragas_emb = get_ragas_embeddings()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result = evaluate(
            dataset=dataset,
            metrics=build_metrics(),
            llm=ragas_llm,
            embeddings=ragas_emb,
            show_progress=True,
            raise_exceptions=False,
        )
    return result
