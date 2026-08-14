# RETOMAR — handoff do render-agroshow

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Escrito em 14/08/2026, no fim da sessão.

Abra este arquivo primeiro, depois `ESTADO.md`. Aqui está só o que a próxima
sessão precisa para continuar sem reler a conversa.

---

## O veredito do Natan, e é ele que manda o próximo passo

Ele olhou o primeiro quadro renderizado (portal em Cycles, 2760×1380) e disse:

> **"não corrija pois esta longe de um render de qualidade"**

Isso foi em resposta a mim consertando um detalhe da geometria do portal. A
leitura correta: **o que separa a cena de um render de qualidade não é
geometria — é luz, material e vegetação.** Parar de lapidar polígono e atacar
essas três. Nesta ordem, que é a ordem do salto visual:

1. **HDRI de golden hour** no lugar do céu chapado + sol alinhado a ele.
   `construir_ceu()` hoje é uma cor lisa. É o maior salto por menos trabalho.
2. **Materiais PBR** calibrados pelas provas do footage
   (`docs/MATERIAIS-referencia.md`): brita, telha, lona, terra. Grama vem de
   biblioteca CC0 calibrada pela cor medida — não existe close de grama no
   acervo.
3. **Vegetação e povoamento.** O mapa tem Bosque (6 rótulos), Mata Nativa (2) e
   15 Taludes; hoje tudo é grama chapada.

Fontes de asset autorizadas, verba zero: Poly Haven, ambientCG e o material
gratuito da **Blender Foundation / Blender Studio**. Decisão dele: os arquivos
vão **dentro do repositório**, em `assets/`, com `assets/MANIFESTO.md` listando
nome, licença e URL de cada um.

---

## O número que decide o Plano A vs Plano B

Medido nesta máquina, não estimado:

| grandeza | valor |
|---|---|
| um quadro, 2760×1380, Cycles 128 samples, OptiX na RTX 4060 | **31 s** |
| o filme inteiro, 4.635 quadros | **≈ 39 h** |

Isso é com a cena ainda crua. Com textura, vegetação e gente, sobe. Vale
recronometrar depois do passo 2 antes de prometer prazo.

---

## Como rodar

O Python do projeto é o venv em `.venv` (386 MB, criado com uv, fora do git):

```bash
.venv/Scripts/python.exe scripts/auditar_mapa.py
.venv/Scripts/python.exe scripts/extrair_vias.py --min-comprimento 35 --dpi 300
.venv/Scripts/python.exe scripts/classificar_estandes.py
.venv/Scripts/python.exe scripts/planos.py --conferir
.venv/Scripts/python.exe scripts/print_mapa.py --roteiro
```

A cena roda pelo Blender instalado, **sem `--factory-startup`** (ele derruba os
addons e o Cycles some):

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python scripts/build_scene.py -- --out out/cena.blend
```

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background out/cena.blend --render-output "E:\I.A Edit\render-expovizinhos\out\quadro_" --render-frame 1
```

**Disco:** o `E:` chegou a **0 GB livres** nesta sessão e travaria o render.
Hoje tem ~48 GB. Uma sequência de 4.635 PNG em 2760×1380 não cabe nisso —
mandar a saída de render para o **F:** (299 GB livres).

---

## O que foi feito em 14/08

**Integração.** O branch `claude/render-structure-research-on4ogj` entrou por
merge. Ele traz a decupagem em 22 planos com conferidor de velocidade, e a
avaliação foi que a mudança faz sentido: o percurso antigo corria a 9,0 m/s.
O `ESTADO.md` juntou as duas narrativas sem perder nada.

**O extrator descartava um terço do mapa.** Só aceitava rótulo de uma lista
branca escrita à mão — 50 dos 118 nomes caíam em silêncio. Entre eles a
**Fazendinha**, a Área de Show, os Expositores Externos e a Exposição de
Máquinas: exatamente os lugares que o projeto tratava como "sem posição na
planta". `scripts/auditar_mapa.py` lê todos.

**A camada vermelha do PDF (`#ff3131`, 36 spans) é o roteiro do cliente**
desenhado por cima da planta técnica — a mesma ordem do áudio, já posicionada.

**As 22 âncoras viraram `planta`.** Nenhuma estimada. A Fazendinha está em
(−164,4 · −18,6) m; decisão dele: vale o mapa, não a descrição do áudio.

**Altura de câmera passou a seguir o ambiente** (ordem dele): ~2 m dentro de
pavilhão, 4–15 m aberto, 40–50 m só num plano de conjunto do rodeio — que é o
P21. Treze planos desceram; o mais alto ia a 72 m.

**Estruturas modeladas** em `scripts/estruturas.py`: portal, palco, dois
camarotes, pavilhões de duas águas e as vias. Nível de bloco, sem textura.

**Cycles gravado na cena** com a configuração que ele ditou, e a GPU marcada
nas preferências.

---

## Armadilhas que já custaram uma rodada cada — não repetir

1. **O enum de motores não lista o Cycles.** Ele é addon; não aparece em
   `render.bl_rna.properties["engine"].enum_items` nem quando está ligado e
   funcionando. O teste honesto é **atribuir e conferir**.
2. **`read_factory_settings()` derrubaba os addons da sessão** — por isso
   `--factory-startup` faz o gerador abortar dizendo que a build não tem
   Cycles, o que é falso.
3. **`cycles.device = "GPU"` sozinho não basta.** Sem marcar a placa nas
   preferências, o render vai para a CPU sem reclamar.
4. **Agrupar rótulo por bloco do PDF não funciona** — o PDF quebra bloco onde
   quer. O que separa "Café Colonial" de "Cozinha Didática", que são dois
   lugares, é o deslocamento paralelo entre as linhas.
5. **As linhas de rua vivem no cinza 230–252**, quase o branco do fundo.
   Cortando em 215 elas somem inteiras.
6. **A via interna encosta no estande colorido** e o contorno funde os dois.
   Cortar por saturação antes resolve — traço técnico é cinza puro.
7. **Mexer no `alvo` de um plano sem mexer no `alvo_fim`** faz o sobrevoo
   varrer da posição real até a antiga. P16 chegou a 21,2 m/s. Rodar sempre
   `planos.py --conferir` depois.
8. **Comparar cor de estande com o quadradinho da legenda não fecha:** a
   legenda é pontilhado fino e o estande é hachurado diagonal — densidades
   diferentes para a mesma tinta.

---

## O que está aberto

| # | pendência | com quem |
|---|---|---|
| 1 | **Luz, material e vegetação** — o veredito dele | próxima sessão |
| 2 | Escala 0,5611 m/pt nunca conferida em campo. Tentei pelas 282 cotas do mapa: **inconclusivo** (q1 0,357 / q3 0,557) | cliente |
| 3 | Alturas dos patamares (0 → 3,5 → 7 → 10 m) seguem estimadas. Falta um voo lateral rasante | cliente |
| 4 | Medidas das estruturas — todas estimadas contra a pessoa de ~1,70 m do quadro `1 (4)` 00:00:02 | cliente |
| 5 | Traçado das vias: 42 lidos do bitmap, `conferido_pelo_natan: false`. Print em `docs/conferencia-tracado.jpg` | Natan |
| 6 | 37 estandes com categoria ambígua (mesma tinta, densidades diferentes) | cliente |
| 7 | Títulos, letreiros e logos — passo 3 do fluxo dele. Logo: **usar o JPEG achado ou o nome simples**, sem esperar vetor | próxima sessão |
| 8 | Interiores de pavilhão não existem; por isso nenhum plano entra a ~2 m | próxima sessão |

---

## Os arquivos que importam

| arquivo | o que é |
|---|---|
| `ESTADO.md` | o estado completo do projeto |
| `docs/LOCAIS.md` | os 21 lugares do roteiro, com a ficha de conteúdo tirada dos áudios |
| `docs/PLANOS.md` | a decupagem, a régua de altura e as âncoras |
| `docs/MATERIAIS-referencia.md` | a triagem dos 137 GB: que quadro serve para cada material |
| `data/locais.json` | 142 locais com coordenada em metros |
| `data/planos.json` | os 22 planos |
| `data/vias.json` | 50 traçados, 6 de perímetro e 36 internos |
| `data/estandes.json` | 134 estandes com categoria por cor |
| `scripts/estruturas.py` | portal, palco, camarote, pavilhão, via |
| `docs/conferencia-roteiro.jpg` | print dos 21 lugares, para conferência |
| `docs/conferencia-tracado.jpg` | print das vias traçadas |
