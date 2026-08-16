/**
 * Prova que a pagina de triagem faz o que promete -- em navegador de verdade,
 * carregada por file://, que e como ele vai abrir.
 *
 *   node scripts/provar_pagina_acervo.mjs
 *
 * O que ela testa, e cada um destes ja falhou em alguma pagina deste projeto:
 *
 *   1. a pagina carrega e a grade desenha carta
 *   2. localStorage FUNCIONA em file:// -- se nao funcionar, a selecao dele
 *      nao sobrevive a fechar a aba, e a pagina inteira perde o sentido
 *   3. marcar SIM grava, e a marca CONTINUA LA depois de recarregar
 *   4. comentario grava e sobrevive do mesmo jeito
 *   5. a exportacao monta o registro com CAMINHO ABSOLUTO, video e timecode
 *   6. o visor abre a imagem ORIGINAL do disco (nao a miniatura)
 *
 * Sai com codigo 1 no primeiro que falhar.
 */
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const require = createRequire(
  'file:///C:/Users/natan/AppData/Roaming/npm/node_modules/hyperframes/package.json');
const puppeteer = require('puppeteer-core');

const CHROME = 'C:/Users/natan/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';
import { fileURLToPath } from 'node:url';
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PAGINA = path.join(RAIZ, 'out', 'acervo', 'ACERVO.html');

let falhas = 0;
const ok = (nome, cond, extra = '') => {
  console.log(`${cond ? '  ok  ' : '  FALHOU '} ${nome}${extra ? '  -- ' + extra : ''}`);
  if (!cond) falhas++;
};

if (!fs.existsSync(PAGINA)) {
  console.error('Nao existe ' + PAGINA + ' -- rode scripts/pagina_acervo.py antes.');
  process.exit(1);
}

const b = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--allow-file-access-from-files', '--no-sandbox'],
});
const p = await b.newPage();
await p.setViewport({ width: 1680, height: 1000 });
const erros = [];
p.on('dialog', d => d.accept());   // o aviso de "sair sem exportar" trava a automacao
p.on('pageerror', e => erros.push(String(e)));
p.on('console', m => { if (m.type() === 'error') erros.push(m.text()); });

const url = pathToFileURL(PAGINA).href;
await p.goto(url, { waitUntil: 'load' });
await p.evaluate(() => new Promise(r => setTimeout(r, 900)));

ok('a pagina carrega sem erro de JS', erros.length === 0, erros.slice(0, 3).join(' | '));

const cartas = await p.$$eval('.cel', e => e.length);
ok('a grade desenhou carta', cartas > 0, cartas + ' cartas');

const bloqueado = await p.evaluate(() => document.getElementById('aviso').style.display === 'block');
ok('localStorage NAO esta bloqueado em file://', !bloqueado,
   bloqueado ? 'a pagina caiu no modo so-exportacao' : '');

// --- marcar SIM na primeira carta e comentar
const id = await p.$eval('.cel', e => e.dataset.id);
await p.click('.cel .marcas button[data-v="1"]');
await p.$eval('.cel textarea', e => {
  e.value = 'prova automatica 15/08';
  e.dispatchEvent(new Event('change'));
});
await p.evaluate(() => new Promise(r => setTimeout(r, 200)));

const gravado = await p.evaluate(() => localStorage.getItem('acervo-agroshow-2026'));
ok('a marca foi para o localStorage', !!gravado && gravado.includes('"m":1'));

// --- recarregar: e AQUI que a promessa dele se cumpre ou nao
await p.goto(url, { waitUntil: 'load' });
await p.evaluate(() => new Promise(r => setTimeout(r, 900)));
const sobreviveu = await p.evaluate(idAlvo => {
  const c = document.querySelector(`.cel[data-id="${CSS.escape(idAlvo)}"]`);
  if (!c) return { achou: false };
  return {
    achou: true,
    marcada: c.classList.contains('m1'),
    comentario: c.querySelector('textarea').value,
  };
}, id);
ok('a carta continua no lugar depois de recarregar', sobreviveu.achou);
ok('a marca SIM sobreviveu ao recarregar', sobreviveu.marcada === true);
ok('o comentario sobreviveu ao recarregar',
   sobreviveu.comentario === 'prova automatica 15/08', sobreviveu.comentario);

// --- o que a exportacao carrega
const linha = await p.evaluate(() => linhas()[0]);
ok('a exportacao traz o caminho ABSOLUTO do arquivo',
   !!linha && /^[A-Z]:\\/.test(linha.arquivo), linha && linha.arquivo);
ok('a exportacao traz o video de origem', !!linha && !!linha.video, linha && linha.video);
ok('a exportacao traz o timecode', !!linha && /^\d\d:\d\d:\d\d$/.test(linha.timecode),
   linha && linha.timecode);
ok('o arquivo apontado existe mesmo em disco',
   !!linha && fs.existsSync(linha.arquivo));

// --- o visor abre o original, nao a miniatura
await p.click('.cel .foto');
await p.evaluate(() => new Promise(r => setTimeout(r, 1400)));
const visor = await p.evaluate(() => {
  const i = document.querySelector('#lupa img');
  return { aberto: document.getElementById('lupa').style.display === 'flex',
           src: i.src, w: i.naturalWidth };
});
ok('o visor abre', visor.aberto);
ok('o visor carrega o JPG ORIGINAL do disco', visor.w > 1200,
   `${visor.w}px de largura natural`);

await p.evaluate(() => localStorage.removeItem('acervo-agroshow-2026'));
await p.goto(url, { waitUntil: 'load' });
await p.evaluate(() => new Promise(r => setTimeout(r, 1500)));
const png = path.join(RAIZ, 'out', 'acervo', '_prova-pagina.png');
await p.screenshot({ path: png });
console.log('\nRetrato da pagina em ' + png);

await b.close();
console.log(falhas ? `\n${falhas} teste(s) falharam.` : '\nTodos os testes passaram.');
process.exit(falhas ? 1 : 0);
