import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/md_to_pdf.py <input.md> <output.pdf>")
        return 2

    md_path = Path(sys.argv[1]).resolve()
    pdf_path = Path(sys.argv[2]).resolve()

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer
    except Exception as e:
        print("Missing dependency: reportlab. Install with: pip install reportlab")
        print(str(e))
        return 3

    md = md_path.read_text(encoding="utf-8", errors="replace").splitlines()

    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    h3 = styles["Heading3"]

    story = []
    in_code = False
    code_lines: list[str] = []

    def flush_code():
        nonlocal code_lines
        if not code_lines:
            return
        story.append(Preformatted("\n".join(code_lines), styles["Code"]))
        story.append(Spacer(1, 0.15 * inch))
        code_lines = []

    for raw in md:
        line = raw.rstrip("\n")

        if line.strip().startswith("```"):
            if in_code:
                in_code = False
                flush_code()
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            story.append(Spacer(1, 0.12 * inch))
            continue

        # Simple markdown headings
        if line.startswith("### "):
            story.append(Paragraph(re.escape(line[4:]).replace("\\ ", " "), h3))
            continue
        if line.startswith("## "):
            story.append(Paragraph(re.escape(line[3:]).replace("\\ ", " "), h2))
            continue
        if line.startswith("# "):
            story.append(Paragraph(re.escape(line[2:]).replace("\\ ", " "), h1))
            continue

        # Basic bullet handling
        if line.startswith("- "):
            text = line[2:]
            story.append(Paragraph(f"• {text}", normal))
            continue

        # Convert inline code `...` to <font face="Courier">...</font>
        def repl(m):
            return f'<font face="Courier">{m.group(1)}</font>'

        htmlish = re.sub(r"`([^`]+)`", repl, line)
        story.append(Paragraph(htmlish, normal))

    if in_code:
        flush_code()

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=md_path.stem,
    )
    doc.build(story)
    print(f"Wrote {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


