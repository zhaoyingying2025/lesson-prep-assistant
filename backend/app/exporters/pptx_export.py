"""教学PPT渲染引擎 - 根据LLM生成的幻灯片结构渲染为PPTX

支持多种视觉风格：
- academic: 学术简约（蓝白配色）
- cyan_ink: 青绿水墨（传统水墨）
- cute_cartoon: 清新卡通（温暖活泼）
- formal: 商务正式（深色稳重）
- minimal: 极简黑白（黑白灰）
"""
from __future__ import annotations

import io
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu


# ============ 风格配色方案 ============
STYLE_COLORS = {
    "academic": {
        "bg": RGBColor(0xFF, 0xFF, 0xFF),
        "bg_alt": RGBColor(0xF0, 0xF4, 0xFA),
        "primary": RGBColor(0x1A, 0x56, 0xDB),     # 蓝
        "primary_dark": RGBColor(0x0F, 0x3B, 0x9E),
        "primary_light": RGBColor(0xD6, 0xE4, 0xFD),
        "accent": RGBColor(0xE8, 0x6C, 0x00),       # 橙
        "text": RGBColor(0x1A, 0x1A, 0x2E),
        "text_light": RGBColor(0x6B, 0x72, 0x88),
        "text_white": RGBColor(0xFF, 0xFF, 0xFF),
        "rule": RGBColor(0xE0, 0xE5, 0xEE),
        "highlight_bg": RGBColor(0xFF, 0xF3, 0xE0),
    },
    "cyan_ink": {
        "bg": RGBColor(0xFA, 0xF8, 0xF5),
        "bg_alt": RGBColor(0xF0, 0xF7, 0xF5),
        "primary": RGBColor(0x2E, 0x7D, 0x6E),     # 青绿
        "primary_dark": RGBColor(0x1C, 0x52, 0x47),
        "primary_light": RGBColor(0xD9, 0xEB, 0xE6),
        "accent": RGBColor(0xC7, 0x5C, 0x2E),       # 赭石
        "text": RGBColor(0x2C, 0x18, 0x10),          # 墨色
        "text_light": RGBColor(0x8A, 0x79, 0x68),
        "text_white": RGBColor(0xFF, 0xFF, 0xFF),
        "rule": RGBColor(0xE8, 0xE0, 0xD8),
        "highlight_bg": RGBColor(0xFD, 0xF2, 0xE8),
    },
    "cute_cartoon": {
        "bg": RGBColor(0xFF, 0xFD, 0xFA),
        "bg_alt": RGBColor(0xFF, 0xF5, 0xF5),
        "primary": RGBColor(0xE8, 0x6B, 0x8A),     # 粉
        "primary_dark": RGBColor(0xC2, 0x4E, 0x6E),
        "primary_light": RGBColor(0xFD, 0xE0, 0xE8),
        "accent": RGBColor(0x58, 0xB3, 0x8E),       # 绿
        "text": RGBColor(0x3D, 0x2C, 0x2E),
        "text_light": RGBColor(0x9E, 0x8A, 0x8C),
        "text_white": RGBColor(0xFF, 0xFF, 0xFF),
        "rule": RGBColor(0xEE, 0xE0, 0xE2),
        "highlight_bg": RGBColor(0xE8, 0xF5, 0xEE),
    },
    "formal": {
        "bg": RGBColor(0xF8, 0xF9, 0xFA),
        "bg_alt": RGBColor(0xEE, 0xEF, 0xF1),
        "primary": RGBColor(0x1E, 0x29, 0x3B),     # 深蓝灰
        "primary_dark": RGBColor(0x0F, 0x16, 0x24),
        "primary_light": RGBColor(0xD4, 0xD8, 0xDE),
        "accent": RGBColor(0xC0, 0x82, 0x3E),       # 金
        "text": RGBColor(0x1E, 0x1E, 0x1E),
        "text_light": RGBColor(0x6B, 0x72, 0x80),
        "text_white": RGBColor(0xFF, 0xFF, 0xFF),
        "rule": RGBColor(0xE0, 0xE2, 0xE6),
        "highlight_bg": RGBColor(0xFE, 0xF5, 0xE7),
    },
    "minimal": {
        "bg": RGBColor(0xFF, 0xFF, 0xFF),
        "bg_alt": RGBColor(0xF5, 0xF5, 0xF5),
        "primary": RGBColor(0x33, 0x33, 0x33),     # 深灰
        "primary_dark": RGBColor(0x11, 0x11, 0x11),
        "primary_light": RGBColor(0xE0, 0xE0, 0xE0),
        "accent": RGBColor(0x75, 0x75, 0x75),       # 中灰
        "text": RGBColor(0x1A, 0x1A, 0x1A),
        "text_light": RGBColor(0x75, 0x75, 0x75),
        "text_white": RGBColor(0xFF, 0xFF, 0xFF),
        "rule": RGBColor(0xE5, 0xE5, 0xE5),
        "highlight_bg": RGBColor(0xFA, 0xFA, 0xFA),
    },
}

# 16:9 标准尺寸
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# 全局边距
MARGIN_L = Inches(0.7)
MARGIN_R = Inches(0.7)
MARGIN_T = Inches(0.5)
CONTENT_W = SLIDE_W - MARGIN_L - MARGIN_R


def _get_colors(style: str) -> dict[str, RGBColor]:
    return STYLE_COLORS.get(style, STYLE_COLORS["academic"])


def _set_bg(slide, color: RGBColor) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_rect(slide, left, top, width, height, color: RGBColor, line_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line_color is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(0.5)
    shape.shadow.inherit = False
    return shape


def _add_rounded_rect(slide, left, top, width, height, color: RGBColor, line_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line_color is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(0.5)
    shape.shadow.inherit = False
    return shape


def _add_textbox(slide, left, top, width, height, text: str,
                 font_size=18, bold=False, color: RGBColor = None,
                 align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
                 font_name="Microsoft YaHei"):
    if color is None:
        color = RGBColor(0x1A, 0x1A, 0x1A)
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(50000)
    tf.margin_right = Emu(50000)
    tf.margin_top = Emu(30000)
    tf.margin_bottom = Emu(30000)
    tf.vertical_anchor = anchor
    lines = text.split("\n") if text else [""]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = font_name
    return tb


def _add_bullet_text(slide, left, top, width, height, items: list[str],
                     font_size=16, color: RGBColor = None, bullet_color: RGBColor = None,
                     line_spacing=1.5, font_name="Microsoft YaHei"):
    if not items:
        return
    if color is None:
        color = RGBColor(0x1A, 0x1A, 0x1A)
    if bullet_color is None:
        bullet_color = color
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = line_spacing
        # 圆点
        run_dot = p.add_run()
        run_dot.text = "● "
        run_dot.font.size = Pt(font_size - 2)
        run_dot.font.color.rgb = bullet_color
        run_dot.font.name = font_name
        # 正文
        run = p.add_run()
        run.text = str(item)
        run.font.size = Pt(font_size)
        run.font.color.rgb = color
        run.font.name = font_name
    return tb


def _add_page_number(slide, page_num: int, total: int, colors: dict):
    """添加页码（右下角）"""
    _add_textbox(slide, SLIDE_W - Inches(1.5), SLIDE_H - Inches(0.45),
                 Inches(1.3), Inches(0.35),
                 f"{page_num} / {total}", font_size=9, color=colors["text_light"],
                 align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)


# ============ 幻灯片渲染器 ============

def _render_cover(slide, data: dict, colors: dict, style: str):
    """封面页"""
    _set_bg(slide, colors["bg"])
    title = data.get("title", "教学课件")
    subtitle = data.get("subtitle", "")
    metadata = data.get("content", "")

    # 顶部装饰条
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), colors["primary"])
    # 底部装饰条
    _add_rect(slide, 0, SLIDE_H - Inches(0.08), SLIDE_W, Inches(0.08), colors["primary"])

    # 中间装饰框
    box_top = Inches(2.0)
    box_h = Inches(3.5)
    _add_rect(slide, MARGIN_L, box_top, CONTENT_W, box_h, colors["bg_alt"],
              line_color=colors["primary_light"])

    # 顶部色条
    _add_rect(slide, MARGIN_L, box_top, CONTENT_W, Inches(0.06), colors["primary"])

    # 主标题
    _add_textbox(slide, MARGIN_L + Inches(0.5), box_top + Inches(0.5),
                 CONTENT_W - Inches(1.0), Inches(1.2),
                 title, font_size=36, bold=True, color=colors["primary_dark"],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # 副标题（章节）
    if subtitle:
        _add_textbox(slide, MARGIN_L + Inches(0.5), box_top + Inches(1.8),
                     CONTENT_W - Inches(1.0), Inches(0.7),
                     f"· {subtitle} ·", font_size=22, color=colors["text_light"],
                     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # 元信息（课时/教师等）
    if metadata:
        _add_textbox(slide, MARGIN_L + Inches(0.5), box_top + Inches(2.6),
                     CONTENT_W - Inches(1.0), Inches(0.6),
                     metadata, font_size=14, color=colors["text_light"],
                     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def _render_section_header(slide, data: dict, colors: dict, style: str):
    """章节标题页"""
    _set_bg(slide, colors["bg"])
    title = data.get("title", "")
    subtitle = data.get("subtitle", "")

    # 全宽色块
    bar_top = Inches(2.8)
    bar_h = Inches(1.8)
    _add_rect(slide, 0, bar_top, SLIDE_W, bar_h, colors["primary"])
    # 左侧装饰条
    _add_rect(slide, 0, bar_top, Inches(0.12), bar_h, colors["primary_dark"])

    _add_textbox(slide, MARGIN_L + Inches(0.5), bar_top + Inches(0.2),
                 CONTENT_W - Inches(1.0), Inches(0.8),
                 title, font_size=32, bold=True, color=colors["text_white"],
                 align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)

    if subtitle:
        _add_textbox(slide, MARGIN_L + Inches(0.5), bar_top + Inches(1.0),
                     CONTENT_W - Inches(1.0), Inches(0.6),
                     subtitle, font_size=16, color=colors["text_white"],
                     align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)


def _render_content(slide, data: dict, colors: dict, style: str, page_num: int, total: int):
    """普通内容页 - 带标题和正文"""
    _set_bg(slide, colors["bg"])
    title = data.get("title", "")
    bullet_points = data.get("bullet_points", [])
    content = data.get("content", "")
    highlight = data.get("highlight", "")

    # 顶部装饰条
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.06), colors["primary"])

    # 标题区域
    _add_rect(slide, MARGIN_L, Inches(0.3), CONTENT_W, Inches(0.7), colors["bg_alt"],
              line_color=colors["rule"])
    _add_rect(slide, MARGIN_L, Inches(0.3), Inches(0.08), Inches(0.7), colors["primary"])
    _add_textbox(slide, MARGIN_L + Inches(0.3), Inches(0.3), CONTENT_W - Inches(0.6), Inches(0.7),
                 title, font_size=24, bold=True, color=colors["primary_dark"],
                 anchor=MSO_ANCHOR.MIDDLE)

    content_top = Inches(1.3)
    content_height = Inches(5.0)

    # 正文（bullet points 优先）
    if bullet_points:
        _add_bullet_text(slide, MARGIN_L + Inches(0.3), content_top,
                         CONTENT_W - Inches(0.6), content_height,
                         bullet_points, font_size=18, color=colors["text"],
                         bullet_color=colors["primary"])
    elif content:
        _add_textbox(slide, MARGIN_L + Inches(0.3), content_top,
                     CONTENT_W - Inches(0.6), content_height,
                     content, font_size=16, color=colors["text"],
                     anchor=MSO_ANCHOR.TOP)

    # 高亮内容（底部）
    if highlight:
        hl_y = content_top + content_height - Inches(0.8)
        _add_rounded_rect(slide, MARGIN_L + Inches(0.3), hl_y,
                          CONTENT_W - Inches(0.6), Inches(0.7),
                          colors["highlight_bg"], line_color=colors.get("accent", colors["primary"]))
        _add_textbox(slide, MARGIN_L + Inches(0.6), hl_y + Inches(0.05),
                     CONTENT_W - Inches(1.2), Inches(0.6),
                     f"★ {highlight}", font_size=16, bold=True,
                     color=colors.get("accent", colors["primary_dark"]),
                     anchor=MSO_ANCHOR.MIDDLE)

    _add_page_number(slide, page_num, total, colors)


def _render_two_column(slide, data: dict, colors: dict, style: str, page_num: int, total: int):
    """双栏布局页"""
    _set_bg(slide, colors["bg"])
    title = data.get("title", "")
    left_col = data.get("left_column", "")
    right_col = data.get("right_column", "")

    # 顶部装饰条
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.06), colors["primary"])
    _add_textbox(slide, MARGIN_L, Inches(0.3), CONTENT_W, Inches(0.7),
                 title, font_size=24, bold=True, color=colors["primary_dark"],
                 anchor=MSO_ANCHOR.MIDDLE)

    col_w = (CONTENT_W - Inches(0.3)) / 2
    col_top = Inches(1.3)
    col_h = Inches(5.2)

    # 左栏
    _add_rect(slide, MARGIN_L, col_top, col_w, col_h, colors["bg_alt"],
              line_color=colors["rule"])
    _add_rect(slide, MARGIN_L, col_top, col_w, Inches(0.04), colors["primary"])
    _add_textbox(slide, MARGIN_L + Inches(0.2), col_top + Inches(0.2),
                 col_w - Inches(0.4), col_h - Inches(0.4),
                 left_col, font_size=14, color=colors["text"])

    # 右栏
    right_x = MARGIN_L + col_w + Inches(0.3)
    _add_rect(slide, right_x, col_top, col_w, col_h, colors["bg_alt"],
              line_color=colors["rule"])
    _add_rect(slide, right_x, col_top, col_w, Inches(0.04), colors.get("accent", colors["primary"]))
    _add_textbox(slide, right_x + Inches(0.2), col_top + Inches(0.2),
                 col_w - Inches(0.4), col_h - Inches(0.4),
                 right_col, font_size=14, color=colors["text"])

    _add_page_number(slide, page_num, total, colors)


def _render_bullets(slide, data: dict, colors: dict, style: str, page_num: int, total: int):
    """纯列表页"""
    _set_bg(slide, colors["bg"])
    title = data.get("title", "")
    bullet_points = data.get("bullet_points", [])

    # 顶部装饰条
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.06), colors["primary"])
    _add_textbox(slide, MARGIN_L, Inches(0.3), CONTENT_W, Inches(0.7),
                 title, font_size=24, bold=True, color=colors["primary_dark"],
                 anchor=MSO_ANCHOR.MIDDLE)

    if bullet_points:
        _add_bullet_text(slide, MARGIN_L + Inches(0.5), Inches(1.4),
                         CONTENT_W - Inches(1.0), Inches(5.0),
                         bullet_points, font_size=18, color=colors["text"],
                         bullet_color=colors["primary"], line_spacing=1.8)

    _add_page_number(slide, page_num, total, colors)


def _render_table(slide, data: dict, colors: dict, style: str, page_num: int, total: int):
    """表格页"""
    _set_bg(slide, colors["bg"])
    title = data.get("title", "")
    headers = data.get("table_header", [])
    rows = data.get("table_rows", [])

    # 顶部装饰条
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.06), colors["primary"])
    _add_textbox(slide, MARGIN_L, Inches(0.3), CONTENT_W, Inches(0.7),
                 title, font_size=24, bold=True, color=colors["primary_dark"],
                 anchor=MSO_ANCHOR.MIDDLE)

    if not headers or not rows:
        _add_textbox(slide, MARGIN_L, Inches(2.0), CONTENT_W, Inches(1.0),
                     "暂无数据", font_size=16, color=colors["text_light"],
                     align=PP_ALIGN.CENTER)
        _add_page_number(slide, page_num, total, colors)
        return

    # 绘制表格
    n_cols = len(headers)
    n_rows = len(rows) + 1  # +1 表头
    tbl_left = MARGIN_L + Inches(0.3)
    tbl_top = Inches(1.4)
    tbl_w = CONTENT_W - Inches(0.6)
    tbl_h = Inches(0.5) * min(n_rows, 10)

    shape = slide.shapes.add_table(n_rows, n_cols, tbl_left, tbl_top, tbl_w, tbl_h)
    table = shape.table

    # 表头
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = str(h)
        for para in cell.text_frame.paragraphs:
            para.alignment = PP_ALIGN.CENTER
            for run in para.runs:
                run.font.size = Pt(14)
                run.font.bold = True
                run.font.color.rgb = colors["text_white"]
                run.font.name = "Microsoft YaHei"
        cell.fill.solid()
        cell.fill.fore_color.rgb = colors["primary"]

    # 数据行
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            if j >= n_cols:
                break
            cell = table.cell(i + 1, j)
            cell.text = str(val)
            for para in cell.text_frame.paragraphs:
                para.alignment = PP_ALIGN.CENTER
                for run in para.runs:
                    run.font.size = Pt(13)
                    run.font.color.rgb = colors["text"]
                    run.font.name = "Microsoft YaHei"
            cell.fill.solid()
            cell.fill.fore_color.rgb = colors["bg"] if i % 2 == 0 else colors["bg_alt"]

    _add_page_number(slide, page_num, total, colors)


def _render_quote(slide, data: dict, colors: dict, style: str, page_num: int, total: int):
    """引用/强调页"""
    _set_bg(slide, colors["bg"])
    title = data.get("title", "")
    content = data.get("content", "")
    bullet_points = data.get("bullet_points", [])

    # 顶部装饰
    _add_rect(slide, 0, 0, SLIDE_W, Inches(0.06), colors.get("accent", colors["primary"]))

    if title:
        _add_textbox(slide, MARGIN_L, Inches(0.3), CONTENT_W, Inches(0.7),
                     title, font_size=22, bold=True, color=colors["primary_dark"],
                     anchor=MSO_ANCHOR.MIDDLE)

    # 大引用框
    q_top = Inches(1.8)
    q_h = Inches(3.5)
    _add_rect(slide, MARGIN_L + Inches(0.5), q_top, CONTENT_W - Inches(1.0), q_h,
              colors["bg_alt"], line_color=colors.get("accent", colors["primary"]))
    # 左侧竖线
    _add_rect(slide, MARGIN_L + Inches(0.5), q_top, Inches(0.08), q_h,
              colors.get("accent", colors["primary"]))

    if bullet_points:
        display_text = "\n".join(f"● {b}" for b in bullet_points)
    else:
        display_text = content

    _add_textbox(slide, MARGIN_L + Inches(0.9), q_top + Inches(0.3),
                 CONTENT_W - Inches(1.8), q_h - Inches(0.6),
                 display_text, font_size=20, color=colors["text"],
                 anchor=MSO_ANCHOR.MIDDLE)

    _add_page_number(slide, page_num, total, colors)


def _render_activity(slide, data: dict, colors: dict, style: str, page_num: int, total: int):
    """互动活动页"""
    _set_bg(slide, colors["bg"])
    title = data.get("title", "课堂互动")
    content = data.get("content", "")
    bullet_points = data.get("bullet_points", [])

    # 顶部全宽色块
    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.0), colors["primary"])
    _add_textbox(slide, MARGIN_L, Inches(0.15), CONTENT_W, Inches(0.7),
                 f"💬 {title}", font_size=26, bold=True, color=colors["text_white"],
                 anchor=MSO_ANCHOR.MIDDLE)

    # 活动内容
    act_top = Inches(1.4)
    act_h = Inches(5.0)

    if bullet_points:
        # 带序号的大号列表
        for i, item in enumerate(bullet_points):
            y = act_top + i * Inches(0.9)
            _add_rounded_rect(slide, MARGIN_L + Inches(0.5), y,
                              CONTENT_W - Inches(1.0), Inches(0.75),
                              colors["bg_alt"], line_color=colors["rule"])
            # 序号
            _add_rect(slide, MARGIN_L + Inches(0.5), y, Inches(0.6), Inches(0.75),
                      colors["primary"])
            _add_textbox(slide, MARGIN_L + Inches(0.5), y, Inches(0.6), Inches(0.75),
                         str(i + 1), font_size=18, bold=True, color=colors["text_white"],
                         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            # 内容
            _add_textbox(slide, MARGIN_L + Inches(1.4), y, CONTENT_W - Inches(1.9), Inches(0.75),
                         item, font_size=16, color=colors["text"],
                         anchor=MSO_ANCHOR.MIDDLE)
    elif content:
        _add_textbox(slide, MARGIN_L + Inches(0.5), act_top,
                     CONTENT_W - Inches(1.0), act_h,
                     content, font_size=18, color=colors["text"])

    _add_page_number(slide, page_num, total, colors)


def _render_summary(slide, data: dict, colors: dict, style: str, page_num: int, total: int):
    """小结页"""
    _set_bg(slide, colors["bg"])
    title = data.get("title", "本课小结")
    bullet_points = data.get("bullet_points", [])
    content = data.get("content", "")

    # 顶部全宽色块
    _add_rect(slide, 0, 0, SLIDE_W, Inches(1.0), colors["primary_dark"])
    _add_textbox(slide, MARGIN_L, Inches(0.15), CONTENT_W, Inches(0.7),
                 f"📋 {title}", font_size=26, bold=True, color=colors["text_white"],
                 anchor=MSO_ANCHOR.MIDDLE)

    content_top = Inches(1.5)
    content_h = Inches(5.0)

    if bullet_points:
        _add_bullet_text(slide, MARGIN_L + Inches(0.5), content_top,
                         CONTENT_W - Inches(1.0), content_h,
                         bullet_points, font_size=18, color=colors["text"],
                         bullet_color=colors["primary"], line_spacing=1.8)
    elif content:
        _add_textbox(slide, MARGIN_L + Inches(0.5), content_top,
                     CONTENT_W - Inches(1.0), content_h,
                     content, font_size=16, color=colors["text"])

    _add_page_number(slide, page_num, total, colors)


# ============ 幻灯片类型映射 ============
SLIDE_RENDERERS = {
    "cover": _render_cover,
    "section_header": _render_section_header,
    "content": _render_content,
    "two_column": _render_two_column,
    "bullets": _render_bullets,
    "table": _render_table,
    "quote": _render_quote,
    "activity": _render_activity,
    "summary": _render_summary,
}


def export_teaching_pptx(
    slide_data: dict[str, Any],
    style: str = "academic",
) -> bytes:
    """将LLM生成的幻灯片结构渲染为PPTX字节流

    Args:
        slide_data: LLM生成的幻灯片数据，包含 {"slides": [...], "total_slides": N}
        style: 视觉风格标识

    Returns:
        PPTX 文件的字节流
    """
    colors = _get_colors(style)
    slides = slide_data.get("slides", [])
    total = len(slides)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    page_num = 0
    for slide_info in slides:
        slide_type = slide_info.get("type", "content")
        renderer = SLIDE_RENDERERS.get(slide_type)

        if renderer is None:
            # 未知类型，默认用 content 渲染
            renderer = _render_content

        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局

        if slide_type in ("cover", "section_header"):
            renderer(slide, slide_info, colors, style)
        else:
            page_num += 1
            renderer(slide, slide_info, colors, style, page_num, total)

        # 添加 speaker notes
        notes_text = slide_info.get("speaker_notes", "")
        if notes_text:
            notes_slide = slide.notes_slide
            notes_tf = notes_slide.notes_text_frame
            notes_tf.text = notes_text

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


# 兼容旧接口（保留原有导出函数，但标记为deprecated）
def export_pptx(plan) -> bytes:
    """[已废弃] 使用 export_teaching_pptx 替代"""
    raise DeprecationWarning("请使用 export_teaching_pptx(slide_data, style) 替代")