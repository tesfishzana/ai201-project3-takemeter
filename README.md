# TakeMeter — Discourse Quality Classifier for r/nba

A fine-tuned text classifier that evaluates the discourse quality of posts and comments in the NBA subreddit. Built as part of CodePath AI201 Project 3.

---

## Community

**r/nba** — one of Reddit's most active sports communities, where members post game reactions, trade analysis, historical arguments, and bold predictions around the clock. The community itself actively distinguishes between substantive analysis and baseless hot takes, making it a natural fit for this classification task.

---

## Label Taxonomy

The classifier assigns each post to exactly one of three labels:

### `analysis`
A structured argument backed by specific, verifiable evidence — statistics, historical comparison, tactical observation, or cited reporting. The reasoning is present even after stripping away the opinion framing.

> **Example:** "The Lakers' half-court offense ranks 28th in points per 100 possessions when LeBron sits. The 'he's dragging the team' narrative ignores that no other ball-handler creates the same spacing."

### `hot_take`
A bold, confident claim stated as fact, without supporting evidence or with only decorative/cherry-picked stats. The post asserts a strong opinion but doesn't construct an argument. Often contrarian or phrased to provoke.

> **Example:** "Steph Curry is not top-5 all time. The three-point era inflated every guard's numbers. Put him in the 80s and he's an above-average starter."

### `reaction`
An immediate emotional response to a specific game event, trade announcement, or news item. The post is primarily expressing a feeling in the moment — little to no argumentative structure.

> **Example:** "I cannot believe they blew a 20-point fourth quarter lead AGAIN. This team is going to give me a heart attack. Season over fr"

---

## Why These Distinctions Matter

People who regularly post in r/nba actively distinguish between posts that add substantive information to a conversation and posts that are just noise. A well-reasoned breakdown of lineup efficiency is valued very differently from a "this player is trash" declaration. These labels capture that distinction in a way that's grounded in how the community itself talks about discourse quality.

---

## Dataset

- **Source:** Reddit's JSON API now requires OAuth authentication; 216 representative examples were generated using Claude with knowledge of real r/nba discourse patterns (player names, authentic statistics, community-specific debate topics and writing styles). All examples are marked `ai_assisted=True` in the CSV per the project's disclosed pre-labeling workflow.
- **File:** `data/dataset.csv`
- **Total examples:** 216
- **Split:** 70% / 15% / 15% train/val/test (handled by Colab notebook)
- **Label distribution:**

| Label | Count | % |
|---|---|---|
| `analysis` | 66 | 30.6% |
| `hot_take` | 83 | 38.4% |
| `reaction` | 67 | 31.0% |

### Difficult Labeling Cases

Five hard cases are documented in `planning.md` (Section 3, "Hard Cases Encountered During Annotation"). Brief summary:

1. **Defending a controversial player with a real stat** — Kyrie Irving efficiency post. Assertive framing but stat does real argumentative work → `analysis`.
2. **Strong conclusion language on a KD rings argument** — "backward" framing sounds like a hot take but the reasoning chain holds when opinion is stripped → `analysis`.
3. **Shocking trade news with a bold embedded claim** — "The league is never going to be the same" is a hyperbole serving the emotional reaction, not a position being argued → `reaction`.
4. **Load management argument with specific two-window comparison** — Confident conclusion, controversial topic, but evidence drives the conclusion → `analysis`.
5. **Comeback win reaction with timing detail** — "Seven minutes" is factual but documents what happened, not why. No argumentative intent → `reaction`.

---

## Model

- **Base model:** `distilbert-base-uncased` (66M parameters)
- **Training approach:** Fine-tuned for 3 epochs using the HuggingFace `Trainer` API on the 151-example training split
- **Hardware:** CPU (no GPU available locally); training completed in ~3.7 minutes
- **Hyperparameters:**

| Parameter | Value | Rationale |
|---|---|---|
| Epochs | 3 | Standard for small classification datasets; early stopping on macro F1 |
| Learning rate | 2e-5 | HuggingFace default for DistilBERT fine-tuning |
| Batch size | 16 | Fits comfortably in memory; standard for sequence classification |
| Max length | 256 | Covers all posts (longest ~180 tokens); pads shorter ones |
| Seed | 42 | Matches baseline split seed for identical test sets |

**Training curve (validation set):**

| Epoch | Val Accuracy | Val Macro F1 |
|---|---|---|
| 1 | 71.9% | 0.707 |
| 2 | 90.6% | 0.909 |
| 3 | **93.8%** | **0.939** |

---

## Evaluation Results

Zero-shot baseline: `llama-3.3-70b-versatile` via Groq (no task-specific training).
Fine-tuned model: `distilbert-base-uncased` trained on 151 examples for 3 epochs.
Test set: 33 examples (same stratified split, seed=42, for both models).

### Overall metrics

| Metric | Fine-tuned DistilBERT | Zero-shot Baseline | Delta |
|---|---|---|---|
| Overall Accuracy | **97.0%** | 100.0% | -3.0% |
| Macro F1 | **0.9701** | 1.0000 | -0.0299 |

### Per-class metrics (fine-tuned model)

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| `analysis` | 1.0000 | 1.0000 | 1.0000 | 10 |
| `hot_take` | 0.9286 | 1.0000 | 0.9630 | 13 |
| `reaction` | 1.0000 | 0.9000 | 0.9474 | 10 |

### Confusion matrix (fine-tuned model)

Rows = true label, Columns = predicted label.

|  | analysis | hot_take | reaction |
|---|---|---|---|
| **analysis** | 10 | 0 | 0 |
| **hot_take** | 0 | 13 | 0 |
| **reaction** | 0 | **1** | 9 |

The single error: one `reaction` post was predicted as `hot_take`. See the Evaluation Report section below.

### Per-class metrics (zero-shot baseline)

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| `analysis` | 1.0000 | 1.0000 | 1.0000 | 10 |
| `hot_take` | 1.0000 | 1.0000 | 1.0000 | 13 |
| `reaction` | 1.0000 | 1.0000 | 1.0000 | 10 |

---

## How to Run

> *(To be filled in after Milestone 3)*

---

## Files

| File | Description |
|---|---|
| `planning.md` | Label design, edge cases, data collection plan, milestone tracker |
| `data/dataset.csv` | Annotated dataset (added after Milestone 2) |
| `evaluation_results.json` | Per-example predictions and metrics (added after Milestone 5) |
| `confusion_matrix.png` | Confusion matrix visualization (added after Milestone 5) |
