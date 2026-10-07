/* UI1–UI15 real-browser gate. Run against a fresh, local synthetic demo database. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const { chromium } = require("playwright");
const base = process.env.AURA_BROWSER_URL || "http://127.0.0.1:8016";
const artifacts = process.env.AURA_BROWSER_ARTIFACTS || "/tmp/aura-m6-browser-artifacts";
if (!["127.0.0.1", "localhost", "[::1]"].includes(new URL(base).hostname)) throw new Error("Browser tests require a local synthetic-only demo server.");

async function main() {
  await fs.mkdir(artifacts, {recursive:true});
  const browser = await chromium.launch({headless:true});
  const context = await browser.newContext({viewport:{width:390,height:844}, reducedMotion:"reduce"});
  const page = await context.newPage(), errors = [], results = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("dialog", dialog => dialog.dismiss());
  const http = context.request;
  const catalog = await (await http.get(`${base}/demo/scenarios`)).json();
  assert.equal(catalog.synthetic_only, true);
  const id = key => catalog.scenarios.find(item => item.id === key).patient_id;
  const state = async key => (await (await http.get(`${base}/patients/${id(key)}/status`)).json());
  const snapshot = async key => (await (await http.get(`${base}/patients/${id(key)}/review-snapshot`)).json());
  async function choose(key) {
    await page.locator("#demo-toggle").click();
    if (await page.locator("#demo-panel").isHidden()) await page.locator("#demo-toggle").click();
    await page.locator("#scenario").selectOption(id(key));
    await page.waitForFunction(patient => document.getElementById("patient-label").textContent && document.getElementById("scenario").value === patient && !document.getElementById("home-view").hidden && document.getElementById("notice").hidden, id(key));
    await page.locator("#demo-toggle").click();
  }
  async function test(name, work) {
    try { await work(); results.push({test:name,result:"PASS"}); console.log(`${name} PASS`); }
    catch (error) { results.push({test:name,result:"FAIL",error:error.message}); console.error(`${name} FAIL: ${error.message}`); await page.screenshot({path:path.join(artifacts,`${name}-failure.png`),fullPage:true}); }
  }
  async function submitAndWait(button) {
    const saved = page.waitForResponse(response => response.request().method() === "POST" && /\/(events|context-explanations)$/.test(new URL(response.url()).pathname));
    await button.click(); const response = await saved; assert.equal(response.status(), 200); const result = await response.json();
    await page.waitForFunction(() => document.getElementById("notice").textContent === "Recorded. Nothing has been sent to a clinician." && !document.querySelector("[data-checkin]").disabled);
    return result;
  }

  try {
    await page.goto(base); await page.waitForSelector("#home-view:not([hidden])");
    await test("UI1", async () => { assert.equal((await state("stable")).latest_communication_decision,"STAY_QUIET"); assert.equal(await page.locator("#communication-card").isHidden(),true); assert.equal(await page.locator("#safety-panel").isHidden(),true); await page.screenshot({path:path.join(artifacts,"home-mobile.png"),fullPage:true}); });
    await test("UI2", async () => { const result = await submitAndWait(page.locator('[data-checkin="Good"]')); assert.equal(result.longitudinal.deferred,false); assert.match(await page.locator("#checkin-saved").innerText(),/Good/); });
    await test("UI8", async () => { await page.locator('#routine-details summary').click(); const result = await submitAndWait(page.locator('[data-medication="acknowledged"]')); assert.equal(result.longitudinal.deferred,false); assert.match(await page.locator("#routine-saved").innerText(),/acknowledged/i); assert.equal(await page.locator('input[name="dose"], input[name="taper"]').count(),0); });
    await test("UI12", async () => { await page.locator("#talk").click(); await page.locator('[data-fixture="fixture ordinary message"]').click(); const result = await submitAndWait(page.locator("#send-input")); assert.equal(result.conversation_status,"NORMAL_CONVERSATION_ALLOWED"); assert.match(await page.locator("#communication-message").innerText(),/What would you like/); });
    await test("UI4", async () => { await choose("D-before"); const before=(await state("D-before")).signals.map(s=>s.anchor); await page.locator('[data-page="patterns"]').click(); await page.locator("#explain").click(); assert.equal(await page.locator("#input-text").inputValue(),"new stable work schedule"); await submitAndWait(page.locator("#send-input")); const after=await state("D-before"); assert.equal(after.held_for_review.length,2); assert.deepEqual(before,after.signals.map(s=>s.anchor)); });
    await test("UI5", async () => { await choose("D"); await page.locator('[data-page="patterns"]').click(); assert.equal(await page.locator(".held-item").count(),2); assert.match(await page.locator("#held-list").innerText(),/reference is unchanged/); assert.match(await page.locator("#held-list").innerText(),/held for review/); });
    await test("UI6", async () => { await choose("E-gap"); assert.match(await page.locator("#data-heading").innerText(),/unavailable/); assert.match(await page.locator("#data-summary").innerText(),/Missing data is just missing data/); assert.ok((await state("E-gap")).signals.every(s=>s.rolling.mean===null && s.rolling.sample_count===0)); });
    await test("UI7", async () => { await choose("E"); await page.locator('[data-page="patterns"]').click(); await page.locator('.signal-card summary').first().click(); assert.match(await page.locator("#signal-list").innerText(),/No automatic exit rule/); assert.ok((await state("E")).signals.every(s=>s.trust_state==="REESTABLISHING")); });
    await test("UI9", async () => { await choose("F"); assert.equal(await page.locator("#safety-panel").isVisible(),true); await submitAndWait(page.locator('[data-checkin="Good"]')); await page.locator('[data-page="review"]').click(); assert.equal(await page.locator("#safety-panel").isVisible(),true); assert.equal((await state("F")).latest_communication_decision,"SAFETY_REVIEW_REQUIRED"); assert.equal(await page.locator("#safety-panel button:visible").count(),0); await page.screenshot({path:path.join(artifacts,"safety-mobile.png"),fullPage:true}); });
    await test("UI10", async () => { await choose("D"); await page.locator('[data-page="review"]').click(); await page.locator('.review-group summary').first().click(); await page.locator("#review-list input").first().check(); assert.match(await page.locator("#selection-summary").innerText(),/1 item selected/); assert.equal((await snapshot("D")).automatically_sent,false); assert.equal((await snapshot("D")).share_status,"NOT_SHARED"); });
    await test("UI11", async () => { await choose("C"); await page.locator("#why-home").click(); for(const detail of await page.locator('#why-content details summary').all())await detail.click(); assert.match(await page.locator("#why-content").innerText(),/Version 1/); assert.match(await page.locator("#why-content").innerText(),/synthetic_wearable/); const status=await state("C"); assert.ok((await page.locator("#why-content").innerText()).includes(status.active_longitudinal_observations[0].description)); await page.locator("#close-why").click(); });
    await test("UI14", async () => { for (const key of "ABCDEF") { await choose(key); assert.equal(await page.locator("#home-view").isVisible(),true); await page.locator('[data-page="patterns"]').click(); assert.equal(await page.locator(".signal-card").count(),4); await page.locator('[data-page="review"]').click(); assert.ok(await page.locator("#review-list .review-group").count()>=8); } });
    await test("UI13", async () => { for (const key of "ABCDEF") { await choose(key); const visible=await page.locator("body").innerText(); assert.doesNotMatch(visible,/relapse (?:probability|likelihood)|psychiatric risk\s*\d|T[1-4]\b|depression score/i); } });
    await test("UI15", async () => {
      await choose("stable");
      for (const width of [320,390,1280]) {
        await page.setViewportSize({width,height:900});
        for (const panel of ["home","patterns","review","about"]) {
          await page.locator(`[data-page="${panel}"]`).click();
          const overflow = await page.evaluate(()=>({width:innerWidth, scroll:document.documentElement.scrollWidth,
            elements:[...document.querySelectorAll("body *")].filter(el=>el.getBoundingClientRect().right>innerWidth+1).map(el=>({tag:el.tagName,id:el.id,class:el.className,right:el.getBoundingClientRect().right}))}));
          assert.ok(overflow.scroll<=overflow.width,`${width}/${panel} overflow ${JSON.stringify(overflow)}`);
        }
      }
      await page.setViewportSize({width:390,height:844}); await page.locator('[data-page="home"]').click();
      await page.locator("#talk").click(); assert.equal(await page.locator("#input-dialog").isVisible(),true);
      assert.equal(await page.evaluate(()=>document.getElementById("input-dialog").contains(document.activeElement)),true);
      await page.keyboard.press("Escape"); assert.equal(await page.locator("#input-dialog").isHidden(),true);
      await page.setViewportSize({width:1280,height:900}); await page.screenshot({path:path.join(artifacts,"home-desktop.png"),fullPage:true});
    });
    await test("UI3", async () => {
      const patient=`browser-unscripted-${Date.now()}`;
      assert.equal((await http.post(`${base}/patients`,{data:{patient_id:patient,display_name:"Synthetic note test",age:35}})).status(),200);
      await page.locator("#demo-toggle").click(); await page.locator("#patient-id").fill(patient); await page.locator("#connect").click();
      await page.waitForFunction(()=>document.getElementById("patient-label").textContent.includes("Synthetic note test")); await page.locator("#demo-toggle").click();
      await page.locator("#add-note").click(); await page.locator("#input-text").fill("<script>window.injection=true</script> arbitrary note");
      const result=await submitAndWait(page.locator("#send-input")); assert.equal(result.longitudinal.deferred,true); assert.equal(result.safety.state.degraded,true); assert.equal(await page.locator("#safety-resources").isVisible(),true); assert.equal(await page.evaluate(()=>window.injection),undefined);
    });
    await test("OFFLINE", async () => {
      await choose("stable"); await page.locator("#talk").click(); await page.locator('[data-fixture="fixture ordinary message"]').click();
      await context.setOffline(true); await page.locator("#send-input").click(); await page.waitForFunction(()=>document.getElementById("notice").textContent.includes("memory only"));
      assert.equal(await page.locator("#safety-resources").isVisible(),true); assert.match(await page.locator("#safety-message").innerText(),/cannot assess this input while offline/);
      await context.setOffline(false); await page.waitForFunction(()=>document.getElementById("notice").textContent === "Recorded. Nothing has been sent to a clinician.");
      assert.equal(await page.locator("#safety-panel").isHidden(),true);
    });
    await test("MANUAL_RETRY", async () => {
      const pattern=`**/patients/${id("stable")}/events`;
      let failedBody;
      await page.route(pattern, async route=>{failedBody=route.request().postDataJSON();await route.abort("failed");});
      await page.locator("#talk").click(); await page.locator('[data-fixture="fixture ordinary message"]').click();
      await page.locator("#send-input").click();
      await page.waitForFunction(()=>document.getElementById("notice").textContent.includes("memory only"));
      assert.equal(await page.locator("#input-dialog").isHidden(),true);
      assert.equal(await page.locator("#retry-connection").isVisible(),true);
      await page.unroute(pattern);
      const retry=page.waitForRequest(request=>request.method()==="POST" && new URL(request.url()).pathname.endsWith("/events"));
      await page.locator("#retry-connection").click();
      assert.equal((await retry).postDataJSON().idempotency_key,failedBody.idempotency_key);
      await page.waitForFunction(()=>document.getElementById("notice").textContent === "Recorded. Nothing has been sent to a clinician.");
      const timeline=await (await http.get(`${base}/patients/${id("stable")}/timeline`)).json();
      assert.equal(timeline.filter(row=>row.event_id===failedBody.event_id && row.record_type==="PATIENT_FREE_TEXT").length,1);
    });
    assert.deepEqual(errors,[],"Browser console errors");
    await fs.writeFile(path.join(artifacts,"results.json"),JSON.stringify({viewport:"390x844; 320 and 1280 responsive checks",results,errors},null,2)+"\n");
    if (results.some(result=>result.result!=="PASS")) process.exitCode=1;
    console.log(`Artifacts: ${artifacts}`);
  } finally { await browser.close(); }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
