# Onde gerar as imagens do Plano B — as contas, o que elas custam, e a saída grátis

Medido em **16/08/2026**, tentando gerar o P19 de verdade e apanhando. Saldo de
conta muda todo dia; o que não muda é o **método** e os **números de custo**.

`PLANO-B.md` diz *o que* gerar, plano a plano. Este diz *onde*.

---

## O estado das três contas, em 16/08

| conta | plano | saldo | custo de uma geração | dá? |
|---|---|---|---|---|
| **Artlist** | Max Pro RAW | **19** de 7.500 · **renova 17/08** | recusou até o modelo mais barato | ❌ hoje · ✅ amanhã |
| **Kairogen** | free | **1** | imagem 2 · Seedance 9 s **6** | ❌ |
| **claude** | plus | **0,1** | — | ❌ |

**Nenhuma das três gerava nada em 16/08.** A Artlist é a única que volta sozinha,
e volta com 7.500 — que é folga suficiente para as 22 imagens e os 25 clipes.

### O que foi tentado, para ninguém repetir

Três modelos de imagem-para-imagem na Artlist, com as 5 placas do P19 anexadas,
do mais caro ao mais barato: **Seedream 5.0 I2I 2K**, **Nano Banana 2 I2I 1K**,
**Nano Banana 2 LITE I2I**. Os três responderam *créditos insuficientes*. Com 19
créditos não sai **uma** geração com referência — descer de modelo não resolve, e
não vale gastar chamada tentando.

### Não existe conector de Gemini

Procurado no registro de conectores em 16/08: **não há** conector de Gemini nem
de Google AI Studio. Os conectores Google da conta (Gmail, Drive, Agenda) não
geram imagem. Conectar conector é ação do Natan no claude.ai, de todo jeito.

---

## A saída grátis, e ela é boa

**Google AI Studio** — `aistudio.google.com`. Login com conta Google, e o modelo
de imagem do Gemini roda **sem custo**, no navegador. Aceita várias imagens de
referência ao mesmo tempo, que é o que os planos de 3 e 5 placas exigem.

O ciclo vira: sobe as placas → cola o prompt do `PLANO-B.md` → baixa → salva em
`out/plano-b/PXX/gerado/`. A esteira é a mesma; só o motor muda.

**Limite conhecido:** dali não sai vídeo. A animação continua dependendo do
Seedance, e o Seedance continua dependendo de crédito.

---

## O teto de 12 s continua valendo

Seedance V1.5 Pro: **4 a 12 s por clipe**. P06 (17,5 s), P14 (18,5 s) e P08
(13,5 s) viram dois clipes cada, encadeados pelo último quadro. Está encodado em
`scripts/plano_b.py` e impresso no `PLANO-B.md`. **25 clipes para 22 planos.**

---

## O prompt do P19 como ele foi realmente montado

Este não é o prompt automático do `plano_b.py`. É a versão **imagem-para-imagem**,
escrita contra as **cinco fotos que o Natan subiu em 16/08** — e por isso a
primeira ordem dele é *preservar*, não *descrever*. Prompt de i2i que redescreve
a cena inteira faz o modelo regenerar tudo e perder o lugar.

As placas: quatro do **palco fixo em fim de tarde** (a luz do filme, 18:15) e uma
da **bacia em dia de evento**, sol a pino — esta serve de leitura de montagem
(truss, balões, tendas, gradil), nunca de luz. **Três dos cinco caminhos em disco
não estão confirmados** — ver `PENDENCIAS.md` P06.

```
Keep the exact location, terrain and architecture from the reference photos: the
same natural earth bowl / amphitheatre with its grass banks, the same dirt arena
floor, the same fixed concrete stage with the white proscenium shell, blue base
and red steel roof facing the arena, the same tree line and the same background.
Do not redesign the site.

Change it to the venue in full event: a rodeo running in the dirt arena — one
bucking bull mid-buck with a mounted rider on its back, dust kicked up under the
hooves. Along the two long sides of the arena, low covered VIP boxes with people
watching from them. A crowd of spectators standing at the arena rails. White
peaked event marquees and tents pitched on the flat ground around the bowl, guy
ropes and steel poles visible. Banners and flags on the stage.

CRITICAL: there are NO grandstand bleachers anywhere around this arena. Only the
dirt track, the low side boxes and the stage facing it. Never add tiered stadium
seating.

Light: late-afternoon golden hour, sun low at about 10 degrees above the horizon,
long warm raking shadows across the dirt and grass, warm sky — match the light of
the late-afternoon reference photos, not the midday one.

Ultra-photorealistic photograph of a real Southern Brazil agricultural fairground
in Dois Vizinhos, Parana. Shot on a full-frame camera from a drone about 26 m
above the ground, roughly 85 m from the arena, looking down at a shallow angle so
the ground plane still reads — not a top-down map view. Natural colour, real
atmospheric haze, believable depth of field. No CGI look, no plastic surfaces, no
oversaturation, no cartoon or illustration, no distorted faces, no warped text or
unreadable signage, no watermark.

16:9 horizontal.
```

### A regra de i2i que este prompt aplica

1. **Primeiro o que fica**, nomeado peça por peça — bacia, palco, taludes, árvores.
   *"Do not redesign the site."*
2. **Depois o que entra** — touro, cavaleiro, camarotes, público, tendas.
3. **A restrição em maiúscula, e repetida ao contrário.** Não basta pedir "sem
   arquibancada": o modelo desenha arquibancada em arena por hábito. Diz o que
   existe (*only the dirt track, the low side boxes and the stage*) **e** proíbe
   de novo (*never add tiered stadium seating*).
4. **Qual referência manda na luz**, quando elas discordam entre si.

Vale para todos os 22, não só para o P19.

---

## O que conferir quando a imagem voltar

Antes de animar. É barato e pega o que causa rejeição:

| # | conferir | por quê |
|---|---|---|
| 1 | **arquibancada na arena** | restrição dura do cliente, e o erro mais provável |
| 2 | a palavra **"Kids"** em qualquer placa | proibida; é *Fazendinha* |
| 3 | o portal continua **celeiro econômico** | não virou arco monumental |
| 4 | letreiro inventado pela IA | o letreiro é da edição; texto de IA sai torto |
| 5 | a luz bate com **18:15** | sombra longa, sol baixo, sem sol a pino |

Quadro que passar nos cinco vai para `gerado/` e vira entrada do Seedance.
