"""
Run the fine-tuned TakeMeter model on one or more posts.

Usage:
    # Interactive mode (type a post and press Enter twice)
    python scripts/predict.py

    # Batch mode — classify every post in a JSON/text file
    python scripts/predict.py --file path/to/posts.json

    # Quick evaluation of hard edge cases (used in the evaluation report)
    python scripts/predict.py --hard-cases
"""

import argparse
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

MODEL_DIR = "results/finetuned_model"
LABELS    = ["analysis", "hot_take", "reaction"]
LABEL2ID  = {l: i for i, l in enumerate(LABELS)}

# Hard annotation cases from planning.md — used in the evaluation report
HARD_CASES = [
    {
        "name": "Hard Case A — defending controversial player with one real stat",
        "true_label": "analysis",
        "text": (
            "Kyrie Irving's shot creation ability is statistically elite: his points per shot "
            "attempt off the dribble (.98) is higher than any other guard not named Curry in the "
            "last five seasons. The narrative that he's a poor fit in every organization is about "
            "behavior and chemistry — his on-court skill set is not in question if you look at the "
            "efficiency numbers."
        ),
    },
    {
        "name": "Hard Case B — assertive conclusion language on a KD rings argument",
        "true_label": "analysis",
        "text": (
            "The criticism of KD's rings ignores that Oklahoma City was statistically better than "
            "the Warriors teams he joined when adjusted for playoff performance. His PIPM on both "
            "championship teams ranked first on the roster. The rings argument is backward — the "
            "teams improved because of him, not the other way around."
        ),
    },
    {
        "name": "Hard Case C — trade shock with a bold embedded claim",
        "true_label": "reaction",
        "text": (
            "Trade just confirmed. Three All-Stars on the same team. The league is never going to "
            "be the same. I don't know how to feel. I need a minute."
        ),
    },
    {
        "name": "Hard Case D — load management argument with specific two-window comparison",
        "true_label": "analysis",
        "text": (
            "The load management destroyed competitive balance argument doesn't hold up against the "
            "injury data. Soft tissue injury rates actually declined 12% league-wide after load "
            "management became standard practice (2018-2023 vs. 2013-2018). The games missed to "
            "rest are offset by fewer season-ending injuries to star players."
        ),
    },
    {
        "name": "Hard Case E — comeback win reaction with timing detail",
        "true_label": "reaction",
        "text": (
            "The 20-point lead just evaporated in seven minutes. HOW. SEVEN MINUTES. I was making "
            "dinner. I come back. It's tied. I need to sit down."
        ),
    },
    {
        "name": "Test error — Tatum fadeaway reaction",
        "true_label": "reaction",
        "text": (
            "Jayson Tatum just hit a fadeaway over two defenders with 1.3 seconds left to force "
            "overtime. This is the best series in ten years and I'm not sleeping until it ends."
        ),
    },
]


def load_model(model_dir=MODEL_DIR):
    if not os.path.isdir(model_dir):
        print(f"ERROR: Model directory not found at '{model_dir}'.")
        print("Run `python scripts/finetune.py` first to train the model.")
        sys.exit(1)
    tokenizer = DistilBertTokenizerFast.from_pretrained(model_dir)
    model     = DistilBertForSequenceClassification.from_pretrained(model_dir)
    model.eval()
    return tokenizer, model


def predict(tokenizer, model, text, max_length=256):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=max_length,
    )
    with torch.no_grad():
        logits = model(**inputs).logits
    probs     = F.softmax(logits, dim=-1).squeeze().tolist()
    pred_id   = int(torch.argmax(logits).item())
    pred_label = LABELS[pred_id]
    return pred_label, {LABELS[i]: round(probs[i], 4) for i in range(len(LABELS))}


def print_prediction(text, pred_label, probs, true_label=None, name=None):
    if name:
        print(f"\n{'-' * 60}")
        print(f"  {name}")
    print(f"{'-' * 60}")
    preview = text[:120] + "..." if len(text) > 120 else text
    print(f"  Text    : {preview}")
    if true_label:
        correct = "OK" if pred_label == true_label else "XX"
        print(f"  True    : {true_label}  [{correct}]")
    print(f"  Predicted: {pred_label.upper()}  (confidence: {probs[pred_label]:.1%})")
    print(f"  Scores  : ", end="")
    for label in LABELS:
        print(f"{label}={probs[label]:.3f}  ", end="")
    print()


def hard_cases_mode(tokenizer, model):
    print("\n=== Hard Case Evaluation ===")
    print("Running 5 annotation edge cases + 1 test error through the model.\n")
    results = []
    correct = 0
    for case in HARD_CASES:
        pred_label, probs = predict(tokenizer, model, case["text"])
        is_correct = (pred_label == case["true_label"])
        if is_correct:
            correct += 1
        print_prediction(case["text"], pred_label, probs,
                         true_label=case["true_label"], name=case["name"])
        results.append({
            "name":       case["name"],
            "true_label": case["true_label"],
            "predicted":  pred_label,
            "correct":    is_correct,
            "probs":      probs,
            "text":       case["text"],
        })
    print(f"\n{'-' * 60}")
    print(f"Hard case accuracy: {correct}/{len(HARD_CASES)} ({100*correct/len(HARD_CASES):.0f}%)")
    return results


def interactive_mode(tokenizer, model):
    print("\nTakeMeter — fine-tuned r/nba discourse classifier")
    print("Paste a post and press Enter twice to classify. Ctrl-C to quit.\n")
    while True:
        try:
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            text = " ".join(lines).strip()
            if not text:
                continue
            pred_label, probs = predict(tokenizer, model, text)
            print_prediction(text, pred_label, probs)
        except KeyboardInterrupt:
            print("\nBye.")
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hard-cases", action="store_true",
                        help="Classify the documented hard annotation cases")
    parser.add_argument("--file", type=str, help="JSON file of texts to classify")
    args = parser.parse_args()

    print(f"Loading model from {MODEL_DIR}...")
    tokenizer, model = load_model()
    print("Model loaded.\n")

    if args.hard_cases:
        results = hard_cases_mode(tokenizer, model)
        out = "results/hard_case_predictions.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {out}")
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            data = json.load(f)
        texts = data if isinstance(data, list) else data.get("texts", [])
        for item in texts:
            text = item if isinstance(item, str) else item.get("text", "")
            pred_label, probs = predict(tokenizer, model, text)
            print_prediction(text, pred_label, probs)
    else:
        interactive_mode(tokenizer, model)


if __name__ == "__main__":
    main()
