"""
Inter-annotator reliability: Groq llama-3.3-70b-versatile as Annotator 2.

Selects 35 examples from the dataset (weighted toward ambiguous types),
has Groq label them using only a generic task description (no detailed
decision rules), computes agreement rate and Cohen's kappa vs. the
original labels (Annotator 1), and analyzes disagreements.

Disclosure: Annotator 2 is an LLM, not a human. This tests whether the
labels are clear to a general-purpose model given only a brief description,
revealing where the taxonomy needs the explicit decision rules.

Usage:
    $env:GROQ_API_KEY = "your_key"
    python scripts/interannotator.py

Outputs:
    results/interannotator_results.json
"""

import os
import csv
import json
import time
import sys
import random
from pathlib import Path
from collections import Counter

import numpy as np
from sklearn.metrics import cohen_kappa_score
from groq import Groq

DATASET_PATH = "data/dataset.csv"
RESULTS_DIR  = Path("results")
LABELS       = ["analysis", "hot_take", "reaction"]
LABEL2ID     = {l: i for i, l in enumerate(LABELS)}
RANDOM_SEED  = 7          # different from training seed
N_EXAMPLES   = 35
GROQ_MODEL   = "llama-3.3-70b-versatile"

# Annotator 2 gets a brief description only — no detailed decision rules.
# This is intentionally less specific than the full taxonomy to reveal
# where the rules do the most work.
SYSTEM_PROMPT = """\
You are classifying posts from the NBA subreddit (r/nba).

Assign each post to exactly one of three categories:

  analysis  — the post makes a substantive argument or provides specific
               evidence (statistics, historical comparison, tactical breakdown)
  hot_take  — the post states a bold opinion without real evidence to back it
               up; confident assertion, not an argument
  reaction  — immediate emotional response to a game, trade, or news;
               expressing a feeling, not arguing a point

Reply with ONLY one label: analysis, hot_take, or reaction\
"""

USER_TEMPLATE = "Classify: {text}\n\nLabel:"


def load_dataset():
    rows = []
    with open(DATASET_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["label"] in LABEL2ID:
                rows.append({"text": row["text"], "label": row["label"]})
    return rows


def select_sample(rows, n=N_EXAMPLES, seed=RANDOM_SEED):
    """
    Sample examples weighted toward ambiguous label types:
    - analysis posts with assertive framing
    - reaction posts with embedded bold claims
    - typical clear examples of each class
    """
    rng = random.Random(seed)
    by_label = {l: [r for r in rows if r["label"] == l] for l in LABELS}

    # Aim: 12 analysis, 13 hot_take, 10 reaction
    sample = (
        rng.sample(by_label["analysis"], 12)
        + rng.sample(by_label["hot_take"], 13)
        + rng.sample(by_label["reaction"], 10)
    )
    rng.shuffle(sample)
    return sample


def label_one(client, text, retries=3):
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": USER_TEMPLATE.format(text=text)},
                ],
                temperature=0.0,
                max_tokens=10,
            )
            raw = resp.choices[0].message.content.strip().lower()
            raw = raw.replace(" ", "_").replace("-", "_").strip(".,;:\"'")
            if raw in LABEL2ID:
                return raw, raw
            for lbl in LABELS:
                if lbl in raw:
                    return lbl, raw
            return None, raw
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None, str(e)


def compute_kappa(labels1, labels2):
    # Map to int for sklearn
    def to_int(lbls):
        return [LABEL2ID.get(l, -1) for l in lbls]
    y1 = to_int(labels1)
    y2 = to_int(labels2)
    # Filter out unparseable (−1)
    paired = [(a, b) for a, b in zip(y1, y2) if a >= 0 and b >= 0]
    if not paired:
        return 0.0
    y1c, y2c = zip(*paired)
    return cohen_kappa_score(y1c, y2c)


def main():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set.")
        sys.exit(1)

    print("Loading dataset...")
    rows   = load_dataset()
    sample = select_sample(rows)
    print(f"  Selected {len(sample)} examples")
    dist = Counter(r["label"] for r in sample)
    for lbl in LABELS:
        print(f"    {lbl:12s}: {dist[lbl]}")

    client = Groq(api_key=api_key)
    print(f"\nRunning Groq ({GROQ_MODEL}) as Annotator 2...")
    print(f"  Estimated time: ~{len(sample) * 2.1 / 60:.1f} min\n")

    ann1_labels = []  # original (my) labels
    ann2_labels = []  # Groq labels
    details     = []

    for i, row in enumerate(sample, 1):
        pred, raw = label_one(client, row["text"])
        ann1_labels.append(row["label"])
        ann2_labels.append(pred)

        agree  = "AGREE" if pred == row["label"] else "DISAGREE"
        status = "OK" if pred == row["label"] else "!!"
        print(f"  [{i:2d}/{len(sample)}] {status}  ann1={row['label']:10s}  ann2={str(pred):10s}  raw={repr(raw[:30])}")

        details.append({
            "text":       row["text"],
            "annotator1": row["label"],
            "annotator2": pred,
            "raw_ann2":   raw,
            "agree":      pred == row["label"],
        })
        time.sleep(2.1)

    # Metrics
    valid = [(a1, a2) for a1, a2 in zip(ann1_labels, ann2_labels) if a2 is not None]
    n_valid   = len(valid)
    n_agree   = sum(1 for a1, a2 in valid if a1 == a2)
    pct_agree = n_agree / n_valid if n_valid else 0
    kappa     = compute_kappa(ann1_labels, ann2_labels)

    print(f"\n{'=' * 55}")
    print(f"  INTER-ANNOTATOR RELIABILITY")
    print(f"  (Annotator 1 = original labels, Annotator 2 = Groq)")
    print(f"{'=' * 55}")
    print(f"  Examples labeled  : {n_valid} / {len(sample)}")
    print(f"  Agreements        : {n_agree} / {n_valid}")
    print(f"  Percent agreement : {pct_agree:.1%}")
    print(f"  Cohen's kappa     : {kappa:.4f}")
    print()

    # Kappa interpretation
    if kappa >= 0.80:
        interp = "Almost perfect agreement (kappa >= 0.80)"
    elif kappa >= 0.60:
        interp = "Substantial agreement (0.60 <= kappa < 0.80)"
    elif kappa >= 0.40:
        interp = "Moderate agreement (0.40 <= kappa < 0.60)"
    else:
        interp = "Fair or poor agreement (kappa < 0.40)"
    print(f"  Interpretation    : {interp}")
    print()

    # Disagreement analysis
    disagreements = [d for d in details if not d["agree"] and d["annotator2"] is not None]
    if disagreements:
        print(f"  Disagreements ({len(disagreements)}):")
        pair_counts = Counter(
            (d["annotator1"], d["annotator2"]) for d in disagreements
        )
        print("  Most confused pairs (ann1 -> ann2):")
        for (a1, a2), count in pair_counts.most_common():
            print(f"    {a1:12s} -> {a2:12s}  ({count}x)")
        print()
        print("  Individual disagreements:")
        for d in disagreements:
            print(f"    ann1={d['annotator1']:10s}  ann2={d['annotator2']:10s}")
            print(f"    text: {d['text'][:100]}...")
            print()
    else:
        print("  No disagreements — perfect agreement.")

    # Save
    out = {
        "annotator2_model":    GROQ_MODEL,
        "annotator2_prompt":   "brief description only (no decision rules)",
        "n_examples":          n_valid,
        "percent_agreement":   round(pct_agree, 4),
        "cohen_kappa":         round(kappa, 4),
        "interpretation":      interp,
        "label_distribution":  {l: dist[l] for l in LABELS},
        "disagreements":       disagreements,
        "details":             details,
    }
    out_path = RESULTS_DIR / "interannotator_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
