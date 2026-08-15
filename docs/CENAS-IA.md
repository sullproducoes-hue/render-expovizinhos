# Cenas para IA — o Plano A, operável

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Escrito em 15/08/2026, respondendo à ordem: *"preciso gerar as cenas no flow
para posteriormente animar, ou no flow ou no higgsfield mas não posso cometer
erros o lugar tem que ser exatamente o lugar onde será o agroshow, preciso
colocar as tendas nas posições reais, criar o vídeo como o Tega falou"*.

Isto fecha a pendência **14b** do `RETOMAR.md`: **é o Plano A.**

---

## A regra única, e ela é o que garante o lugar

> **Nenhum clipe é texto-para-vídeo. Todo clipe é quadro-para-vídeo, com os
> DOIS extremos renderizados da cena medida.**

Texto-para-vídeo inventa um parque de exposições genérico — é exatamente o modo
de falha que você nomeou. Descrever o parque em palavras não resolve: quanto
mais detalhe se escreve, mais a IA compõe **um** parque, e nunca **este**.

O que resolve é não deixar a escolha na mão dela. Cada clipe recebe o primeiro e
o último quadro renderizados da planta medida. A IA não decide onde ficam as
coisas: ela preenche o movimento entre dois quadros que **já são** o lugar
certo. Ela põe pele nas figuras, pelo no gado, poeira na roda e vento na lona.
A posição nunca entra em disputa.

**E a decupagem já entregava isso de graça.** Cada um dos 22 planos declara
câmera de início e de fim desde 14/08. "Primeiro e último quadro" é literalmente
o que o *Frames to Video* do Flow pede.

Consequência direta, e é a parte contraintuitiva: **o prompt não descreve onde
as coisas estão.** O quadro já diz, com medida. Repetir em palavra é convidar a
IA a discordar do quadro — e quando ela discorda, quem ganha é o texto.

---

## Os números

```
plataforma FLOW ....... 29 clipes · 51 quadros-guia · 166 s de filme
plataforma HIGGSFIELD . 23 clipes · 45 quadros-guia · 165 s (com 4 ressalvas)
render do Plano A ..... 51 quadros = 1,1% dos 4.635 do filme
custo .................. ~8 min de render, contra as 12,9 h do Plano B
```

**É esse o argumento do Plano A**, e ele não é de qualidade — é de aritmética.
O render local do filme inteiro custa 12,9 h e entrega gente proxy. O render dos
quadros-guia custa 8 minutos e entrega a mesma geometria medida, para a IA
vestir. Regenere os números com:

```bash
python3 scripts/cenas_ia.py --conferir
python3 scripts/cenas_ia.py --plataforma higgsfield --conferir
```

---

> **Decidido em 15/08:** *"quero fazer no flow então"* e *"o filme fica 12 s mais
> longo pode ser, não tenho limite de tempo"*. Então: **Flow**, e o filme fica
> com **166 s**. Nenhum plano precisou de ajuste de câmera — os 22 entraram na
> grade com a velocidade dentro da faixa.

## Flow ou Higgsfield? — Flow, e o motivo é medido

| | Flow (Veo 3.1) | Higgsfield (Kling 2.6 / 3.0) |
|---|---|---|
| grade de duração | **4, 6, 8 s** | 5, 10 s |
| primeiro+último quadro | **Frames to Video** | start/end frame |
| aspectos | 16:9, 9:16 | 16:9, 9:16, 1:1, 21:9 |
| resolução | 720p, 1080p, **4K** | 1080p |
| planos que **não** cabem | **nenhum** | **4** |

**A grade de 5/10 s do Higgsfield não hospeda 4 dos 22 planos.** Não é
preferência: é medição. Um plano de 5,5 s comprimido a 5,0 s acelera a câmera; o
mesmo plano esticado a 10 s a deixa lenta demais. Nos quatro casos as duas
opções caem fora da faixa cinematográfica de drone:

| plano | dur. | a 5 s | a 10 s | faixa |
|---|---|---|---|---|
| P04 Praça de Alimentação Coberta | 5,5 s | 2,28 m/s | 1,14 m/s | 1,3–2,2 |
| P10 Recinto de Leilões | 6,0 s | 2,24 m/s | 1,12 m/s | 1,3–2,2 |
| P13 Expositores Externos | 5,5 s | 7,00 m/s | 3,50 m/s | 3,6–6,7 |
| P22 saída pelo portal | 6,0 s | 2,53 m/s | 1,27 m/s | 1,3–2,2 |

O conferidor imprime o conserto exato de cada um — encurtar o percurso da câmera
entre 87% e 98%, mexendo em `dist_ini_m`/`dist_fim_m` daquele plano. São ajustes
pequenos, então **o Higgsfield é viável**; ele só cobra quatro correções que o
Flow não cobra.

**Recomendação: Flow como caminho principal.** Higgsfield vale para os planos em
que o movimento é o assunto — o touro pulando do P19 e o público do P20 —, onde
o Kling costuma dar movimento mais convincente e o *Cinema Studio* deixa declarar
lente e movimento, que a decupagem já tem medidos.

---

## O aspecto — a conta que não pode errar

**Nenhuma das duas plataformas gera 2:1**, e a entrega é 2:1 (2760 × 1380, telão
P2,9). Então:

> **Gera-se em 16:9 e corta-se a faixa central 2:1 na montagem. Nunca esticar.**

**Por que o corte é seguro:** toda câmera da cena mira o alvo por constraint
*Track To*, então o assunto está no **centro** do quadro por construção. Cortar
topo e base simetricamente não pode perdê-lo. E o corte não mexe na largura —
16:9 e 2:1 têm a mesma horizontal; o 16:9 só tem mais céu e mais chão.

```
guia 3840×2160 (16:9)
   ↓  Flow em 4K
clipe 3840×2160
   ↓  corte central, 120 px de cada lado
3840×1920 (2:1)
   ↓  redução (0,72× — reduz, não amplia)
master 2760×1380
   ↓
painel P2,9  1379×690
```

Pelo caminho de 1080p a conta também fecha: 1920×960 cortado ainda é maior que
os 1379×690 do painel. O master de 2760×1380 é 2× o painel de propósito — é
folga, não exigência.

---

## Os letreiros ficam FORA do quadro-guia

Modelo generativo **destrói tipografia**: reescreve letra, troca acento, inventa
palavra. Passar por uma IA as suas duas frases literais —

- *É daqui que sai o alimento que sustenta o mundo*
- *Aqui será um grande balcão de negócios*

— é a maneira mais rápida de perdê-las. E a proibição da palavra **Kids** não
sobrevive a um modelo que resolve "melhorar" um letreiro de área infantil.

Então o `render_guias.py` esconde a coleção `LETREIROS`, e o texto entra
**depois**, na montagem, por cima do clipe pronto.

### E no Plano A ele deixa de ser objeto 3D

No Plano B o letreiro é geometria: um billboard plantado no mundo, dimensionado
pela lente e pela distância daquele plano, que a câmera atravessa e que muda de
tamanho durante o movimento. **No Plano A isso deixa de servir** — e o motivo é
que o clipe da IA **não segue o caminho da câmera quadro a quadro**. Ela
interpola entre os dois extremos travados do jeito dela. Um letreiro renderizado
do nosso percurso exato ia **deslizar contra a imagem**, e texto que desliza
contra o fundo é o tipo de erro que só aparece no telão.

Como **texto 2D** ele não tem com o que brigar. E a regra de 8%/4% fica mais
simples, não mais frouxa — vira conta direta sobre os 1380 px do master:

| nível | fração | pixels | onde |
|---|---|---|---|
| frase | 11,5% | 159 px | as duas frases literais dele |
| diferencial | 10,8% | 149 px | os quatro diferenciais |
| título | 8,0% | 110 px | o mínimo da regra, exato |
| apoio | 4,2% | 58 px | a descrição pequena embaixo |

O `montar_flow.sh` grava os 35 campos de texto com `drawtext`, cada um entrando
e saindo junto com o plano dele (meio segundo de folga em cada ponta, para o
letreiro não piscar no corte).

### Cinco letreiros estavam no plano errado — corrigido em 15/08

Achado ao montar a linha de tempo, e ia para a entrega:

| letreiro | estava em | é o plano |
|---|---|---|
| Pista de Julgamentos | P16 (Máquinas) | **P12** |
| Expositores Externos | P17 (Veículos) | **P13** |
| Máquinas e Implementos | P18 (Área de Shows) | **P16** |
| Área de Shows | P20 (Palco) | **P18** |
| *Aqui será um grande balcão de negócios* | P22 (saída) | **P21** |

Nada acusava, porque `letreiros.json` e `planos.json` só se falavam pelo `id` —
e id errado é id válido. Agora se falam **pelo texto também**, e
`cenas_ia.py --conferir` compara o texto do letreiro com o título do plano em
que ele está. Divergência de palavra que é intencional (o letreiro diz *Pavilhão
3* onde a decupagem diz *Agroindústrias*) tem de ser **declarada no arquivo** —
afrouxar o comparador para engolir essas duas deixaria passar as cinco de cima.

O mesmo conferidor mostrou que **P01, P17 e P20 não tinham letreiro nenhum** — a
falta estava mascarada pelos que sentavam em cima deles. Os três títulos já
estavam ditados em `docs/BRIEFING.md` (blocos 00, 15 e 18), então entraram por
transcrição, não por invenção. São 20 letreiros agora.

---

## O passo a passo

**1. Construir a cena** (com as tendas nas posições reais, feito em 15/08):

```bash
blender --background --python scripts/build_scene.py -- --out out/cena.blend
```

**2. Conferir o encaixe na grade da plataforma:**

```bash
python3 scripts/cenas_ia.py --conferir
```

Ele mede a velocidade de cada plano **depois** do encaixe e falha se algum sair
da faixa. Não pule: encurtar um plano acelera a câmera, e a 32 km/h não se lê
placa — foi por isso que a decupagem existe.

**3. Renderizar os quadros-guia** (~8 min):

```bash
blender --background --python scripts/render_guias.py -- \
    --blend out/cena.blend --plataforma flow
```

Saem em `out/cenas/flow/quadros/`, em 3840 × 2160, sem letreiro.

**4. Gerar o caderno de prompts:**

```bash
python3 scripts/cenas_ia.py --roteiro > out/cenas/roteiro-flow.md
```

Cada clipe vem com o nome dos dois PNG, o prompt em inglês para colar e o mesmo
prompt em português para você conferir antes de mandar.

**5. No Flow**, clipe a clipe: *Frames to Video* → primeiro quadro → último
quadro → colar o prompt → 16:9 → a duração que o caderno manda (4, 6 ou 8 s) →
gerar em 4K.

Baixe cada clipe **com o nome que o caderno dá** — `P01.mp4`, `P02-1.mp4`,
`P02-2.mp4`… — numa pasta só. O nome é o que amarra o clipe à linha de tempo; a
montagem não adivinha por ordem de download.

**6. Montar:**

```bash
bash scripts/montar_flow.sh out/cenas/flow/clipes out/cenas/flow
```

Ele confere cada clipe **antes** de montar (existe? duração certa? 16:9? não é
720p?) e **para** se algo estiver errado — descobrir isso depois de exportar
custa a exportação inteira. Depois corta a faixa 2:1, conforma para 30 fps,
emenda na ordem do percurso e grava os letreiros por cima.

Se a fonte não estiver no caminho declarado, ele avisa e sai **sem letreiro** em
vez de trocar por outra: tipografia errada num telão de 4 m é visível.

```bash
FONTE=/caminho/ArchivoNarrow-Bold.ttf bash scripts/montar_flow.sh
```

**7. Entregar:**

```bash
bash scripts/encode.sh out/cenas/flow/montagem_2760x1380.mov out/entrega
```

O `encode.sh` agora aceita os dois caminhos — uma pasta de PNG (Plano B) ou um
vídeo (Plano A) — e a especificação de entrega mora só nele: ProRes 422 HQ,
H.264 principal, reserva leve de 1380×690 e a cartela de teste de 10 s.

---

## O que conferir em cada clipe antes de aceitar

Na ordem em que costumam falhar:

1. **A arena tem arquibancada?** É a restrição 1 e é rejeição. A negativa está
   nos prompts de P10, P12, P18, P19, P20 e P21 — os seis em que há público
   assistindo alguma coisa. Nos outros ela **não** entra de propósito: citar
   "arquibancada" num plano de estacionamento não protege nada e ainda puxa o
   conceito para dentro do quadro.
2. **Apareceu texto?** Placa, faixa, marca d'água. Descarta e regera.
3. **A estrutura mudou?** Tenda a mais, pavilhão movido, prédio inventado. É o
   que o quadro-guia existe para impedir; se acontecer, o prompt está descrevendo
   posição em algum lugar — tire.
4. **A emenda casa?** Nos planos de dois clipes o quadro do meio é o **mesmo
   arquivo** nas duas pontas, então a geometria bate. O que pode variar é
   exposição e densidade de público — o prompt já pede continuidade, mas confira.
5. **O movimento é constante?** Sem rampa, sem corte, sem zoom.

---

## O que muda no filme

O encaixe na grade estica o filme de **154 s para 166 s** (+12 s, +7,8%).
**Decidido por ele em 15/08: fica assim** — *"não tenho limite de tempo"*. A
alternativa era comprimir planos para fora da faixa cinematográfica, e não
existe duração contratada.

---

## O que continua sendo verdade

- A **posição** de tudo continua vindo da planta medida. Este documento não
  move nada.
- Os 22 planos, a régua de altura por ambiente e a faixa de velocidade
  continuam valendo — ver `docs/PLANOS.md`.
- O conteúdo de cada ambiente continua saindo do **áudio do Tega**, minuto a
  minuto: `data/cenas-ia.json` cita o timecode de cada cena, e
  `docs/brief-audios.md` é a transcrição.
- O **Plano B** (render local completo, 12,9 h) não foi apagado. Continua em
  `scripts/render_shots.py`, e é para onde se volta se a IA não convencer.
