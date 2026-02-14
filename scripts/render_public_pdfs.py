from __future__ import annotations

from pathlib import Path
import textwrap

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_RELEASE = REPO_ROOT / "public_release"
PUBLIC_EXPORTS = PUBLIC_RELEASE / "exports"
PUBLIC_DOCS = PUBLIC_RELEASE / "docs"

MEMO_MD = REPO_ROOT / "docs" / "DECISION_MEMO_1PAGE.md"
CASE_MD = REPO_ROOT / "case_study_readme.md"
STORY_IMAGES = [
    REPO_ROOT / "public_demo" / "story_chart_1.png",
    REPO_ROOT / "public_demo" / "story_chart_2.png",
    REPO_ROOT / "public_demo" / "story_chart_3.png",
]

OUT_STORY_PDF = PUBLIC_EXPORTS / "cohort_retention_story.pdf"
OUT_MEMO_PDF = PUBLIC_DOCS / "DECISION_MEMO_1PAGE.pdf"
OUT_CASE_PDF = PUBLIC_RELEASE / "case_study_readme.pdf"


def to_rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def sanitize_line(line: str) -> str:
    return (
        line.replace("≥", ">=")
        .replace("Δ", "Delta")
        .replace("≈", "~=")
        .replace("·", "-")
        .replace("—", "-")
        .replace("–", "-")
    )


def markdown_to_lines(md_text: str) -> list[str]:
    lines: list[str] = []
    for raw in md_text.splitlines():
        line = sanitize_line(raw.rstrip())
        if line.startswith("# "):
            lines.append("")
            lines.append(line[2:].strip().upper())
            lines.append("")
        elif line.startswith("## "):
            lines.append("")
            lines.append(line[3:].strip())
            lines.append("")
        elif line.startswith("### "):
            lines.append("")
            lines.append(line[4:].strip())
        elif line.startswith("- "):
            lines.append(f"* {line[2:].strip()}")
        elif line.startswith("|"):
            lines.append(line)
        else:
            lines.append(line)
    return lines


def draw_wrapped_text(pdf: canvas.Canvas, lines: list[str], top_y: float) -> None:
    width, height = LETTER
    left = 54
    right = width - 54
    y = top_y

    pdf.setFont("Helvetica", 10)
    for line in lines:
        wrap_width = 105
        if line.startswith("|"):
            wrap_width = 120
        chunks = textwrap.wrap(line, width=wrap_width) if line else [""]
        for chunk in chunks:
            if y < 54:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 54
            pdf.drawString(left, y, chunk)
            y -= 13
        if right < left:
            break


def render_text_pdf(source_md: Path, out_pdf: Path, title: str) -> None:
    if not source_md.exists():
        raise FileNotFoundError(f"Missing source markdown: {source_md}")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    text = source_md.read_text(encoding="utf-8", errors="ignore")
    lines = markdown_to_lines(text)

    pdf = canvas.Canvas(str(out_pdf), pagesize=LETTER)
    width, height = LETTER
    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(54, height - 48, title)
    draw_wrapped_text(pdf, lines, top_y=height - 72)
    pdf.save()


def render_story_pdf(out_pdf: Path) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    for image_path in STORY_IMAGES:
        if not image_path.exists():
            raise FileNotFoundError(f"Missing story screenshot: {image_path}")

    captions = [
        "Chart 1: Cohort heatmap (logo retention)",
        "Chart 2: Net retention proxy curves (3 cohorts max)",
        "Chart 3: M2 retention by first product family",
    ]

    pdf = canvas.Canvas(str(out_pdf), pagesize=LETTER)
    width, height = LETTER
    pdf.setTitle("Cohort Retention Story Snapshot")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(54, height - 48, "Cohort Retention Story Snapshot")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(54, height - 64, "Public-safe PDF built from story screenshots (diagnostic baseline).")

    for idx, image_path in enumerate(STORY_IMAGES):
        if idx > 0:
            pdf.showPage()
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(54, height - 48, captions[idx])

        image = ImageReader(str(image_path))
        img_w, img_h = image.getSize()
        max_w = width - 108
        max_h = height - 150
        scale = min(max_w / img_w, max_h / img_h)
        draw_w = img_w * scale
        draw_h = img_h * scale
        x = (width - draw_w) / 2
        y = (height - 90 - draw_h)
        pdf.drawImage(image, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True, anchor="c")

        pdf.setFont("Helvetica", 10)
        pdf.drawString(54, 36, f"Source image: {to_rel(image_path)}")

    pdf.save()


def main() -> None:
    render_story_pdf(OUT_STORY_PDF)
    render_text_pdf(MEMO_MD, OUT_MEMO_PDF, "Decision Memo (PDF)")
    render_text_pdf(CASE_MD, OUT_CASE_PDF, "Case Study Narrative (PDF)")

    outputs = [OUT_STORY_PDF, OUT_MEMO_PDF, OUT_CASE_PDF]
    parts = []
    for path in outputs:
        size = path.stat().st_size
        parts.append(f"{to_rel(path)}:{size}")

    print("render_public_pdfs=PASS " + " ".join(parts))


if __name__ == "__main__":
    main()
