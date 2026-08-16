# PROPOSTAS — o que é escolha minha, e não medida

Regra da casa: **o que não desce de medida ou de doutrina declarada é
proposta, e é apresentado como proposta.** Este arquivo existe para você não ter
que adivinhar o que foi medido e o que foi decidido por mim.

Nada aqui está errado. Está **em aberto**, esperando você julgar.

---

## Do quadro Q1 — o portal

| item | o que fiz | por que é proposta |
|---|---|---|
| **profundidade da fachada** (3,2 m) | escolhido | **não é medível em foto frontal.** A única imagem do portal é frontal, e profundidade não aparece nela. Tudo o mais do portal foi medido em pixel; isto não |
| **fonte do letreiro** | ArchivoNarrow-Bold, comprimida em X | a foto mostra letra condensada de caixa alta; a família exata não dá para identificar em 1448 px. A largura e a altura **estão medidas** — a família não |
| **cor da madeira** | 0,21 / 0,11 / 0,055 | é o valor **declarado** em `build_scene.py:186`, não medido: o portal não aparece em nenhum dos 173 vídeos, então não há madeira em `materiais-medidos.json`. A textura foi normalizada para esse alvo |
| **portão de ferro ao fundo** | barras verticais + arco | a foto mostra portões brancos com desenho em arco atrás dos vãos, mas em contraluz. O ritmo das barras é leitura minha |
| **espécie da árvore** | `island_tree_01` (Poly Haven, CC0) | a árvore da foto não é identificável. Escolhi porte e copa, não espécie |

---

## Do quadro Q2 — arena e palco fixo

| item | o que fiz | por que é proposta |
|---|---|---|
| **azul da base** e **claro da parede** | 0,020/0,085/0,30 e 0,72/0,72/0,70 | **já estava declarado como proposta** em `estruturas.py`: o vídeo `1 (4)` é golden hour, e o método do céu (D018) só vale em dia encoberto. Ninguém mediu essa cor |
| **balanço da cobertura** (5,20 m) | lido na foto contra a profundidade da planta | leitura em perspectiva de foto grande-angular, não medida frontal. Carrega erro maior que as do portal |
| **largura da caixa cênica** (13,60 m) | lida na foto | a planta dá o footprint inteiro (20,28 m); a separação entre base e caixa é leitura minha |
| **geometria da treliça** | 5 planos, 12 nós, diagonal alternada | a foto mostra que **existe** treliça espacial e mostra a silhueta dela. A contagem de nós e a direção das diagonais são reconstrução plausível, não contagem |
| **quadro de treliça do topo** | 14 módulos, 1,05 m de altura | idem |

---

## A maior delas: a hora do LOOK LOCK

**Medido, não achado** (D084). Com o sol a 10,1° (18:15, o contrato), toda
superfície **horizontal** recebe `sin(10,1) = 0,17` do disco solar e quase todo o
resto do céu, que é azul. O chão inteiro dessatura e esfria.

| hora | elevação do sol | grama · saturação | grama · valor |
|---|---|---|---|
| **18:15** — o contrato | 10,1° | **0,05** | 0,36 |
| 17:30 | 19,8° | 0,08 | 0,37 |
| 17:00 | 26,4° | 0,11 | 0,38 |
| a foto, meio-dia | ~60° | **0,42** | **0,70** |

Folha com as três lado a lado: `out/heroi/Q2-hora.jpg`.

**A honestidade do número: subir a hora ajuda e não fecha a distância.** Sobra
gap por duas razões declaradas — o albedo medido da grama é escuro (em sRGB dá
V≈0,39, e nenhuma luz faz uma superfície dessas chegar a 0,70 sem estourar), e o
AgX Punchy dessatura de propósito.

**Isto vale para o filme inteiro, não para este quadro.** O parque é todo chão
horizontal. As alternativas com o número já estavam escritas em `data/luz.json`
desde 14/08; o que faltava era alguém medir o efeito.

---

## Do que atravessa os dois

| item | o que fiz | por que é proposta |
|---|---|---|
| **escala de textura** de terra, brita, grama e concreto | 8,0 / 2,2 / 4,5 / 2,0 m | só **telha (2,432 m)** e **madeira (2,10 m)** têm `lado_m` medido. Os outros quatro são estimados por objeto de referência, com ±40 a 50%. **É um número no JSON** — trocar não exige regerar mapa |
| **hora do golden hour** (18:15) | do contrato `data/luz.json` | está declarado lá como PROPOSTA desde 14/08. As alternativas com o número estão no mesmo arquivo: 17:30 deixa o recinto todo legível; 18:45 põe metade da arena na sombra |
| **mistura de figuras estilizadas com árvores fotogramétricas** | ainda não entrou em quadro | as 12 figuras do Quaternius são low-poly sem textura; as árvores são fotogrametria. A 24 m provavelmente passa, mas é **decisão estética**, e estética é sua |

---

## O que NÃO é proposta — está medido, e o número está em disco

- toda a geometria do portal, a 47,6 px/m, com âncora no vão de passagem;
- a cor de terra, brita, grama, concreto e telha — do footage do próprio recinto,
  com erro do albedo < 0,5% contra a medida;
- o passo da onda da telha: 2,432 m, por autocorrelação;
- a nuvem de pontos: 42.090 pontos, erro de reprojeção de 0,80 px;
- o custo de render: 7,5 s a 960×540 na 4060;
- o vão entre pilar e telhado dos pavilhões: 16 a 26 cm.

---

## Q3 · a boca do Pavilhão 1 — o que aqui é proposta

Construtor: `scripts/heroi_pavilhao.py`. Referência real:
`out/quadros-ia/P03_pavilhao-1-industria-comercio-e-prestacao-de/real/2_img-9131-004_176.00s.jpg`.

| item | o que fiz | por que é proposta, e não medida |
|---|---|---|
| **cor da face de baixo da água** | albedo 0,44 cinza neutro | `MAT_TELHA` em `materiais-medidos.json` está em **(1,0 / 1,0 / 0,95)** — foi amostrada na água **virada para o sol** e saiu grampeada no branco. Serve para a telha vista de cima; **não serve** para a face de baixo, que é o que este quadro mostra. E aqui ela é a maior superfície de rebote da cena: no teste `t01`, com 0,185, o interior inteiro fechava em preto |
| **azul do pilar** | (0,021 / 0,038 / 0,072) | não há medida de azul no acervo. Mesma situação do azul da concha (D024) |
| **ferrugem da treliça** | (0,128 / 0,052 / 0,036) | idem |
| **tijolo aparente** | (0,155 / 0,062 / 0,045) | idem. E **não há textura de tijolo** em `assets/textura/` — a parede entra lisa |
| **piso** | `MAT_SAIBRO` medido (brita) | na foto o piso do Pavilhão 1 é **asfalto escuro**, e asfalto **não tem medida** no acervo. A brita é a medida mais próxima que existe, e ela puxa o chão para o marrom. **Ou se aceita, ou se mede o asfalto num quadro do footage** |
| **pé-direito 4,60 m + treliça 1,05 m** | soma 5,65 m | `estruturas.py:68` declarava 5,0 m até o beiral com ~20% de incerteza. A partição em pé-direito livre + altura de treliça é **proporção lida na foto**, não trena |
| **13 pórticos, passo de 4,32 m** | ritmo lido na foto | o passo não está cotado em lugar nenhum. Com 9 (6,5 m) o teto lia como plano vazio |
| **eixos locais, rumo não aplicado** | comprimento em Y, boca em −Y, lado aberto em −X | o footprint de `PAVILHÃO 1` traz `rumo_graus: 90,0` **com `rumo_confiavel: false`**. Aplicar um rumo em que a própria planta não confia só mudaria de que lado o sol entra pela boca — trocaria a luz do quadro por um número que não se sustenta |

**A hora do LOOK LOCK pesa mais aqui do que nos outros dois.** O Q3 é um
interior coberto: com o sol a 10,1° do contrato, quase nada entra pela boca e o
fundo do pavilhão vira túnel escuro. As três horas foram rodadas para o mesmo
quadro — `F:/heroi/Q3/hora-1815.png`, `hora-1730.png`, `hora-1700.png`.
