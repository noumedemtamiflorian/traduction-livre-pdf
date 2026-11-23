#!/usr/bin/env python3
"""
book_pipeline.py — Universal CLI utility for the `traduction-livre-pdf` skill.

Subcommands:
  1. extract   : Extracts full text (page by page) and all embedded images from a source PDF.
  2. audit     : Audits completeness and fidelity between the source PDF and translated Markdown chapters.
  3. merge     : Merges translated Markdown chapters into a single unified Markdown book.
  4. build-pdf : Converts a unified Markdown book (with images and image-translation boxes)
                 into a print-ready A4 PDF and a standalone HTML file.

Works across Windows, macOS, and Linux, and with any AI model/agent.
"""

import argparse
import base64
import html
import json
import os
import pathlib
import re
import shutil
import sys


def cmd_extract(args):
    try:
        from pypdf import PdfReader
        from PIL import Image as PILImage
        import io
    except ImportError as exc:
        sys.stderr.write(
            f"Error: Missing Python dependency ({exc}).\n"
            "Run: python -m pip install pypdf reportlab Pillow\n"
        )
        sys.exit(1)

    pdf_path = pathlib.Path(args.pdf).resolve()
    if not pdf_path.exists():
        sys.stderr.write(f"Error: Source PDF not found: {pdf_path}\n")
        sys.exit(1)

    out_dir = pathlib.Path(args.out_dir).resolve()
    images_dir = out_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    text_chunks = []
    manifest_images = []
    img_counter = 0

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text() or ""
        text_chunks.append(f"=== PAGE {page_num} / {total_pages} ===\n{page_text}\n")

        try:
            page_images = page.images
        except Exception:
            page_images = []

        for img_file in page_images:
            img_counter += 1
            raw_data = img_file.data
            ext = pathlib.Path(img_file.name).suffix.lower() or ".jpg"
            width, height = 0, 0
            try:
                with PILImage.open(io.BytesIO(raw_data)) as pil_im:
                    width, height = pil_im.size
                    # Normalize to RGB JPEG for universal compatibility if needed
                    if ext not in (".jpg", ".jpeg", ".png"):
                        ext = ".jpg"
                    img_filename = f"page_{page_num:03d}_img_{img_counter:02d}{ext}"
                    img_out_path = images_dir / img_filename
                    if ext in (".jpg", ".jpeg") and pil_im.mode not in ("RGB", "L"):
                        pil_im = pil_im.convert("RGB")
                    pil_im.save(str(img_out_path))
            except Exception:
                img_filename = f"page_{page_num:03d}_img_{img_counter:02d}{ext}"
                img_out_path = images_dir / img_filename
                img_out_path.write_bytes(raw_data)

            manifest_images.append(
                {
                    "index": img_counter,
                    "page": page_num,
                    "filename": f"images/{img_filename}",
                    "original_name": img_file.name,
                    "width": width,
                    "height": height,
                    "bytes": len(raw_data),
                }
            )

    text_out_path = out_dir / "book_text.txt"
    text_out_path.write_text("\n".join(text_chunks), encoding="utf-8")

    manifest = {
        "source_pdf": str(pdf_path),
        "total_pages": total_pages,
        "extracted_text_file": str(text_out_path),
        "total_images_extracted": len(manifest_images),
        "images_dir": str(images_dir),
        "images": manifest_images,
    }
    manifest_path = out_dir / "extraction_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"Success! Extracted {total_pages} pages of text to '{text_out_path}' "
        f"and {len(manifest_images)} images to '{images_dir}'. "
        f"Manifest written to: '{manifest_path}'"
    )


def slugify(text):
    text = re.sub(r"[\*_`]", "", text)
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text


def cmd_merge(args):
    chapters_dir = pathlib.Path(args.chapters_dir).resolve()
    if not chapters_dir.exists():
        sys.stderr.write(f"Error: Chapters directory not found: {chapters_dir}\n")
        sys.exit(1)

    output_md = pathlib.Path(args.output).resolve()
    output_md.parent.mkdir(parents=True, exist_ok=True)

    # Find numbered chapter files like 00_Introduction.md, 01_Chapitre_1.md, etc.
    all_md = sorted(chapters_dir.glob("*.md"))
    chapter_files = []
    for p in all_md:
        name_upper = p.name.upper()
        if "INDEX" in name_upper or "RAPPORT" in name_upper or "AUDIT" in name_upper or "LIVRE_COMPLET" in name_upper or p.resolve() == output_md:
            continue
        if re.match(r"^\d{2}_", p.name):
            chapter_files.append(p)

    if not chapter_files:
        sys.stderr.write(f"Error: No numbered chapter files (e.g. 00_*.md, 01_*.md) found in {chapters_dir}\n")
        sys.exit(1)

    toc_lines = []
    chapter_contents = []
    for ch_file in chapter_files:
        txt = ch_file.read_text(encoding="utf-8").strip()
        chapter_contents.append(txt)
        m_h1 = re.search(r"^#\s+(.+)$", txt, flags=re.MULTILINE)
        if m_h1:
            h1_title = m_h1.group(1).strip()
            toc_lines.append(f"- [{h1_title}](#{slugify(h1_title)})")

    subtitle_line = f"## {args.subtitle}\n" if args.subtitle else ""
    header = (
        f"# {args.title}\n"
        f"{subtitle_line}"
        f"**Auteur :** {args.author}  \n"
        f"**Traduction intégrale (avec illustrations originales et traductions visuelles)**\n\n"
        f"---\n\n"
        f"## Table des matières\n\n"
        + "\n".join(toc_lines)
        + "\n\n---\n"
    )

    full_text = header + "\n\n---\n\n".join(chapter_contents) + "\n"
    output_md.write_text(full_text, encoding="utf-8")

    # Verify image references
    img_refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", full_text)
    missing_imgs = [src for src in img_refs if not (output_md.parent / src).exists() and not (chapters_dir / src).exists()]

    report = {
        "merged_chapters_count": len(chapter_files),
        "chapters": [p.name for p in chapter_files],
        "output_markdown": str(output_md),
        "total_characters": len(full_text),
        "total_images_referenced": len(img_refs),
        "missing_images": missing_imgs,
    }
    report_path = output_md.with_suffix(".merge_report.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if missing_imgs:
        sys.stderr.write(f"Warning: {len(missing_imgs)} referenced images were not found: {missing_imgs}\n")

    print(
        f"Success! Merged {len(chapter_files)} chapters ({len(img_refs)} images referenced) "
        f"into: '{output_md}'"
    )


def register_cross_platform_fonts():
    """Registers serif and sans-serif TrueType fonts across Windows, macOS, and Linux."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates_serif = [
        # Windows
        (
            r"C:\Windows\Fonts\georgia.ttf",
            r"C:\Windows\Fonts\georgiab.ttf",
            r"C:\Windows\Fonts\georgiai.ttf",
            r"C:\Windows\Fonts\georgiaz.ttf",
        ),
        # macOS
        (
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
            "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
            "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf",
        ),
        # Linux (DejaVu Serif)
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
        ),
        # Linux (Liberation Serif)
        (
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
        ),
    ]

    candidates_sans = [
        # Windows
        (
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\segoeuii.ttf",
            r"C:\Windows\Fonts\segoeuiz.ttf",
        ),
        # macOS
        (
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
        ),
        # Linux (DejaVu Sans)
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
        ),
    ]

    serif_name = "Times-Roman"
    serif_bold = "Times-Bold"
    serif_italic = "Times-Italic"

    for reg, bld, ita, bi in candidates_serif:
        if os.path.exists(reg) and os.path.exists(bld) and os.path.exists(ita) and os.path.exists(bi):
            pdfmetrics.registerFont(TTFont("BookSerif", reg))
            pdfmetrics.registerFont(TTFont("BookSerif-Bold", bld))
            pdfmetrics.registerFont(TTFont("BookSerif-Italic", ita))
            pdfmetrics.registerFont(TTFont("BookSerif-BoldItalic", bi))
            pdfmetrics.registerFontFamily(
                "BookSerif",
                normal="BookSerif",
                bold="BookSerif-Bold",
                italic="BookSerif-Italic",
                boldItalic="BookSerif-BoldItalic",
            )
            serif_name = "BookSerif"
            serif_bold = "BookSerif-Bold"
            serif_italic = "BookSerif-Italic"
            break

    sans_name = "Helvetica"
    sans_bold = "Helvetica-Bold"
    sans_italic = "Helvetica-Oblique"

    for reg, bld, ita, bi in candidates_sans:
        if os.path.exists(reg) and os.path.exists(bld) and os.path.exists(ita) and os.path.exists(bi):
            pdfmetrics.registerFont(TTFont("BookSans", reg))
            pdfmetrics.registerFont(TTFont("BookSans-Bold", bld))
            pdfmetrics.registerFont(TTFont("BookSans-Italic", ita))
            pdfmetrics.registerFont(TTFont("BookSans-BoldItalic", bi))
            pdfmetrics.registerFontFamily(
                "BookSans",
                normal="BookSans",
                bold="BookSans-Bold",
                italic="BookSans-Italic",
                boldItalic="BookSans-BoldItalic",
            )
            sans_name = "BookSans"
            sans_bold = "BookSans-Bold"
            sans_italic = "BookSans-Italic"
            break

    return (serif_name, serif_bold, serif_italic), (sans_name, sans_bold, sans_italic)


def cmd_build_pdf(args):
    try:
        from PIL import Image as PILImage
        from pypdf import PdfReader
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            HRFlowable,
            Image,
            KeepTogether,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:
        sys.stderr.write(
            f"Error: Missing Python dependency ({exc}).\n"
            "Run: python -m pip install pypdf reportlab Pillow\n"
        )
        sys.exit(1)

    input_md = pathlib.Path(args.input).resolve()
    if not input_md.exists():
        sys.stderr.write(f"Error: Input Markdown file not found: {input_md}\n")
        sys.exit(1)

    output_pdf = pathlib.Path(args.output).resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    base_dir = input_md.parent
    md_text = input_md.read_text(encoding="utf-8")

    (serif_reg, serif_bold, serif_ita), (sans_reg, sans_bold, sans_ita) = register_cross_platform_fonts()

    PAGE_WIDTH, PAGE_HEIGHT = A4
    LEFT_MARGIN = 20 * mm
    RIGHT_MARGIN = 20 * mm
    TOP_MARGIN = 22 * mm
    BOTTOM_MARGIN = 22 * mm
    CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

    style_body = ParagraphStyle(
        "BookBody",
        fontName=serif_reg,
        fontSize=10.8,
        leading=16.2,
        textColor=colors.HexColor("#1a1a1a"),
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )
    style_h1_main = ParagraphStyle(
        "BookTitleMain",
        fontName=sans_bold,
        fontSize=22,
        leading=28,
        textColor=colors.HexColor("#111827"),
        alignment=TA_CENTER,
        spaceBefore=6,
        spaceAfter=10,
        keepWithNext=True,
    )
    style_h1 = ParagraphStyle(
        "BookH1",
        fontName=sans_bold,
        fontSize=18,
        leading=23,
        textColor=colors.HexColor("#111827"),
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=10,
        keepWithNext=True,
    )
    style_h2 = ParagraphStyle(
        "BookH2",
        fontName=sans_bold,
        fontSize=13.5,
        leading=18,
        textColor=colors.HexColor("#92400e"),
        alignment=TA_LEFT,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    style_h3 = ParagraphStyle(
        "BookH3",
        fontName=sans_bold,
        fontSize=11.5,
        leading=15.5,
        textColor=colors.HexColor("#374151"),
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    style_caption = ParagraphStyle(
        "BookCaption",
        fontName=sans_ita,
        fontSize=9.2,
        leading=13,
        textColor=colors.HexColor("#4b5563"),
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=6,
    )
    style_bq = ParagraphStyle(
        "BookBlockquote",
        fontName=serif_reg,
        fontSize=10.2,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
        alignment=TA_LEFT,
        spaceAfter=5,
    )
    style_img_trans_title = ParagraphStyle(
        "ImgTransTitle",
        fontName=sans_bold,
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#92400e"),
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    style_img_trans_item = ParagraphStyle(
        "ImgTransItem",
        fontName=sans_reg,
        fontSize=9.2,
        leading=13.2,
        textColor=colors.HexColor("#1f2937"),
        alignment=TA_LEFT,
        leftIndent=10,
        firstLineIndent=-8,
        spaceAfter=2.5,
    )
    style_list_item = ParagraphStyle(
        "BookListItem",
        fontName=serif_reg,
        fontSize=10.5,
        leading=15.5,
        textColor=colors.HexColor("#1a1a1a"),
        alignment=TA_JUSTIFY,
        leftIndent=16,
        firstLineIndent=-10,
        spaceAfter=4,
    )
    style_sublist_item = ParagraphStyle(
        "BookSubListItem",
        fontName=serif_reg,
        fontSize=10.0,
        leading=14.5,
        textColor=colors.HexColor("#374151"),
        alignment=TA_LEFT,
        leftIndent=30,
        firstLineIndent=-10,
        spaceAfter=3,
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        fontName=sans_bold,
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#92400e"),
        alignment=TA_LEFT,
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        fontName=sans_reg,
        fontSize=9.2,
        leading=13,
        textColor=colors.HexColor("#1f2937"),
        alignment=TA_LEFT,
    )

    def md_inline_to_rl(text):
        text = text.replace("&#42;", "@@ASTERISK@@")
        text = html.escape(text, quote=False)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
        text = text.replace("^&amp;*", "^&amp;@@ASTERISK@@")
        text = re.sub(r"\*\*\*([^*]+?)\*\*\*", r"<b><i>\1</i></b>", text)
        text = re.sub(r"\*\*([^*]+?)\*([^*]+?)\*\*\*", r"<b>\1<i>\2</i></b>", text)

        def repl_bold(m):
            inner = m.group(1)
            inner = re.sub(r"\*([^*]+?)\*", r"<i>\1</i>", inner)
            return f"<b>{inner}</b>"

        text = re.sub(r"\*\*(.+?)\*\*", repl_bold, text)
        text = re.sub(r"\*([^*]+?)\*", r"<i>\1</i>", text)
        text = text.replace("@@ASTERISK@@", "*")

        sub_map = {"₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8"}
        for k, v in sub_map.items():
            text = text.replace(k, f'<font size="7">{v}</font>')

        for sym in ["→", "☆☆☆☆☆", "●", "•"]:
            if sym in text:
                text = text.replace(sym, f'<font name="{sans_reg}">{sym}</font>')
        return text

    def resolve_image_path(src_rel):
        cand1 = base_dir / src_rel
        if cand1.exists():
            return cand1
        cand2 = output_pdf.parent / src_rel
        if cand2.exists():
            return cand2
        return cand1

    def create_image_flowable(src_rel, caption_text=None):
        img_path = resolve_image_path(src_rel)
        if not img_path.exists():
            return [Paragraph(f"[Image manquante : {html.escape(src_rel)}]", style_caption)]

        with PILImage.open(img_path) as im:
            orig_w, orig_h = im.size

        if "00_couverture" in src_rel or "cover" in src_rel.lower():
            max_w, max_h = 115 * mm, 165 * mm
        elif any(k in src_rel for k in ("tri_metre", "zone_", "ajustements", "impasse")):
            max_w, max_h = 105 * mm, 105 * mm
        else:
            max_w, max_h = 145 * mm, 115 * mm

        scale = min(max_w / orig_w, max_h / orig_h)
        rl_img = Image(str(img_path), width=orig_w * scale, height=orig_h * scale)
        rl_img.hAlign = "CENTER"

        elems = [Spacer(1, 4), rl_img]
        if caption_text:
            elems.append(Paragraph(md_inline_to_rl(caption_text), style_caption))
        else:
            elems.append(Spacer(1, 4))
        return elems

    def render_blockquote(bq_lines):
        raw_joined = "\n".join(bq_lines)
        is_img_trans = (
            "Traduction du texte" in raw_joined
            or "Traduction des inscriptions" in raw_joined
            or "Image Text Translation" in raw_joined
        )
        inner_flowables = []
        for line in bq_lines:
            s = line.strip()
            if not s:
                continue
            m_ul = re.match(r"^(\s*)[*\-]\s+(.*)$", line)
            if m_ul:
                indent_len = len(m_ul.group(1))
                content = md_inline_to_rl(m_ul.group(2).strip())
                if is_img_trans:
                    st = ParagraphStyle(
                        "ImgTransNested",
                        parent=style_img_trans_item,
                        leftIndent=10 + (indent_len * 5),
                    )
                    b_char = f'<font name="{sans_reg}">•</font>' if indent_len == 0 else f'<font name="{sans_reg}">–</font>'
                    inner_flowables.append(Paragraph(f"{b_char} {content}", st))
                else:
                    inner_flowables.append(Paragraph(f'<font name="{sans_reg}">•</font> {content}', style_bq))
            else:
                content = md_inline_to_rl(s)
                inner_flowables.append(Paragraph(content, style_img_trans_title if is_img_trans else style_bq))

        if not inner_flowables:
            return []

        bg_color = colors.HexColor("#fffbeb") if is_img_trans else colors.HexColor("#f9fafb")
        border_color = colors.HexColor("#f59e0b") if is_img_trans else colors.HexColor("#9ca3af")
        tbl = Table([[inner_flowables]], colWidths=[CONTENT_WIDTH - 4 * mm])
        t_style = [
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("LINEBEFORE", (0, 0), (0, -1), 3, border_color),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]
        if is_img_trans:
            t_style.append(("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fde68a")))
        tbl.setStyle(TableStyle(t_style))
        return [Spacer(1, 2), tbl, Spacer(1, 8)]

    lines = md_text.splitlines()
    story = []
    i = 0
    n = len(lines)
    first_h1 = True

    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        if stripped in ("---", "***", "___"):
            story.append(Spacer(1, 4))
            story.append(
                HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#d1d5db"), spaceBefore=4, spaceAfter=8)
            )
            i += 1
            continue

        m_head = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m_head:
            level = len(m_head.group(1))
            title_txt = md_inline_to_rl(m_head.group(2).strip())
            if level == 1:
                if first_h1:
                    story.append(Paragraph(title_txt, style_h1_main))
                    first_h1 = False
                else:
                    story.append(PageBreak())
                    story.append(Paragraph(title_txt, style_h1))
                    story.append(
                        HRFlowable(width="100%", thickness=2, color=colors.HexColor("#f59e0b"), spaceBefore=0, spaceAfter=10)
                    )
            elif level == 2:
                story.append(Paragraph(title_txt, style_h2))
            else:
                story.append(Paragraph(title_txt, style_h3))
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            headers = [c.strip() for c in stripped.strip("|").split("|")]
            num_cols = len(headers)
            rows_data = [[Paragraph(md_inline_to_rl(h), style_table_header) for h in headers]]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                while len(cells) < num_cols:
                    cells.append("")
                cells = cells[:num_cols]
                rows_data.append([Paragraph(md_inline_to_rl(c), style_table_cell) for c in cells])
                i += 1

            col_w = CONTENT_WIDTH / num_cols
            tbl = Table(rows_data, colWidths=[col_w] * num_cols, repeatRows=1)
            t_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef3c7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
            for r_idx in range(1, len(rows_data)):
                if r_idx % 2 == 0:
                    t_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), colors.HexColor("#f9fafb")))
            tbl.setStyle(TableStyle(t_style))
            story.append(Spacer(1, 4))
            story.append(tbl)
            story.append(Spacer(1, 8))
            continue

        m_img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if m_img:
            src_p = m_img.group(2)
            caption_t = None
            if i + 1 < n and re.match(r"^\*[^*]+\*$", lines[i + 1].strip()):
                caption_t = lines[i + 1].strip()
                i += 2
            else:
                i += 1

            img_elems = create_image_flowable(src_p, caption_t)
            temp_i = i
            while temp_i < n and not lines[temp_i].strip():
                temp_i += 1
            if temp_i < n and lines[temp_i].strip().startswith(">"):
                bq_lines = []
                k = temp_i
                while k < n and lines[k].strip().startswith(">"):
                    bq_lines.append(re.sub(r"^\s*>\s?", "", lines[k]))
                    k += 1
                bq_joined = "\n".join(bq_lines)
                if "Traduction du texte" in bq_joined or "Traduction des inscriptions" in bq_joined:
                    bq_elems = render_blockquote(bq_lines)
                    story.append(KeepTogether(img_elems + bq_elems))
                    i = k
                    continue

            story.append(KeepTogether(img_elems))
            continue

        if stripped.startswith(">"):
            bq_lines = []
            while i < n and lines[i].strip().startswith(">"):
                bq_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            story.extend(render_blockquote(bq_lines))
            continue

        m_ul = re.match(r"^(\s*)([*\-])\s+(.*)$", line)
        m_ol = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if m_ul or m_ol:
            while i < n:
                l = lines[i]
                if not l.strip():
                    if i + 1 < n and (
                        re.match(r"^(\s*)([*\-]|\d+\.)\s+", lines[i + 1]) or lines[i + 1].startswith("  ")
                    ):
                        i += 1
                        continue
                    else:
                        break
                mu = re.match(r"^(\s*)([*\-])\s+(.*)$", l)
                mo = re.match(r"^(\s*)(\d+)\.\s+(.*)$", l)
                if mu:
                    indent = len(mu.group(1))
                    txt = md_inline_to_rl(mu.group(3).strip())
                    st = style_sublist_item if indent >= 2 else style_list_item
                    b_sym = f'<font name="{sans_reg}">–</font>' if indent >= 2 else f'<font name="{sans_reg}">•</font>'
                    story.append(Paragraph(f"{b_sym} {txt}", st))
                    i += 1
                elif mo:
                    indent = len(mo.group(1))
                    num_str = mo.group(2)
                    txt = md_inline_to_rl(mo.group(3).strip())
                    st = style_sublist_item if indent >= 2 else style_list_item
                    story.append(Paragraph(f"<b>{num_str}.</b> {txt}", st))
                    i += 1
                elif l.startswith("  "):
                    sub_s = l.strip()
                    if sub_s.startswith(">"):
                        sub_txt = md_inline_to_rl(re.sub(r"^>\s?", "", sub_s))
                        story.append(Paragraph(f"<i>{sub_txt}</i>", style_sublist_item))
                    else:
                        story.append(Paragraph(md_inline_to_rl(sub_s), style_sublist_item))
                    i += 1
                else:
                    break
            story.append(Spacer(1, 4))
            continue

        para_lines = []
        while i < n:
            l = lines[i]
            s = l.strip()
            if (
                not s
                or s in ("---", "***", "___")
                or re.match(r"^(#{1,6})\s+", s)
                or s.startswith(">")
                or re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", s)
                or (s.startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]))
                or re.match(r"^(\s*)([*\-]|\d+\.)\s+", l)
            ):
                break
            if l.endswith("  "):
                para_lines.append(md_inline_to_rl(s) + "<br/>")
            else:
                para_lines.append(md_inline_to_rl(s))
            i += 1
        if para_lines:
            story.append(Paragraph(" ".join(para_lines), style_body))

    running_header = f"{args.title} — {args.author}"

    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        if page_num > 1:
            canvas.saveState()
            canvas.setFont(sans_reg, 9)
            canvas.setFillColor(colors.HexColor("#6b7280"))
            canvas.drawCentredString(PAGE_WIDTH / 2.0, 12 * mm, f"— {page_num} —")
            canvas.drawString(LEFT_MARGIN, PAGE_HEIGHT - 14 * mm, running_header)
            canvas.setStrokeColor(colors.HexColor("#e5e7eb"))
            canvas.setLineWidth(0.5)
            canvas.line(LEFT_MARGIN, PAGE_HEIGHT - 16 * mm, PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 16 * mm)
            canvas.restoreState()

    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=args.title,
        author=args.author,
    )
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    # Verify output PDF
    reader = PdfReader(str(output_pdf))
    total_pages = len(reader.pages)
    embedded_imgs = sum(len(p.images) for p in reader.pages)

    report = {
        "output_pdf": str(output_pdf),
        "file_size_bytes": output_pdf.stat().st_size,
        "total_pages": total_pages,
        "embedded_images_count": embedded_imgs,
    }
    report_path = output_pdf.with_suffix(".pdf_report.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"Success! Generated PDF '{output_pdf}' "
        f"({total_pages} pages, {embedded_imgs} embedded images, {output_pdf.stat().st_size} bytes)."
    )


def cmd_audit(args):
    """
    Audits the completeness and fidelity between the source PDF and translated Markdown chapters.
    Calculates expansion ratios, checks for missing sections from the PDF outline,
    flags prohibited code blocks, and verifies image coverage.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        sys.stderr.write(
            f"Error: Missing Python dependency ({exc}).\n"
            "Run: python -m pip install pypdf reportlab Pillow\n"
        )
        sys.exit(1)

    pdf_path = pathlib.Path(args.pdf).resolve()
    chapters_dir = pathlib.Path(args.chapters_dir).resolve()

    if not pdf_path.exists():
        sys.stderr.write(f"Error: Source PDF not found: {pdf_path}\n")
        sys.exit(1)

    if not chapters_dir.exists():
        sys.stderr.write(f"Error: Chapters dir not found: {chapters_dir}\n")
        sys.exit(1)

    reader = PdfReader(str(pdf_path))
    total_pdf_pages = len(reader.pages)

    # Extract page text
    pages_text = [p.extract_text() or "" for p in reader.pages]
    total_src_words = sum(len(txt.split()) for txt in pages_text)

    # Parse PDF Outline
    outline = []
    def parse_items(items, depth=1):
        for it in items:
            if isinstance(it, list):
                parse_items(it, depth + 1)
            else:
                try:
                    p = reader.get_destination_page_number(it)
                    outline.append({'depth': depth, 'title': it.title, 'page': p + 1})
                except Exception:
                    pass
    if reader.outline:
        parse_items(reader.outline)

    # Get translated markdown chapter files
    md_files = sorted([
        f for f in chapters_dir.glob("*.md")
        if not f.name.startswith("00_INDEX")
        and not f.name.startswith("00_RAPPORT")
        and not f.name.startswith("LIVRE_COMPLET")
    ])

    # Identify chapter anchors from outline
    anchors = []
    intro_start = None
    for o in outline:
        title_lower = o['title'].lower()
        if any(w in title_lower for w in ['prelude', 'introduction', 'overview', 'foreword', 'preface']):
            if intro_start is None:
                intro_start = o['page']
    if intro_start is None:
        intro_start = 1
    anchors.append(('00', 'Introduction / Prelude', intro_start))

    for o in outline:
        title = o['title']
        m = re.match(r'^(?:Chapter\s+|Part\s+)?([0-9]+)\s*[:\.\-]\s*(.*)$', title, re.IGNORECASE)
        if m:
            ch_num = int(m.group(1))
            ch_prefix = f"{ch_num:02d}"
            anchors.append((ch_prefix, title, o['page']))

    # Fallback if no numbered chapters detected in outline
    if len(anchors) <= 1 and md_files:
        anchors = []
        for idx, f in enumerate(md_files):
            prefix = f.name[:2] if f.name[:2].isdigit() else f"{idx:02d}"
            anchors.append((prefix, f.stem, 1))

    chapter_audits = []
    total_trans_words = 0
    total_code_blocks = 0
    total_images_found = 0
    total_image_boxes_found = 0
    has_critical_failure = False

    min_ratio = getattr(args, 'min_ratio', 1.05)

    for idx, anc in enumerate(anchors):
        ch_num = anc[0]
        ch_title = anc[1]
        p_start = anc[2]
        p_end = anchors[idx+1][2] - 1 if idx + 1 < len(anchors) else total_pdf_pages

        # Subheadings in outline for this chapter
        subs = [o['title'] for o in outline if p_start <= o['page'] <= p_end and o['title'] != ch_title]

        # Source words in this range
        src_words = sum(len(pages_text[p-1].split()) for p in range(p_start, min(p_end, total_pdf_pages) + 1))

        # Matching markdown file
        matching_md = None
        for f in md_files:
            if f.name.startswith(f"{ch_num}_") or f.name == f"{ch_num}.md":
                matching_md = f
                break

        trans_words = 0
        trans_chars = 0
        code_blocks_count = 0
        img_refs = []
        img_boxes = 0
        md_headings = []
        file_present = matching_md is not None

        if matching_md:
            text = matching_md.read_text(encoding='utf-8')
            trans_words = len(text.split())
            trans_chars = len(text)
            total_trans_words += trans_words

            # Code block check (```)
            code_blocks = re.findall(r'```[a-zA-Z0-9_-]*\n', text)
            code_blocks_count = len(code_blocks)
            total_code_blocks += code_blocks_count

            # Images check
            img_refs = re.findall(r'!\[.*?\]\((.*?)\)', text)
            total_images_found += len(img_refs)

            # Translation boxes
            img_boxes = len(re.findall(r'>\s*\*\*Traduction (?:du texte|des inscriptions) présent', text, re.IGNORECASE))
            total_image_boxes_found += img_boxes

            # MD headings
            md_headings = [line.lstrip('#').strip() for line in text.splitlines() if line.strip().startswith('#')]

        ratio = (trans_words / src_words) if src_words > 0 else 0

        # Determine status
        if not file_present:
            status = "CRITIQUE (Fichier Manquant)"
            badge = "🔴 MANQUANT"
            has_critical_failure = True
        elif ratio < 0.88:
            status = "CRITIQUE (Fortement Tronqué / Résumé)"
            badge = "🔴 COUPÉ"
            has_critical_failure = True
        elif ratio < min_ratio:
            status = "ATTENTION (Condensé ou Résumé Partiel)"
            badge = "🟡 CONDENSÉ"
        elif ratio > 1.60:
            status = "ATTENTION (Volume Anormalement Élevé)"
            badge = "🟡 VOLUMINEUX"
        else:
            status = "CONFORME (Traduction Intégrale Respectée)"
            badge = "🟢 CONFORME"

        chapter_audits.append({
            "chapter_num": ch_num,
            "title": ch_title,
            "file": matching_md.name if matching_md else None,
            "page_range": f"p.{p_start}-{p_end}",
            "source_words": src_words,
            "translated_words": trans_words,
            "expansion_ratio": round(ratio, 2),
            "status": status,
            "badge": badge,
            "code_blocks": code_blocks_count,
            "images_count": len(img_refs),
            "image_translation_boxes": img_boxes,
            "source_subheadings_count": len(subs),
            "source_subheadings": subs,
            "translated_headings": md_headings
        })

    global_ratio = (total_trans_words / total_src_words) if total_src_words > 0 else 0
    if global_ratio < 0.90:
        global_status = "🔴 ÉCHEC GLOBAL : Le document est tronqué d'au moins 20-30% par rapport à l'original."
    elif global_ratio < min_ratio:
        global_status = f"🟡 ATTENTION GLOBALE : Le volume traduit ({global_ratio:.2f}x) est inférieur au seuil recommandé ({min_ratio:.2f}x)."
    else:
        global_status = "🟢 CONFORME GLOBAL : Le volume global correspond à une traduction intégrale rigoureuse."

    # Print Console Report
    print("=" * 80)
    print(" AUDIT D'INTÉGRITÉ ET DE COMPLÉTUDE DE LA TRADUCTION")
    print("=" * 80)
    print(f"Livre original : {pdf_path.name} ({total_pdf_pages} pages, {total_src_words:,} mots)")
    print(f"Dossier cible  : {chapters_dir.name} ({len(md_files)} chapitres, {total_trans_words:,} mots)")
    print(f"Ratio global   : {global_ratio:.2f}x (Seuil minimal attendu : {min_ratio:.2f}x)")
    print(f"Statut global  : {global_status}")
    print("-" * 80)

    header = f"{'CH':<4} | {'TITRE':<28} | {'SRC':<7} | {'TRAD':<7} | {'RATIO':<6} | {'IMAGES':<6} | {'CODE':<5} | {'STATUT'}"
    print(header)
    print("-" * 80)
    for c in chapter_audits:
        title_disp = (c['title'][:25] + "...") if len(c['title']) > 28 else c['title']
        row = f"{c['chapter_num']:<4} | {title_disp:<28} | {c['source_words']:<7} | {c['translated_words']:<7} | {c['expansion_ratio']:<6.2f} | {c['images_count']:<6} | {c['code_blocks']:<5} | {c['badge']}"
        print(row)
    print("-" * 80)
    print(f"Images détectées : {total_images_found} (avec {total_image_boxes_found} encadrés de traduction visuelle)")
    if total_code_blocks > 0:
        print(f"⚠️ AVERTISSEMENT : {total_code_blocks} blocs de code informatique (```) détectés ! (Doivent être remplacés par des citations ou tableaux)")
    print("=" * 80)

    # Save JSON report
    report_json = args.report_json
    if not report_json:
        report_json = chapters_dir / "audit_report.json"
    else:
        report_json = pathlib.Path(report_json).resolve()

    audit_data = {
        "source_pdf": str(pdf_path),
        "total_source_pages": total_pdf_pages,
        "total_source_words": total_src_words,
        "total_translated_words": total_trans_words,
        "global_expansion_ratio": round(global_ratio, 2),
        "min_required_ratio": min_ratio,
        "global_status": global_status,
        "total_code_blocks_prohibited": total_code_blocks,
        "total_images": total_images_found,
        "total_image_translation_boxes": total_image_boxes_found,
        "has_critical_failure": has_critical_failure,
        "chapters": chapter_audits
    }
    report_json.write_text(json.dumps(audit_data, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Rapport JSON enregistré : '{report_json}'")

    # Save Markdown report
    report_md = args.report_md
    if not report_md:
        report_md = chapters_dir / "00_RAPPORT_AUDIT_COMPLETUDE.md"
    else:
        report_md = pathlib.Path(report_md).resolve()

    md_lines = [
        f"# Rapport d'Audit de Complétude et d'Intégrité de Traduction",
        f"",
        f"> **Document source :** `{pdf_path.name}` ({total_pdf_pages} pages, {total_src_words:,} mots)  ",
        f"> **Traduction française :** {total_trans_words:,} mots  ",
        f"> **Ratio de foisonnement global :** **{global_ratio:.2f}x** (Norme FR attendue : ≥ {min_ratio:.2f}x)  ",
        f"> **Verdict global :** {global_status}",
        f"",
        f"---",
        f"",
        f"## Tableau Récapitulatif par Chapitre",
        f"",
        f"| Chapitre | Titre Source | Pages | Mots Anglais | Mots Français | Ratio | Images | Blocs Code | Évaluation |",
        f"| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |"
    ]
    for c in chapter_audits:
        md_lines.append(
            f"| **{c['chapter_num']}** | {c['title']} | {c['page_range']} | {c['source_words']:,} | {c['translated_words']:,} | **{c['expansion_ratio']:.2f}** | {c['images_count']} ({c['image_translation_boxes']} trad.) | {c['code_blocks']} | {c['badge']} |"
        )
    md_lines.extend([
        f"",
        f"---",
        f"",
        f"## Diagnostic Détaillé et Sections Manquantes",
        f""
    ])
    for c in chapter_audits:
        if c['badge'].startswith("🔴") or c['badge'].startswith("🟡"):
            md_lines.append(f"### Chapitre {c['chapter_num']} : {c['title']} ({c['badge']})")
            md_lines.append(f"- **Fichier :** `{c['file']}`")
            md_lines.append(f"- **Déficit estimé :** {max(0, int(c['source_words'] * 1.15 - c['translated_words']))} mots manquants pour atteindre le standard d'intégralité.")
            if c['source_subheadings']:
                md_lines.append(f"- **Sous-sections sources identifiées dans l'ouvrage original :**")
                for s in c['source_subheadings']:
                    md_lines.append(f"  - `{s}`")
            md_lines.append("")

    report_md.write_text("\n".join(md_lines), encoding='utf-8')
    print(f"Rapport Markdown enregistré : '{report_md}'")

    if args.strict and has_critical_failure:
        sys.stderr.write("\n❌ ERREUR STRICTE : Des chapitres tronqués ou manquants ont été détectés. Fusion bloquée.\n")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Universal CLI pipeline for translating illustrated PDF books (traduction-livre-pdf skill)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. extract
    p_ext = subparsers.add_parser("extract", help="Extract text and embedded images from source PDF.")
    p_ext.add_argument("--pdf", required=True, help="Path to source PDF file.")
    p_ext.add_argument("--out-dir", required=True, help="Directory to save book_text.txt, images/, and manifest.")
    p_ext.set_defaults(func=cmd_extract)

    # 2. audit (or verify)
    p_aud = subparsers.add_parser("audit", aliases=["verify", "check"], help="Audit completeness and fidelity between source PDF and translated chapters.")
    p_aud.add_argument("--pdf", required=True, help="Path to source PDF file.")
    p_aud.add_argument("--chapters-dir", required=True, help="Directory containing numbered chapter .md files.")
    p_aud.add_argument("--min-ratio", type=float, default=1.05, help="Minimum acceptable word expansion ratio (default: 1.05).")
    p_aud.add_argument("--strict", action="store_true", help="Fail with exit code 1 if any chapter is cut or missing.")
    p_aud.add_argument("--report-md", default=None, help="Custom output path for Markdown audit report.")
    p_aud.add_argument("--report-json", default=None, help="Custom output path for JSON audit report.")
    p_aud.set_defaults(func=cmd_audit)

    # 3. merge
    p_mrg = subparsers.add_parser("merge", help="Merge translated Markdown chapters into a unified book.")
    p_mrg.add_argument("--chapters-dir", required=True, help="Directory containing numbered chapter .md files.")
    p_mrg.add_argument("--output", required=True, help="Path for the merged Markdown file.")
    p_mrg.add_argument("--title", required=True, help="Translated book title.")
    p_mrg.add_argument("--subtitle", default="", help="Translated book subtitle (optional).")
    p_mrg.add_argument("--author", required=True, help="Book author name.")
    p_mrg.set_defaults(func=cmd_merge)

    # 4. build-pdf
    p_pdf = subparsers.add_parser("build-pdf", help="Build a print-ready A4 PDF from the merged Markdown book.")
    p_pdf.add_argument("--input", required=True, help="Path to merged Markdown file.")
    p_pdf.add_argument("--output", required=True, help="Path to output PDF file.")
    p_pdf.add_argument("--title", required=True, help="Book title for PDF metadata and running header.")
    p_pdf.add_argument("--author", required=True, help="Book author for PDF metadata and running header.")
    p_pdf.set_defaults(func=cmd_build_pdf)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
