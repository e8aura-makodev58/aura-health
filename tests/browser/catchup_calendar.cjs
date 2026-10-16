/* Past medication records, calendar, welcome back and coverage (spec §9.5 IDs). Hosted synthetic fixture only. */
'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL;
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw Error('Local synthetic fixture only');
const noScroll=page=>page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1
 &&[...document.querySelectorAll('#med-update-dialog[open],#med-update-preview,#calendar-grid,#calendar-detail')].every(node=>node.scrollWidth<=node.clientWidth+1));
const shift=(iso,by)=>{const d=new Date(iso+'T00:00:00Z');d.setUTCDate(d.getUTCDate()+by);return d.toISOString().slice(0,10);};

async function run(browser,width){
 const tag=width<500?'PHONE':'LAPTOP';
 const context=await browser.newContext({viewport:{width,height:900}}),errors=[];
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 const loaded=()=>page.waitForFunction(()=>window.auraAgentContext().record&&document.getElementById('notice').hidden);
 const api=async path=>(await page.request.get(`${base}/patients/${encodeURIComponent(await page.evaluate(()=>window.auraAgentContext().patientId))}${path}`)).json();
 await page.goto(base);await loaded();
 try{
 await page.getByRole('button',{name:'Patient',exact:true}).click();
 // 1 · the gentle prompt on the dose card
 await page.waitForSelector('#med-update-line:not([hidden])');
 assert.match(await page.locator('#med-update-line').innerText(),/of the last 14 days have no medication record/);
 await page.locator('#dose-card .dose-btn[data-dose="ACKNOWLEDGED"]').click();
 await page.waitForFunction(()=>window.auraCompanionData?.dose_today?.status==='ACKNOWLEDGED',null,{timeout:20000});
 console.log(`CU1_${tag}_PROMPT PASS`);
 // 1b · icon shortcuts under the heading: each visible card has one; a jump brings the card to the top
 assert.equal(await page.locator('#home-shortcuts a:not([hidden])').count(),7);
 const [navY,recapY]=await page.evaluate(()=>[document.getElementById('home-shortcuts').getBoundingClientRect().top,document.getElementById('month-recap').getBoundingClientRect().top]);
 assert.ok(navY<recapY,'shortcuts sit above the summary');
 await page.locator('#home-shortcuts a[data-jump="suggestion-card"]').click();
 // Content above may still settle (the summary finishes writing), so allow the card anywhere near the top.
 await page.waitForFunction(()=>{const top=document.getElementById('suggestion-card').getBoundingClientRect().top;return (top>=-40&&top<=innerHeight*0.4)||innerHeight+scrollY>=document.documentElement.scrollHeight-2;},null,{timeout:10000});
 assert.equal(await page.evaluate(()=>document.activeElement.id),'suggestion-card');
 await page.evaluate(()=>scrollTo(0,0));
 console.log(`CU1b_${tag}_SHORTCUTS PASS`);
 // 1c · Language menu in the header: four Singapore languages in their own scripts; English only for now
 assert.equal(await page.locator('#language-card').count(),0,'no card on the home page');
 await page.evaluate(()=>scrollTo(0,0));await page.locator('#language-button').click();
 await page.waitForSelector('#language-menu:not([hidden])');
 const langs=await page.$$eval('#language-menu [data-lang]',items=>items.map(i=>[i.dataset.lang,i.getAttribute('aria-checked'),i.getAttribute('aria-disabled')]));
 assert.deepEqual(langs,[['en','true',null],['zh','false','true'],['ms','false','true'],['ta','false','true']]);
 assert.match(await page.locator('#language-menu').innerText(),/中文[\s\S]*Bahasa Melayu[\s\S]*தமிழ்[\s\S]*future release/);
 await page.locator('#language-menu [data-lang="zh"]').click({force:true});
 assert.equal(await page.locator('#language-menu').isVisible(),true,'a greyed language does nothing');
 assert.equal(await noScroll(page),true);
 await page.keyboard.press('Escape');assert.equal(await page.locator('#language-menu').isHidden(),true);
 console.log(`CU1c_${tag}_LANGUAGE_MENU PASS`);
 // 2 · tap-only: today's recorded dose is locked, two past days set by tapping, nothing saved before Save
 await page.locator('#med-update-open').click();
 await page.waitForSelector('#med-update-dialog[open]');
 assert.equal(await page.locator('#med-update-save').isDisabled(),true);
 await page.locator('#med-update-tap').click();
 const days=page.locator('#med-update-preview .med-day');
 assert.equal(await days.count(),14);
 const last=days.last();
 assert.equal(await last.getAttribute('data-locked'),'true');assert.equal(await last.isDisabled(),true);
 const window1=await api('/medication/update-window');
 const open1=window1.days.filter(d=>!d.locked).map(d=>d.date);
 assert.ok(open1.length>=2,'two unrecorded days to fill');
 const aDate=open1.at(-2),bDate=open1.at(-1);
 await page.locator(`#med-update-preview .med-day[data-date="${aDate}"]`).click();
 // Keyboard: focus stays on the same day after each change, and the change is announced.
 await page.locator(`#med-update-preview .med-day[data-date="${bDate}"]`).focus();
 await page.keyboard.press('Enter');await page.keyboard.press('Enter');
 assert.equal(await page.evaluate(()=>document.activeElement?.dataset.date),bDate,'focus kept');
 assert.match(await page.locator('#med-update-message').innerText(),/: Missed\.$/);
 assert.equal(await page.locator(`#med-update-preview .med-day[data-date="${aDate}"]`).getAttribute('data-status'),'ACKNOWLEDGED');
 assert.equal(await page.locator(`#med-update-preview .med-day[data-date="${bDate}"]`).getAttribute('data-status'),'MISSED');
 assert.equal(await noScroll(page),true,'dialog fits');
 await page.locator('#med-update-save').click();
 await page.waitForSelector('#med-update-result:not([hidden])');
 assert.match(await page.locator('#med-update-result').innerText(),/Saved 2 days/);
 assert.equal(await page.locator(`#med-update-preview .med-day[data-date="${aDate}"]`).getAttribute('data-locked'),'true');
 await page.locator('#med-update-close').click();
 console.log(`CU2_${tag}_TAP_SAVE_LOCKED PASS`);
 // 3 · typed update (agent proposal mocked): "most days" styling and the one question
 await page.route('**/medication/update/interpret',async route=>{
  const window=await (await page.request.get(`${base}/patients/${encodeURIComponent(await page.evaluate(()=>window.auraAgentContext().patientId))}/medication/update-window`)).json();
  const open=window.days.filter(d=>!d.locked);
  await route.fulfill({json:{status:'PROPOSED',window,question:`Were ${open[1].weekday} the only days you missed?`,out_of_window:[],advice_request:false,message:null,
   days:[{date:open[0].date,status:'ACKNOWLEDGED',basis:'from_most_days'},{date:open[1].date,status:'MISSED',basis:'explicit'}]}});
 });
 await page.locator('#med-update-open').click();await page.waitForSelector('#med-update-dialog[open]');
 await page.locator('#med-update-text').fill('I took it most days except one');
 await page.locator('#med-update-interpret').click();
 await page.waitForSelector('#med-update-question:not([hidden])');
 assert.equal(await page.locator('#med-update-preview .med-day[data-basis="from_most_days"]').count(),1);
 assert.equal(await page.locator('#med-update-save').isDisabled(),true,'question first');
 const dashed=await page.locator('#med-update-preview .med-day[data-basis="from_most_days"]').evaluate(n=>getComputedStyle(n).borderTopStyle);
 assert.equal(dashed,'dashed','"most days" styling');
 await page.locator('#med-update-no').click();
 assert.equal(await page.locator('#med-update-preview .med-day[data-basis="from_most_days"]').count(),0,'No leaves them unresolved');
 assert.equal(await page.locator('#med-update-save').isDisabled(),false);
 await page.locator('#med-update-close').click();
 await page.locator('#med-update-open').click();await page.waitForSelector('#med-update-dialog[open]');
 await page.locator('#med-update-text').fill('I took it most days except one');await page.locator('#med-update-interpret').click();
 await page.waitForSelector('#med-update-question:not([hidden])');await page.locator('#med-update-yes').click();
 assert.equal(await page.locator('#med-update-preview .med-day[data-basis="from_most_days"]').count(),0,'Yes confirms them');
 assert.equal(await page.locator('#med-update-preview .med-day[data-basis="explicit"]').count(),2);
 assert.equal(await page.locator('#med-update-save').isDisabled(),false);
 await page.locator('#med-update-close').click();await page.unroute('**/medication/update/interpret');
 console.log(`CU3_${tag}_MOST_DAYS_QUESTION PASS`);
 // 4 · patient calendar: reported-later markers and day detail
 await page.locator('#calendar-link').click();
 await page.waitForSelector('#calendar-view:not([hidden]) #calendar-grid .cal-day');
 const cell=page.locator(`#calendar-grid .cal-day[data-date="${bDate}"]`);
 assert.equal(await cell.locator('.cal-med').getAttribute('data-status'),'MISSED');
 assert.equal(await cell.locator('.cal-med').getAttribute('data-reported-later'),'true');
 assert.ok(await page.locator('#calendar-grid .cal-checkin[data-state]').count()>0);
 assert.match(await page.locator('#calendar-legend').innerText(),/blank day means nothing was recorded/);
 await cell.click();await page.waitForSelector('#calendar-detail:not([hidden])');
 assert.match(await page.locator('#calendar-detail').innerText(),/Missed · filled in later/);
 assert.equal(await noScroll(page),true,'calendar and detail fit');
 const today=(await api('/coverage')).today;
 const future=page.locator(`#calendar-grid .cal-day[data-date="${shift(today,1)}"]`);
 if(await future.count())assert.equal(await future.isDisabled(),true,'future days are not selectable');
 await page.locator('#calendar-prev').click();
 await page.waitForFunction(m=>document.getElementById('calendar-month').textContent!==m,await page.locator('#calendar-month').innerText());
 console.log(`CU4_${tag}_PATIENT_CALENDAR PASS`);
 // 5 · clinician calendar: Everything vs Minimum only; coverage strip
 await page.getByRole('button',{name:'Clinician',exact:true}).click();
 await page.waitForFunction(()=>/filled in later/.test(document.getElementById('record-coverage').textContent)&&!document.getElementById('record-coverage').hidden);
 assert.match(await page.locator('#record-coverage').innerText(),/^Record coverage: last medication record \w{3} \d+ \w{3} \(2 of the last 14 days filled in later\)/);
 await page.locator('#clinician-calendar-link').click();
 await page.waitForSelector('#calendar-view:not([hidden]) #calendar-grid .cal-day');
 assert.ok(await page.locator('#calendar-grid .cal-checkin').count()>0,'everything shared');
 await page.evaluate(()=>window.auraSaveSharing({notes:false,readings:false,checkin_history:false,activity_details:false}));
 await page.evaluate(()=>{location.hash='patterns';});await page.waitForSelector('#patterns-view:not([hidden])');
 await page.locator('#clinician-calendar-link').click();
 await page.waitForFunction(()=>!document.querySelector('#calendar-view').hidden&&document.querySelectorAll('#calendar-grid .cal-day').length&&!document.querySelector('#calendar-grid .cal-checkin'));
 assert.equal(await page.locator(`#calendar-grid .cal-day[data-date="${bDate}"] .cal-med`).getAttribute('data-status'),'MISSED','medication stays');
 await page.locator(`#calendar-grid .cal-day[data-date="${bDate}"]`).click();await page.waitForSelector('#calendar-detail:not([hidden])');
 assert.match(await page.locator('#calendar-detail').innerText(),/Not shared by the patient: detailed readings/);
 assert.equal(await page.locator('#calendar-update-day').count(),0,'clinician cannot edit the patient\'s records');
 await page.evaluate(()=>window.auraSaveSharing({notes:true,readings:true,checkin_history:true,activity_details:true}));
 assert.equal(await noScroll(page),true);
 console.log(`CU5_${tag}_CLINICIAN_SHARING PASS`);
 // 6 · welcome back after a long gap (coverage mocked)
 const real=await api('/coverage');
 await page.route('**/coverage',route=>route.fulfill({json:{...real,last_medication_day:shift(real.today,-19),last_checkin_day:shift(real.today,-18)}}));
 await page.getByRole('button',{name:'Patient',exact:true}).click();
 await page.evaluate(()=>{location.hash='home';});
 await page.waitForSelector('#welcome-back:not([hidden])');
 assert.match(await page.locator('#welcome-back').innerText(),/Welcome back\. You can carry on from today/);
 await page.unroute('**/coverage');
 console.log(`CU6_${tag}_WELCOME_BACK PASS`);
 // 7 · after the safety example (outside the story), a visible demo-only reset starts fresh
 const before=await page.evaluate(()=>window.auraAgentContext().patientId);
 await page.locator('#talk').click();await page.waitForSelector('#input-dialog[open]');
 await page.locator('[data-fixture="fixture safety concern"]').click();await page.locator('#send-input').click();
 await page.waitForSelector('#safety-panel:not([hidden]) #safety-demo-reset:not([hidden])',{timeout:30000});
 const inView=await page.locator('#safety-reset-demo').evaluate(b=>{const r=b.getBoundingClientRect(),p=document.getElementById('safety-panel').getBoundingClientRect();return r.top>=p.top&&r.bottom<=p.bottom&&r.bottom<=innerHeight;});
 assert.equal(inView,true,'reset visible without scrolling the panel');
 page.once('dialog',dialog=>dialog.accept());
 await page.locator('#safety-reset-demo').click();
 await page.waitForFunction(()=>document.getElementById('safety-panel').hidden&&window.auraAgentContext().record,null,{timeout:60000});
 assert.equal(await page.evaluate(()=>window.auraAgentContext().patientId),before,'same patient, fresh');
 assert.equal(await page.locator('#med-update-line').isVisible(),true,'fresh record: prompt is back');
 console.log(`CU7_${tag}_SAFETY_PANEL_RESET PASS`);
 assert.deepEqual(errors,[]);
 }finally{
  // Leave the session as found even if a check fails.
  await page.evaluate(()=>window.auraSaveSharing?.({notes:true,readings:true,checkin_history:true,activity_details:true})).catch(()=>{});
  await context.close();
 }
}
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{await run(browser,390);await run(browser,1280);}finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
