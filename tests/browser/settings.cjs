/* UI contract test with mocked operator API: no real credentials/provider calls. */
"use strict";
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const base=process.env.AURA_BROWSER_URL||'http://127.0.0.1:8017';
if(!['localhost','127.0.0.1'].includes(new URL(base).hostname))throw Error('Local demo only');
async function main(){
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[],calls=[];
  page.on('pageerror',error=>errors.push(error.message));
  const providers=['openrouter','openai','deepseek','tencent'];
  const state={provider:'openrouter',enabled:false,revision:'fixture',models:Object.fromEntries(providers.map(id=>[id,{model:'',variant:id==='tencent'?'singapore':'default'}])),providers:providers.map(id=>({id,label:id,credential_configured:false,variants:id==='tencent'?['singapore','guangzhou','hunyuan']:['default']}))};
  await page.route('**/system/settings/*',async route=>{
    const action=new URL(route.request().url()).pathname.split('/').pop(),body=route.request().postDataJSON();calls.push(action);
    assert.equal(route.request().headers().authorization,'Bearer synthetic-operator-token');
    if(action==='credential')state.providers.find(row=>row.id===body.provider).credential_configured=true;
    if(action==='remove-key')state.providers.find(row=>row.id===body.provider).credential_configured=false;
    if(action==='save'){state.provider=body.provider;state.enabled=body.enabled;state.models[body.provider]={model:body.model,variant:body.variant};}
    await route.fulfill({json:action==='models'?{models:['fixture-text'],status:'READY'}:state});
  });
  try{
    await page.goto(base);await page.waitForSelector('#home-view:not([hidden])');
    await page.locator('#system-settings').click();await page.locator('#settings-admin').fill('synthetic-operator-token');
    await page.locator('#settings-unlock button').click();await page.waitForSelector('#settings-editor:not([hidden])');
    assert.equal(await page.locator('#settings-provider option').count(),4);
    await page.locator('#settings-provider').selectOption('tencent');assert.equal(await page.locator('#settings-variant option').count(),3);
    await page.locator('#settings-key').fill('synthetic-key-not-real');await page.locator('#settings-save-key').click();
    await page.waitForFunction(()=>document.getElementById('settings-feedback').textContent.startsWith('Key saved'));
    assert.equal(await page.locator('#settings-key').inputValue(),'');
    await page.locator('#settings-discover').click();await page.waitForFunction(()=>document.getElementById('settings-models').children.length===1);
    await page.locator('#settings-model').fill('fixture-text');await page.locator('#settings-save').click();
    await page.waitForFunction(()=>document.getElementById('settings-feedback').textContent.startsWith('Provider settings saved'));
    assert.equal(state.models.tencent.model,'fixture-text');assert.equal(state.enabled,false);
    for(const width of [320,390,1280]){await page.setViewportSize({width,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.equal(await page.locator('#close-settings').isVisible(),true);}
    await page.locator('#settings-lock').click();assert.equal(await page.locator('#settings-editor').isHidden(),true);assert.equal(await page.locator('#settings-admin').inputValue(),'');
    assert.deepEqual(await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length})),{local:0,session:0});
    await page.locator('#close-settings').click();assert.equal(await page.locator('#settings-dialog').isVisible(),false);
    assert.deepEqual(calls,['read','credential','models','save']);assert.deepEqual(errors,[]);
    console.log('SETTINGS_UI PASS: unlock, four providers, Tencent regions, write-only key, discovery, save, lock, 320/390/1280 widths; no paid calls');
  }finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
