"""RAGAS 与新版 langchain 的兼容垫片。

ragas 0.4.x 在 `ragas.llms.base` 中硬导入了已被下线的
`langchain_community.chat_models.vertexai.ChatVertexAI` 与
`langchain_community.llms.VertexAI`。本项目使用的是 langchain 1.x，
该路径已被移除，直接 import ragas 会抛 ModuleNotFoundError。

由于项目根本不使用 Vertex，这里在导入 ragas 之前注入轻量 stub 占位类，
仅用于让 ragas 的模块级导入与 isinstance 判断通过，不影响任何实际功能。

使用方式：在 import ragas 之前调用 patch_langchain_vertex()。
"""
import sys
import types


def patch_langchain_vertex() -> None:
    """注入 Vertex stub，使 ragas 可在 langchain 1.x 下正常导入。"""
    import langchain_community.chat_models as chat_models

    if "langchain_community.chat_models.vertexai" not in sys.modules:
        vertex_module = types.ModuleType("langchain_community.chat_models.vertexai")

        class ChatVertexAI:  # noqa: D401 - stub 占位，仅供 ragas 导入
            """Vertex stub，本项目不使用。"""

        vertex_module.ChatVertexAI = ChatVertexAI
        sys.modules["langchain_community.chat_models.vertexai"] = vertex_module
        chat_models.vertexai = vertex_module

    import langchain_community.llms as community_llms

    if not hasattr(community_llms, "VertexAI"):
        class VertexAI:  # noqa: D401 - stub 占位，仅供 ragas 导入
            """Vertex stub，本项目不使用。"""

        community_llms.VertexAI = VertexAI
