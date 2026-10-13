"""Assemble the walkthrough (no voice) from deck slides and the recorded in-app guided story."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
FF = str(HERE.parent / "vtools/node_modules/ffmpeg-static/ffmpeg")
DECK = Path("/home/makodev58/aura-health/docs/presentation/deck/png")
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
PHONE = json.loads((HERE / "tour/marks-tour-phone.json").read_text())["video"]
DESK = json.loads((HERE / "tour/marks-tour-desk.json").read_text())["video"]
ENC = ["-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-shortest"]
SILENCE = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
parts, n = [], 0
def run(args): subprocess.run([FF, "-v", "error", "-y", *args], check=True)
def add(out, label, seconds): parts.append((out, label, seconds))
def slide(number, seconds):
    global n; n += 1; out = OUT / f"part{n:02d}.mp4"
    run(["-loop", "1", "-t", str(seconds), "-i", str(DECK / f"slide-{number:02d}.png"), *SILENCE,
         "-vf", "scale=1920:1080,format=yuv420p", "-t", str(seconds), *ENC, str(out)]); add(out, f"slide {number}", seconds)
def phone(bg, start, end, hold=0):
    global n; n += 1; out = OUT / f"part{n:02d}.mp4"; seconds = round(end - start + hold, 2)
    run(["-loop", "1", "-i", str(HERE / "bg" / f"{bg}.png"), "-ss", str(start), "-t", str(end - start), "-i", PHONE, *SILENCE,
         "-filter_complex", f"[1:v]scale=446:965:flags=lanczos,tpad=stop_mode=clone:stop_duration={hold}[p];[0:v][p]overlay=312:58:shortest=1,format=yuv420p[v]",
         "-map", "[v]", "-map", "2:a", "-t", str(seconds), *ENC, str(out)]); add(out, f"{bg} {start}-{end}+{hold}", seconds)
def desk(start, end, hold=0):
    global n; n += 1; out = OUT / f"part{n:02d}.mp4"; seconds = round(end - start + hold, 2)
    run(["-ss", str(start), "-t", str(end - start), "-i", DESK, *SILENCE,
         "-vf", f"scale=1920:1080:flags=lanczos,tpad=stop_mode=clone:stop_duration={hold},format=yuv420p",
         "-map", "0:v", "-map", "1:a", "-t", str(seconds), *ENC, str(out)]); add(out, f"desk {start}-{end}+{hold}", seconds)

slide(1, 12); slide(2, 13); slide(3, 28); slide(4, 6)
phone("t3", 2.3, 32.1)                               # 3 · A calm start (landing, guided story intro, breath, summary)
phone("t4", 32.1, 70.8)                              # 4 · My medication, my day (dose, leaflet answer, honest limit)
phone("t5", 70.8, 82.7, hold=6)                      # 5 · Ready for the appointment
desk(43.3, 57.5); desk(68.6, 74.2); desk(88.4, 104.6, hold=4)  # 6 · Clinician + agent (fallback shown, Ask again, checked answer)
phone("t7", 114.8, 117.6); phone("t7", 123.9, 136.0, hold=8)    # 7 · Something changes (flu wait trimmed)
phone("t8", 136.0, 163.1)                            # 8 · Safety first (finish card, paced masked example, safety panel, explanation card)
slide(11, 16); slide(12, 16); slide(13, 10); slide(14, 12)   # 9 · How it's built
slide(15, 25); slide(16, 20); slide(17, 18); slide(18, 6)    # 10–12

(OUT / "parts.txt").write_text("".join(f"file '{p.name}'\n" for p, _, _ in parts))
final = OUT / "aura-health-walkthrough-novoice.mp4"
run(["-f", "concat", "-safe", "0", "-i", str(OUT / "parts.txt"), "-c", "copy", "-movflags", "+faststart", str(final)])
t, lines = 0.0, []
for p, label, seconds in parts:
    lines.append(f"{int(t//60)}:{t%60:04.1f}  {label}  ({seconds}s)"); t += seconds
(OUT / "timeline.txt").write_text("\n".join(lines) + f"\nTotal {int(t//60)}:{t%60:04.1f}\n"); print("\n".join(lines)); print(f"Total {int(t//60)}:{t%60:04.1f}")
