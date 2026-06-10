const state = { view: 'dashboard', projects: [], routes: [], responses: [], selectedProject: null, selectedRoute: null };
const $ = (s) => document.querySelector(s);
const api = async (url, options = {}) => {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) throw new Error(data?.detail || data?.message || res.statusText);
  return data;
};
const toast = (msg) => { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'), 2500); };
const pretty = (v) => JSON.stringify(v ?? null, null, 2);
const parseJSON = (value, field) => { if (!value.trim()) return null; try { return JSON.parse(value); } catch { throw new Error(`${field} must be valid JSON`); } };
const esc = (v) => String(v ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function setView(view) {
  state.view = view;
  document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
  $(`#${view}`).classList.remove('hidden');
  document.querySelectorAll('.nav').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  $('#pageTitle').textContent = view[0].toUpperCase() + view.slice(1);
}

async function loadDashboard() {
  setView('dashboard');
  const d = await api('/admin/dashboard');
  $('#dashboard').innerHTML = `<div class="grid">
    ${card('Total projects', d.total_projects)}${card('Total routes', d.total_routes)}${card('Active routes', d.total_active_routes)}${card('Request logs', d.total_request_logs)}
  </div><div class="panel"><div class="toolbar"><h3>Latest request logs</h3><button class="light" onclick="loadLogs()">Open logs</button></div>${logsTable(d.latest_logs)}</div>`;
}
const card = (label, num) => `<div class="card"><div class="num">${num}</div><div class="label">${label}</div></div>`;

async function loadProjects() {
  setView('projects');
  state.projects = await api('/admin/projects');
  $('#projects').innerHTML = `<div class="panel"><div class="toolbar"><h3>Projects</h3><button onclick="projectForm()">Create project</button></div>
    <table><thead><tr><th>Name</th><th>Slug</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead><tbody>${state.projects.map(p => `<tr><td><b>${esc(p.name)}</b><br><span>${esc(p.description||'')}</span></td><td><code>${esc(p.slug)}</code></td><td>${badge(p.is_active)}</td><td>${new Date(p.created_at).toLocaleString()}</td><td class="actions"><button class="light" onclick="openRoutes(${p.id})">Routes</button><button class="gray" onclick="projectForm(${p.id})">Edit</button><button class="danger" onclick="deleteProject(${p.id})">Delete</button></td></tr>`).join('')}</tbody></table></div>`;
}
function badge(on){return `<span class="badge ${on?'':'off'}">${on?'Active':'Inactive'}</span>`}

function projectForm(id) {
  const p = state.projects.find(x => x.id === id) || {name:'',slug:'',description:'',is_active:true};
  showModal(`<h3>${id?'Edit':'Create'} project</h3><form class="form" id="projectForm">
    <label>Name<input name="name" value="${esc(p.name)}" required></label><label>Slug<input name="slug" value="${esc(p.slug)}" required></label>
    <label class="full">Description<textarea name="description">${esc(p.description||'')}</textarea></label><label><input type="checkbox" name="is_active" ${p.is_active?'checked':''}> Active</label>
    <footer><button type="button" class="gray" onclick="closeModal()">Cancel</button><button>Save</button></footer></form>`);
  $('#projectForm').onsubmit = async e => { e.preventDefault(); const f = new FormData(e.target); await api(id?`/admin/projects/${id}`:'/admin/projects',{method:id?'PUT':'POST',body:JSON.stringify({name:f.get('name'),slug:f.get('slug'),description:f.get('description'),is_active:f.has('is_active')})}); closeModal(); toast('Saved'); loadProjects(); };
}
async function deleteProject(id){ if(confirm('Delete project and all routes/responses?')){ await api(`/admin/projects/${id}`,{method:'DELETE'}); toast('Deleted'); loadProjects(); }}

async function openRoutes(projectId) {
  state.selectedProject = state.projects.find(p => p.id === projectId) || await api(`/admin/projects/${projectId}`);
  setView('routes'); $('#pageTitle').textContent = `${state.selectedProject.name} routes`;
  state.routes = await api(`/admin/projects/${projectId}/routes`);
  $('#routes').innerHTML = `<div class="panel"><div class="toolbar"><div><button class="gray" onclick="loadProjects()">← Projects</button> <b>${esc(state.selectedProject.name)}</b></div><button onclick="routeForm()">Create route</button></div>
  <table><thead><tr><th>Name</th><th>Method</th><th>Path</th><th>Mock URL</th><th>Status</th><th>Actions</th></tr></thead><tbody>${state.routes.map(r => `<tr><td><b>${esc(r.name)}</b><br>${esc(r.description||'')}</td><td class="method">${r.method}</td><td><code>${esc(r.path)}</code></td><td><code>${location.origin}/mock/${state.selectedProject.slug}${r.path}</code></td><td>${badge(r.is_active)}</td><td class="actions"><button class="light" onclick="openResponses(${r.id})">Responses</button><button class="light" onclick="loadLogs(null,${r.id})">Logs</button><button class="gray" onclick="routeForm(${r.id})">Edit</button><button class="danger" onclick="deleteRoute(${r.id})">Delete</button></td></tr>`).join('')}</tbody></table></div>`;
}
function routeForm(id){
  const r = state.routes.find(x=>x.id===id)||{name:'',method:'GET',path:'/api/example',description:'',expected_headers_json:null,expected_body_json:null,is_active:true};
  showModal(`<h3>${id?'Edit':'Create'} route</h3><form class="form" id="routeForm"><label>Name<input name="name" value="${esc(r.name)}" required></label><label>Method<select name="method">${['GET','POST','PUT','PATCH','DELETE'].map(m=>`<option ${r.method===m?'selected':''}>${m}</option>`)}</select></label><label class="full">Path<input name="path" value="${esc(r.path)}" required></label><label class="full">Description<textarea name="description">${esc(r.description||'')}</textarea></label><label class="full">Expected headers JSON<textarea name="expected_headers_json">${esc(r.expected_headers_json?pretty(r.expected_headers_json):'')}</textarea></label><label class="full">Expected body JSON<textarea name="expected_body_json">${esc(r.expected_body_json?pretty(r.expected_body_json):'')}</textarea></label><label><input type="checkbox" name="is_active" ${r.is_active?'checked':''}> Active</label><footer><button type="button" class="gray" onclick="closeModal()">Cancel</button><button>Save</button></footer></form>`);
  $('#routeForm').onsubmit = async e => { e.preventDefault(); try{ const f=new FormData(e.target); await api(id?`/admin/routes/${id}`:`/admin/projects/${state.selectedProject.id}/routes`,{method:id?'PUT':'POST',body:JSON.stringify({name:f.get('name'),method:f.get('method'),path:f.get('path'),description:f.get('description'),expected_headers_json:parseJSON(f.get('expected_headers_json'),'Expected headers'),expected_body_json:parseJSON(f.get('expected_body_json'),'Expected body'),is_active:f.has('is_active')})}); closeModal(); toast('Saved'); openRoutes(state.selectedProject.id);}catch(err){toast(err.message)}};
}
async function deleteRoute(id){ if(confirm('Delete route and responses?')){ await api(`/admin/routes/${id}`,{method:'DELETE'}); toast('Deleted'); openRoutes(state.selectedProject.id); }}

async function openResponses(routeId){
  state.selectedRoute = state.routes.find(r=>r.id===routeId) || await api(`/admin/routes/${routeId}`); state.responses = await api(`/admin/routes/${routeId}/responses`); setView('responses'); $('#pageTitle').textContent = `${state.selectedRoute.name} responses`;
  $('#responses').innerHTML = `<div class="panel"><div class="toolbar"><div><button class="gray" onclick="openRoutes(${state.selectedProject.id})">← Routes</button> <code>${state.selectedRoute.method} ${state.selectedRoute.path}</code></div><button onclick="responseForm()">Create response</button></div><table><thead><tr><th>Name</th><th>Status</th><th>Priority</th><th>Delay</th><th>Default</th><th>Condition</th><th>Actions</th></tr></thead><tbody>${state.responses.map(r=>`<tr><td><b>${esc(r.name)}</b></td><td>${r.status_code}</td><td>${r.priority}</td><td>${r.delay_ms}ms</td><td>${r.is_default?'Yes':'No'}</td><td><pre class="json">${esc(pretty(r.condition_json))}</pre></td><td class="actions"><button class="gray" onclick="responseForm(${r.id})">Edit</button><button class="light" onclick="makeDefault(${r.id})">Mark default</button><button class="danger" onclick="deleteResponse(${r.id})">Delete</button></td></tr>`).join('')}</tbody></table></div>`;
}
function responseForm(id){
 const r=state.responses.find(x=>x.id===id)||{name:'',status_code:200,headers_json:{},body_json:{message:'ok'},condition_json:null,priority:100,delay_ms:0,is_default:false,is_active:true};
 showModal(`<h3>${id?'Edit':'Create'} response</h3><form class="form" id="responseForm"><label>Name<input name="name" value="${esc(r.name)}" required></label><label>Status code<input type="number" name="status_code" value="${r.status_code}" min="100" max="599"></label><label>Priority<input type="number" name="priority" value="${r.priority}"></label><label>Delay ms<input type="number" name="delay_ms" value="${r.delay_ms}" min="0"></label><label class="full">Headers JSON<textarea name="headers_json">${esc(pretty(r.headers_json||{}))}</textarea></label><label class="full">Body JSON<textarea name="body_json">${esc(pretty(r.body_json||{}))}</textarea></label><label class="full">Condition JSON<textarea name="condition_json">${esc(r.condition_json?pretty(r.condition_json):'')}</textarea></label><label><input type="checkbox" name="is_default" ${r.is_default?'checked':''}> Default</label><label><input type="checkbox" name="is_active" ${r.is_active?'checked':''}> Active</label><footer><button type="button" class="gray" onclick="closeModal()">Cancel</button><button>Save</button></footer></form>`);
 $('#responseForm').onsubmit=async e=>{e.preventDefault();try{const f=new FormData(e.target);await api(id?`/admin/responses/${id}`:`/admin/routes/${state.selectedRoute.id}/responses`,{method:id?'PUT':'POST',body:JSON.stringify({name:f.get('name'),status_code:Number(f.get('status_code')),headers_json:parseJSON(f.get('headers_json'),'Headers'),body_json:parseJSON(f.get('body_json'),'Body'),condition_json:parseJSON(f.get('condition_json'),'Condition'),priority:Number(f.get('priority')),delay_ms:Number(f.get('delay_ms')),is_default:f.has('is_default'),is_active:f.has('is_active')})});closeModal();toast('Saved');openResponses(state.selectedRoute.id)}catch(err){toast(err.message)}};
}
async function makeDefault(id){ await api(`/admin/responses/${id}`,{method:'PUT',body:JSON.stringify({is_default:true})}); toast('Default updated'); openResponses(state.selectedRoute.id); }
async function deleteResponse(id){ if(confirm('Delete response?')){ await api(`/admin/responses/${id}`,{method:'DELETE'}); toast('Deleted'); openResponses(state.selectedRoute.id); }}

async function loadLogs(projectId=null, routeId=null){
  setView('logs'); $('#pageTitle').textContent='Logs'; if(!state.projects.length) state.projects=await api('/admin/projects');
  const url = routeId ? `/admin/routes/${routeId}/logs` : projectId ? `/admin/projects/${projectId}/logs` : '/admin/logs'; const logs=await api(url);
  $('#logs').innerHTML = `<div class="panel"><div class="toolbar"><h3>Request logs</h3><div class="filters"><select id="projectFilter"><option value="">All projects</option>${state.projects.map(p=>`<option value="${p.id}" ${projectId===p.id?'selected':''}>${esc(p.name)}</option>`)}</select><button class="light" onclick="loadLogs(Number($('#projectFilter').value)||null)">Filter</button><button class="gray" onclick="loadLogs()">Clear</button></div></div>${logsTable(logs, true)}</div>`;
}
function logsTable(logs, expanded=false){ return `<table><thead><tr><th>Time</th><th>Method</th><th>Path</th><th>Status</th><th>Matched</th>${expanded?'<th>Payload</th>':''}</tr></thead><tbody>${logs.map(l=>`<tr><td>${new Date(l.created_at).toLocaleString()}</td><td class="method">${l.method}</td><td><code>${esc(l.path)}</code></td><td>${l.status_code}</td><td>${esc(l.response_name||'-')}</td>${expanded?`<td><details><summary>View JSON</summary><b>Query</b><pre class="json">${esc(pretty(l.query_json))}</pre><b>Body</b><pre class="json">${esc(pretty(l.body_json))}</pre><b>Headers</b><pre class="json">${esc(pretty(l.headers_json))}</pre></details></td>`:''}</tr>`).join('')}</tbody></table>`; }
function showModal(html){ $('#modalBody').innerHTML=html; $('#modal').showModal(); }
function closeModal(){ $('#modal').close(); }
document.querySelectorAll('.nav').forEach(b=>b.onclick=()=> b.dataset.view==='dashboard'?loadDashboard():b.dataset.view==='projects'?loadProjects():loadLogs());
$('#seedBtn').onclick=async()=>{ await api('/admin/seed/demo',{method:'POST'}); toast('Demo seeded'); loadDashboard(); };
loadDashboard().catch(e=>toast(e.message));
