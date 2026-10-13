"""Generate the AURA Health deck slides as 1920x1080 HTML pages.

Speaker notes come verbatim from ../SCRIPT.md (scene narration). Screenshots are the live,
unedited captures in ../screenshots/v2/. Run: python3 build.py, then node render.cjs,
then make_pptx.py (see README.md).
"""

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLIDES = HERE / "slides"
SHOT = "../../screenshots/v2/"
DIAG = "../../diagrams/"
MEDIA = "../../../../aura_ui/media/"

CSS = """
@font-face{font-family:'Nunito';src:url('../../../../aura_ui/media/nunito.woff2') format('woff2');font-weight:200 1000;font-style:normal}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;overflow:hidden}
body{background:#fbfaf7;color:#2a2320;font-family:'Nunito',system-ui,sans-serif;position:relative}
.brand{position:absolute;left:96px;top:56px;display:flex;align-items:center;gap:14px;font-weight:800;letter-spacing:.14em;font-size:26px}
.brand img{width:44px;height:44px}
.foot{position:absolute;left:96px;right:96px;bottom:44px;display:flex;justify-content:space-between;font-size:22px;color:#7a7066}
.content{position:absolute;left:96px;right:96px;top:150px;bottom:110px}
h1{font-size:72px;font-weight:800;letter-spacing:-.02em;line-height:1.08}
h2{font-size:58px;font-weight:800;letter-spacing:-.015em;line-height:1.1;margin-bottom:18px}
.kicker{font-size:24px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#9c5700;margin-bottom:14px}
.lead{font-size:32px;line-height:1.45;color:#4a413b;max-width:1100px}
.row{display:flex;gap:56px;align-items:flex-start}
.col{display:flex;flex-direction:column;gap:22px}
.phone{background:#2a2320;border-radius:56px;padding:14px;box-shadow:0 24px 60px rgba(42,35,32,.18);flex:none}
.phone img{display:block;border-radius:44px;width:330px}
.cardshot{background:#fff;border-radius:28px;box-shadow:0 16px 44px rgba(42,35,32,.12);padding:10px;flex:none;align-self:flex-start;overflow:hidden}
.crop{overflow:hidden;border-radius:20px}
.reply{background:#fff;border-radius:28px;box-shadow:0 16px 44px rgba(42,35,32,.12);padding:34px 34px;display:flex;flex-direction:column;gap:22px}
.bubble-q{align-self:flex-end;background:#f4f1ea;border-radius:22px 22px 6px 22px;padding:16px 22px;font-size:26px}
.bubble-a{background:#e8f3ea;border-left:6px solid #8cc499;border-radius:6px 22px 22px 22px;padding:18px 22px;font-size:27px;line-height:1.4}
.cardshot img{display:block;border-radius:20px}
.desk{background:#fff;border-radius:22px;box-shadow:0 20px 56px rgba(42,35,32,.16);overflow:hidden;border:10px solid #2a2320;flex:none}
.desk img{display:block}
.cap{font-size:28px;line-height:1.4;color:#4a413b}
.cap b{color:#2a2320}
.points{display:flex;flex-direction:column;gap:26px;margin-top:10px}
.point{display:flex;gap:20px;align-items:flex-start;font-size:32px;line-height:1.4}
.dot{width:22px;height:22px;border-radius:50%;flex:none;margin-top:12px}
.pill{display:inline-block;padding:12px 26px;border-radius:999px;font-size:26px;font-weight:700}
.quote{font-size:44px;line-height:1.35;font-weight:700;max-width:1500px}
.callout{position:absolute;background:#fff4d6;border:3px solid #d4a943;border-radius:22px;padding:18px 24px;font-size:26px;line-height:1.35;box-shadow:0 12px 30px rgba(42,35,32,.15)}
table{border-collapse:separate;border-spacing:0 12px;width:100%}
td{font-size:27px;line-height:1.3;padding:16px 22px;background:#fff;vertical-align:top}
td:first-child{border-radius:16px 0 0 16px;font-weight:800;width:420px}
td:last-child{border-radius:0 16px 16px 0;width:230px;text-align:center}
.status{display:inline-block;padding:6px 18px;border-radius:999px;font-weight:800;font-size:23px}
.built{background:#dff0e3;color:#2f6b3d}.partial{background:#fff0d0;color:#8a5a00}.next{background:#ece6f6;color:#5b4a86}
.slot{border:5px dashed #c4b4e0;border-radius:28px;background:#f7f3fb;display:flex;align-items:center;justify-content:center;text-align:center;font-size:34px;font-weight:700;color:#5b4a86;padding:40px}
.full{position:absolute;inset:0;width:1920px;height:1080px}
"""

PALETTE = {"sunny": "#f5a623", "coral": "#f47e6b", "blue": "#7bc4e4", "lilac": "#c4b4e0", "leaf": "#8cc499"}


def scenes():
    """Scene number -> notes text (screen direction + verbatim narration) from SCRIPT.md."""
    text = (HERE.parent / "SCRIPT.md").read_text()
    out = {}
    for block in re.split(r"\n### ", text)[1:]:
        head, _, body = block.partition("\n")
        number = int(head.split("·")[0].strip())
        lines, quote = [], []
        for line in body.splitlines():
            if line.startswith(">"):
                quote.append(line.lstrip("> ").strip())
                continue
            if quote:
                lines.append(" ".join(quote)); quote = []
            if line.startswith("**") and line.strip():
                lines.append("[" + re.sub(r"\*\*|\*", "", line).strip() + "]")
            if line.startswith("---"):
                break
        if quote:
            lines.append(" ".join(quote))
        out[number] = (f"Scene {number} · {head.split('·',1)[1].strip()}\n\n" + "\n\n".join(lines)).replace("*", "")
    return out


def page(body, *, brand=True, foot=True):
    parts = ["<!doctype html><html lang='en'><head><meta charset='utf-8'><style>", CSS, "</style></head><body>"]
    if brand:
        parts.append(f"<div class='brand'><img src='{MEDIA}aura-mark.svg' alt=''>AURA HEALTH</div>")
    parts.append(body)
    if foot:
        parts.append("<div class='foot'><span>Healthcare track · Challenge Statement 2 · Scenario 1</span><span>Synthetic demo data · aura-health.makodev58.com</span></div>")
    parts.append("</body></html>")
    return "".join(parts)


def phone(name, width=330):
    return f"<div class='phone'><img src='{SHOT}{name}.png' style='width:{width}px' alt=''></div>"


def card(name, width=430, crop=None):
    image = f"<img src='{SHOT}{name}.png' style='width:{width}px' alt=''>"
    if crop:
        image = f"<div class='crop' style='height:{crop}px'>{image}</div>"
    return f"<div class='cardshot'>{image}</div>"


def point(color, text):
    return f"<div class='point'><span class='dot' style='background:{PALETTE[color]}'></span><span>{text}</span></div>"


def slides():
    s = []
    # 1 Cover
    s.append(("cover", 1, page(f"""
      <img class='full' src='{MEDIA}welcome-hero.svg' style='object-fit:cover;opacity:.95' alt=''>
      <div class='full' style='background:linear-gradient(90deg,rgba(251,250,247,.97) 0%,rgba(251,250,247,.9) 46%,rgba(251,250,247,.15) 75%)'></div>
      <div style='position:absolute;left:120px;top:250px;max-width:1000px'>
        <div style='display:flex;align-items:center;gap:22px;margin-bottom:36px'><img src='{MEDIA}aura-mark.svg' style='width:96px;height:96px' alt=''></div>
        <h1 style='font-size:120px'>AURA Health</h1>
        <p class='lead' style='font-size:44px;margin-top:22px;color:#2a2320'>A calm companion between doctor visits</p>
        <div class='pill' style='background:#fff;border:2px solid #eee9e0;margin-top:54px'>Healthcare track · Challenge Statement 2 · Scenario 1</div>
      </div>""", brand=False, foot=False)))
    # 2 Chosen challenge
    s.append(("challenge", 1, page("""
      <div class='content'>
        <div class='kicker'>Our chosen case study</div>
        <h2>Challenge Statement 2 · AI Healthier Every Day</h2>
        <p class='lead' style='font-size:36px;margin-bottom:56px;max-width:1700px'>Scenario 1 · Mental health maintenance for working adults on antidepressants</p>
        <div style='border-left:10px solid #f5a623;padding:10px 0 10px 44px'>
          <p class='quote'>“How might we build an AI-powered health companion that helps people understand and manage their medications, stay on track with their care, and take greater ownership of their long-term health?”</p>
          <p class='cap' style='margin-top:26px'>Problem statement · Healthcare track, NTU Lee Kong Chian School of Medicine</p>
        </div>
      </div>""")))
    # 3 Problem
    s.append(("problem", 2, page(f"""
      <div class='content'>
        <div class='kicker'>The problem</div>
        <h2>Staying well happens between appointments</h2>
        <div class='points' style='margin-top:50px;max-width:1300px'>
          {point('coral', 'A dose gets missed, sleep drifts later, a flu knocks you out for a few days.')}
          {point('blue', 'Most apps ask you to log your mood every evening, which is hard when you are tired or low.')}
          {point('lilac', 'When the appointment comes, it is all pieced together from memory.')}
        </div>
      </div>
      <img src='{MEDIA}calm-state.svg' style='position:absolute;right:110px;bottom:120px;width:440px;border-radius:36px' alt=''>""")))
    # 4 What AURA does
    s.append(("what-aura-does", 3, page(f"""
      <div class='content'><div class='row'>
        <div class='col' style='width:640px'>
          <div class='kicker'>What AURA does</div>
          <h2>A calm companion between doctor visits</h2>
          <div class='points'>
            {point('sunny', 'Reads everyday wearable data quietly')}
            {point('leaf', "Compares it with <b>this person's own usual</b>, not a population average")}
            {point('blue', 'A calm view for the patient; a clear “what changed and when” for the clinician they share with')}
          </div>
        </div>
        <div class='desk' style='margin-top:20px'><img src='{SHOT}s01-landing-desktop.png' style='width:1020px' alt=''></div>
      </div></div>""")))
    # 5 Calm start
    s.append(("calm-start", 3, page(f"""
      <div class='content'><div class='row' style='gap:44px'>
        <div class='col' style='width:560px'>
          <div class='kicker'>A calm start</div>
          <h2>A breath, not a dashboard</h2>
          <p class='cap'>Then one short summary, <b>written by AI from facts the system has checked</b>: sleep time later than usual since late February, and how the person has been checking in.</p>
        </div>
        <div class='col' style='align-items:center'>{phone('s03b-welcome-phone', 300)}<span class='cap'>Take a breath</span></div>
        <div class='col' style='align-items:center'>{phone('s03c-summary-phone', 300)}<span class='cap'>One short summary</span></div>
      </div></div>""")))
    # 6 Medication
    s.append(("my-medication", 4, page(f"""
      <div class='content'>
        <div class='kicker'>My medication, my day</div>
        <h2 style='font-size:52px'>One tap a day, plain answers, honest limits</h2>
        <div class='row' style='gap:40px;margin-top:20px;align-items:flex-start'>
          <div class='col' style='width:480px'>{card('s04a-dose-reasons', 460, 300)}<p class='cap'><b>Skipped?</b> AURA asks what got in the way, because that is worth bringing to the doctor.</p></div>
          <div class='col' style='width:470px'>{card('s04c-medication-answer', 450, 640)}</div>
          <div class='col' style='width:560px'>
            <div class='reply'>
              <div class='bubble-q'>Can I take ibuprofen with it?</div>
              <div class='bubble-a'>I'm not able to identify that medication, please check with your pharmacist.</div>
              <span class='cap' style='font-size:22px'>AURA's exact reply in the live demo</span>
            </div>
            <p class='cap'>Answers come from <b>approved information</b>, not made up by AI. When it can't answer, it says so.</p>
          </div>
        </div>
      </div>""")))
    # 7 Something changes
    s.append(("something-changes", 5, page(f"""
      <div class='content'><div class='row' style='gap:56px'>
        <div class='col' style='width:600px'>
          <div class='kicker'>Something changes</div>
          <h2>A simulated three-day flu</h2>
          <p class='cap'>AURA notices resting heart rate is higher than in the person's <b>recent</b> records, and says exactly that: a recent change, not a change from their usual.</p>
          <p class='cap'>When a change shows up, it offers <b>a small idea for today</b>. Optional, never about medication.</p>
        </div>
        {phone('s05a-after-flu-phone', 320)}
        <div class='col' style='margin-top:120px'>{card('s05b-suggestion', 470)}</div>
      </div></div>""")))
    # 8 Appointment
    s.append(("appointment", 6, page(f"""
      <div class='content'><div class='row' style='gap:70px'>
        <div class='col' style='width:720px'>
          <div class='kicker'>Ready for the appointment</div>
          <h2>Everything for the visit, in one place</h2>
          <p class='cap'>What changed, when, and the missed dose with its reason, ready to discuss with the doctor or pharmacist.</p>
          <div style='margin-top:26px;display:flex'>{card('s06b-missed-dose', 560)}</div>
          <div class='pill' style='background:#fff;border:2px solid #eee9e0;align-self:flex-start;margin-top:14px'>Nothing is sent automatically · Not sent</div>
        </div>
        {phone('s06a-appointment-phone', 330)}
      </div></div>""")))
    # 9 Clinician + agent
    s.append(("clinician-agent", 7, page(f"""
      <div class='content'>
        <div class='kicker'>What the clinician sees · the agent at work</div>
        <h2 style='font-size:50px'>It decides what to look at, cites every statement, and is checked</h2>
        <div class='row' style='gap:40px;margin-top:26px'>
          <div class='col' style='width:640px'>
            <div class='desk'><img src='{SHOT}s07a-clinician-desktop.png' style='width:620px' alt=''></div>
            <p class='cap'>What changed and when, with exact values and sources.</p>
          </div>
          <div class='col' style='width:1080px'>
            <div class='desk' style='height:400px'><img src='{SHOT}s07b-qa-trail-desktop.png' style='width:1060px' alt=''></div>
            <div class='callout' style='position:static'><b>How AURA looked</b>: which records it read, then “A second check reviewed 10 statements; 1 removed as unsupported”. It can only read; it never changes the record or the treatment.</div>
          </div>
        </div>
      </div>""")))
    # 10 Safety
    s.append(("safety-first", 8, page(f"""
      <div class='content'><div class='row' style='gap:80px'>
        <div class='col' style='width:900px'>
          <div class='kicker'>Safety first</div>
          <h2>Anything a patient types is safety-checked first</h2>
          <div class='points'>
            {point('coral', 'If there is a concern, fixed safety resources take over the screen and the AI steps back.')}
            {point('sunny', 'Those messages are never AI-written.')}
            {point('lilac', 'Asking to double a dose goes to safety, not to an answer.')}
          </div>
        </div>
        {phone('s08-safety-phone', 330)}
      </div></div>""")))
    # 11-12 diagrams full bleed
    s.append(("architecture", 9, page(f"<img class='full' src='{DIAG}system-overview.png' alt=''>", brand=False, foot=False)))
    s.append(("agent-loop", 9, page(f"<img class='full' src='{DIAG}agent-investigation.png' alt=''>", brand=False, foot=False)))
    s.append(("safety-precedence", 9, page(f"<img class='full' src='{DIAG}safety-precedence.png' alt=''>", brand=False, foot=False)))
    # 14 trade-offs
    s.append(("trade-offs", 9, page(f"""
      <div class='content'>
        <div class='kicker'>Key design trade-offs</div>
        <h2>Signals propose, rules decide, AI words it</h2>
        <div class='points' style='margin-top:40px;max-width:1500px'>
          {point('blue', '<b>Deterministic state, flexible language</b> — engines own personal baselines and safety; AI writes words and investigates.')}
          {point('sunny', '<b>Quiet patient surface, deep clinician inspection</b> — one record, two views.')}
          {point('lilac', '<b>Strict checks, honest fallback</b> — numbers, dates and citations are checked plus an independent verifier; failures show related facts and say why.')}
          {point('leaf', '<b>Curated medication information</b> — AI only matches a question to an approved topic.')}
          {point('coral', '<b>Synthetic data now, private hosting later</b> — a hospital would run the model on its own infrastructure.')}
        </div>
      </div>""")))
    # 15 fit
    rows = [
        ("Medication understanding", "Approved information about the person's own prescription; AI matches a question to an approved topic; honest “check with your pharmacist” when it can't answer", "built", "Built"),
        ("Medication management", "One tap a day: taken, not yet, skipped (no push reminders yet)", "built", "In the demo"),
        ("Adherence support", "“What got in the way?” reasons, carried to the visit note", "built", "In the demo"),
        ("Health tracking", "Wearable signals against the person's own usual and recent pattern", "built", "Built"),
        ("Preventive health", "Refill and medication-review dates; screenings and vaccinations not yet", "partial", "Partial"),
        ("Healthcare preparation", "Visit note with changes and missed doses, Not sent until the patient decides", "built", "Built"),
    ]
    body = "".join(f"<tr><td>{a}</td><td>{b}</td><td><span class='status {c}'>{d}</span></td></tr>" for a, b, c, d in rows)
    s.append(("challenge-fit", 10, page(f"""
      <div class='content' style='top:130px'>
        <div class='kicker'>Fit with the challenge</div>
        <h2 style='font-size:50px;margin-bottom:6px'>Six features the challenge asks for</h2>
        <table>{body}</table>
        <p class='cap' style='margin-top:6px'><b>Deliberately different:</b> AURA describes changes; it does not predict relapse or give medication advice.</p>
      </div>""")))
    # 16 how built
    s.append(("how-we-built-it", 11, page(f"""
      <div class='content'><div class='row' style='gap:80px;align-items:center'>
        <div class='col' style='width:900px'>
          <div class='kicker'>How we built it</div>
          <h2>Core first, then the agent, then the experience</h2>
          <div class='points'>
            {point('blue', 'Safety and personal-baseline engines first, then the read-only agent, then the patient experience')}
            {point('lilac', 'AI development tools, including Tencent CodeBuddy and Miora, working from written specs')}
            {point('leaf', 'Every change reviewed and tested before release')}
          </div>
          <p class='cap' style='margin-top:20px'><b>Our tip:</b> write down what must never change before asking an AI to build anything.</p>
        </div>
        <img src='{MEDIA}calm-state.svg' style='width:640px;border-radius:40px;box-shadow:0 20px 56px rgba(42,35,32,.12)' alt=''>
      </div></div>""")))
    # 17 impact
    s.append(("impact", 12, page(f"""
      <div class='content'><div class='row' style='gap:60px'>
        <div class='col' style='width:830px'>
          <div class='kicker'>Impact we would measure in a pilot</div>
          <div class='pill' style='background:#fff0d0;color:#8a5a00;align-self:flex-start'>Targets to measure, not results</div>
          <div class='points'>
            {point('sunny', 'Missed doses with a recorded reason')}
            {point('blue', 'Preparation time before visits')}
            {point('leaf', 'How many appointments start with a prepared note')}
          </div>
        </div>
        <div class='col' style='width:780px'>
          <div class='kicker'>Next</div>
          <p class='cap'>Push reminders, screenings and pharmacist-reviewed content; consented real wearables; private hosting.</p>
          <div class='kicker' style='margin-top:30px'>Limits</div>
          <p class='cap'>No diagnosis, relapse prediction or medication advice. Synthetic data only. Not clinically validated.</p>
          <img src='{MEDIA}breathing-circle.svg' style='width:300px;margin-top:40px;align-self:flex-end;border-radius:32px' alt=''>
        </div>
      </div></div>""")))
    # 18 close
    s.append(("close", 12, page(f"""
      <img class='full' src='{MEDIA}welcome-hero.svg' style='object-fit:cover' alt=''>
      <div class='full' style='background:linear-gradient(180deg,rgba(251,250,247,.15) 0%,rgba(251,250,247,.92) 58%)'></div>
      <div style='position:absolute;left:0;right:0;top:600px;text-align:center'>
        <h1 style='font-size:96px'>AURA Health</h1>
        <p class='lead' style='margin:22px auto 0;font-size:40px;max-width:1300px;color:#2a2320'>A calm companion between doctor visits, so both sides start the conversation on the same page.</p>
        <p class='cap' style='margin-top:30px'>aura-health.makodev58.com · github.com/e8aura-makodev58/aura-health</p>
      </div>""", brand=False, foot=False)))
    return s


def main():
    SLIDES.mkdir(exist_ok=True)
    for old in SLIDES.glob("*.html"):
        old.unlink()
    notes = scenes()
    manifest, seen = [], set()
    for index, (name, scene, markup) in enumerate(slides(), start=1):
        path = SLIDES / f"{index:02d}-{name}.html"
        path.write_text(markup)
        text = notes[scene] if scene not in seen else f"(Continues scene {scene}.)\n\n" + notes[scene]
        seen.add(scene)
        manifest.append({"slide": index, "file": path.name, "scene": scene, "notes": text})
    (HERE / "slides.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"{len(manifest)} slides")


if __name__ == "__main__":
    main()
