# RETOMAR — noite dos três quadros, 16/08/2026

Handoff auto-contido. Para retomar em contexto novo, leia **este arquivo +
`ESTADO.md` + `DECISOES.md` D072–D088**, e nada além disso antes de começar.

O contrato da sessão é `NOITE-3-QUADROS.md` (escrito pelo Natan). A fila de
longo prazo é `FILA-CENA.md`.

---

## O que era o alvo

**Não** a cena inteira: **três quadros parados que convençam o cliente.**
As três leis, dele:

1. só existe o que está dentro do enquadramento;
2. um quadro pronto vale mais que três a 60%;
3. o 3D tem que **ganhar** da folha `real | 3D`, não só existir.

---

## Onde parou

```
Q1 portal ....... RENDERIZADO. Reprovado 2x pelo verificador, consertado 2x.
                  A 3a rodada de consertos NAO foi conferida por ninguem
                  alem de mim. -> proxima acao: 3a conferencia.
Q2 arena ........ RENDERIZADO. Reprovado 1x, 6 de 7 consertadas.
                  A 7a (cor da grama) virou PROPOSTA -- e' a hora, nao o
                  material. Sem reconferencia ainda.
Q3 pavilhao ..... NAO ABERTO, e corretamente: o gatilho do adendo exige zero
                  reprovacao em aberto nos dois primeiros.
```

**Não se renderiza o filme.** Ordem D067/D069 segue de pé. Os três quadros são
parados.

---

## Os arquivos

| o quê | onde |
|---|---|
| folha `real \| 3D` do portal | `out/heroi/Q1.jpg` |
| folha `real \| 3D` da arena | `out/heroi/Q2.jpg` |
| antes/depois da arena | `out/heroi/Q2-antes-depois.jpg` |
| as três horas de golden hour | `out/heroi/Q2-hora.jpg` |
| página para o cliente | `out/heroi/APRESENTACAO.html` (abrir do disco — imagens relativas) |
| cenas para abrir no Blender | `out/cena-heroi-q1.blend`, `out/cena-heroi-q2.blend` |
| renders 2560×1440 | `F:/heroi/Q1/final-2560.png`, `F:/heroi/Q2/final-2560.png` |
| match-frame para comparar | `F:/heroi/Q1/match-1600.png` (4:3), `F:/heroi/Q2/match-1600.png` |
| construtores | `scripts/heroi_portal.py`, `scripts/heroi_arena.py` |
| folha lado a lado | `scripts/folha_heroi.py` |
| prova do caminho de render | `scripts/prova_cycles.py` |
| configuração de render | `data/render-config.json` |
| portão a portão | `ENTREGA.md` |
| o que é proposta, não medida | `PROPOSTAS.md` |
| o que travou | `PENDENCIAS.md` |

**As referências reais:**
`E:\Projetos todos\Mapa - agroshow\WhatsApp Image 2026-08-12 at 13.15.32.jpeg`
(portal, 1448×1086) e
`out/quadros-ia/P19_arena-de-rodeio/real/2_img-9133_005.00s.jpg` (palco vazio,
3840×2160).

---

## Comandos que funcionam, como estão

```bash
BL="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
```

**Q1 — portal, entrega 16:9**
```bash
"$BL" --background --factory-startup --python scripts/heroi_portal.py -- \
  --blend out/cena-heroi-q1.blend --saida F:/heroi/Q1/final-2560.png \
  --largura 2560 --altura 1440 --samples 50 --dist 21.5 --alvo-z 3.4
```

**Q1 — match-frame 4:3, que é o que vai na folha**
```bash
"$BL" --background --factory-startup --python scripts/heroi_portal.py -- \
  --saida F:/heroi/Q1/match-1600.png --largura 1600 --altura 1200 \
  --samples 50 --dist 21.5 --alvo-z 3.4
```

**Q2 — arena, entrega e match**
```bash
"$BL" --background --factory-startup --python scripts/heroi_arena.py -- \
  --blend out/cena-heroi-q2.blend --saida F:/heroi/Q2/final-2560.png \
  --largura 2560 --altura 1440 --samples 50 \
  --dist 30 --alt 1.9 --alvo-z 6.0 --alvo-x 3.0 --desloc-x -13.0 --lente 28

"$BL" --background --factory-startup --python scripts/heroi_arena.py -- \
  --saida F:/heroi/Q2/match-1600.png --largura 1600 --altura 900 --samples 50 \
  --dist 62 --alt 2.3 --alvo-z 5.0 --alvo-x 9.0 --desloc-x -20.0 --lente 24
```

**A folha**
```bash
python scripts/folha_heroi.py --real "<foto>" --render "<render>" \
  --saida out/heroi/Q1.jpg --titulo "Q1 · Portal de entrada" --altura 780
```

**Testar outra hora de golden hour** (só no `heroi_arena.py`)
```bash
"$BL" --background --factory-startup --python scripts/heroi_arena.py -- \
  --saida F:/heroi/Q2/hora-1730.png --hora "17:30" --largura 1400 --altura 790 \
  --samples 50 --dist 30 --alt 1.9 --alvo-z 6.0 --alvo-x 3.0 --desloc-x -13.0 --lente 28
```

---

## ARMADILHAS — leia antes de rodar qualquer coisa

**1. Portão só vale com o `.venv` DO PROJETO.** O `python` do PATH é o venv do
Hermes e **não tem `cv2`**:
```bash
./.venv/Scripts/python.exe scripts/conferir_texturas.py     # certo
python scripts/conferir_texturas.py                          # morre no meio
```
E **portão dentro de pipe não reporta o próprio exit code** — eu li `EXIT=0`
logo abaixo de um traceback porque o `$?` era do `tail`. (D082)

**2. Nunca `pip install` no `python` do PATH** — contamina o agente do Hermes.

**3. PowerShell 5.1: `&&` é erro de parser.** Use `;` ou o Bash.

**4. Marcador de timeline vence `scene.camera`** (armadilha 34). Todo script que
renderiza limpa `timeline_markers` **na sessão**. A `cena-revisar.blend` tem 22.

**5. `prefs.devices` vem VAZIA até `get_devices()` ser chamado.** Sem essa
chamada o laço que liga a GPU não liga nada, em silêncio, e o render cai na CPU
(D009). `prova_cycles.py` **aborta** se nenhum OptiX ficar ativo.

**6. Asset de biblioteca NÃO entra inteiro, entra filtrado.** A coleção do Poly
Haven traz LOD0 **e** LOD1 sobrepostos, os cartões-fonte de folha e galho, e um
objeto `geometry_nodes` com origem deslocada 7,71 m — que a escala multiplica.
Sem filtro isso vira árvore dentro do vão do portal e gravetos de pé na grama.
Filtro em `heroi_portal.py:vegetacao` e `heroi_arena.py:cortina_de_arvores`.

**7. Booleano EXACT sobre face coincidente devolve lixo, sem erro na tela.**
Comeu o corpo central inteiro do portal. Monte por partes, com **6 cm de
sobreposição** entre peças vizinhas.

**8. Deslocar a câmera sem deslocar o ALVO não reenquadra — só guina.** (D087)

---

## As três regras que a noite provou

**a) Quando duas peças se encontram, UMA função decide a cota das duas.**
A mesma família de erro apareceu três vezes: pilar e telhado do pavilhão
divergindo 16–26 cm; mourão encostando rente no portal; parede e cobertura da
concha deixando 2,1 m de céu aberto. `heroi_arena.py:_cota_cobertura` é o
modelo a copiar.

**b) Olhar lado a lado e medir em pixel são instrumentos diferentes.**
Olhar pega o que está grosseiramente errado. **Medir pega o que está 20%
errado** — e 20% errado é o que faz a imagem parecer *quase* o lugar. Eu olhei o
Q1 contra a foto sete vezes e não vi nenhuma das sete divergências que o
verificador mediu.

**c) Quando um ajuste erra para os dois lados com a mesma magnitude, o
parâmetro não é o problema — a forma é.** Tentei fechar a inclinação do frontão
duas vezes mexendo em `CUMEEIRA_MEIA`: primeiro 6° raso, depois 7° íngreme. O
frontão é **assimétrico** (D086).

---

## O verificador

`.claude/agents/render3d-verificador.md` existe em disco **e só vale a partir da
próxima sessão** — o registro de agentes é lido na abertura. Nesta noite rodou
como `general-purpose` com a instrução embutida no prompt (D079).

**Nunca use o `render-agroshow` no papel**: ele é quem planeja a cena, e seria a
mesma voz conferindo o próprio plano.

Regra dura dele: **reprova sozinho, nunca aprova sozinho.** O melhor veredito
possível é "SEM DIVERGÊNCIA GROSSEIRA".

---

## O que espera decisão do Natan

1. **A hora do LOOK LOCK.** Com o sol a 10,1° (18:15, o contrato) todo chão
   horizontal recebe `sin(10,1)=0,17` do sol e o resto do céu azul. Grama sai
   com saturação **0,05** contra **0,42** da foto. Medido nas três horas:

   | hora | elevação | grama S | grama V |
   |---|---|---|---|
   | 18:15 | 10,1° | 0,05 | 0,36 |
   | 17:30 | 19,8° | 0,08 | 0,37 |
   | 17:00 | 26,4° | 0,11 | 0,38 |
   | foto, meio-dia | ~60° | 0,42 | 0,70 |

   **Subir a hora ajuda e não fecha a distância** — o albedo medido da grama é
   escuro e o AgX Punchy dessatura de propósito. Folha em `out/heroi/Q2-hora.jpg`.
   **Vale para o filme inteiro**, não só para estes quadros.

2. **Uma foto de celular da parede do portal a 2 metros.** A madeira está
   ampliada ~14× (166 px nativos → 2048): cadência, largura de tábua e junta são
   reais; a fibra fina é interpolação. É o pedido mais barato que existe aqui.

3. **`data/vegetacao.json` declara "malha compartilhada / árvore procedural"** e
   agora existem 4 assets CC0 em disco. O parágrafo `GEOMETRIA` precisa ser
   reescrito — é doutrina, não execução.

4. **Escala de textura**: só telha (2,432 m) e madeira (2,10 m) são medidas.
   Terra 8,0 / brita 2,2 / grama 4,5 / concreto 2,0 são estimadas com ±40 a 50%.
   **É um número no JSON** — trocar não exige regerar mapa.

---

## A correção que atravessa tudo

**A fotogrametria fechou** (D072). As seis tentativas sempre tinham fechado — eu
lia o submodelo `0`, que é o descarte de duas imagens, em vez do `1`.

| modelo | imagens | pontos | erro |
|---|---|---|---|
| `montagem/sparse/1` | 100/100 | 42.090 | 0,797 px |
| `montagem/sparsec/2` | 100/100 | 42.020 | 0,794 px |
| `fazendinha/sparse/1` | 150/150 | 37.730 | 0,602 px |

Todos ≤ 1,5 px → **a nuvem entra como gabarito de medida**.

**Mas o número não diz o conteúdo** (D073): a `fazendinha` tem o melhor erro do
lote e reconstruiu **o evento à noite, com a arena tomada de gente**. Erro baixo
e trilha dobrada vêm de multidão e luz darem feature demais. A nuvem que presta é
a **`montagem`** — dia, montagem do evento.

`D071`, `RETOMAR-1608-FOTOGRAMETRIA.md` e `docs/FOTOGRAMETRIA.md` já receberam
aviso de correção no topo. **Nada foi apagado.**

---

## A próxima ação, se ninguém disser o contrário

Terceira conferência do Q1 e primeira reconferência do Q2, com o verificador
separado, medindo em pixel contra as fotos. Só depois disso o Q3 pode abrir.
