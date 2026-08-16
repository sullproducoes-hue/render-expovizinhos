# O acervo de quadros — como está catalogado e como se usa

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Levantamento de 15/08/2026, feito por ordem dele:

> *"faça novamente o levantamento eu atualizei os arquivos de uma forma que eu
> possa avaliar e comentar e saber depois onde esta as que eu selecionei"*

---

## Abra isto

**`out/acervo/ACERVO.html`** — dois cliques, offline, sem servidor e sem internet.

| tecla / clique | o que faz |
|---|---|
| clique na foto | abre o **JPG original** do disco, resolução nativa |
| setas ← → | anda pelos quadros do filtro atual |
| **S / T / N** | marca SIM, TALVEZ, NÃO sem tirar a mão do teclado |
| Esc | fecha o visor |
| clique no caminho | copia o caminho do arquivo |

A marca e o comentário são gravados **a cada clique** no armazenamento do
navegador. Fechar a aba não perde. **Antes de encerrar de vez, clique em
"Exportar seleção (JSON)"** — é o arquivo que traz a escolha de volta para o
projeto, e é o único que sobrevive a uma limpeza de navegador.

Depois de exportar:

```
.venv/Scripts/python.exe scripts/colher_selecao.py            # relatório
.venv/Scripts/python.exe scripts/colher_selecao.py --copiar   # + os JPG originais
```

Sai `out/acervo/SELECAO.md` — cada quadro escolhido com **caminho absoluto,
vídeo de origem e timecode**, agrupado por plano. É a resposta literal do
*"saber depois onde está"*.

---

## O que foi varrido

| raiz | pastas | quadros |
|---|---|---|
| `F:\Extração quadros expo 2025` | 156 | 7.940 |
| `E:\…\Brutos Expo\agroshow extrator somente\extracao` | 17 | 2.040 |
| **total** | **173** | **9.980** |

Cobertura dos vídeos: **173 arquivos de vídeo** existem nas duas pastas, e
depois desta sessão **todos os 173 têm quadros extraídos**. Quatro não tinham
(`DJI_0937_stabilized`, `DJI_0937_stabilized_1`, `DJI_0938_stabilized`,
`DJI_0938-001`) e foram extraídos com o próprio `extrair_quadros.py` dele, na
mesma convenção. Dois deles eram justamente as âncoras de P16 e P18.

Entrou também o **`IMG_0706.MOV`**, que estava numa pasta cujo nome é uma ordem
de edição — ver abaixo.

---

## A procedência está resolvida: é tudo Dois Vizinhos — fechado em 15/08 por GPS

> Esta seção descrevia uma dúvida aberta sobre 33% do acervo. Ela foi **fechada
> por medida** na décima primeira sessão de 15/08. O texto antigo continua no
> git; o que vale é o que está abaixo.

Duas sessões do mesmo dia diziam coisas opostas sobre as pastas `DJI_2025112*`:
a sétima usava **12 desses voos como âncora confirmada**, e a nona escreveu que
eles mostram *"outro recinto — autódromo oval, silos de grão… usar aquilo seria
errar de cidade"*. Eram **71 pastas e 2.770 quadros**, cobrindo **dez dos vinte
e dois planos**, entre eles a Fazendinha.

**Nenhuma das duas sessões abriu o metadado.** O drone gravou GPS: a DJI escreve
latitude e longitude amostra a amostra num stream `djmd` dentro do próprio MP4,
e `_triagem/telemetria/*.resumo.json` já tinha a mediana de cada voo desde
14/08. Faltava cruzar com a coordenada do recinto.

`scripts/provar_recinto.py` cruza, e o resultado não deixa margem:

| | |
|---|---|
| pastas sob dúvida | **71** |
| com GPS gravado, **dentro** do recinto | **60** pastas · **2.440** quadros |
| com GPS gravado, **fora** | **0** |
| distância ao ponto de referência | **mín. 24 m · máx. 387 m** (terreno de 808 × 454 m) |
| sem GPS próprio | 11 pastas · 330 quadros — exports estabilizados, metadado perdido |

**E as duas feições que levantaram a dúvida aparecem dentro de voos com GPS
confirmado:** o **oval** está em `DJI_20251126155520_0054_D`, a **168 m**, e os
**silos de grão** em `DJI_20251129182345_0168_D`, a **336 m**. Não são de outra
cidade — são o próprio recinto e a cooperativa vizinha. O
`DJI_20251127184025_0104_D`, que a nona sessão leu como "recinto dentro de uma
cidade", está a **79 m** do ponto de referência.

As 11 pastas sem GPS (voos 0034–0046, manhã de 26/11) mostram a **mesma feira**,
o **mesmo horizonte** e o **mesmo oval** das que têm GPS, do mesmo drone, no
mesmo dia, com numeração intercalada com a de 0053/0054, que estão provadas.
Elas continuam marcadas na página — não com selo vermelho de dúvida, mas com a
etiqueta **SEM GPS PRÓPRIO**, porque medido e não medido não se misturam.

**Nada foi descartado.** Custo evitado: 2.770 quadros e dez planos.

Provas: `data/recinto-gps.json` · `out/prova-recinto-gps.jpg` ·
`out/prova-recinto-provados.jpg` · `out/prova-recinto-sem-gps.jpg` ·
`DECISOES.md` D061.

---

## O que é medido, e o que é receita

Toda medida é por pixel, feita uma vez sobre cada um dos 9.980 quadros
(`scripts/acervo_quadros.py`). Nenhuma é opinião:

| medida | como |
|---|---|
| **nitidez** | variância do laplaciano, sobre a imagem normalizada a **960 px de largura** — sem normalizar, 4K e 1080p não se comparam |
| **luma / desvio** | média e desvio do canal de luminância, 0–255 |
| **estouro / escuro** | % de pixel acima de 250 e abaixo de 10 |
| **dhash** | assinatura de 64 bits (9×8, comparação com o vizinho da direita) |
| **céu** | % de pixel claro no terço de cima do quadro |
| **hora do voo** | o carimbo da câmera no nome do arquivo — `DJI_20251126185022_…` = 26/11/2025 às 18:50 |

A **nota** de 0 a 100 **não é medida, é receita** — está escrita em
`_criterio` dentro de `data/acervo-quadros.json` e pode ser discutida:

```
nota = 55·(percentil de nitidez dentro do próprio voo)
     + 20·(exposição dentro da faixa do período)
     + 15·(contraste)
     + 10·(1 − estouro)
     × 0,45 se "fraco"   × 0,80 se "parecido"
```

O percentil é **dentro do voo**, não global. Voo estabilizado e voo cru têm
níveis de detalhe muito diferentes, e comparar entre eles enterraria voos
inteiros por causa do codec, não do conteúdo.

### Três etiquetas, e nenhuma apaga nada

| etiqueta | quantos | o que quer dizer |
|---|---|---|
| **bom** | 7.242 | passou em tudo e é o representante do seu trecho |
| **parecido** | 2.472 | quase idêntico a outro quadro do mesmo voo (dhash a ≤ 6 bits de 64) |
| **fraco** | 266 | preto, chapado, estourado acima de 25%, ou dos mais borrados do próprio voo |

Os 2.738 etiquetados continuam no catálogo e continuam na página — a etiqueta
só muda a ordem e o filtro padrão. **O motivo de cada etiqueta está escrito no
próprio registro**, quadro a quadro. `nada se apaga`.

Os "parecidos" são agrupados em **trechos**: cada trecho tem um representante,
que é o quadro **mais nítido** dele. A comparação é sempre contra a âncora do
trecho, nunca contra o quadro anterior — encadear pelo anterior deixa um giro
lento de drone virar um trecho só e engolir plano diferente.

### Período: o carimbo da câmera vence o brilho

| período | quadros |
|---|---|
| dia (6h–17h) | 2.900 |
| **fim de tarde (17h–19h)** | **4.545** |
| noite (≥19h) | 2.535 |

Isto começou errado e foi corrigido dentro da própria sessão. A primeira versão
classificava período pelo **brilho mediano do voo** — e 13 voos gravados entre
**21h e 23h** saíam como "crepúsculo", porque noite de evento com iluminação
artificial forte tem o mesmo brilho de um fim de tarde. A hora do arquivo
distingue, e é medida da própria câmera. Onde o nome não carrega hora (95 dos
173 voos, os `DJI_09xx` e os `1 (N)`), o brilho volta a valer, e o registro diz
qual dos dois foi usado (`periodo_de_onde`).

Isso importa porque `data/luz.json` declara a hora do filme em **18:20–18:55** —
a faixa "fim de tarde" é, literalmente, a luz do filme.

### 2.116 quadros estão EM PÉ

Um quinto do acervo (**51 dos 173 voos**) foi gravado vertical: 1512×2688,
1080×1920, 1508×2680, 2160×3840. O filme é deitado. Quadro em pé não serve de
placa sem corte pesado — a página tem filtro próprio para isso, e a miniatura
**não corta** o quadro justamente para ele conseguir julgar.

---

## Local: o que está classificado e por quê tão pouco

**Nenhum quadro foi reconhecido por conteúdo.** Não há visão computacional aqui,
e forçar um local errado custa mais caro que deixar sem — o material é venda de
espaço físico.

| origem | quantos |
|---|---|
| **âncora** — o quadro mais próximo de uma escolha feita à mão em 15/08 | 40 |
| **perto da âncora** — mesmo voo, até 12 s de distância, ninguém olhou | 1.182 |
| **não classificado** | 8.764 |

Os 8.764 carregam uma **sugestão**: quais locais aquele *mesmo voo* toca em
algum instante. Sugestão não é classificação, e a página diz isso na cara.

Uma âncora marca **um** quadro, o mais próximo dela no tempo. A primeira versão
marcava tudo dentro de ±3 s e produzia 498 "âncoras" — em voos com 100 quadros
em 2 segundos, uma escolha à mão virava 40. Era mentira estatística.

### Duas contradições herdadas do catálogo de 15/08

O `data/quadros-ia.json` dá o **mesmo instante do mesmo vídeo** a dois locais
diferentes:

| vídeo, instante | reivindicado por |
|---|---|
| `DJI_20251127211745_0128_D` @ 0,5 s | **P02 Portal** e **P14 Fazendinha** |
| `DJI_0961_stabilized` @ 11 s | **P18 Área de Shows** e **P19 Arena de Rodeio** |

Pode não ser erro — um aéreo aberto mostra os dois lugares no mesmo quadro. Mas
para classificar é ambíguo, e quem desempatou foi a ordem de leitura, o que não
é critério. **Fica registrado como pendência de conferência a olho.**

### Dois planos com ZERO quadro

| plano | por quê |
|---|---|
| **P17 Veículos e Motos Náuticas** | nunca teve âncora — nem no levantamento de 15/08 |
| **P22 Saída pelo portal** | a única referência é a foto do portal, que não é vídeo |

E **P12 Pista de Julgamentos** e **P15 Fazendinha (órbita)** têm **um quadro
cada** — porque a única âncora de cada um cai num voo de 10 quadros em 3
segundos. Material fino, e os dois estão entre os voos cuja procedência foi confirmada por GPS em 15/08.

E os quatro diferenciais, que são os planos com **mais tempo de tela** no
roteiro, seguem sendo os de material mais fino:

| diferencial | quadros com local atribuído |
|---|---|
| P19 Arena de Rodeio | 44 |
| P14 + P15 Fazendinha | 43 |
| P06 Mercado do Produtor | 17 |
| P08 Café Colonial | 10 |

Isso não contradiz a **D037** — reforça. Os quatro continuam `nao_confirmado`
por falta de placa em quadro.

---

## A ordem que estava escrita num nome de pasta

```
E:\Projetos todos\Mapa - agroshow\Brutos Expo\Vídeo IA AGROSHOW 2026\
  Vídeo IA AGROSHOW 2026\
    Fala do drone colocar como finalização e anoitecendo depois entra a logo animada\
      IMG_0706.MOV
```

O nome da pasta é instrução de edição dele, e está tratada como ordem:

1. o **IMG_0706** entra como **finalização**;
2. o filme **anoitece** no fim;
3. depois entra a **logo animada**.

O arquivo: 21,6 s, 3840×2160, HEVC, **120 fps**, com áudio. Foi extraído em 16
quadros e está no acervo, pasta `IMG_0706`.

**Isso bate de frente com uma restrição do briefing** e precisa da palavra dele:
o cliente pediu *"plano final saindo pelo portal"*, e o `ESTADO.md` trata isso
como restrição de rejeição. Anoitecer + logo animada pode ser **depois** do
plano do portal, ou **no lugar** dele. Não arbitrei. **Pergunta aberta.**

O que ajuda: os **2.535 quadros de noite**, em 36 voos, existem e estão
medidos — a virada para a noite tem material real. Os voos noturnos com mais
material aproveitável são `DJI_20251126210515_0014_D` (147 bons), `DJI_0974`
(146), `DJI_0968-009` (144) e `DJI_0979-011` (135).

---

## Bloqueio: `docs/prompts-higgsfield.md` não existe

O `INDICE.md` da pasta de extração manda preencher a coluna **Bloco** com *"o
número do bloco de `docs/prompts-higgsfield.md`"*. **Esse arquivo não existe em
lugar nenhum** — nem em `render-expovizinhos/docs/`, nem em `Brutos Expo`, nem
em `E:\I.A Edit`. Foi procurado por nome em toda a árvore.

O texto veio junto com o `extrair_quadros.py`, que é um script genérico
reaproveitado; a numeração que ele pressupõe nunca foi criada para este job.

**Consequência:** a coluna Bloco não tem fonte de numeração e continua vazia. O
que existe de numeração real neste projeto são os **22 planos** (`data/planos.json`)
e os **19 pontos do roteiro** (`docs/BRIEFING.md`) — e é por eles que a página
organiza. Se ele quiser a numeração de blocos do Higgsfield, ela precisa ser
criada primeiro, e é decisão dele: **prompt de IA é geração, e o projeto ainda
não gerou nenhuma imagem** (D036).

---

## Os arquivos

| arquivo | o que é |
|---|---|
| `scripts/acervo_quadros.py` | varre, mede, etiqueta e classifica. `--varrer` mede tudo (≈15 min); `--reetiquetar` refaz regra sem reler disco; `--reclassificar` refaz só o local |
| `scripts/pagina_acervo.py` | monta a página a partir do catálogo |
| `scripts/colher_selecao.py` | lê a seleção exportada e escreve o relatório com caminhos |
| `scripts/provar_pagina_acervo.mjs` | prova em navegador de verdade que a marca sobrevive a recarregar |
| `scripts/refazer_indice_extracao.py` | reconstrói o `INDICE.md` da pasta de extração a partir do disco |
| `data/acervo-quadros.json` | o catálogo, 12 MB, um registro por quadro |
| `out/acervo/ACERVO.html` | **a página** |
| `out/acervo/thumbs/` | 9.980 miniaturas de 440 px (≈170 MB, fora do git) |

### Isto supera o levantamento anterior em cobertura, não em julgamento

`out/quadros-ia/INDICE.html` (15/08, manhã) olhou **44 quadros escolhidos à
mão**, com o porquê de cada um escrito. Aqueles 44 continuam sendo os únicos
**conferidos por olho** neste projeto, e entram aqui como âncora.

O levantamento novo cobre **9.980** e não conferiu nenhum a olho. São coisas
diferentes e as duas ficam: a página antiga não foi apagada, e o
`data/quadros-ia.json` continua sendo a fonte das âncoras.
