import re
import sys
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


import re
import sys
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls


def add_bottom_border(paragraph):
    """Adds a crisp hairline border directly under section headings."""
    pPr = paragraph._element.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')  # 0.75 pt
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '333333')
    pBdr.append(bottom)
    pPr.append(pBdr)


def add_right_tab(paragraph, right_margin_in_inches=7.5):
    """Sets an explicit right-aligned tab stop at the right margin boundary."""
    pPr = paragraph._element.get_or_add_pPr()
    tabs = OxmlElement('w:tabs')
    tab = OxmlElement('w:tab')
    tab.set(qn('w:val'), 'right')
    tab.set(qn('w:pos'), str(int(right_margin_in_inches * 1440)))  # 1440 dxa per inch (7.5" = 10800)
    tabs.append(tab)
    pPr.append(tabs)


def parse_inline_formatting(paragraph, text, base_font_size=11, bold_all=False, italic_all=False):
    """Parses markdown bold (**text**) and italic (*text*) spans cleanly."""
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
    for token in tokens:
        if not token:
            continue
        is_bold = bold_all or token.startswith('**')
        is_italic = italic_all or (token.startswith('*') and not token.startswith('**'))
        cleaned = token.strip('*')

        run = paragraph.add_run(cleaned)
        run.font.name = 'Calibri'
        run.font.size = Pt(base_font_size)
        run.font.color.rgb = RGBColor(30, 30, 30)
        run.bold = is_bold
        run.italic = is_italic

def add_two_column_row(doc, left_text, right_text, space_before_pt=3, space_after_pt=0, base_font_size=10):
    """Creates a seamless, borderless 2-column container for title and right-aligned date/meta."""
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.autofit = False

    # Lock column widths: 5.5 inches left, 2.0 inches right (total 7.5" printable width)
    table.columns[0].width = Inches(5.5)
    table.columns[1].width = Inches(2.0)

    # Strip default table borders and internal margins
    tblPr = table._tbl.tblPr
    borders_xml = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="none"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders_xml)

    # Strip cell margins (padding) so text aligns flush with margins
    tblCellMar = parse_xml(
        f'<w:tblCellMar {nsdecls("w")}>'
        f'  <w:top w:w="0" w:type="dxa"/>'
        f'  <w:left w:w="0" w:type="dxa"/>'
        f'  <w:bottom w:w="0" w:type="dxa"/>'
        f'  <w:right w:w="0" w:type="dxa"/>'
        f'</w:tblCellMar>'
    )
    tblPr.append(tblCellMar)

    # Left Cell: School / Company / Project Title (Bold, Left-Aligned)
    p_left = table.cell(0, 0).paragraphs[0]
    p_left.paragraph_format.space_before = Pt(space_before_pt)
    p_left.paragraph_format.space_after = Pt(space_after_pt)
    p_left.paragraph_format.line_spacing = 1.0
    parse_inline_formatting(p_left, left_text, base_font_size=base_font_size, bold_all=True)

    # Right Cell: Date / Location (Right-Aligned, Italic)
    p_right = table.cell(0, 1).paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_right.paragraph_format.space_before = Pt(space_before_pt)
    p_right.paragraph_format.space_after = Pt(space_after_pt)
    p_right.paragraph_format.line_spacing = 1.0
    run_right = p_right.add_run(right_text)
    run_right.font.name = 'Calibri'
    run_right.font.size = Pt(base_font_size)
    run_right.italic = True
    run_right.font.color.rgb = RGBColor(30, 30, 30)


def markdown_to_docx(md_path: Path, docx_path: Path):
    doc = Document()

    # 0.5" Margins for standard single-page engineering layout
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11.0)
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)
    usable_width = 7.5

    raw_content = md_path.read_text(encoding='utf-8')
    # Collapse broken newlines in bullets like "- **\nAction**"
    normalized_content = re.sub(r'([-\*]\s*\*\*)\s*\n\s*', r'\1', raw_content)
    lines = normalized_content.splitlines()

    current_section = ""

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line == '---':
            continue

        # 1. Candidate Name (Header 1)
        if line.startswith('# '):
            name_text = re.sub(r'^[#\s\*]+|[\*\s]+$', '', line)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            run = p.add_run(name_text)
            run.font.name = 'Calibri'
            run.font.size = Pt(16)
            run.bold = True
            run.font.color.rgb = RGBColor(15, 23, 42)

        # 2. Contact Info Line (Email, LinkedIn, Phone)
        elif ('@' in line or 'linkedin.com' in line or 'github.com' in line) and not line.startswith(('-', '*')):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.0
            parse_inline_formatting(p, line, base_font_size=11)

        # 3. Section Headings (e.g., ### TECHNICAL & ROBOTICS PROJECTS)
        elif line.startswith(('## ', '### ')) and not ('|' in line or '—' in line or '\t' in line):
            heading_text = re.sub(r'^[#\s\*]+|[\*\s]+$', '', line)
            current_section = heading_text.upper()

            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(current_section)
            run.font.name = 'Calibri'
            run.font.size = Pt(11)
            run.bold = True
            run.font.color.rgb = RGBColor(20, 20, 20)
            add_bottom_border(p)

        # 4. Project Titles, School Names, or Job Titles with Right-Aligned Meta/Stack
        elif ('|' in line or '—' in line) and not line.startswith(('-', '*')):
            cleaned_line = re.sub(r'^[#\s]+', '', line)
            parts = [pt.strip() for pt in re.split(r'\s*\|\s*', cleaned_line)]

            if len(parts) >= 2:
                # ALL parts except the last one stay on the LEFT
                left_content = " | ".join(parts[:-1])
                # ONLY the final part (the date/year) goes on the RIGHT
                right_meta = parts[-1]

                add_two_column_row(doc, left_content, right_meta, space_before_pt=3, space_after_pt=0,
                                   base_font_size=10)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(3)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                parse_inline_formatting(p, cleaned_line, base_font_size=10, bold_all=True)
                
        # 5. Bullet Points (Accomplishments / Responsibilities)
        elif line.startswith('-'):
            bullet_text = re.sub(r'^[-*]\s+', '', line)

            if "EDUCATION" in current_section and ("Coursework" in bullet_text or "GPA" in bullet_text):
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.line_spacing = 1.0
                parse_inline_formatting(p, bullet_text, base_font_size=11)
            else:
                p = doc.add_paragraph(style='List Bullet')
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.left_indent = Inches(0.5)
                parse_inline_formatting(p, bullet_text, base_font_size=11)

        # 6. Plain Text / Skills Block
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0.5)
            p.paragraph_format.line_spacing = 1.0
            is_sub = any(kw in line for kw in ["Master", "Bachelor", "Fulfillment", "Associate Banker"])
            parse_inline_formatting(p, line, base_font_size=11, italic_all=is_sub)

    doc.save(docx_path)
    print(f"Generated DOCX: {docx_path}")


if __name__ == '__main__':
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output/Jared Ocotlan Garcia - zendar_resume.md")
    markdown_to_docx(target, target.with_suffix('.docx'))

