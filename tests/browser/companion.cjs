/* Patient companion cards — PATIENT_COMPANION_SPEC.md §4.
   Verifies the four cards appear, are hidden during safety, and
   missed-dose items appear on the review page. Uses the mock fallback
   (endpoint may not exist yet). Phone (390px) and laptop (1280px). */
'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL;
if(!['127.0.0.1','localhost'].includes(new URL(base).hostname))throw Error('Local synthetic fixture only');

(async()=>{
  const browser=await chromium.launch({headless:true});
  const errors=[];
  const context=await browser.newContext({viewport:{width:390,height:844}});
  await context.addInitScript(()=>{window.auraWelcomeInAutomation=true;window.auraLandingInAutomation=true;});
  const page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));

  try{
    await page.goto(base);
    await page.waitForFunction(()=>window.auraAgentContext().record&&document.getElementById('notice').hidden);
    // Switch to patient view
    await page.getByRole('button',{name:'Patient',exact:true}).click();
    await page.waitForSelector('#companion-cards:not([hidden])');

    // 1. All four cards visible on phone (390px)
    assert.equal(await page.locator('#dose-card:not([hidden])').isVisible(),true,'dose card visible');
    assert.equal(await page.locator('#medication-card:not([hidden])').isVisible(),true,'medication card visible');
    assert.equal(await page.locator('#coming-up-card:not([hidden])').isVisible(),true,'coming-up card visible');
    assert.equal(await page.locator('#suggestion-card:not([hidden])').isVisible(),true,'suggestion card visible');
    console.log('COMPANION1_FOUR_CARDS_PHONE_390 PASS');

    // 2. Dose card content
    assert.match(await page.locator('#dose-detail').innerText(),/Sertraline/i);
    const doseBtns=await page.locator('.dose-btn').all();
    assert.equal(doseBtns.length,3,'three dose buttons');
    assert.match(await doseBtns[0].innerText(),/Taken/i);
    assert.match(await doseBtns[1].innerText(),/Not yet/i);
    assert.match(await doseBtns[2].innerText(),/Skipped/i);

    // 3. Click Skipped → reason chips appear
    await doseBtns[2].click();
    assert.equal(await page.locator('#dose-reason:not([hidden])').isVisible(),true,'reason chips shown');
    const reasonChips=await page.locator('.reason-chip').all();
    assert.equal(reasonChips.length,5,'five reason chips');
    assert.match(await reasonChips[0].innerText(),/Forgot/i);
    assert.match(await reasonChips[1].innerText(),/Side effects/i);
    assert.match(await reasonChips[2].innerText(),/Ran out/i);
    console.log('COMPANION2_DOSE_SKIP_REASON_CHIPS PASS');

    // 4. Medication card: topic chips and answers
    const topicChips=await page.locator('.topic-chip').all();
    assert.ok(topicChips.length>=5,'at least five topic chips');
    await topicChips[0].click();
    assert.equal(await page.locator('#medication-answer:not([hidden])').isVisible(),true,'medication answer shown');
    assert.match(await page.locator('#answer-text').innerText(),/Sertraline/i);
    assert.match(await page.locator('#answer-source').innerText(),/Approved medication/i);
    console.log('COMPANION3_MEDICATION_TOPIC_ANSWER PASS');

    // 5. Coming up card has items
    const comingUpItems=await page.locator('.coming-up-list li').count();
    assert.ok(comingUpItems>=2,'at least two coming-up items');
    assert.match(await page.locator('.coming-up-list li').first().innerText(),/review|refill|appointment/i);
    console.log('COMPANION4_COMING_UP_ITEMS PASS');

    // 6. Suggestion card has options
    const suggestions=await page.locator('.suggestion-chip').count();
    assert.ok(suggestions>=2,'at least two suggestions');
    // Click a suggestion
    await page.locator('.suggestion-chip').first().click();
    assert.equal(await page.locator('.suggestion-chip').first().getAttribute('aria-pressed'),'true','suggestion selected');
    console.log('COMPANION5_SUGGESTION_SELECTABLE PASS');

    // 7. Hidden during safety
    await page.evaluate(()=>{document.getElementById('safety-panel').hidden=false;dispatchEvent(new HashChangeEvent('hashchange'));});
    await page.waitForFunction(()=>document.getElementById('companion-cards').hidden);
    console.log('COMPANION6_HIDDEN_DURING_SAFETY PASS');
    await page.evaluate(()=>{document.getElementById('safety-panel').hidden=true;dispatchEvent(new HashChangeEvent('hashchange'));});

    // 8. Switch to laptop (1280px)
    await page.setViewportSize({width:1280,height:900});
    await page.waitForSelector('#companion-cards:not([hidden])');
    assert.equal(await page.locator('#dose-card:not([hidden])').isVisible(),true,'dose card visible laptop');
    assert.equal(await page.locator('#suggestion-card:not([hidden])').isVisible(),true,'suggestion card visible laptop');
    console.log('COMPANION7_LAPTOP_1280 PASS');

    // 9. Missed-dose items on review page
    await page.evaluate(()=>{location.hash='review';});
    await page.waitForSelector('#review-view:not([hidden])');
    assert.equal(await page.locator('#missed-dose-items:not([hidden])').isVisible(),true,'missed-dose items on review');
    assert.match(await page.locator('#missed-dose-summary').innerText(),/Missed doses/i);
    assert.match(await page.locator('#missed-dose-summary').innerText(),/pharmacist/i);
    console.log('COMPANION8_MISSED_DOSE_REVIEW_PAGE PASS');

    // 10. No plain-language violations on companion cards
    const terms=await (await page.request.get(base+'/assets/plain_terms.json')).json();
    const failures=await page.evaluate(({terms})=>{
      const bad=[],walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
      let text;
      while((text=walker.nextNode())){
        const parent=text.parentElement;
        if(!parent||!parent.closest('#companion-cards,#missed-dose-items')||!parent.checkVisibility({checkVisibilityCSS:true})||!text.textContent.trim())continue;
        if(parent.closest('details:not([open])')&&!parent.closest('summary'))continue;
        const value=text.textContent;
        const patterns=(terms.patient||[]).map(({term})=>[term,new RegExp('\\b'+term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b','i')]);
        patterns.push(['internal code',/\b[A-Z][A-Z0-9]+_[A-Z0-9_]+\b/],['ISO date',/\b\d{4}-\d{2}-\d{2}\b/]);
        for(const [term,pattern] of patterns)if(pattern.test(value))bad.push(`${term}: ${parent.tagName.toLowerCase()}#${parent.id}.${parent.className}: ${value}`);
      }
      return bad;
    },{terms});
    assert.deepEqual(failures,[],'no plain-language violations on companion cards');
    console.log('COMPANION9_PLAIN_LANGUAGE_PASS');

    assert.deepEqual(errors,[],'no page errors');

  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
