#!/usr/bin/env python3
"""Build the assignment submission PDF.

Uses the original report text verbatim, adds measured SYSTEMS.md experiment
results, then appends all /chats transcripts with distinct user styling.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Image,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = Path(__file__).resolve().parent / "results"
CHATS = Path(__file__).resolve().parent / "chats_parsed"
OUT_DIR = ROOT / "report"
ASSETS = RESULTS / "plots"

# Visual system — cool ink on warm paper-adjacent gray-blue (not purple / cream / terracotta)
INK = colors.HexColor("#1A2332")
MUTED = colors.HexColor("#5A6575")
RULE = colors.HexColor("#C5CCD6")
ACCENT = colors.HexColor("#0B6E6E")  # deep teal for YOU
USER_BG = colors.HexColor("#E6F2F2")
ASSIST_INK = colors.HexColor("#243040")
BAND = colors.HexColor("#F2F5F8")
WHITE = colors.white


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\u0000", "")
    )


def nl2br(s: str) -> str:
    return esc(s).replace("\n", "<br/>")


def make_styles():
    base = getSampleStyleSheet()
    styles = {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=ACCENT,
            letterSpacing=1.2,
            spaceAfter=10,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=26,
            leading=30,
            textColor=INK,
            spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=MUTED,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Times-Bold",
            fontSize=16,
            leading=20,
            textColor=INK,
            spaceBefore=18,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Times-Bold",
            fontSize=13,
            leading=16,
            textColor=INK,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=ACCENT,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10.5,
            leading=15,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "quote": ParagraphStyle(
            "quote",
            parent=base["Normal"],
            fontName="Times-Italic",
            fontSize=11,
            leading=15,
            textColor=INK,
            leftIndent=18,
            rightIndent=12,
            spaceBefore=8,
            spaceAfter=10,
            borderPadding=6,
        ),
        "note": ParagraphStyle(
            "note",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=MUTED,
            leftIndent=10,
            spaceAfter=6,
        ),
        "meta": ParagraphStyle(
            "meta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=MUTED,
            spaceAfter=4,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "table_head",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=INK,
        ),
        "user_label": ParagraphStyle(
            "user_label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=ACCENT,
            spaceBefore=10,
            spaceAfter=3,
        ),
        "user_body": ParagraphStyle(
            "user_body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12.5,
            textColor=colors.HexColor("#0A4F4F"),
            backColor=USER_BG,
            borderPadding=8,
            spaceAfter=8,
        ),
        "claude_label": ParagraphStyle(
            "claude_label",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            spaceBefore=8,
            spaceAfter=3,
        ),
        "claude_body": ParagraphStyle(
            "claude_body",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=9,
            leading=12.5,
            textColor=ASSIST_INK,
            spaceAfter=8,
        ),
        "chat_title": ParagraphStyle(
            "chat_title",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=14,
            leading=18,
            textColor=INK,
            spaceBefore=6,
            spaceAfter=8,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }
    return styles


ORIGINAL_REPORT = {
    "problem_statement": """I am framing the assignment inside a specific business context, because it is only safe to
switch into engineering mode once you understand that context — who is paying for the
model usage, who all the stakeholders are, and where the real pain points sit.

For the sake of efficient communication, let me frame it as a story.

Isaac is a physics professor. Every year he helps write the problems and worked solutions
for the International Physics Olympiad, the world championship for high-school physicists.

Writing them by hand is slow and costly, so his team is building an AI pipeline to draft each
problem and its solution. But no solution can be trusted until something checks that it is
actually correct. That check is another AI system, and every call costs money.

I am framing this assignment as an experimentation phase before sitting down with Isaac, so
that when we talk, I can discuss cost in concrete terms.

My goal going in is to already know the levers: which shortcuts make verification cheaper,
and how much accuracy each one costs

Then when a grader tells me one step is critical, I can weigh it on the spot — spend more
and give that step its own dedicated AI check, or save money where accuracy matters less.

Because I will have already measured the cost and the quality of some of the shortcuts.

Let’s get to precisely defining what we’re solving for.

Concretely, the problem I'm solving is this:""",
    "problem_box": """Given the workload of verifying IPhO-level physics solutions, design an
inference-time execution system that cuts cost-per-verification by 50% versus a
strong single-frontier-model baseline, while catching bad solutions at least as reliably
as that baseline.""",
    "problem_cont": """This is a faithful reading of the assignment, as the brief asks for an "AI execution system"
that reduces "inference costs" — and its own vocabulary (workload, application, model
family, infrastructure layer, combination of techniques) signals that "inference" is meant
broadly: the cost of running a pipeline to produce an output, not one model's forward pass.
So I read inference cost as dollars per solution verified, summed across every model and
tool call the system makes.

The statement also pins down the two things a percentage claim needs to be credible. It
fixes a reference point — a strong single-frontier-model baseline, the kind a competent
engineer would actually ship— and it treats "equal quality" as a floor rather than a goal: the
cheap system has to catch bad solutions at least as reliably as that baseline, so any savings
I report are savings at held-constant quality. What it deliberately leaves open is how. It
names no cascade, no router, no caching scheme, because the assignment is open-ended
on technique and the honest version of this work lets the evidence decide which levers pay
off. That keeps the definition of the problem separable from the solution to it — which, given
the story above, is the whole point: I want to walk into the conversation with Isaac
already knowing what each shortcut costs and what it buys.""",
    "notes": [
        "The verifier system isn’t necessarily a realtime system, it’s a system you run periodically, so whenever talking to LLM should use Batch API to send multiple reqs together instead of one -> this alone yields 50% cost savings w/ certain models",
    ],
}


def plot_costs(summary: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq = summary["cost_quality_by_system"]
    systems = ["S3", "S2", "S1"]
    costs = [cq[s]["mean_cost_usd"] for s in systems]
    est = [summary["systems_md_estimates"][s] for s in systems]

    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=160)
    fig.patch.set_facecolor("#F2F5F8")
    ax.set_facecolor("#F2F5F8")
    x = range(len(systems))
    w = 0.36
    ax.bar([i - w / 2 for i in x], est, width=w, color="#9AA7B5", label="SYSTEMS.md estimate")
    ax.bar([i + w / 2 for i in x], costs, width=w, color="#0B6E6E", label="Measured (2023 pair)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(systems)
    ax.set_ylabel("USD per solution verified")
    ax.set_title("Cost ladder: estimate vs measured")
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, c in enumerate(costs):
        ax.text(i + w / 2, c + 0.01, f"${c:.2f}", ha="center", va="bottom", fontsize=8, color="#1A2332")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def para_blocks(text: str, style) -> list:
    blocks = []
    for chunk in re.split(r"\n\s*\n", text.strip()):
        chunk = re.sub(r"\s*\n\s*", " ", chunk.strip())
        if chunk:
            blocks.append(Paragraph(esc(chunk), style))
    return blocks


def styled_table(headers, rows, styles, col_widths=None):
    data = [[Paragraph(esc(h), styles["table_head"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(esc(str(c)), styles["table_cell"]) for c in row])
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BAND),
                ("TEXTCOLOR", (0, 0), (-1, -1), INK),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
                ("LINEBELOW", (0, 1), (-1, -2), 0.3, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
            ]
        )
    )
    return t


def add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(0.75 * inch, LETTER[1] - 0.55 * inch, LETTER[0] - 0.75 * inch, LETTER[1] - 0.55 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.75 * inch, LETTER[1] - 0.45 * inch, "IPhO verifier — cost/quality assignment")
    canvas.drawRightString(LETTER[0] - 0.75 * inch, LETTER[1] - 0.45 * inch, "submission report")
    canvas.line(0.75 * inch, 0.55 * inch, LETTER[0] - 0.75 * inch, 0.55 * inch)
    canvas.drawCentredString(LETTER[0] / 2, 0.38 * inch, f"{doc.page}")
    canvas.restoreState()


def build_chat_flow(chat: dict, styles) -> list:
    flow = []
    flow.append(Paragraph(esc(f"Chat {chat['id']} — {chat['title']}"), styles["chat_title"]))
    src = chat.get("source", "")
    model = chat.get("model") or ""
    flow.append(Paragraph(esc(f"Source: /chats/{src}" + (f" · model {model}" if model else "")), styles["meta"]))
    flow.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceAfter=8))

    for msg in chat["messages"]:
        text = msg["text"]
        # Soft-trim absurd skill dumps if any slipped through
        if len(text) > 60000:
            text = text[:60000] + "\n\n[truncated for PDF length]"
        if msg["role"] == "user":
            flow.append(Paragraph("<b>YOU</b>", styles["user_label"]))
            # Split long user messages into paragraphs for readability
            for chunk in re.split(r"\n\s*\n", text.strip()) or [text]:
                chunk = chunk.strip()
                if not chunk:
                    continue
                flow.append(Paragraph(nl2br(chunk), styles["user_body"]))
        else:
            flow.append(Paragraph("Claude", styles["claude_label"]))
            for chunk in re.split(r"\n\s*\n", text.strip()) or [text]:
                chunk = chunk.strip()
                if not chunk:
                    continue
                # Keep markdown-ish headings readable without full md render
                chunk = re.sub(r"^#{1,6}\s*", "", chunk, flags=re.M)
                flow.append(Paragraph(nl2br(chunk), styles["claude_body"]))
    flow.append(PageBreak())
    return flow


def build() -> Path:
    styles = make_styles()
    summary = json.loads((RESULTS / "summary.json").read_text())
    spend = summary["spend"]
    cq = summary["cost_quality_by_system"]
    arm = summary["sol_vs_terra_arm"]
    ingestion = summary["ingestion"]

    plot_path = ASSETS / "cost_ladder.png"
    plot_costs(summary, plot_path)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "SUBMISSION_REPORT.pdf"

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="IPhO Verifier — Assignment Submission Report",
        author="Ismail Brkic",
    )

    story: list = []

    # Cover / original problem statement
    story.append(Paragraph("ASSIGNMENT SUBMISSION", styles["cover_kicker"]))
    story.append(Paragraph("Cutting verification cost in half<br/>without losing error-catching quality", styles["cover_title"]))
    story.append(
        Paragraph(
            "Workload: verifying IPhO-mechanics reference solutions · Evidence: measured OpenAI runs on the 2023 Water-and-Objects clean/faulty pair · Hard spend cap: $25 (actual: $%.2f)"
            % spend["spent_usd"],
            styles["cover_sub"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=14))

    story.append(Paragraph("PROBLEM STATEMENT", styles["h1"]))
    story.extend(para_blocks(ORIGINAL_REPORT["problem_statement"], styles["body"]))
    story.append(Paragraph(nl2br(ORIGINAL_REPORT["problem_box"]), styles["quote"]))
    story.extend(para_blocks(ORIGINAL_REPORT["problem_cont"], styles["body"]))

    story.append(Paragraph("NOTES", styles["h2"]))
    for n in ORIGINAL_REPORT["notes"]:
        story.append(Paragraph("• " + esc(n), styles["note"]))

    story.append(PageBreak())

    # Experiment results
    story.append(Paragraph("EXPERIMENT RESULTS", styles["h1"]))
    story.append(
        Paragraph(
            "Executed the first measurement plan in <font face='Courier'>verifier_experiments/SYSTEMS.md</font> "
            "on exactly two solution PDFs — the official 2023 S3 and the deliberately faulty twin — "
            "plus the matching problem statement Q3. The 2021 held-out pair was not used.",
            styles["body"],
        )
    )

    story.append(Paragraph("Corpus &amp; labels", styles["h2"]))
    story.append(
        styled_table(
            ["Role", "File", "Expected verdict"],
            [
                ["Clean (must PASS)", "IPhO_2023_S3.pdf", "ACCEPT"],
                ["Faulty (must FAIL)", "IPhO_2023_S3_FAULTY.pdf", "REJECT"],
                ["Problem P", "IPhO_2023_Q3.pdf", "—"],
            ],
            styles,
            col_widths=[1.6 * inch, 3.2 * inch, 1.5 * inch],
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Injected faults on the faulty PDF (from <font face='Courier'>INJECTED_ERRORS.md</font>): "
            "ERR-1 A.1 dimensionless geometric factor · ERR-2 B.3 sign flip · ERR-3 B.4 dimensional "
            "inconsistency · ERR-4 B.5 wrong root branch · ERR-5 C.2 symbol-whitelist violation.",
            styles["body"],
        )
    )

    story.append(Paragraph("Spend", styles["h2"]))
    story.append(
        Paragraph(
            f"Hard cap <b>${spend['hard_cap_usd']:.2f}</b>. Actual OpenAI spend "
            f"<b>${spend['spent_usd']:.4f}</b> across {spend['n_calls']} calls "
            f"({spend['input_tokens']:,} input / {spend['cached_tokens']:,} cached / "
            f"{spend['output_tokens']:,} output tokens, including {spend['reasoning_tokens']:,} reasoning). "
            "Costs are from logged usage × pinned prices in <font face='Courier'>prices.json</font>. "
            "S1 judge costs are reported with the Batch API 50% discount applied (SYSTEMS.md §4).",
            styles["body"],
        )
    )

    story.append(Paragraph("1. Ingestion experiment (settles SYSTEMS.md §1)", styles["h2"]))
    story.append(
        Paragraph(
            f"I4 (<font face='Courier'>gpt-5.6-terra</font> vision → typed IR) mean cost per 5-page solution PDF: "
            f"<b>${ingestion['i4_mean_cost_usd']:.4f}</b> "
            f"(total ${ingestion['i4_total_cost_usd']:.4f} for clean+faulty; 0 retries on both). "
            f"I2 (<font face='Courier'>gpt-5.4-mini</font>) was ~${sum(ingestion['i2_costs'].values())/2:.4f} mean. "
            "Prior in SYSTEMS.md (~$0.28 I4) was high — measured I4 is cheaper, so the §4 system totals "
            "should shift downward mainly with the judge/escalation tiers, not ingestion.",
            styles["body"],
        )
    )

    story.append(Paragraph("2. sol vs terra escalation arm (settles SYSTEMS.md §0)", styles["h2"]))
    story.append(
        Paragraph(
            "On faulty A.1 (ERR-1, the dimensionless geometric factor), both "
            "<font face='Courier'>gpt-5.6-terra</font> and <font face='Courier'>gpt-5.6-sol</font> "
            "escalation agents returned <b>FAIL</b> with the same root cause "
            "(area factor 2^(1/3) instead of 2^(2/3)). "
            f"Costs: terra ${arm['gpt-5.6-terra']['cost_usd']:.4f}, sol ${arm['gpt-5.6-sol']['cost_usd']:.4f}. "
            "On this fault, the ~2× sol premium bought no additional catch — supporting the SYSTEMS.md bet "
            "to keep escalation on terra.",
            styles["body"],
        )
    )

    story.append(Paragraph("3. S3 / S2 / S1 on the matched pair", styles["h2"]))
    story.append(Image(str(plot_path), width=6.4 * inch, height=3.2 * inch))
    story.append(Spacer(1, 6))

    rows = []
    for sys in ("S3", "S2", "S1"):
        r = cq[sys]
        rows.append(
            [
                sys,
                f"${r['mean_cost_usd']:.4f}",
                f"{r['savings_vs_S3']*100:.1f}%" if sys != "S3" else "baseline",
                "ACCEPT ✓" if r["clean_accept_ok"] else "FAIL",
                f"REJECT · {r['faults_caught']}/5",
                f"{r['mean_escalation_rate']*100:.0f}%",
            ]
        )
    story.append(
        styled_table(
            ["System", "Mean $/sol", "vs S3", "Clean", "Faulty faults", "Escalation"],
            rows,
            styles,
            col_widths=[0.7 * inch, 1.0 * inch, 0.9 * inch, 1.0 * inch, 1.3 * inch, 1.0 * inch],
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "<b>Quality.</b> Every system accepted the clean official solution (false-reject = 0) and "
            "rejected the faulty twin while localizing all five injected faults (false-accept = 0 on this pair). "
            "Deterministic Tier-0/1 alone caught ERR-2/3/4/5; ERR-1 required the LLM judge/escalation path, "
            "exactly as DEFINITION.MD §6 predicted.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>Cost.</b> Measured S2 is <b>53% cheaper</b> than S3 at equal catch rate on this pair — "
            "the assignment’s 50% target, taken as S3→S2, holds without quality loss here. "
            "S1 is 86% cheaper than S3, but SYSTEMS.md flags it as eating the expert residue; "
            "on this small labeled pair it still caught ERR-1 in the bulk luna judge, which should "
            "not be over-generalized (N=2 documents).",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>Where faults were caught (S3 faulty).</b> ERR-1→escalation; ERR-2/3/4/5→deterministic. "
            "Mean escalation rate: S3 33% of sub-parts, S2 17%, S1 0%. "
            "That matches the SYSTEMS.md claim that escalation rate — not bulk model choice — dominates cost.",
            styles["body"],
        )
    )

    story.append(Paragraph("Threats to validity", styles["h2"]))
    story.append(
        Paragraph(
            "• N=2 solution documents (one clean, one with five known faults); this is an existence proof of the "
            "mechanism on the primary eval pair, not a population statistic.<br/>"
            "• Deterministic checkers are problem-structure-aware for 2023 Water-and-Objects; they are not yet a "
            "general IR→SymPy layer.<br/>"
            "• Verification judges used I1 text extraction for the cascade runs; I4 vision cost was measured "
            "separately so the open ingestion question is answered without double-billing vision into every system.<br/>"
            "• S1 Batch discount is applied in accounting; calls themselves were synchronous.",
            styles["note"],
        )
    )

    story.append(Paragraph("Artifacts", styles["h2"]))
    story.append(
        Paragraph(
            "Raw per-run JSON, API call log, and summary: "
            "<font face='Courier'>verifier_experiments/systems_bench/results/</font>. "
            "Harness: <font face='Courier'>verifier_experiments/systems_bench/</font>. "
            "Design docs: <font face='Courier'>SYSTEMS.md</font>, <font face='Courier'>DEFINITION.MD</font>, "
            "<font face='Courier'>INJECTED_ERRORS.md</font>.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # AI use record / chats
    story.append(Paragraph("AI-USE RECORD — FULL CHATS", styles["h1"]))
    story.append(
        Paragraph(
            "Below are the assignment-related chat transcripts from <font face='Courier'>/chats</font>. "
            "<font color='#0B6E6E'><b>YOU</b></font> (the human) appears in teal, lightly emphasized. "
            "Claude appears in regular body text. Tool-only / skill-dump noise was stripped; conversational "
            "content is otherwise complete.",
            styles["body"],
        )
    )
    story.append(Spacer(1, 6))

    # Preferred order: framing (3), designing experiments (1), correctness (2), error PDFs (4)
    order = ["3", "1", "2", "4"]
    for cid in order:
        path = CHATS / f"chat_{cid}.json"
        if not path.exists():
            continue
        chat = json.loads(path.read_text())
        story.extend(build_chat_flow(chat, styles))

    # If last element is PageBreak, drop it
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return out_path


if __name__ == "__main__":
    p = build()
    print("Wrote", p, "size", p.stat().st_size)
