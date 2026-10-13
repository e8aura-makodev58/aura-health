// Records the live in-app guided story. Usage: node record_tour.cjs <base> <outdir> <phone|desk>
const {chromium}=require('playwright');const fs=require('fs');
const [base,out,mode]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
const cursor=()=>{const add=()=>{if(document.getElementById('rec-cursor'))return;const d=document.createElement('div');d.id='rec-cursor';
  Object.assign(d.style,{position:'fixed',left:'-40px',top:'-40px',width:'22px',height:'22px',borderRadius:'50%',background:'rgba(156,87,0,.35)',border:'2px solid rgba(156,87,0,.85)',zIndex:2147483647,pointerEvents:'none',transform:'translate(-50%,-50%)',transition:'width .15s,height .15s'});
  document.documentElement.appendChild(d);addEventListener('mousemove',e=>{d.style.left=e.clientX+'px';d.style.top=e.clientY+'px';},true);
  addEventListener('mousedown',()=>{d.style.width='14px';d.style.height='14px';},true);addEventListener('mouseup',()=>{d.style.width='22px';d.style.height='22px';},true);};
  if(document.readyState==='loading')addEventListener('DOMContentLoaded',add);else add();};
(async()=>{
 const [w,h]=mode==='desk'?[1600,900]:[390,844];
 const b=await chromium.launch();const c=await b.newContext({viewport:{width:w,height:h},recordVideo:{dir:out,size:{width:w,height:h}}});
 await c.addInitScript(cursor);await c.addInitScript(()=>{window.auraLandingInAutomation=true;window.auraWelcomeInAutomation=true;});
 const p=await c.newPage();const t0=Date.now();const marks=[];const errors=[];p.on('pageerror',e=>errors.push(e.message));
 const mark=label=>marks.push({label,t:(Date.now()-t0)/1000});const pause=ms=>new Promise(r=>setTimeout(r,ms));
 const click=async(selector,after=600)=>{const el=p.locator(selector).first();await el.waitFor({state:'visible',timeout:60000});const inView=await el.evaluate(n=>{const r=n.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;});if(!inView){await el.evaluate(n=>n.scrollIntoView({block:'center',behavior:'smooth'}));await pause(900);}const box=await el.boundingBox();
   await p.mouse.move(box.x+box.width/2,box.y+box.height/2,{steps:22});await pause(300);await p.mouse.down();await pause(80);await p.mouse.up();await pause(after);};
 const ready=async i=>{mark('wait_start_'+i);await p.waitForFunction(()=>{const n=document.querySelector('.tour-next');return n&&!n.disabled;},null,{timeout:240000}).catch(()=>errors.push('stuck '+i));mark('wait_end_'+i);};
 const status=()=>p.locator('.tour-status').innerText().catch(()=>'');
 await p.goto(base,{waitUntil:'networkidle'});await pause(1500);mark('start');await pause(3000);
 await click('#start-demo',300);await p.waitForSelector('.tour-card');await pause(5500);mark('intro_read');
 await click('.tour-next',300);
 const read={phone:[6000,8000,8500,9000,9500,9000,7000,11000,11000],desk:[2500,2500,2500,2500,2500,2500,11000,15000,1000]}[mode];
 for(let i=0;i<9;i++){
  await ready(i);mark('step_'+i);
  if(mode==='desk'&&i===7){
   for(let attempt=0;attempt<5&&/couldn't complete/.test(await status());attempt++){mark('fallback_'+attempt);await pause(3500);await click('.tour-retry',300);await ready('retry'+attempt);}
   mark('agent_result');await pause(4000);await p.mouse.move(w*0.35,h*0.4,{steps:15});await p.mouse.wheel(0,380);await pause(read[i]-4000);
  }else await pause(read[i]);
  mark('next_'+i);
  if(mode==='desk'&&i===7)break;
  await click('.tour-next',300);
 }
 if(mode==='phone'){await pause(1500);mark('finish');await pause(4500);await click('text=Show the safety example',300);mark('wait_safety');
  await p.waitForFunction(()=>document.getElementById('input-dialog').open,null,{timeout:20000}).catch(()=>errors.push('note box'));mark('note_open');
  await p.waitForSelector('#safety-panel:not([hidden])',{timeout:60000}).catch(()=>errors.push('safety'));mark('safety_shown');
  await p.waitForFunction(()=>/Safety takes priority/.test(document.querySelector('.tour-title')?.textContent||''),null,{timeout:60000}).catch(()=>errors.push('safety card'));mark('safety_card');await pause(10000);mark('end');}
 else mark('end');
 const video=await p.video().path();await c.close();
 fs.writeFileSync(`${out}/marks-tour-${mode}.json`,JSON.stringify({marks,video,errors},null,1));
 console.log(JSON.stringify({video,errors,marks:marks.map(m=>m.label+'@'+m.t.toFixed(1))}));await b.close();})();
