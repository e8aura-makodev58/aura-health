/* Isolated deterministic rendering checks: no live model, policy or API mutation. */
"use strict";
const assert=require('node:assert/strict');
const path=require('node:path');
const {chromium}=require('playwright');
(async()=>{
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  try{
    await page.setContent(`<div class="workspace-heading"><select id="chart-range"><option value="56">Recent</option><option value="all">All</option></select></div><p id="workspace-patient"></p><div id="changes-overview"></div><p id="workspace-decision"></p><div id="evidence-charts"></div><div id="workspace-evidence"></div><div id="evidence-strip"></div><div id="safety-evidence"></div><section id="workspace-safety"></section><div id="evidence-review"></div><section id="workspace-review"></section><section id="month-recap">Patient text</section><div id="recap-charts"></div><p id="story-finding-1" tabindex="-1">Sourced change</p>`);
    await page.addStyleTag({path:path.resolve('aura_ui/evidence.css')});
    await page.addScriptTag({path:path.resolve('aura_ui/evidence.js')});
    await page.evaluate(()=>{
      const channel=(name,source,event)=>({key:{signal:name,source,metric:''},label:name,unit:'units',registry:{enabled_in_engine:true},current:null,
        observations:[{day:'2026-01-01',value:10,coverage:1,data_quality:1,event_id:event,deferred:false},{day:'2026-03-01',value:15,coverage:1,data_quality:1,event_id:event+'b',deferred:false}],history:[],
        findings:[{first_seen:'2026-02-01',last_seen:'2026-03-01',event_id:event,drift:{key:{signal:name,source,metric:''},description:'Recorded change',attenuated:false}}],contexts:[]});
      const signals=[channel('RESTING_HEART_RATE','watch-one','hr-1'),channel('RESTING_HEART_RATE','watch-two','hr-2'),channel('ACTIVITY','watch-one','act-1'),channel('SLEEP_MIDPOINT','watch-one','sleep-1')];
      signals[0].contexts=[{event_id:'illness',start:'2026-02-10',end:'2026-02-12',category:'BENIGN_CONTEXT',affected_signals:['RESTING_HEART_RATE'],explanation:'Reported illness'}];
      window.fixture={patient:{display_name:'Synthetic',age:40,timezone:'UTC'},period:{start:'2026-01-01',end:'2026-03-01'},signals,held:[],checkins:[{at:'2026-02-15',state:'Good',event_id:'checkin',deferred:false}],medication:[],safety:{references:[],state:null},questions:[],review_items:[],current_decision:'STAY_QUIET'};
      window.renderAuraEvidence(window.fixture);
      window.linkAuraStoryFindings([{number:1,fact_id:'fact-1',signal:'RESTING_HEART_RATE',since:'2026-02-01'}],[{fact_id:'fact-1',source_ref:'hr-1'}]);
    });
    assert.equal(await page.locator('.story-finding-band').count(),1);
    assert.equal(await page.locator('[data-source="watch-one"][data-signal="RESTING_HEART_RATE"] .story-finding-band').count(),1);
    assert.equal(await page.locator('[data-source="watch-two"] .story-finding-band').count(),0);
    assert.equal(await page.locator('.story-finding-band').getAttribute('data-since'),'2026-02-01');
    assert.equal(await page.locator('.story-finding-band').getAttribute('data-until'),'2026-03-01');
    await page.locator('#story-finding-1 .story-chart-link').click();
    assert.equal(await page.evaluate(()=>document.activeElement.dataset.signal),'RESTING_HEART_RATE');
    console.log('I2_EXACT_SOURCE_DATED_SPAN_BACKLINK PASS');
    assert.equal(await page.locator('[data-signal="ACTIVITY"] [data-context-linked="true"]').count(),0);
    assert.equal(await page.locator('[data-signal="ACTIVITY"] .context-timing-marker').count(),1);
    assert.equal(await page.locator('.aligned-checkins').count(),4);
    assert.equal(await page.locator('.aligned-checkins circle').count(),4);
    assert.equal(await page.locator('.chart-sources details').count(),0);
    assert.equal(await page.locator('#recap-charts svg').count(),0);
    assert.equal(await page.locator('#month-recap').isVisible(),true);
    console.log('I2_SIGNAL_SCOPED_CONTEXT_SHARED_CHECKIN_AXIS PASS');
    assert.equal(await page.locator('#record-comparison').isHidden(),true);
    await page.locator('#record-comparison-toggle').click();
    assert.equal(await page.locator('#record-comparison').getAttribute('data-start'),'2026-01-05');
    assert.equal(await page.locator('#record-comparison tbody tr').count(),4);
    await page.locator('#chart-range').selectOption('all');
    await page.evaluate(()=>window.renderAuraEvidence(window.fixture));
    assert.equal(await page.locator('#record-comparison tbody tr').count(),8);
    assert.equal(await page.locator('#record-comparison').getAttribute('data-start'),'2026-01-01');
    await page.evaluate(()=>window.setAuraComparisonAssessment({draft:{claims:[{text:'Checked recent observation',fact_ids:['recent']},{text:'Outside selected dates',fact_ids:['old']}]},sources:[{fact_id:'recent',at:'2026-02-15',source_ref:'recent-event'},{fact_id:'old',at:'2025-12-01',source_ref:'old-event'}]}));
    assert.match(await page.locator('.comparison-assessment').innerText(),/Checked recent observation/);
    assert.doesNotMatch(await page.locator('.comparison-assessment').innerText(),/Outside selected dates/);
    await page.locator('#record-comparison-toggle').click();
    await page.evaluate(()=>window.clearAuraStory());
    await page.locator('#record-comparison-toggle').click();
    assert.equal(await page.locator('.comparison-assessment').count(),0);
    assert.equal(await page.locator('.story-finding-band').count(),0);
    console.log('I8_OPT_IN_RAW_COMPARISON_EXACT_WINDOW PASS');
    await page.evaluate(()=>window.linkAuraStoryFindings([{number:1,signal:'RESTING_HEART_RATE',since:'2026-02-01'}]));
    assert.equal(await page.locator('.story-finding-band').count(),0);
    assert.deepEqual(errors,[]);
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
