#!/usr/bin/env python3
"""Gera o AJUSTADOR: pagina local para o Natan corrigir e CRIAR peca a peca.

Pedido dele em 15/08, em tres partes:

1. *"tem como criar alguma coisa para eu manualmente ajustar a posicao no estilo
   dessa prova de rumo? por exemplo tem um pequeno detalhe no angulo do portal"*
2. *"quero poder alterar o tamanho tbm"*
3. *"quero adicionar blocos ali (de tendas e quadrada ou circulares ou poligonos
   irregulares), e uma aba pra eu falar o que penso sobre o bloco que crie por
   ex: area do estacionamento"*

Sai um HTML auto-contido em `out/ajustar/ajustar.html` -- a planta do cliente ao
fundo, cada peca arrastavel, giravel e redimensionavel, blocos novos de quatro
formas, e um campo de anotacao por peca. O JSON baixado vai para
`data/ajustes-manuais.json` e passa a mandar no gerador, acima de qualquer
medicao.

A imagem vai embutida em base64 para o HTML abrir com dois cliques, sem servidor
e sem caminho relativo que quebre quando ele mover a pasta.

Uso:
    .venv/Scripts/python.exe scripts/ajustar_posicoes.py
"""

import base64
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terreno

RAIZ = Path(__file__).resolve().parent.parent
PDF = RAIZ / "reference" / "Mapa_AGROSHOW26.pdf"
ZOOM = 2.0                       # 2880 x 1620: legivel e leve o bastante
SAIDA = RAIZ / "out" / "ajustar" / "ajustar.html"

# As pecas que valem ajuste fino: rotulo na planta -> (nome na cena, largura,
# profundidade, rumo). O rumo vem das constantes do `build_scene.py`, nao do
# footprint -- estas pecas sao construidas por `estruturas.py` e o rumo delas e'
# declarado, nao medido.
ESTRUTURAS = {
    "PORTAL": ("PortalCeleiro", 20.0, 8.0, 73.0),
    "PALCO": ("Palco de evento", 24.0, 12.0, 334.0),
    "CAMAROTES - LADO A": ("CAMAROTES - LADO A", 60.0, 8.0, None),
    "CAMAROTES - LADO B": ("CAMAROTES - LADO B", 60.0, 8.0, None),
}

ALTURA_PADRAO = {"pavilhao": 7.0, "estrutura": 4.0}


def coletar():
    """Peca a peca: rotulo, centro em metros, rumo, tamanho e altura."""
    fp = json.loads((RAIZ / "data" / "footprints.json").read_text(encoding="utf-8"))
    dados = terreno.carregar_mapa(RAIZ / terreno.MAPA_PADRAO)
    origem = dados["_origem"]

    pecas, vistos = [], set()

    for z in fp["itens"]:
        rot = str(z.get("rotulo", ""))
        e_pav = "PAVILHÃO" in rot.upper()
        e_est = rot in ESTRUTURAS
        if not (e_pav or e_est) or rot in vistos:
            continue
        vistos.add(rot)

        mx, my = terreno.para_mundo(z["x_pt"], z["y_pt"], origem)
        larg = z.get("largura_m") or 20.0
        prof = z.get("profundidade_m") or 10.0
        rumo = float(z.get("rumo_graus", 90.0))
        grupo = "pavilhao" if e_pav else "estrutura"
        if e_est:
            _, larg, prof, r_decl = ESTRUTURAS[rot]
            if r_decl is not None:
                rumo = r_decl
        pecas.append({
            "id": rot,
            # O NOME NA CENA nao e' o rotulo da planta. O rotulo "PORTAL" existe
            # tambem como zona estimada e como letreiro; sem dizer o alvo, o
            # gerador movia o homonimo errado -- 226 m de desvio no teste.
            "alvo": ESTRUTURAS[rot][0] if e_est else rot,
            "grupo": grupo, "forma": "retangulo",
            "x": round(mx, 2), "y": round(my, 2), "rumo": round(rumo, 1),
            "larg": round(float(larg), 2), "prof": round(float(prof), 2),
            "alt": ALTURA_PADRAO[grupo], "raio": 10.0, "pontos": [],
            "nota": "", "conf": z.get("confianca", "-"),
        })

    # O portal ja tem posicao conferida por ele, e ela MANDA. O arquivo guarda
    # `novo_m` / `antigo_m` -- ler `x_m` aqui deixava o portal no lugar velho e
    # com rumo generico, que foi como esta pagina saiu na primeira versao.
    corr = RAIZ / "data" / "correcao-posicao-1508.json"
    if corr.exists():
        p = (json.loads(corr.read_text(encoding="utf-8")).get("portal") or {})
        novo = p.get("novo_m")
        if novo:
            achou = next((q for q in pecas if q["id"] == "PORTAL"), None)
            if achou:
                achou["x"], achou["y"] = round(novo[0], 2), round(novo[1], 2)
                achou["conf"] = "posicao conferida pelo Natan"
    return pecas, origem


def main():
    import pymupdf

    pecas, origem = coletar()

    pix = pymupdf.open(PDF)[0].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR if pix.n == 3 else cv2.COLOR_RGBA2BGR)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if not ok:
        raise SystemExit("nao consegui codificar a planta")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")

    cfg = {
        "larguraPx": pix.w, "alturaPx": pix.h,
        "zoom": ZOOM, "escala": terreno.ESCALA,
        "origemPt": [origem[0], origem[1]],
        "pecas": pecas,
    }

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(MODELO.replace("__CFG__", json.dumps(cfg, ensure_ascii=False))
                     .replace("__IMG__", b64), encoding="utf-8")

    mb = SAIDA.stat().st_size / 1e6
    print(f"{len(pecas)} pecas ajustaveis  +  criacao de blocos novos")
    print(f"planta {pix.w}x{pix.h} embutida")
    print(f"gravado: {SAIDA}  ({mb:.1f} MB)")


MODELO = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Ajustar posicoes - AGROSHOW 2026</title>
<style>
  :root { --bg:#14161a; --painel:#1d2026; --linha:#2c313a; --texto:#e8eaed;
          --fraco:#9aa0aa; --verde:#3fa34d; --laranja:#e08a2e; --roxo:#8b5cf6; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--texto);
         font:14px/1.5 system-ui,Segoe UI,sans-serif; display:flex; height:100vh; }
  #tela { flex:1; position:relative; overflow:hidden; cursor:grab; }
  #tela.arrastando { cursor:grabbing; }
  #tela.desenhando { cursor:crosshair; }
  canvas { position:absolute; top:0; left:0; transform-origin:0 0; }
  aside { width:352px; background:var(--painel); border-left:1px solid var(--linha);
          display:flex; flex-direction:column; }
  .rolagem { flex:1; overflow-y:auto; padding:16px; }
  .rodape { padding:14px 16px; border-top:1px solid var(--linha); }
  h1 { font-size:15px; margin:0 0 4px; }
  p.dica { color:var(--fraco); font-size:12px; margin:0 0 12px; }
  .abas { display:flex; gap:4px; margin-bottom:12px; }
  .aba { flex:1; padding:7px; text-align:center; border-radius:6px;
         background:#2a2f38; cursor:pointer; font-size:12.5px; font-weight:600; }
  .aba.on { background:var(--verde); }
  .peca { border:1px solid var(--linha); border-radius:7px; padding:9px 10px;
          margin-bottom:7px; cursor:pointer; }
  .peca:hover { border-color:#3d4450; }
  .peca.sel { border-color:var(--verde); background:#1a2a1e; }
  .peca.novo { border-left:3px solid var(--roxo); }
  .peca .n { font-weight:600; font-size:12.5px; }
  .peca .v { color:var(--fraco); font-size:11.5px; font-variant-numeric:tabular-nums; }
  .campos { display:grid; grid-template-columns:auto 1fr; gap:6px 8px;
            align-items:center; margin-top:8px; }
  input, textarea, select { background:#0e1013; color:var(--texto);
          border:1px solid var(--linha); border-radius:5px; padding:5px 7px;
          width:100%; font:inherit; font-size:13px;
          font-variant-numeric:tabular-nums; }
  textarea { min-height:64px; resize:vertical; font-size:12.5px; }
  button { background:var(--verde); color:#fff; border:0; border-radius:7px;
           padding:11px; width:100%; font-weight:600; cursor:pointer;
           font-size:14px; }
  button.sec { background:#333a45; margin-top:7px; }
  button.rx { background:var(--roxo); }
  .formas { display:grid; grid-template-columns:1fr 1fr; gap:6px; }
  .formas button { padding:9px 6px; font-size:12.5px; background:#2a2f38; }
  .formas button:hover { background:#3a4150; }
  .mudou { color:var(--laranja); }
  .anot { color:#9fd8a8; font-size:11.5px; font-style:italic;
          margin-top:3px; display:block; }
  kbd { background:#0e1013; border:1px solid var(--linha); border-radius:4px;
        padding:1px 5px; font-size:11px; }
  .aviso { background:#3a2a12; border:1px solid #6b4a1a; border-radius:6px;
           padding:9px 10px; font-size:12px; margin-bottom:10px; }
</style></head><body>

<div id="tela"><canvas id="c"></canvas></div>

<aside>
  <div class="rolagem">
    <h1>Ajustar e criar</h1>
    <div class="abas">
      <div class="aba on" data-aba="pecas">Pecas</div>
      <div class="aba" data-aba="novo">Novo bloco</div>
      <div class="aba" data-aba="nota">Anotacao</div>
    </div>

    <div id="painel-pecas">
      <p class="dica">
        Arraste para <b>mover</b> &middot; <kbd>Shift</kbd>+arraste <b>gira</b>
        &middot; <kbd>Alt</kbd>+arraste <b>redimensiona</b><br>
        Setas 0,5 m &middot; <kbd>,</kbd> <kbd>.</kbd> giram &middot;
        <kbd>+</kbd> <kbd>&minus;</kbd> largura (com <kbd>Shift</kbd>, profundidade)
      </p>
      <p class="dica" style="border-left:3px solid var(--laranja); padding-left:9px">
        <span style="color:#5c8fd6">&mdash; &mdash;</span> tracejado = eixo
        comprido, a direcao do rumo.<br>
        <span style="color:var(--laranja)">&#9679;&mdash;</span> ponta laranja =
        o lado da profundidade, por onde fica a fachada.<br>
        O rumo gira o eixo comprido, <b>nao</b> a frente.
      </p>
      <div id="lista"></div>
    </div>

    <div id="painel-novo" style="display:none">
      <p class="dica">Escolha a forma e <b>clique no mapa</b> onde ela entra.</p>
      <div class="formas">
        <button data-f="retangulo">Quadrada</button>
        <button data-f="circulo">Circular</button>
        <button data-f="tenda">Tenda</button>
        <button data-f="poligono">Poligono</button>
      </div>
      <p class="dica" style="margin-top:10px">
        <b>Poligono irregular:</b> clique ponto a ponto e feche com
        <kbd>Enter</kbd> ou clicando no primeiro ponto. <kbd>Esc</kbd> cancela.
      </p>
      <div id="status-novo"></div>
    </div>

    <div id="painel-nota">
      <p class="dica">O que voce pensa sobre a peca selecionada. Vai junto no
        JSON e chega ao gerador como instrucao sua.</p>
      <div id="area-nota"></div>
    </div>
  </div>

  <div class="rodape">
    <button id="baixar">Baixar ajustes-manuais.json</button>
    <button id="zerar" class="sec">Desfazer tudo</button>
    <p class="dica" style="margin:9px 0 0">
      Salve em <code>data/ajustes-manuais.json</code>. O gerador obedece ele
      acima de qualquer medicao.
    </p>
  </div>
</aside>

<script>
const CFG = __CFG__;
const planta = new Image();
planta.src = "data:image/jpeg;base64,__IMG__";

const cv = document.getElementById("c"), ctx = cv.getContext("2d");
const tela = document.getElementById("tela");
cv.width = CFG.larguraPx; cv.height = CFG.alturaPx;

const orig = JSON.parse(JSON.stringify(CFG.pecas));
let pecas = JSON.parse(JSON.stringify(CFG.pecas));
let sel = null, vista = {x:0, y:0, z:0.42}, arrasta = null;
let modoNovo = null, rascunho = [], aba = "pecas", contador = 0;

const paraPx = (mx, my) => [
  (mx / CFG.escala + CFG.origemPt[0]) * CFG.zoom,
  (-my / CFG.escala + CFG.origemPt[1]) * CFG.zoom ];
const paraM = (px, py) => [
  (px / CFG.zoom - CFG.origemPt[0]) * CFG.escala,
  -(py / CFG.zoom - CFG.origemPt[1]) * CFG.escala ];
const pxPorM = CFG.zoom / CFG.escala;

/* contorno em pixel, conforme a forma */
function contorno(p) {
  const [cx, cy] = paraPx(p.x, p.y);
  if (p.forma === "circulo") {
    const r = p.raio * pxPorM, k = [];
    for (let i = 0; i < 40; i++) {
      const t = i / 40 * Math.PI * 2;
      k.push([cx + Math.cos(t) * r, cy + Math.sin(t) * r]);
    }
    return k;
  }
  if (p.forma === "poligono" && p.pontos.length > 2) {
    // os pontos do poligono sao ABSOLUTOS em metros; giram em torno do centro
    const a = (p.rumo - (p.rumo0 === undefined ? p.rumo : p.rumo0)) * Math.PI/180;
    const co = Math.cos(a), si = Math.sin(a);
    return p.pontos.map(([mx, my]) => {
      const dx = mx - p.x, dy = my - p.y;
      return paraPx(p.x + dx*co - dy*si, p.y + dx*si + dy*co);
    });
  }
  const a = p.rumo * Math.PI / 180;
  const ux = Math.sin(a), uy = -Math.cos(a), vx = -uy, vy = ux;
  const hl = p.larg * pxPorM / 2, hp = p.prof * pxPorM / 2;
  return [[cx+ux*hl+vx*hp, cy+uy*hl+vy*hp], [cx+ux*hl-vx*hp, cy+uy*hl-vy*hp],
          [cx-ux*hl-vx*hp, cy-uy*hl-vy*hp], [cx-ux*hl+vx*hp, cy-uy*hl+vy*hp]];
}

function mudou(p) {
  if (p.novo) return true;
  const o = orig.find(q => q.id === p.id);
  return o && (Math.abs(o.x-p.x)>0.01 || Math.abs(o.y-p.y)>0.01
               || Math.abs(o.rumo-p.rumo)>0.05 || Math.abs(o.larg-p.larg)>0.01
               || Math.abs(o.prof-p.prof)>0.01 || (p.nota||"") !== (o.nota||""));
}

function desenhar() {
  ctx.clearRect(0, 0, cv.width, cv.height);
  if (planta.complete) ctx.drawImage(planta, 0, 0);

  for (const p of pecas) {
    const k = contorno(p), s = p === sel;
    if (k.length < 3) continue;
    ctx.beginPath(); ctx.moveTo(k[0][0], k[0][1]);
    for (let i = 1; i < k.length; i++) ctx.lineTo(k[i][0], k[i][1]);
    ctx.closePath();
    ctx.fillStyle = s ? "rgba(63,163,77,.30)"
      : p.novo ? "rgba(139,92,246,.24)"
      : (mudou(p) ? "rgba(224,138,46,.22)" : "rgba(40,90,200,.13)");
    ctx.fill();
    ctx.strokeStyle = s ? "#3fa34d" : p.novo ? "#8b5cf6"
                    : (mudou(p) ? "#e08a2e" : "#2f5fbf");
    ctx.lineWidth = (s ? 3.5 : 2) / vista.z; ctx.stroke();

    if (p.forma === "tenda") {   // duas aguas: risco da cumeeira
      const a = p.rumo * Math.PI/180, [cx,cy] = paraPx(p.x,p.y);
      const ux = Math.sin(a), uy = -Math.cos(a), h = p.larg*pxPorM*.5;
      ctx.beginPath();
      ctx.moveTo(cx-ux*h, cy-uy*h); ctx.lineTo(cx+ux*h, cy+uy*h);
      ctx.strokeStyle = s ? "#3fa34d" : "#8b5cf6";
      ctx.lineWidth = 2.4/vista.z; ctx.stroke();
    }

    if (p.forma !== "circulo" && p.forma !== "poligono") {
      const [cx, cy] = paraPx(p.x, p.y);
      const a = p.rumo * Math.PI / 180;
      const ux = Math.sin(a), uy = -Math.cos(a);
      ctx.save();
      ctx.setLineDash([9/vista.z, 6/vista.z]);
      ctx.beginPath();
      ctx.moveTo(cx-ux*p.larg*pxPorM*.46, cy-uy*p.larg*pxPorM*.46);
      ctx.lineTo(cx+ux*p.larg*pxPorM*.46, cy+uy*p.larg*pxPorM*.46);
      ctx.strokeStyle = s ? "#3fa34d" : "#2f5fbf";
      ctx.lineWidth = (s ? 2.4 : 1.4)/vista.z; ctx.stroke();
      ctx.restore();
      const fx = -uy, fy = ux, alc = p.prof*pxPorM*.60;
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx+fx*alc, cy+fy*alc);
      ctx.strokeStyle = s ? "#e08a2e" : "#b0763a";
      ctx.lineWidth = (s ? 3.4 : 2)/vista.z; ctx.stroke();
      ctx.beginPath();
      ctx.arc(cx+fx*alc, cy+fy*alc, (s?6:4)/vista.z, 0, 7);
      ctx.fillStyle = s ? "#e08a2e" : "#b0763a"; ctx.fill();
    }

    if (p.nota) {   // marca quem tem anotacao, para achar no mapa
      const [cx, cy] = paraPx(p.x, p.y);
      ctx.beginPath(); ctx.arc(cx, cy, 7/vista.z, 0, 7);
      ctx.fillStyle = "#9fd8a8"; ctx.fill();
    }
  }

  if (rascunho.length) {          // poligono em construcao
    ctx.beginPath();
    rascunho.forEach(([mx,my], i) => {
      const [px,py] = paraPx(mx,my);
      i ? ctx.lineTo(px,py) : ctx.moveTo(px,py);
    });
    ctx.strokeStyle = "#8b5cf6"; ctx.lineWidth = 2.5/vista.z; ctx.stroke();
    rascunho.forEach(([mx,my]) => {
      const [px,py] = paraPx(mx,my);
      ctx.beginPath(); ctx.arc(px,py,5/vista.z,0,7);
      ctx.fillStyle = "#8b5cf6"; ctx.fill();
    });
  }
  cv.style.transform = `translate(${vista.x}px,${vista.y}px) scale(${vista.z})`;
}

function lista() {
  document.getElementById("lista").innerHTML = pecas.map((p, i) => {
    const o = orig.find(q => q.id === p.id);
    const partes = [];
    if (p.novo) partes.push(`<b>novo</b> &middot; ${p.forma}`);
    else {
      if (Math.abs(p.x-o.x)>0.01 || Math.abs(p.y-o.y)>0.01)
        partes.push(`movida ${(p.x-o.x).toFixed(1)}, ${(p.y-o.y).toFixed(1)} m`);
      if (Math.abs(p.rumo-o.rumo)>0.05)
        partes.push(`girada ${(p.rumo-o.rumo).toFixed(1)}&deg;`);
      if (Math.abs(p.larg-o.larg)>0.01 || Math.abs(p.prof-o.prof)>0.01)
        partes.push(`${p.larg.toFixed(1)} x ${p.prof.toFixed(1)} m`);
    }
    const d = partes.length
      ? `<span class="mudou">${partes.join(" &middot; ")}</span>`
      : `${p.x.toFixed(1)}, ${p.y.toFixed(1)} m &middot; ${p.rumo.toFixed(1)}&deg;
         &middot; ${p.larg.toFixed(1)}x${p.prof.toFixed(1)}`;
    const medidas = p.forma === "circulo"
      ? `<label>Raio (m)</label><input data-c="raio" value="${p.raio.toFixed(2)}">`
      : `<label>Largura</label><input data-c="larg" value="${p.larg.toFixed(2)}">
         <label>Profund.</label><input data-c="prof" value="${p.prof.toFixed(2)}">`;
    return `<div class="peca ${p===sel?'sel':''} ${p.novo?'novo':''}" data-i="${i}">
      <div class="n">${p.id}</div><div class="v">${d}</div>
      ${p.nota ? `<span class="anot">&ldquo;${p.nota.slice(0,70)}&rdquo;</span>` : ""}
      ${p===sel ? `<div class="campos">
        <label>X (m)</label><input data-c="x" value="${p.x.toFixed(2)}">
        <label>Y (m)</label><input data-c="y" value="${p.y.toFixed(2)}">
        <label>Rumo</label><input data-c="rumo" value="${p.rumo.toFixed(1)}">
        ${medidas}
        <label>Altura</label><input data-c="alt" value="${(p.alt||3.2).toFixed(2)}">
      </div>
      ${p.novo ? `<button class="sec apagar" data-i="${i}">Apagar este bloco</button>` : ""}`
      : ""}</div>`;
  }).join("");

  document.querySelectorAll(".peca").forEach(el => {
    el.onclick = e => {
      if (e.target.tagName === "INPUT" || e.target.classList.contains("apagar")) return;
      sel = pecas[+el.dataset.i]; lista(); notaUI(); desenhar();
    };
  });
  document.querySelectorAll("input[data-c]").forEach(inp => {
    inp.onchange = () => {
      const v = parseFloat(inp.value.replace(",", "."));
      if (!isNaN(v) && sel) { sel[inp.dataset.c] = v; lista(); desenhar(); }
    };
  });
  document.querySelectorAll(".apagar").forEach(b => {
    b.onclick = () => {
      pecas.splice(+b.dataset.i, 1); sel = null; lista(); notaUI(); desenhar();
    };
  });
}

function notaUI() {
  const el = document.getElementById("area-nota");
  if (!sel) { el.innerHTML = `<p class="dica">Selecione uma peca no mapa ou na
    aba <b>Pecas</b>.</p>`; return; }
  el.innerHTML = `<div class="aviso">${sel.id}</div>
    <textarea id="txt-nota" placeholder="ex: area do estacionamento, chao de
saibro, sem cobertura">${sel.nota || ""}</textarea>
    <p class="dica" style="margin-top:8px">Escreva o que a peca e' e como deve
    parecer. Isso viaja no JSON e chega ao gerador.</p>`;
  document.getElementById("txt-nota").oninput = e => {
    sel.nota = e.target.value; lista(); desenhar();
  };
}

function dentro(p, px, py) {
  const k = contorno(p); let d = false;
  for (let i = 0, j = k.length-1; i < k.length; j = i++)
    if ((k[i][1] > py) !== (k[j][1] > py) &&
        px < (k[j][0]-k[i][0]) * (py-k[i][1]) / (k[j][1]-k[i][1]) + k[i][0]) d = !d;
  return d;
}
const naTela = e => {
  const r = cv.getBoundingClientRect();
  return [(e.clientX - r.left) / vista.z, (e.clientY - r.top) / vista.z];
};

function criar(forma, mx, my, pontos) {
  contador++;
  const nomes = {retangulo:"Bloco", circulo:"Circulo", tenda:"Tenda",
                 poligono:"Area"};
  const p = { id: `${nomes[forma]} ${contador}`, alvo: `NOVO_${forma}_${contador}`,
    grupo:"novo", forma, novo:true, x:+mx.toFixed(2), y:+my.toFixed(2),
    rumo:90, larg: forma==="tenda"?10:20, prof: forma==="tenda"?10:20,
    alt: forma==="tenda"?4.0:3.2, raio:12, pontos: pontos||[], nota:"" };
  if (pontos && pontos.length > 2) {
    const xs = pontos.map(q=>q[0]), ys = pontos.map(q=>q[1]);
    p.x = +((Math.min(...xs)+Math.max(...xs))/2).toFixed(2);
    p.y = +((Math.min(...ys)+Math.max(...ys))/2).toFixed(2);
    p.larg = +(Math.max(...xs)-Math.min(...xs)).toFixed(2);
    p.prof = +(Math.max(...ys)-Math.min(...ys)).toFixed(2);
    p.rumo0 = 90;
  }
  pecas.push(p); sel = p;
  modoNovo = null; rascunho = []; tela.classList.remove("desenhando");
  document.getElementById("status-novo").innerHTML = "";
  trocarAba("nota");    // ele acabou de criar: a pergunta seguinte e' o que e'
  lista(); notaUI(); desenhar();
}

tela.onmousedown = e => {
  const [px, py] = naTela(e);
  const [mx, my] = paraM(px, py);

  if (modoNovo === "poligono") {
    if (rascunho.length > 2) {
      const [fx, fy] = paraPx(rascunho[0][0], rascunho[0][1]);
      if (Math.hypot(px-fx, py-fy) < 12/vista.z) { criar("poligono", 0, 0, rascunho); return; }
    }
    rascunho.push([+mx.toFixed(2), +my.toFixed(2)]);
    document.getElementById("status-novo").innerHTML =
      `<p class="dica">${rascunho.length} pontos &middot; <kbd>Enter</kbd> fecha</p>`;
    desenhar(); return;
  }
  if (modoNovo) { criar(modoNovo, mx, my); return; }

  const achou = [...pecas].reverse().find(p => dentro(p, px, py));
  if (achou) {
    sel = achou;
    const [cx, cy] = paraPx(achou.x, achou.y);
    const tipo = e.altKey ? "medir" : (e.shiftKey ? "girar" : "mover");
    arrasta = { tipo, px, py, x0: achou.x, y0: achou.y, r0: achou.rumo,
                l0: achou.larg, p0: achou.prof, ra0: achou.raio,
                a0: Math.atan2(py - cy, px - cx) };
    lista(); notaUI();
  } else {
    arrasta = { tipo:"vista", cx:e.clientX, cy:e.clientY, vx:vista.x, vy:vista.y };
    tela.classList.add("arrastando");
  }
  desenhar();
};

window.onmousemove = e => {
  if (!arrasta) return;
  if (arrasta.tipo === "vista") {
    vista.x = arrasta.vx + (e.clientX - arrasta.cx);
    vista.y = arrasta.vy + (e.clientY - arrasta.cy);
  } else {
    const [px, py] = naTela(e);
    if (arrasta.tipo === "mover") {
      const [mx, my] = paraM(px, py), [ox, oy] = paraM(arrasta.px, arrasta.py);
      const dx = mx - ox, dy = my - oy;
      sel.x = +(arrasta.x0 + dx).toFixed(2);
      sel.y = +(arrasta.y0 + dy).toFixed(2);
      if (sel.pontos && sel.pontos.length)   // poligono anda junto
        sel.pontos = sel.pontos.map(([a,b]) => [+(a+dx).toFixed(2), +(b+dy).toFixed(2)]);
      arrasta.px = px; arrasta.py = py;
      arrasta.x0 = sel.x; arrasta.y0 = sel.y;
    } else if (arrasta.tipo === "medir") {
      // o arrasto e' lido NO EIXO DA PECA, nao no da tela: assim "para fora"
      // cresce a largura mesmo com a peca girada a 71 graus
      const a = sel.rumo * Math.PI / 180;
      const ux = Math.sin(a), uy = -Math.cos(a);
      const dx = (px - arrasta.px) / pxPorM, dy = (py - arrasta.py) / pxPorM;
      if (sel.forma === "circulo") {
        sel.raio = +Math.max(1, arrasta.ra0 + Math.hypot(dx, dy)).toFixed(2);
      } else {
        sel.larg = +Math.max(1, arrasta.l0 + (dx*ux + dy*uy) * 2).toFixed(2);
        sel.prof = +Math.max(1, arrasta.p0 + (dx*-uy + dy*ux) * 2).toFixed(2);
      }
    } else {
      const [cx, cy] = paraPx(sel.x, sel.y);
      const d = Math.atan2(py - cy, px - cx) - arrasta.a0;
      sel.rumo = +(((arrasta.r0 + d*180/Math.PI) % 360 + 360) % 360).toFixed(1);
    }
    lista();
  }
  desenhar();
};
window.onmouseup = () => { arrasta = null; tela.classList.remove("arrastando"); };

tela.onwheel = e => {
  e.preventDefault();
  const f = e.deltaY < 0 ? 1.12 : 1/1.12;
  const r = cv.getBoundingClientRect();
  vista.x -= (e.clientX - r.left) * (f - 1);
  vista.y -= (e.clientY - r.top) * (f - 1);
  vista.z *= f; desenhar();
};

window.onkeydown = e => {
  if (e.key === "Escape") {
    modoNovo = null; rascunho = []; tela.classList.remove("desenhando");
    document.getElementById("status-novo").innerHTML = ""; desenhar(); return;
  }
  if (e.key === "Enter" && rascunho.length > 2) { criar("poligono",0,0,rascunho); return; }
  if (!sel || e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  const passo = e.shiftKey ? 0.1 : 0.5;
  const dim = sel.forma === "circulo" ? "raio" : (e.shiftKey ? "prof" : "larg");
  const t = { ArrowLeft:["x",-passo], ArrowRight:["x",passo],
              ArrowUp:["y",passo], ArrowDown:["y",-passo],
              ",":["rumo",-passo], ".":["rumo",passo],
              "+":[dim,0.5], "=":[dim,0.5], "-":[dim,-0.5] }[e.key];
  if (!t) return;
  e.preventDefault();
  const piso = ["larg","prof","raio"].includes(t[0]) ? 1 : -1e9;
  sel[t[0]] = +Math.max(piso, sel[t[0]] + t[1]).toFixed(2);
  lista(); desenhar();
};

function trocarAba(nome) {
  aba = nome;
  document.querySelectorAll(".aba").forEach(a =>
    a.classList.toggle("on", a.dataset.aba === nome));
  document.getElementById("painel-pecas").style.display =
    nome === "pecas" ? "" : "none";
  document.getElementById("painel-novo").style.display =
    nome === "novo" ? "" : "none";
  document.getElementById("painel-nota").style.display =
    nome === "nota" ? "" : "none";
}
document.querySelectorAll(".aba").forEach(a =>
  a.onclick = () => trocarAba(a.dataset.aba));
document.querySelectorAll(".formas button").forEach(b => b.onclick = () => {
  modoNovo = b.dataset.f; rascunho = [];
  tela.classList.add("desenhando");
  document.getElementById("status-novo").innerHTML =
    `<p class="dica" style="color:#8b5cf6">Clique no mapa para por a
     <b>${b.textContent.toLowerCase()}</b>. <kbd>Esc</kbd> cancela.</p>`;
});

document.getElementById("baixar").onclick = () => {
  const mudadas = {}, novos = [];
  for (const p of pecas) {
    if (p.novo) {
      novos.push({ nome:p.id, objeto_na_cena:p.alvo, forma:p.forma,
        x_m:p.x, y_m:p.y, rumo_graus:p.rumo, altura_m:p.alt,
        largura_m:p.larg, profundidade_m:p.prof,
        raio_m: p.forma==="circulo" ? p.raio : undefined,
        pontos_m: p.forma==="poligono" ? p.pontos : undefined,
        nota_do_natan: p.nota || "" });
      continue;
    }
    if (!mudou(p)) continue;
    const o = orig.find(q => q.id === p.id);
    mudadas[p.id] = { objeto_na_cena:p.alvo, x_m:p.x, y_m:p.y,
      rumo_graus:p.rumo, largura_m:p.larg, profundidade_m:p.prof,
      altura_m:p.alt, nota_do_natan:p.nota || "",
      antes:{ x_m:o.x, y_m:o.y, rumo_graus:o.rumo,
              largura_m:o.larg, profundidade_m:o.prof } };
  }
  if (!Object.keys(mudadas).length && !novos.length) {
    alert("Nada mudou ainda."); return;
  }
  const doc = {
    o_que_e: "Ajuste manual do Natan, feito no ajustador visual. MANDA ACIMA " +
             "de footprints.json e de qualquer medicao.",
    autoridade: "ele",
    unidade: "metros no mundo da cena; rumo em azimute de prancha",
    pecas: mudadas, blocos_novos: novos
  };
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(doc, null, 2)],
                                        {type:"application/json"}));
  a.download = "ajustes-manuais.json"; a.click();
};
document.getElementById("zerar").onclick = () => {
  if (!confirm("Desfazer todos os ajustes e apagar os blocos novos?")) return;
  pecas = JSON.parse(JSON.stringify(orig)); sel = null; contador = 0;
  lista(); notaUI(); desenhar();
};

planta.onload = () => {
  vista.x = (tela.clientWidth - cv.width * vista.z) / 2;
  vista.y = (tela.clientHeight - cv.height * vista.z) / 2;
  trocarAba("pecas"); lista(); notaUI(); desenhar();
};
</script></body></html>
"""


if __name__ == "__main__":
    main()
