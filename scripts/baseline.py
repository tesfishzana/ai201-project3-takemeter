"""
Zero-shot baseline: Groq llama-3.3-70b-versatile on the TakeMeter test set.

Usage:
    set GROQ_API_KEY=<your_key>   (Windows CMD)
    $env:GROQ_API_KEY="<key>"     (PowerShell)
    python scripts/baseline.py

Outputs:
    results/baseline_results.json  -- full per-example predictions + metrics
    results/baseline_confusion.txt -- confusion matrix (ASCII, for the report)
"""

import os
import json
import csv
import time
import sys
from pathlib import Path
from collections import Counter

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)
from groq import Groq

# ── Config ─────────────────────────────────────────────────────────────────────

DATASET_PATH = "data/dataset.csv"
RESULTS_DIR  = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

LABELS     = ["analysis", "hot_take", "reaction"]
LABEL2ID   = {l: i for i, l in enumerate(LABELS)}
RANDOM_SEED = 42

GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Prompts ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a text classifier for an NBA subreddit discourse quality task.

You will be given a single post or comment from r/nba. Your job is to assign it
to exactly one of these three categories:

  analysis — The post constructs a structured argument for a claim, supported by
  specific verifiable evidence (statistics, historical comparison, tactical
  observation, or cited reporting). The reasoning is present even if you strip
  away the opinion framing. A single stat embedded in a real reasoning chain
  qualifies; a stat pasted in to dress up an assertion does not.

  hot_take — A bold, confident opinion stated as fact, without supporting
  evidence or with only decorative / cherry-picked stats that are invoked but
  not reasoned through. The post asserts a position but does not construct an
  argument for it. Often contrarian or phrased to provoke.

  reaction — An immediate emotional response to a specific game event, trade
  announcement, injury report, or other news item. The primary purpose is to
  express a feeling in the moment. Little to no argumentative structure — the
  post documents a reaction, not a position.

Decision rules:
- If a post includes stats but uses them only as decoration (not driving the
  argument), label it hot_take, not analysis.
- If a post is emotional but still constructs an argument backed by evidence,
  label it based on argumentative intent (analysis or hot_take), not emotion.
- Reserve reaction for posts that are purely expressive with no argumentative
  intent — even a bold incidental claim mid-reaction stays reaction if the
  post's purpose is to express a feeling.

Respond with ONLY the label name — one of: analysis, hot_take, reaction
Do not add punctuation, explanation, or any other text.\
"""

USER_TEMPLATE = """\
Classify this r/nba post or comment:

{text}

Label:\
"""

# ── Data loading ───────────────────────────────────────────────────────────────

def load_dataset(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["label"] in LABEL2ID:
                rows.append({"text": row["text"], "label": row["label"]})
    return rows


def make_splits(rows, seed=RANDOM_SEED):
    texts  = [r["text"]  for r in rows]
    labels = [r["label"] for r in rows]

    # 70 / 15 / 15  (same seed used in fine-tuning so test sets match)
    X_train, X_temp, y_train, y_temp = train_test_split(
        texts, labels, test_size=0.30, random_state=seed, stratify=labels
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=seed, stratify=y_temp
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


# ── Groq classification ────────────────────────────────────────────────────────

def classify_one(client, text, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": USER_TEMPLATE.format(text=text)},
                ],
                temperature=0.0,
                max_tokens=10,
            )
            raw = response.choices[0].message.content.strip().lower()
            # normalise: allow "hot take" → "hot_take"
            raw = raw.replace(" ", "_").replace("-", "_")
            raw = raw.strip(".,;:\"'")
            if raw in LABEL2ID:
                return raw, raw
            # partial match fallback
            for label in LABELS:
                if label in raw:
                    return label, raw
            return None, raw
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"  Retry {attempt+1} after {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"  Failed after {retries} attempts: {e}")
                return None, str(e)


def run_baseline(client, texts, true_labels):
    predictions = []
    raw_responses = []
    unparseable = 0

    for i, (text, true_label) in enumerate(zip(texts, true_labels), start=1):
        pred, raw = classify_one(client, text)
        predictions.append(pred)
        raw_responses.append(raw)

        status = "OK" if pred == true_label else ("??" if pred is None else "XX")
        print(f"  [{i:3d}/{len(texts)}] {status}  true={true_label:10s}  pred={str(pred):10s}  raw={repr(raw[:40])}")

        if pred is None:
            unparseable += 1

        # Respect Groq free-tier rate limits (~30 req/min)
        time.sleep(2.1)

    if unparseable > 0:
        pct = 100 * unparseable / len(texts)
        print(f"\nWARNING: {unparseable}/{len(texts)} responses unparseable ({pct:.1f}%)")
        if pct > 10:
            print("  > 10% unparseable — consider tightening the prompt output instruction.")

    return predictions, raw_responses


# ── Metrics ────────────────────────────────────────────────────────────────────

def compute_metrics(true_labels, predictions):
    # Replace None (unparseable) with a dummy label that will always be wrong
    preds_clean = [p if p is not None else "__unparseable__" for p in predictions]

    acc = accuracy_score(true_labels, preds_clean)

    # Per-class precision, recall, F1
    prec, rec, f1, support = precision_recall_fscore_support(
        true_labels, preds_clean, labels=LABELS, average=None, zero_division=0
    )
    macro_f1 = float(np.mean(f1))

    per_class = {}
    for i, label in enumerate(LABELS):
        per_class[label] = {
            "precision": round(float(prec[i]), 4),
            "recall":    round(float(rec[i]),  4),
            "f1":        round(float(f1[i]),   4),
            "support":   int(support[i]),
        }

    cm = confusion_matrix(true_labels, preds_clean, labels=LABELS).tolist()

    return {
        "overall_accuracy": round(acc, 4),
        "macro_f1":         round(macro_f1, 4),
        "per_class":        per_class,
        "confusion_matrix": cm,
        "confusion_labels": LABELS,
    }


def print_confusion_matrix(cm, labels):
    col_w = 12
    header = " " * col_w + "".join(f"{l:>{col_w}}" for l in labels)
    print(header)
    print("-" * (col_w * (len(labels) + 1)))
    for i, row_label in enumerate(labels):
        row = f"{row_label:<{col_w}}" + "".join(f"{cm[i][j]:>{col_w}}" for j in range(len(labels)))
        print(row)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set.")
        print("  PowerShell: $env:GROQ_API_KEY = 'your_key_here'")
        print("  CMD:        set GROQ_API_KEY=your_key_here")
        sys.exit(1)

    print(f"Loading dataset from {DATASET_PATH}...")
    rows = load_dataset(DATASET_PATH)
    print(f"  Loaded {len(rows)} labeled examples")

    _, _, X_test, _, _, y_test = make_splits(rows)
    print(f"  Test set: {len(X_test)} examples")
    dist = Counter(y_test)
    for label in LABELS:
        print(f"    {label:12s}: {dist[label]}")

    print(f"\nRunning zero-shot baseline with Groq {GROQ_MODEL}...")
    print(f"  Estimated time: ~{len(X_test) * 2.1 / 60:.1f} min\n")

    client = Groq(api_key=api_key)
    predictions, raw_responses = run_baseline(client, X_test, y_test)

    print("\nComputing metrics...")
    metrics = compute_metrics(y_test, predictions)

    print("\n" + "=" * 55)
    print("  BASELINE RESULTS  (Groq llama-3.3-70b-versatile zero-shot)")
    print("=" * 55)
    print(f"  Overall accuracy : {metrics['overall_accuracy']:.4f}  ({metrics['overall_accuracy']*100:.1f}%)")
    print(f"  Macro F1         : {metrics['macro_f1']:.4f}")
    print()
    print(f"  {'Label':12s} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print("  " + "-" * 52)
    for label in LABELS:
        pc = metrics["per_class"][label]
        print(f"  {label:12s} {pc['precision']:>10.4f} {pc['recall']:>10.4f} {pc['f1']:>10.4f} {pc['support']:>10}")
    print()
    print("  Confusion matrix (rows=true, cols=predicted):")
    cm = metrics["confusion_matrix"]
    print_confusion_matrix(cm, LABELS)
    print("=" * 55)

    # ── Save results ──────────────────────────────────────────────────────────
    full_results = {
        "model":   GROQ_MODEL,
        "type":    "zero_shot_baseline",
        "metrics": metrics,
        "test_examples": [
            {
                "text":         text,
                "true_label":   true,
                "predicted":    pred,
                "raw_response": raw,
                "correct":      pred == true,
            }
            for text, true, pred, raw in zip(X_test, y_test, predictions, raw_responses)
        ],
    }

    out_path = RESULTS_DIR / "baseline_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {out_path}")

    # ASCII confusion matrix for easy copy-paste into README
    conf_txt_path = RESULTS_DIR / "baseline_confusion.txt"
    with open(conf_txt_path, "w", encoding="utf-8") as f:
        f.write("Confusion matrix — Groq zero-shot baseline\n")
        f.write("Rows = true label, Columns = predicted label\n\n")
        col_w = 12
        header = " " * col_w + "".join(f"{l:>{col_w}}" for l in LABELS)
        f.write(header + "\n")
        f.write("-" * (col_w * (len(LABELS) + 1)) + "\n")
        for i, row_label in enumerate(LABELS):
            row = f"{row_label:<{col_w}}" + "".join(f"{cm[i][j]:>{col_w}}" for j in range(len(LABELS)))
            f.write(row + "\n")
    print(f"Confusion matrix saved to {conf_txt_path}")

    # Quick reflection prompt
    wrongs = [ex for ex in full_results["test_examples"] if not ex["correct"] and ex["predicted"] is not None]
    if wrongs:
        print(f"\nBaseline wrong on {len(wrongs)}/{len(X_test)} examples.")
        confusion_pairs = Counter(
            (ex["true_label"], ex["predicted"]) for ex in wrongs
        )
        print("  Most confused label pairs (true → predicted):")
        for (true, pred), count in confusion_pairs.most_common(5):
            print(f"    {true:12s} → {pred:12s}  ({count} times)")


if __name__ == "__main__":
    main()
