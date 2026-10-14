// Records a real usage session on the live site, 1920×1080 landscape video (no guided story, no safety
// example). Every AI wait is marked (wait_start/wait_end) so assemble_usage.py can trim only waiting.
// Usage: node record_usage.cjs <base-url> <outdir>
const {chromium} = require('playwright'); const fs = require('fs');
const [base, out] = process.argv.slice(2); fs.mkdirSync(out, {recursive: true});
const NOTE = 'I enjoyed painting today for 3 hours';
const cursor = () => { const add = () => { if (document.getElementById('rec-cursor')) return; const d = document.createElement('div'); d.id = 'rec-cursor';
  Object.assign(d.style, {position:'fixed', left:'-40px', top:'-40px', width:'24px', height:'24px', borderRadius:'50%', background:'rgba(156,87,0,.33)', border:'2px solid rgba(156,87,0,.85)', zIndex:2147483647, pointerEvents:'none', transform:'translate(-50%,-50%)', transition:'width .15s,height .15s'});
  document.documentElement.appendChild(d); addEventListener('mousemove', e => { d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', () => { d.style.width = '15px'; d.style.height = '15px'; }, true); addEventListener('mouseup', () => { d.style.width = '24px'; d.style.height = '24px'; }, true); };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', add); else add(); };
(async () => {
  const b = await chromium.launch(); // 1440×810 CSS pixels at 4/3 device scale: the page reads about a third larger and still fills 1920×1080.
  const c = await b.newContext({viewport:{width:1440, height:810}, deviceScaleFactor:4/3, recordVideo:{dir:out, size:{width:1920, height:1080}}});
  await c.addInitScript(cursor); await c.addInitScript(() => { window.auraLandingInAutomation = true; window.auraWelcomeInAutomation = true; });
  const p = await c.newPage(); const t0 = Date.now(); const marks = []; const errors = []; p.on('pageerror', e => errors.push(e.message));
  const mark = label => marks.push({label, t:(Date.now() - t0) / 1000}); const pause = ms => new Promise(r => setTimeout(r, ms));
  const view = async sel => { const el = p.locator(sel).first(); await el.waitFor({state:'visible', timeout:90000});
    const inView = await el.evaluate(n => { const r = n.getBoundingClientRect(); return r.top >= 70 && r.bottom <= innerHeight - 40; });
    if (!inView) { await el.evaluate(n => n.scrollIntoView({block:'center', behavior:'smooth'})); await pause(1100); } return el; };
  const point = async sel => { const el = await view(sel); const box = await el.boundingBox(); await p.mouse.move(box.x + Math.min(box.width/2, 260), box.y + box.height/2, {steps:24}); await pause(250); return el; };
  const click = async (sel, after = 700) => { await point(sel); await p.mouse.down(); await pause(90); await p.mouse.up(); await pause(after); };
  const waitFor = async (label, fn, arg, timeout = 180000) => { mark('wait_start:' + label); await p.waitForFunction(fn, arg, {timeout}).catch(() => errors.push('timeout ' + label)); mark('wait_end:' + label); };
  const type = async (sel, text) => { await p.locator(sel).fill(''); await click(sel, 300); await p.keyboard.press('End'); await p.keyboard.type(text, {delay:65}); await pause(600); };
  const ask = async (q, label) => {
    await p.evaluate(() => document.getElementById('agent-record_qa').replaceChildren());
    await type('#agent-question-text', q); await click('.question-submit', 300);
    await waitFor(label, () => document.querySelector('#agent-record_qa .investigation-trail'));
    await pause(500); await view('#agent-record_qa'); await p.mouse.move(520, 450, {steps:15}); await pause(9000); };

  await p.goto(base, {waitUntil:'networkidle'}); await pause(1500); mark('start'); await pause(3500);
  // 1 · Patient: a calm start
  await click('#start-patient', 300); mark('patient');
  await p.waitForSelector('#breath-welcome:not([hidden])', {timeout:30000}).catch(() => {}); await pause(5000);
  await click('#breath-continue', 300);
  await waitFor('recap', () => document.querySelector('.patient-recap') && !document.querySelector('.recap-pending'), null, 60000);
  await point('#month-recap'); await pause(6000); mark('summary_read');
  // 2 · Today's dose and medication
  await click('#dose-card .dose-taken', 300); await waitFor('dose', () => /Recorded/.test(document.getElementById('dose-saved')?.textContent || ''), null, 30000); await pause(3000);
  await click('.topic-chip[data-topic-id="missed_dose"]', 300); await waitFor('medication', () => !document.getElementById('medication-answer').hidden, null, 30000);
  await point('#medication-answer'); await pause(7000); mark('medication_read');
  // 3 · The positive note
  await p.evaluate(() => scrollTo({top:0, behavior:'smooth'})); await pause(900);
  await click('#talk', 900); await type('#input-text', NOTE); mark('note_typed'); await pause(800);
  await click('#send-input', 300);
  await waitFor('note_reply', () => !document.getElementById('communication-card').hidden && document.getElementById('communication-message').textContent.length > 0, null, 90000);
  await point('#communication-card'); await pause(7000); mark('reply_read');
  await waitFor('activities', () => !document.getElementById('activities-card').hidden, null, 60000);
  await point('#activities-card'); await pause(7000); mark('activities_read');
  // 4 · Ideas picked for today
  if (await p.locator('#suggestion-card').isVisible()) {
    await waitFor('ideas', () => !document.getElementById('suggestion-why').hidden, null, 60000);
    await point('#suggestion-card'); await pause(6000);
    await click('.suggestion-chip', 300); await waitFor('idea_ack', () => !document.getElementById('suggestion-ack').hidden, null, 60000);
    await point('#suggestion-ack'); await pause(6000); mark('idea_done');
  }
  await point('#coming-up-card').catch(() => {}); await pause(3000);
  // 5 · Getting ready for the appointment
  await p.evaluate(() => { location.hash = 'review'; scrollTo(0, 0); }); await pause(2500); mark('review');
  await click('[data-agent-role="visit_prep"]', 300);
  await waitFor('visit_note', () => { const o = document.getElementById('agent-visit_prep'); return o && o.querySelector('.visit-line, .agent-claim'); });
  await point('#agent-visit_prep'); await pause(8000); mark('visit_read');
  await point('#sharing-card'); await pause(7000); mark('sharing_read');
  // 6 · The clinician's view
  await p.evaluate(() => scrollTo({top:0, behavior:'smooth'})); await pause(800);
  await click('#clinician-role', 300); await waitFor('clinician', () => document.querySelector('#agent-clinician_brief .clinician-finding'), null, 60000);
  await pause(1200); await point('#agent-clinician_brief'); await pause(7000); mark('findings_read');
  await point('#activity-summary'); await pause(7000); mark('activity_summary_read');
  await ask('Has the patient mentioned spending more time on hobbies recently?', 'qa_hobbies'); mark('qa_hobbies_read');
  await ask('What percentage of the last 30 days were recorded as Rough check-ins?', 'qa_percent'); mark('qa_percent_read');
  // 7 · The patient decides what is shared
  await p.evaluate(() => scrollTo({top:0, behavior:'smooth'})); await pause(800);
  await click('#demo-toggle', 900); await click('#share-minimum', 1500); await click('#demo-toggle', 600); mark('minimum');
  await point('#sharing-status'); await pause(7000); mark('status_read');
  await ask("Do we have access to the patient's notes?", 'qa_notes'); mark('qa_notes_read');
  // 8 · Back to the patient, calm
  await p.evaluate(() => scrollTo({top:0, behavior:'smooth'})); await pause(800);
  await click('#patient-role', 300); await p.evaluate(() => { location.hash = 'home'; scrollTo(0, 0); }); await pause(5000); mark('end');
  const video = await p.video().path(); await c.close(); await b.close();
  fs.writeFileSync(`${out}/marks-usage.json`, JSON.stringify({marks, video, errors}, null, 1));
  console.log(JSON.stringify({video, errors, marks:marks.map(m => m.label + '@' + m.t.toFixed(1))}));
})();
