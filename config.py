import os
from dotenv import load_dotenv

load_dotenv()

def _get_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))

def _get_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")

PGVECTOR_HOST = os.getenv("PGVECTOR_HOST", "localhost")
PGVECTOR_PORT = _get_int("PGVECTOR_PORT", 15432)
PGVECTOR_DATABASE = os.getenv("PGVECTOR_DATABASE", "customer-aide")
PGVECTOR_USER = os.getenv("PGVECTOR_USER", "postgres")
PGVECTOR_PASSWORD = os.getenv("PGVECTOR_PASSWORD", "")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")
ALI_MODEL_KEY = os.getenv("ALI_MODEL_KEY", "")
ALI_MODEL_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
ALI_MODEL_NAME = "glm-5.1"

# 文件上传
# 上传文件存储目录
UPLOAD_DIR = "uploads"
# 最大允许文件大小：10MB
MAX_FILE_SIZE = 10 * 1024 * 1024
# 允许的文件扩展名
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}






# ======== 文本分割参数 ========
CHUNK_SIZE = 400          # 每个分块的最大字符数
CHUNK_OVERLAP = 80        # 相邻分块之间的重叠字符数

# ======== 混合检索（BM25 + 向量）配置 ========
HYBRID_SEARCH_ENABLED = True   # 是否启用混合检索
RRF_K = 60                     # RRF 融合常数，防止除零并平滑排名
HYBRID_TOP = 20              # BM25 和向量各自取 Top-K
BM25_K1 = 1.5                  # BM25 词频饱和参数
BM25_B = 0.75                  # BM25 文档长度归一化参数 控制长文档惩罚有多强

# ======== Cross-Encoder 重排序配置 ========
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"   # 重排序模型名称
RERANK_ENABLED = True                         # 是否启用重排序
RERANK_CANDIDATES = 20                        # RRF 融合后保留多少候选给 reranker
RERANK_TOP_N = 5                              # reranker 后最终取多少
RERANK_SCORE_THRESHOLD = 0.3                  # 低于此分的视为不相关，丢弃

# ======== 查询改写配置 ========
QUERY_REWRITE_MODE = os.getenv("QUERY_REWRITE_MODE", "llm").lower()  # off | rule | llm
QUERY_REWRITE_TIMEOUT = _get_float("QUERY_REWRITE_TIMEOUT", 10.0)

# ======== Tool Calling 配置 ========
TOOL_CALLING_ENABLED = os.getenv("TOOL_CALLING_ENABLED", "true").lower() == "true"
TOOL_CALLING_MAX_ITERATIONS = _get_int("TOOL_CALLING_MAX_ITERATIONS", 5)