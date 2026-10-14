"""Readable PDF source (HTML) from the CodeBuddy export + the genuine session screenshots."""
import base64, html, json, sys
from datetime import datetime, timezone
from pathlib import Path
src, shots, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
doc = json.loads(src.read_text()); conv = doc["data"]["conversations"][0]
esc = lambda s: html.escape(s.replace("/home/makodev58/", "~/"))
def short(s, n): s = s.strip(); return s if len(s) <= n else s[:n].rstrip() + " … [shortened]"
def when(ms): return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%d %b %Y %H:%M UTC")
parts, totals = [], {"calls": 0, "texts": 0}
for number, request in enumerate(conv["requests"], 1):
    first = json.loads(request["messages"][0]["message"])["content"][0]["text"]
    query = first.split("<user_query>")[-1].split("</user_query>")[0].strip() if "<user_query>" in first else first
    usage = request.get("usage", {})
    parts.append(f"<h2>Request {number} · {when(request['startedAt'])}</h2><p class='meta'>Mode: {esc(request['type'])} · state: {esc(request['state'])} · tokens: {usage.get('totalTokens','?'):,}</p>")
    parts.append(f"<div class='user'><b>User</b><pre>{esc(query)}</pre></div>")
    for message in request["messages"][1:]:
        inner = json.loads(message["message"]); content = inner.get("content")
        for part in content if isinstance(content, list) else [{"type": "text", "text": str(content)}]:
            kind = part.get("type")
            if kind == "text" and part.get("text", "").strip():
                totals["texts"] += 1; parts.append(f"<div class='ai'><b>CodeBuddy</b><pre>{esc(part['text'].strip())}</pre></div>")
            elif kind == "reasoning" and part.get("text", "").strip():
                parts.append(f"<div class='think'>Thinking: {esc(short(part['text'], 320))}</div>")
            elif kind == "tool-call":
                totals["calls"] += 1; args = json.dumps(part.get("args", {}), ensure_ascii=False)
                parts.append(f"<div class='tool'>→ <b>{esc(part['toolName'])}</b> {esc(short(args, 220))}</div>")
            elif kind == "tool-result":
                result = part.get("result"); text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
                parts.append(f"<div class='result'>← {esc(short(text, 200))}</div>")
images = sorted(shots.glob("*.png"))
gallery = "".join(f"<section class='shot'><h3>{esc(p.stem)}</h3><img src='data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}'></section>" for p in images)
page = f"""<!doctype html><html><head><meta charset='utf-8'><style>
body{{font-family:'Nunito',system-ui,sans-serif;color:#2a2320;font-size:11pt;margin:0}} h1{{font-size:24pt;margin:0 0 8pt}} h2{{font-size:15pt;margin:18pt 0 2pt;page-break-after:avoid}}
h3{{font-size:12pt;margin:0 0 8pt}} .meta{{color:#6b6258;margin:0 0 8pt}} pre{{white-space:pre-wrap;font-family:inherit;margin:4pt 0 0}}
.user,.ai{{break-inside:avoid}} .user{{background:#fff0d0;border-radius:8pt;padding:8pt 10pt;margin:6pt 0}} .ai{{background:#e8f3ea;border-radius:8pt;padding:8pt 10pt;margin:6pt 0}}
.tool,.result{{font-family:ui-monospace,monospace;font-size:8pt;color:#4a413b;margin:1pt 0 1pt 10pt;word-break:break-all}} .result{{color:#8a8076}}
.think{{font-size:8.5pt;color:#8a8076;font-style:italic;margin:3pt 0 3pt 10pt}}
.cover{{page-break-after:always}} .cover td{{padding:3pt 12pt 3pt 0;vertical-align:top}} @page shots{{size:A4 landscape}} .shot{{page:shots;page-break-before:always}} .shot img{{display:block;max-width:100%;max-height:150mm;margin:0 auto;border:1px solid #ddd}}
</style></head><body>
<section class='cover'><h1>AURA Health · development conversation history</h1>
<p>Tencent Cloud Hackathon Singapore 2026 · Healthcare track, Challenge Statement 2, Scenario 1.</p>
<table>
<tr><td><b>Tool</b></td><td>CodeBuddy (Tencent), {esc(conv['chatMode'])} mode</td></tr>
<tr><td><b>Export</b></td><td>{esc(src.name)} · schema {esc(doc['schema'])} v{doc['schemaVersion']} · exported {esc(doc['exportedAt'])}</td></tr>
<tr><td><b>Conversation</b></td><td>“{esc(conv['name'])}” · {len(conv['requests'])} requests · {totals['calls']} tool calls · {totals['texts']} CodeBuddy replies</td></tr>
<tr><td><b>Screenshots</b></td><td>{len(images)} genuine session screenshots (CodeBuddy and Miora), after the transcript</td></tr>
</table>
<p class='meta'>Transcript reproduced from the export, in order. Omitted: the IDE's injected system context. Shortened: long tool arguments/results and model reasoning (marked “shortened”). Home-folder paths are written as ~/. Nothing else edited.</p></section>
{''.join(parts)}
{gallery}
</body></html>"""
out.write_text(page); print(out, len(page), totals, len(images))
