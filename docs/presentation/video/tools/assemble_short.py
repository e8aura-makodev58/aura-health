"""Assemble the 3-minute short cut (no voice) from deck slides and the recorded in-app guided story."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
FF = str(HERE.parent / "vtools/node_modules/ffmpeg-static/ffmpeg")
DECK = Path(__file__).resolve().parents[2] / "deck" / "png"
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

import os
if os.environ.get("FIRST_HALF") == "1":
    # First half of the combined video: same scenes, paced for a spoken voice-over
    # (~110 words a minute plus a breath at each cut; see SONG_CUT_PLAN.md sections 1–10).
    slide(1, 6); slide(3, 14); slide(4, 7)                  # 1 · cover, problem, what AURA does   27 s
    phone("t3", 5.0, 32.0)                                  # 2 · calm start                       27 s
    phone("t4", 33.0, 44.0); phone("t4", 60.5, 70.8, hold=1)  # 3 · dose + honest reply           22.3 s
    phone("t5", 72.3, 81.4, hold=4.3)                       # 4 · appointment (ends before the story moves on) 13.4 s
    desk(43.3, 52.0); desk(68.6, 74.2); desk(88.4, 100.0, hold=3)  # 5 · clinician + agent        28.9 s
    phone("t7", 114.8, 117.6); phone("t7", 123.9, 135.0)    # 6 · flu                              13.9 s
    phone("t8", 143.0, 162.0)                               # 7 · safety                           19 s
    slide(11, 13); slide(12, 11)                            # 8 · architecture, agent loop         24 s
    slide(15, 16)                                           # 9 · fit with the challenge           16 s
    slide(16, 15)                                           # 10 · how we built it                 15 s
else:
    slide(1, 6); slide(3, 12); slide(4, 6)                 # cover, problem, what AURA does
    phone("t3", 5.0, 32.0)                                  # start the story, breath, summary
    phone("t4", 33.5, 43.0); phone("t4", 61.0, 70.8)        # skipped dose + reason; honest "can't identify" reply
    phone("t5", 71.5, 80.0)                                 # appointment: missed dose, Not sent
    desk(44.0, 52.0); desk(68.6, 72.0); desk(88.4, 100.0, hold=3)  # clinician view; first draft rejected; checked answer
    phone("t7", 114.8, 117.6); phone("t7", 123.9, 134.0)    # simulated flu, new summary, small idea
    phone("t8", 143.5, 161.0)                               # safety example (masked), safety panel, explanation card
    slide(11, 12); slide(12, 10); slide(15, 12); slide(18, 10.8)   # architecture, agent loop, challenge fit, close

(OUT / "parts.txt").write_text("".join(f"file '{p.name}'\n" for p, _, _ in parts))
final = OUT / ("aura-health-part1-voiceover-novoice.mp4" if os.environ.get("FIRST_HALF") == "1" else "aura-health-short-3min-novoice.mp4")
run(["-f", "concat", "-safe", "0", "-i", str(OUT / "parts.txt"), "-c", "copy", "-movflags", "+faststart", str(final)])
t, lines = 0.0, []
for p, label, seconds in parts:
    lines.append(f"{int(t//60)}:{t%60:04.1f}  {label}  ({seconds}s)"); t += seconds
(OUT / "timeline.txt").write_text("\n".join(lines) + f"\nTotal {int(t//60)}:{t%60:04.1f}\n"); print("\n".join(lines)); print(f"Total {int(t//60)}:{t%60:04.1f}")
