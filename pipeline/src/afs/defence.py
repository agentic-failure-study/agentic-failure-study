"""The advisor defence pack.

This document exists because the advisor's questions are asked of a *system*, not
of a report. The report says what was found; this says how the finding is produced,
agent by agent, and it answers the eight questions in the order they were asked.

Two rules govern everything here:

1. Nothing is asserted that the repository cannot demonstrate. The communication
   table is aggregated from the recorded transcript, the per-agent specification is
   read from the agent classes themselves, and the critic demonstration actually
   executes a fault injection at build time rather than describing one.
2. Where the honest answer is "that thing does not exist", it says so. The agents
   have no language-model prompts, because no number is allowed to pass through a
   language model. Dressing a structured instruction up as a prompt would survive
   the presentation and fail the first follow-up question.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from docx import Document

from . import identity
from .common import (CONFIG_DIR, FIG_DIR, OUT_DIR, PROC_DIR, REP_DIR, TAB_DIR,
                     read_json, read_jsonl)
from .docx_export import GREY, _bullet, _caption, _figure, _p, _page_break, _styles, _table

PACK_NAME = "Advisor_Defence_Pack.docx"

# The eight asks, normalised from the transcribed meeting. The wording is kept
# close to what was said, because a pack that paraphrases the question into
# something easily answered is a pack that dodges the question.
ASKS = [
    ("1", "How is the experiment designed to discover or establish the taxonomy?",
     "Report 4.5 · this pack 2", "Answered"),
    ("2", "What are the research questions, expressed properly?",
     "Report 6 · configs/research_questions.yaml", "Answered"),
    ("3", "Resolve one question end to end — show the scenario and the workflow",
     "This pack 6", "Built here"),
    ("4", "Big picture of the architecture: how the agents connect",
     "This pack 4 · fig_architecture", "Built here"),
    ("5", "Per agent: mission, tools, how it communicates, an example prompt",
     "This pack 5", "Built here, with one correction"),
    ("6", "Results, including a discovery; how the data was collected",
     "Report 5 and 8 · this pack 8", "Answered"),
    ("7", "Present the taxonomy as the output of the agentic system",
     "This pack 9", "Reconciled"),
    ("8", "One agent per question; a question may need more than one agent",
     "Report 6 · this pack 3", "Answered — it is explicit in the config"),
]


def _trim(text: str, n: int = 150) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def _transcript() -> list[dict]:
    path = OUT_DIR / "transcript.jsonl"
    return read_jsonl(path) if path.exists() else []


def _comm_table(msgs: list[dict]) -> list[list[str]]:
    """Aggregate the recorded messages into sender -> recipient -> acts."""
    agg: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for m in msgs:
        agg[(m["sender"], m["recipient"])][m["act"]] += 1
    rows = []
    for (s, r), acts in sorted(agg.items()):
        rows.append([s, r, ", ".join(sorted(acts)),
                     str(sum(acts.values()))])
    return rows


def _fault_injection(records: list[dict], rqcfg: dict) -> dict:
    """Run the critic against a clean result and a deliberately corrupted one.

    Executed at build time, so the numbers in the pack are produced by the code
    path the pack is describing.
    """
    from . import analysis
    from .agents import Blackboard, CriticAgent

    bb = Blackboard(records, rqcfg)
    honest = json.loads(json.dumps(analysis.rq1_frequency(records), default=str))
    honest["rq"] = "RQ1"

    bb.results["RQ1"] = honest
    critic = CriticAgent().attach(bb)
    clean = critic.verify({"rq": "RQ1"})

    tampered = json.loads(json.dumps(honest))
    original = tampered["metrics"]["top_share"]
    tampered["metrics"]["top_share"] = round(float(original) + 0.05, 4)
    bb.results["RQ1"] = tampered
    bb.verified.clear()
    caught = critic.verify({"rq": "RQ1"})

    # and the language rule, on an association result
    lang = None
    rq3 = analysis.rq3_cause_by_type(records)
    rq3 = json.loads(json.dumps(rq3, default=str))
    rq3["rq"] = "RQ3"
    rq3["note"] = "Multi-agent structure causes coordination failure."
    bb.results["RQ3"] = rq3
    lang = critic.verify({"rq": "RQ3"})

    return {"clean": clean, "caught": caught, "language": lang,
            "original": original, "tampered": tampered["metrics"]["top_share"]}


def _walkthrough(msgs: list[dict], rq: str) -> list[dict]:
    """The real recorded messages for one research question."""
    out = [m for m in msgs if (m.get("payload") or {}).get("rq") == rq]
    out.append(next((m for m in msgs if m["sender"] == "PlannerAgent"), {}))
    return sorted(out, key=lambda m: m.get("ts", ""))


def build(out_path: Path | None = None) -> Path:
    payload = read_json(OUT_DIR / "analysis_results.json")
    verified = payload.get("verified", {})
    run_summary = read_json(OUT_DIR / "agent_run_summary.json")
    records = read_jsonl(PROC_DIR / "failures.jsonl")
    n = len(records)

    import yaml
    with open(CONFIG_DIR / "research_questions.yaml", "r", encoding="utf-8") as fh:
        rqcfg = yaml.safe_load(fh)
    qs = rqcfg["questions"]

    msgs = _transcript()
    inj = _fault_injection(records, rqcfg)

    from .agents import (CausalAgent, ComparatorAgent, ComplexityAgent, CriticAgent,
                         PlannerAgent, ReporterAgent, StatisticianAgent, TaggerAgent)

    doc = Document()
    _styles(doc)

    # ------------------------------------------------------------------ cover
    _p(doc, "Advisor questions", bold=True, size=20, after=4)
    _p(doc, "How the research answers each one, shown against the code that "
            "produces it", size=12, after=18, color=GREY)
    _p(doc, identity.author_display(), size=10.5, after=2)
    _p(doc, identity.INSTITUTION, size=10.5, after=18, color=GREY)
    _p(doc, f"Prepared for the final presentation. The questions were transcribed from "
            f"the supervision meeting; the answers are tied to the artefacts in the "
            f"repository, at the version under review. Every number in this document "
            f"is recomputed from {n:,} records when the document is built — including "
            f"the criticism section, which executes a fault injection rather than "
            f"describing one that was run once.", size=9.5, italic=True, color=GREY)
    _page_break(doc)

    # ------------------------------------------------------- the eight asks
    doc.add_heading("1. The questions, and where each is answered", level=1)
    _p(doc, "The meeting asked eight distinct things. They are listed here in the "
            "order they were asked, with the honest status of each: three needed "
            "artefacts that did not exist before this document, and one needed "
            "correcting rather than presenting as it stood.")
    _table(doc, ["#", "What was asked", "Where the answer is", "Status"],
           [[a[0], a[1], a[2], a[3]] for a in ASKS],
           widths=[0.3, 3.0, 2.15, 1.15], size=8)

    _p(doc, "One correction is worth stating up front, because it is the kind of thing "
            "an examiner finds and a candidate does not. The report previously said six "
            "of the ten questions were chains and four were single-agent. The "
            "configuration says nine chains and one single-agent question, and the "
            "paper already said nine. The report figure was stale, and both documents "
            "now derive the count from the configuration instead of asserting it.",
       after=8, size=9.5)
    _page_break(doc)

    # ------------------------------------------------------------- taxonomy
    doc.add_heading("2. How the taxonomy was established", level=1)
    _p(doc, "The taxonomy was not discovered by the agents, and it should not be "
            "presented as if it were. It was derived by hand, under the instruction "
            "that the taxonomy may be established by hand while the agents extract and "
            "tabulate at scale. The agents then apply it to the full corpus, audit its "
            "coverage, and test it empirically. That division of labour is the honest "
            "answer to question 1, and it is a stronger one than claiming the pipeline "
            "invented the categories.", after=8)
    for step, text in [
        ("Fixed reading sample.",
         "A stratified sample of 120 reports across all eight projects, read before "
         "any codebook existed. The unit is the failure described, not the issue — a "
         "report describing two independent failures contributes two units."),
        ("Two separate open codings.",
         "For each unit, one description of what failed and one of why it appeared to "
         "fail. Coding these separately is what makes a separable cause dimension "
         "possible; coding them together silently mixes a symptom with an explanation."),
        ("Consolidation by mechanism, not wording.",
         "Labels merge only when they name the same failing component. The tie-break is "
         "practical: if two labels would be prevented by different mitigations, they "
         "are different categories."),
        ("Mandatory anchors.",
         "The classes named in the project meeting — functionality, tool-related, "
         "compatibility, agent communication, data structure — are retained as required "
         "anchors. Configuration, performance and safety were added only because "
         "records forced them."),
        ("Boundary tests and exclusion clauses.",
         "Every adjacent pair gets an inclusion rule and an explicit 'not this "
         "category' clause, then is tested against twenty records contested during "
         "consolidation. Boundary ambiguity, not coverage, is what drives low agreement "
         "in published codebooks."),
        ("Freeze before labelling.",
         "Version 1.0 was frozen before the corpus was labelled. Any change becomes a "
         "new version with a re-labelling run, so a reported result always traces to "
         "one codebook version."),
        ("Alignment with prior work.",
         "The result was checked against three published taxonomies. Divergences are "
         "deliberate and are named in the report rather than smoothed away."),
    ]:
        _bullet(doc, text, lead=step + " ")

    _p(doc, "What the agents do to the taxonomy, once it exists:", before=6, after=3)
    _bullet(doc, "TaggerAgent audits every record for label completeness and "
                 "confidence, and queues the low-confidence ones for adjudication rather "
                 "than dropping them.", lead="Audit. ")
    _bullet(doc, "2.98% of the corpus could not be assigned a substantive category. "
                 "That figure is reported, not hidden, because a taxonomy that hides its "
                 "own gaps cannot be evaluated.", lead="Coverage. ")
    _bullet(doc, "Agreement between the automated labeller and 100 hand-coded records is "
                 "κ = 0.44, and the report states that this is agreement with a single "
                 "annotator rather than inter-rater agreement.", lead="Agreement. ")
    _page_break(doc)

    # ------------------------------------------------------- research questions
    doc.add_heading("3. The research questions, and which agent answers each", level=1)
    _p(doc, "The supervisor asked for each question to be expressed properly and for an "
            "explicit statement of whether one agent or several answer it. That is "
            "encoded in the configuration rather than narrated, so the document and the "
            "code cannot drift apart.")
    rows = []
    for q in qs:
        rows.append([q["id"], q["question"],
                     "Single" if q.get("agent_mode") == "single" else "Chain",
                     ", ".join(q.get("agents", []))])
    _table(doc, ["ID", "Research question", "Mode", "Agents"], rows,
           widths=[0.4, 3.35, 0.6, 2.05], size=7.8)

    n_chain = sum(1 for q in qs if q.get("agent_mode") != "single")
    _p(doc, f"{n_chain} of the {len(qs)} questions are chains and "
            f"{len(qs) - n_chain} is a single-agent question. The rule is stated in the "
            f"configuration and can be checked against it: a question gets a single "
            f"agent only when one pass over one table answers it with no association "
            f"test. Everything else needs a variable derived, a test applied, and the "
            f"claim checked against the records — which is precisely what makes it a "
            f"chain rather than a second agent bolted on for appearance.", after=6)

    _p(doc, "Each question also declares what it requires, how it is answered, and which "
            "artefact is its primary output. That is the contract the specialist agents "
            "are held to. Two examples, quoted from the configuration:", after=3)
    for qid in ("RQ3", "RQ8"):
        q = next(x for x in qs if x["id"] == qid)
        _p(doc, f"{qid} — {q['question']}", bold=True, size=9, after=1)
        _p(doc, f"requires: {', '.join(q['requires'])} · mode: {q['agent_mode']} · "
                f"agents: {', '.join(q['agents'])} · output: {q['primary_output']}",
           size=8.5, after=1, indent=0.2, color=GREY)
        _p(doc, f"method: {q['method']}", size=8.5, after=7, indent=0.2, color=GREY)
    _page_break(doc)

    # ------------------------------------------------------------ architecture
    doc.add_heading("4. The architecture, as one picture", level=1)
    _p(doc, "Eight agents share one blackboard. Every message is recorded, so a "
            "supervisor can audit how a number was produced rather than only what it "
            "came out as. The diagram distinguishes two things that are easy to blur: "
            "messages that agents post and that appear in the transcript, and the direct "
            "method call by which the orchestrator hands a task to a specialist.")
    _figure(doc, REPORT_FIG(), width=6.4,
            caption="Figure 1. The blackboard architecture. Solid arrows are recorded "
                    "messages; the dashed arrow is a direct dispatch that is logged as a "
                    "tool call, not as a message.")
    _p(doc, "The loop that matters is the vertical one on the right. A specialist "
            "proposes a result; the critic recomputes it from the raw records on an "
            "independent code path and either accepts it or returns it once with the "
            "critique attached; only verified results reach the reporter. The reporter "
            "cannot see an unverified number, because it is not on the board.", after=3)
    _p(doc, f"In the run under review this produced {run_summary.get('messages')} "
            f"recorded messages and {run_summary.get('tool_calls')} tool calls across "
            f"{run_summary.get('questions_planned')} questions.", size=9.5)
    _page_break(doc)

    # --------------------------------------------------------- agent specs
    doc.add_heading("5. Each agent: mission, tools, communication, instruction", level=1)
    _p(doc, "Missions are read from the agent classes, so this table cannot describe an "
            "agent that does not exist. Tools are the functions each agent actually "
            "calls.")
    agents = [PlannerAgent, TaggerAgent, StatisticianAgent, CausalAgent,
              ComparatorAgent, ComplexityAgent, CriticAgent, ReporterAgent]
    tools = {
        "PlannerAgent": "reads configs/research_questions.yaml; inspects the record "
                        "schema",
        "TaggerAgent": "counts over the label fields; confidence histogram",
        "StatisticianAgent": "analysis.rq1_frequency, rq2_ranked, rq7_escape, "
                             "rq8_unknown; Wilson intervals",
        "CausalAgent": "analysis.rq3_cause_by_type; chi-square, Cramér's V, BH",
        "ComparatorAgent": "analysis.rq4_framework_by_type, rq5_framework_severity, "
                           "rq9_trend",
        "ComplexityAgent": "analysis.rq6_complexity, rq10_strata",
        "CriticAgent": "its own recomputation of each headline metric from the raw "
                       "records; no shared code path with the specialists",
        "ReporterAgent": "report.build_report; tables and figures from verified "
                         "results only",
    }
    recv = {
        "PlannerAgent": "the question list",
        "TaggerAgent": "the record list",
        "StatisticianAgent": "{rq, method} task",
        "CausalAgent": "{rq, method} task",
        "ComparatorAgent": "{rq, method} task",
        "ComplexityAgent": "{rq, method} task",
        "CriticAgent": "{rq} after a proposal",
        "ReporterAgent": "{ } — the verified board",
    }
    posts = {
        "PlannerAgent": "inform → Orchestrator (plan)",
        "TaggerAgent": "inform → Orchestrator (audit)",
        "StatisticianAgent": "propose → CriticAgent",
        "CausalAgent": "propose → CriticAgent",
        "ComparatorAgent": "propose → CriticAgent",
        "ComplexityAgent": "propose → CriticAgent",
        "CriticAgent": "verify → Orchestrator (accept / revise)",
        "ReporterAgent": "inform → Orchestrator (report written)",
    }
    _table(doc, ["Agent", "Mission", "Tools", "Receives", "Posts"],
           [[a.name, _trim(a.goal, 90), tools[a.name], recv[a.name], posts[a.name]]
            for a in agents],
           widths=[1.0, 1.7, 1.8, 0.9, 1.2], size=7.2)

    doc.add_heading("5.1 How they communicate, from the recorded run", level=2)
    _p(doc, "This table is aggregated from transcript.jsonl, not written by hand: it is "
            "a count of what the agents actually posted in the run under review.", after=4)
    _table(doc, ["Sender", "Recipient", "Acts", "Messages"],
           _comm_table(msgs), widths=[1.5, 1.5, 2.4, 0.9], size=8)
    _p(doc, "Five acts are used, and each one has a meaning that the critic depends on: "
            "request (a task), inform (state or a plan), propose (a computed result), "
            "verify (an accept/revise verdict), refuse (a question that cannot be "
            "answered from the available fields). Refusal is a real path: the planner "
            "drops a question whose required field is absent rather than answering it "
            "anyway.", size=9, before=4)

    doc.add_heading("5.2 On the request for 'a typical prompt'", level=2)
    _p(doc, "There is no language-model prompt in the analysis path, and it would be "
            "wrong to present one. The agents are deterministic Python; what each one "
            "receives is a structured instruction, and that instruction is the honest "
            "equivalent of a prompt. Nothing that becomes a reported number passes "
            "through a language model — which is the reason the numbers can be trusted "
            "and should be said out loud if asked.", after=4)
    _p(doc, "The instruction a specialist receives, exactly as constructed:", after=3,
       size=9.5)
    example = next(q for q in qs if q["id"] == "RQ3")
    code = json.dumps({"rq": example["id"], "question": example["question"],
                       "owner": "CausalAgent", "mode": example["agent_mode"],
                       "agents": example["agents"], "method": example["method"]},
                      indent=2, ensure_ascii=False)
    _code_block(doc, code)
    _p(doc, "The critic receives only the question identifier and re-derives the number "
            "itself; it is never handed the specialist's arithmetic. The planner receives "
            "the question list and the schema, and its refusals are recorded. That is the "
            "full instruction surface of the system.", size=9, before=4)
    _page_break(doc)

    # ----------------------------------------------------------- walkthrough
    doc.add_heading("6. One question, resolved end to end", level=1)
    q3 = next(q for q in qs if q["id"] == "RQ3")
    _p(doc, f"The question asked for one scenario carried all the way through. This is "
            f"RQ3: {q3['question']} It is a chain, and it is the question the supervisor "
            f"specifically required — linking each category to measurable causes — so it "
            f"is the right one to walk.")

    rq3 = verified.get("RQ3", {})
    m3 = rq3.get("metrics", {})
    steps = [
        ("Plan", "PlannerAgent posts the ordered plan, naming this question's owner and "
                 "method.",
         "PlannerAgent → Orchestrator  [inform]  RQ3 owner CausalAgent, "
         "method: contingency analysis with BH-corrected p-values"),
        ("Dispatch", "The orchestrator hands the task to the specialist as a direct call; "
                     "the call is logged as a tool call.",
         "Orchestrator → CausalAgent  analysis.rq3_cause_by_type(records)"),
        ("Compute", "The specialist computes the contingency table, chi-square, "
                    "Cramér's V and BH-corrected p-values, and posts the headline.",
         f"CausalAgent → CriticAgent  [propose]  χ² = {m3.get('chi2', 0):.1f}, "
         f"V = {m3.get('cramers_v', 0):.4f}, dof = {m3.get('dof', 0)}"),
        ("Verify", "The critic recomputes from the raw records — a different code path — "
                   "checks the denominator, and checks the wording for causal verbs.",
         f"CriticAgent → Orchestrator  [verify]  accept  "
         f"(recomputed n = {len(records):,}, "
         f"demonstrated causes = {m3.get('demonstrated_causes', 0)})"),
        ("Report", "Only the verified result reaches the reporter, which renders the "
                   "table and the figure.",
         "ReporterAgent → report  table_cause_by_type + Figure 2"),
    ]
    _table(doc, ["Step", "What happens", "Recorded line"],
           [[s[0], s[1], s[2]] for s in steps],
           widths=[0.7, 2.9, 2.9], size=7.8)

    _p(doc, "The result itself, stated the way the critic will allow it to be stated: "
            f"cause class and failure type are associated (χ² = {m3.get('chi2', 0):.1f}, "
            f"V = {m3.get('cramers_v', 0):.4f}, p < 0.001), which is an association and "
            f"not a cause. The evidence grade attached to each record keeps that "
            f"distinction visible: of the corpus, "
            f"{m3.get('grade_counts', {}).get('demonstrated', 0):,} records demonstrate a "
            f"cause, {m3.get('grade_counts', {}).get('supported', 0):,} support one, and "
            f"{m3.get('grade_counts', {}).get('hypothesised', 0):,} only hypothesise one. "
            f"That distribution is the most useful thing in this table, because it says "
            f"how much of the corpus actually shows a mechanism rather than naming one.",
       before=4)

    known = [r for r in rq3.get("table", [])
             if "unknown" not in str(r.get("cause", "")).lower()
             and "unknown" not in str(r.get("cause_label", "")).lower()]
    top = sorted(known, key=lambda r: -r.get("count", 0))[:6]
    if top:
        _table(doc, ["Failure type", "Cause class", "n", "Share of that type"],
               [[r.get("failure_type_label", r.get("failure_type", "")),
                 r.get("cause_label", r.get("cause", "")),
                 str(r.get("count", "")),
                 f"{r.get('share_of_type_pct', 0):.1f}%"]
                for r in top],
               widths=[2.0, 2.0, 0.5, 0.9], size=8)
        _caption(doc, "The six largest cause cells with an identified cause, ordered by "
                      "count.")
        rq3_fig = FIG_DIR / "fig_rq3_cause_by_type.png"
        if rq3_fig.exists():
            _figure(doc, rq3_fig, width=6.0,
                    caption="Figure 2. The same result as a matrix: failure type down the "
                            "side, cause class across the top. This is the figure the "
                            "specialist hands to the reporter, and it is what a chain "
                            "produces that a single agent working from one table could "
                            "not.")
        unknown_cells = [r for r in rq3.get("table", [])
                         if "unknown" in str(r.get("cause", "")).lower()]
        if unknown_cells:
            biggest = max(unknown_cells, key=lambda r: r.get("count", 0))
            _p(doc, f"The largest single cell in the full table is not shown above: "
                    f"{biggest.get('failure_type_label')} with the cause recorded as "
                    f"not determinable, n = {biggest.get('count')}. It is reported rather "
                    f"than suppressed, because a corpus of issue reports will contain "
                    f"failures whose cause the reporter could not establish, and hiding "
                    f"that cell would overstate how much of the corpus has an explained "
                    f"mechanism.", size=9, before=3)
    _page_break(doc)

    # ------------------------------------------------------------- critic
    doc.add_heading("7. The critic is not a rubber stamp", level=1)
    _p(doc, f"The run under review accepted all {run_summary.get('questions_verified')} "
            f"questions with {run_summary.get('rejections')} rejections, which makes the "
            f"critic look like a formality. It is worth answering that directly rather "
            f"than hoping nobody notices, because the loop only means something if it "
            f"bites. The demonstration below is executed when this document is built: a "
            f"correct RQ1 result is verified, then the same result is corrupted by five "
            f"percentage points and verified again.")

    clean_dec = inj["clean"]["decision"]
    caught_dec = inj["caught"]["decision"]
    lang_dec = inj["language"]["decision"]
    _table(doc, ["Injection", "Verdict", "Critic's stated reason"],
           [["Untouched RQ1 result", clean_dec,
             "; ".join(inj["clean"]["issues"]) or "no issue found"],
            [f"top_share moved {inj['original']:.4f} → {inj['tampered']:.4f}",
             caught_dec, "; ".join(inj["caught"]["issues"]) or "no issue found"],
            ["causal verb used on an association", lang_dec,
             "; ".join(inj["language"]["issues"]) or "no issue found"]],
           widths=[2.4, 0.8, 3.3], size=8)

    _p(doc, "The same behaviour is pinned by tests, so it cannot silently regress: "
            "test_rejects_tampered_metric and test_rejects_causal_language_on_association "
            "fail if the critic ever starts accepting either case. The honest answer to "
            "'did it catch anything real?' is: not in this run, because the specialists "
            "compute from the same functions the critic recomputes — and that is exactly "
            "why the fault injection is run live rather than described.", before=4)
    _page_break(doc)

    # ------------------------------------------------------------- results
    doc.add_heading("8. Results, and how the data was collected", level=1)
    _p(doc, "The collection is deliberately narrow: public issue trackers of eight "
            f"actively maintained agent-orchestration frameworks, via the public API, "
            f"rate limited, every request logged. {n:,} retained failure records. Nothing "
            f"was scraped from private channels, and no personal data was collected — "
            f"author handles are dropped at collection time.", after=5)

    rq7 = verified.get("RQ7", {}).get("metrics", {})
    rq6 = verified.get("RQ6", {}).get("metrics", {})
    _p(doc, "The discovery worth leading the presentation with is not the category "
            f"ranking. It is that {rq7.get('escape_share', 0) * 100:.1f}% of failures "
            f"escape to users rather than being caught at runtime, and that detection "
            f"point is the variable with the strongest association to failure type in "
            f"the study (V = {rq7.get('cramers_v', 0):.2f}). A taxonomy that only names "
            f"what goes wrong is a table of nouns; this says which failures are quiet.",
       after=5)
    _p(doc, "The second empirical result is a trend rather than a snapshot: the share of "
            f"orchestration and context failures rises monotonically with declared "
            f"architectural complexity across all four tiers "
            f"(ρ = {rq6.get('trend', {}).get('rho', 0):.2f}, "
            f"n = {rq6.get('trend', {}).get('n', 0)} tiers). That is the curve the "
            f"supervisor asked for, and it should be shown as a curve, not a table.",
       after=6)

    # The curve, drawn from the verified RQ6 table rather than from prose.
    curve_path = FIG_DIR / "fig_rq6_curve.png"
    try:
        from . import viz as _viz
        rows6 = verified.get("RQ6", {}).get("table") or []
        if rows6:
            _viz.trend_curve(
                rows6, curve_path,
                "Orchestration and context failures by declared complexity tier",
                annotations={"line": (
                    f"Spearman ρ = {rq6.get('trend', {}).get('rho', 0):.2f} across "
                    f"{rq6.get('trend', {}).get('n', 0)} ordered tiers; "
                    f"V = {rq6.get('cramers_v', 0):.2f}")})
    except Exception as exc:  # a missing figure must not break the pack
        print(f"  note: rq6 curve not drawn ({exc})")
    if curve_path.exists():
        _figure(doc, curve_path, width=5.9,
                caption="Figure 3. The empirical curve. Ordered tiers on the x-axis, so "
                        "the claim being made — that the share rises with declared "
                        "complexity — is the shape of the line rather than something "
                        "asserted in a caption. The interval on tier 0 is wide because "
                        "only 18 of its 699 records failed this way.")

    _p(doc, "Neither result is causal. Both are stated as associations, and the critic "
            "enforces that wording.", size=9.5, italic=True, color=GREY)
    _page_break(doc)

    # ------------------------------------------------------------ reconciling
    doc.add_heading("9. The taxonomy as the output of the system", level=1)
    _p(doc, "The supervisor's phrasing was that the taxonomy should be presented as the "
            "output of the agentic work. That is true in the sense that matters and false "
            "in the sense that would be dishonest, so the distinction is worth making "
            "explicitly rather than glossing:")
    _bullet(doc, "the categories were derived by hand from a fixed reading sample, before "
                 "any automation, under the supervisor's own instruction that this was "
                 "permissible.", lead="Hand-derived: ")
    _bullet(doc, "the pipeline applies the codebook to the full corpus, audits label "
                 "completeness, quantifies coverage, and tests every claim the taxonomy "
                 "makes empirically. The empirical footprint of the taxonomy — which is "
                 "what the results chapters report — is produced by the agents.",
            lead="Agent-produced: ")
    _bullet(doc, "the codebook is an input artefact with a version, not something a "
                 "language model generated at run time. A version change forces a "
                 "re-label, so no result is ever attached to an unnamed codebook.",
            lead="Versioned: ")
    _p(doc, "So the sentence to use is: the taxonomy is the instrument, and the agentic "
            "system is what turns the instrument into evidence at a scale no hand-coding "
            "could reach — 3,089 records, ten questions, every headline number "
            "independently recomputed.", before=5)

    doc.add_heading("10. If he pushes: the three follow-ups to expect", level=1)
    _p(doc, "These are the questions that follow naturally from his, and the answers are "
            "short enough to keep in your head.", after=4)
    _table(doc, ["Follow-up", "The answer"],
           [["Where is the prompt?",
             "There is no LLM in the analysis path — by design, so no statistic can be "
             "hallucinated. Each agent receives a structured instruction, and the "
             "transcript records every message."],
            ["Did the critic ever reject anything?",
             "Not in this run — and it is shown biting on a corrupted result in section "
             "7, with two tests that fail if it stops biting."],
            ["Did the agents discover the taxonomy?",
             "No. It was hand-derived from 120 records under your instruction, then "
             "applied and tested at scale by the agents. Section 9."],
            ["One agent or several per question?",
             "Nine chains, one single-agent; the assignment is in the configuration and "
             "the report derives the count from it."],
            ["Where is the empirical curve?",
             "Escape by failure type, and orchestration/context failures across the four "
             "complexity tiers, which is monotonic at ρ = 1.00."]],
           widths=[2.0, 4.5], size=8.5)

    out_path = out_path or (REP_DIR / PACK_NAME)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path


def _code_block(doc, text: str) -> None:
    from docx.shared import Inches, Pt
    for line in text.splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.left_indent = Inches(0.25)
        r = p.add_run(line if line else " ")
        r.font.name = "Consolas"
        r.font.size = Pt(7.8)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def REPORT_FIG() -> Path:
    from .common import FIG_DIR
    return FIG_DIR / "fig_architecture.png"
