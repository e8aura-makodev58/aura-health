"""Assemble the AURA walkthrough video (no voice) from deck slides and live recordings."""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
FF = str(HERE.parent / "vtools/node_modules/ffmpeg-static/ffmpeg")
DECK = Path("/home/makodev58/aura-health/docs/presentation/deck/png")
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
vids = json.loads((HERE / "marks.json").read_text())["vids"]
vids["desk"] = json.loads((HERE / "marks-desk.json").read_text())["vids"]["desk"]
ENC = ["-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-shortest"]
SILENCE = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
parts, n = [], 0

def run(args):
    subprocess.run([FF, "-v", "error", "-y", *args], check=True)

def slide(number, seconds):
    global n; n += 1; out = OUT / f"part{n:02d}.mp4"
    run(["-loop", "1", "-t", str(seconds), "-i", str(DECK / f"slide-{number:02d}.png"), *SILENCE,
         "-vf", "scale=1920:1080,format=yuv420p", "-t", str(seconds), *ENC, str(out)])
    parts.append((out, f"slide {number}", seconds))

def phone(bg, start, end, video="phone"):
    global n; n += 1; out = OUT / f"part{n:02d}.mp4"; seconds = round(end - start, 2)
    run(["-loop", "1", "-i", str(HERE / "bg" / f"{bg}.png"), "-ss", str(start), "-t", str(seconds), "-i", vids[video], *SILENCE,
         "-filter_complex", "[1:v]scale=446:965:flags=lanczos[p];[0:v][p]overlay=312:58:shortest=1,format=yuv420p[v]",
         "-map", "[v]", "-map", "2:a", "-t", str(seconds), *ENC, str(out)])
    parts.append((out, f"{bg} {start}-{end}", seconds))

def desk(start, end):
    global n; n += 1; out = OUT / f"part{n:02d}.mp4"; seconds = round(end - start, 2)
    run(["-ss", str(start), "-t", str(seconds), "-i", vids["desk"], *SILENCE,
         "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-map", "0:v", "-map", "1:a", "-t", str(seconds), *ENC, str(out)])
    parts.append((out, f"desk {start}-{end}", seconds))

# Script v2 order. Scenes 1–2 and the problem are slides; 3–8 are live recordings; 9–12 are slides.
slide(1, 12); slide(2, 13); slide(3, 28); slide(4, 6)
phone("s3", 5.2, 28.2)                       # 3 · A calm start
phone("s4", 28.2, 72.5)                      # 4 · My medication, my day
phone("s5", 72.5, 85.0); phone("s5", 90.0, 109.5)   # 5 · Something changes (flu wait trimmed)
phone("s6", 109.5, 126.0)                    # 6 · Ready for the appointment
desk(2.8, 17.3); desk(42.5, 53.3); desk(57.7, 71.5)  # 7 · Clinician + agent (attempt 2; waits trimmed)
phone("s8", 2.3, 24.2, video="safety")       # 8 · Safety first
slide(11, 16); slide(12, 16); slide(13, 10); slide(14, 12)   # 9 · How it's built
slide(15, 25)                                # 10 · Fit with the challenge
slide(16, 20)                                # 11 · How we built it
slide(17, 18); slide(18, 6)                  # 12 · Impact and close

listing = OUT / "parts.txt"
listing.write_text("".join(f"file '{p.name}'\n" for p, _, _ in parts))
final = OUT / "aura-health-walkthrough-novoice.mp4"
run(["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(final)])
t = 0.0
timeline = []
for p, label, seconds in parts:
    timeline.append(f"{int(t//60)}:{t%60:04.1f}  {label}  ({seconds}s)"); t += seconds
(OUT / "timeline.txt").write_text("\n".join(timeline) + f"\nTotal {int(t//60)}:{t%60:04.1f}\n")
print("\n".join(timeline)); print(f"Total {int(t//60)}:{t%60:04.1f}")
