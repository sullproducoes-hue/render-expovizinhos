# RETOMAR — o letreiro virou superfície (15/08/2026)

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**

> Handoff da frente de **letreiros e proporção**. Corre em paralelo ao
> `RETOMAR-1508-DECIMA.md`, que é a frente do **acervo de quadros** — as duas
> não se cruzam em nenhum arquivo. Decisões novas: `DECISOES.md` **D044, D045,
> D059, D060**.

---

## Estado em uma linha

As duas ordens que estavam pendentes no `RETOMAR-1508-OITAVA.md` foram
executadas. **Os 16 letreiros passam nos dois portões**, e o defeito dos 9
cortados acabou. Arquivo vivo: **`out/cena-1508c.blend`**. Stills em
`out/entrega-1508c/planos/`.

---

## O que ele mandou, e o que virou

### 1. 16:9 nativo (D044)

*"sobre o painel de led eu vou exportar em 16:9 não se preocupa."* Perguntado se
era render nativo ou master 2:1 reencaixado: **nativo**. Master agora é
**2560 × 1440**, escolhido por custo — 3,69 Mpx contra os 3,81 Mpx do 2760×1380,
a troca de proporção sai de graça em tempo de render.

**A armadilha que isso abre:** a régua de 8%/4% usa o **sensor vertical**, que
sai da proporção — 18,0 mm em 2:1, **20,25 mm em 16:9**. Quem trocar só
`resolution_y` entrega letreiro 12,5% pequeno demais, calado. `letreiros.py`
agora lê a proporção da cena; o `ESTADO.md` foi corrigido.

### 2. A letra vai na superfície (D045)

*"inclui a letra embutida no painel usa as imagens extraídas."* As imagens foram
lidas — 17 clipes do parque vazio e 152 pastas de quadros do evento montado.
Levantamento em **`docs/COMO-O-PARQUE-ESCREVE.md`**, prova em quadro em
**`out/referencia-letreiros/como-o-parque-escreve.jpg`**.

O parque tem seis modos de escrever e **em nenhum deles a letra flutua**.
Perguntado como aplicar nos 16, ele escolheu **pelo lugar**. O modo de cada um
está declarado no campo `suporte` de `data/letreiros.json`, com o objeto da cena
nomeado (armadilha 38) e o motivo escrito quando não é óbvio.

| modo | onde é usado hoje |
|---|---|
| `letra_no_painel` | P03, P05, P07, P08 — faixa na fachada, letra por cima |
| `chapa_na_parede` | nenhum ainda — a referência C espera plano que olhe o camarote |
| `placa_suspensa` | nenhum ainda — **é o modo certo para o portal**, ver D059 |
| `painel_plantado` | os outros 11 — último recurso, e é o único que gira para a câmera |

---

## O que estava errado de verdade nos 9 letreiros (D060)

O handoff anterior culpava o portal ter mudado de lugar. **Medido, é outra
coisa, e a conta fecha exata.**

A `aproximacao = 0.45` puxava o letreiro na direção da câmera para tirá-lo de
trás das árvores. Num **push-in**, isso põe o objeto no caminho: no P02 a câmera
fecha de 42 m para 24 m do alvo, o letreiro estava a 18,9 m do alvo, e a câmera
passava a **5 m dele**. Dimensionado para 23 m, lido a 14 m → 138% da largura.

Os nove se separam em dois grupos, e os dois grupos batem:

- **push-in** — P02, P06, P08, P14, P22
- **sobrevoo com alvo que viaja** — P09, P11, P16, P18 (a mira anda até 45 m
  durante o plano, e o letreiro plantado ficava para trás)

### Os três portões que passaram a existir

| portão | o que pergunta | onde |
|---|---|---|
| **teto** | a prancha inteira cabe em 90% do quadro no instante mais próximo? | `letreiros.py` |
| **obliquidade** | a fachada está de esguelha? Acima de **65°** reprova | `letreiros.py` |
| **janela** | ele fica **≥ 2 s** em quadro? | `letreiros.py`, medindo com `world_to_camera_view` |

O piso de 8% continua valendo — ele só nunca tinha teto, e é por isso que
passava verde com o letreiro estourando a borda.

**`letreiros.construir` roda DEPOIS das câmeras agora.** Enquanto rodava antes,
a única coisa mensurável era distância, e distância não vê a mira viajar.

**O letreiro acende só no trecho em que cabe.** As chaves de visibilidade saem
da janela medida, não do plano inteiro.

---

## A pergunta que ficou aberta, e é a única (D059)

**O portal e as câmeras de P02/P22 apontam para lugares diferentes — 77°.**

| o quê | direção |
|---|---|
| fachada do `PortalCeleiro` (rumo 73° aplicado ao vão) | 163° / 343° |
| câmera do P02 / P22 | 60° / 240° |
| estrada de asfalto dele, junto ao portal | 34° / 214° |

O comentário do próprio `RUMO_PORTAL = 73.0` diz *"de frente para quem chega"* —
a intenção escrita é que 73° seja a direção **encarada**, e as duas câmeras
foram escritas nessa convenção. `estruturas.portal()` aplica o rumo ao **vão**,
e a fachada acaba 90° fora.

**Não desempatei.** Girar o portal mexe em geometria que ele olhou; girar a
câmera reescreve a abertura e o fechamento do filme. Fiz a terceira: P02 e P22
saíram para `painel_plantado`, passam nos portões, e as duas frases **leem
inteiras** — nos stills de 15/08 elas saíam cortadas nas duas bordas.

`data/letreiros.json` guarda `proposta_em_aberto` nos dois: voltar para a tábua
pendurada assim que ele decidir.

---

## O que os quadros mostram e os números não mostram

Conferido em `out/entrega-1508c/contato-letreiros.jpg`.

**Leem bem:** P02, P04, P06, P10, P11, P16, P19, P20, P22.

**Comprometidos por enquadramento que já era assim antes de eu mexer** —
conferido contra `out/entrega-1508/planos/` da sessão anterior, mesmo defeito
nos dois: **P07, P08, P09 e P20 têm o quadro tomado por telhado branco ou
parede de árvore**, e **P18 e P14 têm árvore na frente do letreiro**. Não é do
letreiro: é a câmera daqueles planos. **Nenhum portão pega isso** — os três
medem se o letreiro cabe, não se o plano mostra alguma coisa.

Isso é trabalho de reenquadramento, é decisão dele, e não entrou aqui.

---

## Comandos

```bash
python scripts/letreiros.py --conferir
```

```bash
cd "E:\I.A Edit\render-expovizinhos" && "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python scripts/build_scene.py -- --out out/cena-1508c.blend
```

```bash
cd "E:\I.A Edit\render-expovizinhos" && "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" out/cena-1508c.blend --background --python scripts/conferir_letreiro_no_quadro.py
```

`build_scene.py --letreiros-so-avisam` não aborta no portão. É para montar a
cena que **mostra** o defeito, e ela sai carimbada com `letreiro_reprovado` em
cada objeto. Não é entrega.

---

## Armadilhas novas (somam às 40)

**41. `text_boxes[0].width` está em unidade de mundo, não em em.** Medido no
Blender 5.2: `size=2` com caixa 20 dá bloco de 18,18 m; `size=1` com caixa 10 dá
9,09 m. É isso que dá largura máxima cumprível ao letreiro.

**42. A caixa de texto nasce na origem e cresce para um lado.** `align_x=CENTER`
centra as linhas DENTRO da caixa, não a caixa no objeto. Pôr a origem no meio do
painel deslocava o texto inteiro meia largura para a direita — e era isso, não a
câmera, que jogava metade dos letreiros para fora da borda.

**43. Objeto escondido não é avaliado pelo depsgraph, e a matriz que sobra é
velha.** O portão media quadro apagado e devolvia *57.929% da largura*. Pular
objeto com `hide_render`.

**44. Constraint só existe depois que o depsgraph avalia.** Lendo
`cam.matrix_world` cru depois de `frame_set`, a posição vem certa e a **mira vem
do quadro anterior** — o bastante para inventar "atrás da câmera" num letreiro
que está na frente. Usar `cam.evaluated_get(depsgraph)`.

**45. Caixa alinhada ao mundo mente em objeto girado.** `_fachada` usava a AABB
e o portal está a 73°: dava 3,2 m de largura onde o portal tem 24, e a frase do
P02 quebrava em seis linhas numa tábua de 7 m. Medir no espaço local.

**46. Portão de enquadramento não vê intersecção.** No P11 a prancha nascia
dentro do telhado: cabia no quadro, passava verde, e o still mostrava a segunda
linha serrada pela cumeeira. Quem viu foi o quadro, não o número.

---

## Próximos passos

1. **Decidir o portal** (D059) — girar o portal, girar as câmeras de P02/P22, ou
   deixar como está. É o que devolve a tábua pendurada.
2. **Reenquadrar P07, P08, P09, P18, P20** — o quadro é telhado ou árvore, e era
   assim antes destes letreiros.
3. Re-render dos 22 em escala cheia, depois que 1 e 2 fecharem.
4. Só então promover `out/cena-1508c.blend` para `out/cena.blend`.
