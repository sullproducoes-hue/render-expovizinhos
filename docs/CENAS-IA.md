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
**depois**, na montagem, por cima do clipe pronto. A regra de 8%/4% da altura
continua valendo, medida sobre o master 2760 × 1380 — que é onde ela sempre foi
medida.

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

**6. Na montagem:** cortar a faixa central 2:1, montar na ordem P01→P22, entrar
com os 16 letreiros por cima, e exportar `.mov` (ProRes 422 HQ) **e** `.mp4`
(H.264), mais a cartela de teste de 10 s.

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

O encaixe na grade estica o filme de **154 s para 166 s** (+12 s, +7,8%). Não há
duração contratada — o cliente nunca pediu um tempo — e a alternativa seria
comprimir planos para fora da faixa cinematográfica. **Fica o filme mais longo.**
Se você quiser os 154 s de volta, o caminho é encurtar percurso de câmera, não
duração de clipe, e o conferidor imprime quanto.

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
