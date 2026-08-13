# ESTADO DO PROJETO — leia isto primeiro

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Atualizado em 13/08/2026, madrugada.

Este arquivo existe para retomar o trabalho em outra sessão sem perder contexto.
Leia daqui e siga para os documentos citados.

---

## Situação

Vídeo de apresentação do parque, para telão, com percurso pelo recinto na ordem
ditada pelo cliente. **Prazo original era domingo; o cliente antecipou para
amanhã (13/08)**, para sobrar tempo de lapidação antes da entrega.

Com essa antecipação, a meta de amanhã **não é o filme acabado** — é a **base
navegável e renderizando**, para lapidar por cima. Essa base existe: a cena
monta em segundos, o percurso cobre os 20 blocos do roteiro e a câmera enquadra
cada bloco pela frente.

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
| Gerador da cena 3D | `scripts/build_scene.py` | Roda ponta a ponta em bpy 5.0.1 |
| Relevo medido do entorno | `scripts/fetch_dem.py` → `data/dem_recinto.npz` | 2,4 × 2,4 km, 4,3 m/px |
| Percurso dos 20 blocos | `PERCURSO` no gerador | 22 pontos, na ordem do roteiro |
| Portal, palco, camarotes | `construir_portal/palco/camarotes` | Modelados, leitura econômica |
| Galpões da faixa norte | `GALPOES` no gerador | Medidos no bitmap da prancha (±2 m) |
| Recinto de Leilões | `construir_leiloes` | Estrela de 8 pontas, 38 m, medida no bitmap |
| Pista de Julgamentos | `construir_pista_julgamento` | Pasto cercado, 42 × 59 m |
| Fazendinha | `construir_fazendinha` | Faixa cercada 28 × 90 m com porteira |
| Estacionamentos | `construir_estacionamentos` | Lajes de asfalto, dimensão aproximada |
| Caminho do render final | `scripts/render_final.sh` | Cena → quadros → `.mov` + 2 `.mp4` |
| Quadros de conferência | `docs/conferencia/` | Um por bloco, 690×345 |
| **Conferência contra a planta** | `scripts/overlay_check.py` → `docs/conferencia-planta.png` | Cena sobreposta ao desenho |
| Transcrição dos áudios | `docs/brief-audios.md` | Fonte primária do roteiro |
| Briefing completo | `docs/BRIEFING.md` | Roteiro, restrições, entrega |
| Referência do portal | `reference/PORTAL-referencia.md` | Descrição da fachada |
| Agente | `.claude/agents/render-agroshow.md` | Reescrito para o caminho 3D |

Saída atual do gerador:

```
escala .............. 0.5611 m/pt
extensao do terreno . 1808 x 1454 m (prancha + 500 m de entorno)
pavilhoes ........... 6
estandes ............ 74 instanciados + 60 proprios
estacionamentos ..... 8
galpoes da faixa norte 2
camarotes ........... 16 modulos, sem arquibancada
pontos do percurso .. 22 de 22
extensao do percurso  1693 m
trechos aereos ...... 10
camera .............. 30 mm, 4-52 m
render .............. 2760x1380 (2:1)
animacao ............ 4440 quadros (148 s a 30 fps)
sol ................. azimute 295°, elevacao 12°
relevo medido ....... 4.3 m/px, origem familia SRTM/NASADEM
mistura planta/dem .. 150 a 320 m do centro da arena
patamares ........... arena 0 m -> shows 3.5 m -> anel 7.0 m -> plato 10.0 m
```

São 22 pontos para 20 blocos: o Bosque e a travessia do portal são nós de
passagem, sem título na tela.

```bash
pip install bpy pymupdf ezdxf pillow numpy
python3 scripts/fetch_dem.py                       # so quando faltar o .npz
python3 scripts/build_scene.py --out cena.blend
python3 scripts/build_scene.py --conferencia docs/conferencia/
python3 scripts/overlay_check.py                   # cena sobre a planta
```

Conferência custa 10–20 s por quadro: Cycles em CPU, 25% da resolução, 32
amostras com denoise. **Não há GPU aqui** — EEVEE precisa de libEGL e quebra no
meio do render, por isso o padrão é Cycles. Em máquina com GPU, `--motor
BLENDER_EEVEE`.
Renders antigos do layout: `docs/conferencia-layout.png` (topo),
`docs/conferencia-bacia.png` (patamares).

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

**DEM global não resolve os patamares — mas resolve a profundidade geral, e
isso agora está na cena.** A frase anterior aqui era "DEM não serve", e era
curta demais. O que é verdade: com ~30 m de origem, um talude de 3,5 m em 15 m
de extensão não existe no dado, então **os patamares continuam vindo da planta
e as alturas continuam estimadas**. O que o dado entrega, e a planta não: o
recinto **não é plano**. Ele cai cerca de 1,4 m a cada 100 m e tem 44 m entre o
ponto mais alto e o mais baixo dentro dos 808 × 454 m. A cena tinha 10 m
chapados.

Fonte: **terrain tiles da AWS** (`s3.amazonaws.com/elevation-tiles-prod`,
formato terrarium, domínio público) — é o único provedor de elevação que o
proxy libera; OpenTopography, opentopodata e open-elevation estão bloqueados.
`scripts/fetch_dem.py` baixa e grava `data/dem_recinto.npz` (2,4 × 2,4 km),
para o gerador rodar depois sem rede.

A mistura entre as duas fontes é por raio a partir do centro da arena:
até 150 m manda a planta, além de 320 m manda o relevo medido, no meio é
transição suave. O registro do recorte assume que a coordenada do recinto cai
no centro da prancha e que o desenho tem o norte para cima — por isso a planta
é quem manda justamente onde a posição importa.

**A bacia veio de três fontes concordando:** os 93 estandes da série C se
agrupam em anéis a 72–90 m e 108–113 m do centro da arena; as 15 anotações de
"Talude" caem nas faixas de transição; e o áudio descreve três níveis. Os
**raios** são dado; as **alturas** (3,5 / 7 / 10 m) são estimadas por proporção.

**Ordem dos pavilhões de animais: não há divergência.** Um briefing anterior
travou o bloco alegando conflito entre áudio e planta. Ordenando os rótulos por
coordenada Y real, a sequência bate exatamente com a ditada. O bloco está
liberado.

**A cena foi conferida contra a planta, e a conferência achou erro grosso.**
Render de câmera mostra se o quadro ficou bonito; só a sobreposição em planta
mostra se o galpão está 90 m ao lado. Rode `scripts/overlay_check.py` depois de
mexer em qualquer posição. O que a primeira conferência pegou:

- **Cinco blocos do percurso estavam errados de 88 a 182 m.** Eu os havia
  posicionado por geometria da bacia. A planta traz os títulos do roteiro
  escritos em vermelho, com posição — inclusive a Fazendinha. O extrator não os
  pegava porque só reconhecia rótulos de uma lista fixa, e vários estão
  rotacionados. Agora saem em `titulos` no JSON.
- **Os Pavilhões 1, 2 e a Praça Coberta são um prédio só**, de ~176 × 33 m, e o
  "Pavilhão 3" é o bloco laranja do Galpão do Produtor, ~20 × 37 m. Eu havia
  suposto quatro galpões separados de 30 × 70 m.
- **Nada estava rotacionado.** Os seis pavilhões de animais correm a 18°, os
  camarotes são duas faixas retas a −54° e −70°, o palco a 28°. A direção sai
  do próprio rótulo, que na prancha corre no eixo do que ele nomeia; agora vai
  em `dir` em cada zona do JSON.
- **A pista da arena tinha 45 m de raio**; medida no desenho, tem ~26.

Desvios que sobraram, conhecidos: a caixa de cada pavilhão de animais fica
centrada no rótulo e não no prédio, o que a desloca uns 10 m no eixo; as lajes
de estacionamento são aproximadas; e os galpões têm a incerteza de leitura do
bitmap.

**A câmera errava por três motivos, não um.** Voava a 12 m com inclinação fixa
e **parava em cima do assunto** — e de cima do assunto só se vê cobertura. As
três correções, que valem para qualquer bloco novo: altura por trecho (aéreo a
52 m nas transições, baixa nos pontos), **recuo** (a câmera para dezenas de
metros antes do assunto) e **mira em alvo animado** em vez de ângulo fixo.

**A planta não desenha os Pavilhões 1, 2 e 3.** Ela rotula e desenha os
estandes de dentro, mas não o contorno do galpão — e agrupar estandes por
proximidade não serve de envoltória (o grupo do Pavilhão 3 esparrama por
122 × 106 m, o do Pavilhão 1 junta quatro estandes). Os volumes atuais são
**supostos**, na leitura mais conservadora: como os pavilhões 2 e 3 distam
39 m, o lado comprido corre norte-sul. Seis blocos do roteiro acontecem neles.

**Recuo maior que o trecho gruda duas paradas no mesmo ponto** — e dois títulos
sobre o mesmo quadro. Acontece na faixa norte, onde os rótulos distam 55–68 m.
O gerador avisa na saída quando isso ocorre; a correção é baixar o `recuo` do
bloco. Mercado, Agroindústrias e Café Colonial dividem o Pavilhão 3 e por isso
têm recuo decrescente: a câmera avança pelo galpão enquanto o título muda.

**Eixo de área aberta se lê no título, não se deduz.** Tentei deduzir o eixo da
faixa da Fazendinha por geometria duas vezes — radial, depois tangente — e errei
as duas; a cerca atravessava as fileiras de estandes. O título vermelho é escrito
**ao longo** da faixa, e agora `titulos` carrega a direção de cada um. A largura e
o comprimento também deixaram de ser escolhidos: saem do vão livre medido entre as
fileiras, e se nada couber o gerador monta só a porteira. Cerca por cima de estande
vendido é erro mais caro que cerca ausente.

**A Fazendinha não é prédio, é área aberta.** O título dela na prancha cai
numa faixa de grama entre duas fileiras de estandes, descendo o talude — bate
com o áudio ("desce pro lado da pista de tiro de laço"). Por isso ela entrou
como faixa cercada de 28 × 90 m com **porteira de destaque** na ponta que olha
para o percurso, e não como construção. A porteira o cliente pediu nominalmente.

**Cinco blocos não têm rótulo CAD — mas quatro têm título vermelho.**
Expositores Externo, Fazendinha, Exposição de Máquinas e Área de Show saem dos
títulos da prancha. Só **Veículos e Motos Náuticas** não tem nem rótulo nem
título: a prancha o marca apenas pela cor da legenda, e a posição usada é o
centroide dos pixels azuis do bitmap, fora da caixa de legenda.

**Local:** -25,73144 / -53,07627 — R. Jorge Amado, Jardim Marcante, Dois
Vizinhos - PR, 85660-000.

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
   palco de frente.
2. **A palavra "Kids" é proibida.** Use *Fazendinha*; "Área Infantil" só em
   descrição secundária.
3. **Fazendinha:** nome grande, descrição pequena embaixo.
4. **O portal é o da foto** (`reference/PORTAL-referencia.md`). Na dúvida sobre
   um detalhe, escolha a leitura mais econômica.
5. **Quatro diferenciais** com mais tela: Fazendinha, Rodeio, Café Colonial,
   Mercado do Produtor.
6. **Plano final saindo pelo portal.** Já está na cena: o caminho atravessa o
   vão central a 3,5 m de altura, abaixo da verga.

Frases literais, não reescrever:
- Abertura: *É daqui que sai o alimento que sustenta o mundo*
- Fechamento: *Aqui será um grande balcão de negócios*

---

## Próximos passos, em ordem de valor

1. **Ajustar recuo, altura e mira bloco a bloco** pelos quadros em
   `docs/conferencia/`, conferindo posição em `docs/conferencia-planta.png`. Os parâmetros estão na lista `PERCURSO`, um dicionário
   por bloco — mexer é trocar um número, não remontar cena. Os blocos da faixa
   norte (02 a 07) são os que ainda leem como telhado branco sem assunto.
2. **Confirmar as três cotas dos patamares** (3,5 / 7 / 10 m). É a última
   dimensão importante que ainda é estimativa, e o relevo medido não a resolve.
   Uma foto lateral da arena com pessoa ou veículo no quadro basta.
3. **Vegetação e povoamento** com assets CC0 (Quaternius, Kenney, Poly Haven).
   Gente é o que mais entrega maquete; ver `docs/CAMINHO-3D.md`.
4. **Texturas PBR** em vez da variação procedural de cor. Poly Haven e
   ambientCG, ambos CC0 — **os dois estão bloqueados pelo proxy do ambiente
   remoto**, precisam ser baixados localmente e anexados.
5. **HDRI real** no lugar do céu Nishita, pelo mesmo caminho.
6. **Render em passes** (beauty, depth, cryptomatte, motion vectors) antes de
   qualquer render longo. Sem os passes, refino vira re-render.
7. **Títulos e letreiros** sobre os quadros, na tipografia do telão.

---

## O que falta para o render final

O render final **não roda neste ambiente**: sem GPU, Cycles leva de 2 a 4 min
por quadro em 2760 × 1380, e são 4440 quadros — entre 6 e 12 dias. Numa máquina
com placa, EEVEE fecha o mesmo filme em torno de uma hora.

O passo a passo para quem vai rodar está em **`docs/RENDER-LOCAL.md`**:
o que instalar, como montar a cena, como conferir a posição antes de gastar
horas e como codificar os arquivos. `scripts/render_final.sh` tem o caminho
inteiro: monta a cena, roda a
conferência de posição, renderiza os quadros e codifica os três arquivos de
entrega (ProRes `.mov`, H.264 `.mp4` e a reserva 1380 × 690). Falta a cartela
de teste de 10 s.

## Pendências com o cliente

| # | Pendência | Impacto |
|---|---|---|
| 1 | Footage de edições anteriores — prometido, não chegou | Alto — vira textura e referência |
| 2 | Quadro de drone lateral da arena | Médio — trava as cotas dos patamares |
| 3 | Medida real de qualquer estrutura | Médio — confirma a escala |
| 4 | Identidade visual AGROSHOW 2026 em vetor | Médio — títulos e letreiros |

Duas pendências saíram da lista porque **a própria planta respondeu**: onde
fica a Fazendinha (título vermelho, x=426,9 y=438,1 na prancha) e a dimensão
dos galpões da faixa norte (medida no bitmap). Antes de perguntar ao cliente,
procure no desenho.

---

## Limitações do ambiente remoto

Registrado para não se repetir tentativa: o proxy de egresso bloqueia
`drive.google.com`, `at.adobe.com`, `portal.opentopography.org`,
`huggingface.co`, o CDN da OpenAI, `openstreetmap.org`,
`doisvizinhos.pr.gov.br` e — testado nesta sessão — `polyhaven.com`,
`ambientcg.com`, `api.opentopodata.org` e `open-elevation.com`. **Passa:**
`s3.amazonaws.com/elevation-tiles-prod`, que é de onde vem o relevo. Vídeo do Drive, transcrição de áudio, HDRI e textura PBR
precisam ser obtidos localmente e anexados no chat. GitHub, PyPI e o arquivo
principal do Ubuntu funcionam.

Não há GPU: o render roda em CPU, ~80 s por quadro a 25% da resolução. Render
final é trabalho de máquina local.
