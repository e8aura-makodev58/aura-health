const {chromium}=require('playwright');const path=require('path');
const font='file://'+path.resolve('/home/makodev58/aura-health/aura_ui/media/nunito.woff2');
const mark='file://'+path.resolve('/home/makodev58/aura-health/aura_ui/media/aura-mark.svg');
const scenes=[
 ['s3','3 · A calm start','A breath first, then one short summary written from checked facts and compared with this person\'s own usual.'],
 ['s4','4 · My medication, my day','One tap a day. If a dose is skipped, AURA asks what got in the way. Medication answers come from approved information, and AURA says when it can\'t answer.'],
 ['s5','5 · Something changes','Three days of flu, simulated. AURA describes a recent change and offers a small, optional idea for today.'],
 ['s6','6 · Ready for the appointment','What changed, when, and the missed dose with its reason. Not sent until the patient decides.'],
 ['s8','8 · Safety first','Anything a patient types is safety-checked first. Fixed safety resources take over; the AI steps back.']];
const fs=require('fs');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
for(const [id,title,caption] of scenes){
 const html=`<html><head><style>@font-face{font-family:Nunito;src:url('${font}')}body{margin:0;width:1920px;height:1080px;background:#fbfaf7;font-family:Nunito,sans-serif;color:#2a2320;position:relative;overflow:hidden}
 .glow{position:absolute;left:-200px;top:-200px;width:1100px;height:1100px;border-radius:50%;background:radial-gradient(circle,#fdebd0 0%,rgba(251,250,247,0) 65%)}
 .phone{position:absolute;left:300px;top:30px;width:470px;height:1020px;border-radius:56px;background:#2a2320;box-shadow:0 30px 80px rgba(42,35,32,.18)}
 .text{position:absolute;left:900px;top:330px;width:880px}.eyebrow{font-weight:700;letter-spacing:.18em;color:#9c5700;font-size:26px;text-transform:uppercase;margin-bottom:22px}
 h1{font-size:72px;line-height:1.1;margin:0 0 30px;font-weight:800}p{font-size:36px;line-height:1.45;color:#5b524a;margin:0}
 .brand{position:absolute;left:900px;top:90px;display:flex;align-items:center;gap:18px;font-weight:800;letter-spacing:.2em;font-size:30px}.brand img{width:56px}
 .foot{position:absolute;left:900px;bottom:60px;font-size:24px;color:#8a8178}</style></head><body><div class="glow"></div><div class="phone"></div>
 <div class="brand"><img src="${mark}">AURA HEALTH</div><div class="text"><div class="eyebrow">Live demo</div><h1>${title}</h1><p>${caption}</p></div><div class="foot">Synthetic demo data · aura-health.makodev58.com</div></body></html>`;const file=path.resolve('bg/'+id+'.html');fs.writeFileSync(file,html);await p.goto('file://'+file);await p.evaluate(()=>document.fonts.ready);
 await p.waitForTimeout(400);await p.screenshot({path:`bg/${id}.png`});}
await b.close();})();
