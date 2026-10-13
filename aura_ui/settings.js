/* Operator control only. No keys/tokens are saved to browser storage. */
"use strict";
(() => {
  const node=id=>document.getElementById(id), dialog=node("settings-dialog");
  let token="", state=null, working=false, ticket=0;
  const variantNames={default:"Provider default",singapore:"TokenHub · Singapore",guangzhou:"TokenHub · Guangzhou",hunyuan:"Hunyuan · legacy endpoint"};
  function feedback(text){node("settings-feedback").textContent=text;}
  function lock(){token="";state=null;ticket++;node("settings-admin").value="";node("settings-key").value="";node("settings-editor").hidden=true;node("settings-unlock").hidden=false;}
  async function call(action,body){
    const response=await fetch(`/system/settings/${action}`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${token}`},body:JSON.stringify(body),cache:"no-store"});
    const data=await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(data.error?.message || "System settings unavailable on this entry point.");
    return data;
  }
  function options(target,rows,value){target.replaceChildren();for(const row of rows){const option=document.createElement("option");option.value=row.value;option.textContent=row.label;target.append(option);}target.value=value;}
  function select(){
    const id=node("settings-provider").value, meta=state.providers.find(row=>row.id===id), saved=state.models[id];
    options(node("settings-variant"),meta.variants.map(value=>({value,label:variantNames[value]})),saved.variant);
    node("settings-model").value=saved.model;node("settings-models").replaceChildren();node("settings-key").value="";
    node("settings-reasoning").value=saved.reasoning||"medium";
    loadModels(meta);
    node("settings-key-status").textContent=meta.credential_configured?"Key configured. Its value is never returned to the browser.":"No saved key for this provider.";
    node("settings-enabled").checked=state.enabled&&state.provider===id;
  }
  // Model list comes from the provider itself; the saved model stays selected even if unlisted.
  async function loadModels(meta){
    const list=node("settings-model-list"),current=ticket,saved=node("settings-model").value;
    const fill=(ids,label)=>{list.replaceChildren();const ask=document.createElement("option");ask.value="";ask.textContent=label;list.append(ask);
      for(const id of new Set([...(saved?[saved]:[]),...ids])){const option=document.createElement("option");option.value=id;option.textContent=id;list.append(option);}
      list.value=saved||"";node("settings-models").replaceChildren(...ids.map(id=>{const o=document.createElement("option");o.value=id;return o;}));};
    if(!meta||!meta.credential_configured){fill([],"Save an API key to list this provider's models");return;}
    fill([],"Loading the provider's models…");
    try{const result=await call("models",{provider:node("settings-provider").value,variant:node("settings-variant").value});
      if(current!==ticket)return;
      fill(result.models||[],result.status==="READY"?`Choose a model (${(result.models||[]).length} available)`:"Model list unavailable; type an exact ID");
    }catch{if(current===ticket)fill([],"Model list unavailable; type an exact ID");}
  }
  function render(next,selected){state=next;options(node("settings-provider"),state.providers.map(row=>({value:row.id,label:row.label})),selected||state.provider);select();node("settings-unlock").hidden=true;node("settings-editor").hidden=false;}
  async function work(action){
    if(working)return;working=true;const current=++ticket;
    for(const control of dialog.querySelectorAll("button:not(#close-settings),input,select"))control.disabled=true;
    feedback("Working…");
    try{await action(current);}catch(error){if(current===ticket)feedback(error.message);}
    finally{working=false;for(const control of dialog.querySelectorAll("button,input,select"))control.disabled=false;
      if(!window.isSecureContext)node("settings-unlock").querySelector("button").disabled=true;}
  }
  node("system-settings").addEventListener("click",()=>{
    lock();feedback("");dialog.showModal();
    node('settings-current-model').textContent='Loading current model…';
    fetch('/system/status',{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject()).then(s=>{
      node('settings-current-model').textContent=`${s.provider} / ${s.model}${s.reasoning?` · reasoning ${s.reasoning}`:''} · ${s.live_enabled?'Live model enabled':'Offline fallback'} · synthetic data`;
    }).catch(()=>{node('settings-current-model').textContent='Current provider unavailable on this entry point.';});
    const secure=window.isSecureContext && (location.protocol==="https:"||["localhost","127.0.0.1","[::1]"].includes(location.hostname));
    node("settings-unlock").querySelector("button").disabled=!secure;
    if(!secure)feedback("Use HTTPS or forward port 8017 over SSH and open localhost. Credentials must not be sent over unencrypted LAN HTTP.");
  });
  node("close-settings").addEventListener("click",()=>dialog.close());dialog.addEventListener("close",lock);
  node("settings-lock").addEventListener("click",()=>{lock();feedback("Locked. Browser-held credentials cleared.");});
  node("settings-provider").addEventListener("change",select);
  node("settings-variant").addEventListener("change",()=>loadModels(state?.providers.find(row=>row.id===node("settings-provider").value)));
  node("settings-model-list").addEventListener("change",()=>{if(node("settings-model-list").value)node("settings-model").value=node("settings-model-list").value;});
  node("settings-unlock").addEventListener("submit",event=>{event.preventDefault();token=node("settings-admin").value;node("settings-admin").value="";work(async current=>{const next=await call("read",{});if(current!==ticket)return;render(next);feedback("Administrator settings unlocked for this dialog only.");});});
  node("settings-save-key").addEventListener("click",()=>work(async current=>{const provider=node("settings-provider").value,key=node("settings-key").value;node("settings-key").value="";const next=await call("credential",{provider,api_key:key});if(current!==ticket)return;render(next,provider);feedback("Key saved on the server. It remains write-only.");document.dispatchEvent(new Event("aura-settings-updated"));}));
  node("settings-remove-key").addEventListener("click",()=>work(async current=>{const provider=node("settings-provider").value;if(!confirm("Remove this provider's stored key? Live wording will use fallback if this provider is active."))return;const next=await call("remove-key",{provider});if(current!==ticket)return;render(next,provider);feedback("Stored key removed.");document.dispatchEvent(new Event("aura-settings-updated"));}));
  node("settings-discover").addEventListener("click",()=>work(async()=>{await loadModels(state?.providers.find(row=>row.id===node("settings-provider").value));feedback("Model list refreshed from the provider.");}));
  node("settings-save").addEventListener("click",()=>work(async current=>{const next=await call("save",{provider:node("settings-provider").value,model:node("settings-model").value.trim(),variant:node("settings-variant").value,enabled:node("settings-enabled").checked,reasoning:node("settings-reasoning").value});if(current!==ticket)return;render(next);feedback("Provider settings saved. Safety permissions remain unchanged.");document.dispatchEvent(new Event("aura-settings-updated"));}));
  node("settings-test").addEventListener("click",()=>work(async current=>{if(!confirm("Send one small synthetic connection test to the saved model? This may incur a provider charge.")){feedback("Test cancelled.");return;}const result=await call("test",{confirm:"SYNTHETIC_TEST_MAY_COST"});if(current!==ticket)return;feedback(result.status==="PASS"?"Live synthetic connection test passed; exact output validated.":result.message||"Provider returned invalid output; application wording would use fixed fallback.");}));
})();
