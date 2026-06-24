"""RAGAS 评估主入口。

用法（在项目根目录执行）：
    python -m eval.run_eval
    python -m eval.run_eval --dataset eval/dataset/golden_set.jsonl --limit 3

流程：读取评测集 -> 复用线上管线生成 answer/contexts -> RAGAS 评分 ->
打印逐题分数与平均分汇总 -> 落盘 csv / json 报告到 eval/report/。

注意：golden_set.jsonl 中的 ground_truth 需对照你实际上传到知识库的文档内容编写，
否则检索类指标（ContextPrecision / ContextRecall）会偏低。
"""
import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

from eval.pipeline_runner import run_pipeline_batch
from eval.ragas_evaluator import METRIC_LABELS, evaluate_samples

DEFAULT_DATASET = os.path.join("eval", "dataset", "golden_set.jsonl")
REPORT_DIR = os.path.join("eval", "report")


def load_golden_set(path: str) -> List[Dict]:
    """读取 jsonl 评测集，每行包含 question 与 ground_truth。"""
    rows: List[Dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if "question" not in item or "ground_truth" not in item:
                raise ValueError(f"第 {line_no} 行缺少 question 或 ground_truth 字段: {line}")
            item.setdefault("id", f"q{line_no}")
            rows.append(item)
    if not rows:
        raise ValueError(f"评测集为空: {path}")
    return rows


def _aggregate(df) -> Dict[str, float]:
    """从结果 DataFrame 计算各指标的平均分（忽略 NaN）。"""
    means: Dict[str, float] = {}
    for col in df.columns:
        if col in METRIC_LABELS:
            series = df[col]
            mean = series.mean(skipna=True)
            means[col] = float(mean) if mean == mean else float("nan")  # nan != nan
    return means


def _print_report(rows: List[Dict], df, means: Dict[str, float]) -> None:
    metric_cols = [c for c in df.columns if c in METRIC_LABELS]

    print("\n" + "=" * 72)
    print("逐题评分")
    print("=" * 72)
    for i, row in enumerate(rows):
        print(f"\n[{row.get('id')}] {row['question']}")
        for col in metric_cols:
            val = df.iloc[i][col]
            val_str = f"{val:.4f}" if val == val else "NaN"  # nan != nan
            print(f"    - {METRIC_LABELS[col]}: {val_str}")

    print("\n" + "=" * 72)
    print(f"平均分汇总（样本数 = {len(rows)}）")
    print("=" * 72)
    for col in metric_cols:
        mean = means.get(col, float("nan"))
        mean_str = f"{mean:.4f}" if mean == mean else "NaN"
        print(f"    {METRIC_LABELS[col]:<34}: {mean_str}")
    print("=" * 72 + "\n")


def _save_report(rows: List[Dict], df, means: Dict[str, float]) -> Tuple[str, str]:
    os.makedirs(REPORT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(REPORT_DIR, f"ragas_{ts}.csv")
    json_path = os.path.join(REPORT_DIR, f"ragas_{ts}.json")

    # csv：逐题明细
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # json：含逐题明细 + 平均分汇总
    metric_cols = [c for c in df.columns if c in METRIC_LABELS]
    per_sample = []
    for i, row in enumerate(rows):
        scores = {}
        for col in metric_cols:
            val = df.iloc[i][col]
            scores[col] = float(val) if val == val else None
        per_sample.append({
            "id": row.get("id"),
            "question": row["question"],
            "ground_truth": row["ground_truth"],
            "scores": scores,
        })
    payload = {
        "timestamp": ts,
        "sample_count": len(rows),
        "metric_labels": {k: METRIC_LABELS[k] for k in metric_cols},
        "average_scores": {k: (means[k] if means.get(k) == means.get(k) else None) for k in metric_cols},
        "samples": per_sample,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return csv_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser(description="电商客服 RAG Agent 的 RAGAS 评估")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="评测集 jsonl 路径")
    parser.add_argument("--limit", type=int, default=0, help="仅评测前 N 条（0 表示全部）")
    args = parser.parse_args()

    rows = load_golden_set(args.dataset)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    print(f"加载评测集: {args.dataset}，共 {len(rows)} 条")

    questions = [r["question"] for r in rows]
    ground_truths = [r["ground_truth"] for r in rows]

    print("开始运行 Agent 管线（查询改写 -> 混合检索 -> LLM 生成）...")
    samples = run_pipeline_batch(questions)

    print("开始 RAGAS 评分（裁判 LLM = 阿里模型，embedding = bge-m3）...")
    result = evaluate_samples(samples, ground_truths)
    df = result.to_pandas()

    means = _aggregate(df)
    _print_report(rows, df, means)
    csv_path, json_path = _save_report(rows, df, means)
    print(f"报告已保存:\n    CSV : {csv_path}\n    JSON: {json_path}")


if __name__ == "__main__":
    main()
