/* Same production projection in two presentations; engineering UX, not clinical validation. */
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs/promises"),path=require("node:path");
const {chromium}=require("playwright");
const base=process.env.AURA_BROWSER_URL||"http://127.0.0.1:8016";
const out=process.env.AURA_BROWSER_ARTIFACTS||"/tmp/aura-dual-view-browser-artifacts";
if(!["127.0.0.1","localhost"].includes(new URL(base).hostname))throw Error("Local synthetic server required");
async function main(){
  await fs.mkdir(out,{recursive:true});
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:"reduce"});
  const page=await context.newPage(),errors=[],results=[],writes=[];
  page.on("pageerror",error=>errors.push(error.message));
  page.on("request",request=>{if(request.method()==="POST")writes.push(request.url());});
  async function check(name,work){await work();results.push({name,result:"PASS"});console.log(name+" PASS");}
  try{
    await page.goto(base);await page.waitForSelector("#patterns-view:not([hidden])");
    await page.waitForFunction(()=>document.getElementById("notice").hidden);
    const catalog=await(await context.request.get(base+"/demo/scenarios")).json();
    const id=key=>catalog.scenarios.find(row=>row.id===key).patient_id;
    async function choose(key){
      if(await page.locator("#demo-panel").isHidden())await page.locator("#demo-toggle").click();
      await page.locator("#scenario").selectOption(id(key));
      try { await page.waitForFunction(()=>document.getElementById("notice").hidden&&document.getElementById("workspace-patient").textContent.length>0); }
      catch(error){console.error("Browser errors",errors,"notice",await page.locator("#notice").textContent());await page.screenshot({path:path.join(out,"failure.png"),fullPage:true});throw error;}
      await page.locator("#demo-toggle").click();
    }
    async function role(name){await page.locator("#"+name+"-role").click();await page.waitForFunction(value=>document.body.dataset.role===value,name);}
    async function navigate(name){await page.evaluate(value=>location.hash=value,name);await page.waitForSelector("#"+name+"-view:not([hidden])");}
    await check("DV1_CLINICIAN_FIRST",async()=>{
      assert.equal(await page.locator("#scenario").inputValue(),id("B"));
      assert.equal(await page.locator("#evidence-charts .chart-card").count(),4);
      assert.ok(await page.locator("#changes-overview>section").count()<=3);
      assert.match(await page.locator("#clinician-disclosure").innerText(),/Clinician view.*Demo/);
      assert.match(await page.locator('#about-view').textContent(),/real clinician would see only information approved by the patient/);
      assert.equal(await page.locator("#talk").isVisible(),false);
      await page.screenshot({path:path.join(out,"clinician-b-laptop.png"),fullPage:true});
    });
    await check("DV2_TOGGLE_READ_ONLY_SAME_RECORD",async()=>{
      const before=await(await context.request.get(base+`/patients/${id("B")}/status`)).json();
      const count=writes.filter(url=>!url.includes('/agent/')).length;
      await role("patient");assert.equal(await page.locator("#home-view").isVisible(),true);
      assert.equal(await page.locator("#evidence-charts").isVisible(),false);
      await page.getByRole("link",{name:"See my full data"}).click();
      await role("clinician");assert.equal(await page.locator("#scenario").inputValue(),id("B"));
      assert.equal(writes.filter(url=>!url.includes('/agent/')).length,count);
      assert.deepEqual(await(await context.request.get(base+`/patients/${id("B")}/status`)).json(),before);
    });
    await check("DV3_MINIMAL_PATIENT_HOME",async()=>{
      await choose("stable");await role("patient");
      assert.equal(await page.locator("#records-panel").getAttribute("open"),null);
      assert.equal(await page.locator(".checkin-options").isVisible(),false);
      assert.equal(await page.locator("#signal-list").isVisible(),false);
      assert.equal(await page.locator(".bottom-nav").isVisible(),false);
      await page.setViewportSize({width:390,height:844});
      for(const selector of ["#quiet-card", "#talk", ".patient-links"]){const box=await page.locator(selector).boundingBox();assert.ok(box.y>=0&&box.y+box.height<=844,selector);}
      await page.screenshot({path:path.join(out,"patient-stable-phone.png"),fullPage:true});
    });
    await check("DV4_RANGE_DISPLAY_ONLY",async()=>{
      await choose("B");await role("clinician");
      const count=writes.length, before=await(await context.request.get(base+`/patients/${id("B")}/evidence`)).json();
      const recent=await page.locator(".chart-observed").count();
      await page.locator("#chart-range").selectOption("all");
      assert.ok(await page.locator(".chart-observed").count()>recent);
      assert.equal(writes.length,count);
      assert.deepEqual(await(await context.request.get(base+`/patients/${id("B")}/evidence`)).json(),before);
      await page.locator("#chart-range").selectOption("56");
    });
    await check("DV5_HELD_REFERENCE_VISIBLE",async()=>{
      await choose("D");assert.equal(await page.locator(".held-item").count(),2);
      assert.match(await page.locator("#held-list").textContent(),/reference is unchanged/);
      assert.match(await page.locator("#held-list").textContent(),/Repeat prompts/);
      assert.match(await page.locator("#context-list").textContent(),/new stable work schedule/);
      await page.screenshot({path:path.join(out,"clinician-d-phone.png"),fullPage:true});
    });
    await check("DV6_GAP_RETURN_NO_ZERO_INTERPOLATION",async()=>{
      await choose("E-gap");assert.match(await page.locator(".chart-status").first().innerText(),/Data unavailable/);
      await page.locator("#chart-range").selectOption("all");
      const evidence=await(await context.request.get(base+`/patients/${id("E-gap")}/evidence`)).json();
      const rawCount=evidence.signals.reduce((sum,row)=>sum+row.observations.filter(point=>!point.deferred).length,0);
      assert.equal(await page.locator(".chart-observed").count(),rawCount);
      await choose("E");assert.match(await page.locator(".chart-status").first().innerText(),/re-established/);
      assert.match(await page.locator("#about-view").textContent(),/no governed automatic exit/);
      await page.screenshot({path:path.join(out,"clinician-e-return-phone.png"),fullPage:true});
    });
    await check("DV7_SAFETY_PERSISTENT_BOTH_VIEWS",async()=>{
      await choose("F");await page.setViewportSize({width:390,height:500});
      for(const name of ["patient","clinician","patient"]){await role(name);assert.equal(await page.locator("#safety-panel").isVisible(),true);assert.equal(await page.locator("#safety-resources").isVisible(),true);}
      await navigate("patterns");assert.equal(await page.locator("#safety-panel").isVisible(),true);
      await page.locator("#safety-panel").focus();await page.keyboard.press("End");
      await page.waitForFunction(()=>document.getElementById("safety-panel").scrollTop>0);
      await page.screenshot({path:path.join(out,"safety-short-phone.png"),fullPage:true});
    });
    await check("DV8_OFFLINE_IN_CLINICIAN_VIEW",async()=>{
      await choose("stable");await role("clinician");await context.setOffline(true);
      await page.waitForSelector("#safety-panel:not([hidden])");
      assert.match(await page.locator("#safety-message").innerText(),/cannot assess this input while offline/);
      await role("patient");assert.equal(await page.locator("#safety-resources").isVisible(),true);
      await context.setOffline(false);await page.waitForFunction(()=>document.getElementById("safety-panel").hidden);
    });
    await check("DV9_CASES_A_F_SHARED_EVIDENCE",async()=>{
      await page.setViewportSize({width:1280,height:900});
      for(const key of "ABCDEF"){
        await choose(key);await role("clinician");assert.equal(await page.locator("#evidence-charts .chart-card").count(),4);
        const evidence=await page.locator('.chart-observed').count();
        await role("patient");await navigate("patterns");assert.equal(await page.locator('.chart-observed').count(),evidence);
      await navigate("review");assert.match(await page.locator(".sharing-note").innerText(),/Not sent/);
      }
    });
    await check("DV10_RESPONSIVE_KEYBOARD",async()=>{
      await choose("B");
      for(const size of [{width:320,height:568},{width:390,height:844},{width:1280,height:900}]){
        await page.setViewportSize(size);
        for(const name of ["clinician","patient"]){await role(name);if(name==="patient")await navigate("patterns");assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);}
      }
      await role("patient");await page.locator("#talk").click();assert.equal(await page.evaluate(()=>document.getElementById("input-dialog").contains(document.activeElement)),true);
      await page.keyboard.press("Escape");assert.equal(await page.locator("#input-dialog").isHidden(),true);
      await role("clinician");await page.screenshot({path:path.join(out,"clinician-b-final-laptop.png"),fullPage:true});
    });
    await check("DV11_EXPLANATION_USES_PRODUCTION_HOLD",async()=>{
      await choose("D-before");await role("patient");await navigate("patterns");await page.locator('#workspace-context > summary').click();
      const before=await(await context.request.get(base+`/patients/${id("D-before")}/status`)).json();
      await page.locator("#explain").click();assert.equal(await page.locator("#input-text").inputValue(),"new stable work schedule");
      const saved=page.waitForResponse(response=>response.request().method()==="POST"&&new URL(response.url()).pathname.endsWith("/context-explanations"));
      await page.locator("#send-input").click();assert.equal((await saved).status(),200);
      await page.waitForFunction(()=>document.getElementById("notice").textContent==="Recorded. Nothing has been sent to a clinician.");
      const after=await(await context.request.get(base+`/patients/${id("D-before")}/status`)).json();
      assert.equal(after.held_for_review.length,2);
      assert.deepEqual(before.signals.map(row=>row.anchor),after.signals.map(row=>row.anchor));
      await role("clinician");assert.equal(await page.locator(".held-item").count(),2);
    });
    await check("DV12_HOSTED_CONTEXT_SUBMISSION_HONESTY",async()=>{
      await choose("C");await role("patient");
      if(catalog.hosted)assert.equal(await page.locator("#clarify").isHidden(),false);
      await navigate("patterns");assert.ok((await page.locator("#context-list").textContent()).length>0);
      if(catalog.hosted)assert.equal(await page.locator("#explain").isDisabled(),false);
    });
    assert.deepEqual(errors,[]);await fs.writeFile(path.join(out,"dual-view-results.json"),JSON.stringify({results,errors},null,2));
  }finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
