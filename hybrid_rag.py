# 日志工具
from logs.logging_server import logger
from typing import List, Dict, Any, Optional, Tuple
# 中文分词
import jieba
# BM25 关键词检索
from rank_bm25 import BM25Okapi
# 全局配置
from config import EMBEDDING_MODEL,OLLAMA_BASE_URL, COLLECTION_NAME,RERANK_ENABLED,HYBRID_TOP,BM25_K1,BM25_B,RERANK_CANDIDATES,RRF_K,RERANK_SCORE_THRESHOLD,RERANK_TOP_N, COLLECTION_NAME, PGVECTOR_HOST, PGVECTOR_PORT, PGVECTOR_DATABASE, PGVECTOR_USER, PGVECTOR_PASSWORD,CHUNK_SIZE, CHUNK_OVERLAP
# Ollama 嵌入模型
from langchain_ollama import OllamaEmbeddings
# Cross-Encoder 重排序器
from reranker import CrossEncoderReranker
from db.pg_conn import get_pg_conn
# 文本分割器
from langchain_text_splitters import RecursiveCharacterTextSplitter
# PGVector 向量存储
from langchain_postgres import PGVector

# 全局共享的嵌入模型实例
_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

# PGVector 连接字符串
connection = (
    f"postgresql+psycopg2://{PGVECTOR_USER}:{PGVECTOR_PASSWORD}"
    f"@{PGVECTOR_HOST}:{PGVECTOR_PORT}/{PGVECTOR_DATABASE}"
)

# 创建 PGVector 向量存储实例
vectorstore = PGVector(
    embeddings=_embeddings,
    connection=connection,
    collection_name=COLLECTION_NAME,
    use_jsonb=True,
)



class HybridSearchEngine:
    """混合检索引擎：融合 BM25 关键词检索 + 向量语义检索 + RRF 融合 + Cross-Encoder 重排序"""

    def __init__(self):
        # 文档列表，元素包含 id / content / knowledge_base
        self._documents: List[Dict[str, Any]] = []
        # BM25 索引实例
        self._bm25: Optional[BM25Okapi] = None
        # 文档 id → 文档列表索引 的映射
        self._id_to_idx: Dict[str, int] = {}
        # Cross-Encoder 重排序器（可选）
        self._reranker : Optional[CrossEncoderReranker] = None
        if RERANK_ENABLED:
            self._reranker = CrossEncoderReranker()
        # 启动时自动从数据库加载语料并构建 BM25 索引
        self._load_corpus_from_db()


    def _load_corpus_from_db(self):
        """从 PGVector 拉取全量文档块，重建 BM25 索引"""
        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT e.id::text, e.document
                    FROM langchain_pg_embedding e
                    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                    WHERE c.name = %s
                    ORDER BY e.id
                """, (COLLECTION_NAME,))
                rows = cur.fetchall()
        finally:
            conn.close()

        # 清空旧数据，重新构建内存索引
        self._documents.clear()
        self._id_to_idx.clear()
        for i, (doc_id, content) in enumerate(rows):
            self._documents.append({
                "id": doc_id,
                "content": content
            })
            self._id_to_idx[doc_id] = i

        # 对所有文档执行中文分词，构建 BM25 索引
        tokenized = [self._tokenize(d["content"]) for d in self._documents]
        self._bm25 = BM25Okapi(tokenized, k1=BM25_K1, b=BM25_B)
        logger.info(f"BM25 索引重建完成，共 {len(self._documents)} 个文档块")

    def rebuild_index(self):
        """上传新文档后调用，刷新 BM25 索引"""
        self._load_corpus_from_db()

    # BM25 关键词检索
    def _bm25_search(self, query: str,
                     knowledge_base: Optional[str],
                     top_k: int) -> List[Tuple[str, float]]:
        """基于 BM25 算法的关键词检索，支持按知识库过滤"""
        if not self._bm25 or not self._documents:
            return []
        # 把用户问题分词 对每一篇文档算 BM25 相关性分数
        scores = self._bm25.get_scores(self._tokenize(query))
        idx_scores = [(idx, float(scores[idx])) for idx in range(len(scores)) if scores[idx] > 0]
        if knowledge_base:
            idx_scores = [(i, s) for i, s in idx_scores
                          if self._documents[i]["knowledge_base"] == knowledge_base]
        idx_scores.sort(key=lambda x: x[1], reverse=True)
        return [(self._documents[i]["id"], s) for i, s in idx_scores[:top_k]]

    # 向量语义检索
    def _vector_search(self, query: str,
                       knowledge_base: Optional[str],
                       top_k: int) -> List[Tuple[str, float]]:
        """基于嵌入向量的余弦相似度检索，支持按知识库过滤"""
        vec = _embeddings.embed_query(query)
        vec_literal = "[" + ",".join(str(v) for v in vec) + "]"

        sql = """
            SELECT e.id::text,
                   1 - (e.embedding <=> %s::vector) AS similarity
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = %s
        """
        params: List[Any] = [vec_literal, COLLECTION_NAME]
        if knowledge_base:
            sql += " AND e.cmetadata->>'knowledge_base' = %s"
            params.append(knowledge_base)
        sql += " ORDER BY similarity DESC LIMIT %s"
        params.append(top_k)

        conn = get_pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return [(r[0], float(r[1])) for r in cur.fetchall()]
        finally:
            conn.close()

    # ── 工具方法 ────────────────────────────────────────────
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """使用 jieba 对文本进行中文分词"""
        return list(jieba.cut(text.lower()))

    @staticmethod
    def _rrf_fusion(bm25: List[Tuple[str, float]],
                    vec: List[Tuple[str, float]],
                    k: int = 60,
                    top_n: int = 10) -> List[Tuple[str, float]]:
        """Reciprocal Rank Fusion：融合 BM25 和向量检索的排序结果"""
        scores: Dict[str, float] = {}
        for rank, (doc_id, _) in enumerate(bm25):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        for rank, (doc_id, _) in enumerate(vec):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # ── 对外搜索接口 ────────────────────────────────────────
    def search(self, query: str,
               knowledge_base: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        混合搜索入口：
        1. BM25 关键词检索
        2. 向量语义检索（异常时降级为纯 BM25）
        3. RRF 融合排序
        4. Cross-Encoder 重排序（可选）
        """
        bm25_results = self._bm25_search(query, knowledge_base, HYBRID_TOP)

        vec_results: List[Tuple[str, float]] = []
        degraded = False
        try:
            vec_results = self._vector_search(query, knowledge_base, HYBRID_TOP)
        except Exception as e:
            logger.warning(f"向量检索异常，自动降级为纯 BM25: {e}")
            degraded = True

        # 向量检索失败时仅用 BM25 结果，否则执行 RRF 融合
        if degraded or not vec_results:
            fused = self._format_results(bm25_results[:RERANK_CANDIDATES])
        else:
            fused = self._rrf_fusion(bm25_results, vec_results, k=RRF_K, top_n=RERANK_CANDIDATES)
            fused = self._format_results(fused)

        # 可选：Cross-Encoder 重排序
        if self._reranker:
            fused = self._reranker.rerank(
                query, fused,
                top_k=RERANK_TOP_N,
                score_threshold=RERANK_SCORE_THRESHOLD
            )
        else:
            fused = fused[:RERANK_TOP_N]

        return fused

    def _format_results(self, results: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
        """将 (id, score) 元组格式化为带完整内容的字典列表"""
        out = []
        for doc_id, score in results:
            idx = self._id_to_idx.get(doc_id)
            if idx is not None:
                out.append({
                    "id": doc_id,
                    "content": self._documents[idx]["content"],
                    "score": score,
                })
        return out


# ── 全局单例 + 对外函数 ──────────────────────────────
_engine: Optional[HybridSearchEngine] = None


def get_engine() -> HybridSearchEngine:
    """获取 HybridSearchEngine 全局单例"""
    global _engine
    if _engine is None:
        _engine = HybridSearchEngine()
    return _engine


def build_to_llm_hybrid_search_str(query: str,
                                   knowledge_base: Optional[str] = None) -> str:
    """
    执行混合搜索并将结果格式化为 LLM 可用的参考信息字符串。
    """
    results = get_engine().search(query, knowledge_base)
    if not results:
        return "[参考信息] \n" + "非常抱歉，目前的知识库中暂未找到该问题的具体信息，建议您联系人工客服获取帮助。"
    return "[参考信息] \n" + "".join(r["content"] for r in results)



def vector_input_txt(file_path: str, knowledge_base: str) -> int:
    """读取 txt 文件 → 文本分块 → 生成 embedding → 写入 PGVector（含知识库归属）"""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 使用递归字符文本分割器进行分块
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.create_documents(
        texts=[text],
        metadatas=[{"knowledge_base": knowledge_base}],
    )
    # 将分块写入向量数据库
    vectorstore.add_documents(chunks)
    return len(chunks)