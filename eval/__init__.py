"""电商客服 RAG Agent 的 RAGAS 评估体系（轻量版）。

模块组成：
- pipeline_runner：复用线上检索 + LLM 管线，对每条问题产出 answer 与 contexts
- ragas_evaluator：配置 RAGAS（裁判 LLM、embedding、指标）并执行评估
- run_eval：主入口，读取评测集 -> 跑管线 -> RAGAS 评分 -> 打印并落盘报告
"""
