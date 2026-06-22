"""
Confidence calibration analysis for the fine-tuned TakeMeter model.

Runs inference on all 216 dataset examples, bins predictions by confidence,
and reports whether high-confidence predictions are actually more accurate.

Usage:
    python scripts/calibration.py

Outputs:
    results/calibration_results.json  -- per-bin accuracy data
    results/calibration_plot.png      -- calibration curve
"""

import os
import json
import csv
import warnings
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

MODEL_DIR    = "results/finetuned_model"
DATASET_PATH = "data/dataset.csv"
RESULTS_DIR  = Path("results")
LABELS       = ["analysis", "hot_take", "reaction"]
LABEL2ID     = {l: i for i, l in enumerate(LABELS)}
MAX_LENGTH   = 256


def load_model():
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_DIR)
    model     = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    return tokenizer, model


def load_dataset():
    rows = []
    with open(DATASET_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["label"] in LABEL2ID:
                rows.append({"text": row["text"], "label": row["label"]})
    return rows


def run_inference(tokenizer, model, rows):
    results = []
    for row in rows:
        inputs = tokenizer(
            row["text"],
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
        )
        with torch.no_grad():
            logits = model(**inputs).logits
        probs     = F.softmax(logits, dim=-1).squeeze().tolist()
        pred_idx  = int(torch.argmax(logits).item())
        pred_lbl  = LABELS[pred_idx]
        confidence = probs[pred_idx]
        results.append({
            "true_label": row["label"],
            "predicted":  pred_lbl,
            "correct":    pred_lbl == row["label"],
            "confidence": round(confidence, 4),
            "probs":      {LABELS[i]: round(probs[i], 4) for i in range(len(LABELS))},
        })
    return results


def calibration_analysis(results):
    # Bin by confidence in 10-point increments
    bins = [(lo / 100, (lo + 10) / 100) for lo in range(30, 100, 10)]
    bin_data = []

    for lo, hi in bins:
        subset = [r for r in results if lo <= r["confidence"] < hi]
        if not subset:
            continue
        acc = sum(r["correct"] for r in subset) / len(subset)
        mean_conf = np.mean([r["confidence"] for r in subset])
        bin_data.append({
            "bin":       f"{lo:.0%}–{hi:.0%}",
            "lo":        lo,
            "hi":        hi,
            "count":     len(subset),
            "accuracy":  round(acc, 4),
            "mean_conf": round(float(mean_conf), 4),
        })

    # Also handle >=100% bucket (exact 1.0)
    subset = [r for r in results if r["confidence"] >= 1.0]
    if subset:
        bin_data.append({
            "bin": "100%",
            "lo": 1.0, "hi": 1.01,
            "count": len(subset),
            "accuracy": 1.0,
            "mean_conf": 1.0,
        })

    return bin_data


def plot_calibration(bin_data, out_path):
    counts     = [b["count"]     for b in bin_data]
    mean_confs = [b["mean_conf"] for b in bin_data]
    accs       = [b["accuracy"]  for b in bin_data]
    labels_x   = [b["bin"]       for b in bin_data]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7),
                                   gridspec_kw={"height_ratios": [3, 1]})

    # Calibration curve
    ax1.plot([0.3, 1.0], [0.3, 1.0], "k--", linewidth=1, label="Perfect calibration", alpha=0.5)
    ax1.scatter(mean_confs, accs, s=[c * 8 for c in counts],
                color="#2563eb", zorder=5, label="Observed (size = sample count)")
    ax1.plot(mean_confs, accs, color="#2563eb", alpha=0.6)

    for b, x, y in zip(bin_data, mean_confs, accs):
        ax1.annotate(
            f"n={b['count']}",
            (x, y),
            textcoords="offset points", xytext=(6, 4),
            fontsize=8, color="#374151",
        )

    ax1.set_xlim(0.3, 1.02)
    ax1.set_ylim(0.3, 1.05)
    ax1.set_xlabel("Mean confidence in bin", fontsize=11)
    ax1.set_ylabel("Accuracy in bin", fontsize=11)
    ax1.set_title("Confidence Calibration — Fine-tuned DistilBERT", fontsize=12, pad=10)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Count bar chart
    ax2.bar(labels_x, counts, color="#93c5fd", edgecolor="#2563eb", linewidth=0.7)
    ax2.set_ylabel("Count", fontsize=10)
    ax2.set_xlabel("Confidence bin", fontsize=10)
    ax2.tick_params(axis="x", labelrotation=30)
    ax2.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Calibration plot saved to {out_path}")


def main():
    print("Loading model and dataset...")
    tokenizer, model = load_model()
    rows = load_dataset()
    print(f"  {len(rows)} examples")

    print("Running inference on all examples...")
    results = run_inference(tokenizer, model, rows)

    overall_acc = sum(r["correct"] for r in results) / len(results)
    print(f"  Overall accuracy (full dataset): {overall_acc:.1%}")

    print("\nComputing calibration bins...")
    bin_data = calibration_analysis(results)

    print()
    print(f"  {'Confidence bin':15s} {'Count':>6} {'Accuracy':>10} {'Mean conf':>10}")
    print("  " + "-" * 45)
    for b in bin_data:
        print(f"  {b['bin']:15s} {b['count']:>6} {b['accuracy']:>10.1%} {b['mean_conf']:>10.1%}")

    # Calibration quality check
    print()
    well_calibrated = all(
        abs(b["accuracy"] - b["mean_conf"]) < 0.10
        for b in bin_data if b["count"] >= 5
    )
    print(f"  Well-calibrated (all bins within 10pp of diagonal): {well_calibrated}")

    # Check monotonicity: does accuracy increase with confidence?
    accs = [b["accuracy"] for b in bin_data if b["count"] >= 3]
    monotone = all(accs[i] <= accs[i+1] + 0.05 for i in range(len(accs) - 1))
    print(f"  Approximately monotone (higher confidence = higher accuracy): {monotone}")

    # Save results
    out = {
        "overall_accuracy_full_dataset": round(overall_acc, 4),
        "calibration_bins": bin_data,
        "well_calibrated":  well_calibrated,
        "monotone":         monotone,
        "per_example": results,
    }
    json_path = RESULTS_DIR / "calibration_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nCalibration results saved to {json_path}")

    plot_path = RESULTS_DIR / "calibration_plot.png"
    plot_calibration(bin_data, plot_path)


if __name__ == "__main__":
    main()
