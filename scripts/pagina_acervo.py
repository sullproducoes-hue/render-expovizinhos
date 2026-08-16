#!/usr/bin/env python3
"""
Monta a pagina de triagem do acervo: out/acervo/ACERVO.html

    .venv/Scripts/python.exe scripts/pagina_acervo.py

Ela existe por causa de uma frase dele, 15/08/2026:

    "eu atualizei os arquivos de uma forma que eu possa avaliar e comentar
     e saber depois onde esta as que eu selecionei"

Tres requisitos, e a pagina se organiza em torno deles:

  AVALIAR   -- marca de quatro estados (sim / talvez / nao / sem marca), com
               teclado, e pre-triagem por medida para o melhor vir primeiro
  COMENTAR  -- texto livre por quadro, salvo junto da marca
  SABER ONDE ESTA -- cada quadro carrega o caminho ABSOLUTO em disco, o video
               de origem e o timecode. A exportacao sai com os tres.

COMO A SELECAO SOBREVIVE (o ponto mais delicado, e a escolha e conservadora):

  1. localStorage, gravado a cada clique. Funciona offline e sem servidor.
  2. botao "Exportar" que baixa um JSON -- e o unico arquivo que sai da maquina
     do navegador para o disco, e e o que o `colher_selecao.py` le depois.
  3. contador vermelho de "marcas sem exportar" e aviso ao fechar a aba.
  4. botao "Importar" para recarregar um JSON exportado, em outra maquina ou
     depois de limpar o navegador.

Nao ha servidor, nao ha internet e nao ha dependencia de rede. Se o navegador
bloquear o localStorage (acontece em file:// em algumas configuracoes), a
pagina avisa em vermelho no topo e o caminho passa a ser so' o botao Exportar.
"""

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

CSS = r"""
:root{color-scheme:dark;
  --bg:#121212;--card:#1b1b1b;--linha:#2d2d2d;--txt:#e9e9e9;--fraco:#8d8d8d;
  --sim:#3ddc84;--talvez:#ffc94a;--nao:#ff6b6b;--azul:#68b6ff}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--txt);margin:0;
  font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--azul)}
#topo{position:sticky;top:0;z-index:40;background:#161616;
  border-bottom:1px solid var(--linha);padding:10px 16px}
#topo h1{font-size:17px;margin:0 0 6px;display:inline-block}
#topo h1 small{color:var(--fraco);font-weight:400;font-size:13px;margin-left:10px}
.barra{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin-top:6px}
select,input[type=text],button{background:#242424;color:var(--txt);
  border:1px solid #3a3a3a;border-radius:6px;padding:5px 9px;font:inherit}
button{cursor:pointer}
button:hover{background:#303030}
button.acao{background:#1d3a52;border-color:#2b5b80}
button.acao:hover{background:#28506f}
label.chk{display:inline-flex;align-items:center;gap:5px;color:#c3c3c3;
  background:#1f1f1f;border:1px solid #333;border-radius:6px;padding:4px 9px;cursor:pointer}
#aviso{background:#5a1d1d;border:1px solid #a33;padding:8px 14px;display:none}
#nota{background:#3a2a12;border-bottom:1px solid #6b4d1e;padding:9px 16px;
  font-size:12.5px;line-height:1.5;color:#f0dfc0}
#nota code{background:#00000040;padding:0 4px;border-radius:3px}
#placar{margin-left:auto;font-size:13px;color:#bdbdbd;white-space:nowrap}
#placar b{color:var(--sim)}
#placar .pend{color:#ff8a8a;font-weight:700}
#corpo{display:flex;align-items:flex-start}
#lado{width:262px;flex:0 0 262px;position:sticky;top:96px;max-height:calc(100vh - 106px);
  overflow:auto;padding:12px 6px 40px 14px;border-right:1px solid var(--linha)}
#lado h3{font-size:11px;letter-spacing:.9px;color:#7b7b7b;margin:16px 0 5px;text-transform:uppercase}
.sec{display:block;width:100%;text-align:left;background:none;border:0;color:#cfcfcf;
  padding:4px 8px;border-radius:6px;cursor:pointer;font-size:13px;line-height:1.35}
.sec:hover{background:#222}
.sec.on{background:#26456080;color:#fff;font-weight:600}
.sec .n{float:right;color:#767676;font-size:11px;padding-top:2px}
.sec.dif{color:#ffcf5c}
#area{flex:1;padding:14px 18px 120px;min-width:0}
#cab{margin-bottom:10px}
#cab h2{margin:0;font-size:19px}
#cab p{margin:4px 0 0;color:#a0a0a0;font-size:13px;max-width:940px}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:13px}
.cel{background:var(--card);border:1px solid var(--linha);border-radius:9px;overflow:hidden;
  display:flex;flex-direction:column}
.cel.m1{border-color:var(--sim);box-shadow:0 0 0 1px var(--sim) inset}
.cel.m2{border-color:var(--talvez)}
.cel.m3{border-color:var(--nao);opacity:.6}
/* SEM object-fit:cover e SEM aspect-ratio fixo: 2.116 quadros do acervo sao
   VERTICAIS (o drone gravou em pe), e cortar o quadro na miniatura esconde
   justamente o que ele precisa julgar. Grade irregular e o preco. */
.cel .foto{position:relative;cursor:zoom-in;background:#000}
.cel .foto img{width:100%;height:auto;display:block}
.cel.pe .foto img{max-height:520px;width:auto;margin:0 auto}
.bad{position:absolute;top:5px;left:5px;background:#000b;border-radius:4px;
  padding:1px 6px;font-size:11px;font-weight:700}
.bad.dir{left:auto;right:5px;font-weight:600}
.bad.dv{top:auto;bottom:5px;left:5px;background:#7a1f1fdd;color:#ffd7d7;font-size:10px}
.t-bom{color:var(--sim)}.t-parecido{color:var(--talvez)}.t-fraco{color:var(--nao)}
.cel .info{padding:6px 9px;font-size:11.5px;color:#b6b6b6;line-height:1.35;
  word-break:break-all;flex:1}
.cel .info .lin1{color:#e2e2e2;font-weight:600;font-size:12px}
.cel .info .mot{color:#ff9d9d;font-style:italic}
.cel .info .cam{color:#6f6f6f;font-size:10.5px;margin-top:3px;cursor:copy}
.marcas{display:flex;gap:0;border-top:1px solid var(--linha)}
.marcas button{flex:1;border:0;border-radius:0;background:#1f1f1f;padding:6px 0;
  font-size:11.5px;font-weight:700;color:#8f8f8f;border-right:1px solid var(--linha)}
.marcas button:last-child{border-right:0}
.marcas button.on1{background:var(--sim);color:#062}
.marcas button.on2{background:var(--talvez);color:#4a3400}
.marcas button.on3{background:var(--nao);color:#4a0000}
.cel textarea{width:100%;border:0;border-top:1px solid var(--linha);background:#181818;
  color:#ddd;font:12px/1.4 inherit;padding:6px 9px;resize:vertical;min-height:30px}
.cel textarea.tem{background:#1d2418;border-top-color:#3a5a30}
#mais{display:block;margin:20px auto;padding:9px 22px}
#lupa{position:fixed;inset:0;background:#000e;z-index:90;display:none;
  flex-direction:column;padding:10px}
#lupa img{flex:1;min-height:0;object-fit:contain;width:100%}
#lupa .meta{color:#ddd;font-size:13px;padding:8px 4px 0;display:flex;gap:16px;
  flex-wrap:wrap;align-items:center}
#lupa .meta .cam{color:#9a9a9a;font-size:11.5px;word-break:break-all}
#lupa .marcas{border:0;max-width:420px}
#lupa textarea{width:100%;max-width:900px;background:#181818;color:#eee;border:1px solid #333;
  border-radius:6px;padding:6px 9px;font:13px inherit;margin-top:6px}
.dica{color:#6f6f6f;font-size:11.5px}
.vazio{color:#8a8a8a;padding:40px 0;text-align:center}
"""

JS = r"""
const D = window.ACERVO;
const CHAVE = 'acervo-agroshow-2026';
const ROTULO = {1:'SIM', 2:'TALVEZ', 3:'NAO'};
let marcas = {}, pendentes = 0, semStorage = false;
let secao = {tipo:'local', id:D.locais[0] ? D.locais[0].plano : null};
let mostrando = 0, listaAtual = [], LOTE = 180;

/* ------------------------------------------------------------ persistencia */
function carregar(){
  try{
    const t = localStorage.getItem(CHAVE);
    if(t) marcas = JSON.parse(t);
  }catch(e){
    semStorage = true;
    const a = document.getElementById('aviso');
    a.style.display='block';
    a.textContent = 'ATENCAO: este navegador bloqueou o armazenamento local nesta pagina. '
      + 'As marcas ficam so na memoria — clique em "Exportar selecao" ANTES de fechar a aba.';
  }
}
function gravar(){
  if(!semStorage){
    try{ localStorage.setItem(CHAVE, JSON.stringify(marcas)); }
    catch(e){ semStorage = true; }
  }
  pendentes++;
  placar();
}
/* O aviso ao fechar so' aparece quando ha risco REAL de perder trabalho:
   ou o localStorage esta bloqueado (as marcas vivem so' na memoria), ou ja
   ha muita coisa marcada sem nenhuma copia em arquivo. Avisar a cada recarga
   e' ruido -- com o localStorage funcionando, recarregar nao perde nada. */
window.addEventListener('beforeunload', e => {
  if(semStorage ? pendentes > 0 : pendentes >= 25){ e.preventDefault(); e.returnValue = ''; }
});

/* ------------------------------------------------------------------ ajudas */
const pasta = q => D.pastas[q.pi];
function caminho(q){ return pasta(q).dir + '\\quadros\\' + q.f; }
function urlOriginal(q){
  return 'file:///' + encodeURI(caminho(q).replace(/\\/g,'/'));
}
function marcaDe(id){ const m = marcas[id]; return m ? (m.m||0) : 0; }
function comentarioDe(id){ const m = marcas[id]; return m ? (m.c||'') : ''; }
function setMarca(id, v){
  const m = marcas[id] || {};
  m.m = (m.m === v) ? 0 : v;
  m.q = new Date().toISOString().slice(0,19);
  if(!m.m && !m.c) delete marcas[id]; else marcas[id] = m;
  gravar();
}
function setComentario(id, txt){
  const m = marcas[id] || {};
  m.c = txt;
  m.q = new Date().toISOString().slice(0,19);
  if(!m.m && !m.c) delete marcas[id]; else marcas[id] = m;
  gravar();
}
function placar(){
  let s=0,t=0,n=0,c=0;
  for(const k in marcas){
    const m = marcas[k];
    if(m.m===1)s++; else if(m.m===2)t++; else if(m.m===3)n++;
    if(m.c) c++;
  }
  document.getElementById('placar').innerHTML =
    `<b>${s}</b> sim · ${t} talvez · ${n} nao · ${c} comentarios`
    + (pendentes ? ` · <span class="pend">${pendentes} sem exportar</span>` : '');
}

/* ------------------------------------------------------------------ filtro */
function lerFiltros(){
  return {
    busca: document.getElementById('busca').value.trim().toLowerCase(),
    tier: document.getElementById('f-tier').value,
    per: document.getElementById('f-per').value,
    enq: document.getElementById('f-enq').value,
    ori: document.getElementById('f-or').value,
    dv: document.getElementById('f-dv').value,
    ordem: document.getElementById('f-ordem').value,
    soMarcados: document.getElementById('f-marcados').checked,
    soComent: document.getElementById('f-coment').checked,
  };
}
function aplicar(){
  const f = lerFiltros();
  let L = D.q.filter(q => {
    if(secao.tipo==='local'   && q.pl !== secao.id) return false;
    if(secao.tipo==='pasta'   && pasta(q).p !== secao.id) return false;
    if(secao.tipo==='nc'      && q.pl !== null) return false;
    if(secao.tipo==='marcados'&& !marcaDe(q.id)) return false;
    if(f.tier!=='todos' && q.t !== f.tier) return false;
    if(f.per !=='todos' && pasta(q).per !== f.per) return false;
    if(f.enq !=='todos' && q.eq !== f.enq) return false;
    if(f.ori !=='todos' && q.or !== f.ori) return false;
    if(f.dv === 'ok' && pasta(q).dv) return false;
    if(f.dv === 'dv' && !pasta(q).dv) return false;
    if(f.soMarcados && !marcaDe(q.id)) return false;
    if(f.soComent  && !comentarioDe(q.id)) return false;
    if(f.busca){
      const alvo = (pasta(q).p + ' ' + q.f + ' ' + (q.pl||'') + ' ' +
                    (pasta(q).v||'') + ' ' + comentarioDe(q.id)).toLowerCase();
      if(!alvo.includes(f.busca)) return false;
    }
    return true;
  });
  if(f.ordem==='nota')     L.sort((a,b)=> b.n - a.n);
  else if(f.ordem==='nitidez') L.sort((a,b)=> b.nit - a.nit);
  else L.sort((a,b)=> (a.pi - b.pi) || (a.q - b.q));
  listaAtual = L;
  mostrando = 0;
  document.getElementById('grade').innerHTML='';
  desenharCabecalho(L.length);
  mais();
}
function mais(){
  const g = document.getElementById('grade');
  const fim = Math.min(mostrando + LOTE, listaAtual.length);
  const frag = document.createDocumentFragment();
  for(let i=mostrando;i<fim;i++) frag.appendChild(celula(listaAtual[i], i));
  g.appendChild(frag);
  mostrando = fim;
  const b = document.getElementById('mais');
  b.style.display = mostrando < listaAtual.length ? 'block' : 'none';
  b.textContent = `mostrar mais ${Math.min(LOTE, listaAtual.length-mostrando)} `
                + `(faltam ${listaAtual.length-mostrando})`;
  if(!listaAtual.length)
    g.innerHTML = '<p class="vazio">Nenhum quadro com esses filtros. '
                + 'Tente soltar o filtro de etiqueta ou de periodo.</p>';
}

/* ----------------------------------------------------------------- celulas */
function celula(q, i){
  const p = pasta(q), m = marcaDe(q.id), c = comentarioDe(q.id);
  const d = document.createElement('div');
  d.className = 'cel' + (m ? ' m'+m : '') + (q.or==='pe' ? ' pe' : '');
  d.dataset.id = q.id;
  if(q.or==='pe') d.dataset.pe = '1';
  const cls = q.cl==='ancora' ? 'ANCORA' : (q.cl==='perto_da_ancora' ? 'perto da ancora' : '');
  d.innerHTML = `
    <div class="foto" data-i="${i}">
      <img loading="lazy" src="${q.th}" alt="">
      <span class="bad">${q.n.toFixed(0)}</span>
      <span class="bad dir t-${q.t}">${q.t}</span>
      ${p.dv ? '<span class="bad dv">SEM GPS PRÓPRIO</span>' : ''}
    </div>
    <div class="info">
      <div class="lin1">${p.p} · ${q.tc}${cls ? ' · <span style="color:#68b6ff">'+cls+'</span>' : ''}</div>
      <div>${q.f} · ${q.w}x${q.h} · ${p.per} · ${q.eq}${q.or==='pe'?' · EM PÉ':''}${p.h ? ' · '+p.h.slice(11,16) : ''}</div>
      ${q.mo ? '<div class="mot">'+q.mo+'</div>' : ''}
      ${q.sg && q.sg.length && !q.pl ? '<div style="color:#8aa">sugestao: '+q.sg.join(' ')+'</div>' : ''}
      <div class="cam" title="clique para copiar">${caminho(q)}</div>
    </div>
    <div class="marcas">
      <button data-v="1" class="${m===1?'on1':''}">SIM</button>
      <button data-v="2" class="${m===2?'on2':''}">TALVEZ</button>
      <button data-v="3" class="${m===3?'on3':''}">NAO</button>
    </div>
    <textarea class="${c?'tem':''}" placeholder="comentario...">${c.replace(/</g,'&lt;')}</textarea>`;
  d.querySelector('.foto').onclick = () => abrirLupa(i);
  d.querySelector('.cam').onclick = ev => {
    navigator.clipboard && navigator.clipboard.writeText(caminho(q));
    ev.target.style.color = '#3ddc84';
    setTimeout(()=>ev.target.style.color='', 700);
  };
  d.querySelectorAll('.marcas button').forEach(b => b.onclick = () => {
    setMarca(q.id, +b.dataset.v);
    repintar(d, q.id);
  });
  const ta = d.querySelector('textarea');
  ta.onchange = () => { setComentario(q.id, ta.value); ta.className = ta.value?'tem':''; };
  return d;
}
function repintar(d, id){
  const m = marcaDe(id);
  d.className = 'cel' + (m ? ' m'+m : '') + (d.dataset.pe ? ' pe' : '');
  d.querySelectorAll('.marcas button').forEach(b => {
    b.className = (+b.dataset.v === m) ? 'on'+m : '';
  });
}

/* -------------------------------------------------------------------- lupa */
let iLupa = -1;
function abrirLupa(i){
  iLupa = i;
  const q = listaAtual[i], p = pasta(q);
  const el = document.getElementById('lupa');
  el.style.display = 'flex';
  const img = el.querySelector('img');
  img.onerror = () => { img.onerror=null; img.src = q.th; };
  img.src = urlOriginal(q);
  el.querySelector('.tit').textContent = `${p.p} · ${q.tc} · ${q.f}`;
  el.querySelector('.dados').textContent =
    `nota ${q.n.toFixed(0)} · ${q.t} · ${q.w}x${q.h} · nitidez ${q.nit} · `
    + `luma ${q.lu} · desvio ${q.sd} · estouro ${q.es}% · ${p.per} · ${q.eq} (ceu ${q.ce}%)`
    + (q.pl ? ` · ${q.pl} (${q.cl})` : ' · sem local');
  el.querySelector('.cam').textContent = caminho(q);
  el.querySelector('.vid').textContent = p.v ? ('video: ' + p.v) : 'video original nao localizado';
  const ta = el.querySelector('textarea');
  ta.value = comentarioDe(q.id);
  ta.onchange = () => setComentario(q.id, ta.value);
  pintaLupa();
}
function pintaLupa(){
  const q = listaAtual[iLupa], m = marcaDe(q.id);
  document.querySelectorAll('#lupa .marcas button').forEach(b => {
    b.className = (+b.dataset.v === m) ? 'on'+m : '';
  });
  const cel = document.querySelector(`.cel[data-id="${CSS.escape(q.id)}"]`);
  if(cel) repintar(cel, q.id);
}
function fecharLupa(){ document.getElementById('lupa').style.display='none'; iLupa=-1; }
function andar(d){
  if(iLupa < 0) return;
  const n = iLupa + d;
  if(n < 0 || n >= listaAtual.length) return;
  if(n >= mostrando) mais();
  abrirLupa(n);
}
document.addEventListener('keydown', e => {
  if(e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
  if(iLupa < 0) return;
  if(e.key === 'Escape') fecharLupa();
  else if(e.key === 'ArrowRight') andar(1);
  else if(e.key === 'ArrowLeft') andar(-1);
  else if(e.key === 's' || e.key === 'S'){ setMarca(listaAtual[iLupa].id,1); pintaLupa(); }
  else if(e.key === 't' || e.key === 'T'){ setMarca(listaAtual[iLupa].id,2); pintaLupa(); }
  else if(e.key === 'n' || e.key === 'N'){ setMarca(listaAtual[iLupa].id,3); pintaLupa(); }
});

/* --------------------------------------------------------------- exportacao */
function baixar(nome, texto, tipo){
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([texto], {type: tipo}));
  a.download = nome;
  a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
}
function linhas(){
  const idx = {}; D.q.forEach(q => idx[q.id] = q);
  const out = [];
  for(const id in marcas){
    const q = idx[id]; if(!q) continue;
    const p = pasta(q);
    out.push({
      id, marca: ROTULO[marcas[id].m] || 'sem_marca',
      comentario: marcas[id].c || '',
      quando: marcas[id].q || '',
      arquivo: caminho(q),
      video: p.v || '', pasta: p.p, raiz: p.r,
      timecode: q.tc, segundos: q.q_s,
      plano: q.pl || '', classificacao: q.cl,
      sugestao: (q.sg||[]).join(' '),
      nota: q.n, etiqueta: q.t, motivo: q.mo || '',
      periodo: p.per, hora_do_voo: p.h || '',
      recinto: p.dv ? 'Dois Vizinhos por vizinhanca - esta pasta nao tem GPS proprio'
                    : 'Dois Vizinhos - GPS do drone, ver data/recinto-gps.json',
      largura: q.w, altura: q.h,
      nitidez: q.nit, luma: q.lu, desvio: q.sd, estouro: q.es,
    });
  }
  out.sort((a,b) => (a.plano||'zz').localeCompare(b.plano||'zz')
                 || a.pasta.localeCompare(b.pasta) || a.segundos - b.segundos);
  return out;
}
function exportarJSON(){
  const L = linhas();
  baixar('selecao-acervo-agroshow.json', JSON.stringify({
    _o_que_e: 'Selecao do Natan sobre o acervo de quadros da AGROSHOW. '
            + 'Leia com scripts/colher_selecao.py.',
    _gerado: new Date().toISOString(),
    _acervo: D.meta.gerado,
    _total_marcado: L.length,
    itens: L,
  }, null, 1), 'application/json');
  pendentes = 0; placar();
}
function exportarCSV(){
  const L = linhas();
  if(!L.length){ alert('Nada marcado ainda.'); return; }
  const cols = Object.keys(L[0]);
  const esc = v => '"' + String(v).replace(/"/g,'""') + '"';
  const txt = '﻿' + cols.join(';') + '\n'
            + L.map(r => cols.map(c => esc(r[c])).join(';')).join('\n');
  baixar('selecao-acervo-agroshow.csv', txt, 'text/csv');
  pendentes = 0; placar();
}
function copiarCaminhos(){
  const L = linhas().filter(r => r.marca === 'SIM');
  if(!L.length){ alert('Nenhum quadro marcado como SIM.'); return; }
  navigator.clipboard.writeText(L.map(r => r.arquivo).join('\n'));
  alert(L.length + ' caminhos copiados.');
}
function importar(ev){
  const f = ev.target.files[0]; if(!f) return;
  const r = new FileReader();
  r.onload = () => {
    try{
      const j = JSON.parse(r.result);
      let n = 0;
      (j.itens || []).forEach(it => {
        const v = {SIM:1, TALVEZ:2, NAO:3}[it.marca] || 0;
        if(v || it.comentario){ marcas[it.id] = {m:v, c:it.comentario||'', q:it.quando||''}; n++; }
      });
      gravar(); pendentes = 0; placar(); aplicar();
      alert(n + ' marcas importadas.');
    }catch(e){ alert('Nao consegui ler esse arquivo: ' + e); }
  };
  r.readAsText(f);
  ev.target.value = '';
}

/* ------------------------------------------------------------------ layout */
function desenharCabecalho(n){
  const c = document.getElementById('cab');
  let tit = '', sub = '';
  if(secao.tipo === 'local'){
    const L = D.locais.find(x => x.plano === secao.id);
    tit = `${L.plano} — ${L.local}` + (L.diferencial ? '   ★ diferencial' : '');
    sub = (L.cena_3d ? 'na cena 3D: ' + L.cena_3d + '. ' : '')
        + 'So entra aqui o quadro que caiu perto de uma escolha a mao de 15/08. '
        + 'O resto do mesmo voo esta em "nao classificados".'
        + (L.bloqueio ? '  BLOQUEIO: ' + L.bloqueio : '');
  } else if(secao.tipo === 'pasta'){
    const p = D.pastas.find(x => x.p === secao.id);
    tit = p.p;
    sub = `${p.n} quadros · ${p.per}${p.h ? ' · voo de ' + p.h : ''}`
        + (p.v ? ' · video: ' + p.v : ' · video original nao localizado')
        + (p.f && p.f.length ? ' · ' + p.f.length + ' folha(s) de contato' : '');
    if(p.dv) sub += '  · sem GPS próprio (export estabilizado). O recinto foi confirmado pelos voos '
                  + 'de 25 a 30/11/2025 são de OUTRO recinto (autódromo oval, silos de grão). '
                  + 'O catálogo da manhã usa voos desta faixa como âncora confirmada. '
                  + 'Ninguém decidiu ainda — ver docs/ACERVO.md.';
  } else if(secao.tipo === 'nc'){
    tit = 'Nao classificados';
    sub = 'Nenhum destes foi atribuido a um local. Isso e de proposito: '
        + 'nenhum quadro foi reconhecido por conteudo, e forcar um local errado '
        + 'custa mais caro que deixar sem. A "sugestao" diz quais locais aquele '
        + 'MESMO voo toca em algum instante — e pista, nao classificacao.';
  } else {
    tit = 'O que eu marquei';
    sub = 'Tudo que tem marca ou comentario, de qualquer secao. '
        + 'Exporte daqui antes de fechar a aba.';
  }
  c.innerHTML = `<h2>${tit}</h2><p>${sub}</p>
    <p class="dica">${n} quadros neste filtro · clique na foto para ver em tamanho real ·
    no visor: setas navegam, S/T/N marcam, Esc fecha</p>`;
}
function lado(){
  const el = document.getElementById('lado');
  const cnt = {}; D.q.forEach(q => { if(q.pl) cnt[q.pl] = (cnt[q.pl]||0)+1; });
  let h = '<h3>triagem</h3>';
  h += `<button class="sec" data-t="marcados">O que eu marquei<span class="n" id="n-marc"></span></button>`;
  h += '<h3>os 22 planos do roteiro</h3>';
  D.locais.forEach(L => {
    h += `<button class="sec${L.diferencial?' dif':''}" data-t="local" data-id="${L.plano}">`
       + `${L.plano} ${L.local}<span class="n">${cnt[L.plano]||0}</span></button>`;
  });
  const nc = D.q.filter(q => !q.pl).length;
  h += `<h3>sem local</h3><button class="sec" data-t="nc">Nao classificados<span class="n">${nc}</span></button>`;
  h += '<h3>por voo — dia</h3>';
  ['dia','fim de tarde','noite'].forEach((per,k) => {
    if(k) h += `<h3>por voo — ${per}</h3>`;
    D.pastas.filter(p => p.per === per).forEach(p => {
      h += `<button class="sec" data-t="pasta" data-id="${p.p}">${p.p}<span class="n">${p.n}</span></button>`;
    });
  });
  el.innerHTML = h;
  el.querySelectorAll('.sec').forEach(b => b.onclick = () => {
    secao = {tipo: b.dataset.t, id: b.dataset.id};
    el.querySelectorAll('.sec').forEach(x => x.classList.remove('on'));
    b.classList.add('on');
    aplicar();
  });
  el.querySelector('.sec').classList.add('on');
}

/* -------------------------------------------------------------------- inicio */
carregar();
lado();
placar();
['busca','f-tier','f-per','f-dv','f-or','f-enq','f-ordem','f-marcados','f-coment'].forEach(id => {
  const e = document.getElementById(id);
  e.addEventListener(e.tagName === 'INPUT' && e.type === 'text' ? 'input' : 'change', aplicar);
});
document.getElementById('b-json').onclick = exportarJSON;
document.getElementById('b-csv').onclick  = exportarCSV;
document.getElementById('b-cam').onclick  = copiarCaminhos;
document.getElementById('b-imp').onchange = importar;
document.getElementById('mais').onclick   = mais;
document.getElementById('lupa').onclick   = e => { if(e.target.id === 'lupa') fecharLupa(); };
document.getElementById('l-fecha').onclick = fecharLupa;
document.querySelectorAll('#lupa .marcas button').forEach(b => b.onclick = () => {
  setMarca(listaAtual[iLupa].id, +b.dataset.v); pintaLupa();
});
secao = {tipo:'local', id: D.locais[0].plano};
aplicar();
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", default="data/acervo-quadros.json")
    ap.add_argument("--saida", default="out/acervo")
    a = ap.parse_args()

    cat = json.loads((RAIZ / a.catalogo).read_text(encoding="utf-8"))
    saida = RAIZ / a.saida
    saida.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------- portao
    # Isto aborta a pagina, e existe porque JA falhou: duas pastas com nomes
    # diferentes cairam no mesmo slug e 4 quadros dividiram `id` e miniatura --
    # marcar um marcava o outro, e a carta mostrava a imagem do voo errado.
    # Silencioso, 4 em 9.980. Regra que so' existe como paragrafo e a mais fraca
    # das tres (delta 0029): esta e portao.
    from collections import Counter
    problemas = []
    ids = Counter(q["id"] for q in cat["quadros"])
    rep = [k for k, v in ids.items() if v > 1]
    if rep:
        problemas.append(f"{len(rep)} `id` repetidos, o primeiro e {rep[0]} -- "
                         f"a selecao dele marcaria dois quadros de uma vez")
    th = Counter(q["thumb"] for q in cat["quadros"])
    repth = [k for k, v in th.items() if v > 1]
    if repth:
        problemas.append(f"{len(repth)} miniaturas compartilhadas por quadros "
                         f"diferentes, a primeira e {repth[0]}")
    faltando = [q for q in cat["quadros"] if not (saida / q["thumb"]).exists()]
    if faltando:
        problemas.append(f"{len(faltando)} quadros sem miniatura em disco "
                         f"(rode acervo_quadros.py --varrer)")
    if problemas:
        print("A PAGINA NAO FOI GERADA -- o catalogo esta inconsistente:")
        for p in problemas:
            print("  * " + p)
        return 1

    # ------------------------------------------------- procedencia, ja resolvida
    # A duvida (D055) foi FECHADA em 15/08 pelo GPS do proprio drone -- ver
    # DECISOES.md D061 e scripts/provar_recinto.py. Das 71 pastas, 60 tem
    # coordenada gravada e todas caem entre 24 e 387 m do recinto; nenhuma cai
    # fora. As 11 restantes sao exports estabilizados que perderam o metadado.
    #
    # O selo continua existindo, mas mudou de significado: nao e' mais "pode ser
    # outra cidade", e' "esta pasta nao tem GPS proprio". Marcar a diferenca
    # entre medido e nao medido e' regra da casa e nao se apaga so porque a
    # resposta foi boa.
    prova = Path("data/recinto-gps.json")
    sem_gps = set()
    if prova.exists():
        doc_gps = json.loads(prova.read_text(encoding="utf-8"))
        sem_gps = {v["pasta"] for v in doc_gps["voos"] if "lat" not in v}

    def em_duvida(nome):
        return nome in sem_gps

    idx_pasta = {p["pasta"]: i for i, p in enumerate(cat["pastas"])}
    pastas = [{
        "p": p["pasta"], "r": p["raiz"], "dir": p["dir"],
        "v": p.get("video_arquivo"), "f": p.get("folhas_de_contato") or [],
        "per": p["periodo"], "h": p.get("hora_do_nome"), "n": p["n_quadros"],
        "dv": em_duvida(p["pasta"]),
    } for p in cat["pastas"]]
    n_duvida = sum(p["n_quadros"] for p, q in zip(cat["pastas"], pastas) if q["dv"])

    # Enquadramento aproximado, derivado de UMA medida: a fracao de pixel claro
    # no terco de cima do quadro. Nadir nao tem ceu nenhum; rasante tem muito.
    # E aproximacao declarada, nao reconhecimento de imagem -- ceu encoberto
    # sobre pista clara engana, e telhado branco a contraluz tambem.
    def enquadramento(ceu):
        if ceu is None:
            return "?"
        if ceu < 2:
            return "nadir"
        if ceu < 15:
            return "alto"
        if ceu < 40:
            return "obliquo"
        return "horizonte"

    quadros = []
    for q in cat["quadros"]:
        quadros.append({
            "ce": q.get("ceu"), "eq": enquadramento(q.get("ceu")),
            "or": "pe" if q["h"] > q["w"] else "deitado",
            "id": q["id"], "pi": idx_pasta[q["pasta"]],
            "f": Path(q["arquivo"]).name, "th": q["thumb"],
            "q": q["q"], "q_s": q["tc_s"], "tc": q["tc"],
            "w": q["w"], "h": q["h"],
            "n": q["nota"], "t": q["tier"], "mo": q.get("motivo_da_etiqueta"),
            "nit": q["nitidez"], "lu": q["luma"], "sd": q["std"], "es": q["estouro"],
            "pl": q.get("plano"), "cl": q.get("classificacao"),
            "sg": q.get("sugestao") or [],
        })

    dados = {
        "meta": {"gerado": cat["_procedencia"], "resumo": cat["_resumo"],
                 "criterio": cat["_criterio"], "raizes": cat["_raizes"]},
        "locais": cat["locais"],
        "pastas": pastas,
        "q": quadros,
    }
    js = "window.ACERVO = " + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + ";"
    (saida / "dados.js").write_text(js, encoding="utf-8")

    r = cat["_resumo"]
    html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Acervo de quadros — AGROSHOW 2026</title>
<style>{CSS}</style></head><body>

<div id="aviso"></div>

<div id="nota">
  <b>Procedência resolvida em 15/08 — é tudo Dois Vizinhos.</b>
  Os voos <code>DJI_2025112…</code> estavam marcados como possível "outro recinto".
  O GPS do próprio drone desmentiu: <b>60 das 71 pastas têm coordenada gravada e
  todas caem entre 24 m e 387 m</b> do recinto, num terreno de 808 × 454 m.
  <b>Nenhuma cai fora.</b> O "autódromo oval" está em
  <code>DJI_20251126155520_0054_D</code> (168 m) e os "silos de grão" em
  <code>DJI_20251129182345_0168_D</code> (336 m) — os dois com GPS confirmado.
  As {n_duvida} imagens ainda marcadas são de 11 exports estabilizados que
  perderam o metadado; mostram a mesma feira, no mesmo dia, do mesmo drone.
  Prova em <code>data/recinto-gps.json</code> · <code>scripts/provar_recinto.py</code>.
</div>

<div id="topo">
  <h1>Acervo de quadros — AGROSHOW 2026
    <small>{r['quadros']} quadros · {r['pastas']} voos · {r['bons']} bons ·
      {r['parecidos']} parecidos · {r['fracos']} fracos</small></h1>
  <div class="barra">
    <input type="text" id="busca" placeholder="buscar voo, arquivo, comentario..." size="26">
    <select id="f-tier">
      <option value="bom">só os bons</option>
      <option value="todos">todas as etiquetas</option>
      <option value="parecido">só os parecidos</option>
      <option value="fraco">só os fracos</option>
    </select>
    <select id="f-per">
      <option value="todos">dia e noite</option>
      <option value="dia">só dia</option>
      <option value="fim de tarde">só fim de tarde (17h-19h)</option>
      <option value="noite">só noite</option>
    </select>
    <select id="f-dv" title="GPS do drone: o recinto está confirmado; o filtro separa quem tem coordenada própria">
      <option value="todos">toda procedência</option>
      <option value="ok">só com GPS próprio</option>
      <option value="dv">só os sem GPS</option>
    </select>
    <select id="f-or" title="o filme é deitado; quadro em pé não serve de placa sem corte pesado">
      <option value="todos">deitado e em pé</option>
      <option value="deitado">só deitado</option>
      <option value="pe">só em pé</option>
    </select>
    <select id="f-enq" title="derivado da fração de céu no terço de cima — aproximação">
      <option value="todos">todo enquadramento</option>
      <option value="nadir">nadir (sem céu)</option>
      <option value="alto">aéreo alto</option>
      <option value="obliquo">oblíquo</option>
      <option value="horizonte">horizonte / rasante</option>
    </select>
    <select id="f-ordem">
      <option value="nota">melhor primeiro</option>
      <option value="cron">ordem do voo</option>
      <option value="nitidez">mais nítido primeiro</option>
    </select>
    <label class="chk"><input type="checkbox" id="f-marcados"> só marcados</label>
    <label class="chk"><input type="checkbox" id="f-coment"> só comentados</label>
    <button class="acao" id="b-json">Exportar seleção (JSON)</button>
    <button id="b-csv">CSV</button>
    <button id="b-cam">Copiar caminhos dos SIM</button>
    <label class="chk">Importar<input type="file" id="b-imp" accept=".json" style="display:none"></label>
    <span id="placar"></span>
  </div>
</div>

<div id="corpo">
  <div id="lado"></div>
  <div id="area">
    <div id="cab"></div>
    <div class="grade" id="grade"></div>
    <button id="mais" style="display:none"></button>
  </div>
</div>

<div id="lupa">
  <img alt="">
  <div class="meta">
    <b class="tit"></b>
    <span class="dados"></span>
    <div class="marcas">
      <button data-v="1">SIM (s)</button>
      <button data-v="2">TALVEZ (t)</button>
      <button data-v="3">NÃO (n)</button>
    </div>
    <button id="l-fecha">fechar (Esc)</button>
  </div>
  <div class="meta"><span class="cam"></span></div>
  <div class="meta"><span class="cam vid"></span></div>
  <textarea placeholder="comentário deste quadro..."></textarea>
</div>

<script src="dados.js"></script>
<script>{JS}</script>
</body></html>
"""
    alvo = saida / "ACERVO.html"
    alvo.write_text(html, encoding="utf-8")
    print(f"Gravado {alvo}  ({alvo.stat().st_size/1024:.0f} KB)")
    print(f"Gravado {saida / 'dados.js'}  ({(saida / 'dados.js').stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
