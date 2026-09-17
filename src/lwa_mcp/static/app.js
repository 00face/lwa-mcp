const $ = (s) => document.querySelector(s);
const fmt = new Intl.NumberFormat();
const money = new Intl.NumberFormat(undefined,{style:'currency',currency:'USD',minimumFractionDigits:4});
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = (used, cap) => cap ? Math.min(100, Math.round((used/cap)*100)) : 0;

async function json(url, options={}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}
function badge(text, kind='') { return `<span class="badge ${kind}">${esc(text)}</span>`; }
function renderProviders(rows) {
  $('#providersTable tbody').innerHTML = rows.map(p => {
    const state = p.experimental ? badge(p.enabled ? 'experimental' : 'experimental · disabled','warn') : !p.enabled ? badge('disabled','bad') : p.configured ? badge('configured','ok') : badge('key missing','warn');
    const d=p.caps.daily, m=p.caps.monthly;
    const dailyCap=p.daily_request_cap;
    const monthlyCap=p.monthly_usd_cap;
    const daily = dailyCap ? `${fmt.format(d.requests)} / ${fmt.format(dailyCap)}<div class="meter" style="--pct:${pct(d.requests,dailyCap)}%"><i></i></div>` : `${fmt.format(d.requests)} / local cap off`;
    const monthly = monthlyCap ? `${money.format(m.cost)} / ${money.format(monthlyCap)}<div class="meter" style="--pct:${pct(m.cost,monthlyCap)}%"><i></i></div>` : `${money.format(m.cost)} / local cap off`;
    const subscription = `${badge(p.subscription_plan || 'unknown', p.subscription_status === 'active' ? 'ok' : 'warn')}<br><small>${esc(p.subscription_status || 'unknown')}${p.billing_credential_configured ? ' · billing key ready' : ''}</small>`;
    return `<tr><td><strong>${esc(p.name)}</strong>${p.disabled_reason?`<br><small>${esc(p.disabled_reason)}</small>`:''}</td><td>${state}</td><td>${badge(p.billing_class,p.billing_class==='paid'?'warn':'')}</td><td>${subscription}</td><td>${daily}</td><td>${monthly}</td><td>${esc(p.adapter)}</td></tr>`;
  }).join('');
}
function renderTiers(rows) {
  $('#tiersTable tbody').innerHTML = rows.map(m=>`<tr><td>${esc(m.rank)}</td><td><strong>${esc(m.display_name || m.model)}</strong><br><small>${esc(m.provider)} · ${esc(m.billing_class)}</small></td><td>${m.free_plan_max_tokens == null ? badge('not declared','warn') : fmt.format(m.free_plan_max_tokens)}</td><td>${m.pro_plan_max_tokens == null ? badge('not declared','warn') : fmt.format(m.pro_plan_max_tokens)}</td><td>${badge(m.subscription_plan || 'unknown', m.subscription_status === 'active' ? 'ok' : 'warn')}<br><small>${esc(m.subscription_status || 'unknown')}</small></td><td>${fmt.format(m.context_length || 0)}</td></tr>`).join('') || '<tr><td colspan="6"><small>No configured model tiers.</small></td></tr>';
}
function renderLibrary(rows) {
  $('#library').innerHTML = rows.slice(0,20).map(t=>`<article class="mini-card"><strong>${esc(t.name)} ${badge(t.status,t.status==='active'?'ok':'warn')}</strong><small><code>${esc(t.slug)}</code> · ${esc(t.task)} · ${esc(t.kind)} · v${esc(t.version)}</small><p>${esc(t.description)}</p><small>${fmt.format(t.evidence_count)} observations · confidence ${Number(t.confidence).toFixed(2)} · ${esc(t.created_by)}</small></article>`).join('') || '<article class="mini-card"><small>No tools yet. Repeated successful workflows will generate documented recipes here.</small></article>';
}
function renderPatterns(rows) {
  $('#patterns').innerHTML = rows.slice(0,20).map(p=>`<article class="mini-card"><strong>${esc(p.label)} ${p.tool_slug?badge('tool created','ok'):badge('observing','warn')}</strong><small>${esc(p.task)} · ${fmt.format(p.occurrences)} occurrences · ${fmt.format(p.successes)} successes · confidence ${Number(p.confidence).toFixed(2)}</small><p>${esc(p.description)}</p><small>${esc((p.keywords||[]).join(' · '))}${p.tool_slug?`<br>Library: <code>${esc(p.tool_slug)}</code>`:''}</small></article>`).join('') || '<article class="mini-card"><small>No repeated patterns recorded yet.</small></article>';
}
function renderCredentials(rows) {
  $('#credentialName').innerHTML = rows.map(c => `<option value="${esc(c.env_name)}">${esc(c.provider)} · ${esc(c.env_name)}</option>`).join('');
  $('#credentials').innerHTML = rows.map(c => `<article class="mini-card credential-card"><strong>${esc(c.provider)} ${badge(c.configured ? 'configured' : 'not configured', c.configured ? 'ok' : 'warn')}</strong><small><code>${esc(c.env_name)}</code> · ${esc(c.label)}${c.configured ? ` · ${esc(c.masked)}` : ''}</small></article>`).join('');
}
function renderStatus(s, library, patterns) {
  const u=s.usage;
  $('#consent').value=s.consent_mode;
  $('#todayRequests').textContent=fmt.format(u.today.requests);
  $('#todayTokens').textContent=fmt.format(u.today.input_tokens+u.today.output_tokens);
  $('#monthCost').textContent=money.format(u.month.cost);
  $('#modelCount').textContent=fmt.format(s.catalog_models);
  $('#toolCount').textContent=fmt.format(s.library.active);
  $('#patternCount').textContent=fmt.format(patterns.length);
  renderLibrary(library);
  renderPatterns(patterns);
  $('#recentTable tbody').innerHTML=u.recent.map(r=>`<tr><td>${esc(new Date(r.created_at).toLocaleString())}</td><td>${esc(r.task)}</td><td><strong>${esc(r.provider)}</strong><br><small>${esc(r.model)}</small></td><td>${badge(r.billing_class)}</td><td>${fmt.format(r.input_tokens+r.output_tokens)}</td><td>${fmt.format(r.latency_ms)} ms</td><td>${badge(r.status,r.status==='ok'?'ok':'bad')}</td></tr>`).join('') || '<tr><td colspan="7"><small>No executions recorded yet.</small></td></tr>';
  $('#quotas').innerHTML=u.quotas.map(q=>`<article class="mini-card"><strong>${esc(q.provider)}</strong><small>${esc(new Date(q.created_at).toLocaleString())}</small><pre>${esc(JSON.stringify(q.values,null,2))}</pre></article>`).join('') || '<article class="mini-card"><small>Quota and rate-limit headers appear after providers return them.</small></article>';
  $('#health').innerHTML=s.health.map(h=>`<article class="mini-card"><strong>${esc(h.provider)} ${h.healthy===true?badge('healthy','ok'):h.healthy===false?badge('probe failed','bad'):badge('not probed','warn')}</strong><small>${esc(h.detail)}</small></article>`).join('') || '<article class="mini-card"><small>Run a catalog refresh to populate provider health.</small></article>';
  $('#preflights').innerHTML=(u.preflights||[]).map(p=>{const routes=(p.routes||[]).map(r=>`${r.role}: ${r.provider}/${r.model}`).join(' · '); const locks=Object.entries(p.locks||{}).filter(([,v])=>v).map(([k])=>k.replaceAll('_',' ')).join(' · '); return `<article class="route"><div><strong>${esc(p.task)}</strong><small>${esc(new Date(p.created_at).toLocaleString())} · ${esc(p.mode)}</small></div><div><strong>${esc(p.status)}</strong><small>${p.working_may_begin?'Working authorized':'Working blocked'} · ${fmt.format(p.estimated_input_tokens)} estimated input tokens</small></div><p>${esc(routes)}<br>${esc(locks)}</p></article>`;}).join('') || '<article class="route"><small>No preflight plans recorded yet.</small></article>';
  $('#routes').innerHTML=u.routes.map(r=>`<article class="route"><div><strong>${esc(r.task)}</strong><small>${esc(new Date(r.created_at).toLocaleString())}</small></div><div><strong>${esc(r.provider)} / ${esc(r.model)}</strong><small>score ${Number(r.score).toFixed(1)} · ${r.requires_confirmation?'confirmation required':'automatic'}</small></div><p>${esc(r.reasons.join(' · '))}</p></article>`).join('') || '<article class="route"><small>No routing decisions recorded yet.</small></article>';
}
async function load() {
  try {
    const [status,providers,tiers,library,patterns,credentials]=await Promise.all([json('/api/status'),json('/api/providers'),json('/api/model-tiers'),json('/api/library'),json('/api/patterns'),json('/api/credentials')]);
    renderStatus(status,library,patterns); renderProviders(providers); renderTiers(tiers);
    renderCredentials(credentials);
    $('#notice').className='notice';
    $('#notice').textContent=`Lwa MCP online. Confirmation: ${status.consent_mode}. Tool library: ${status.library.root}`;
  } catch(e) { $('#notice').className='notice error'; $('#notice').textContent=`Dashboard error: ${e.message}`; }
}
$('#consent').addEventListener('change', async e=>{ await json('/api/consent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:e.target.value})}); await load(); });
$('#refresh').addEventListener('click', async()=>{ $('#notice').textContent='Refreshing configured provider catalogs and quotas…'; try { const [r,q]=await Promise.all([json('/api/catalog/refresh',{method:'POST'}),json('/api/quotas/refresh',{method:'POST'})]); const ok=Object.values(q).filter(x=>x.status==='ok').length; $('#notice').textContent=`Catalog refresh complete: ${r.models} models, ${r.refreshed} live entries, ${ok} remote quota probes.`; await load(); } catch(e) { $('#notice').className='notice error'; $('#notice').textContent=`Refresh failed: ${e.message}`; }});
$('#analyze').addEventListener('click', async()=>{ $('#notice').textContent='Analyzing repeated workflows and rebuilding the library catalog…'; try { const r=await json('/api/library/analyze',{method:'POST'}); await json('/api/library/catalog',{method:'POST'}); $('#notice').textContent=`Pattern analysis complete. ${r.created_tools.length} new tool(s) created.`; await load(); } catch(e) { $('#notice').className='notice error'; $('#notice').textContent=`Pattern analysis failed: ${e.message}`; }});
$('#credentialForm').addEventListener('submit', async e=>{ e.preventDefault(); const name=$('#credentialName').value; const value=$('#credentialValue').value; if(!value) { $('#notice').textContent='Enter a new value before saving.'; return; } if(!window.confirm(`Save a new value for ${name}?`)) return; try { await json(`/api/credentials/${encodeURIComponent(name)}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({value,confirm:true})}); $('#credentialValue').value=''; $('#notice').textContent=`${name} saved to Lwa's protected credential store.`; await load(); } catch(e) { $('#notice').className='notice error'; $('#notice').textContent=`Credential update failed: ${e.message}`; }});
$('#deleteCredential').addEventListener('click', async()=>{ const name=$('#credentialName').value; if(!window.confirm(`Delete the managed value for ${name}? This does not revoke the provider key.`)) return; try { await json(`/api/credentials/${encodeURIComponent(name)}`,{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirm:true})}); $('#notice').textContent=`${name} removed from Lwa's protected credential store.`; await load(); } catch(e) { $('#notice').className='notice error'; $('#notice').textContent=`Credential deletion failed: ${e.message}`; }});
load(); setInterval(load, 15000);
