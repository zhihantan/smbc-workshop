#!/usr/bin/env python3
"""Build the participant handouts for the SMBC Data & AI Workshop (22 Oct 2026) from the workshop guide.

Everything participants read is taken from docs/SMBC_Workshop_Guide.md at build time, so the handouts can't drift
from the guide. Facilitator-only passages (setup, the facilitator close, the governance moment, test findings) are
left out, and the build stops if the guide changes in a way that could let one through.

    python handouts/build_handouts.py
    python handouts/build_handouts.py --workspace-url https://adb-1234567890123456.7.azuredatabricks.net

Writes:
  handouts/Lab_Workbook.md             participant version of the guide: data, labs, Genie Code, copy-paste kit
  handouts/Lab_Workbook_notebook.py    the same as a Databricks notebook, with runnable check-in and checkpoint cells
  handouts/dist/Lab_Workbook.html|pdf  A4, for printing or sharing
  handouts/dist/Cheat_Sheet.html|pdf   one A4 page, with QR codes
  handouts/dist/SMBC_Workshop_Guide.html|pdf     the whole guide, unfiltered, for sharing with SMBC
  handouts/dist/Workspace_Requirements.html|pdf  guide section 3 only, for the SAG team and workspace admins

The PDFs are printed with headless Google Chrome (set CHROME to its path if it isn't in /Applications); without
Chrome only the HTML is written. Needs the markdown and segno packages.
"""
import argparse, html, os, pathlib, re, shutil, subprocess, sys, tempfile

import markdown
import segno

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDE = os.path.join(ROOT, "docs", "SMBC_Workshop_Guide.md")
OUT = os.path.join(ROOT, "handouts")
DIST = os.path.join(OUT, "dist")
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

PLACEHOLDER = "<workspace URL>"
TRAINING_URL = "https://www.databricks.com/learn/training"
TITLE = "Lab workbook · SMBC Data & AI Workshop · Thursday 22 October 2026"
REQUIREMENTS = "3. Workspace requirements: what must be enabled"
REQUIREMENTS_TITLE = "SMBC Data & AI Workshop · 22 October 2026 · Workspace requirements"
FOOTER = "SMBC Data & AI Workshop · 22 October 2026 · All data is synthetic"

# (heading in the guide, heading in the workbook). Everything else in the guide is for facilitators and admins.
SECTIONS = [
    ("6. The scenario and the data", "1. The scenario and the data"),
    ("7. Lab 1: Build the trusted exposure table", "2. Lab 1: Build the trusted exposure table"),
    ("8. Lab 2: Credit Committee in 30 seconds", "3. Lab 2: Credit Committee in 30 seconds"),
    ("9. AI-assisted development with Genie Code", "4. AI-assisted development with Genie Code"),
    ("11. Next steps and resources", "5. Resources"),
    ("Appendix A: Copy-paste kit", "Appendix A: Copy-paste kit"),
    ("Appendix B: Troubleshooting", "Appendix B: Troubleshooting"),
]
# Text that must never reach participants, whatever happens to the guide.
BANNED = [r"(?i)answer key", r"facilitator/", r"What we saw when testing", r"Proposed follow-up", r"\bSAG\b",
          r"setup/", r"Facilitator close", r"Governance moment", r"§"]
# Fixes in Appendix B that only an admin can carry out.
ADMIN_FIX = re.compile(r"\]\(#[34]|Re-run `01_setup_workspace`|messaging team")

LAB1_CHECK_SQL = """-- Compare your Lab 1 result with the reference. Your schema is worked out from your login.
BEGIN
  DECLARE my_schema STRING DEFAULT regexp_replace(lower(split_part(current_user(), '@', 1)), '[^a-z0-9_]', '_');
  SELECT my_schema,
         (SELECT round(sum(exposure_usd) / 1e6, 1) FROM IDENTIFIER('smbc_workshop.' || my_schema || '.gold_group_exposure')
          WHERE as_of_date = '2026-09-30') AS mine_usd_m,
         (SELECT round(sum(exposure_usd) / 1e6, 1) FROM smbc_workshop.checkpoint.gold_group_exposure
          WHERE as_of_date = '2026-09-30') AS reference_usd_m;
END"""


# ---------------------------------------------------------------------------
# Extracting the participant text from the guide
# ---------------------------------------------------------------------------

def split_h2(text):
    """Return {heading: body} for every '## ' heading outside code fences."""
    sections, current, fence = {}, None, False
    for line in text.splitlines():
        if line.startswith("```"):
            fence = not fence
        if not fence and line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {k: "\n".join(v).strip().removesuffix("---").strip() for k, v in sections.items()}


def drop_h3(body, heading):
    """Remove the '### heading' subsection, up to the next ### heading."""
    body, n = re.subn(rf"^### {re.escape(heading)}\n.*?(?=^### |\Z)", "", body, flags=re.S | re.M)
    assert n == 1, f"expected one '### {heading}' subsection in the guide"
    return body.strip()


def drop_block(body, start):
    """Remove the paragraph or blockquote that starts with `start`, up to the next blank line."""
    body, n = re.subn(rf"^{re.escape(start)}.*?(?:\n\n|\Z)", "", body, flags=re.S | re.M)
    assert n == 1, f"expected one block starting {start!r} in the guide"
    return body.strip()


def cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def participant_troubleshooting(body):
    """In the troubleshooting table, replace fixes that need an admin with 'Ask a facilitator'."""
    lines, changed = [], 0
    for line in body.splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            row = cells(line)
            assert len(row) == 3, f"unexpected troubleshooting row: {line}"
            if ADMIN_FIX.search(row[2]):
                row[2], changed = "Ask a facilitator", changed + 1
            line = "| " + " | ".join(row) + " |"
        lines.append(line)
    assert changed >= 3, "expected the admin-only fixes (sections 3/4, re-running setup) in the troubleshooting table"
    return "\n".join(lines)


def slug(text):
    """GitHub-style heading anchor."""
    text = re.sub(r"[^\w\- ]", "", text.replace("`", "").strip().lower())
    return text.replace(" ", "-")


def headings(md_text):
    found, fence = [], False
    for line in md_text.splitlines():
        if line.startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,3}) (.+)$", line)
        if m:
            found.append((len(m.group(1)), m.group(2).strip()))
    return found


def resolve_links(md_text, outside=lambda anchor, text: text):
    """Keep links to headings in this document; a link to another part of the guide becomes `outside(anchor, text)`."""
    anchors = {slug(h) for _, h in headings(md_text)}

    def fix(m):
        text, anchor = m.groups()
        return m.group(0) if anchor in anchors else outside(anchor, text)

    md_text = re.sub(r"\[([^\]]+)\]\(#([^)]+)\)", fix, md_text)
    dangling = [a for a in re.findall(r"\]\(#([^)]+)\)", md_text) if a not in anchors]
    assert not dangling, f"dangling anchors: {dangling}"
    return md_text


def sql_line(text, prefix):
    m = re.search(rf"^{re.escape(prefix)}.*;$", text, re.M)
    assert m, f"expected a line starting {prefix!r} in the guide"
    return m.group(0)


def extract(guide_text, url):
    """Return (workbook markdown without contents, contents markdown, snippets used elsewhere)."""
    sections = split_h2(guide_text)
    for heading, _ in SECTIONS:
        assert heading in sections, f"expected '## {heading}' in the guide"
    notice = re.search(r"^> \*\*All workshop data is synthetic\.\*\*.*$", guide_text, re.M)
    assert notice, "expected the synthetic-data notice at the top of the guide"

    body = {new: sections[old] for old, new in SECTIONS}
    lab1, lab2 = "2. Lab 1: Build the trusted exposure table", "3. Lab 2: Credit Committee in 30 seconds"
    body[lab1] = drop_h3(body[lab1], "Facilitator close (3 min)")
    body[lab2] = drop_h3(body[lab2], "Governance moment (facilitator, 3 min)")
    body[lab2] = drop_block(body[lab2], "> **What we saw when testing")
    body["5. Resources"] = drop_block(body["5. Resources"], "**Proposed follow-up with SMBC:**")
    body["Appendix B: Troubleshooting"] = participant_troubleshooting(body["Appendix B: Troubleshooting"])

    for expected in ["2,370 → 2,325", "21 failed rows", "74,799 → 74,757"]:
        assert expected in body[lab1], f"expected {expected!r} in Lab 1 (the cheat sheet quotes it)"
    kit = body["Appendix A: Copy-paste kit"]
    lab1_check = re.search(r"✅ \*\*Checkpoint:\*\*.*?```sql\n(.*?)```", body[lab1], re.S)
    assert lab1_check, "expected the Lab 1 checkpoint queries"
    snippets = {
        "checkin": sql_line(kit, "INSERT INTO smbc_workshop.ops.checkin"),
        "answer": sql_line(kit, "INSERT INTO smbc_workshop.ops.lab_answers"),
        "lab1_check": lab1_check.group(1).strip(),
    }

    url_md = f"[{url}]({url})" if url else f"`{PLACEHOLDER}`"
    before = f"""## Before you start

**1. Sign in.** Open {url_md} in Microsoft Edge or Google Chrome and sign in with your SMBC account.

**2. Check in.** Open **SQL Editor**, choose the **SMBC Workshop** warehouse, paste this line and click **Run**. Change `DA` to `DE` if you're a data engineer.

```sql
{snippets["checkin"]}
```

**3. Find your schema.** Your Lab 1 tables go in `smbc_workshop.<your schema>`: the part of your email address before the @, in lower case, with any other characters replaced by `_`. For example, `jane.tan@…` becomes `jane_tan`.

**4. Getting help.** Turn your card to red, or raise a hand, and a helper will come to you.

**5. Short on time?** The checkpoint tables in `smbc_workshop.checkpoint` hold the reference result, so you can carry on with Lab 2 and the Genie Code segment whatever happens in Lab 1."""

    parts = [before] + [f"## {h}\n\n{b}" for h, b in body.items()]
    text = "\n\n---\n\n".join(parts)
    if url:
        text = text.replace(PLACEHOLDER, url)
    contents = "## Contents\n\n" + "\n".join(f"- [{h}](#{slug(h)})" for lvl, h in headings(text) if lvl == 2)
    return f"# {TITLE}\n\n{notice.group(0)}", contents, text, snippets


def requirements(guide_text):
    """Guide section 3 on its own, for the SAG team and workspace administrators."""
    sections = split_h2(guide_text)
    assert REQUIREMENTS in sections, f"expected '## {REQUIREMENTS}' in the guide"
    text = resolve_links(f"## {REQUIREMENTS}\n\n{sections[REQUIREMENTS]}")
    return (f"# {REQUIREMENTS_TITLE}\n\n*An extract from the SMBC Data & AI Workshop guide (section 3), for the SAG team "
            f"and workspace administrators.*\n\n{text}\n")


def check_banned(text, what):
    for pattern in BANNED:
        assert not re.search(pattern, text), f"{what} contains {pattern!r}"


# ---------------------------------------------------------------------------
# Notebook
# ---------------------------------------------------------------------------

def notebook_cells(title, text, snippets):
    """One markdown cell per H2/H3 section, plus runnable SQL at the check-in and the two lab checkpoints."""
    chunks, current, fence = [], [], False
    for line in text.splitlines():
        if line.startswith("```"):
            fence = not fence
        if not fence and re.match(r"^#{2,3} ", line) and current:
            chunks.append(current)
            current = []
        current.append(line)
    chunks.append(current)

    cells_out = [("md", f"{title}\n\nThis is a read-only copy. To run the SQL cells, use **File → Clone** to copy it to "
                        "your own folder, or paste the SQL into the SQL editor.")]
    inserted, h2 = set(), ""
    for chunk in chunks:
        md_text = "\n".join(l for l in chunk if l.strip() != "---").strip()
        cells_out.append(("md", md_text))
        heading = chunk[0]
        if heading.startswith("## "):
            h2 = heading[3:]
        if heading == "## Before you start":
            cells_out.append(("sql", f"-- Check in. Change 'DA' to 'DE' if you're a data engineer.\n{snippets['checkin']}"))
            inserted.add("checkin")
        elif heading == "### Core path" and h2.startswith("2. Lab 1"):
            cells_out.append(("sql", LAB1_CHECK_SQL))
            inserted.add("lab1")
        elif heading == "### Core path" and h2.startswith("3. Lab 2"):
            cells_out.append(("sql", "-- Lab 2 checkpoint. Replace <group name> with the group you found, then run the cell.\n"
                                     + snippets["answer"]))
            inserted.add("lab2")
    assert inserted == {"checkin", "lab1", "lab2"}, f"runnable cells not placed: {inserted}"
    return cells_out


def notebook_source(cells_in):
    blocks = []
    for kind, text in cells_in:
        lines = [f"%{kind}"] + text.splitlines()
        assert not any(l.startswith("# COMMAND") for l in lines), "a cell line starts with '# COMMAND'"
        blocks.append("\n".join("# MAGIC" + (f" {l}" if l else "") for l in lines))
    return "# Databricks notebook source\n" + "\n\n# COMMAND ----------\n\n".join(blocks) + "\n"


def check_notebook(source, cells_in):
    """Parse the notebook back and compare it with what was written."""
    assert source.startswith("# Databricks notebook source\n")
    blocks = source[len("# Databricks notebook source\n"):].rstrip("\n").split("\n\n# COMMAND ----------\n\n")
    assert len(blocks) == len(cells_in), f"notebook has {len(blocks)} cells, expected {len(cells_in)}"
    for block, (kind, text) in zip(blocks, cells_in):
        lines = block.split("\n")
        assert all(l == "# MAGIC" or l.startswith("# MAGIC ") for l in lines), "a notebook line lacks '# MAGIC'"
        back = [l[len("# MAGIC "):] if l.startswith("# MAGIC ") else "" for l in lines]
        assert back[0] == f"%{kind}" and "\n".join(back[1:]) == text, "notebook cell doesn't round-trip"
    return len(blocks)


# ---------------------------------------------------------------------------
# HTML and PDF
# ---------------------------------------------------------------------------

BASE_CSS = """
:root { --navy: #1B3139; --lava: #FF3621; --oat: #F9F7F4; --oat2: #EEEDE9; --slate: #5A6F77; --rule: #D5D2CC; }
@page { size: A4; margin: 15mm 15mm 17mm 15mm;
  @bottom-left { content: "FOOTER"; font: 7.5pt "Helvetica Neue", Arial, sans-serif; color: #5A6F77; }
  @bottom-right { content: "Page " counter(page) " of " counter(pages); font: 7.5pt "Helvetica Neue", Arial, sans-serif; color: #5A6F77; } }
html { font-family: "Helvetica Neue", Helvetica, Arial, "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif;
       color: var(--navy); -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; }
a { color: #2272B4; text-decoration: none; }
code { font-family: Menlo, Consolas, "Courier New", monospace; background: var(--oat); border-radius: 2px; padding: 0 1.5px; }
pre { background: var(--oat); border-left: 3px solid var(--lava); white-space: pre-wrap; overflow-wrap: anywhere;
      break-inside: avoid; margin: 0; }
pre code { background: none; padding: 0; }
"""

WORKBOOK_CSS = BASE_CSS + """
html { font-size: 9.8pt; line-height: 1.45; }
h1 { font-size: 24pt; line-height: 1.15; margin: 0 0 4mm; padding-bottom: 2.5mm; border-bottom: 3px solid var(--lava); }
h1 .sub { display: block; font-size: 12pt; font-weight: 400; color: var(--slate); margin-top: 1.5mm; }
h2 { font-size: 14pt; margin: 6mm 0 3mm; padding-bottom: 1.2mm; border-bottom: 1.2px solid var(--lava); break-after: avoid; }
h2.newpage { break-before: page; margin-top: 0; }
h3 { font-size: 11pt; margin: 5mm 0 2mm; break-after: avoid; }
p { margin: 0 0 2.2mm; }
ul, ol { margin: 0 0 2.6mm; padding-left: 6mm; }
li { margin: 0 0 1mm; }
li > ul { margin-top: 1mm; }
code { font-size: 8.4pt; }
pre { padding: 2.4mm 2.6mm; margin: 0 0 3mm; }
pre code { font-size: 7.6pt; line-height: 1.42; }
blockquote { margin: 0 0 3mm; padding: 2mm 3.5mm; background: var(--oat); border-left: 3px solid var(--navy); break-inside: avoid; }
blockquote p { margin: 0; }
table { border-collapse: collapse; width: 100%; margin: 0 0 3.5mm; font-size: 8.6pt; line-height: 1.35; }
th, td { border: 0.6pt solid var(--rule); padding: 1.3mm 1.8mm; vertical-align: top; text-align: left; }
th { background: var(--oat2); }
tr { break-inside: avoid; }
td code { font-size: 7.8pt; overflow-wrap: break-word; }
hr { display: none; }
p:has(+ pre), p:has(+ table), p:has(+ ul), p:has(+ ol) { break-after: avoid; }
"""


def page_html(title, css, body):
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>\n'
            f"<style>{css.replace('FOOTER', FOOTER)}</style></head>\n<body>\n{body}\n</body></html>\n")


LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+\.) ")
PLACEHOLDER_TAG = re.compile(r"<([A-Za-z][^<>=\"']*\s[^<>=\"']*)>")  # e.g. <workspace URL>: text, not an HTML tag


def escape_placeholders(line):
    """Show <placeholder text> outside code spans literally, instead of letting it pass through as an HTML tag."""
    parts = re.split(r"(`[^`]*`)", line)
    return "".join(p if i % 2 else PLACEHOLDER_TAG.sub(r"&lt;\1&gt;", p) for i, p in enumerate(parts))


def python_markdown_compat(text):
    """Adapt the guide's Markdown for Python-Markdown and for print.

    Python-Markdown needs a blank line before a list, quote, table or fence, and 4-space indents for nesting. For
    print, prompt text that the guide hard-wraps (```text blocks) is re-joined so it wraps at the page width, and the
    Goal / Time / Tools lines at the top of each lab get line breaks.
    """
    out, fence, prev = [], None, ""
    for line in text.splitlines():
        if line.startswith("```"):
            if fence is None and prev.strip():
                out.append("")
            fence = line[3:].strip() if fence is None else None
        elif fence == "text":
            if prev.strip() and not prev.startswith("```") and (line[:1].isspace() or line[:1].islower()):
                out[-1] = f"{out[-1]} {line.strip()}"
                prev = out[-1]
                continue
        elif fence is None:
            line = escape_placeholders(line)
            if re.match(r"\*\*(Time|Tools):\*\*", line) and prev.strip():
                out[-1] += "  "
            item = LIST_ITEM.match(line)
            if item and 0 < len(item.group(1)) < 4 and LIST_ITEM.match(prev):
                line = "    " + line.lstrip()
            elif item and not item.group(1) and prev.strip() and not LIST_ITEM.match(prev):
                out.append("")
            elif (item and not item.group(1) and (above := LIST_ITEM.match(prev)) and not above.group(1)
                  and item.group(2)[0].isdigit() != above.group(2)[0].isdigit()):
                out.append("")  # a bullet list straight after a numbered one (or vice versa) is a new list
            elif line.startswith(">") and prev.strip() and not prev.startswith(">"):
                out.append("")
            elif line.startswith("|") and prev.strip() and not prev.startswith("|"):
                out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


def render_html(md_text, main=None, sub=None):
    """Markdown to print-ready HTML. Numbered sections and appendices start a new page (unless they come first), and
    every internal link must land on a heading. `main` and `sub` restyle the H1 as a title and a subtitle."""
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"],
                           extension_configs={"toc": {"slugify": lambda value, separator: slug(value)}})
    body = md.convert(python_markdown_compat(md_text))
    title = re.search(r"^# (.+)$", md_text, re.M).group(1)
    if main:
        body, n = re.subn(rf"<h1([^>]*)>{re.escape(html.escape(title))}</h1>",
                          rf'<h1\1>{html.escape(main)}<span class="sub">{html.escape(sub)}</span></h1>', body)
        assert n == 1, f"title {title!r} not found in the HTML"
    h2s = [h for lvl, h in headings(md_text) if lvl == 2]
    for h in h2s[1:]:
        if re.match(r"\d+\.|Appendix", h):
            body, n = re.subn(rf'<h2 id="{re.escape(slug(h))}">', f'<h2 class="newpage" id="{slug(h)}">', body)
            assert n == 1, f"heading #{slug(h)} not found in the HTML"
    ids = set(re.findall(r' id="([^"]+)"', body))
    missing = [a for a in re.findall(r'href="#([^"]+)"', body) if a not in ids]
    assert not missing, f"{title}: links to missing headings: {missing}"
    return page_html(title, WORKBOOK_CSS, body)


def qr_svg(url):
    return segno.make(url, error="m").svg_inline(dark="#1B3139", border=0, omitsize=True)


def code(text):
    return f"<pre><code>{html.escape(text)}</code></pre>"


def narrow_sql(sql, width=56):
    """Re-break SQL for a narrow column: SELECT and WHERE on their own lines, long lines wrapped with an indent."""
    sql = sql.replace(" SELECT current_user()", "\nSELECT current_user()").replace(" WHERE ", "\nWHERE ")
    lines = []
    for line in sql.splitlines():
        while len(line) > width and " " in line[:width]:
            cut = line.rindex(" ", 0, width)
            if line[:cut].endswith(" AS"):  # keep an alias with its AS
                cut -= 3
            lines.append(line[:cut])
            line = "    " + line[cut + 1:]
        lines.append(line)
    return "\n".join(lines)


CHEAT_CSS = BASE_CSS + """
@page { size: A4; margin: 9mm 10mm 9mm 10mm; @bottom-left { content: none; } @bottom-right { content: none; } }
html { font-size: 8.6pt; line-height: 1.37; }
header { background: var(--navy); color: #fff; padding: 3mm 4.5mm 3mm; border-bottom: 2.2mm solid var(--lava);
         display: flex; justify-content: space-between; align-items: flex-end; }
header h1 { font-size: 15pt; margin: 0; line-height: 1.15; }
header p { margin: 0.8mm 0 0; font-size: 8.4pt; color: #D7E0E3; }
header .tag { font-size: 7.6pt; text-align: right; color: #D7E0E3; }
main { display: grid; grid-template-columns: 1fr 1fr; column-gap: 5mm; margin-top: 3.6mm; }
section { margin: 0 0 3.6mm; break-inside: avoid; }
h2 { font-size: 10pt; margin: 0 0 1.4mm; padding-bottom: 0.8mm; border-bottom: 1px solid var(--lava); }
h2 .n { display: inline-block; min-width: 4.2mm; height: 4.2mm; line-height: 4.2mm; border-radius: 2.1mm; background: var(--lava);
        color: #fff; text-align: center; font-size: 7.4pt; margin-right: 1.4mm; vertical-align: 0.3mm; }
p { margin: 0 0 1.4mm; }
code { font-size: 7.6pt; }
pre { padding: 1.4mm 2mm; margin: 0.6mm 0 1.6mm; }
pre code { font-size: 7.2pt; line-height: 1.34; }
ol { margin: 0 0 1.4mm; padding-left: 5mm; }
ol.steps { list-style: none; padding-left: 0; counter-reset: step -1; }
ol.steps li { counter-increment: step; position: relative; padding-left: 4.6mm; margin-bottom: 0.9mm; }
ol.steps li::before { content: counter(step); position: absolute; left: 0; top: 0; font-weight: 700; color: var(--lava); }
ol.steps.from1 { counter-reset: step 0; }
.signin { display: flex; gap: 3mm; align-items: center; }
.signin .url { font-size: 9pt; font-weight: 700; overflow-wrap: anywhere; }
.qr { width: 21mm; height: 21mm; flex: none; }
.qr svg { width: 100%; height: 100%; display: block; }
.qr.placeholder { border: 1.2px dashed var(--slate); border-radius: 1.5mm; color: var(--slate); font-size: 7pt;
                  display: flex; align-items: center; justify-content: center; text-align: center; }
.prompt { background: var(--oat); border-left: 3px solid var(--navy); padding: 1.2mm 2mm; margin: 0 0 1.3mm; }
.prompt b { color: var(--navy); }
.cards { display: flex; gap: 2mm; margin: 0 0 1.4mm; }
.card { flex: 1; padding: 1.4mm 2mm; border-radius: 1.2mm; color: #fff; font-weight: 700; text-align: center; }
.card.red { background: var(--lava); } .card.green { background: #00A972; }
.learn { display: flex; gap: 3mm; align-items: center; }
footer { margin-top: 1mm; padding-top: 1.6mm; border-top: 1px solid var(--rule); color: var(--slate); font-size: 7.4pt; text-align: center; }
"""


def cheat_sheet_html(url, snippets):
    shown_url = url or PLACEHOLDER
    qr = (f'<div class="qr">{qr_svg(url)}</div>' if url
          else '<div class="qr placeholder">QR code<br>for the<br>workspace</div>')
    one = f"{html.escape(shown_url)}/one"
    lab1 = [
        "<b>Find your schema</b> in Catalog Explorer → <code>smbc_workshop</code>.",
        "<b>+ New → Visual data prep</b>. Name it <i>Monday exposure report</i>; compute: <b>Serverless</b>.",
        "<b>Sources</b> from <code>smbc_workshop.raw.landing</code>: <code>counterparties</code>, <code>facilities</code>, "
        "<code>monthly_balances</code>, <code>fx_rates</code>, and the limits (<code>group_limits.xlsx</code> or its folder).",
        "<b>Unique</b> on counterparties, all columns: 2,370 → 2,325 rows.",
        "<b>Genie Code</b> on facilities: clean <code>currency</code>, parse both date formats (prompt in A.2).",
        "<b>Guardrails</b>: <code>committed_amount</code> &gt; 0, <code>maturity_date &gt;= start_date</code>, dates not null. "
        "<b>Failed</b> → Output <code>quarantine_facilities</code>: 21 failed rows.",
        "<b>Balances</b>: parse <code>as_of_date</code>, add <code>month</code>; <b>Unique</b> on <code>facility_id</code>, "
        "<code>as_of_date</code>, latest <code>extract_ts</code>: 74,799 → 74,757. <b>FX</b>: add <code>rate_month</code>.",
        "<b>Join</b> with Genie Code (A.2): balances → facilities → counterparties → FX on currency and month; "
        "add <code>exposure_usd</code>, <code>exposure_jpy</code>.",
        "<b>Aggregate</b> by <code>as_of_date</code>, <code>parent_group_id</code>; <b>Join</b> the limits; "
        "<code>utilisation_pct</code> = 100 × exposure ÷ limit.",
        "<b>Output</b> <code>gold_group_exposure</code> (Overwrite) → <b>Run</b> → <b>Schedule</b> daily, 07:00 Singapore time.",
    ]
    lab2 = [
        "<b>Dashboard</b>: + New → Dashboard on both <code>checkpoint</code> gold tables. Ask the AI assistant for the "
        f"top-10 bar chart; add counters, a monthly trend and exposure by country; filters; <b>Publish</b>. Then open "
        f"<code>{one}</code>.",
        "<b>Genie Agent</b>: Genie Agents → New on the same two tables. Title <i>Credit Risk – &lt;your name&gt;</i>, "
        "warehouse <b>SMBC Workshop</b>; add the instructions (A.3), example SQL (A.5) and questions (A.6).",
        "<b>Ask, then open the SQL.</b> Trust, but verify.",
        "<b>Fiscal-year test</b>: ask about Q1 FY2026 and FY2025 and check the dates in the SQL. Add A.4, ask again.",
    ]
    li = lambda items: "".join(f"<li>{i}</li>" for i in items)
    body = f"""
<header>
  <div><h1>SMBC Data &amp; AI Workshop · Cheat sheet</h1><p>Thursday 22 October 2026 · Lakeflow, AI/BI, Genie Agents and Genie Code</p></div>
  <div class="tag">All data is synthetic</div>
</header>
<main>
<div>
  <section><h2><span class="n">1</span>Sign in</h2>
    <div class="signin">{qr}<div><div class="url">{html.escape(shown_url)}</div>
      <p>Microsoft Edge or Google Chrome; sign in with your SMBC account. Warehouse: <b>SMBC Workshop</b>.</p></div></div>
  </section>
  <section><h2><span class="n">2</span>Check in</h2>
    <p>SQL Editor → <b>SMBC Workshop</b> → paste and <b>Run</b>. Use <code>'DE'</code> if you're a data engineer.</p>
    {code(narrow_sql(snippets["checkin"]))}
  </section>
  <section><h2><span class="n">3</span>Your schema</h2>
    <p><code>smbc_workshop.&lt;your schema&gt;</code>: the part of your email before the @, in lower case, other characters
    replaced by <code>_</code>. <code>jane.tan@…</code> → <code>jane_tan</code></p>
  </section>
  <section><h2>Lab 1 · Build the trusted exposure table</h2>
    <ol class="steps">{li(lab1)}</ol>
    <p><b>✅ Checkpoint:</b> the two totals should be identical.</p>
    {code(narrow_sql(snippets["lab1_check"]))}
  </section>
</div>
<div>
  <section><h2>Lab 2 · Credit Committee in 30 seconds</h2>
    <ol class="steps from1">{li(lab2)}</ol>
    <p><b>✅ Checkpoint:</b> ask <i>"Which groups were above 90% of their limit at the end of FY2026 H1?"</i>, then submit the group's name:</p>
    {code(narrow_sql(snippets["answer"]))}
  </section>
  <section><h2>Genie Code · Ask why, safely</h2>
    <div class="prompt"><b>Explore:</b> "Profile <code>smbc_workshop.checkpoint.gold_group_exposure</code> and tell me what is unusual about the latest month compared with April 2026."</div>
    <div class="prompt"><b>Generate:</b> "For the group with the highest utilisation at 30 Sep 2026, split its change in exposure since April into an FX effect and a new-drawdowns effect, by subsidiary. Chart it."</div>
    <div class="prompt"><b>Explain and convert:</b> "Explain this procedure and point out any risks, then rewrite it as Databricks SQL. Just explain first, don't run any code." Paste the legacy procedure from A.9.</div>
    <p>Full prompts: workbook A.8.</p>
  </section>
  <section><h2>Getting help</h2>
    <div class="cards"><div class="card red">Red: I need help</div><div class="card green">Green: all good</div></div>
    <p><b>Stuck or short on time?</b> Carry on from the reference tables in <code>smbc_workshop.checkpoint</code>: nothing
    later depends on finishing Lab 1. Common problems and fixes: workbook Appendix B.</p>
  </section>
  <section><h2>Keep learning</h2>
    <div class="learn"><div class="qr">{qr_svg(TRAINING_URL)}</div>
      <p>Free self-paced training, learning paths and certifications for data analysts and data engineers:<br>
      <b>databricks.com/learn/training</b></p></div>
  </section>
</div>
</main>
<footer>All data is synthetic: the borrowers, groups and figures are made up, and no SMBC data, systems or customer
information is used.</footer>
"""
    page = page_html("SMBC Data & AI Workshop · Cheat sheet", CHEAT_CSS, body)
    text = re.sub(r"<[^>]+>", " ", body)
    for answer in ["Orchid", "94%", "27,239", "366.9", "USD 27"]:
        assert answer not in text, f"the cheat sheet gives away an answer: {answer}"
    return page


def print_pdf(html_path, pdf_path):
    if not os.path.exists(CHROME):
        print(f"Chrome not found at {CHROME}; skipped {os.path.relpath(pdf_path, ROOT)}")
        return None
    profile = tempfile.mkdtemp(prefix="handouts-chrome-")
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={profile}",
                        f"--print-to-pdf={pdf_path}", pathlib.Path(html_path).as_uri()],
                       check=True, capture_output=True, timeout=120)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    with open(pdf_path, "rb") as f:
        return len(re.findall(rb"/Type\s*/Page\b", f.read()))


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", os.path.relpath(path, ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the participant handouts from the workshop guide")
    ap.add_argument("--workspace-url", default="", help=f"workshop workspace URL (default: the placeholder {PLACEHOLDER})")
    a = ap.parse_args(argv)
    url = a.workspace_url.strip().rstrip("/")
    if url and not url.startswith("https://"):
        sys.exit("--workspace-url must start with https://")

    with open(GUIDE, encoding="utf-8") as f:
        guide_text = f.read()
    title, contents, text, snippets = extract(guide_text, url)
    text = resolve_links(text, lambda anchor, text: "a facilitator" if re.match(r"[34]", anchor) else text)
    workbook = f"{title}\n\n{contents}\n\n{text}\n"
    check_banned(workbook, "the workbook")

    os.makedirs(DIST, exist_ok=True)
    write(os.path.join(OUT, "Lab_Workbook.md"), workbook)

    cells_in = notebook_cells(title, text, snippets)
    source = notebook_source(cells_in)
    check_banned(source, "the notebook")
    n_cells = check_notebook(source, cells_in)
    write(os.path.join(OUT, "Lab_Workbook_notebook.py"), source)

    pages_out = [
        ("Lab_Workbook", render_html(workbook, *TITLE.split(" · ", 1))),
        ("Cheat_Sheet", cheat_sheet_html(url, snippets)),
        ("SMBC_Workshop_Guide", render_html(guide_text)),
        ("Workspace_Requirements", render_html(requirements(guide_text), *REQUIREMENTS_TITLE.rsplit(" · ", 1)[::-1])),
    ]
    for name, page in pages_out:
        html_path, pdf_path = os.path.join(DIST, f"{name}.html"), os.path.join(DIST, f"{name}.pdf")
        write(html_path, page)
        pages = print_pdf(html_path, pdf_path)
        if pages is not None:
            print(f"wrote {os.path.relpath(pdf_path, ROOT)} ({pages} pages)")
            if name == "Cheat_Sheet":
                assert pages == 1, f"the cheat sheet must fit on one page; it has {pages}"
    print(f"notebook: {n_cells} cells; workspace URL: {url or 'placeholder'}")


if __name__ == "__main__":
    main()
