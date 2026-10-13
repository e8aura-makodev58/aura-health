// Records script v2 scenes 3–8 on the live site. One synthetic session throughout.
// Writes webm per page plus marks.json (scene windows and AI waits to trim).
const {chromium}=require('playwright');
const fs=require('fs');
const base=process.argv[2], out=process.argv[3];
fs.mkdirSync(out,{recursive:true});
const cursor=()=>{const add=()=>{if(document.getElementById('rec-cursor'))return;const d=document.createElement('div');d.id='rec-cursor';
  Object.assign(d.style,{position:'fixed',left:'-40px',top:'-40px',width:'22px',height:'22px',borderRadius:'50%',background:'rgba(156,87,0,.35)',border:'2px solid rgba(156,87,0,.85)',zIndex:2147483647,pointerEvents:'none',transform:'translate(-50%,-50%)',transition:'width .15s,height .15s'});
  document.documentElement.appendChild(d);
  addEventListener('mousemove',e=>{d.style.left=e.clientX+'px';d.style.top=e.clientY+'px';},true);
  addEventListener('mousedown',()=>{d.style.width='14px';d.style.height='14px';},true);addEventListener('mouseup',()=>{d.style.width='22px';d.style.height='22px';},true);};
  if(document.readyState==='loading')addEventListener('DOMContentLoaded',add);else add();};
(async()=>{
 const b=await chromium.launch();const marks={};let t0={};const errors=[];
 const mark=(page,label)=>{const v=page.__name;(marks[v]=marks[v]||[]).push({label,t:(Date.now()-t0[v])/1000});};
 const pause=ms=>new Promise(r=>setTimeout(r,ms));
 const moveClick=async(page,selector,opts={})=>{const el=page.locator(selector).first();await el.waitFor({state:'visible',timeout:30000});await el.evaluate(n=>n.scrollIntoView({block:'center',behavior:'smooth'}));await pause(700);await pause(300);let box=await el.boundingBox();for(let i=0;i<10;i++){await pause(120);const next=await el.boundingBox();if(next&&box&&Math.abs(next.y-box.y)<1)break;box=next;}
   const x=box.x+box.width/2,y=box.y+box.height/2;await page.mouse.move(x,y,{steps:25});await pause(350);await page.mouse.down();await pause(80);await page.mouse.up();await pause(opts.after??900);};
 const smoothScroll=async(page,selector)=>{await page.evaluate(sel=>document.querySelector(sel)?.scrollIntoView({behavior:'smooth',block:'center'}),selector);await pause(1400);};
 const typeSlow=async(page,selector,text)=>{await moveClick(page,selector,{after:300});await page.locator(selector).fill('');await page.locator(selector).pressSequentially(text,{delay:55});await pause(600);};
 const open=async(name,w,h,storage)=>{const c=await b.newContext({viewport:{width:w,height:h},deviceScaleFactor:2,storageState:storage,recordVideo:{dir:out,size:{width:w,height:h}}});
   await c.addInitScript(cursor);await c.addInitScript(()=>{window.auraLandingInAutomation=true;window.auraWelcomeInAutomation=true;});
   const p=await c.newPage();p.__name=name;t0[name]=Date.now();p.on('pageerror',e=>errors.push(name+': '+e.message));return {c,p};};
 // Desktop: scene 7 (same session cookie)
 let {c:deskCtx,p:desk}=await open('desk',1600,900);  // fresh session: the agent scene is recorded on the record before the flu
 await desk.goto(base,{waitUntil:'networkidle'});await pause(1500);mark(desk,'scene7_start');
 await moveClick(desk,'#clinician-role',{after:300});mark(desk,'wait_brief_start');
 await desk.waitForFunction(()=>/AI-written/.test(document.querySelector('#agent-clinician_brief .agent-disclosure')?.textContent||''),null,{timeout:90000}).catch(()=>errors.push('brief'));
 mark(desk,'wait_brief_end');await pause(8000);
 for(let attempt=1;attempt<=3;attempt++){
  await smoothScroll(desk,'.record-questions');await typeSlow(desk,'#agent-question-text','When did sleep timing change, and was anything reported around then?');
  await moveClick(desk,'.question-submit',{after:300});mark(desk,'wait_qa_start_'+attempt);
  await desk.waitForFunction(()=>/How AURA looked/.test(document.querySelector('#agent-record_qa .investigation-trail')?.textContent||''),null,{timeout:120000}).catch(()=>errors.push('qa'));
  mark(desk,'wait_qa_end_'+attempt);
  const ok=/AI-written/.test(await desk.locator('#agent-record_qa .agent-disclosure').first().innerText().catch(()=>''));
  mark(desk,(ok?'qa_success_':'qa_fallback_')+attempt);
  await desk.evaluate(()=>{const el=document.querySelector('#agent-record_qa');window.scrollTo({top:el.getBoundingClientRect().top+scrollY-140,behavior:'smooth'});});await pause(9000);
  if(ok)break;
 }
 await desk.mouse.wheel(0,420);await pause(5000);mark(desk,'scene7_end');
 const vids={desk:await desk.video().path()};await deskCtx.close();
 fs.writeFileSync(out+'/marks-desk.json',JSON.stringify({marks,vids,errors},null,2));console.log(JSON.stringify({marks,vids,errors},null,2));
 await b.close();})();
