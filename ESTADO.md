# ESTADO DO PROJETO — leia isto primeiro

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Atualizado em 15/08/2026.

> **Regime de trabalho em vigor**, ordem dele de 15/08: *"Trabalhe de forma
> autônoma até o fim. Não me pergunte nada: quando houver ambiguidade, escolha a
> opção mais conservadora, registre a decisão e o motivo em DECISOES.md e siga.
> Se algo travar de vez, pule para a próxima tarefa da fila e documente o
> bloqueio."* → **`DECISOES.md` é leitura obrigatória.**
>
> **Precedência:** ordem do Natan → `reference/DOUTRINA-RENDER-3D.md` → doutrina
> do projeto. A doutrina é ordem norteadora dele, entregue em 15/08. Onde ela
> contraria uma ordem direta, a ordem vence — e a divergência fica escrita.

## Os números do render, remedidos em 15/08

```
saida ........ beauty EXR (Half/DWAA) + data EXR (Float32/ZIP, crypto) + preview PNG 8
custo ........ 10,0 s/quadro · 12,9 h o filme · 176 GB de 300 GB livres no F:
amostragem ... 128 samples / limiar 0,1 + denoise -- medido contra 0,01/max: EMPATAM
```

**O que estava errado antes:** este arquivo e o `RETOMAR.md` declaravam 36–38
s/quadro e 46–49 h. Era **CPU**. A cena guarda `cycles.device = "GPU"` mas o
dispositivo mora nas preferências, que são da instalação e não do `.blend` —
aberto numa sessão limpa, o Cycles caía para a CPU sem avisar. Conserto em
`scripts/placa.py`; o `render_shots.py` agora **aborta** sem GPU.

**E a projeção de disco só vale amostrando vários planos:** medida no P01 deu
199 GB, e a média de seis planos deu 285 GB — o P01 tem metade do quadro em céu,
que comprime quase de graça. Os 176 GB de hoje são de seis planos, depois de
cortar do beauty os quatro passes de difuso/glossy (16 dos 19,8 MB do slot).

Este arquivo existe para retomar o trabalho em outra sessão sem perder contexto.
Leia daqui e siga para os documentos citados.

> **Retomando depois de uma pausa? Abra `RETOMAR.md` antes deste arquivo.**
> Ele tem o veredito do Natan sobre o próximo passo, o tempo de render medido
> na máquina, os comandos e as oito armadilhas que já custaram uma rodada cada.

---

## O caminho ativo: o fluxo de 5 passos do Natan

Decidido por ele em 14/08/2026, e é isto que manda:

1. **Posições de todos os locais** do mapa (`Mapa_AGROSHOW26`), sem faltar
   nenhum, com todos os nomes — **incluindo as estradas**, que entram no
   Blender. Dúvida de leitura ou posição vira **pergunta com print** do trecho
   do mapa, respondida por ele.
2. **Modelagem e texturas.**
3. ~~**Títulos e letreiros**~~ — **feito em 15/08**, com o nome simples, que foi
   o caminho que ele autorizou. Ver `data/letreiros.json`.
4. **Projeto pronto para ele renderizar.** A cena sai salva com a configuração
   dele já marcada; **quem exporta é ele, no Blender dele**.
5. ~~**Plano A**~~ — **decidido por ele em 15/08: é o Plano A.** Os quadros
   viram entrada de **IA geradora de vídeo**, no **Flow** (ou Higgsfield).
   Operável em **`docs/CENAS-IA.md`**; contrato em `data/cenas-ia.json`.
   **A regra que garante o lugar: nenhum clipe é texto-para-vídeo.** Todo clipe
   é quadro-para-vídeo, com os DOIS extremos renderizados da cena medida — e o
   prompt é **proibido de descrever posição**, porque o quadro já a tem medida.
   Custo: **51 quadros-guia (~8 min)** contra as 12,9 h do filme inteiro.
   **Plano B** (render local completo) não foi apagado: continua em
   `scripts/render_shots.py`, e é para onde se volta se a IA não convencer.

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
| Footprint das zonas | `scripts/extrair_footprints.py` + `data/footprints.json` | Mede o desenho. **18 zonas com footprint que serve; 35 só têm rótulo** — ver `docs/FOOTPRINTS.md` |
| Estimativa das demais | `data/estimativas.json` + `scripts/estimativas.py` | 33 zonas na coleção **ESTIMADO**, carimbadas. Autorizado por ele em 14/08. Medida e estimativa não se misturam |
| Cor-base dos materiais | `scripts/medir_materiais.py` + `data/materiais-medidos.json` | Medida do footage, com âncora na lona branca e **teste de controle** na lavoura |
| Textura PBR | `data/texturas.json` + `scripts/texturas.py` | 4 materiais com normal, rugosidade e mancha CC0. **A cor medida não é sobrescrita** — a biblioteca entra como relevo e variação normalizada, e `--conferir` prova a conta |
| Relevo do entorno | `scripts/relevo_entorno.py` + `data/relevo-entorno.json` | DEM público até 12 km, conferido contra segunda fonte em ±5 m. Amortecido a zero dentro de 600 m para não tocar no recinto |
| Cobertura do solo | `scripts/cobertura_entorno.py` + `data/cobertura-entorno.json` | ESA WorldCover 10 m (CC-BY, **exige crédito**) diz o QUE é cada chão; `materiais-medidos.json` diz que COR. 45% lavoura, 38% mata, 14% campo. Faltam os silos e o socalco |
| Povoamento | `data/povoamento.json` + `scripts/povoamento.py` | 1.681 figuras, censo tirado do áudio do cliente minuto a minuto. **São PROXY** — destravar depende da escolha Plano A vs Plano B |
| **Tendas nas posições reais** | `data/tendas.json` + `scripts/tendas.py` | Os 134 estandes deixaram de ser caixa de 3,2 m e viraram **tenda piramidal de lona**. **131 são instância de 3 malhas** (3×3, 5×5, 10×10), 3 têm malha própria. A posição não mudou — o que era falso era a forma. A planta provou a família: 35 dos 41 da série A têm 25,00 m² e 39 dos 93 da série C têm 100,00 m², em cima das medidas padrão |
| **Cenas para IA (Plano A)** | `data/cenas-ia.json` + `scripts/cenas_ia.py` + `docs/CENAS-IA.md` | Os 22 planos quebrados na grade da plataforma, com prompt por clipe e os quadros-guia. **Flow: 29 clipes, 51 quadros, zero planos fora da faixa. Higgsfield: 4 planos não cabem na grade de 5/10 s** |
| **Render dos quadros-guia** | `scripts/render_guias.py` | 3840×2160 (16:9), **sem letreiro**, só as pontas de clipe. ~8 min contra 12,9 h |
| Peças avulsas | `data/pecas-avulsas.json` + `scripts/avulsas.py` | **8** peças na coleção **AREA_DE_ESPERA** em (520, −240), etiquetadas: silo, conjunto de silos, porteira, guichê, curral, torre, inflável, trator. **Ele posiciona no Blender.** As 3 tendas saíram da espera em 15/08 — agora têm 134 lugares medidos |
| Letreiros | `data/letreiros.json` + `scripts/letreiros.py` | 16 letreiros com o texto do áudio dele. O tamanho sai da regra de 8%/4% por conta, e o script **acusa** quem cair abaixo. Cada um só existe durante o plano dele. Tipografia é proposta |
| Mobiliário | `data/mobiliario.json` + `scripts/mobiliario.py` | 209 peças **CC0 de verdade** (cadeira monobloco, mesa de piquenique, mesa de 4 lugares) nas duas praças e no Café Colonial. Pedido dele em [00:57] |
| **Saída de render** | `data/saida.json` + `scripts/saida.py` | Três slots. **Half+DWAA destrói o Cryptomatte** (hash é float 32, DWAA é lossy) — por isso o dado vai em Float32/ZIP à parte. `save_as_render` é a mesma chave invertida entre PNG e EXR |
| **Conferidor de matte** | `scripts/conferir_matte.py` | Extrai matte de verdade do EXR: MurmurHash3 do nome, casamento bit a bit, cobertura por faixa. **É o portão** — não se renderiza a fila com crypto quebrado |
| **GPU** | `scripts/placa.py` | Liga OptiX e desliga a CPU. Chamar depois de abrir o `.blend`, **sempre** |
| **Medição de render** | `scripts/medir_render.py` + `medir_ruido.py` + `medir_compressao.py` | Tempo, ruído local e custo em disco por arranjo. Render e medição são passos separados: o Python do Blender não tem cv2 |
| **Footage de 13/08** | `data/footage-quinta.json` | Os 17 vídeos decupados: o que cada um mostra, quais servem de prova de forma e quais de amostra de material, o datum de escala de cada um, e a **regra de desempate footage × planta**. Todos **bt709 SDR 10 bits 4:2:0** — não são HDR |
| **Extração linear** | `scripts/extrair_linear.py` | A **segunda** extração, linear 16 bits, para medir. A de `extracao/` é JPEG sRGB e serve só para o olho — medir nela dá número errado que passa no `--conferir` |
| Briefing completo | `docs/BRIEFING.md` | Roteiro, restrições, entrega |
| Dossiê de materiais | `docs/MATERIAIS-referencia.md` | Triagem dos 137 GB: escolha por classe, com vídeo, timecode e prova |
| Referência do portal | `reference/PORTAL-referencia.md` | Descrição da fachada |
| Agente | `.claude/agents/render-agroshow.md` | Reescrito para 3D em 13/08/2026. Sistema próprio, fora do Cláudio. Texto 2.5D arquivado em `docs/AGENTE-2.5D-suspenso.md` |

Saída atual do gerador (filme completo, sem `--plano`):

```
escala .............. 0.5611 m/pt
extensao do terreno . 808 x 454 m
entorno ............. relevo REAL ate 12 km (SRTM), sitio a 602 m
cobertura do solo ... ESA WorldCover 10 m: 45% lavoura, 38% mata, 14% campo
pavilhoes ........... 8
zonas medidas ....... 9 (footprint do desenho, altura declarada)
zonas estimadas ..... 33 na colecao ESTIMADO (4 recusadas) -- NAO SAO MEDIDA
estandes ............ 131 TENDAS instanciadas + 3 proprias (eram caixas)
arvores ............. 418 + 189 arbustos de talude (so onde ha declive)
povoamento .......... 1681 figuras PROXY na colecao POVOAMENTO -- NAO sao finais
mobiliario .......... 209 pecas CC0 (mesa e cadeira) na colecao MOBILIARIO
letreiros ........... 16, texto do audio dele, tamanho pela regra de 8%
area de espera ...... 8 pecas em (520,-240) para ele posicionar (as 3 tendas sairam)
textura ............. PBR CC0 em 4 materiais; a cor MEDIDA nao e sobrescrita
planos .............. 22 de 22 (filme completo)
render .............. 2760x1380 (2:1)
duracao do filme .... 4635 quadros (154 s a 30 fps)
patamares ........... arena 0 m -> shows 3.5 m -> anel 7.0 m -> plato 10.0 m
bacia ............... ferradura aberta 120 graus para SUL-SUDESTE (medida)
```

```bash
python scripts/build_scene.py --out out/cena.blend                 # filme completo
python scripts/build_scene.py --plano P19 --out out/P19.blend      # so um plano
python scripts/build_scene.py --export-fbx out/cena.fbx            # FBX
python scripts/planos.py --conferir                                # velocidades, sem bpy
python scripts/tendas.py --conferir                                # familias de tenda, sem bpy
python scripts/cenas_ia.py --conferir                              # grade do Flow, sem bpy
```

O caminho do **Plano A**, do zero até o Flow (detalhe em `docs/CENAS-IA.md`):

```bash
blender --background --python scripts/build_scene.py  -- --out out/cena.blend
python3 scripts/cenas_ia.py --conferir
blender --background --python scripts/render_guias.py -- --blend out/cena.blend --plataforma flow
python3 scripts/cenas_ia.py --roteiro > out/cenas/roteiro-flow.md
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

**A planta descreve 113 zonas e desenha footprint para 18.** O resto é rótulo
sobre chão aberto, e o extrator antigo media a tinta da própria palavra — três
métodos foram testados para recuperar o que falta e os três foram recusados pelo
número. Consequência direta para o passo 1 do fluxo dele: as 35 zonas sem
desenho precisam de **print com posição e tamanho**, de **caixa padrão
declarada**, ou de ficar fora desta versão. Detalhe em `docs/FOOTPRINTS.md`.

**Nem o PDF nem o DWG têm geometria vetorial.** Os dois carregam o mesmo bitmap
de 1806 × 1383 px. O DWG (AC1018) tem 4883 TEXT, 1 LINE, 1 SOLID, 2 HATCH e
zero polilinha — e 4483 dos textos são caracteres soltos, glifo a glifo.
Assinatura de PDF importado para CAD. Não insista em extrair contorno dele.
**Reconferido em 14/08**, por varredura crua do DXF que conta entidade dentro
dos BLOCKS: 4 entidades de desenho no arquivo inteiro. O DWG da pasta
`E:\Projetos todos\Mapa - agroshow\` é este mesmo, byte a byte. E o PDF também
não tem vetor — `get_drawings()` devolve só o retângulo branco da página.
**Consequência para as estradas:** o traçado é lido do bitmap e conferido por
print com o Natan antes de virar geometria.

**DEM global não serve para o recinto.** SRTM, Copernicus, NASADEM e AW3D30 são
todos ~30 m. Um recorte de 2 × 2 km sai com **67 × 67 pixels** — o recinto
ocuparia uns 27. Os patamares somem. A bacia foi derivada da planta, e é mais
precisa. DEM só vale para o entorno distante.

**E para o entorno distante ele valeu, em 14/08.** `scripts/relevo_entorno.py`
baixa AWS Terrain Tiles (SRTM, domínio público, **sem chave nem cadastro** — o
OpenTopography exigiria criar conta) e o `Entorno` passou de disco chapado de
3 km a terreno real de 12 km de raio. Sítio a **602 m**, região caindo a
**−435 m**: o horizonte deixou de ser uma reta. Conferido contra o opentopodata
em 5 pontos ao longo de 16 km, **±5 m**. Dentro de 600 m do centro o desnível é
zerado, para o DEM de 30 m não tocar no recinto medido.

**A bacia veio de três fontes concordando:** os 93 estandes da série C se
agrupam em anéis a 72–90 m e 108–113 m do centro da arena; as 15 anotações de
"Talude" caem nas faixas de transição; e o áudio descreve três níveis. Os
**raios** são dado; as **alturas** (3,5 / 7 / 10 m) são estimadas por proporção.

**E ela não é um cilindro — corrigido em 14/08.** As mesmas duas fontes dizem
*onde* há arrimo: no setor de **240° a 360°** (0° = leste, 90° = norte) não há
nenhum dos 15 taludes nem nenhum dos 93 estandes. A bacia é ferradura aberta em
~120° para **sul-sudeste**, e é por ali que o palco olha para a pista e que
animal e veículo chegam em nível. Contrato em `data/bacia.json`, prova em
`docs/conferencia-bacia-ferradura.png`. Em r = 150 m os dois perfis se
reencontram: nada longe da arena mudou.

**Ordem dos pavilhões de animais: não há divergência.** Um briefing anterior
travou o bloco alegando conflito entre áudio e planta. Ordenando os rótulos por
coordenada Y real, a sequência bate exatamente com a ditada. O bloco está
liberado.

**O motor de render não pode cair sozinho.** No Blender 5.2 o identificador é
`BLENDER_EEVEE`; `BLENDER_EEVEE_NEXT` não existe mais. O `try/except` antigo
engolia o `TypeError` e a cena saía em **Cycles CPU em silêncio**. Motor é
declaração explícita, nunca fallback mudo.

**Biblioteca de modelo 3D: o que serve e o que não serve.** Conferido em 15/08,
site por site, e a conclusão não é sobre dificuldade, é sobre **licença**:

- **free3d** — o gratuito é em geral **"Licença de Uso Pessoal"**, e isto é
  entrega de cliente. **Criar conta não resolve.** A categoria "Arquitetura" tem
  26 modelos grátis e nenhum serve.
- **TurboSquid** — o gratuito é **Royalty Free e serve**, mas **exige conta**.
  Ele se ofereceu a criar: *"se precisa eu posso criar a conta onde tiver o
  modelo que precisar"*. Ele cria e entra no Chrome; eu baixo pela sessão
  aberta, **sem digitar senha**.
- **Poly Haven** — CC0, sem cadastro, e é a fonte padrão da casa. Mas são 521
  modelos de **props de interior**: tem mesa e cadeira, não tem silo, tenda,
  gente nem gado.

**Regra que sai disso:** antes de baixar modelo para este projeto, ler a
licença. CC0 e Royalty Free entram; "personal use" não entra, por melhor que
seja o modelo.

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

## Próximos passos

**O veredito do Natan em 14/08, olhando o primeiro quadro renderizado:**
*"não corrija pois esta longe de um render de qualidade"* — dito quando eu
consertava um detalhe da geometria do portal. O que falta não é polígono:

1. ~~**HDRI de golden hour** no lugar do céu chapado~~ — **fechado em 14/08.**
   `construir_ceu()` carrega o HDRI, a SUN é calculada pelo NOAA e colorida pelo
   disco medido do céu. O escolhido é o `kloppenheim_06`, por erro de elevação
   de 2,1° contra 8,0° do belfast. Provas em `out/luz/`.
2. ~~**Materiais**~~ — **fechado em 14/08, à noite.** A cor-base tinha sido
   medida de manhã; à noite entrou a textura, com contrato em
   `data/texturas.json`: `aerial_grass_rock` (15 m), `dirt_aerial_03` (25 m),
   `gravel_road` (2 m) e `corrugated_iron_02` (2,7 m), todos CC0 do Poly Haven.
   A regra que manda: **a cor medida não é sobrescrita** — a biblioteca entra
   como normal, como *variação* de rugosidade em torno do valor declarado, e
   como mancha de luminância normalizada pela própria média (a média fica 1,0,
   então a cor média da superfície é exatamente a medida).
   Custo: **36,3 → 38,2 s/quadro**, +5,2%.
   Ficaram de fora com motivo: lona (o que se vê é a barriga do pano, que é
   geometria), copa (não aparece do sobrevoo) e madeira do portal (merece a
   textura da foto do cliente, não uma tábua de biblioteca).
   No caminho apareceu um defeito antigo: a rampa das duas gramas entregava
   **meio a meio** onde o comentário prometia "mais campo que desgaste" — o
   recinto estava com albedo médio 0,192 contra os **0,129 medidos**. Calibrada
   por varredura, ficou em 0,152. Provas com e sem em `out/textura/`.
3. **Vegetação** — feita em 14/08, e completada à noite com os **189 arbustos
   dos 15 taludes**, plantados só onde o terreno tem declive medido: os 6 Bosques, as 2 Matas Nativas e a
   **alameda arborizada**, num total de **418 árvores, todas instâncias de UMA
   malha**. Contrato em `data/vegetacao.json`; o terreno deixou de ser cor
   chapada e mistura as **duas gramas medidas** — a sã e a pisada — por ruído de
   duas frequências. Falta o **povoamento** (gente, gado, montaria) e o arbusto
   dos 15 taludes.
3b. **Povoamento** — feito em 14/08 à noite: **1.681 figuras**, censo tirado do
   áudio do cliente minuto a minuto (`data/povoamento.json`). **São PROXY**, na
   coleção `POVOAMENTO`: não existe gente nem gado em CC0 que sirva, e a 6 m de
   câmera o proxy lê como balizador. Destravar isso é a pergunta Plano A vs
   Plano B — ver `RETOMAR.md`, pendências 14 e 14b.
4. **Títulos, letreiros e logos** — passo 3 do fluxo dele. Logo se resolve com
   o JPEG achado ou o nome simples; não esperar vetor.
5. Confirmar as alturas dos patamares com um quadro de drone lateral.

Feito e fechado: inventário dos locais, vias lidas do bitmap, as 22 âncoras em
`planta`, a régua de altura por ambiente, portal/palco/camarotes/pavilhões
modelados e a configuração de Cycles gravada na cena.

### O número que decide o Plano A vs o Plano B

Medido nesta máquina, com a cena ainda crua: **31 s por quadro** em 2760×1380,
Cycles 128 samples, OptiX na RTX 4060 — o filme inteiro, 4.635 quadros, dá
**cerca de 39 h**. Com textura, vegetação e gente, sobe. Recronometrar depois
do passo 2 antes de prometer prazo.

**Recronometrado em 14/08, já com as 42 zonas e as 232 árvores** (por ordem
dele: *"medir o custo da vegetação antes de escolher o teto de horas"*),
com `scripts/cronometrar_vegetacao.py` — o mesmo quadro, duas vezes:

| | s/quadro | filme inteiro |
|---|---|---|
| sem vegetação | 30,0 s | 38,7 h |
| **com vegetação (418 árvores)** | **33,1 s** | **42,6 h** |
| custo das árvores | +3,0 s (+10%) | +3,9 h |

**A vegetação é barata, e é a instanciação que faz isso** — 308 vértices reais
em memória contra 128.744 se cada árvore tivesse a sua malha. Ainda é cena sem
textura e sem gente — recronometrar depois da textura.

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
