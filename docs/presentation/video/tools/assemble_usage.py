"""Usage demo (song half): one live take, with only AI waiting time trimmed.

Every wait_start/wait_end pair in marks-usage.json longer than KEEP (3 s) is shortened to KEEP
seconds (the first part of the wait is kept so the viewer sees AURA working). Nothing else is cut.
Usage: assemble_usage.py <dir with marks-usage.json> <outdir>
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
FF = str(HERE.parent / "vtools/node_modules/ffmpeg-static/ffmpeg")
KEEP = 3.0
src, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
data = json.loads((src / "marks-usage.json").read_text())
marks = data["marks"]
start = next(m["t"] for m in marks if m["label"] == "start") - 1.0
end = next(m["t"] for m in marks if m["label"] == "end")
cuts, pending = [], {}
for m in marks:
    kind, _, label = m["label"].partition(":")
    if kind == "wait_start":
        pending[label] = m["t"]
    elif kind == "wait_end" and label in pending and m["t"] - pending[label] > KEEP:
        cuts.append((pending[label] + KEEP, m["t"], label))
keep, cursor = [], start
for a, b, _ in sorted(cuts):
    keep.append((cursor, a)); cursor = b
keep.append((cursor, end))
ENC = ["-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-shortest"]
parts = []
for index, (a, b) in enumerate(keep):
    part = out / f"usage{index:02d}.mp4"
    subprocess.run([FF, "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", data["video"],
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                    "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-map", "0:v", "-map", "1:a",
                    "-t", f"{b - a:.3f}", *ENC, str(part)], check=True)
    parts.append(part)
(out / "usage-parts.txt").write_text("".join(f"file '{p.name}'\n" for p in parts))
final = out / "aura-health-usage-demo-novoice.mp4"
subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(out / "usage-parts.txt"),
                "-c", "copy", "-movflags", "+faststart", str(final)], check=True)
total = sum(b - a for a, b in keep)
print(f"raw {end - start:.1f}s, trimmed waits: " + ", ".join(f"{label} -{b - a:.1f}s" for a, b, label in cuts))
print(f"final {int(total // 60)}:{total % 60:04.1f} -> {final}")
