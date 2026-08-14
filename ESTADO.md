# ESTADO DO PROJETO — leia isto primeiro

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Atualizado em 14/08/2026.

Este arquivo existe para retomar o trabalho em outra sessão sem perder contexto.
Leia daqui e siga para os documentos citados.

---

## O caminho ativo: o fluxo de 5 passos do Natan

Decidido por ele em 14/08/2026, e é isto que manda:

1. **Posições de todos os locais** do mapa (`Mapa_AGROSHOW26`), sem faltar
   nenhum, com todos os nomes — **incluindo as estradas**, que entram no
   Blender. Dúvida de leitura ou posição vira **pergunta com print** do trecho
   do mapa, respondida por ele.
2. **Modelagem e texturas.**
3. **Títulos e letreiros** do que o mapa descreve. Logo procurado na internet:
   **usa o JPEG achado ou o nome simples** — não esperar vetor.
4. **Projeto pronto para ele renderizar.** A cena sai salva com a configuração
   dele já marcada; **quem exporta é ele, no Blender dele**.
5. **Plano A** (o que ele acha mais viável): os quadros aprovados viram entrada
   de **IA geradora de vídeo** com prompt ultra-realista por local.
   **Plano B**: se o render local convencer, renderizar o trajeto completo aqui
   com as animações — pessoas, gado, montaria, laçada, salão do leiloeiro.

**Regra permanente:** a descrição dos áudios (`docs/brief-audios.md`) é a régua
do que vai dentro de cada ambiente — conteúdo, posição e detalhe. Dúvida sobre
o que ele quis dizer: **perguntar**, com print.

### Configuração de render ditada por ele (Cycles)

GPU habilitada nas preferências · max samples **128** · noise threshold **0,1**
habilitado · denoise habilitado, prefilter **Fast**, quality **Balanced**,
**Use GPU** · **Fast GI Approximation** habilitado.

A cena já sai com tudo isso gravado. Máquina: **RTX 4060, 8 GB**.
Verba de asset: **zero** — só CC0 e gratuito (Poly Haven, ambientCG e o
material gratuito da **Blender Foundation / Blender Studio**).

### O que ficou superado

A `docs/PROPOSTA-3-DIAS.md` (cronograma de 3 dias, Twinmotion como Plano A,
portão de sábado 12h) foi escrita antes deste fluxo e **está superada pelo
Plano A/B acima**. Fica no repositório como registro do raciocínio de motor e
dos números de render — não como plano de trabalho.

---

## O achado que mudou o filme

O percurso antigo (16 pontos, uma curva bezier única, 128 s) foi medido contra
a planta: **1.152 m em 128 s dão 9,0 m/s — 32 km/h**, de 1,3 a 7× acima da
faixa cinematográfica de drone (1,3–2,2 m/s em órbita/push-in, 3,6–6,7 m/s em
sobrevoo). Nessa velocidade não se lê placa nem se reconhece área.

**A câmera virou dado.** `data/planos.json` declara 22 planos — alvo, lente,
altura, movimento, duração — cada um dentro da faixa cinematográfica, conferido
por `python scripts/planos.py --conferir`. Ver `docs/PLANOS.md`.

### Altura de câmera: a régua é o ambiente, não a telemetria

Ordem do Natan, 14/08: **pavilhão por dentro ~2 m · lugar aberto 4–15 m · e
talvez um plano de 40–50 m mostrando o rodeio inteiro.** A telemetria dos 62
voos serve para **aperfeiçoar o mapa**, não para definir altura de câmera.

### Duas abordagens conviveram nesta conversa

1. **Mapa animado 2.5D** com imagens de IA como janelas — veio de um chat
   anterior (`reference/SULL_MAPA_EVENTO.md`), documentado em `docs/BRIEFING.md`.
2. **Cena 3D real em Blender** — decisão do cliente, é o caminho ativo.
   Qualidade de jogo moderno é suficiente, não precisa fotorrealismo.

**O caminho ativo é o 2.** O material do caminho 1 segue válido para o LOOK LOCK
das imagens de apoio, os títulos e as restrições do cliente.

---

## O que já está pronto e testado

| Item | Onde | Estado |
|---|---|---|
| Planta extraída do PDF | `data/mapa_agroshow26.json` | 134 estandes com área, 181 blocos, 122 zonas |
| Auditoria do DWG | `data/dwg_agroshow26.json` | Confirma: não há vetor |
| Núcleo de terreno/bacia | `scripts/terreno.py` | Sem `bpy` — escala, bacia, leitura da planta. Fonte única para o gerador e a decupagem |
| Decupagem do filme | `data/planos.json` + `scripts/planos.py` | 22 planos, conferidos em velocidade — ver `docs/PLANOS.md` |
| Gerador da cena 3D | `scripts/build_scene.py` | Roda ponta a ponta. `--plano` corta por região, `--export-fbx` exporta FBX |
| Render retomável | `scripts/render_shots.py` | Plano a plano, animatic, calibração de tempo (`--cronometrar`) |
| Entrega | `scripts/encode.sh` | Os 3 arquivos + cartela de teste, a partir da sequência de PNG |
| Transcrição dos áudios | `docs/brief-audios.md` | Fonte primária do roteiro **e do conteúdo de cada ambiente** |
| Briefing completo | `docs/BRIEFING.md` | Roteiro, restrições, entrega |
| Dossiê de materiais | `docs/MATERIAIS-referencia.md` | Triagem dos 137 GB: escolha por classe, com vídeo, timecode e prova |
| Referência do portal | `reference/PORTAL-referencia.md` | Descrição da fachada |
| Agente | `.claude/agents/render-agroshow.md` | Reescrito para 3D em 13/08/2026. Sistema próprio, fora do Cláudio. Texto 2.5D arquivado em `docs/AGENTE-2.5D-suspenso.md` |

Saída atual do gerador (filme completo, sem `--plano`):

```
escala .............. 0.5611 m/pt
extensao do terreno . 808 x 454 m
pavilhoes ........... 6
estandes ............ 74 instanciados + 60 proprios
planos .............. 22 de 22 (filme completo)
render .............. 2760x1380 (2:1)
duracao do filme .... 4635 quadros (154 s a 30 fps)
patamares ........... arena 0 m -> shows 3.5 m -> anel 7.0 m -> plato 10.0 m
```

```bash
python scripts/build_scene.py --out out/cena.blend                 # filme completo
python scripts/build_scene.py --plano P19 --out out/P19.blend      # so um plano
python scripts/build_scene.py --export-fbx out/cena.fbx            # FBX
python scripts/planos.py --conferir                                # velocidades, sem bpy
```

Na máquina do Natan o gerador roda pelo Blender instalado, não pelo `bpy` do
pip:

```bash
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python scripts/build_scene.py -- --out out/cena.blend
```

Renders de conferência: `docs/conferencia-layout.png` (topo),
`docs/conferencia-bacia.png` (patamares), `docs/conferencia-quadro.png`
(quadro da animação) — **desatualizado**, ainda mostra a câmera antiga de 16
pontos. Regenerar com a decupagem nova.

---

## Descobertas que não podem ser perdidas

**Escala do mapa: 0,5611 m/pt.** Derivada dos 39 estandes de 100 m² da série C,
que ficam encostados em fileira — a mediana entre rótulos consecutivos é
17,82 pt. A série A não serve para o mesmo cálculo, há corredor entre módulos.
Resulta em terreno de 808 × 454 m. **Ainda não conferida com medida em campo.**

**Nem o PDF nem o DWG têm geometria vetorial.** Os dois carregam o mesmo bitmap
de 1806 × 1383 px. O DWG (AC1018) tem 4883 TEXT, 1 LINE, 1 SOLID, 2 HATCH e
zero polilinha — e 4483 dos textos são caracteres soltos, glifo a glifo.
Assinatura de PDF importado para CAD. Não insista em extrair contorno dele.
**Consequência para as estradas:** o traçado é lido do bitmap e conferido por
print com o Natan antes de virar geometria.

**DEM global não serve para o recinto.** SRTM, Copernicus, NASADEM e AW3D30 são
todos ~30 m. Um recorte de 2 × 2 km sai com **67 × 67 pixels** — o recinto
ocuparia uns 27. Os patamares somem. A bacia foi derivada da planta, e é mais
precisa. OpenTopography só vale para o entorno distante.

**A bacia veio de três fontes concordando:** os 93 estandes da série C se
agrupam em anéis a 72–90 m e 108–113 m do centro da arena; as 15 anotações de
"Talude" caem nas faixas de transição; e o áudio descreve três níveis. Os
**raios** são dado; as **alturas** (3,5 / 7 / 10 m) são estimadas por proporção.

**Ordem dos pavilhões de animais: não há divergência.** Um briefing anterior
travou o bloco alegando conflito entre áudio e planta. Ordenando os rótulos por
coordenada Y real, a sequência bate exatamente com a ditada. O bloco está
liberado.

**O motor de render não pode cair sozinho.** No Blender 5.2 o identificador é
`BLENDER_EEVEE`; `BLENDER_EEVEE_NEXT` não existe mais. O `try/except` antigo
engolia o `TypeError` e a cena saía em **Cycles CPU em silêncio**. Motor é
declaração explícita, nunca fallback mudo.

**Local:** -25,73144 / -53,07627 — R. Jorge Amado, Jardim Marcante, Dois
Vizinhos - PR, 85660-000.

---

## O footage — 137 GB, 173 vídeos, triados em 14/08

Em `E:\Projetos todos\Mapa - agroshow\Brutos Expo`. **Não está neste
repositório e não deve entrar**: é material de cliente e o `origin` é público.
O que sobe para cá é o dossiê e o caminho absoluto de cada prova.

Triagem completa: 173 folhas de contato, 10 quadros por vídeo com timecode
gravado no pixel, mais a análise de todas elas por classe de material. As
escolhas estão em **`docs/MATERIAIS-referencia.md`** — leia antes de tocar em
material, portal, palco ou camarotes.

O que o dossiê entrega, em uma linha cada:

- **Material por classe** com vídeo, timecode e rajada em resolução nativa em
  `_triagem\provas-materiais\<classe>\`. Grama não tem close no acervo: vem de
  biblioteca CC0 **calibrada** pela cor e mancha medidas.
- **Luz:** o material se parte em sol a pino, golden hour e noturno. O melhor
  material de textura está no golden hour; noturno é inútil para PBR.
  Temperatura medida: mediana 5206 K, extremos 3318 K e 8061 K.
- **Portal, palco e camarotes:** o portal celeiro **não aparece em nenhum dos
  173 vídeos** — a referência é a foto do cliente em
  `E:\Projetos todos\Mapa - agroshow\WhatsApp Image 2026-08-12 at 13.15.32.jpeg`.
  Palco: `DJI_20251127184447_0110_D` 00:00:02. Camarotes:
  `DJI_20251128224305_0163_D` 00:00:09 — e **não há arquibancada em nenhum
  quadro do recinto inteiro**, o que confirma a restrição 1 por imagem.
- **Escala vertical:** a pessoa em pé no quadro `1 (4)` 00:00:02 dá ~1,70 m no
  mesmo quadro que o palco fixo. Não é trena, mas é melhor que proporção.
- **As cotas dos patamares continuam estimadas.** A telemetria **não** resolve:
  dentro de uma sessão a DJI mantém a referência barométrica do primeiro
  takeoff, então `AbsoluteAltitude − RelativeAltitude` mede calibração, não
  terreno — 9 das 10 sessões dão desnível 0,00 m.

Telemetria dos 62 voos em `_triagem\telemetria\`, resumo em `camera-real.json`.
Ferramentas para regerar tudo em `E:\Projetos todos\Mapa - agroshow\Comandos\`
(`extrair_quadros.py`, `extrair_telemetria.py`, `camera_real.py`,
`extrair_provas.py`, e `cotas_do_terreno.py`, que **não funciona** — ver acima).

**Registro de material sondado que não está no disco:** há 17 `.ffprobe.json` em
`_triagem\metadados\` de arquivos `dji_fly_20260813_*` que não existem mais na
pasta. Vieram de um zip que falhou na descompactação de 13/08 e foi apagado
depois de extraído. Não é perda conhecida — é uma ausência que ninguém decidiu.
Decisão do Natan.

---

## Especificações de entrega — não negociar

Telão LED **P2,9 · 1379 × 690 px nativos · 4,00 × 2,00 m**.

- Proporção **2:1**, master em **2760 × 1380**
- **Nunca masterizar em 1379 × 690** — largura ímpar não codifica em H.264 4:2:0
- **`.mov` (ProRes 422 HQ) e `.mp4` (H.264)** — os dois, sempre
- **2:1 limpo, jamais tarja embutida.** Tarja embutida não se desfaz, e se o
  processador estiver em modo preencher, estica a tarja junto
- **Área de segurança de 90%** — 2484 × 1242 centralizados
- Tipografia: o painel tem 951.510 pixels para 4 m de tela. Título com no mínimo
  8% da altura do quadro; apoio nunca abaixo de 4%
- Mandar junto uma **cartela de teste** de 10 s com marcas de canto

A resolução de entrada do processador não será confirmada — decisão do cliente.

---

## Restrições do cliente — violar é rejeição

1. **Arena de rodeio SEM arquibancada.** Só pista, camarotes nos dois lados,
   palco de frente. **Confirmada por imagem** no footage do próprio recinto.
2. **A palavra "Kids" é proibida.** Use *Fazendinha*; "Área Infantil" só em
   descrição secundária.
3. **Fazendinha:** nome grande, descrição pequena embaixo.
4. **O portal é o da foto** (`reference/PORTAL-referencia.md`). Na dúvida sobre
   um detalhe, escolha a leitura mais econômica.
5. **Quatro diferenciais** com mais tela: Fazendinha, Rodeio, Café Colonial,
   Mercado do Produtor.
6. **Plano final saindo pelo portal.**

Frases literais, não reescrever:
- Abertura: *É daqui que sai o alimento que sustenta o mundo*
- Fechamento: *Aqui será um grande balcão de negócios*

---

## Próximos passos — na ordem do fluxo de 5 passos

1. **Inventário completo dos locais** (`data/locais.json` + `docs/LOCAIS.md`):
   todo rótulo do mapa, com coordenada, categoria, plano de câmera e a **ficha
   de conteúdo tirada dos áudios**.
2. **Estradas e vias** lidas do bitmap, conferidas com o Natan por print antes
   de virar geometria.
3. **Alturas de câmera** em `data/planos.json` ajustadas às bandas dele
   (~2 m interior · 4–15 m aberto · 40–50 m só no conjunto do rodeio).
4. **Portal, palco, camarotes e pavilhões modelados** — hoje são caixa ou nem
   isso. O portal é o primeiro e o último plano (P02 e P22).
5. **Texturas e luz:** PBR calibrado pelas provas + HDRI golden hour.
6. **Títulos, letreiros e logos** (JPEG ou nome simples).
7. **Cena salva com a configuração Cycles dele** e entregue como `.blend`.
8. Confirmar as alturas dos patamares com um quadro de drone lateral.

Feito em 13/08/2026: o agente `.claude/agents/render-agroshow.md` foi reescrito
para o caminho 3D. Ele é **sistema próprio** — não responde ao Cláudio (o
diretor de montagem em `E:\I.A Edit\claudio`) e não herda a doutrina 2.5D, por
decisão do Natan.

Feito em 14/08/2026, de manhã: triagem completa dos 137 GB e o dossiê
`docs/MATERIAIS-referencia.md`.

Feito em 14/08/2026, à tarde: a câmera deixou de ser uma curva única e virou
decupagem em `data/planos.json` (22 planos); o gerador ganhou corte por região
(`--plano`) e exportação FBX; e o Natan fixou o fluxo de 5 passos, a régua de
altura por ambiente e a configuração de render.

---

## Pendências com o cliente

| # | Pendência | Impacto |
|---|---|---|
| ~~1~~ | ~~Footage de edições anteriores~~ — **chegou em 13/08, triado em 14/08** | Resolvida — `docs/MATERIAIS-referencia.md` |
| 2 | **Posição da Fazendinha e do portão** — não existe na planta, só no áudio | **O Natan vai mandar um print com a posição e instruções.** Enquanto não chega, P14/P15 seguem com âncora `estimada` |
| 3 | Quadro de drone **lateral** da arena, rasante, com elemento de altura conhecida | Médio — trava as cotas dos patamares. Das 173 folhas, nenhuma serve: todas são oblíquas altas |
| 4 | Medida real de qualquer estrutura | Médio — confirma a escala de 0,5611 m/pt |
| 5 | Identidade visual AGROSHOW 2026 em vetor | Baixo agora — decisão do Natan: **usar o JPEG achado na internet ou o nome simples** |

---

## Limitações do ambiente remoto

Registrado para não se repetir tentativa: em sessão remota o proxy de egresso
bloqueia `drive.google.com`, `at.adobe.com`, `portal.opentopography.org`,
`huggingface.co`, o CDN da OpenAI, `openstreetmap.org` e
`doisvizinhos.pr.gov.br`. Vídeo do Drive e transcrição de áudio precisam ser
feitos localmente e anexados no chat. GitHub, PyPI e o arquivo principal do
Ubuntu funcionam. **Na máquina do Natan isso não vale** — lá o acesso é
direto, e é onde o footage e o Blender moram.
