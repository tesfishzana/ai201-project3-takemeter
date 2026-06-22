"""
TakeMeter — Gradio deployed interface.

Loads the fine-tuned DistilBERT model and serves a web UI where a user
can paste any r/nba post and see the predicted label with per-class
confidence scores.

Usage:
    python scripts/interface.py
    # Opens at http://localhost:7860
    # Set share=True inside main() for a public Gradio link.
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import gradio as gr
import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

MODEL_DIR  = "results/finetuned_model"
LABELS     = ["analysis", "hot_take", "reaction"]
MAX_LENGTH = 256

LABEL_DESCRIPTIONS = {
    "analysis": (
        "A structured argument backed by specific, verifiable evidence "
        "(stats, historical comparison, tactical observation). "
        "The reasoning is present even after stripping the opinion framing."
    ),
    "hot_take": (
        "A bold, confident claim stated as fact, without supporting evidence "
        "or with only decorative/cherry-picked stats. "
        "Asserts a position but does not construct an argument."
    ),
    "reaction": (
        "An immediate emotional response to a game event, trade, or news. "
        "Primarily expressing a feeling in the moment — "
        "little to no argumentative structure."
    ),
}

LABEL_COLORS = {
    "analysis": "#2563eb",   # blue
    "hot_take": "#dc2626",   # red
    "reaction": "#16a34a",   # green
}

EXAMPLES = [
    "The three-pointer has made the shot clock more valuable as a strategic tool. Teams with fewer than 7 seconds on the clock are now taking corner threes at 2.4x the rate they were in 2010, and those shots score at 1.07 points per possession — better than almost any other end-of-clock option.",
    "LeBron James is not the GOAT and never will be. Jordan won six rings, never lost a Finals, and had to deal with the Bad Boy Pistons. LeBron had everything handed to him and still lost Finals. Not even close.",
    "WAIT WHAT. CURRY JUST HIT A 50 FOOTER AT THE BUZZER. I'm screaming. My neighbors hate me right now. That was the most insane thing I've ever seen.",
    "Jayson Tatum just hit a fadeaway over two defenders with 1.3 seconds left to force overtime. This is the best series in ten years and I'm not sleeping until it ends.",
    "Kyrie Irving's shot creation ability is statistically elite: his points per shot attempt off the dribble (.98) is higher than any other guard not named Curry in the last five seasons. The narrative that he's a poor fit in every organization is about behavior and chemistry — his on-court skill set is not in question.",
]


def load_model():
    if not os.path.isdir(MODEL_DIR):
        raise FileNotFoundError(
            f"Model not found at '{MODEL_DIR}'. Run `python scripts/finetune.py` first."
        )
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_DIR)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    return tokenizer, model


def classify(text, tokenizer, model):
    if not text or not text.strip():
        return None, None, "Please enter a post."

    inputs = tokenizer(
        text.strip(),
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
    )
    with torch.no_grad():
        logits = model(**inputs).logits

    probs      = F.softmax(logits, dim=-1).squeeze().tolist()
    pred_idx   = int(torch.argmax(logits).item())
    pred_label = LABELS[pred_idx]
    conf       = probs[pred_idx]

    scores = {LABELS[i]: round(probs[i], 4) for i in range(len(LABELS))}
    return pred_label, conf, scores


def build_output(pred_label, conf, scores):
    if pred_label is None:
        return "<p style='color:gray'>Enter a post above to classify it.</p>", {}

    color = LABEL_COLORS[pred_label]
    desc  = LABEL_DESCRIPTIONS[pred_label]

    html = f"""
    <div style="border-left: 5px solid {color}; padding: 12px 16px; background: #f8fafc; border-radius: 4px;">
      <div style="font-size: 1.4em; font-weight: bold; color: {color}; margin-bottom: 6px;">
        {pred_label.upper().replace('_', ' ')}
      </div>
      <div style="font-size: 0.9em; color: #64748b; margin-bottom: 8px;">
        {desc}
      </div>
      <div style="font-size: 0.85em; color: #374151;">
        Confidence: <strong>{conf:.1%}</strong>
      </div>
    </div>
    """

    bar_data = {label: round(score * 100, 1) for label, score in scores.items()}
    return html, bar_data


def make_classify_fn(tokenizer, model):
    def fn(text):
        pred_label, conf, scores = classify(text, tokenizer, model)
        html, bar_data = build_output(pred_label, conf, scores)
        return html, bar_data
    return fn


def main():
    print("Loading model...")
    tokenizer, model = load_model()
    print("Model loaded. Starting interface...")

    classify_fn = make_classify_fn(tokenizer, model)

    with gr.Blocks(title="TakeMeter — r/nba Discourse Classifier", theme=gr.themes.Soft()) as demo:

        gr.Markdown(
            """
# TakeMeter
### r/nba Discourse Quality Classifier

Paste any NBA-related Reddit post or comment below.
The model will classify it as **analysis**, **hot_take**, or **reaction**
and show its confidence score for each label.

---
"""
        )

        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="Post or Comment",
                    placeholder="Paste an r/nba post here...",
                    lines=5,
                    max_lines=10,
                )
                classify_btn = gr.Button("Classify", variant="primary")

            with gr.Column(scale=2):
                result_html = gr.HTML(
                    value="<p style='color:gray'>Enter a post above to classify it.</p>",
                    label="Prediction",
                )
                confidence_bars = gr.Label(
                    label="Confidence scores (all labels)",
                    num_top_classes=3,
                )

        gr.Markdown("### Try an example")
        gr.Examples(
            examples=[[ex] for ex in EXAMPLES],
            inputs=text_input,
            outputs=[result_html, confidence_bars],
            fn=classify_fn,
            cache_examples=False,
            label="",
        )

        gr.Markdown(
            """
---
**Label definitions**

| Label | Definition |
|---|---|
| `analysis` | Structured argument backed by specific verifiable evidence (stats, historical comparison, tactical observation) |
| `hot_take` | Bold confident claim stated without real supporting reasoning; asserts a position but doesn't argue for it |
| `reaction` | Immediate emotional response to a game, trade, or news; expressing a feeling, not a position |

*Model: distilbert-base-uncased fine-tuned on 151 r/nba examples. See the [repo](https://github.com/tesfishzana/ai201-project3-takemeter) for full details.*
"""
        )

        classify_btn.click(
            fn=classify_fn,
            inputs=text_input,
            outputs=[result_html, confidence_bars],
        )
        text_input.submit(
            fn=classify_fn,
            inputs=text_input,
            outputs=[result_html, confidence_bars],
        )

    demo.launch(share=False)


if __name__ == "__main__":
    main()
