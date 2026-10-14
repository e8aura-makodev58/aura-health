"""Slides 11–13 as native PowerPoint diagrams: editable boxes and connector arrows glued to them.

Every arrow is a connector whose ends are attached to a box's connection site (stCxn/endCxn), so
moving a box in PowerPoint drags its arrows along. Coordinates are CSS pixels on a 1920×1080
slide (1 px = 6350 EMU). Connection sites on rectangles: 0 top, 1 left, 2 bottom, 3 right.
"""
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt
from lxml import etree

PX = 6350
FONT = "Nunito"
INK, MUTED, LINE = "2a2320", "6b6258", "6b6258"
FILL = {"blue": "dceef7", "lilac": "e8e1f3", "rose": "fde3df", "sand": "f3f0ea", "sun": "fff0d0", "white": "ffffff"}
TOP, LEFT, BOTTOM, RIGHT = 0, 1, 2, 3


def _plain(shape):
    """Drop the theme style reference (no theme shadow or colours); everything is set explicitly."""
    style = shape._element.find(qn("p:style"))
    if style is not None:
        shape._element.remove(style)


def _rgb(hex6):
    return RGBColor.from_string(hex6)


def text(slide, x, y, w, h, lines, *, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name=None):
    """Free text. lines: [(text, px size, bold, colour)]."""
    box = slide.shapes.add_textbox(Emu(x * PX), Emu(y * PX), Emu(w * PX), Emu(h * PX))
    _fill_text(box.text_frame, lines, align, anchor, margin=0)
    box.name = name or ("Text: " + lines[0][0][:40])
    return box


def _fill_text(frame, lines, align, anchor, margin):
    frame.word_wrap = True
    frame.auto_size = None
    frame.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(frame, side, Emu(margin * PX))
    for index, (content, size, bold, colour) in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.alignment = align
        paragraph.space_after = Pt(size * 0.5 * (0.45 if index == 0 else 0.25))
        run = paragraph.add_run()
        run.text = content
        run.font.name = FONT
        run.font.size = Pt(size * 0.5)
        run.font.bold = bold
        run.font.color.rgb = _rgb(colour)


def node(slide, x, y, w, h, title, body=(), *, fill="sand", dashed=False, title_size=27, body_size=22, name=None):
    """A rounded box with a bold title and body lines; arrows glue to it."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(x * PX), Emu(y * PX), Emu(w * PX), Emu(h * PX))
    shape.adjustments[0] = min(0.5, 22 / min(w, h))
    _plain(shape)
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(FILL[fill])
    if dashed:
        shape.line.color.rgb = _rgb("cfc8bd")
        shape.line.width = Pt(1.25)
        shape.line.dash_style = 7  # dash
    else:
        shape.line.fill.background()
    lines = [(title, title_size, True, INK)] + [(line, body_size, False, INK if i < 3 else MUTED) for i, line in enumerate(body)]
    _fill_text(shape.text_frame, lines, PP_ALIGN.LEFT, MSO_ANCHOR.TOP, margin=24)
    shape.name = name or ("Box: " + title[:40])
    shape._px = (x, y, w, h)
    return shape


def _site(shape, index):
    x, y, w, h = shape._px
    return {TOP: (x + w / 2, y), LEFT: (x, y + h / 2), BOTTOM: (x + w / 2, y + h), RIGHT: (x + w, y + h / 2)}[index]


def arrow(slide, start, start_site, end, end_site, *, both=False, bend=0.5, name=None):
    """Connector glued to two boxes. Straight when aligned, otherwise a one-bend-pair elbow.

    Elbows run horizontal–vertical–horizontal between side sites, and vertical–horizontal–vertical
    (a bentConnector3 rotated 90°) between top/bottom sites. bend sets where the middle segment sits.
    """
    (x1, y1), (x2, y2) = _site(start, start_site), _site(end, end_site)
    vertical = start_site in (TOP, BOTTOM)
    assert vertical == (end_site in (TOP, BOTTOM)), "join top/bottom to top/bottom, or side to side"
    straight = abs(x1 - x2) < 1 if vertical else abs(y1 - y2) < 1
    connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT if straight else MSO_CONNECTOR.ELBOW,
                                           Emu(0), Emu(0), Emu(PX), Emu(PX))
    sp_pr = connector._element.spPr
    xfrm = sp_pr.find(qn("a:xfrm"))
    for attribute in ("rot", "flipH", "flipV"):
        xfrm.attrib.pop(attribute, None)
    dx, dy = x2 - x1, y2 - y1
    if straight or not vertical:
        w, h = abs(dx), abs(dy)
        off = (min(x1, x2), min(y1, y2))
        if dx < 0: xfrm.set("flipH", "1")
        if dy < 0: xfrm.set("flipV", "1")
    else:
        # Rotate a horizontal elbow by 90° so it leaves and enters vertically.
        w, h = abs(dy), abs(dx)
        xfrm.set("rot", "5400000")
        if dx > 0: xfrm.set("flipV", "1")
        if dy < 0: xfrm.set("flipH", "1")
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        off = (cx - w / 2, cy - h / 2)
    xfrm.find(qn("a:off")).set("x", str(int(off[0] * PX))); xfrm.find(qn("a:off")).set("y", str(int(off[1] * PX)))
    xfrm.find(qn("a:ext")).set("cx", str(max(1, int(w * PX)))); xfrm.find(qn("a:ext")).set("cy", str(max(1, int(h * PX))))
    if not straight:
        geometry = sp_pr.find(qn("a:prstGeom"))
        geometry.set("prst", "bentConnector3")
        av = geometry.find(qn("a:avLst"))
        for child in list(av): av.remove(child)
        guide = etree.SubElement(av, qn("a:gd")); guide.set("name", "adj1"); guide.set("fmla", f"val {int(bend * 100000)}")
    # Glue both ends to the boxes' connection sites.
    nv = connector._element.find(qn("p:nvCxnSpPr")).find(qn("p:cNvCxnSpPr"))
    for tag, shape, site in (("a:stCxn", start, start_site), ("a:endCxn", end, end_site)):
        link = etree.SubElement(nv, qn(tag)); link.set("id", str(shape.shape_id)); link.set("idx", str(site))
    _plain(connector)
    line = connector.line
    line.color.rgb = _rgb(LINE)
    line.width = Pt(2)
    ln = sp_pr.find(qn("a:ln"))
    for tag in (["a:headEnd"] if both else []) + ["a:tailEnd"]:
        end_marker = etree.SubElement(ln, qn(tag)); end_marker.set("type", "triangle"); end_marker.set("w", "med"); end_marker.set("len", "med")
    connector.name = name or f"Arrow: {start.name[5:25]} → {end.name[5:25]}"
    return connector


def heading(slide, title, subtitle="Challenge 2 · Scenario 1: mental health maintenance for working adults on antidepressants"):
    text(slide, 80, 46, 1760, 70, [(title, 54, True, INK)])
    text(slide, 80, 122, 1760, 40, [(subtitle, 26, False, MUTED)])


def system_overview(slide):
    heading(slide, "AURA Health · system architecture")
    web = node(slide, 80, 190, 360, 500, "Web experience", fill="white", dashed=True, title_size=28)
    app = node(slide, 520, 190, 600, 500, "Python app · owns the state", fill="white", dashed=True, title_size=28)
    ai = node(slide, 1200, 190, 640, 500, "Bounded AI · read-only", fill="white", dashed=True, title_size=28)
    node(slide, 104, 256, 312, 200, "Patient companion", ["Breath + short recap", "Dose + reasons, medication", "Dates + optional suggestions"], fill="sand", title_size=25, body_size=20)
    node(slide, 104, 472, 312, 150, "Clinician view", ["Findings with sources", "Ask about the record"], fill="sand", title_size=25, body_size=20)
    text(slide, 104, 640, 312, 40, [("Presentation, not policy", 21, False, MUTED)])
    node(slide, 544, 256, 552, 112, "FastAPI application services", ["Atomic + idempotent events · SQLite + audit"], fill="blue", body_size=21)
    node(slide, 544, 384, 552, 112, "Curated medication content", ["Typed questions: safety first, fixed answers"], fill="blue", body_size=21)
    safety = node(slide, 544, 512, 268, 150, "Safety engine", ["T0–T4, fails closed"], fill="rose", body_size=21)
    node(slide, 828, 512, 268, 150, "Longitudinal", ["Personal + recent baselines"], fill="blue", body_size=21)
    agent = node(slide, 1224, 256, 592, 130, "Aura-Agent + patient-scoped tools", ["The model chooses tools, dates and comparisons"], fill="lilac", body_size=21)
    verify = node(slide, 1224, 446, 592, 130, "Ground · verify · recheck", ["Cited answer, or a labelled fallback + trace"], fill="lilac", body_size=21)
    text(slide, 1224, 590, 592, 100, [("Model gateway: provider configurable", 22, True, INK),
                                      ("Operator picks model + reasoning level", 21, False, MUTED), ("Synthetic data only", 21, False, MUTED)])
    display = node(slide, 498, 760, 360, 200, "Independent safety display", ["Pinned resources + fallback", "Never AI-written"], fill="rose", title_size=25, body_size=20)
    sim = node(slide, 900, 760, 420, 200, "Separate simulation plane", ["Plans + seeded synthetic data", "Only observable events enter"], fill="sun", title_size=25, body_size=20)
    arrow(slide, web, RIGHT, app, LEFT, both=True)
    arrow(slide, app, RIGHT, ai, LEFT, both=True)
    arrow(slide, agent, BOTTOM, verify, TOP)
    arrow(slide, safety, BOTTOM, display, TOP)
    arrow(slide, sim, TOP, app, BOTTOM, bend=0.5)
    text(slide, 442, 390, 76, 58, [("inputs", 16, False, MUTED), ("views", 16, False, MUTED)], align=PP_ALIGN.CENTER)
    text(slide, 1122, 388, 76, 64, [("request", 16, False, MUTED), ("result", 16, False, MUTED)], align=PP_ALIGN.CENTER)
    text(slide, 842, 692, 440, 36, [("Observable events via app ingestion", 19, False, MUTED)])
    text(slide, 80, 760, 380, 180, [("Signals propose. Rules decide. AI words it.", 30, True, INK)])
    text(slide, 1360, 760, 480, 250, [("One application · synthetic workspaces · development storage", 21, False, MUTED),
                                      ("Demo roles, no clinical authentication. Visit preview: Not sent.", 21, False, MUTED),
                                      ("Institutional hosting is future work", 21, False, MUTED)])


def agent_investigation(slide):
    heading(slide, "Aura-Agent · investigate, cite, check")
    c1, c2, c3, w = 80, 720, 1360, 480
    step1 = node(slide, c1, 200, w, 190, "1 · Guard the request", ["Skill, selected patient, current safety", "Read-only record + permitted window"], fill="blue")
    step2 = node(slide, c2, 200, w, 190, "2 · Model chooses a step", ["Which tool? Which dates? Which signal?", "Read more, or draft a cited answer"], fill="lilac")
    step3 = node(slide, c3, 200, w, 190, "3 · Execute scoped tools", ["Series, context, gaps, routine records", "Return facts, sources and calculations"], fill="blue")
    question = node(slide, c1, 470, w, 190, "“When did sleep timing change, and was anything reported around then?”",
                    ["A clinician's question. Patient-typed text is safety-checked first."], fill="sand", title_size=24, body_size=20)
    step4 = node(slide, c2, 470, w, 190, "4 · Ground and verify", ["Exact facts, citations, allowed claims", "Live drafts: separate verification call"], fill="lilac")
    step5 = node(slide, c3, 470, w, 190, "5 · Recheck current state", ["Record, safety + provider revision", "Unsafe or stale results are withheld"], fill="blue")
    step6 = node(slide, c3, 740, w, 190, "6 · Persist and display", ["Answer, sources, How AURA looked", "No care-action or treatment-write tools"], fill="sand")
    arrow(slide, question, TOP, step1, BOTTOM)
    arrow(slide, step1, RIGHT, step2, LEFT)
    arrow(slide, step2, RIGHT, step3, LEFT, both=True)
    arrow(slide, step2, BOTTOM, step4, TOP)
    arrow(slide, step4, RIGHT, step5, LEFT)
    arrow(slide, step5, BOTTOM, step6, TOP)
    text(slide, 1200, 196, 160, 60, [("tool calls,", 18, False, MUTED), ("facts back", 18, False, MUTED)], align=PP_ALIGN.CENTER)
    text(slide, 966, 400, 260, 60, [("cited draft", 18, False, MUTED), ("when ready", 18, False, MUTED)])
    text(slide, 80, 750, 1180, 60, [("Loop budgets: 8 model steps · 24 tool calls · 90 seconds", 28, True, INK)])
    text(slide, 80, 812, 1180, 200, [("Time checked between calls; provider timeout 30 s. Verifier is separate.", 22, False, MUTED),
                                      ("Failed drafts use related facts when available; blocked/stale requests show no answer.", 22, False, MUTED),
                                      ("The trail shows actions, not hidden reasoning. Verification is not clinical validation.", 22, False, MUTED)])


def safety_precedence(slide):
    heading(slide, "Safety policy has the final say")
    c, w = [80, 527, 974, 1421], 419
    inp = node(slide, c[0], 200, w, 200, "Patient input", ["Typed notes and medication questions", "Safety-relevant path first"], fill="sand")
    gate = node(slide, c[1], 200, w, 200, "Safety gate + proposals", ["Demo fixtures or rules + model", "Raise-only detector proposals"], fill="lilac")
    ctrl = node(slide, c[2], 200, w, 200, "Deterministic safety controller", ["T0–T4 transitions and actions", "Fail closed when degraded"], fill="rose")
    reg = node(slide, c[3], 200, w, 200, "Registry + built-in bundle", ["Lookup failure: built-in fallback", "Stale/unverified: visible + notice"], fill="rose")
    longi = node(slide, c[1], 480, w, 200, "Longitudinal communication", ["Stay quiet / check in / clarify", "Describes personal changes"], fill="blue")
    override = node(slide, c[2], 480, w, 200, "Safety overrides ordinary messages", ["Applies the authoritative state", "The app does not assign tiers"], fill="rose", title_size=25)
    pinned = node(slide, c[3], 480, w, 200, "Pinned safety resources", ["Shown outside generated text", "Resource rendering uses no model"], fill="rose")
    render = node(slide, c[2], 760, w, 210, "Render the allowed interaction", ["Approved wording + checks", "T4 / offline / degraded:", "fixed wording"], fill="sand", body_size=21)
    arrow(slide, inp, RIGHT, gate, LEFT)
    arrow(slide, gate, RIGHT, ctrl, LEFT)
    arrow(slide, ctrl, RIGHT, reg, LEFT)
    arrow(slide, ctrl, BOTTOM, override, TOP)
    arrow(slide, longi, RIGHT, override, LEFT)
    arrow(slide, reg, BOTTOM, pinned, TOP)
    arrow(slide, override, BOTTOM, render, TOP)
    text(slide, 80, 760, 840, 190, [("The patient can't dismiss safety content. The clinician sees the same state when they open the record. No alerts are sent in this prototype.", 24, False, INK),
                                     ("Assessment may call a model; failure holds input and restricts ordinary output.", 21, False, MUTED),
                                     ("Resources need review · no emergency monitoring or suicide-risk determination", 21, False, MUTED)])


DIAGRAMS = {"architecture": system_overview, "agent-loop": agent_investigation, "safety-precedence": safety_precedence}
