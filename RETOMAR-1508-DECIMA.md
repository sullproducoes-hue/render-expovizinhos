# RETOMAR — décima sessão (15/08/2026)

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**

> Handoff da **décima** sessão. Ela não tocou na cena 3D: mexeu só no **acervo
> de quadros**. O `RETOMAR-1508-OITAVA.md` continua valendo para o estado da
> cena, e o `RETOMAR.md` para as 34 armadilhas e o histórico.

---

## Por onde ele volta

**`out/acervo/ACERVO.html`** — dois cliques. Offline, sem servidor, sem internet.

**9.980 quadros**, 173 voos, medidos um por um. Ele marca (SIM / TALVEZ / NÃO),
comenta, e o que marcou **sobrevive a fechar a página**. Antes de encerrar de
vez: **Exportar seleção (JSON)** — depois

```
.venv/Scripts/python.exe scripts/colher_selecao.py --copiar
```

devolve `out/acervo/SELECAO.md` com o **caminho absoluto**, o vídeo e o timecode
de cada escolha, e copia os JPG originais para `out/acervo/selecionados/`.

Doutrina completa em **`docs/ACERVO.md`**. As decisões em **`DECISOES.md`
D046–D056**.

---

## As três perguntas que travam mais coisa, em ordem de custo

### 1. Um terço do acervo é de outro recinto? (a mais barata, a que trava mais)

Duas sessões do mesmo dia se contradizem:

| fonte | o que diz |
|---|---|
| `data/quadros-ia.json` (sétima, manhã) | usa 12 voos `DJI_2025112*` como **âncora confirmada** |
| `docs/COMO-O-PARQUE-ESCREVE.md` (nona, noite) | *"outro recinto — autódromo oval, silos de grão… usar aquilo seria errar de cidade"* |

**São 74 voos, 3.270 quadros, 33% do acervo**, e as âncoras que caem neles cobrem
**P01, P02, P09, P10, P11, P12, P13, P14, P15, P20**.

Não desempatei. Na página vêm com selo vermelho e filtro próprio.
Prova visual em `out/acervo/_duvida-recinto.jpg`.
**Resolve com trinta segundos de olho numa folha de contato.**

### 2. "Anoitecendo depois entra a logo animada" soma ou substitui o portal?

O nome da pasta que ele criou é uma ordem de edição:

> `Fala do drone colocar como finalização e anoitecendo depois entra a logo animada`

O `IMG_0706.MOV` (21,6 s, 4K, 120 fps, com áudio) entrou no acervo com 16
quadros. Mas a restrição 6 do `ESTADO.md` diz **"plano final saindo pelo
portal"**. Sai pelo portal **e depois** anoitece, ou o portal deixa de ser o
plano final? As duas leituras cabem e uma delas quebra a restrição do cliente.

Material para a virada existe: **2.535 quadros de noite em 36 voos**.

### 3. A numeração de "Bloco" — bloqueio documentado

O `INDICE.md` da pasta de extração manda preencher a coluna **Bloco** com o
número de `docs/prompts-higgsfield.md`. **Esse arquivo não existe em lugar
nenhum.** Veio junto com o script genérico de extração. Não inventei a
numeração: criar blocos de prompt é decidir o que vai ser gerado por IA, e este
projeto não gerou nenhuma imagem (D036). A página organiza pelos **22 planos** e
pelos **19 pontos do roteiro**, que é numeração que existe e é do cliente.

---

## O que esta sessão fez no disco dele

**Extraiu os 5 vídeos que não tinham quadro nenhum** — com o `extrair_quadros.py`
dele, mesma convenção:

| vídeo | quadros | por quê importa |
|---|---|---|
| `DJI_0937_stabilized` | 14 | era a **âncora de P16** e não existia em quadro |
| `DJI_0937_stabilized_1` | 14 | era a **âncora de P18** e não existia em quadro |
| `DJI_0938_stabilized` | 12 | |
| `DJI_0938-001` | 100 | |
| `IMG_0706` | 16 | o da ordem no nome da pasta |

**Agora os 173 vídeos das duas pastas têm quadros extraídos.**

**Reconstruiu o `INDICE.md`** — e isso foi conserto de erro meu, ver D050: o
script dele **regrava o índice inteiro** a cada rodada, e uma extração avulsa
apagou as 151 seções. `scripts/refazer_indice_extracao.py` reconstruiu do disco.
Está em **347 KB, 156 seções**. Só a ordem original das seções não voltou.

**Não apagou, moveu nem renomeou nada mais.**

---

## Armadilhas novas — as três desta sessão

### 35. `cv2.imread` devolve `None` em caminho com acento, sem erro

`F:\Extração quadros expo 2025` tem cedilha e til. O `imread` do OpenCV no
Windows **não abre** e devolve `None` sem levantar exceção — parece arquivo
corrompido. O jeito certo:

```python
bruto = np.frombuffer(Path(caminho).read_bytes(), np.uint8)
img = cv2.imdecode(bruto, cv2.IMREAD_REDUCED_COLOR_2)
```

`imdecode` aceita as mesmas flags de `imread`, inclusive as `REDUCED_*`, que
decodificam o JPEG já reduzido e são **4× mais rápidas**.

### 36. Ferramenta de terceiro regrava arquivo do cliente

Ver D050. Antes de rodar script de outro fluxo sobre pasta do cliente,
`grep write_text` nele. Custa dez segundos e evitou-se um índice de 316 KB.

### 37. Duas pastas podem cair no mesmo slug — e ninguém percebe

`DJI_0953_stabilized_1` e `DJI_0953_stabilized_1_` (esta veio de
`DJI_0953_stabilized_1(1).mp4`) dão o **mesmo** `slug()`. Quatro quadros
dividiam `id` e miniatura: marcar um marcaria o outro. Achado contando
**arquivo em disco contra registro no catálogo** — 9.976 contra 9.980 —, não
por amostra.

A pergunta certa não é *"todo quadro tem miniatura?"*, é *"cada miniatura
pertence a um quadro só?"*. Hoje `mapa_de_slugs()` desambigua com md5 e
`pagina_acervo.py` **aborta** se houver `id` repetido. Ver D057.

### 38. `beforeunload` trava automação de navegador

Um `beforeunload` que pede confirmação bloqueia `page.goto` no Puppeteer, e o
erro que aparece é *"Navigation timeout of 30000 ms exceeded"* — que não diz
nada sobre diálogo. Ou se aceita o diálogo (`page.on('dialog', d => d.accept())`)
ou não se usa `beforeunload`. Neste projeto foi feito o dos dois: o aviso agora
só aparece com risco real, e a prova aceita o diálogo.

---

## Os arquivos novos

| arquivo | o que é |
|---|---|
| `scripts/acervo_quadros.py` | varre, mede, etiqueta e classifica. `--varrer` (≈16 min), `--reetiquetar` e `--reclassificar` refazem sem reler disco |
| `scripts/pagina_acervo.py` | monta a página a partir do catálogo |
| `scripts/colher_selecao.py` | lê a seleção exportada, escreve o relatório com caminhos e copia os originais |
| `scripts/provar_pagina_acervo.mjs` | **portão**: prova em Chromium de verdade que a marca sobrevive a recarregar |
| `scripts/refazer_indice_extracao.py` | reconstrói o `INDICE.md` da pasta de extração |
| `data/acervo-quadros.json` | o catálogo, 12 MB, um registro por quadro |
| `docs/ACERVO.md` | a doutrina do acervo |
| `out/acervo/ACERVO.html` + `dados.js` + `thumbs/` | a página (fora do git) |

**Rodar tudo de novo, do zero:**

```
.venv/Scripts/python.exe scripts/acervo_quadros.py --varrer
.venv/Scripts/python.exe scripts/pagina_acervo.py
node scripts/provar_pagina_acervo.mjs
```

---

## O que esta sessão NÃO fez, de propósito

- **não gerou imagem de IA** — continua valendo o D036 e a frase dele,
  *"depois crio os vídeos"*;
- **não renderizou quadro do filme** — o passo dele continua sendo aprovar os
  quadros primeiro;
- **não tocou em `build_scene.py`, `planos.json` nem em nenhum `.blend`** — as
  duas ordens abertas da oitava sessão (16:9 nativo e letreiro na superfície)
  continuam abertas, e estão no `RETOMAR-1508-OITAVA.md`;
- **não apagou a página anterior.** `out/quadros-ia/INDICE.html` tem os 44
  quadros conferidos **a olho**, que é o único julgamento humano que existe
  neste acervo, e eles entram no novo como âncora.

---

## Onde o acervo está fino, e é onde o roteiro pede mais

| plano | quadros com local | observação |
|---|---|---|
| **P17 Veículos e Motos Náuticas** | **0** | nunca teve âncora |
| **P22 Saída pelo portal** | **0** | só a foto do portal, que não é vídeo |
| P12 Pista de Julgamentos | 1 | única âncora cai num voo de 10 quadros em 3 s |
| **P15 Fazendinha (órbita)** ★ | 1 | idem — e é diferencial |
| **P08 Café Colonial** ★ | 10 | |
| **P06 Mercado do Produtor** ★ | 17 | |
| **P14 Fazendinha** ★ | 42 | |
| **P19 Arena de Rodeio** ★ | 44 | |

★ = os quatro diferenciais, que o cliente pediu com **mais tempo de tela**.
Isso não contradiz a **D037** — mede o tamanho dela.

E existem **8.764 quadros sem local**, que é onde provavelmente está o material
desses planos. Achá-lo é trabalho de olho, e a página existe para isso: filtre
por **fim de tarde**, ordem **melhor primeiro**, e vá por voo.
