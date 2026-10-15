"""Captions for the usage demo (song half, no voice-over).

Each caption is anchored to a marker recorded by record_usage.cjs and mapped through the same
wait trimming as assemble_usage.py, so it lands on the moment it describes. Writes an .srt (for
YouTube subtitles) and burns rounded caption cards (Nunito, left-aligned, bottom left) into a copy.
Usage: caption_usage.py <dir with marks-usage.json> <usage mp4> <fonts dir> <outdir>
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
FF = str(HERE.parent / "vtools/node_modules/ffmpeg-static/ffmpeg")
KEEP = 3.0  # must match assemble_usage.py

# (anchor marker, offset seconds, duration seconds, caption). Two lines at most, ~45 characters each.
# Fresh wording on purpose: these captions must not repeat the first half's voice-over lines.
PLAN = [
    ("start", 1.0, 4.5, "A real session, start to finish\nSynthetic patient, live AI"),
    ("patient", 1.0, 4.5, "The patient's home, as they see it each day"),
    ("wait_end:recap", 0.5, 5.5, "Today's picture, in a few calm words"),
    ("wait_start:dose", -0.8, 4.0, "Taken. Done for today."),
    ("wait_start:medication", 0.3, 5.5, "Curious about a missed dose? Just ask."),
    ("note_typed", -6.0, 5.5, "A good day deserves a note"),
    ("wait_end:note_reply", 0.3, 6.5, "AURA answers the person,\nnot with a template"),
    ("reply_read", 0.5, 6.5, "Painting, 3 hours:\nkept in their own words, for their eyes"),
    ("activities_read", 0.3, 5.0, "Ideas shaped by what they enjoy"),
    ("wait_start:idea_ack", -0.8, 5.0, "Pick one. AURA cheers it on."),
    ("review", 0.5, 4.0, "Before the visit"),
    ("wait_end:visit_note", 0.3, 6.5, "The changes, in everyday words"),
    ("visit_read", 0.5, 6.5, "Their data, their call\non who gets to see it"),
    ("wait_start:clinician", -0.5, 5.5, "Same record, the clinician's side"),
    ("findings_read", 0.3, 6.5, "More creative time lately:\na gentle opening for the visit"),
    ("activity_summary_read", 1.0, 5.0, "Ask in plain English"),
    ("wait_end:qa_hobbies", 0.5, 7.0, "Answers arrive with their sources attached"),
    ("wait_start:qa_percent", -2.5, 2.4, "Need a number?"),
    ("wait_end:qa_percent", 0.3, 6.5, "Worked out exactly,\nmissing days included"),
    ("minimum", -7.0, 5.5, "Privacy, one tap away"),
    ("minimum", 0.3, 6.5, "Minimum shared:\nthe details step back"),
    ("wait_end:qa_notes", 0.5, 7.0, "No access, no guessing:\nthe agent says so"),
    ("qa_notes_read", 0.5, 7.5, "AURA Health\nRoom for your day"),
]

src, video, fonts, out = (Path(arg) for arg in sys.argv[1:5]); out.mkdir(parents=True, exist_ok=True)
marks = json.loads((src / "marks-usage.json").read_text())["marks"]
first = {}
for m in marks:
    first.setdefault(m["label"], m["t"])
start = first["start"] - 1.0
cuts, pending = [], {}
for m in marks:
    kind, _, label = m["label"].partition(":")
    if kind == "wait_start":
        pending[label] = m["t"]
    elif kind == "wait_end" and label in pending and m["t"] - pending[label] > KEEP:
        cuts.append((pending[label] + KEEP, m["t"]))


def out_time(raw):
    removed = 0.0
    for a, b in cuts:
        if raw >= b:
            removed += b - a
        elif raw > a:
            removed += raw - a
    return raw - start - removed


events = sorted((out_time(first[anchor] + offset), duration, text) for anchor, offset, duration, text in PLAN if anchor in first)
for index in range(len(events) - 1):  # never overlap: end each caption before the next begins
    at, duration, text = events[index]
    events[index] = (at, min(duration, events[index + 1][0] - at - 0.15), text)

stamp = lambda s: f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d},{int(round(s % 1 * 1000)):03d}"
srt = "\n".join(f"{n}\n{stamp(at)} --> {stamp(at + d)}\n{text}\n" for n, (at, d, text) in enumerate(events, 1))
(out / "aura-health-usage-demo.srt").write_text(srt)

# Burned-in captions: one rounded, softly transparent card per caption (Nunito, left-aligned),
# drawn with Pillow and overlaid with a short fade. Position: bottom left, above the app's button.
from PIL import Image, ImageDraw, ImageFont
font = ImageFont.truetype(str(fonts / "Nunito-Bold.ttf"), 44)
PAD_X, PAD_Y, RADIUS, LINE, LEFT, BOTTOM = 30, 20, 22, 58, 96, 150
cards = []
for index, (at, d, text) in enumerate(events):
    lines = text.split("\n")
    width = max(int(font.getlength(line)) for line in lines) + 2 * PAD_X
    height = LINE * len(lines) + 2 * PAD_Y - 6
    card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), RADIUS, fill=(32, 38, 38, 190))
    for n, line in enumerate(lines):
        draw.text((PAD_X, PAD_Y - 4 + n * LINE), line, font=font, fill=(255, 255, 255, 255))
    path = out / f"caption{index:02d}.png"
    card.save(path)
    cards.append((path, at, d, height))
inputs, chains, last = [], [], "0:v"
for n, (path, at, d, height) in enumerate(cards, 1):
    inputs += ["-loop", "1", "-t", f"{d:.3f}", "-i", str(path)]
    chains.append(f"[{n}:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={max(0, d - 0.25):.3f}:d=0.25:alpha=1,setpts=PTS+{at:.3f}/TB[c{n}]")
    chains.append(f"[{last}][c{n}]overlay=x={LEFT}:y=H-{BOTTOM}-{height}:eof_action=pass[v{n}]")
    last = f"v{n}"
final = out / "aura-health-usage-demo-captioned-novoice.mp4"
subprocess.run([FF, "-v", "error", "-y", "-i", str(video), *inputs, "-filter_complex", ";".join(chains),
                "-map", f"[{last}]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(final)], check=True)
print(f"{len(events)} captions -> {final}\nsrt -> {out / 'aura-health-usage-demo.srt'}")
