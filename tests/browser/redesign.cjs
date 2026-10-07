/* Patient-first layout gate; observable fixtures only, no domain decisions. */
"use strict";
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL||'http://127.0.0.1:8017';
if(!['localhost','127.0.0.1'].includes(new URL(base).hostname))throw Error('Local demo only');
async function main(){
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
  const out='/tmp/aura-redesign-browser-artifacts';await fs.mkdir(out,{recursive:true});
  async function check(name,work){await work();console.log(name+' PASS');}
  try{
    await page.goto(base);await page.waitForSelector('#patterns-view:not([hidden])');await page.locator('#patient-role').click();
    const catalog=await(await context.request.get(base+'/demo/scenarios')).json();
    const id=key=>catalog.scenarios.find(row=>row.id===key).patient_id;
    async function choose(key){
      if(await page.locator('#demo-panel').isHidden())await page.locator('#demo-toggle').click();
      await page.locator('#scenario').selectOption(id(key));
      await page.waitForFunction(()=>document.getElementById('notice').hidden&&!document.getElementById('home-view').hidden);
      await page.locator('#demo-toggle').click();await page.evaluate(()=>scrollTo(0,0));
    }
    async function navigate(name){await page.evaluate(value=>location.hash=value,name);await page.waitForSelector('#'+name+'-view:not([hidden])');}
    await check('UX1_FIRST_SCREEN',async()=>{
      await choose('stable');
      assert.equal(await page.locator('.bottom-nav').isVisible(),false);assert.equal(await page.locator('#records-panel').getAttribute('open'),null);
      assert.equal(await page.locator('#quiet-card').isVisible(),true);
      for(const selector of ['#quiet-card','#talk','.patient-links']){
        const box=await page.locator(selector).boundingBox();assert.ok(box.y>=0&&box.y+box.height<=844,selector);
      }
      assert.equal(await page.locator('#routine-details').getAttribute('open'),null);
      assert.equal(await page.locator('#communication-card').isHidden(),true);
      await page.screenshot({path:out+'/today-mobile.png',fullPage:true});
    });
    await check('UX2_PERSISTENT_HELP',async()=>{
      for(const panel of ['patterns','review','about','home']){
        await navigate(panel);
        const box=await page.locator('#talk').boundingBox();assert.ok(box.y+box.height<844);
        await page.locator('#talk').click();assert.equal(await page.locator('#input-text').getAttribute('readonly'),'');
        assert.equal(await page.locator('#send-input').isDisabled(),true);
        await page.locator('[data-fixture="fixture ordinary message"]').click();assert.equal(await page.locator('#send-input').isEnabled(),true);
        await page.keyboard.press('Escape');assert.equal(await page.locator('#input-dialog').isHidden(),true);
      }
    });
    await check('UX3_PROGRESSIVE_PATTERNS',async()=>{
      await choose('B');await navigate('patterns');
      assert.equal(await page.locator('.signal-card[open]').count(),0);await page.locator('#recorded-details>summary').click();
      await page.locator('.signal-card summary').first().click();
      await page.locator('.signal-card').first().getByRole('button',{name:'Reference, coverage & context'}).click();
      assert.equal(await page.locator('#why-content .technical-details[open]').count(),0);
      await page.locator('#why-content .technical-details summary').first().click();
      assert.match(await page.locator('#why-content').innerText(),/Version 1/);
      await page.keyboard.press('Escape');await page.screenshot({path:out+'/patterns-mobile.png',fullPage:true});
    });
    await check('UX4_HELD_AND_REVIEW',async()=>{
      await choose('D');await navigate('patterns');
      assert.equal(await page.locator('.held-item').count(),2);assert.match(await page.locator('#held-list').innerText(),/Repeat prompts/);
      await navigate('review');assert.ok(await page.locator('.review-group:not([open])').count()>0);
      assert.match(await page.locator('.sharing-note').innerText(),/not saved as approval/);
      await page.locator('#review-details>summary').click();assert.match(await page.locator('#review-list').innerText(),/Explanation:/);
      await page.screenshot({path:out+'/review-mobile.png',fullPage:true});
    });
    await check('UX5_GAP_AND_RETURN',async()=>{
      await choose('E-gap');assert.match(await page.locator('#home-subtitle').innerText(),/unavailable/);
      await choose('E');assert.match(await page.locator('#home-subtitle').innerText(),/re-established/);
    });
    await check('UX6_SAFETY_SHORT_SCREEN',async()=>{
      await choose('F');await page.setViewportSize({width:390,height:500});
      for(const panel of ['home','patterns','review','about']){
        await navigate(panel);
        assert.equal(await page.locator('#safety-panel').isVisible(),true);
        const box=await page.locator('#safety-panel').boundingBox();assert.ok(box.height<=210);
        await page.locator('#safety-panel').focus();await page.keyboard.press('End');
        await page.waitForFunction(()=>document.getElementById('safety-panel').scrollTop>0);
        assert.equal(await page.locator('#safety-resources').count(),1);
        assert.equal(await page.locator('#safety-panel').evaluate(node=>node.scrollTop>0),true);
        const resources=await page.locator('#safety-resources').boundingBox();
        assert.ok(resources.y>=box.y-1&&resources.y<box.y+box.height,'Resources reachable by keyboard scrolling');
      }
      await page.screenshot({path:out+'/safety-short-mobile.png',fullPage:true});
    });
    await check('UX7_LAYOUT_AND_DIALOG',async()=>{
      await page.setViewportSize({width:390,height:844});await choose('stable');
      for(const size of [{width:320,height:568},{width:390,height:844},{width:1280,height:900}]){
        await page.setViewportSize(size);
        for(const panel of ['home','patterns','review','about']){
          await navigate(panel);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
        }
        await page.locator('#talk').click();const box=await page.locator('#input-dialog').boundingBox();assert.ok(box.y>=0&&box.y+box.height<=size.height);
        await page.locator('#close-dialog').click();
      }
      await navigate('home');await page.screenshot({path:out+'/today-laptop.png',fullPage:true});
    });
    await check('UX8_COMPACT_COMPOSER',async()=>{
      await page.setViewportSize({width:390,height:360});await page.locator('#talk').click();
      await page.locator('[data-fixture="fixture ordinary message"]').click();
      await page.locator('#send-input').scrollIntoViewIfNeeded();
      const button=await page.locator('#send-input').boundingBox();assert.ok(button.y>=0&&button.y+button.height<=360);
      await page.locator('#close-dialog').click();assert.equal(await page.locator('#input-dialog').isHidden(),true);
    });
    assert.deepEqual(errors,[]);await fs.writeFile(out+'/results.json',JSON.stringify({checks:8,result:'PASS',errors},null,2));
  }finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
