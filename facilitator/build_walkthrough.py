#!/usr/bin/env python3
"""Assemble the full workshop walkthrough as one Word document: the overview, the facilitator guide, the attendee
guide, workspace setup and the presenter script.

  .venv/bin/python handouts/build_handouts.py           # first: the attendee guide comes from handouts/Lab_Workbook.md
  .venv/bin/python facilitator/build_walkthrough.py     # writes facilitator/dist/Workshop_Walkthrough.md and .docx
  .venv/bin/python facilitator/publish_walkthrough.py   # then: create or update the Google Doc

Everything is taken from the existing sources at build time (the guide, the README's asset table, the run of show,
the answer key, the quiz, the polls and survey, the lab workbook and the slide notes), so the walkthrough never drifts
from them. It contains the answer key, so it lives with the facilitator material. Needs pypandoc_binary and lxml.
"""
import io
import json
import os
import re
import subprocess
import zipfile

import pypandoc
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(HERE, "dist")
OUT_MD = os.path.join(DIST, "Workshop_Walkthrough.md")
OUT_DOCX = os.path.join(DIST, "Workshop_Walkthrough.docx")
TITLE = "SMBC Data & AI Workshop: full walkthrough"
SUBTITLE = "Facilitator guide, attendee guide and workspace setup"
CONTENTS_PLACEHOLDER = "CONTENTS-PLACEHOLDER"  # replaced by the linked contents list
NAVY, HEADER_FILL, BORDER = "1B3139", "EEEDE9", "BFBFBF"
A4_WIDTH, A4_HEIGHT, MARGIN = 11906, 16838, 1134  # twips; 2 cm margins
AFTER_BLOCK = 200  # twips (10 pt) above a paragraph that follows a table, a list or a code block

# The presenter script groups slides into the agenda's segments, starting at these slides.
SEGMENTS = {
    "From days to seconds, with guardrails": "Welcome and check-in · 0:00",
    "Data engineering with Lakeflow": "Data engineering with Lakeflow · 0:25",
    "Lab 1: Build the trusted exposure table": "Lab 1 · 0:45",
    "Self-service analytics": "Self-service analytics · 1:40",
    "Lab 2: Credit Committee in 30 seconds": "Lab 2 · 2:00",
    "AI-assisted development with Genie Code": "Genie Code · 2:55",
    "Quiz: join on your phone": "Quiz and close · 3:10",
}
LIST_ITEM = re.compile(r"\s*([-*]|\d+\.) ")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def headings(md):
    """(line index, level, text) for every heading outside code fences."""
    found, fence = [], False
    for i, line in enumerate(md.split("\n")):
        if line.startswith("```"):
            fence = not fence
        elif not fence and (m := re.match(r"(#{1,6}) (.*)", line)):
            found.append((i, len(m.group(1)), m.group(2).strip()))
    return found


def section(md, title, level, keep_heading=False):
    """The text under a heading, up to the next heading of the same or a higher level. Fails if it's missing."""
    lines, found = md.split("\n"), headings(md)
    for n, (i, lvl, text) in enumerate(found):
        if lvl == level and text == title:
            end = next((j for j, l2, _ in found[n + 1:] if l2 <= level), len(lines))
            return "\n".join(lines[i if keep_heading else i + 1:end]).strip("\n")
    raise SystemExit(f"Heading not found: {'#' * level} {title}")


def shift(md, by):
    """Demote every heading outside code fences by `by` levels."""
    lines, fence = md.split("\n"), False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
        elif not fence and re.match(r"#{1,6} ", line):
            lines[i] = "#" * by + line
    return "\n".join(lines)


def clean(md):
    """Make Markdown safe for a Google Doc. Links to anchors and repo files become text; placeholders such as
    <workspace URL> outside code are escaped, so Pandoc doesn't read them as HTML; "1. + New" stays one list item.
    Horizontal rules are dropped: only some sources have them, and the space above each heading separates sections."""
    out, fence = [], False
    for line in md.split("\n"):
        if line.startswith("```"):
            fence = not fence
        if fence or line.startswith("```"):
            out.append(line)
            continue
        if line == "---":
            continue
        line = re.sub(r"\[([^\]]+)\]\((?!https?://)[^)]*\)", r"\1", line)
        line = re.sub(r"^(\s*(?:\d+\.|[-*]) )\+ ", r"\1\\+ ", line)
        parts = re.split(r"(`[^`]*`)", line)  # leave code spans alone
        parts[::2] = [re.sub(r"<(?!https?://)([A-Za-z][^<>]*)>", r"\\<\1\\>", p) for p in parts[::2]]
        out.append("".join(parts))
    return "\n".join(out)


def note_blocks(lines):
    """Speaker notes are written one thought per line: keep each line its own paragraph, and lists together."""
    out, previous = [], None
    for line in lines:
        is_item = bool(LIST_ITEM.match(line))
        if out:
            out.append("\n" if is_item and previous else "\n\n")
        out.append(line)
        previous = is_item
    return "".join(out)


def presenter_script(slides_md):
    """Slide titles and speaker notes from slides/Workshop_Slides.md, grouped by segment."""
    body = slides_md.split("\n---\n", 1)[1]  # drop the front matter
    slides, current, fence = [], [], False
    for line in body.split("\n"):
        if line.startswith("```"):
            fence = not fence
        if line == "---" and not fence:
            slides.append("\n".join(current))
            current = []
        else:
            current.append(line)
    slides.append("\n".join(current))

    out, seen = [], set()
    for n, slide in enumerate(slides, 1):
        title = next(l[2:].strip() for l in slide.split("\n") if l.startswith("# "))
        if title in SEGMENTS:
            out.append(f"## {SEGMENTS[title]}")
            seen.add(title)
        out.append(f"### Slide {n}: {title}")
        for note in re.findall(r"<!--\n(.*?)\n-->", slide, re.S):
            lines = note.strip().split("\n")
            if (m := re.fullmatch(r"\[(.+)\]", lines[0])):
                lines[0] = f"*{m.group(1)}*"
            out.append(note_blocks(lines))
    missing = set(SEGMENTS) - seen
    assert not missing, f"segment slides not found: {missing}"
    return "\n\n".join(out)


def build_markdown():
    guide = read("docs/SMBC_Workshop_Guide.md")
    run = read("facilitator/run_of_show.md")
    workbook = read("handouts/Lab_Workbook.md")

    # The dry-run set-up steps are specific to the Databricks test workspace: keep the goal and the checklist only.
    dry_run = section(run, "6. Dry run in the Databricks test workspace", 2)
    setup_block = re.search(r"\*\*Set up\*\*.*?(?=\*\*Time and test:\*\*)", dry_run, re.S)
    assert setup_block, "dry-run set-up block not found"
    dry_run = dry_run.replace(setup_block.group(0), "The set-up steps for the Databricks test workspace are in the run "
                                                    "of show in the workshop repository.\n\n")
    run_sections = [(t, section(run, t, 2)) for _, lvl, t in headings(run) if lvl == 2]
    run_sections = [(t, dry_run if t.startswith("6. Dry run") else body) for t, body in run_sections]
    after = run_sections.pop()  # "9. After the workshop" goes last, after the facilitator-only reference material
    assert after[0].startswith("9. After the workshop"), after[0]

    testing_note = re.search(r"^> \*\*What we saw when testing.*$", guide, re.M)
    assert testing_note, "the 'What we saw when testing' note is missing from the guide"
    moments = "\n\n".join([
        "### Lab 1: facilitator close (3 min)", section(guide, "Facilitator close (3 min)", 3),
        "### Lab 2: the fiscal-year test, what we saw in testing", testing_note.group(0),
        "### Lab 2: governance moment (3 min)", section(guide, "Governance moment (facilitator, 3 min)", 3),
    ])

    def strip_title(md):  # an embedded document's H1 is replaced by our own heading
        return re.sub(r"\A# .*\n+", "", md)

    facilitator = [f"## 2.{n} {t.split('. ', 1)[1]}\n\n{shift(body, 1)}" for n, (t, body) in enumerate(run_sections, 1)]
    k = len(facilitator)
    facilitator += [
        f"## 2.{k + 1} Facilitator moments in the labs\n\nThese parts of the labs are run by a facilitator and aren't in "
        "the attendee guide.\n\n" + moments,
        f"## 2.{k + 2} Answer key\n\n" + shift(strip_title(read("facilitator/answer_key.md")), 1),
        f"## 2.{k + 3} Quiz\n\n" + shift(strip_title(read("facilitator/quiz.md")), 1),
        f"## 2.{k + 4} Polls and survey\n\n" + shift(strip_title(read("facilitator/polls_and_survey.md")), 1),
        f"## 2.{k + 5} {after[0].split('. ', 1)[1]}\n\n" + shift(after[1], 1),
    ]
    facilitator = "\n\n".join(facilitator)
    # Links to other repo files don't work in a Google Doc, and this part renumbers the run of show: point its
    # "(section N)" and its links to the facilitator files at their sections here.
    numbers = {t.split(". ", 1)[0]: f"2.{n}" for n, (t, _) in enumerate(run_sections, 1)}
    numbers[after[0].split(". ", 1)[0]] = f"2.{k + 5}"
    facilitator = re.sub(r"\(section (\d+)\)", lambda m: f"(section {numbers[m.group(1)]})", facilitator)
    for name, n in (("answer_key.md", k + 2), ("quiz.md", k + 3), ("polls_and_survey.md", k + 4)):
        facilitator = re.sub(r"\[[^\]]*\]\(%s\)" % re.escape(name), f"section 2.{n}", facilitator)

    # Section 6 of the guide is section 1 of the attendee guide, in Part 3 here.
    glance, found = re.subn(r"\bSection 6\b", "Section 1 of Part 3", section(guide, "1. At a glance", 2))
    assert found == 1, "the guide's pointer to the story (section 6) has changed"
    assets = re.search(r"^\| Asset \|.*?(?=\n\n|\Z)", section(read("README.md"), "The story", 2), re.S | re.M)
    assert assets, "the asset table is missing from the README's story"

    attendee = section(workbook, workbook.split("\n", 1)[0][2:], 1)  # everything under the workbook's title
    attendee = re.sub(r"^## Contents\n.*?(?=^## )", "", attendee, flags=re.S | re.M)

    setup = "\n\n".join(section(guide, t, 2, keep_heading=True) for t in (
        "3. Workspace requirements: what must be enabled", "4. Setting up the workspace", "5. Participant pre-work"))

    doc = f"""**All workshop data is synthetic.** The labs use a made-up SMBC APAC corporate lending book: every borrower, group, limit and balance is fictional. No SMBC data, systems or customer information is used at any point.

This document walks through the whole workshop, from setting up the workspace to the follow-up email. It's assembled from the workshop's source materials (the workshop guide, the README, the run of show, the attendee workbook and the presenter notes), so it matches them.

| Part | What it covers | For | Share with |
|---|---|---|---|
| 1 | The workshop at a glance: goals, agenda, storyline, what the setup creates | Everyone | Anyone |
| 2 | Facilitator guide: roles, countdown, timeline, fallbacks, helper briefing, answer key, quiz, follow-up | Facilitators and helpers | **Facilitators only: it contains the answers** |
| 3 | Attendee guide: setup, Lab 1, Lab 2, Genie Code, copy-paste kit, troubleshooting | Attendees | Attendees (no answers) |
| 4 | Workspace setup and requirements: what must be enabled, the setup notebooks, the pre-work email | SMBC's SAG team and workspace admins | SMBC's admins |
| 5 | Presenter script: slide-by-slide speaker notes | Presenters | Facilitators |

## Contents

{CONTENTS_PLACEHOLDER}

# Part 1. The workshop at a glance

## 1.1 At a glance

{glance}

## 1.2 Agenda

{section(guide, "2. Agenda", 2)}

## 1.3 What the setup creates

`setup/00_master_setup` creates these in the workshop workspace; section 4 of Part 4 has the steps.

{assets.group(0)}

# Part 2. Facilitator guide

> **Facilitators and helpers only.** This part contains the answer key and the planted findings. Don't share it with attendees.

{facilitator}

# Part 3. Attendee guide

> This part is the attendee workbook: it contains no answers, so it can be shared with attendees as it is. Its section numbers match the printed lab workbook.

{attendee}

# Part 4. Workspace setup and requirements

> For SMBC's SAG team and workspace administrators. Section numbers match the workshop guide.

{setup}

# Part 5. Presenter script

> Slide-by-slide speaker notes from the workshop slides: timing, what to say, what helpers should watch for, and fallbacks.

{presenter_script(read("slides/Workshop_Slides.md"))}
"""
    return clean(doc)


def stringify(inlines):
    """Plain text of Pandoc JSON inlines."""
    out = []
    for item in inlines:
        kind, content = item["t"], item.get("c")
        if kind == "Str":
            out.append(content)
        elif kind in ("Space", "SoftBreak", "LineBreak"):
            out.append(" ")
        elif kind == "Code":
            out.append(content[1])
        elif kind in ("Emph", "Strong", "Strikeout", "Underline", "SmallCaps"):
            out.append(stringify(content))
        elif kind in ("Link", "Span", "Quoted"):
            out.append(stringify(content[1]))
    return "".join(out)


def add_contents(md):
    """Replace the placeholder with the Parts and their sections, linked to their headings. Pandoc turns the links
    into Word bookmarks, which Google Docs keeps as working links."""
    ast = json.loads(pypandoc.convert_text(md, "json", format="gfm"))
    entries, after = [], False
    for block in ast["blocks"]:
        if block["t"] != "Header":
            continue
        level, (identifier, _, _), inlines = block["c"]
        text = stringify(inlines)
        if text == "Contents":
            after = True
        elif after and level <= 2:
            entries.append(f"- **[{text}](#{identifier})**" if level == 1 else f"  - [{text}](#{identifier})")
    assert entries and CONTENTS_PLACEHOLDER in md, "contents placeholder or headings missing"
    return md.replace(CONTENTS_PLACEHOLDER, "\n".join(entries), 1)


def reference_docx(path):
    """Pandoc's default Word template, restyled: Arial, navy headings with room above them, each Part on a new
    page."""
    data = subprocess.run([pypandoc.get_pandoc_path(), "--print-default-data-file", "reference.docx"],
                          capture_output=True, check=True).stdout
    src = zipfile.ZipFile(io.BytesIO(data))
    styles = src.read("word/styles.xml").decode("utf-8")

    arial = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial" w:cs="Arial" />'
    styles = re.sub(r"<w:rFonts [^>]*w:asciiTheme=\"minorHAnsi\"[^>]*/>", arial, styles, count=1)
    styles = styles.replace('<w:sz w:val="24" />\n        <w:szCs w:val="24" />',
                            '<w:sz w:val="21" />\n        <w:szCs w:val="21" />', 1)

    def restyle(style_id, extra_ppr="", size=None, spacing=None):
        nonlocal styles
        m = re.search(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % style_id, styles, re.S)
        assert m, style_id
        block = re.sub(r"<w:rFonts [^>]*/>", arial, m.group(0))
        if spacing:  # (before, after) in twips
            block, found = re.subn(r"<w:spacing [^>]*/>", '<w:spacing w:before="%d" w:after="%d" />' % spacing, block, 1)
            assert found, f"{style_id} has no spacing to replace"
        block = re.sub(r"<w:color [^>]*/>", f'<w:color w:val="{NAVY}" />', block)
        if "<w:color " not in block:
            block = block.replace("<w:rPr>", f'<w:rPr><w:color w:val="{NAVY}" />', 1)
        if size:
            block = re.sub(r'<w:sz w:val="\d+" />', f'<w:sz w:val="{size}" />', block)
            block = re.sub(r'<w:szCs w:val="\d+" />', f'<w:szCs w:val="{size}" />', block)
        if extra_ppr:
            block = block.replace("<w:pPr>", "<w:pPr>" + extra_ppr, 1)
        styles = styles.replace(m.group(0), block)

    restyle("Title", size=44)
    restyle("Heading1", extra_ppr="<w:pageBreakBefore />", size=36, spacing=(0, 240))
    restyle("Heading2", size=28, spacing=(480, 120))  # 24 pt above each section, 18 pt above each subsection
    restyle("Heading3", size=24, spacing=(360, 100))
    styles = styles.replace('<w:spacing w:before="180" w:after="180" />', '<w:spacing w:before="60" w:after="120" />', 1)

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            dst.writestr(item, styles if item.filename == "word/styles.xml" else src.read(item.filename))


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def w(tag):
    return f"{{{W}}}{tag}"


def element(tag, **attrs):
    e = etree.Element(w(tag))
    for key, value in attrs.items():
        e.set(w(key), str(value))
    return e


def block_kind(block):
    """What a block in the document body is: table, heading, list (an item), code, text or other."""
    if block.tag == w("tbl"):
        return "table"
    if block.tag != w("p"):
        return "other"
    p_pr = block.find(w("pPr"))
    style = p_pr.find(w("pStyle")) if p_pr is not None else None
    name = style.get(w("val")) if style is not None else ""
    if name.startswith("Heading") or name in ("Title", "Subtitle"):
        return "heading"
    if p_pr is not None and p_pr.find(w("numPr")) is not None:
        return "list"
    return "code" if name == "SourceCode" else "text"


def space_before(paragraph, twips):
    """Set the space above a paragraph. w:spacing goes after w:pStyle, the keep and page-break settings and w:numPr."""
    p_pr = paragraph.find(w("pPr"))
    if p_pr is None:
        p_pr = element("pPr")
        paragraph.insert(0, p_pr)
    spacing = p_pr.find(w("spacing"))
    if spacing is None:
        spacing = element("spacing")
        anchor = [x for x in p_pr if x.tag in (w("pStyle"), w("keepNext"), w("keepLines"), w("pageBreakBefore"), w("numPr"))]
        if anchor:
            anchor[-1].addnext(spacing)
        else:
            p_pr.insert(0, spacing)
    spacing.set(w("before"), str(twips))


def column_widths(cells, text_width):
    """Widths in twips: shared in proportion to each column's longest cell, but never so narrow that the column's
    longest word (header included) has to break. Code and long identifiers may still wrap."""
    columns = max(len(r) for r in cells)
    weights, minimums = [], []
    for c in range(columns):
        texts = ["".join(t.text or "" for t in r[c].iter(w("t"))) for r in cells if len(r) > c]
        longest_word = max((len(word) for text in texts for word in text.split()), default=1)
        weights.append(min(max(max(map(len, texts), default=1), 4), 60))
        minimums.append(min(longest_word * 125 + 240, 0.3 * text_width))  # ~125 twips a character at 10.5 pt Arial
    fixed = {}
    while True:  # pin any column that would fall below its minimum, and share the rest by weight
        free = text_width - sum(fixed.values())
        rest = sum(x for c, x in enumerate(weights) if c not in fixed)
        widths = [fixed.get(c, free * x / rest if rest else 0) for c, x in enumerate(weights)]
        short = [c for c in range(columns) if c not in fixed and widths[c] < minimums[c]]
        if not short:
            break
        fixed.update({c: minimums[c] for c in short})
        if len(fixed) == columns:
            widths = [x * text_width / sum(minimums) for x in minimums]
            break
    return [round(x) for x in widths]


def finish_docx(path):
    """A4 pages, and tables Google Docs can read: Google ignores Word's conditional table styles, so the widths,
    borders and the shaded, bold header row are written into every table and cell."""
    with zipfile.ZipFile(path) as src:
        infos = src.infolist()
        files = {i.filename: src.read(i.filename) for i in infos}
    root = etree.fromstring(files["word/document.xml"])

    for sect in root.iter(w("sectPr")):
        for size in sect.findall(w("pgSz")):
            size.set(w("w"), str(A4_WIDTH))
            size.set(w("h"), str(A4_HEIGHT))
        for margin in sect.findall(w("pgMar")):
            for side in ("top", "bottom", "left", "right"):
                margin.set(w(side), str(MARGIN))
    text_width = A4_WIDTH - 2 * MARGIN

    for tbl in root.iter(w("tbl")):
        rows = tbl.findall(w("tr"))
        cells = [row.findall(w("tc")) for row in rows]
        widths = column_widths(cells, text_width)

        props = tbl.find(w("tblPr"))
        width = props.find(w("tblW"))
        width.set(w("type"), "pct")
        width.set(w("w"), "5000")
        props.find(w("tblLook")).addprevious(element("tblLayout", type="fixed"))
        grid = tbl.find(w("tblGrid"))
        for col, size in zip(grid.findall(w("gridCol")), widths):
            col.set(w("w"), str(size))

        for r, row in enumerate(cells):
            for c, cell in enumerate(row):
                tc_pr = cell.find(w("tcPr"))
                if tc_pr is None:
                    tc_pr = element("tcPr")
                    cell.insert(0, tc_pr)
                for child in list(tc_pr):
                    tc_pr.remove(child)
                tc_pr.append(element("tcW", w=widths[min(c, len(widths) - 1)], type="dxa"))
                borders = element("tcBorders")
                for side in ("top", "left", "bottom", "right"):
                    borders.append(element(side, val="single", sz=4, space=0, color=BORDER))
                tc_pr.append(borders)
                if r == 0:
                    tc_pr.append(element("shd", val="clear", color="auto", fill=HEADER_FILL))
                    for run in cell.iter(w("r")):
                        r_pr = run.find(w("rPr"))
                        if r_pr is None:
                            r_pr = element("rPr")
                            run.insert(0, r_pr)
                        if r_pr.find(w("b")) is None:  # w:b goes after w:rStyle and w:rFonts
                            anchor = [x for x in r_pr if x.tag in (w("rStyle"), w("rFonts"))]
                            if anchor:
                                anchor[-1].addnext(element("b"))
                            else:
                                r_pr.insert(0, element("b"))

    # Text that follows a table, a list or a code block would otherwise sit right against it.
    previous = None
    for block in root.find(w("body")):
        if previous is not None and block_kind(block) == "text" and block_kind(previous) in ("table", "list", "code"):
            space_before(block, AFTER_BLOCK)
        previous = block

    files["word/document.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in infos:
            dst.writestr(item, files[item.filename])


def main():
    os.makedirs(DIST, exist_ok=True)
    md = add_contents(build_markdown())
    for banned in ("Meridian", "meridian-"):
        assert banned not in md, f"'{banned}' is in the walkthrough"
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write(md)
    reference = os.path.join(DIST, ".walkthrough-reference.docx")
    reference_docx(reference)
    pypandoc.convert_file(OUT_MD, "docx", format="gfm", outputfile=OUT_DOCX, extra_args=[
        "--reference-doc", reference, "--metadata", f"title={TITLE}", "--metadata", f"subtitle={SUBTITLE}"])
    os.remove(reference)
    finish_docx(OUT_DOCX)
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} ({len(md.split()):,} words) and {os.path.relpath(OUT_DOCX, ROOT)}")


if __name__ == "__main__":
    main()
