# Failure Taxonomy and Empirical Analysis of Agentic AI Systems

Maryam Aldahmani and Shama Alhosani — United Arab Emirates University.
Author roles are recorded in `src/afs/identity.py` and printed in the report's
authorship appendix and the paper's contributions section; implementation support is
recorded in the acknowledgements.

An empirical study of failures in agentic and multi-agent applications. It has
three parts, which are the three things the project was asked to deliver:

1. a **five-dimension taxonomy** (frozen codebook, with boundaries and coding rules),
2. a **labelled corpus** of 3,089 publicly reported failures with per-record provenance,
3. an **agentic application** that answers ten research questions from the corpus and
   verifies its own numbers before they reach a report.

The written deliverable is `outputs/reports/Agentic_Failure_Study_Report.docx`
(33 tables, 7 figures). A short companion report,
`outputs/reports/Requirement_Conformance.docx`, maps every line of the project
brief to the evidence that satisfies it, and
`outputs/tables/requirements_traceability.csv` is the same matrix in a form you
can filter.

## Seeing what changed

Four places, in order of usefulness:

| What you want | Where |
|---|---|
| What changed, and in which file | `CHANGELOG.md`, one dated entry per release |
| Proof the live site is serving it | `python deploy/proof.py` rewrites `outputs/proof/live_verification.txt`: endpoint responses, published-page checks, headline figures, F1–F4 verdicts, and a SHA-256 per deliverable |
| The running application | `/` for the Conformance tab; `/report/` for the written page |
| Every published revision | `git log` in `outputs/app/` — one commit per release, with the reason in the message |

`outputs/run_audit.jsonl` additionally records each full-pipeline run
(`python -m afs.cli all`) with timestamps, Python version and platform, so a
number can be tied to the run that produced it.

## Headline results (current run)

| Question | Result |
|---|---|
| Most common failure type (RQ1) | Functionality / reasoning defect, 24.2% (95% CI 22.7–25.8%) |
| Second and third | Compatibility / API contract 18.2%, data structure / output parsing 13.7% |
| Causes associated with types (RQ3) | χ² = 3,878.3, df = 81, p < 1e-12, Cramér's V = 0.37 |
| Framework differences (RQ4) | χ² = 1,473.9, V = 0.26 — composition differs by framework |
| Blocking-severity rate (RQ5) | 96.0% (AutoGen) versus 36.5% (OpenAI-Agents and LlamaIndex) |
| Agent complexity (RQ6) | Orchestration/context share rises monotonically across tiers (ρ = 1.0, V = 0.30) |
| Silent escapes (RQ7) | 31.9% of records are not caught by the framework runtime; V = 0.54 by type |
| Corpus coverage (RQ8) | 97.0% labelled; 3.0% unknown, and unknowns stay in every denominator |

Every figure above is recomputed by the critic agent from the raw records and is
blocked from the report if it disagrees with the table it describes.

## Contents

| Path | What it is |
|---|---|
| `configs/taxonomy.v1.yaml` | Frozen codebook: 5 dimensions, category definitions, boundaries, inclusion/exclusion rules, impact rubric |
| `configs/research_questions.yaml` | 10 research questions, each marked single-agent or agent-chain, with method and primary output |
| `src/afs/collect.py` | GitHub collection with rate-limit backoff and per-request provenance |
| `src/afs/classify.py` | Deterministic labeller; each label stores its evidence span and matched rules |
| `src/afs/complexity.py` | Declared-complexity index (0–3 capabilities), its formal definition, and the four checks on the measure |
| `src/afs/exemplars.py` | One traceable, cited exemplar per taxonomy category, chosen by a published demonstration score |
| `src/afs/findings_validation.py` | Robustness of the *findings*: resampling, temporal holdout, leave-one-framework-out, label noise |
| `src/afs/stats.py` | Wilson intervals, chi-square, Cramér's V, Fisher, McNemar, BH-FDR, κ, macro-F1 |
| `src/afs/agents.py` | Planner / Tagger / Statistician / Causal / Comparator / Complexity / Critic / Reporter |
| `src/afs/analysis.py` | Executable analysis for RQ1–RQ10 |
| `src/afs/viz.py` | Publication-quality figures |
| `src/afs/validation.py` | Four validation experiments plus the second-coder protocol |
| `src/afs/requirements.py` | Requirements traceability matrix and the conformance report |
| `src/afs/docx_export.py` | The Word deliverable |
| `data/raw/` | Raw API responses, manifests, collection index |
| `data/processed/failures.jsonl` | The dataset (see schema below) |
| `data/gold/` | Gold annotation sheet and blind second-coder sheet |
| `outputs/` | Tables, figures, transcript, report, run audit |

## Dataset

3,094 candidate issues seen, 3,089 retained. The five exclusions are recorded in
`data/processed/exclusions.json` with a reason each (3 question-only, 2 with no
failure signal) — no record is dropped silently, and unclassifiable records are
kept in the corpus as `A10_unknown`.

| Framework | Repository | Records |
|---|---|---|
| AutoGPT | Significant-Gravitas/AutoGPT | 598 |
| LangGraph | langchain-ai/langgraph | 539 |
| CrewAI | crewAIInc/crewAI | 533 |
| LlamaIndex | run-llama/llama_index | 436 |
| OpenAI Agents | openai/openai-agents-python | 337 |
| AutoGen | microsoft/autogen | 300 |
| MetaGPT | FoundationAgents/MetaGPT | 238 |
| SWE-agent | SWE-agent/SWE-agent | 108 |

Record schema (`data/processed/failures.jsonl`, one JSON object per line):

| Field | Meaning |
|---|---|
| `record_id`, `url`, `repo`, `issue_number` | Provenance; `record_id` is a stable hash |
| `framework`, `created_at`, `year`, `state`, `labels`, `comments` | Context from the tracker |
| `A_failure_type`, `A_confidence`, `A_evidence` | Primary dimension + evidence span that produced it |
| `B_cause_class`, `B_secondary`, `B_evidence_grade` | Stated cause, plus demonstrated / supported / hypothesised |
| `C_lifecycle_stage`, `D_severity`, `E_detection_point` | Remaining three dimensions |
| `matched_rules`, `taxonomy_version`, `filter_reason` | Full audit trail for the label |

### The released dataset (`outputs/hf_dataset/`)

**Published:** [huggingface.co/datasets/agentic-failure-study/failures-in-agentic-ai](https://huggingface.co/datasets/agentic-failure-study/failures-in-agentic-ai) —
`load_dataset("agentic-failure-study/failures-in-agentic-ai")` returns 3,089 rows and
32 features.

> Every public link in this project is derived from one module, `src/afs/identity.py`.
> To move the repository or the dataset to another namespace, set `AFS_GH_OWNER`,
> `AFS_HF_OWNER` (and the `*_REPO` variants if the names change), rebuild with
> `python -m afs.cli export && python -m afs.cli hf && python -m afs.cli handover`,
> then run `python tools/check_identity.py` to prove no stale link survived.

The corpus is packaged for reuse in the layout `load_dataset` expects, built by
`python -m afs.cli hf`:

| File | Contents |
|---|---|
| `README.md` | Dataset card: YAML front matter, schema, class and framework distribution, limitations, citation. Counts are generated from the parquet, so they cannot drift |
| `data/train-00000-of-00001.parquet` | 3,089 rows, 32 typed columns, zstd |
| `data/exemplars.parquet` | 49 cited examples covering all 10 failure types |
| `codebook/taxonomy.v1.yaml` | The codebook the labels were produced with |
| `codebook/schema.md` | Column-by-column schema |
| `LICENSE`, `CITATION.cff` | CC BY 4.0 for the annotations; MIT for the code |

Full issue text is **not** redistributed: each row carries the permalink, the
title, and the short evidence span that decided the label. Publishing is a
separate, credentialled step:

```bash
python deploy/push_hf.py --repo-id <user>/<name>          # pre-flight only
python deploy/push_hf.py --repo-id <user>/<name> --yes     # publish (needs HF_TOKEN)
```

The pre-flight refuses to upload if the card's row count disagrees with the
parquet, if any label is not in the shipped codebook, or if the front matter does
not parse. The release is also served read-only at `/dataset/` by the live app
and summarised at `/api/dataset`.

The card deliberately uses `configs` and nothing else in its front matter. An
earlier version also carried a `dataset_info` block; the Hub accepted the card but
its viewer could not resolve the split, so the redundant block was removed and a
test now pins the single-source-of-truth form.

## Run

```bash
pip install -r requirements.txt

python -m afs.cli collect --pages 3   # ~6 min, rate-limited
python -m afs.cli build               # normalise + label
python -m afs.cli analyze             # multi-agent pipeline
python -m afs.cli validate            # instrument E1-E5, findings F1-F4, exemplars
python -m afs.cli requirements        # traceability matrix + conformance report
python -m afs.cli export              # Word report
python -m afs.cli hf                  # Hugging Face dataset package
python -m afs.cli all                 # build -> analyze -> validate -> export -> hf
```

Set `PYTHONPATH=src` (Windows: `$env:PYTHONPATH="src"`) first. Tests:

```bash
python -m unittest discover -s tests -v   # 39 tests
```

Regenerating the corpus is deterministic: the labeller is rule-based, so the same
input text yields the same label and the same evidence span.

## Design commitments

1. **No unsupported numbers.** The critic agent recomputes every headline metric
   from the raw records on an independent code path; a mismatch blocks the result.
2. **No hidden exclusions.** Every filtered-out issue is recorded with a reason,
   and unclassified records stay in every denominator.
3. **Association is not causation.** Dimension B records the mechanism the report
   states, graded demonstrated / supported / hypothesised / unknown. Only 374
   records (12.1%) name a concrete mechanism, and the report says so.
4. **Reproducible labelling.** A reviewer can regenerate any label and read the
   evidence span and rule list that produced it.

## Validation status

| Experiment | What it measures | Result |
|---|---|---|
| E1 reference agreement | Labeller vs. codebook annotation, 100 records | 51.0% exact match, macro-F1 0.536, κ = 0.44 (moderate) |
| E2 perturbation | Label stability when the text is reworded | 81.3% retention (95% CI 74.3–86.8%) |
| E3 cue ablation | Dependence on traceback/exception cues | 2.7% of labels change when those rules are removed |
| E4 calibration | Does stated confidence predict correctness? | Correctness rises 39% → 40% → 50% → 60% across the four confidence bins — informative but not calibrated |
| E5 second coder | Independent human agreement | **Pending** — `data/gold/second_coder_sheet.csv` is generated and unscored |

E1 is the number to read honestly: agreement is *moderate*, not high. The residual
error concentrates on two codebook boundaries (compatibility vs. configuration,
functionality vs. output parsing). Those boundaries are the first task for codebook
v1.1, and E5 is the step that converts this from a single-coder classification into
a measurement.

## Findings robustness

E1–E5 test the *instrument*. F1–F4 test the *findings* — whether the headline
claims survive the ways an observational corpus can mislead. Both are re-run by
`afs validate` and written to `outputs/tables/findings_validation.json`.

| Test | Claim under test | Result |
|---|---|---|
| F1 resampling | The top category is a property of the population, not of this 3,089-record draw (1,000 bootstrap resamples) | **Stable** — top-1 retained in 100% of resamples, top-3 set stability 0.97; every category keeps its rank band |
| F2 temporal holdout | Composition is stationary before and after 2025 | **Not stable** — the mix shifts (V = 0.30, p < 1e-12): early records lead with compatibility, late records with functionality. Reported as a historical finding, not smoothed over |
| F3 leave-one-framework-out | The ranking and the framework association are not driven by one repository | **Stable** — the top category is unchanged in all 8 exclusions; V stays within 0.23–0.30 |
| F4 label noise | The ranking survives labelling error at the *measured* disagreement rate (0.49) | **Direction stable, magnitude uncertain** — top-1 retained in 100% of 300 simulations under both symmetric and confusion-driven noise; top-3 set stability 0.88–0.92 |

F2 is the reason the report does not claim the taxonomy describes "agentic AI in
general". It describes a reporting population whose composition changed as the
frameworks matured, and the change is itself a result.

## Conformance to the brief

Every requirement in the supervisor checklist and the project requirements
document is traced to the artefact that satisfies it:

```bash
python -m afs.cli requirements   # writes the CSV and the DOCX
```

- `outputs/tables/requirements_traceability.csv` — 26 rows: id, requirement,
  prior status, current status, evidence, location, how it was closed, source.
- `outputs/reports/Requirement_Conformance.docx` — the same matrix as a readable
  three-page report, grouped by document, with the limits stated next to the
  rows that carry them.

The matrix is generated from measured values, so it cannot drift from the
artefacts: if exemplar coverage drops below 10 of 10 categories, or a validation
result disappears, the corresponding row stops saying "Met". Current state: 20
met, 6 met with a stated limit (the limits are E5 still open, moderate agreement,
declared rather than instrumented complexity, and the sampling frame).

## Known limitations

- **Single coder.** E1 compares the labeller against a first-pass annotation, not
  against an independent expert. Until `second_coder_sheet.csv` is completed and
  scored, agreement is reported as a limitation rather than as a validation.
- **Issue-tracker sampling.** The corpus is what people chose to report. Failures
  that a team fixed silently, or that users never attributed to the framework, are
  absent. Frequency shares describe the reporting population, not all failures.
- **Cause grades are uneven.** 12.1% of records state a checkable mechanism;
  the rest are graded supported or hypothesised, and no causal language is used
  for an association that the design cannot identify.
- **Windows environment.** `pandas` is blocked by local Application Control policy,
  so all statistics are implemented in `numpy`/`scipy`/stdlib. Results do not depend
  on that choice, but the dependency list reflects it.

## Deployment

The browser application is published at
**https://agentic.theaiplusplus.com/** and deployed by CI on every push to
`main` of the site repository.

| Piece | Where |
|---|---|
| Live site | https://agentic.theaiplusplus.com/ |
| Static report mirror | `https://agentic-failure-study.github.io/agentic-failure-study/` |
| Site repository | `agentic-failure-study/agentic-failure-study` |
| Workflow | `.github/workflows/deploy.yml` in that repository |
| Host | `169.58.96.40`, document root `/var/www/agentic.theaiplusplus.com` |
| vhost | `/etc/nginx/sites-available/agentic.theaiplusplus.com` (also answers on `:8099`) |
| Deploy identity | system user `agentic-deploy`, key restricted by `rrsync -wo` to the document root |
| Certificate | Let's Encrypt, `agentic.theaiplusplus.com`, auto-renewed by `agentic-cert-renew.timer` |

Pushing a rebuilt `index.html` is the whole release process:

```bash
python -m afs.cli app            # rebuild the page
cd outputs/app
git add -A && git commit -m "rebuild"
git push                         # guard -> rsync -> live probe
```

The workflow refuses to publish if the page contains anything that looks like a
credential, checks that the expected record count is embedded, then rsyncs and
probes the live URL over HTTPS.

`deploy/` holds the scripts used to provision the host. They are idempotent and
additive: one system user, one vhost, one certificate, one timer. Nothing else
on that machine is modified.

## Handover artefacts

```bash
python -m afs.cli paper         # journal-style manuscript
python -m afs.cli app           # self-contained browser application
python -m afs.cli handover      # annotation packet, one-pager, deck
python -m afs.cli score-coder   # kappa once the second coder sheet is filled
```

| File in `outputs/` | Use |
|---|---|
| `app/index.html` | The application: a single self-contained page — overview, searchable corpus, framework comparison, codebook with cited exemplars, research questions, validation, conformance, downloads. Opens by double-click; no server, install or network |
| `reports/Agentic_Failure_Study_Paper.docx` / `.pdf` | Journal-style article: structured abstract, author summary, IMRaD body, 7 tables, 6 figures, data/code statements, 16 references |
| `handover/One_Page_Summary.docx` / `.pdf` | The single page to read before the meeting: ask, findings, evidence limit, decisions |
| `handover/Agentic_Failure_Study_Deck.pptx` / `.pdf` | 13 slides with speaker notes, built from the verified results |
| `handover/Second_Coder_Packet.docx` / `.pdf` | Blind 40-record annotation packet: rules, ten category tests, blank label cells |
| `reports/Requirement_Conformance.docx` | Three-page matrix tracing all 26 brief requirements to evidence, with the stated limits |

`app/index.html` is the artefact to hand over if the reader wants to check the
data rather than read about it. Every record in it can be searched, filtered by
framework, type and severity, and opened to reveal its evidence span, the rules
that fired and a link to the original report. Because the corpus, codebook,
figures and result tables are embedded in the single file, it cannot drift out
of sync with the report, and it can be emailed or dropped on any static host
without a build step. `app/data/` carries the same material as flat files for
anyone who wants to re-analyse it.

The manuscript's format was chosen by analysing four published articles across
clinical, bioinformatics, management-review and computational-biology venues.
The conventions common to all four — a colon title naming object and design, a
structured abstract, statistics reported with intervals rather than as bare
claims, an explicit availability statement, and a limitations section — are the
ones adopted here. Two venue-specific conventions were also adopted: the
PLOS-style plain-language **Author summary**, and the Oxford-style
**Availability and implementation** field in the abstract, which suits a paper
whose main artefact is code plus a dataset.

The packet exists because E5 cannot be completed by the authors alone. Give it to
a second coder with no access to `gold_sample.csv`; fill `coder2_label` in
`data/gold/second_coder_sheet.csv` by `record_id`, then run `score-coder`.

## Next steps

1. Complete the second coder (E5) and adjudicate disagreements — highest value.
2. Sharpen the two contested boundaries in codebook v1.1 and re-score E1.
3. Extend the corpus to Discord/Slack logs and Hugging Face failure datasets.
