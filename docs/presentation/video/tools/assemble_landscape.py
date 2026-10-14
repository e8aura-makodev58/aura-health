"""Landscape song half: one continuous live take of the guided story (1920×1080, record_tour.cjs deskfull),
plus a combined draft = 3-minute voice-over cut + landscape take. Usage: assemble_landscape.py <tourfull dir> <short mp4> <outdir>"""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
FF = str(HERE.parent / "vtools/node_modules/ffmpeg-static/ffmpeg")
src, short, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
marks = json.loads((src / "marks-tour-deskfull.json").read_text())
take, end = marks["video"], next(m["t"] for m in marks["marks"] if m["label"] == "end")
start, hold = 2.0, 3.0  # from just before the visitor presses "Play the 3-minute story"; hold the last frame
ENC = ["-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-shortest"]
def run(args): subprocess.run([FF, "-v", "error", "-y", *args], check=True)
land = out / "aura-health-landscape-demo-novoice.mp4"
run(["-ss", str(start), "-t", str(end - start), "-i", take, "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
     "-vf", f"scale=1920:1080:flags=lanczos,tpad=stop_mode=clone:stop_duration={hold},format=yuv420p",
     "-map", "0:v", "-map", "1:a", "-t", str(end - start + hold), *ENC, "-movflags", "+faststart", str(land)])
(out / "parts.txt").write_text(f"file '{short.resolve()}'\nfile '{land.resolve()}'\n")
combined = out / "aura-health-combined-draft-novoice.mp4"
run(["-f", "concat", "-safe", "0", "-i", str(out / "parts.txt"), "-c", "copy", "-movflags", "+faststart", str(combined)])
print(f"landscape {end - start + hold:.1f}s -> {land}\ncombined -> {combined}")
