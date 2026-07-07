// ===== utilidades =====
async function api(ruta, datos){
  const opt = datos ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(datos)} : {};
  const r = await fetch(ruta, opt);
  return r.json();
}
function fmt(n, d=2){ return (n===null||n===undefined||n==='') ? '—' : Number(n).toFixed(d); }
function esc(s){ return String(s).replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }

const CANALES_OPT = Array.from({length:10}, (_,i)=>`Canal ${i+1}`);
const CANALES_ELE = ['2000Hz','3000Hz','4000Hz','5000Hz'];

// ===== login =====
async function login(){
  const u = document.getElementById('lg-user').value.trim();
  const p = document.getElementById('lg-pass').value;
  const r = await api('/api/login', {usuario:u, clave:p});
  if(r.ok){
    document.getElementById('login').classList.add('oculto');
    document.getElementById('app').classList.remove('oculto');
    document.getElementById('who').textContent = u;
    ir('procesar');
  } else { document.getElementById('lg-err').textContent = 'Usuario o contraseña incorrectos.'; }
}
document.getElementById('lg-pass').addEventListener('keydown', e=>{ if(e.key==='Enter') login(); });

// ===== navegación =====
const TITULOS = {procesar:'Procesar corrida', limites:'Estándar de calidad', dashboard:'Dashboard', historial:'Historial de lotes'};
let estadoEval = null;
function ir(v){
  document.querySelectorAll('.nav a').forEach(a=>a.classList.toggle('activo', a.dataset.v===v));
  document.getElementById('titulo').textContent = TITULOS[v];
  if(v==='procesar') vistaProcesar();
  if(v==='limites') vistaLimites();
  if(v==='dashboard') vistaDashboard();
  if(v==='historial') vistaHistorial();
}

// ===== archivos =====
let archivos = [];
function fileToB64(file){ return new Promise((res,rej)=>{const fr=new FileReader();fr.onload=()=>res(fr.result.split(',')[1]);fr.onerror=rej;fr.readAsDataURL(file);}); }
function numDe(nombre){ const base=nombre.replace(/\.[^.]+$/,''); const m=base.match(/\d+/g); return m?m[m.length-1]:''; }

// ============ VISTA: PROCESAR ============
async function vistaProcesar(){
  const perfiles = (await api('/api/perfiles')).perfiles;
  const ops = perfiles.map(p=>`<option>${esc(p.nombre)}</option>`).join('');
  document.getElementById('vistas').innerHTML = `
    <div class="card">
      <div class="drop" id="drop">⬆ <b>Carga los archivos JSON de la corrida</b>
        <span class="mini">Puedes subir un archivo, varios, o una carpeta completa. El número de pieza se toma del nombre (puedes corregirlo).</span>
        <div class="fila" style="justify-content:center;margin-top:12px">
          <button class="btn-out" id="btnArch" type="button">📄 Subir archivo(s)</button>
          <button class="btn-out" id="btnCarp" type="button">📁 Subir carpeta</button>
        </div>
        <input id="fileinput" type="file" accept=".json,.xlsx,.xlsm" multiple class="oculto">
        <input id="folderinput" type="file" webkitdirectory directory multiple class="oculto">
      </div>
      <div class="fila">
        <div style="flex:1"><label class="f">Perfil de estándar</label>
          <select class="f" id="perfil">${ops||'<option value="">— crea uno en Estándar de calidad —</option>'}</select></div>
        <div style="flex:1"><label class="f">Lote / corrida</label><input class="f" id="lote" placeholder="Ej. Lote 1"></div>
        <div style="flex:1"><label class="f">Operador</label><input class="f" id="operador" placeholder="Tu nombre"></div>
        <button class="btn-sm" onclick="evaluar()">▶ Evaluar corrida</button>
      </div>
    </div>
    <div id="prev"></div><div id="resCorrida"></div>`;
  const fi = document.getElementById('fileinput');
  const fo = document.getElementById('folderinput');
  document.getElementById('btnArch').onclick = ()=> fi.click();
  document.getElementById('btnCarp').onclick = ()=> fo.click();
  const cargar = async (lista)=>{
    archivos = [];
    for(const f of lista){
      const n = f.name.toLowerCase();
      if(!(n.endsWith('.json') || n.endsWith('.xlsx') || n.endsWith('.xlsm'))) continue; // ignora otros archivos de la carpeta
      archivos.push({nombre:f.name, pieza:numDe(f.name), b64:await fileToB64(f)});
    }
    if(!archivos.length){ alert('No se encontraron archivos .json en la selección.'); return; }
    pintarPrev();
  };
  fi.onchange = ()=> cargar(fi.files);
  fo.onchange = ()=> cargar(fo.files);
}
function pintarPrev(){
  if(!archivos.length){ document.getElementById('prev').innerHTML=''; return; }
  const filas = archivos.map((a,i)=>`<tr><td>${esc(a.nombre)}</td>
     <td><input class="f" style="width:120px;padding:5px 8px" value="${esc(a.pieza)}" onchange="archivos[${i}].pieza=this.value"></td></tr>`).join('');
  document.getElementById('prev').innerHTML = `<div class="card"><h3>Piezas detectadas (${archivos.length})</h3>
     <table><tr><th>Archivo</th><th>No. de pieza</th></tr>${filas}</table></div>`;
}
async function evaluar(){
  const perfil=document.getElementById('perfil').value, lote=document.getElementById('lote').value.trim(), operador=document.getElementById('operador').value.trim();
  if(!perfil){ alert('Selecciona un perfil de estándar (créalo en "Estándar de calidad").'); return; }
  if(!archivos.length){ alert('Selecciona los archivos JSON de la corrida.'); return; }
  if(archivos.some(a=>!a.pieza)){ alert('Hay archivos sin número de pieza. Corrígelos arriba.'); return; }
  document.getElementById('resCorrida').innerHTML = '<div class="card">Evaluando…</div>';
  const r = await api('/api/evaluar', {perfil, lote:lote||'Lote sin nombre', operador:operador||'—', archivos});
  if(!r.ok){ document.getElementById('resCorrida').innerHTML = `<div class="card" style="color:var(--rojo-tx)">Error: ${esc(r.error)}</div>`; return; }
  estadoEval = r; pintarResultados(r);
}
function estadoPrueba(detalle, prueba){ const fs=detalle[prueba]; if(!fs||!fs.length) return null; return fs.every(x=>x.resultado==='PASA')?'PASO':'NO PASO'; }
function fallasTexto(detalle){ const out=[]; for(const p in detalle) for(const f of detalle[p]) if(f.resultado==='FALLA') out.push(`${f.canal} (fase ${f.fase_fallo})`); return out.length?out.join('; '):'—'; }

function pintarResultados(r){
  const filas = r.resultados.map(x=>{
    const eo=estadoPrueba(x.detalle,'Optico'), ee=estadoPrueba(x.detalle,'Electrico');
    const pill=v=> v==='PASO'?'<span class="pill ok">Pasó</span>':v==='NO PASO'?'<span class="pill no">No pasó</span>':'—';
    const alerta = x.veredicto!=='PASO' ? '<span class="pill no">⚠ Repetir prueba</span>' : '';
    return `<tr class="row-link" onclick='verPieza(${JSON.stringify(x.pieza)})'>
      <td><b>${esc(x.pieza)}</b></td><td>${pill(eo)}</td><td>${pill(ee)}</td>
      <td>${x.veredicto==='PASO'?'<span class="pill ok">PASÓ</span>':'<span class="pill no">NO PASÓ</span>'}</td>
      <td>${alerta}</td><td class="mini">${esc(fallasTexto(x.detalle))}</td></tr>`;
  }).join('');
  document.getElementById('resCorrida').innerHTML = `
    <div class="grid-kpi">
      <div class="kpi"><div class="lbl">Evaluadas</div><div class="val">${r.resultados.length}</div></div>
      <div class="kpi ok"><div class="lbl">Pasaron</div><div class="val">${r.pasaron}</div></div>
      <div class="kpi no"><div class="lbl">Fallaron</div><div class="val">${r.fallaron}</div></div>
      <div class="kpi az"><div class="lbl">Aprobación</div><div class="val">${r.resultados.length?Math.round(100*r.pasaron/r.resultados.length):0}%</div></div>
    </div>
    <div class="card"><h3>Resultado por desechable</h3>
      <table><tr><th>Pieza</th><th>Óptico</th><th>Eléctrico</th><th>Final</th><th>Alerta</th><th>Detalle</th></tr>${filas}</table>
      <div class="fila" style="margin-top:14px">
        <button class="btn-out" onclick="repLote(${r.batch_id})">📄 Reporte del lote (PDF)</button>
        <button class="btn-out" onclick="exportarExcel(${r.batch_id})">📊 Excel de verificación</button>
      </div></div>`;
}
async function verPieza(pieza){
  if(!estadoEval) return;
  const x = estadoEval.resultados.find(r=>String(r.pieza)===String(pieza)); if(!x) return;
  let html = `<div class="card"><h3>Pieza ${esc(pieza)} — ${x.veredicto==='PASO'?'<span class="pill ok">PASÓ</span>':'<span class="pill no">NO PASÓ</span>'}</h3>`;
  for(const prueba in x.detalle){
    html += `<h4 style="color:var(--azul);font-size:13px;margin:10px 0 6px">${prueba==='Optico'?'Prueba óptica':'Prueba eléctrica'}</h4>`;
    html += `<table><tr><th>Canal</th><th>Media</th><th>Rango media</th><th>Desv.</th><th>Rango desv.</th><th>Mejor hist.</th><th>Estado</th><th>Falla en</th></tr>`;
    for(const f of x.detalle[prueba]){
      const e=f.estandar||{};
      const rm = (e.media_min!=null||e.media_max!=null)?`${fmt(e.media_min)} – ${fmt(e.media_max)}`:'—';
      const rd = (e.desv_min!=null||e.desv_max!=null)?`${fmt(e.desv_min)} – ${fmt(e.desv_max)}`:'—';
      const motivo = f.resultado==='FALLA'? `Fase ${f.fase_fallo}: ${esc(f.motivos.join(', '))}` : '';
      html += `<tr><td>${esc(f.canal)}</td><td>${fmt(f.media)}</td><td class="mini">${rm}</td>
        <td>${fmt(f.desv)}</td><td class="mini">${rd}</td><td class="mini">${fmt(f.mejor_hist)}</td>
        <td>${f.resultado==='PASA'?'<span class="pill ok">Pasa</span>':'<span class="pill no">Falla</span>'}</td>
        <td class="mini">${motivo}</td></tr>`;
    }
    html += `</table>`;
  }
  html += `<div class="fila" style="margin-top:14px"><button class="btn-out" onclick="repPieza(${estadoEval.batch_id},${JSON.stringify(pieza)})">📄 Reporte de esta pieza</button></div></div>`;
  document.getElementById('resCorrida').insertAdjacentHTML('afterbegin', html);
  window.scrollTo(0,0);
}
async function repPieza(bid,pieza){ const r=await api('/api/reporte_pieza',{batch_id:bid,pieza}); alert(r.ok?'Reporte guardado en:\n'+r.ruta:'Error: '+r.error); }
async function repLote(bid){ const r=await api('/api/reporte_lote',{batch_id:bid}); alert(r.ok?'Reporte del lote guardado en:\n'+r.ruta:'Error: '+r.error); }
async function exportarExcel(bid){ const r=await api('/api/exportar_excel',{batch_id:bid}); alert(r.ok?'Excel guardado en:\n'+r.ruta+'\n\nPuedes subirlo a tu Drive desde ahí.':'Error: '+r.error); }

// ============ VISTA: LIMITES / ESTANDAR ============
async function vistaLimites(){
  const perfiles = (await api('/api/perfiles')).perfiles;
  const ops = perfiles.map(p=>`<option>${esc(p.nombre)}</option>`).join('');
  const tabla = (titulo, icono, prueba, canales) => `
    <div class="card"><h3>${icono} ${titulo}</h3>
      <p class="mini" style="margin-bottom:8px">Fase 1: la desviación debe estar en su rango y no superar el mejor histórico. Fase 2: el promedio debe estar en su rango.</p>
      <table><tr><th>Canal</th><th>Desv. mín</th><th>Desv. máx</th><th>Media mín</th><th>Media máx</th></tr>
      ${canales.map(c=>`<tr><td>${esc(c)}</td>
        ${['desv_min','desv_max','media_min','media_max'].map(k=>`<td><input class="f est-in" data-prueba="${prueba}" data-canal="${esc(c)}" data-campo="${k}" type="number" step="0.01" style="width:110px;padding:6px 8px"></td>`).join('')}
      </tr>`).join('')}</table></div>`;
  document.getElementById('vistas').innerHTML = `
    <div class="card"><div class="fila">
      <div><label class="f">Perfil guardado</label><select class="f" id="perfilSel" style="width:240px">${ops||'<option value="">— ninguno —</option>'}</select></div>
      <button class="btn-out" onclick="cargarPerfil()">Cargar</button>
      <button class="btn-out" onclick="borrarPerfil()">Eliminar</button>
    </div></div>
    ${tabla('Prueba óptica','💡','Optico',CANALES_OPT)}
    ${tabla('Prueba eléctrica','⚡','Electrico',CANALES_ELE)}
    <div class="card"><div class="fila">
      <div style="flex:1"><label class="f">Guardar como perfil (nombre)</label><input class="f" id="nombrePerfil" placeholder="Ej. Producto A v1"></div>
      <button class="btn-sm" onclick="guardarPerfil()">💾 Guardar perfil</button>
    </div></div>`;
}
function leerEstandar(){
  const L = {Optico:{}, Electrico:{}};
  document.querySelectorAll('.est-in').forEach(inp=>{
    const p=inp.dataset.prueba, c=inp.dataset.canal, k=inp.dataset.campo, v=inp.value;
    L[p][c] = L[p][c] || {};
    L[p][c][k] = v===''? null : Number(v);
  });
  return L;
}
async function guardarPerfil(){
  const nombre = document.getElementById('nombrePerfil').value.trim();
  if(!nombre){ alert('Escribe un nombre para el perfil.'); return; }
  await api('/api/guardar_perfil', {nombre, limites:leerEstandar()});
  alert('Perfil "'+nombre+'" guardado.'); vistaLimites();
}
async function cargarPerfil(){
  const nombre = document.getElementById('perfilSel').value; if(!nombre) return;
  const L = (await api('/api/cargar_perfil',{nombre})).limites; if(!L) return;
  document.querySelectorAll('.est-in').forEach(inp=>{
    const v = L[inp.dataset.prueba]?.[inp.dataset.canal]?.[inp.dataset.campo];
    inp.value = (v===null||v===undefined)?'':v;
  });
  document.getElementById('nombrePerfil').value = nombre;
}
async function borrarPerfil(){
  const nombre = document.getElementById('perfilSel').value;
  if(nombre && confirm('¿Eliminar el perfil "'+nombre+'"?')){ await api('/api/borrar_perfil',{nombre}); vistaLimites(); }
}

// ============ VISTA: DASHBOARD ============
async function vistaDashboard(){
  const batches = (await api('/api/batches')).batches;
  const conteo = (await api('/api/fallas_canal')).conteo;
  const total = batches.reduce((s,b)=>s+b.total,0), pas = batches.reduce((s,b)=>s+b.pasaron,0);
  const tasa = total?Math.round(100*pas/total):0;
  const pts = batches.slice().reverse();
  const w=600,h=140,pad=24;
  let poly = pts.length? pts.map((b,i)=>{const x=pad+i*((w-2*pad)/Math.max(1,pts.length-1));const t=b.total?b.pasaron/b.total:0;const y=h-pad-t*(h-2*pad);return `${x.toFixed(0)},${y.toFixed(0)}`;}).join(' '):'';
  const top = Object.entries(conteo).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const maxF = top.length?top[0][1]:1;
  const barras = top.map(([c,n])=>`<div style="display:flex;align-items:center;gap:8px;margin:5px 0">
     <span class="mini" style="width:150px">${esc(c)}</span>
     <div class="barra" style="width:${Math.round(100*n/maxF)}%;background:${n===maxF?'#D85A30':'#EF9F27'}"></div>
     <span class="mini">${n}</span></div>`).join('') || '<p class="mini">Sin fallas registradas todavía.</p>';
  document.getElementById('vistas').innerHTML = `
    <div class="grid-kpi">
      <div class="kpi"><div class="lbl">Lotes evaluados</div><div class="val">${batches.length}</div></div>
      <div class="kpi"><div class="lbl">Piezas totales</div><div class="val">${total}</div></div>
      <div class="kpi ok"><div class="lbl">Pasaron</div><div class="val">${pas}</div></div>
      <div class="kpi az"><div class="lbl">Aprobación global</div><div class="val">${tasa}%</div></div>
    </div>
    <div class="card"><h3>Tasa de aprobación por lote (en el tiempo)</h3>
      <svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto">
        <line x1="${pad}" y1="${h-pad}" x2="${w-pad}" y2="${h-pad}" stroke="#E2E2DD"/>
        <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${h-pad}" stroke="#E2E2DD"/>
        ${poly?`<polyline points="${poly}" fill="none" stroke="#185FA5" stroke-width="2.5"/>`:''}
        ${pts.map((b,i)=>{const x=pad+i*((w-2*pad)/Math.max(1,pts.length-1));const t=b.total?b.pasaron/b.total:0;const y=h-pad-t*(h-2*pad);return `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="3" fill="#0C447C"/>`;}).join('')}
      </svg><p class="mini">Cada punto es un lote (del más antiguo al más reciente).</p></div>
    <div class="card"><h3>Canales que más fallan (todos los lotes)</h3>${barras}</div>`;
}

// ============ VISTA: HISTORIAL ============
async function vistaHistorial(){
  const batches = (await api('/api/batches')).batches;
  const filas = batches.map(b=>`<tr class="row-link" onclick="verLote(${b.id})">
     <td><b>${esc(b.nombre)}</b></td><td>${esc((b.fecha||'').slice(0,10))}</td><td>${esc(b.operador||'')}</td>
     <td>${b.total}</td><td style="color:var(--verde-tx)">${b.pasaron}</td><td style="color:var(--rojo-tx)">${b.fallaron}</td>
     <td><b>${b.total?Math.round(100*b.pasaron/b.total):0}%</b></td></tr>`).join('')
     || '<tr><td colspan="7" class="mini">Aún no hay lotes evaluados.</td></tr>';
  document.getElementById('vistas').innerHTML = `
    <div class="card"><input class="f" id="buscar" placeholder="🔎 Buscar lote u operador…" style="margin-bottom:12px" onkeyup="filtrarHist()">
      <table id="tblHist"><tr><th>Lote</th><th>Fecha</th><th>Operador</th><th>Total</th><th>Pasaron</th><th>Fallaron</th><th>% Aprob.</th></tr>${filas}</table></div>
    <div id="detLote"></div>`;
}
function filtrarHist(){ const q=document.getElementById('buscar').value.toLowerCase(); document.querySelectorAll('#tblHist tr').forEach((tr,i)=>{if(i===0)return;tr.style.display=tr.textContent.toLowerCase().includes(q)?'':'none';}); }
async function verLote(bid){
  const r = await api('/api/batch/'+bid); const b=r.batch;
  const pill=v=> v==='PASO'?'<span class="pill ok">PASÓ</span>':'<span class="pill no">NO PASÓ</span>';
  const filas = r.resultados.map(x=>{
    const eo=estadoPrueba(x.detalle,'Optico'), ee=estadoPrueba(x.detalle,'Electrico');
    const p=v=> v==='PASO'?'<span class="pill ok">Pasó</span>':v==='NO PASO'?'<span class="pill no">No pasó</span>':'—';
    return `<tr><td><b>${esc(x.no_pieza)}</b></td><td>${p(eo)}</td><td>${p(ee)}</td><td>${pill(x.veredicto)}</td>
       <td><button class="btn-out" style="padding:5px 10px" onclick="repPieza(${bid},${JSON.stringify(x.no_pieza)})">PDF</button></td></tr>`;
  }).join('');
  const total=b.total||0;
  document.getElementById('detLote').innerHTML = `
    <div class="grid-kpi">
      <div class="kpi"><div class="lbl">Piezas</div><div class="val">${b.total}</div></div>
      <div class="kpi ok"><div class="lbl">Pasaron</div><div class="val">${b.pasaron}</div></div>
      <div class="kpi no"><div class="lbl">Fallaron</div><div class="val">${b.fallaron}</div></div>
      <div class="kpi az"><div class="lbl">Aprobación</div><div class="val">${total?Math.round(100*b.pasaron/total):0}%</div></div></div>
    <div class="card"><h3>${esc(b.nombre)} — detalle</h3>
      <table><tr><th>Pieza</th><th>Óptico</th><th>Eléctrico</th><th>Final</th><th>Reporte</th></tr>${filas}</table>
      <div class="fila" style="margin-top:14px">
        <button class="btn-out" onclick="repLote(${bid})">📄 Reporte del lote (PDF)</button>
        <button class="btn-out" onclick="exportarExcel(${bid})">📊 Excel de verificación</button>
      </div></div>`;
  document.getElementById('detLote').scrollIntoView({behavior:'smooth'});
}
