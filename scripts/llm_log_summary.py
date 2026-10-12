"""Đọc log RAW của LLM (`.hermes/llm_raw/*.jsonl`) và in tóm tắt để tự kiểm tra.

Ví dụ:
    python scripts/llm_log_summary.py                 # tóm tắt mọi file log
    python scripts/llm_log_summary.py --tail 3        # in 3 record cuối (raw)
    python scripts/llm_log_summary.py --caller ragas  # chỉ lượt chấm của RAGAS
    python scripts/llm_log_summary.py --errors        # chỉ các lượt lỗi

Đây là công cụ debug của nhóm, KHÔNG phải bằng chứng nộp bài (đề bài chỉ cần
artifacts/*.json và doc/reports/*.md).
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path


def log_dir() -> Path:
    root = os.getenv("LLM_LOG_DIR")
    if root:
        return Path(root)
    return Path(__file__).resolve().parents[1] / ".hermes" / "llm_raw"


def load_records(files: list[Path]) -> list[dict]:
    records: list[dict] = []
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append({"caller": f"<unparsed:{path.name}>", "error": line[:120]})
    return records


def short(text: str | None, limit: int = 160) -> str:
    if text is None:
        return "<None>"
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[:limit] + "…"


def summarize(records: list[dict]) -> None:
    by_caller: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_caller[record.get("caller", "?").split(".")[0]].append(record)

    print(f"{'caller':<26}{'n':>6}{'err':>6}{'p50 ms':>10}{'p95 ms':>10}  models")
    for caller, rows in sorted(by_caller.items()):
        latencies = [row["latency_ms"] for row in rows if isinstance(row.get("latency_ms"), (int, float))]
        errors = sum(1 for row in rows if row.get("error"))
        models = Counter(row.get("model") or row.get("response_model") or "?" for row in rows)
        p50 = f"{statistics.median(latencies):.0f}" if latencies else "-"
        p95 = "-"
        if len(latencies) >= 2:
            p95 = f"{statistics.quantiles(latencies, n=20)[18]:.0f}"
        elif latencies:
            p95 = f"{latencies[0]:.0f}"
        print(f"{caller:<26}{len(rows):>6}{errors:>6}{p50:>10}{p95:>10}  "
              f"{', '.join(f'{m}×{c}' for m, c in models.most_common(3))}")

    total = len(records)
    failed = sum(1 for row in records if row.get("error"))
    tokens = sum((row.get("response", {}).get("usage") or {}).get("total_tokens") or 0
                 for row in records if isinstance(row.get("response"), dict))
    reasoning = sum(((row.get("response", {}).get("usage") or {})
                     .get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
                    for row in records if isinstance(row.get("response"), dict))
    print("-" * 72)
    print(f"tổng {total} lượt | lỗi {failed} | token tổng {tokens} | trong đó reasoning {reasoning}")


def print_tail(records: list[dict], count: int, caller: str | None, width: int) -> None:
    rows = [row for row in records if caller is None or (row.get("caller") or "").startswith(caller)]
    for row in rows[-count:]:
        print("=" * 78)
        print(f"[{row.get('ts')}] caller={row.get('caller')} model={row.get('model')} "
              f"latency={row.get('latency_ms')}ms")
        request = row.get("request") or {}
        for message in (request.get("messages") or [])[-2:]:
            if isinstance(message, dict):
                print(f"  {message.get('role', '?')}: {short(message.get('content'), width)}")
        if request.get("prompts"):
            print(f"  prompt: {short(request['prompts'][0], width)}")
        if row.get("error"):
            print(f"  ERROR: {row['error']}")
        response = row.get("response") or {}
        if response.get("content") is not None:
            print(f"  ANSWER: {short(response.get('content'), width)}")
        if response.get("finish_reason"):
            print(f"  finish={response['finish_reason']} "
                  f"tokens={(response.get('usage') or {}).get('total_tokens')}")
        if response.get("generations"):
            print(f"  ANSWER: {short(response['generations'][0], width)}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Tóm tắt log RAW LLM (.hermes/llm_raw).")
    parser.add_argument("--dir", type=Path, default=log_dir())
    parser.add_argument("--file", type=Path, default=None, help="chỉ đọc 1 file log cụ thể")
    parser.add_argument("--tail", type=int, default=0, help="in N record cuối (raw)")
    parser.add_argument("--caller", default=None, help="lọc theo caller, ví dụ ragas")
    parser.add_argument("--errors", action="store_true", help="chỉ liệt kê lượt lỗi")
    parser.add_argument("--width", type=int, default=200, help="độ dài text in ra")
    args = parser.parse_args(argv)

    files = [args.file] if args.file else sorted(args.dir.glob("*.jsonl"))
    if not files:
        print(f"Chưa có file log nào trong {args.dir}")
        return 1
    records = load_records(files)
    print(f"{len(files)} file log, {len(records)} record — {args.dir}")
    print("=" * 72)
    summarize(records)
    if args.errors:
        for row in records:
            if row.get("error"):
                print(f"  {row.get('ts')} {row.get('caller')} {row.get('model')}: {short(row['error'], args.width)}")
    if args.tail:
        print_tail(records, args.tail, args.caller, args.width)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
