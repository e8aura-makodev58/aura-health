"use strict";
const assert = require("node:assert/strict");
const {chromium} = require("playwright");
const fs = require("node:fs/promises");
const base = process.env.AURA_BROWSER_URL;
const out = process.env.AURA_BROWSER_ARTIFACTS;
if(!["localhost", "127.0.0.1"].includes(new URL(base).hostname)) throw Error("Local synthetic tests only");
(async () => {
  await fs.mkdir(out,{recursive:true});
  const browser = await chromium.launch({headless:true});
  const context = await browser.newContext({viewport:{width:390,height:844}});
  await context.addInitScript(()=>Object.defineProperty(Crypto.prototype,"randomUUID",{value:undefined,configurable:true}));
  const page = await context.newPage(), errors=[];
  page.on("pageerror",error=>errors.push(error.message));
  try {
    await page.goto(base);
    await page.waitForSelector("#patterns-view:not([hidden])").catch(async error=>{console.error(errors,await page.locator('#notice').textContent());throw error;});
    await page.waitForFunction(()=>document.getElementById("notice").hidden);
    await page.waitForSelector("#agent-clinician_brief .agent-disclosure");
    assert.match(await page.locator("#agent-clinician_brief .agent-disclosure").innerText(),/Summary from the record/);
    assert.ok(await page.locator("#agent-clinician_brief .agent-claim").count()>0);
    await page.waitForFunction(()=>document.querySelector('#agent-clinician_brief .finding-detail'));
    const firstFinding=page.locator('#agent-clinician_brief .finding-card').first();
    await firstFinding.locator('.finding-why').click();
    await firstFinding.locator('.finding-detail:not([hidden])').waitFor();
    assert.match(await firstFinding.locator('.finding-detail').innerText(),/Source:/);
    console.log("AG_UI1_BRIEF_SOURCES_TRACE PASS");
    await page.locator('.suggested-questions button').first().click();
    await page.waitForSelector("#agent-record_qa .agent-disclosure");
    console.log("AG_UI2_SELECTED_RECORD_QUESTION PASS");
    await page.locator("#patient-role").click();
    await page.waitForSelector('#month-recap:not([hidden])');
    assert.equal(await page.locator("#recap-charts .chart-card").count(),0);
    await page.waitForSelector("#agent-patient_insight .patient-recap");
    assert.equal(await page.locator("#agent-patient_insight .agent-disclosure").isVisible(),false);
    assert.ok(await page.locator("#agent-patient_insight .agent-claim").count()<=3);
    console.log("AG_UI3_DEFAULT_PLAIN_MOBILE_RECAP PASS");
    await page.getByRole("link",{name:"Prepare for my appointment"}).click();
    await page.locator('[data-agent-role="visit_prep"]').click();
    await page.waitForSelector("#agent-visit_prep .agent-disclosure");
    const count = await page.locator("#agent-visit_prep .agent-claim").count();
    await page.getByRole("button",{name:"Remove from this preview"}).first().click();
    assert.equal(await page.locator("#agent-visit_prep .agent-claim").count(),count-1);
    assert.match(await page.locator("#review-view").innerText(),/Nothing is.*sent|not sent/i);
    console.log("AG_UI4_REMOVABLE_NOT_SENT_PREVIEW PASS");
    for(const width of [320,390,1280]) {
      await page.setViewportSize({width,height:844});
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
    }
    console.log("AG_UI5_PHONE_LAPTOP_LAYOUT PASS");
    await page.screenshot({path:`${out}/agent-review.png`,fullPage:true});
    assert.deepEqual(errors,[]);
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
