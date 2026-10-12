/* Development-only scalar ingestion; hosted intake remains deliberately gated. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs/promises"), path = require("node:path");
const {randomUUID} = require("node:crypto");
const {chromium} = require("playwright");
const base = process.env.AURA_BROWSER_URL || "http://127.0.0.1:8016";
const out = process.env.AURA_BROWSER_ARTIFACTS || "/tmp/aura-registry-browser";
if (!["127.0.0.1", "localhost"].includes(new URL(base).hostname)) throw Error("Local synthetic server required");
async function main() {
  await fs.mkdir(out, {recursive:true});
  const browser = await chromium.launch({headless:true});
  try {
    const context = await browser.newContext({viewport:{width:390,height:844}});
    const registry = await (await context.request.get(base + "/signals")).json();
    const values = {HRV:42, RESPIRATORY_RATE:16, SKIN_TEMPERATURE_DEVIATION:0.4,
      SPO2:97, BLOOD_PRESSURE_SYSTOLIC:120, BLOOD_PRESSURE_DIASTOLIC:80,
      BODY_TEMPERATURE:38.5, WEIGHT:70};
    const observations = registry.signals.filter(row => row.name in values).map(row => ({
      kind:"scalar", signal:row.name, date:"2026-03-17", value:values[row.name],
      coverage:1, data_quality:1, source:"synthetic_sensor", unit:row.unit}));
    const response = await context.request.post(base + "/patients/demo-B-7/events", {data:{
      event_id:randomUUID(), event_type:"WEARABLE_OBSERVATION", occurred_at:"2026-03-17T12:00:00+00:00",
      source:"SIMULATOR", payload:{observations}, correlation_id:randomUUID(), idempotency_key:randomUUID()}});
    assert.equal(response.status(), 200, "Use this suite without --hosted: public arbitrary intake stays forbidden");
    const result = await response.json();
    assert.equal(result.longitudinal.baselines.length, 7);
    console.log("SR_UI1_TYPED_SCALAR_INGESTION PASS");
    const page = await context.newPage(), errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(base);
    await page.waitForSelector("#patterns-view:not([hidden])");
    await page.waitForFunction(() => document.getElementById("notice").hidden);
    assert.equal(await page.locator("#evidence-charts .chart-card").count(), 12);
    await page.locator('#other-measurements > summary').click();
    const chart = signal => page.locator(`#evidence-charts [data-signal="${signal}"]`);
    for (const signal of ["HRV", "RESPIRATORY_RATE", "SKIN_TEMPERATURE_DEVIATION"]) {
      assert.match(await chart(signal).innerText(), /Newer measure/);
      assert.equal(await chart(signal).locator(".chart-observed").count(), 1);
    }
    for (const signal of ["SPO2", "BLOOD_PRESSURE_SYSTOLIC", "BLOOD_PRESSURE_DIASTOLIC", "BODY_TEMPERATURE", "WEIGHT"]) {
      assert.match(await chart(signal).innerText(), /Readings only/);
      assert.equal(await chart(signal).locator(".chart-observed").count(), 1);
      assert.equal(await chart(signal).locator(".chart-rolling,.chart-anchor,.chart-rolling-point,.chart-anchor-point").count(), 0);
    }
    assert.match(await chart("BODY_TEMPERATURE").innerText(), /°C/);
    assert.match(await chart("SKIN_TEMPERATURE_DEVIATION").innerText(), /°C/);
    console.log("SR_UI2_RESEARCH_AND_DISPLAY_ONLY_VISIBLE PASS");
    for (const width of [390,1280]) {
      await page.setViewportSize({width,height:900});
      await page.waitForTimeout(250);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 2));
      await page.screenshot({path:path.join(out,`registry-${width}.png`),fullPage:true});
    }
    assert.deepEqual(errors, []);
    console.log("SR_UI3_PHONE_LAPTOP_NO_PAGE_ERRORS PASS");
  } finally { await browser.close(); }
}
main().catch(error => {console.error(error);process.exitCode=1;});
