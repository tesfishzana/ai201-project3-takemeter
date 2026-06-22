"""
Fine-tunes distilbert-base-uncased on the TakeMeter labeled dataset.

Usage:
    python scripts/finetune.py

Outputs:
    results/evaluation_results.json  -- fine-tuned + baseline comparison
    results/confusion_matrix.png     -- confusion matrix heatmap
    results/finetuned_model/         -- saved model weights (not committed)

Hyperparameters (matching Colab starter notebook defaults):
    model       : distilbert-base-uncased
    epochs      : 3
    learning_rate: 2e-5
    batch_size  : 16
    max_length  : 256
    seed        : 42
"""

import os
import json
import csv
import warnings
from pathlib import Path
from collections import Counter

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless — no display needed
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)

import torch
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)
from datasets import Dataset

# ── Config ─────────────────────────────────────────────────────────────────────

DATASET_PATH   = "data/dataset.csv"
BASELINE_PATH  = "results/baseline_results.json"
RESULTS_DIR    = Path("results")
MODEL_OUT_DIR  = RESULTS_DIR / "finetuned_model"
RESULTS_DIR.mkdir(exist_ok=True)
MODEL_OUT_DIR.mkdir(exist_ok=True)

LABELS      = ["analysis", "hot_take", "reaction"]
LABEL2ID    = {l: i for i, l in enumerate(LABELS)}
ID2LABEL    = {i: l for i, l in enumerate(LABELS)}
RANDOM_SEED = 42

BASE_MODEL   = "distilbert-base-uncased"
EPOCHS       = 3
LR           = 2e-5
BATCH_SIZE   = 16
MAX_LENGTH   = 256

# ── Data ───────────────────────────────────────────────────────────────────────

def load_dataset_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["label"] in LABEL2ID:
                rows.append({"text": row["text"], "label": row["label"]})
    return rows


def make_splits(rows, seed=RANDOM_SEED):
    texts  = [r["text"]  for r in rows]
    labels = [r["label"] for r in rows]
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(
        texts, labels, test_size=0.30, random_state=seed, stratify=labels
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=0.50, random_state=seed, stratify=y_tmp
    )
    return X_tr, X_val, X_test, y_tr, y_val, y_test


# ── Tokenisation ───────────────────────────────────────────────────────────────

def tokenize_split(tokenizer, texts, labels):
    enc = tokenizer(
        texts,
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
        return_tensors=None,
    )
    return Dataset.from_dict({
        "input_ids":      enc["input_ids"],
        "attention_mask": enc["attention_mask"],
        "labels":         [LABEL2ID[l] for l in labels],
    })


# ── Metrics ────────────────────────────────────────────────────────────────────

def compute_metrics(eval_pred):
    logits, label_ids = eval_pred
    preds = np.argmax(logits, axis=-1)
    acc = accuracy_score(label_ids, preds)
    _, _, f1, _ = precision_recall_fscore_support(
        label_ids, preds, average="macro", zero_division=0
    )
    return {"accuracy": acc, "macro_f1": f1}


def full_metrics(true_ids, pred_ids):
    prec, rec, f1, sup = precision_recall_fscore_support(
        true_ids, pred_ids, labels=list(range(len(LABELS))),
        average=None, zero_division=0
    )
    macro_f1 = float(np.mean(f1))
    per_class = {}
    for i, label in enumerate(LABELS):
        per_class[label] = {
            "precision": round(float(prec[i]), 4),
            "recall":    round(float(rec[i]),  4),
            "f1":        round(float(f1[i]),   4),
            "support":   int(sup[i]),
        }
    cm = confusion_matrix(true_ids, pred_ids, labels=list(range(len(LABELS)))).tolist()
    return {
        "overall_accuracy": round(accuracy_score(true_ids, pred_ids), 4),
        "macro_f1":         round(macro_f1, 4),
        "per_class":        per_class,
        "confusion_matrix": cm,
        "confusion_labels": LABELS,
    }


# ── Confusion matrix plot ───────────────────────────────────────────────────────

def plot_confusion_matrix(cm, labels, path, title="Fine-tuned DistilBERT — Confusion Matrix"):
    cm_arr = np.array(cm)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_arr, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=10)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Predicted label", fontsize=11)
    ax.set_ylabel("True label", fontsize=11)
    ax.set_title(title, fontsize=12, pad=12)

    thresh = cm_arr.max() / 2.0
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(
                j, i, str(cm_arr[i, j]),
                ha="center", va="center",
                color="white" if cm_arr[i, j] > thresh else "black",
                fontsize=13, fontweight="bold",
            )

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Confusion matrix saved to {path}")


# ── Print helpers ───────────────────────────────────────────────────────────────

def print_metrics(metrics, title):
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print(f"{'=' * 55}")
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
    col_w = 12
    cm    = metrics["confusion_matrix"]
    header = " " * col_w + "".join(f"{l:>{col_w}}" for l in LABELS)
    print("  " + header)
    print("  " + "-" * (col_w * (len(LABELS) + 1)))
    for i, row_label in enumerate(LABELS):
        row = f"  {row_label:<{col_w}}" + "".join(f"{cm[i][j]:>{col_w}}" for j in range(len(LABELS)))
        print(row)
    print("=" * 55)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Base model: {BASE_MODEL}")
    print(f"Hyperparameters: epochs={EPOCHS}, lr={LR}, batch_size={BATCH_SIZE}, max_length={MAX_LENGTH}")

    # ── 1. Load and split ──────────────────────────────────────────────────────
    print(f"\nLoading dataset from {DATASET_PATH}...")
    rows = load_dataset_csv(DATASET_PATH)
    print(f"  Total: {len(rows)} examples")

    X_tr, X_val, X_test, y_tr, y_val, y_test = make_splits(rows)
    print(f"  Train: {len(X_tr)}  Val: {len(X_val)}  Test: {len(X_test)}")

    dist_tr = Counter(y_tr)
    print("  Training label distribution:")
    for label in LABELS:
        print(f"    {label:12s}: {dist_tr[label]}")

    # ── 2. Tokenise ────────────────────────────────────────────────────────────
    print(f"\nLoading tokenizer ({BASE_MODEL})...")
    tokenizer = DistilBertTokenizerFast.from_pretrained(BASE_MODEL)

    print("Tokenizing splits...")
    train_ds = tokenize_split(tokenizer, X_tr,   y_tr)
    val_ds   = tokenize_split(tokenizer, X_val,  y_val)
    test_ds  = tokenize_split(tokenizer, X_test, y_test)
    print(f"  Train tokens: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}")

    # ── 3. Model ───────────────────────────────────────────────────────────────
    print(f"\nLoading {BASE_MODEL} for sequence classification...")
    model = DistilBertForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")

    # ── 4. Training ─────────────────────────────────────────────────────────────
    training_args = TrainingArguments(
        output_dir=str(MODEL_OUT_DIR),
        num_train_epochs=EPOCHS,
        learning_rate=LR,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        logging_steps=10,
        report_to="none",
        seed=RANDOM_SEED,
        use_cpu=(device == "cpu"),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    print(f"\nFine-tuning on {device}...")
    print(f"  This takes ~5-15 min on GPU, ~10-20 min on CPU.\n")
    trainer.train()

    # ── 5. Test set evaluation ──────────────────────────────────────────────────
    print("\nEvaluating on test set...")
    raw_preds = trainer.predict(test_ds)
    pred_ids  = np.argmax(raw_preds.predictions, axis=-1).tolist()
    true_ids  = y_test  # string labels

    # convert pred_ids back to string labels
    pred_labels = [ID2LABEL[i] for i in pred_ids]
    true_labels_ids = [LABEL2ID[l] for l in true_ids]

    ft_metrics = full_metrics(true_labels_ids, pred_ids)
    print_metrics(ft_metrics, "FINE-TUNED DistilBERT — Test Set Results")

    # Per-example wrong predictions
    wrong = []
    for text, true, pred in zip(X_test, true_ids, pred_labels):
        if true != pred:
            wrong.append({"text": text, "true_label": true, "predicted": pred})

    if wrong:
        print(f"\nWrong predictions ({len(wrong)}/{len(X_test)}):")
        for w in wrong:
            print(f"  true={w['true_label']:12s}  pred={w['predicted']:12s}")
            print(f"    {w['text'][:100]}...")
    else:
        print(f"\nAll {len(X_test)} test examples predicted correctly.")

    # ── 6. Confusion matrix plot ────────────────────────────────────────────────
    cm_path = RESULTS_DIR / "confusion_matrix.png"
    plot_confusion_matrix(ft_metrics["confusion_matrix"], LABELS, cm_path)

    # ── 7. Load baseline and build comparison ────────────────────────────────────
    baseline_metrics = None
    if Path(BASELINE_PATH).exists():
        with open(BASELINE_PATH, encoding="utf-8") as f:
            baseline_data = json.load(f)
        baseline_metrics = baseline_data["metrics"]
        print("\n" + "=" * 55)
        print("  COMPARISON: Fine-tuned vs Zero-shot Baseline")
        print("=" * 55)
        print(f"  {'Metric':25s} {'Fine-tuned':>12} {'Baseline':>12} {'Delta':>10}")
        print("  " + "-" * 61)

        ft_acc   = ft_metrics["overall_accuracy"]
        bl_acc   = baseline_metrics["overall_accuracy"]
        ft_mf1   = ft_metrics["macro_f1"]
        bl_mf1   = baseline_metrics["macro_f1"]
        print(f"  {'Overall accuracy':25s} {ft_acc:>12.4f} {bl_acc:>12.4f} {ft_acc-bl_acc:>+10.4f}")
        print(f"  {'Macro F1':25s} {ft_mf1:>12.4f} {bl_mf1:>12.4f} {ft_mf1-bl_mf1:>+10.4f}")
        print()
        for label in LABELS:
            ft_f1 = ft_metrics["per_class"][label]["f1"]
            bl_f1 = baseline_metrics["per_class"][label]["f1"]
            print(f"  {label + ' F1':25s} {ft_f1:>12.4f} {bl_f1:>12.4f} {ft_f1-bl_f1:>+10.4f}")
        print("=" * 55)
    else:
        print(f"\nNo baseline results found at {BASELINE_PATH} — skipping comparison.")

    # ── 8. Save evaluation_results.json ─────────────────────────────────────────
    eval_results = {
        "finetuned_model": {
            "base_model": BASE_MODEL,
            "hyperparameters": {
                "epochs":       EPOCHS,
                "learning_rate": LR,
                "batch_size":   BATCH_SIZE,
                "max_length":   MAX_LENGTH,
                "seed":         RANDOM_SEED,
            },
            "metrics": ft_metrics,
            "test_examples": [
                {
                    "text":         text,
                    "true_label":   true,
                    "predicted":    pred,
                    "correct":      true == pred,
                }
                for text, true, pred in zip(X_test, true_ids, pred_labels)
            ],
        },
        "baseline": baseline_metrics,
    }

    out_path = RESULTS_DIR / "evaluation_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2, ensure_ascii=False)
    print(f"\nEvaluation results saved to {out_path}")

    # ── 9. Save model ────────────────────────────────────────────────────────────
    trainer.save_model(str(MODEL_OUT_DIR))
    tokenizer.save_pretrained(str(MODEL_OUT_DIR))
    print(f"Model saved to {MODEL_OUT_DIR}")


if __name__ == "__main__":
    main()
