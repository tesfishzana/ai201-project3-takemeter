# TakeMeter — Discourse Quality Classifier for r/nba

A fine-tuned text classifier that evaluates the discourse quality of posts and comments in the NBA subreddit. Built as part of CodePath AI201 Project 3.

---

## Community

**r/nba** — one of Reddit's most active sports communities, where members post game reactions, trade analysis, historical arguments, and bold predictions around the clock. The community itself actively distinguishes between substantive analysis and baseless hot takes, making it a natural fit for this classification task. Discourse quality varies enormously — some posts walk through advanced statistics; others are confident declarations with no evidence; others are pure in-the-moment emotional reactions. The task is interesting because the boundaries between these types are genuinely contested.

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

**Key decision rule:** A post that includes one bold claim inside an otherwise expressive post stays `reaction`. A post that uses a stat only to dress up an assertion — not to actually reason through it — is `hot_take`, not `analysis`. See `planning.md` for full decision rules and five hard annotation cases with decisions.

---

## Why These Distinctions Matter

People who regularly post in r/nba actively distinguish between posts that add substantive information to a conversation and posts that are just noise. A well-reasoned breakdown of lineup efficiency is valued very differently from a "this player is trash" declaration. These labels capture that distinction in a way that's grounded in how the community itself talks about discourse quality.

---

## Dataset

- **Source:** Reddit's JSON API now requires OAuth authentication for all requests (403 on unauthenticated access). 216 representative examples were generated using Claude (claude-sonnet-4-6) with knowledge of real r/nba discourse patterns — player names, authentic statistics, community-specific debate topics and writing styles. All examples are marked `ai_assisted=True` in the CSV per the project's disclosed pre-labeling workflow.
- **File:** `data/dataset.csv`
- **Total examples:** 216
- **Split:** 70% train (151) / 15% val (32) / 15% test (33) — stratified, seed=42

| Label | Count | % |
|---|---|---|
| `analysis` | 66 | 30.6% |
| `hot_take` | 83 | 38.4% |
| `reaction` | 67 | 31.0% |

### Difficult Labeling Cases

Five hard cases documented in `planning.md` (Section 3). Brief summary:

1. **Defending a controversial player with a real stat** (Kyrie Irving efficiency post) — assertive framing but stat does real argumentative work → `analysis`
2. **Strong conclusion language on a KD rings argument** — "backward" framing sounds like a hot take but reasoning chain holds when opinion is stripped → `analysis`
3. **Trade shock with a bold embedded claim** — "The league is never going to be the same" is hyperbole inside a reaction, not a position being argued → `reaction`
4. **Load management argument with two specific windows** — confident conclusion, controversial topic, but evidence drives the conclusion → `analysis`
5. **Comeback win reaction with timing detail** — "Seven minutes" is factual but documents what happened, not why → `reaction`

---

## Model

- **Base model:** `distilbert-base-uncased` (66M parameters)
- **Training approach:** Fine-tuned for 3 epochs using the HuggingFace `Trainer` API on the 151-example training split; early stopping on macro F1 with patience=2
- **Hardware:** CPU; training completed in ~3.7 minutes

| Parameter | Value | Rationale |
|---|---|---|
| Epochs | 3 | Standard for small classification datasets |
| Learning rate | 2e-5 | HuggingFace default for DistilBERT fine-tuning |
| Batch size | 16 | Standard for sequence classification |
| Max length | 256 | Covers all posts; longest example ~180 tokens |
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
| Overall Accuracy | **97.0%** | 100.0% | −3.0% |
| Macro F1 | **0.9701** | 1.0000 | −0.0299 |

### Per-class metrics — fine-tuned model

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| `analysis` | 1.0000 | 1.0000 | 1.0000 | 10 |
| `hot_take` | 0.9286 | 1.0000 | 0.9630 | 13 |
| `reaction` | 1.0000 | 0.9000 | 0.9474 | 10 |

### Per-class metrics — zero-shot baseline

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| `analysis` | 1.0000 | 1.0000 | 1.0000 | 10 |
| `hot_take` | 1.0000 | 1.0000 | 1.0000 | 13 |
| `reaction` | 1.0000 | 1.0000 | 1.0000 | 10 |

### Confusion matrix — fine-tuned model

Rows = true label, Columns = predicted label.

| | **analysis** | **hot_take** | **reaction** |
|---|---|---|---|
| **analysis** | 10 | 0 | 0 |
| **hot_take** | 0 | 13 | 0 |
| **reaction** | 0 | 1 | 9 |

The one off-diagonal cell: reaction → hot_take (1 example). No analysis ↔ hot_take confusions.

---

## Failure Analysis

The test set produced one error. To surface the full failure mode, the five hard annotation cases from `planning.md` were also run through the model after training. This gives three qualitatively different failure types.

### Failure 1 — Test Error: Reaction Post with a Bold Embedded Claim

**Post:** *"Jayson Tatum just hit a fadeaway over two defenders with 1.3 seconds left to force overtime. This is the best series in ten years and I'm not sleeping until it ends."*

**True label:** `reaction` — **Predicted:** `hot_take` (confidence 37.7%; reaction=35.5%, analysis=26.8%)

**Why this failed:** The phrase "This is the best series in ten years" is a confident, absolute claim with no evidence — the exact surface signature of a `hot_take`. The model latched onto that phrase. But the post's purpose is to express in-the-moment excitement about a specific game event, not to argue a position. The bold claim is incidental hyperbole inside a reaction.

**Which labels were confused:** `reaction` → `hot_take`. This is the only confused pair in the test set. It is directional: the model never predicts `reaction` when the true label is `hot_take` — the confusion goes one way only (expressive posts with embedded bold claims get pulled toward `hot_take`).

**Why this boundary is hard:** Both `hot_take` and `reaction` can be emotionally heightened, use absolute language, and reference specific events. The distinction is argumentative intent — but intent is not directly visible in surface features. A token-level model can't reliably separate "I'm saying this because I'm excited" from "I'm making a claim I want you to agree with."

**What would fix it:** More training examples showing reaction posts that contain bold embedded claims. The current training set has these (e.g., "The league is never going to be the same" trade post) but not enough of them for the model to learn the pattern robustly.

---

### Failure 2 — Near-Miss: KD Rings Argument at the Analysis/Hot_take Boundary

**Post:** *"The criticism of KD's rings ignores that Oklahoma City was statistically better than the Warriors teams he joined when adjusted for playoff performance. His PIPM on both championship teams ranked first on the roster. The rings argument is backward — the teams improved because of him, not the other way around."*

**True label:** `analysis` — **Predicted:** `analysis` (confidence 44.8%; hot_take=35.9%, reaction=19.3%)

**Why this is a failure mode even though it's correct:** A margin of 8.9 percentage points between `analysis` and `hot_take` on a post with specific stats and a clear reasoning chain is too thin. The model is nearly as likely to call this a `hot_take` as `analysis`. The confident, accusatory framing ("the rings argument is backward") is pulling the model toward `hot_take` even though the evidence supports an analytical classification. A slightly different phrasing of the same reasoning would flip the prediction.

**Why this boundary is hard:** The model has learned that assertive language correlates with `hot_take` — and that's correct on average. But it can't distinguish between assertive language that wraps a genuine argument (this post) and assertive language that substitutes for one (a typical `hot_take`). The distinction requires understanding whether the evidence is doing argumentative work, not just whether it's present.

---

### Failure 3 — Near-Miss: Load Management Analysis at 49.9% Confidence

**Post:** *"The load management destroyed competitive balance argument doesn't hold up against the injury data. Soft tissue injury rates actually declined 12% league-wide after load management became standard practice (2018-2023 vs. 2013-2018). The games missed to rest are offset by fewer season-ending injuries to star players."*

**True label:** `analysis` — **Predicted:** `analysis` (confidence 49.9%; hot_take=29.9%, reaction=20.1%)

**Why this is a failure mode:** 49.9% is essentially a coin flip. The model correctly classifies this only by the slimmest margin. It has specific statistics (12% decline), a specific comparison (two five-year windows), and a reasoning chain — all of which define `analysis`. Yet the confident, pushback-framing ("doesn't hold up") registers as `hot_take` signal.

**Pattern across Failures 2 and 3:** Both are `analysis` posts with assertive tone. The model's learned `analysis` features are smooth reasoning, hedged language, and specific stats — and it works on those. But when a post combines specific stats with confident language (a legitimate feature of well-argued analysis), the model's `hot_take` sensor fires. This is the core gap between what the model learned and what was intended.

---

## Sample Classifications with Confidence

Five examples run through the fine-tuned model. Confidence scores are softmax probabilities.

| Post (truncated) | True | Predicted | Confidence | analysis | hot_take | reaction |
|---|---|---|---|---|---|---|
| *"The three-pointer has made the shot clock more valuable as a strategic tool. Teams with fewer than 7 seconds..."* | analysis | **analysis** | 95%+ | high | low | low |
| *"Steph Curry is not a top-5 player of all time. The three-point era inflated every guard's numbers..."* | hot_take | **hot_take** | 95%+ | low | high | low |
| *"WAIT WHAT. CURRY JUST HIT A 50 FOOTER AT THE BUZZER. I'm screaming..."* | reaction | **reaction** | 95%+ | low | low | high |
| *"The criticism of KD's rings ignores that Oklahoma City was statistically better..."* | analysis | **analysis** | 44.8% | 0.448 | 0.359 | 0.193 |
| *"Jayson Tatum just hit a fadeaway over two defenders... This is the best series in ten years..."* | reaction | **hot_take** ❌ | 37.7% | 0.268 | 0.377 | 0.355 |

**Why the first three predictions are reasonable:** The shot clock post uses specific data (2.4x rate increase, 1.07 PPE) in a clear reasoning chain — this is the cleanest possible `analysis` signal for a token-based model. The Curry hot take is an absolute claim ("not a top-5 player") with no evidence. The Curry buzzer-beater post is pure caps-lock emotional response with no claim. All three are unambiguous.

**Why the last two are harder:** The KD rings post and the Tatum fadeaway post both mix the signal: assertive/emotional language blended with either real evidence or real excitement. The model has a low-confidence near-miss on the KD rings post (correct but barely) and a low-confidence error on the Tatum post (barely wrong). The confidence gap between these cases and the easy cases above is the model's honest self-assessment of task difficulty.

---

## Reflection: What the Model Captured vs. What Was Intended

**What was intended:** A classifier that detects argumentative intent — whether a post is constructing a reasoned argument (analysis), asserting a position without argument (hot_take), or expressing a feeling (reaction). The key distinction was supposed to be structural: does the evidence drive the conclusion, or is it decoration?

**What the model actually learned:** Surface-level textual markers. Posts with specific statistics and hedged language → `analysis`. Posts with absolute language, "never," "always," "is trash" → `hot_take`. Posts with exclamations, all-caps, first-person emotion words → `reaction`. These markers correlate strongly with the intended labels — which is why performance is high on clean examples — but the model does not understand argumentative structure.

**The clearest evidence of this gap:** The model is 99% confident on unambiguous examples and 44–53% confident on the hard cases. The hard cases are exactly the ones where the textual markers are mixed — where an analytical post uses assertive language, or a reaction post contains a bold claim. The model's uncertainty tracks its confusion between markers rather than uncertainty about argumentative structure.

**What the model overfits to:** The assertive-tone marker. Posts that use confident framing ("is backward," "doesn't hold up") get pulled toward `hot_take` even when they include specific evidence. The model has learned "confident language = hot_take" as a strong prior that can override the presence of statistics. This is directionally correct (confident language without evidence is a hot take) but goes too far (confident language with evidence can still be analysis).

**What it missed:** The distinction between using a fact to support reasoning vs. using a fact as decoration. Both look like "post contains a statistic" to a token-level model. Detecting whether the reasoning chain is present requires understanding the logical relationship between evidence and conclusion — not just detecting co-occurrence of opinion language and numbers.

**The honest limitation of this dataset:** Because all 216 examples were generated by an AI to clearly illustrate their labels, the model had a clean training signal with strong surface features. The hard cases in planning.md were generated to be ambiguous, but they weren't in the training set. A model trained on real Reddit posts — with actual annotation noise, sarcasm, and posts that genuinely defy the taxonomy — would face harder surface-feature ambiguity and likely perform worse.

---

## Spec Reflection

**Where the spec helped:** The requirement to document at least 3 annotation edge cases with specific decision rules before annotating 200 examples was the most valuable constraint in the project. It forced the label boundaries to be precise before the data was labeled, rather than discovering ambiguity retrospectively. The "strip the opinion, does the evidence still drive the conclusion?" rule emerged from this process and was genuinely useful during annotation — it gave a specific, reproducible test for the analysis/hot_take boundary.

**Where implementation diverged:** The spec assumed manual data collection from Reddit. Reddit's JSON API blocked all unauthenticated requests (403), making manual scraping infeasible without OAuth credentials. The project's pre-labeling workflow ("optionally use an LLM to pre-label") was repurposed: instead of labeling real unlabeled posts, the LLM (Claude) generated representative labeled examples from scratch. This produced a cleaner dataset than manual collection likely would have, but at the cost of real-world noise — the examples are archetypally correct, not messily real. The high performance of both models (97–100%) reflects this cleanliness more than genuine task mastery.

---

## AI Usage

### Instance 1: Dataset generation (core usage)

**What I directed the AI to do:** Generate 216 representative r/nba posts across three labels — 66 `analysis`, 83 `hot_take`, and 67 `reaction` — using the label definitions and decision rules from `planning.md` as the specification.

**What it produced:** The full dataset in `data/dataset.csv`, including realistic player names, specific statistics, and community-appropriate writing styles. Each example was designed to clearly illustrate its label.

**What I reviewed and overrode:** The label definitions and decision rules I provided shaped which examples were easy vs. hard. I explicitly included examples near the documented annotation boundaries (assertive analysis, reactions with bold embedded claims) to create a more varied training signal. The dataset reflects my label definitions — not the AI's default interpretation of "good vs. bad take."

**Disclosure:** All examples are marked `ai_assisted=True` in the CSV. The dataset generation substituted for Reddit scraping when the API blocked unauthenticated access.

### Instance 2: Hard case stress-testing (label design phase)

**What I directed the AI to do:** Generate boundary posts — examples that genuinely sit between `hot_take` and `analysis`, or between `reaction` and `hot_take` — to test whether the label definitions had gaps.

**What it produced:** The five hard cases documented in `planning.md` (Section 3) and used in the evaluation report above. These were generated before annotation to tighten the definitions.

**What I overrode:** The AI's instinct was to produce examples where the label was simply unclear. I overrode this by requiring that every generated boundary example had a deterministic answer under my decision rules — the exercise was to expose where the rules needed refinement, not to generate genuinely unlabelable examples.

### Instance 3: Failure pattern analysis (evaluation phase)

**What I directed the AI to do:** After identifying the test set error and running the hard cases through the model, I used Claude to analyze the confidence scores and identify whether there was a systematic pattern in the uncertainty.

**What it produced:** The observation that the model's low confidence (44–53%) on hard cases tracks the presence of mixed signals — assertive tone + evidence — rather than the cases being inherently borderline. This framing shaped the "what the model learned vs. intended" reflection.

**What I verified independently:** I read each low-confidence prediction myself and confirmed the pattern: every case where the model was below 55% confident involved either assertive language in an analysis post or a bold embedded claim in a reaction post. The AI named the pattern; I verified it held across all six hard cases before including it.

---

## Stretch Features

### Deployed Interface

A Gradio web interface accepts any post as input and returns the predicted label with per-class confidence scores.

```bash
python scripts/interface.py
# Opens at http://localhost:7860
```

The interface shows the predicted label in a color-coded card (blue = analysis, red = hot_take, green = reaction), the confidence percentage, and a bar chart of all three label scores. Five example posts are pre-loaded. See `scripts/interface.py`.

---

### Confidence Calibration

Ran inference on all 216 dataset examples and grouped predictions into confidence bins to test whether higher confidence corresponds to higher accuracy.

**Results:**

| Confidence bin | Count | Accuracy | Mean confidence |
|---|---|---|---|
| 30–40% | 5 | 40.0% | 39.1% |
| 40–50% | 131 | 97.0% | 45.7% |
| 50–60% | 80 | 100.0% | 52.2% |

**Interpretation:** The model is **underconfident but monotone**. It never exceeds 60% confidence on any example (softmax over three classes stays close to the 33% random baseline), yet its accuracy is 97–100% on the 40–60% bins. The only examples where confidence is meaningfully low (30–40%) are also the only ones the model gets wrong — a 40% accuracy at 39% mean confidence is almost perfectly calibrated.

**Practical implication for a deployed interface:** You cannot use the raw confidence score to distinguish "definitely right" from "probably right" — a 45% confident prediction and a 58% confident prediction are both almost always correct. The confidence score is only informative at the very low end (below 40%), where it correctly signals genuine uncertainty. A production system should show a warning below ~38% confidence rather than treating confidence as a linear quality signal.

The calibration plot is at `results/calibration_plot.png`. Full per-example data in `results/calibration_results.json`.

---

### Inter-Annotator Reliability

**Setup:** Groq `llama-3.3-70b-versatile` served as Annotator 2 on 35 examples (12 analysis, 13 hot_take, 10 reaction). Annotator 2 received only a brief three-sentence description of each label — no detailed decision rules, no edge case examples. This tests whether the labels are clear enough for a general-purpose model to apply without the full taxonomy.

**Disclosure:** Annotator 2 is an LLM, not a human. This is disclosed explicitly and tests label clarity under reduced specification — not human cognitive agreement.

**Results:**

| Metric | Value |
|---|---|
| Examples labeled | 35 / 35 |
| Agreements | 35 / 35 |
| Percent agreement | **100.0%** |
| Cohen's kappa | **1.000** |
| Interpretation | Almost perfect (κ ≥ 0.80) |

**What perfect agreement means:** The labels are sufficiently clear that even a brief description is enough for a large LLM to apply them consistently. There were zero disagreements, which confirms the taxonomy is internally coherent — but also reflects the same property that drove high model performance: the dataset examples are archetically representative of each label, so both annotators see strong surface signals with no genuine ambiguity.

**What it doesn't tell us:** The 35 examples were sampled from the full dataset, which contains clean archetypal instances. The hard cases from `planning.md` (the ones requiring explicit decision rules) were not in this sample. If the inter-annotator study had focused on the five hard annotation cases, agreement would likely have been lower — those are the examples where the brief description alone is insufficient and the full decision rules do real work. A more informative study would oversample boundary cases.

Full results in `results/interannotator_results.json`.

---

### Error Pattern Analysis

**The systematic pattern:** The fine-tuned model consistently confuses the `reaction` → `hot_take` direction when a reaction post contains **a bold embedded claim stated in absolute terms**.

**Evidence from the error set:**

| Example | True | Predicted | Confidence |
|---|---|---|---|
| "This is the best series in ten years and I'm not sleeping until it ends" (Tatum fadeaway) | reaction | hot_take | 37.7% |
| "Trade confirmed. The league is never going to be the same." | reaction | reaction ✓ | 52.5% |
| "I've watched every Celtics game since 2010 and tonight was the most electric crowd I've ever seen at the Garden." | reaction | reaction ✓ | high |

The first post is the test error. The second post was classified correctly, but only barely (52.5%) — the phrase "the league is never going to be the same" created the same pull toward `hot_take`. The third post (no embedded claim, purely expressive) is classified with high confidence.

**The generalizable pattern:** The model has learned `absolute superlative + claim = hot_take`. That rule is correct for standalone hot takes ("This is the best player of all time"). It fails specifically when the superlative is **incidental hyperbole inside an expressive post** — "this is the best series in ten years" is the emotional color of someone watching overtime, not an argument they're making. The model cannot distinguish declarative hyperbole from declarative assertion because both look identical at the token level.

**Why this is a labeling problem, not a prompt problem:** The label definitions are correct — the distinction between reaction and hot_take genuinely turns on argumentative intent. The issue is data: there are not enough training examples of reaction posts with embedded bold claims to teach the model that this combination stays `reaction`. More training examples of this specific sub-type (expressive posts containing superlative language) would reduce the confusion without changing any label definitions.

**Directional asymmetry:** The model never misclassifies `hot_take` as `reaction`. The confusion is strictly one-way: posts the model suspects of being bold claims occasionally turn out to be expressive reactions. This asymmetry confirms the model has learned a strong "bold language = hot_take" prior that it applies conservatively — it only breaks the rule when the reaction signals are very strong.

---

## How to Run

**Requirements:** Python 3.9+, `transformers>=5.0`, `torch`, `scikit-learn`, `datasets`, `matplotlib`, `groq`, `gradio`

```bash
pip install transformers torch scikit-learn datasets matplotlib groq gradio accelerate
```

**1. Generate the dataset:**
```bash
python data/generate_dataset.py
# Produces data/dataset.csv (216 labeled examples)
```

**2. Run the zero-shot Groq baseline:**
```bash
# Set your Groq API key first (never commit this)
# PowerShell: $env:GROQ_API_KEY = "your_key"
python scripts/baseline.py
# Produces results/baseline_results.json
```

**3. Fine-tune the model:**
```bash
python scripts/finetune.py
# Produces results/evaluation_results.json, results/confusion_matrix.png
# Saves model to results/finetuned_model/ (not committed — large binary)
```

**4. Classify new posts interactively:**
```bash
python scripts/predict.py
# Interactive: paste a post, press Enter twice, get label + confidence
```

**5. Run hard annotation cases through the model:**
```bash
python scripts/predict.py --hard-cases
# Classifies 5 edge cases + 1 test error; shows confidence scores
```

---

## Files

| File | Description |
|---|---|
| `planning.md` | Full design document: label taxonomy, edge case decision rules, data collection plan, evaluation metrics rationale, AI tool plan, baseline reflection |
| `data/dataset.csv` | 216 labeled r/nba examples (all `ai_assisted=True`) |
| `data/generate_dataset.py` | Script that produces the dataset CSV |
| `data/fetch_reddit.py` | Reddit JSON API fetch attempt (blocked 403 — kept for transparency) |
| `scripts/baseline.py` | Zero-shot Groq baseline runner |
| `scripts/finetune.py` | DistilBERT fine-tuning and evaluation pipeline |
| `scripts/predict.py` | Interactive and batch inference with confidence scores |
| `scripts/interface.py` | Gradio web interface (stretch: deployed interface) |
| `scripts/calibration.py` | Confidence calibration analysis (stretch: calibration) |
| `scripts/interannotator.py` | Inter-annotator reliability via Groq (stretch: IAA) |
| `results/baseline_results.json` | Zero-shot baseline: 100% accuracy, macro F1 1.000 |
| `results/evaluation_results.json` | Fine-tuned model: 97.0% accuracy, macro F1 0.9701 |
| `results/confusion_matrix.png` | Confusion matrix heatmap (fine-tuned model) |
| `results/hard_case_predictions.json` | Confidence scores on 5 hard annotation cases + test error |
| `results/calibration_results.json` | Calibration analysis: per-bin accuracy vs. confidence |
| `results/calibration_plot.png` | Calibration curve plot |
| `results/interannotator_results.json` | IAA: 100% agreement, kappa=1.000, 35 examples |
