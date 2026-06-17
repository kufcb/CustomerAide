# Cross-Encoder 重排序模型
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any
from logs.logging_server import logger
import os
from config import RERANKER_MODEL

class CrossEncoderReranker:
    """Cross-Encoder 重排序器：对检索候选文档进行精细化相关性排序"""

    def __init__(self, model_name: str = RERANKER_MODEL):
        logger.info(f"加载 Cross-Encoder 重排序模型: {model_name}")
        # 加载本地已下载的模型
        self.model = CrossEncoder(model_name, local_files_only=True)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        对候选文档执行重排序：
        1. 计算 query 与每个候选文档的相关性得分
        2. 按得分降序排列
        3. 过滤低分结果
        4. 返回 top-k
        """
        if not candidates:
            return []

        # 构建 query-doc 配对
        pairs = [[query, doc["content"]] for doc in candidates]
        # 批量预测相关性得分
        scores = self.model.predict(pairs, show_progress_bar=False)

        # 将得分写入候选文档
        for doc, score in zip(candidates, scores):
            doc["rerank_score"] = float(score)

        # 按得分降序排序
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        logger.info(f"重排序完成，最高分: {candidates[0]['rerank_score']:.4f}")
        logger.info(f"最低分: {candidates[-1]['rerank_score']:.4f}")

        # 过滤低于阈值的低分文档
        filtered = [d for d in candidates if d["rerank_score"] >= score_threshold]
        logger.info(f"阈值过滤后保留 {len(filtered)}/{len(candidates)} 条")

        return filtered[:top_k]