// ===== utilidades =====
async function api(ruta, datos){
  const opt = datos ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(datos)} : {};
  const r = await fetch(ruta, opt);
  return r.json();
}
function fmt(n, d=2){ return (n===null||n===undefined||n==='') ? '' : Number(n).toFixed(d); }
function esc(s){ return String(s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
// Para pasar un texto como argumento JS dentro de un atributo onclick="...":
// JSON.stringify lo vuelve literal JS y esc() protege las comillas del HTML.
function jsAttr(v){ return esc(JSON.stringify(String(v))); }

// Rango [min,max] como texto claro (sin guiones): tolera que falte un lado.
function rangoTxt(lo, hi){
  if(lo==null && hi==null) return '<span class="mini">Sin límite</span>';
  if(lo==null) return `≤ ${fmt(hi)}`;
  if(hi==null) return `≥ ${fmt(lo)}`;
  return `${fmt(lo)} a ${fmt(hi)}`;
}

// Iconos SVG inline (estilo lucide, trazo 2, heredan el color del texto).
const _IC = {
  play:'<polygon points="6 3 20 12 6 21 6 3"/>',
  file:'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
  folder:'<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
  doc:'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
  sheet:'<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/>',
  trash:'<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  save:'<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
  upload:'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
  alert:'<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  bell:'<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
  check:'<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
  sun:'<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
  zap:'<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
  redo:'<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>',
  chart:'<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
};
function ic(n){ return `<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${_IC[n]||''}</svg>`; }

const CANALES_OPT = ['415','445','480','515','555','590','630','680','CLEAR','>700'];
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
    const av = document.querySelector('.top .user .avatar');
    if(av) av.textContent = (u[0]||'?').toUpperCase();
    ir('procesar');
  } else { document.getElementById('lg-err').textContent = 'Usuario o contraseña incorrectos.'; }
}
document.getElementById('lg-pass').addEventListener('keydown', e=>{ if(e.key==='Enter') login(); });

// ===== navegación =====
const TITULOS = {procesar:'Procesar corrida', limites:'Estándar de calidad', dashboard:'Dashboard', historial:'Historial de lotes'};
let vistaNombre = 'procesar';   // vista visible ahora (para refrescar tras editar/borrar)
function ir(v){
  vistaNombre = v;
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
      <div class="drop" id="drop">
        <div class="drop-ic">${ic('upload')}</div>
        <b>Carga los archivos JSON de la corrida</b>
        <span class="mini">Puedes subir un archivo, varios, o una carpeta completa. El número de pieza se toma del nombre (puedes corregirlo).</span>
        <div class="fila" style="justify-content:center;margin-top:14px">
          <button class="btn-out" id="btnArch" type="button">${ic('file')} Subir archivos</button>
          <button class="btn-out" id="btnCarp" type="button">${ic('folder')} Subir carpeta</button>
        </div>
        <input id="fileinput" type="file" accept=".json,.xlsx,.xlsm" multiple class="oculto">
        <input id="folderinput" type="file" webkitdirectory directory multiple class="oculto">
      </div>
      <div class="fila">
        <div style="flex:1"><label class="f">Perfil de estándar</label>
          <select class="f" id="perfil">${ops||'<option value="">Crea uno en Estándar de calidad</option>'}</select></div>
        <div style="flex:1"><label class="f">Lote / corrida</label><input class="f" id="lote" placeholder="Ej. Lote 1"></div>
        <div style="flex:1"><label class="f">Operador</label><input class="f" id="operador" placeholder="Tu nombre"></div>
        <button class="btn-sm" onclick="evaluar()">${ic('play')} Evaluar corrida</button>
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
  const r = await api('/api/evaluar', {perfil, lote:lote||'Lote sin nombre', operador:operador||'Sin registrar', archivos});
  if(!r.ok){ document.getElementById('resCorrida').innerHTML = `<div class="card" style="color:var(--rojo-tx)">Error: ${esc(r.error)}</div>`; return; }
  pintarResultados(r);
}
function estadoPrueba(detalle, prueba){
  const fs=detalle[prueba]; if(!fs||!fs.length) return null;
  if(fs.some(x=>x.resultado==='FALLA')) return 'NO PASO';
  if(fs.some(x=>x.resultado==='SIN ESTANDAR')) return 'INCOMPLETO';
  return 'PASO';
}
// pill para estado de prueba / veredicto: verde=pasó, rojo=no pasó, ámbar=incompleto, gris=rechazado
function pillVer(v, txtOk, txtNo, txtInc){
  if(v==='PASO') return `<span class="pill ok">${txtOk}</span>`;
  if(v==='NO PASO') return `<span class="pill no">${txtNo}</span>`;
  if(v==='INCOMPLETO') return `<span class="pill warn">${txtInc}</span>`;
  if(v==='RECHAZADO') return `<span class="pill err">Formato inválido</span>`;
  return '<span class="pill neutral">Sin datos</span>';
}
function fallasTexto(detalle){
  const out=[];
  for(const p in detalle) for(const f of detalle[p]){
    if(f.resultado==='FALLA') out.push(`${f.canal} (fase ${f.fase_fallo})`);
    else if(f.resultado==='SIN ESTANDAR') out.push(`${f.canal} (sin estándar)`);
  }
  return out.length?out.join('; '):'Ninguna';
}

// vista actualmente mostrada (corrida recién evaluada o lote del historial),
// para que el modal de detalle sepa de dónde leer la pieza.
let vistaActual = null; // {batch_id, resultados}
function _keyPieza(x){ return String(x.pieza !== undefined ? x.pieza : x.no_pieza); }
function claseEstado(v){ return v==='PASO'?'ok':v==='INCOMPLETO'?'warn':v==='RECHAZADO'?'err':'no'; }

// --- Mapa del lote: un cuadro de color por desechable, clic para ver detalle ---
function mapaHTML(resultados){
  const celdas = resultados.map(x=>{
    const p=_keyPieza(x);
    return `<div class="celda ${claseEstado(x.veredicto)}" title="Pieza ${esc(p)}: ${x.veredicto}" onclick="verPieza(${jsAttr(p)})">${esc(p)}</div>`;
  }).join('');
  return `<div class="card"><h3>Mapa del lote <span class="mini" style="font-weight:400">(${resultados.length} desechables)</span></h3>
    <p class="mini" style="margin-bottom:8px">Clic en un desechable para ver su detalle por canal.</p>
    <div class="mapa">${celdas}</div>
    <div class="leyenda">
      <span><i style="background:var(--ok)"></i> Pasó</span>
      <span><i style="background:var(--no)"></i> No pasó</span>
      <span><i style="background:var(--warn)"></i> Incompleto</span>
      <span><i style="background:#5A6472"></i> Rechazado</span>
    </div></div>`;
}

// --- Tabla de solo los desechables que requieren atención ---
function problemasHTML(resultados){
  const probs = resultados.filter(x=>x.veredicto!=='PASO');
  if(!probs.length) return `<div class="card" style="color:var(--ok-tx);font-weight:600">${ic('check')} Todos los desechables pasaron.</div>`;
  const filas = probs.map(x=>{
    const p=_keyPieza(x);
    let motivos=[];
    if(x.veredicto==='RECHAZADO'){
      motivos.push(esc(x.error||'El archivo no es del formato del equipo.'));
    } else {
      for(const prueba in x.detalle) for(const f of x.detalle[prueba]){
        const pr = prueba==='Optico'?'Óptica':'Eléctrica';
        if(f.resultado==='FALLA') motivos.push(`${pr} ${esc(f.canal)} (Fase ${f.fase_fallo}: ${esc((f.motivos||[]).join(', '))})`);
        else if(f.resultado==='SIN ESTANDAR') motivos.push(`${pr} ${esc(f.canal)} (sin estándar)`);
      }
    }
    return `<tr class="row-link" onclick="verPieza(${jsAttr(p)})">
      <td><b>${esc(p)}</b></td><td>${pillVer(x.veredicto,'PASÓ','NO PASÓ','INCOMPLETO')}</td>
      <td class="mini">${motivos.join('<br>')||''}</td></tr>`;
  }).join('');
  return `<div class="card"><h3>${ic('alert')} Requieren atención <span class="mini" style="font-weight:400">(${probs.length})</span></h3>
    <div class="tabla-scroll"><table><tr><th>Pieza</th><th>Veredicto</th><th>Canales y motivo</th></tr>${filas}</table></div></div>`;
}

// --- Tabla completa (colapsada por defecto) ---
function tablaCompletaHTML(resultados){
  const filas = resultados.map(x=>{
    const p=_keyPieza(x);
    const eo=estadoPrueba(x.detalle,'Optico'), ee=estadoPrueba(x.detalle,'Electrico');
    return `<tr class="row-link" onclick="verPieza(${jsAttr(p)})">
      <td><b>${esc(p)}</b></td><td>${pillVer(eo,'Pasó','No pasó','Incompleto')}</td>
      <td>${pillVer(ee,'Pasó','No pasó','Incompleto')}</td>
      <td>${pillVer(x.veredicto,'PASÓ','NO PASÓ','INCOMPLETO')}</td></tr>`;
  }).join('');
  return `<div class="tabla-scroll"><table><tr><th>Pieza</th><th>Óptico</th><th>Eléctrico</th><th>Final</th></tr>${filas}</table></div>`;
}
function toggleTodas(btn){
  const t=document.getElementById('tablaTodas');
  const abierto=t.classList.toggle('oculto');
  btn.textContent = abierto ? `Ver la lista completa (${t.dataset.n})` : 'Ocultar la lista completa';
}

function pintarResultados(r){
  vistaActual = {batch_id:r.batch_id, resultados:r.resultados};
  const total = r.resultados.length;
  document.getElementById('resCorrida').innerHTML = `
    <div class="grid-kpi">
      <div class="kpi"><div class="lbl">Evaluadas</div><div class="val">${total}</div></div>
      <div class="kpi ok"><div class="lbl">Pasaron</div><div class="val">${r.pasaron}</div></div>
      <div class="kpi no"><div class="lbl">Fallaron</div><div class="val">${r.fallaron}</div></div>
      <div class="kpi"><div class="lbl">Incompletos</div><div class="val" style="color:var(--warn-tx)">${r.incompletos||0}</div></div>
      ${r.rechazados?`<div class="kpi"><div class="lbl">Rechazados</div><div class="val" style="color:var(--neutro-tx)">${r.rechazados}</div></div>`:''}
      <div class="kpi az"><div class="lbl">Aprobación</div><div class="val">${total?Math.round(100*r.pasaron/total):0}%</div></div>
    </div>
    ${mapaHTML(r.resultados)}
    ${problemasHTML(r.resultados)}
    <div class="card">
      <div class="fila" style="justify-content:space-between; align-items:center">
        <button class="btn-out" onclick="toggleTodas(this)">Ver la lista completa (${total})</button>
        <div class="fila">
          <button class="btn-out" onclick="repLote(${r.batch_id})">${ic('doc')} Reporte del lote (PDF)</button>
          <button class="btn-out" onclick="exportarExcel(${r.batch_id})">${ic('sheet')} Excel de verificación</button>
        </div>
      </div>
      <div id="tablaTodas" class="oculto" data-n="${total}" style="margin-top:12px">${tablaCompletaHTML(r.resultados)}</div>
    </div>`;
}

// --- Modal de detalle por canal de una pieza ---
function abrirModal(html){
  document.getElementById('modal-cont').innerHTML = html;
  document.getElementById('modal').classList.remove('oculto');
}
function cerrarModal(){ document.getElementById('modal').classList.add('oculto'); }
document.addEventListener('keydown', e=>{ if(e.key==='Escape') cerrarModal(); });

function verPieza(pieza){
  if(!vistaActual) return;
  const x = vistaActual.resultados.find(r=>_keyPieza(r)===String(pieza)); if(!x) return;
  let html = `<h3 style="display:flex;align-items:center;gap:10px;font-size:16px;font-weight:650;letter-spacing:-.01em">
    Pieza ${esc(pieza)} ${pillVer(x.veredicto,'PASÓ','NO PASÓ','INCOMPLETO')}</h3>`;
  if(x.veredicto==='RECHAZADO'){
    html += `<div style="background:var(--neutro-bg);border:1px solid #D5DAE1;border-radius:12px;padding:14px 16px;margin-top:14px">
      <b style="color:var(--neutro-tx)">Archivo rechazado: no se evaluó</b>
      <p class="mini" style="margin-top:6px">${esc(x.error||'El archivo no tiene el formato que entrega el equipo.')}</p>
      <p class="mini" style="margin-top:6px">Vuelve a descargar el JSON del equipo para esta pieza y súbelo de nuevo.</p></div>`;
    abrirModal(html); return;
  }
  for(const prueba in x.detalle){
    html += `<h4 style="color:var(--tinta);font-size:13px;font-weight:620;margin:16px 0 6px">${prueba==='Optico'?'Prueba óptica':'Prueba eléctrica'}</h4>`;
    html += `<div class="tabla-scroll"><table><tr><th>Canal</th><th>Media</th><th>Límite media</th><th>Desv.</th><th>Límite desv.</th><th>Estado</th><th>Falla en</th></tr>`;
    for(const f of x.detalle[prueba]){
      const e=f.estandar||{};
      const rm = rangoTxt(e.media_min, e.media_max);
      const rd = rangoTxt(e.desv_min, e.desv_max);
      const motivo = f.resultado==='FALLA'? `Fase ${f.fase_fallo}: ${esc((f.motivos||[]).join(', '))}`
                   : f.resultado==='SIN ESTANDAR'? 'Sin límite definido en el perfil' : '';
      const estadoCel = f.resultado==='PASA'?'<span class="pill ok">Pasa</span>'
                      : f.resultado==='FALLA'?'<span class="pill no">Falla</span>'
                      : '<span class="pill warn">Sin estándar</span>';
      html += `<tr><td>${esc(f.canal)}</td><td>${fmt(f.media)}</td><td class="mini">${rm}</td>
        <td>${fmt(f.desv)}</td><td class="mini">${rd}</td><td>${estadoCel}</td><td class="mini">${motivo}</td></tr>`;
    }
    html += `</table></div>`;
  }
  // x.id solo existe en piezas ya guardadas (historial/dashboard), no en una corrida recién evaluada.
  const btnBorrarPieza = x.id
    ? `<button class="btn-danger" onclick="borrarPieza(${x.id},${vistaActual.batch_id})">${ic('trash')} Eliminar esta pieza</button>`
    : '';
  html += `<div class="fila" style="margin-top:18px; justify-content:space-between">
      <button class="btn-out" onclick="repPieza(${vistaActual.batch_id},${jsAttr(pieza)})">${ic('doc')} Reporte de esta pieza</button>
      ${btnBorrarPieza}</div>`;
  abrirModal(html);
}
async function repPieza(bid,pieza){ const r=await api('/api/reporte_pieza',{batch_id:bid,pieza}); alert(r.ok?'Reporte guardado en:\n'+r.ruta:'Error: '+r.error); }
async function repLote(bid){ const r=await api('/api/reporte_lote',{batch_id:bid}); alert(r.ok?'Reporte del lote guardado en:\n'+r.ruta:'Error: '+r.error); }
async function exportarExcel(bid){ const r=await api('/api/exportar_excel',{batch_id:bid}); alert(r.ok?'Excel guardado en:\n'+r.ruta+'\n\nPuedes subirlo a tu Drive desde ahí.':'Error: '+r.error); }

// --- Corregir: eliminar un lote completo o una pieza suelta ---
async function borrarLote(bid, nombre){
  if(!confirm('¿Eliminar el lote "'+nombre+'" y TODAS sus piezas?\n\nEsto no se puede deshacer y se quitará del dashboard.')) return;
  await api('/api/borrar_batch', {batch_id:bid});
  vistaActual = null;
  const det = document.getElementById('detLote'); if(det) det.innerHTML = '';
  ir(vistaNombre); // refresca dashboard o historial
}
async function borrarPieza(rid, bid){
  if(!confirm('¿Eliminar esta pieza del lote?\n\nSe recalcularán los porcentajes del lote. Esto no se puede deshacer.')) return;
  await api('/api/borrar_pieza', {resultado_id:rid});
  batchCache = {}; // la caché del dashboard quedó desactualizada
  cerrarModal();
  verLote(bid); // vuelve a cargar el lote ya corregido
}

// ============ VISTA: LIMITES / ESTANDAR ============
async function vistaLimites(){
  const perfiles = (await api('/api/perfiles')).perfiles;
  const ops = perfiles.map(p=>`<option>${esc(p.nombre)}</option>`).join('');
  const tabla = (titulo, icono, prueba, canales) => `
    <div class="card"><h3>${ic(icono)} ${titulo}</h3>
      <p class="mini" style="margin-bottom:8px">Fase 1: la desviación estándar debe estar dentro de su rango [mín, máx]. Fase 2: el promedio debe estar dentro de su rango [mín, máx]. Deja un campo vacío para no evaluar ese criterio.</p>
      <table><tr><th>Canal</th><th>Desv. mín</th><th>Desv. máx</th><th>Media mín</th><th>Media máx</th></tr>
      ${canales.map(c=>`<tr><td>${esc(c)}</td>
        ${['desv_min','desv_max','media_min','media_max'].map(k=>`<td><input class="f est-in" data-prueba="${prueba}" data-canal="${esc(c)}" data-campo="${k}" type="number" step="0.01" style="width:110px;padding:6px 8px"></td>`).join('')}
      </tr>`).join('')}</table></div>`;
  document.getElementById('vistas').innerHTML = `
    <div class="card"><div class="fila">
      <div><label class="f">Perfil guardado</label><select class="f" id="perfilSel" style="width:240px">${ops||'<option value="">Ninguno todavía</option>'}</select></div>
      <button class="btn-out" onclick="cargarPerfil()">Cargar</button>
      <button class="btn-out" onclick="borrarPerfil()">Eliminar</button>
    </div></div>
    ${tabla('Prueba óptica','sun','Optico',CANALES_OPT)}
    ${tabla('Prueba eléctrica','zap','Electrico',CANALES_ELE)}
    <div class="card"><div class="fila">
      <div style="flex:1"><label class="f">Guardar como perfil (nombre)</label><input class="f" id="nombrePerfil" placeholder="Ej. Producto A v1"></div>
      <button class="btn-sm" onclick="guardarPerfil()">${ic('save')} Guardar perfil</button>
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
// Revisa que ningun rango quede invertido (minimo mayor que maximo).
function validarLimites(L){
  const errs=[];
  for(const p in L) for(const c in L[p]){
    const d=L[p][c]||{}; const pr = p==='Optico'?'Óptica':'Eléctrica';
    if(d.desv_min!=null && d.desv_max!=null && d.desv_min>d.desv_max)
      errs.push(`${pr} · ${c}: desviación mín (${d.desv_min}) es MAYOR que la máx (${d.desv_max}).`);
    if(d.media_min!=null && d.media_max!=null && d.media_min>d.media_max)
      errs.push(`${pr} · ${c}: media mín (${d.media_min}) es MAYOR que la máx (${d.media_max}).`);
  }
  return errs;
}
async function guardarPerfil(){
  const nombre = document.getElementById('nombrePerfil').value.trim();
  if(!nombre){ alert('Escribe un nombre para el perfil.'); return; }
  const L = leerEstandar();
  const errs = validarLimites(L);
  if(errs.length){
    alert('No se guardó. Revisa estos rangos: el mínimo no puede ser mayor que el máximo.\n\n• '+errs.join('\n• '));
    return;
  }
  await api('/api/guardar_perfil', {nombre, limites:L});
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
// Pensado en 3 capas: (1) Resumen para el responsable/jefe, (2) Alertas para el
// operador (qué repetir), (3) Análisis para el ingeniero (gráfica con alcance).
let dash = {batches:[], conteo:{}, alertas:[]};
let gScope='todo', gLote='', gPieza='';   // alcance de la gráfica de análisis
let batchCache = {};
async function cargarBatch(bid){ if(!batchCache[bid]) batchCache[bid]=await api('/api/batch/'+bid); return batchCache[bid]; }

async function vistaDashboard(){
  batchCache = {}; gLote=''; gPieza='';
  dash.batches = (await api('/api/batches')).batches;
  dash.conteo  = (await api('/api/fallas_canal')).conteo;
  dash.alertas = (await api('/api/alertas')).alertas;

  const total = dash.batches.reduce((s,b)=>s+b.total,0);
  const pas   = dash.batches.reduce((s,b)=>s+b.pasaron,0);
  const noPaso      = dash.alertas.filter(a=>a.veredicto==='NO PASO').length;
  const incompletos = dash.alertas.filter(a=>a.veredicto==='INCOMPLETO').length;
  const rechazados  = dash.alertas.filter(a=>a.veredicto==='RECHAZADO').length;
  const tasa = total?Math.round(100*pas/total):0;

  const top = Object.entries(dash.conteo).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const maxF = top.length?top[0][1]:1;
  const barras = top.map(([c,n])=>`<div style="display:flex;align-items:center;gap:10px;margin:7px 0">
     <span class="mini" style="width:150px">${esc(c)}</span>
     <div class="barra" style="width:${Math.round(88*n/maxF)}%"></div>
     <span class="mini" style="font-weight:600;color:var(--tinta-2)">${n}</span></div>`).join('')
     || '<p class="mini">Sin fallas registradas todavía.</p>';

  const loteCards = dash.batches.map(b=>{
    const t = b.total?Math.round(100*b.pasaron/b.total):0;
    const cls = t>=95?'ok':t>=80?'warn':'no';
    return `<div class="lote-card ${cls}" onclick="verLote(${b.id})" title="Abrir el lote ${esc(b.nombre)}">
      <div class="lc-nom">${esc(b.nombre)}</div><div class="lc-pct">${t}%</div>
      <div class="lc-bar"><i style="width:${t}%"></i></div>
      <div class="lc-mini">${b.pasaron} de ${b.total} · ${esc((b.fecha||'').slice(0,10))}</div></div>`;
  }).join('') || '<p class="mini">Aún no hay lotes evaluados.</p>';

  document.getElementById('vistas').innerHTML = `
    <div class="grid-kpi">
      <div class="kpi"><div class="lbl">Lotes</div><div class="val">${dash.batches.length}</div></div>
      <div class="kpi"><div class="lbl">Piezas evaluadas</div><div class="val">${total}</div></div>
      <div class="kpi ok"><div class="lbl">Pasaron</div><div class="val">${pas}</div></div>
      <div class="kpi no"><div class="lbl">No pasaron</div><div class="val">${noPaso}</div></div>
      <div class="kpi"><div class="lbl">Incompletos</div><div class="val" style="color:var(--warn-tx)">${incompletos}</div></div>
      ${rechazados?`<div class="kpi"><div class="lbl">Rechazados</div><div class="val" style="color:var(--neutro-tx)">${rechazados}</div></div>`:''}
      <div class="kpi az"><div class="lbl">Aprobación global</div><div class="val">${tasa}%</div></div>
    </div>
    ${alertasHTML()}
    <div class="card" id="analisis"></div>
    <div class="card"><h3>${ic('chart')} Canales con más fallas <span class="mini" style="font-weight:400">(Pareto, todos los lotes)</span></h3>${barras}</div>
    <div class="card"><h3>Lotes</h3>
      <p class="mini" style="margin-bottom:12px">Verde ≥95%, ámbar ≥80%, rojo &lt;80% de aprobación. Abre un lote para ver el mapa, eliminar una pieza mal hecha o el lote completo.</p>
      <div class="mapa-lotes">${loteCards}</div></div>
    <div id="detLote"></div>`;
  renderAnalisis();
}

// --- Capa 2: Alertas (para el operador) ---
function alertasHTML(){
  if(!dash.alertas.length)
    return `<div class="card" style="border-color:#BFE3CF;background:var(--ok-bg)">
      <h3 style="color:var(--ok-tx)">${ic('bell')} Alertas: desechables a repetir</h3>
      <p style="color:var(--ok-tx);font-weight:600">${ic('check')} No hay desechables pendientes de repetir. Todo el histórico pasó.</p></div>`;
  const filas = dash.alertas.slice().reverse().map(a=>{
    let motivo;
    if(a.veredicto==='RECHAZADO') motivo='Archivo inválido: vuelve a exportar el JSON del equipo.';
    else if(!a.canales.length) motivo='Incompleto: falta límite para comparar.';
    else motivo = a.canales.slice(0,4).map(c=>`${esc(c.prueba)} ${esc(c.canal)}${c.fase?` (Fase ${c.fase})`:''}`).join(', ')
                + (a.canales.length>4?` y ${a.canales.length-4} más`:'');
    return `<tr class="row-link" onclick="abrirAlerta(${a.batch_id},${jsAttr(a.pieza)})">
      <td><b>${esc(a.pieza)}</b></td><td>${esc(a.lote)}</td>
      <td>${pillVer(a.veredicto,'PASÓ','NO PASÓ','INCOMPLETO')}</td>
      <td class="mini">${motivo}</td>
      <td class="mini" style="color:var(--no-tx);font-weight:600">${ic('redo')} Repetir en el siguiente desechable</td></tr>`;
  }).join('');
  return `<div class="card" style="border-color:#F1C4C4">
    <h3 style="color:var(--no-tx)">${ic('bell')} Alertas: desechables a repetir <span class="mini" style="font-weight:400">(${dash.alertas.length})</span></h3>
    <p class="mini" style="margin-bottom:10px">Estos desechables no pasaron. La recomendación es repetir la prueba en el siguiente desechable. Clic en una fila para ver el detalle o corregirla.</p>
    <div class="tabla-scroll"><table><tr><th>Pieza</th><th>Lote</th><th>Estado</th><th>Dónde falló</th><th>Acción</th></tr>${filas}</table></div></div>`;
}
async function abrirAlerta(bid, pieza){
  const r = await cargarBatch(bid);
  vistaActual = {batch_id:bid, resultados:r.resultados};
  verPieza(pieza);
}

// --- Capa 3: Análisis (para el ingeniero) — gráfica con selector de alcance ---
async function renderAnalisis(){
  const cont = document.getElementById('analisis'); if(!cont) return;
  const scopes = [['todo','Todo'],['dia','Por día'],['lote','Por lote'],['pieza','Un desechable']];
  const scopeSel = `<select class="f" style="width:auto" onchange="cambiarScope(this.value)">
    ${scopes.map(([v,t])=>`<option value="${v}" ${gScope===v?'selected':''}>${t}</option>`).join('')}</select>`;
  let extra = '';
  if(gScope==='lote'||gScope==='pieza'){
    const opL = `<option value="">Elige un lote</option>`+dash.batches.map(b=>
      `<option value="${b.id}" ${String(gLote)===String(b.id)?'selected':''}>${esc(b.nombre)}</option>`).join('');
    extra += `<select class="f" style="width:auto" onchange="selLote(this.value)">${opL}</select>`;
  }
  if(gScope==='pieza' && gLote){
    const b = await cargarBatch(gLote);
    const opP = `<option value="">Elige un desechable</option>`+b.resultados.map(r=>
      `<option value="${esc(r.no_pieza)}" ${String(gPieza)===String(r.no_pieza)?'selected':''}>Pieza ${esc(r.no_pieza)} · ${r.veredicto}</option>`).join('');
    extra += `<select class="f" style="width:auto" onchange="selPieza(this.value)">${opP}</select>`;
  }
  cont.innerHTML = `<h3>Análisis de calidad</h3>
    <div class="fila" style="margin-bottom:12px; align-items:center">
      <label class="mini">Ver la gráfica de:</label>${scopeSel}${extra}</div>
    <div id="graf"></div>`;
  pintarGrafica();
}
async function cambiarScope(v){ gScope=v; await renderAnalisis(); }
async function selLote(v){ gLote=v; gPieza=''; await renderAnalisis(); }
async function selPieza(v){ gPieza=v; pintarGrafica(); }

// SVG de línea con eje 0-100% y línea de meta (verde punteada).
function svgLinea(puntos, meta=95){
  const w=620,h=170,padL=34,padR=14,padT=14,padB=28, iw=w-padL-padR, ih=h-padT-padB;
  const X=i=> padL + (puntos.length<=1? iw/2 : i*iw/(puntos.length-1));
  const Y=p=> padT + ih*(1 - p/100);
  const grid=[0,50,100].map(v=>`<line x1="${padL}" y1="${Y(v)}" x2="${w-padR}" y2="${Y(v)}" stroke="#EEF1F4"/>
    <text x="${padL-6}" y="${Y(v)+3}" text-anchor="end" font-size="9" fill="#98A2B3">${v}%</text>`).join('');
  const metaL=`<line x1="${padL}" y1="${Y(meta)}" x2="${w-padR}" y2="${Y(meta)}" stroke="#12A15A" stroke-dasharray="4 3" stroke-width="1.2"/>
    <text x="${w-padR}" y="${Y(meta)-4}" text-anchor="end" font-size="9" fill="#086343">meta ${meta}%</text>`;
  const poly=puntos.map((pt,i)=>`${X(i).toFixed(0)},${Y(pt.pct).toFixed(0)}`).join(' ');
  const dots=puntos.map((pt,i)=>{const c=pt.pct>=meta?'#12A15A':pt.pct>=80?'#E9A23B':'#D03B3B';
    return `<circle cx="${X(i).toFixed(0)}" cy="${Y(pt.pct).toFixed(0)}" r="4" fill="${c}" stroke="#fff" stroke-width="1.5"><title>${esc(pt.label)}: ${pt.pct}%</title></circle>`;}).join('');
  const paso=Math.max(1,Math.ceil(puntos.length/12));
  const labs=puntos.map((pt,i)=> (i%paso===0)?`<text x="${X(i).toFixed(0)}" y="${h-8}" text-anchor="middle" font-size="8" fill="#98A2B3">${esc(pt.label)}</text>`:'').join('');
  return `<svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto">${grid}${metaL}
    ${puntos.length?`<polyline points="${poly}" fill="none" stroke="#2A78D6" stroke-width="2"/>`:''}${dots}${labs}</svg>`;
}

async function pintarGrafica(){
  const cont=document.getElementById('graf'); if(!cont) return;
  if(gScope==='todo'){
    const pts=dash.batches.slice().reverse().map(b=>({label:b.nombre, pct:b.total?Math.round(100*b.pasaron/b.total):0}));
    cont.innerHTML = pts.length? svgLinea(pts)+`<p class="mini">Cada punto es un lote, del más antiguo al más reciente. Verde = pasó la meta, ámbar/rojo = por debajo.</p>` : '<p class="mini">Aún no hay lotes.</p>';
  } else if(gScope==='dia'){
    const m={};
    dash.batches.forEach(b=>{const d=(b.fecha||'').slice(0,10); if(!d)return; m[d]=m[d]||{t:0,p:0}; m[d].t+=b.total; m[d].p+=b.pasaron;});
    const pts=Object.keys(m).sort().map(d=>({label:d.slice(5), pct:m[d].t?Math.round(100*m[d].p/m[d].t):0}));
    cont.innerHTML = pts.length? svgLinea(pts)+`<p class="mini">Cada punto es un día (aprobación de todos los lotes de ese día).</p>` : '<p class="mini">Aún no hay datos por día.</p>';
  } else if(gScope==='lote'){
    if(!gLote){ cont.innerHTML='<p class="mini">Elige un lote en el menú de arriba.</p>'; return; }
    const b=await cargarBatch(gLote);
    if(!b.batch){ cont.innerHTML='<p class="mini">Ese lote ya no existe.</p>'; return; }
    cont.innerHTML = paretoLoteHTML(b);
  } else if(gScope==='pieza'){
    if(!gLote||!gPieza){ cont.innerHTML='<p class="mini">Elige un lote y un desechable en el menú de arriba.</p>'; return; }
    const b=await cargarBatch(gLote);
    const x=(b.resultados||[]).find(r=>String(r.no_pieza)===String(gPieza));
    cont.innerHTML = x? bandasPiezaHTML(x) : '<p class="mini">No se encontró ese desechable.</p>';
  }
}

// Pareto de canales que fallaron dentro de UN lote.
function paretoLoteHTML(b){
  const c={};
  (b.resultados||[]).forEach(r=>{ for(const p in r.detalle) for(const f of r.detalle[p]){
    if(f.resultado==='FALLA'){ const k=(p==='Optico'?'Óptica':'Eléctrica')+' · '+f.canal; c[k]=(c[k]||0)+1; } } });
  const top=Object.entries(c).sort((a,b)=>b[1]-a[1]);
  const cab=`<p class="mini" style="margin-bottom:8px">Lote <b>${esc(b.batch.nombre)}</b>: ${b.batch.pasaron} de ${b.batch.total} pasaron.</p>`;
  if(!top.length) return cab+`<p class="mini" style="color:var(--ok-tx);font-weight:600">${ic('check')} Ningún canal falló en este lote.</p>`;
  const max=top[0][1];
  return cab+top.map(([k,n])=>`<div style="display:flex;align-items:center;gap:10px;margin:7px 0">
    <span class="mini" style="width:150px">${esc(k)}</span>
    <div class="barra" style="width:${Math.round(88*n/max)}%"></div>
    <span class="mini" style="font-weight:600;color:var(--tinta-2)">${n}</span></div>`).join('');
}

// Bandas de límite de UN desechable: la media de cada canal dentro de su rango [mín,máx].
function bandasPiezaHTML(x){
  if(x.veredicto==='RECHAZADO') return `<p class="mini">Este desechable fue rechazado (archivo inválido); no hay medidas que graficar.</p>`;
  let filas='';
  for(const p in x.detalle){
    filas += `<div class="mini" style="font-weight:600;color:var(--tinta);margin:14px 0 5px">${p==='Optico'?'Prueba óptica':'Prueba eléctrica'}</div>`;
    for(const f of x.detalle[p]){
      const e=f.estandar||{}, lo=e.media_min, hi=e.media_max, val=f.media;
      let track;
      if(lo!=null && hi!=null && hi>lo){
        let pos=(val-lo)/(hi-lo); const dentro=pos>=0&&pos<=1; pos=Math.max(0,Math.min(1,pos));
        const col=dentro?'#12A15A':'#D03B3B';
        track=`<div class="banda-track"><div class="banda-ok"></div>
          <div class="banda-dot" style="left:${(pos*100).toFixed(1)}%;background:${col}"></div></div>
          <span class="mini" style="width:150px;text-align:right">${fmt(val)} <span style="color:#B9C0CA">(${fmt(lo)} a ${fmt(hi)})</span></span>`;
      } else {
        track=`<div class="banda-track banda-vacia"></div><span class="mini" style="width:150px;text-align:right;color:#B9C0CA">${fmt(val)} · sin límite</span>`;
      }
      filas += `<div class="banda-row"><span class="mini" style="width:70px">${esc(f.canal)}</span>${track}</div>`;
    }
  }
  return `<p class="mini" style="margin-bottom:2px">Desechable <b>${esc(x.no_pieza)}</b>: la media de cada canal dentro de su banda de límite. Punto verde centrado = con margen; pegado al borde o rojo = cerca de fallar o fuera.</p>${filas}`;
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
    <div class="card"><input class="f" id="buscar" placeholder="Buscar lote u operador…" style="margin-bottom:12px" onkeyup="filtrarHist()">
      <table id="tblHist"><tr><th>Lote</th><th>Fecha</th><th>Operador</th><th>Total</th><th>Pasaron</th><th>Fallaron</th><th>% Aprob.</th></tr>${filas}</table></div>
    <div id="detLote"></div>`;
}
function filtrarHist(){ const q=document.getElementById('buscar').value.toLowerCase(); document.querySelectorAll('#tblHist tr').forEach((tr,i)=>{if(i===0)return;tr.style.display=tr.textContent.toLowerCase().includes(q)?'':'none';}); }
async function verLote(bid){
  const r = await api('/api/batch/'+bid); const b=r.batch;
  vistaActual = {batch_id:bid, resultados:r.resultados};
  const total=b.total||0;
  document.getElementById('detLote').innerHTML = `
    <div class="grid-kpi">
      <div class="kpi"><div class="lbl">Piezas</div><div class="val">${b.total}</div></div>
      <div class="kpi ok"><div class="lbl">Pasaron</div><div class="val">${b.pasaron}</div></div>
      <div class="kpi no"><div class="lbl">No pasaron</div><div class="val">${b.fallaron}</div></div>
      <div class="kpi az"><div class="lbl">Aprobación</div><div class="val">${total?Math.round(100*b.pasaron/total):0}%</div></div></div>
    <h3 style="color:var(--tinta);font-weight:650;letter-spacing:-.01em;margin-bottom:10px">Detalle del lote ${esc(b.nombre)}</h3>
    ${mapaHTML(r.resultados)}
    ${problemasHTML(r.resultados)}
    <div class="card">
      <div class="fila" style="justify-content:space-between; align-items:center">
        <button class="btn-out" onclick="toggleTodas(this)">Ver la lista completa (${total})</button>
        <div class="fila">
          <button class="btn-out" onclick="repLote(${bid})">${ic('doc')} Reporte del lote (PDF)</button>
          <button class="btn-out" onclick="exportarExcel(${bid})">${ic('sheet')} Excel de verificación</button>
          <button class="btn-danger" onclick="borrarLote(${bid},${jsAttr(b.nombre)})">${ic('trash')} Eliminar lote</button>
        </div>
      </div>
      <div id="tablaTodas" class="oculto" data-n="${total}" style="margin-top:12px">${tablaCompletaHTML(r.resultados)}</div>
    </div>`;
  document.getElementById('detLote').scrollIntoView({behavior:'smooth'});
}
