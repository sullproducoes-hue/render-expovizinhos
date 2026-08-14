# Prompts Higgsfield — sequência de imagens do vídeo AGROSHOW 2026

Derivado direto de `docs/brief-audios.md` (áudios do Tega). A ordem abaixo é a
ordem de circulação que ele ditou — é a ordem de geração e a ordem de montagem.

**Como usar:** cada bloco tem um `PROMPT` (cola no Higgsfield Soul / gerador de
imagem), um `NEGATIVO` e um `MOVIMENTO` (preset de câmera para o image-to-video).
Gere a imagem primeiro, aprove o quadro, só então anime.

---

## Regras de operação

### Proporção — não gere em 16:9

A entrega é **2:1** (painel LED P2,9, 1379 × 690, master 2760 × 1380).

Gere em **21:9** e corte as laterais até 2:1. O 21:9 é 2,33 — cortando só as
laterais você mantém a altura inteira. Se gerar em 16:9 (1,78) você é obrigado a
cortar topo e base, e perde 11% da altura do quadro, que é justamente onde estão
céu e horizonte nestes planos.

Componha sempre o assunto no **centro**, com folga nas laterais. Nada importante
a menos de 8% da borda — além do corte do 21:9 ainda existe a área de segurança
de 90% do telão.

### LOOK LOCK — cola em todo prompt

Estas linhas vão **no fim de cada prompt**, sem alterar:

```
golden hour late afternoon sunlight, warm low sun, long soft shadows, clear sky with
scattered high clouds, subtropical southern Brazil, Paraná countryside, rolling green
hills on the horizon, cinematic wide-angle, shot on 24mm anamorphic, natural color
grade, warm highlights and cool shadows, photorealistic, ultra detailed, no text,
no logos, no watermark
```

Motivo: os áudios não pedem hora do dia, mas o vídeo é um percurso contínuo —
se cada plano vier com uma luz, não existe percurso, existe colagem. Fim de
tarde resolve porque valoriza o verde do parque e é a luz de evento cheio.

### NEGATIVO base — cola em todo prompt

```
text, letters, signage with readable words, logos, watermark, distorted faces,
deformed hands, extra limbs, plastic skin, oversaturated, HDR halo, fisheye,
tilted horizon, snow, autumn foliage, european architecture, desert, modern
skyscrapers, blurry, low resolution
```

### Restrições do cliente que aparecem nos prompts

1. **Arena de rodeio SEM arquibancada.** É o ponto de falha mais provável do
   projeto — todo modelo de IA gera arquibancada quando lê "rodeo arena". O
   negativo específico está no bloco 17 e é obrigatório.
2. **Portal = o da foto**, versão econômica. Nunca mais ornamentado.
3. **"Kids" é proibido** — nos letreiros. Não afeta o prompt de imagem, afeta a
   arte do letreiro.
4. **Quatro diferenciais com mais tela:** Fazendinha, Rodeio, Café Colonial,
   Mercado do Produtor. Esses quatro têm dois quadros cada.

### Sobre pessoas nos quadros

Peça sempre **público brasileiro do interior do Paraná** — a descrição está em
cada prompt como `Brazilian rural crowd`. Sem isso o modelo devolve figurantes
americanos de county fair, e o cliente vê na hora. Rostos em primeiro plano são
risco: prefira multidão em plano médio/aberto, de costas ou de perfil.

---

# A SEQUÊNCIA

## 00 · Estacionamentos
**Letreiro:** *Estacionamento* · **Movimento:** `Drone Fly Over` lento, seguindo
para a frente em direção ao portal

```
PROMPT
Aerial view descending toward a large countryside exposition park entrance, two big
grass-and-gravel parking lots full of pickup trucks, SUVs and farm vehicles neatly
parked in rows, families walking from the cars toward a wooden entrance gate in the
distance, dust haze in the warm air, wide paved access road with cars arriving,
Brazilian rural crowd, agricultural fair atmosphere,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + empty parking lot, american flags, snow
```

---

## 01 · PORTAL DE ENTRADA — quadro-chave
**Letreiro:** *É daqui que sai o alimento que sustenta o mundo*
**Movimento:** `Dolly In` lento, atravessando o vão central

Este é o primeiro e o último plano do vídeo. Vale gerar 6–8 variações e escolher.
Referência de forma: `reference/PORTAL-referencia.md`.

```
PROMPT
A wooden barn-style entrance gate to a Brazilian countryside exposition park, dark
treated vertical wood planks in tobacco brown, central gabled roof with exposed
inverted-V truss, large sliding barn doors with X-shaped cross bracing, black iron
wall lanterns mounted along the facade, white double-hung windows with grid panes,
lower side wings with dark corrugated roofing and short eaves, wooden barrels and
leafy potted plants flanking the central passage, three walk-through openings with
decorative iron gates behind, dark gravel ground in front, curved planting bed with
white curb on the left, blue flagpole on the left, simple and economical
construction, not monumental, not ornate, families walking in through the gate,
Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + monumental arch, stone castle gate, ornate carvings, golden
decoration, futuristic structure, neon, oversized scale, cathedral, brick
```

Se o quadro sair grandioso demais, acrescente ao prompt: `modest scale, single
storey side wings, plain construction, low budget rural build`.

---

## 02 · Pavilhão 1
**Letreiro:** *Pavilhão 1 — Indústria, Comércio e Prestação de Serviços*
**Movimento:** `Dolly In` pelo corredor central

Este quadro serve também para o Pavilhão 2 (bloco 04) — gere duas variações do
mesmo prompt, uma para cada, mudando só a cor dominante dos estandes.

```
PROMPT
Interior of a large trade fair pavilion at a Brazilian agricultural expo, long
central aisle flanked by modern exhibitor booths of industry, commerce and services
companies, clean white and grey booth structures with counters and product displays,
bright even lighting under an exposed metal truss roof, visitors walking and talking
with sales staff, polished concrete floor, banners without readable text, busy but
not crowded, Brazilian rural crowd in casual clothes and caps,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + livestock, animals, hay, outdoor, tents, food stalls
```

---

## 03 · Praça de Alimentação Coberta
**Letreiro:** *Praça de Alimentação Coberta* · **Movimento:** `Arc Right` lento

O áudio: mesas, cadeiras, guichês do pessoal vendendo comida e bebida, tudo do
lado da churrasqueira.

```
PROMPT
Large covered food court at a Brazilian agricultural fair, long rows of tables and
chairs under a high open-sided metal roof, families eating together, a line of small
food and drink kiosks along one side, a big charcoal barbecue station with churrasco
skewers and smoke rising, cold drink counters, warm light coming in sideways under
the roof, lively but comfortable atmosphere, Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + fast food chain, indoor mall, fine dining, empty tables
```

---

## 04 · Pavilhão 2
**Letreiro:** *Pavilhão 2 — Indústria, Comércio e Prestação de Serviços*
**Movimento:** `Dolly In`

Reaproveita o prompt do bloco 02. Para o quadro não repetir na montagem: troque
`clean white and grey booth structures` por `warm wood and dark blue booth
structures`, e mude o ângulo pedindo `slightly low camera angle`.

---

## 05 · MERCADO DO PRODUTOR — diferencial · quadro 1 de 2
**Letreiro:** *Mercado do Produtor* · **Movimento:** `Dolly In` na entrada

```
PROMPT
Farmers market inside the entrance of a rural exposition pavilion, wooden stalls
loaded with fresh local produce, crates of vegetables, fruit, cheese, honey jars,
cured sausages, homemade bread and preserves, hand-lettered wooden crates, small
producers standing behind the counters serving customers, abundant colorful display,
warm inviting light from the pavilion entrance, Brazilian rural crowd shopping,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + supermarket shelves, plastic packaging, refrigerated aisles,
industrial retail
```

---

## 06 · Agroindústrias
**Letreiro:** *Agroindústrias* · **Movimento:** `Handheld` caminhando pelo corredor

```
PROMPT
Row of small agro-industry exhibitor booths inside a fair pavilion, each compact
stall with a counter and tasting samples, artisanal dairy, sausage, cachaça, wine,
honey and jam producers presenting their products, visitors sampling food, warm
wooden counters, half-height OSB board partition wall visible at the back of the
hall, friendly small-business atmosphere, Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + factory machinery, industrial plant, livestock
```

> Nota: o material da meia-parede ("OSB") é o único ponto incerto da
> transcrição. Se o Tega confirmar outro material, troque `OSB board` no prompt.

---

## 07 · CAFÉ COLONIAL + COZINHA DIDÁTICA — diferencial · 2 quadros
**Letreiro:** *Café Colonial* / *Cozinha Didática* · **Movimento:** `Crane Down`
no primeiro, `Dolly In` no segundo

**Quadro A — Café Colonial**
```
PROMPT
Traditional Brazilian colonial-style café at a rural fair, long tables covered with
checked cloth and loaded with an abundant spread of homemade cakes, breads, cheeses,
cold cuts, jams, fruit and coffee pots, families seated eating together, warm cozy
lighting, rustic wooden interior at the back of a pavilion, half-height partition
wall separating it from the exhibition area, generous and welcoming abundance,
Brazilian rural crowd,
[LOOK LOCK]
```

**Quadro B — Cozinha Didática**
```
PROMPT
Teaching kitchen demonstration at a rural agricultural fair, a chef cooking at a
stainless steel demonstration counter facing a seated audience, ingredients laid out,
overhead angled mirror above the counter, people watching attentively and taking
photos, bright practical lighting, clean modern kitchen set inside a fair pavilion,
Brazilian rural crowd as audience,
[LOOK LOCK]
```

```
NEGATIVO (ambos)
[NEGATIVO base] + fine dining restaurant, tv studio set, celebrity chef, empty room
```

---

## 08 · Bosque — Praça de Alimentação Aberta
**Letreiro:** *Praça de Alimentação Aberta* · **Movimento:** `FPV Drone` baixo,
atravessando por dentro do bosque

O áudio é claro: o percurso passa **por dentro** do bosque e sai em frente à
Sociedade Rural.

```
PROMPT
Open-air food area under a grove of tall mature trees at a Brazilian agricultural
fair, wooden picnic tables and benches scattered in dappled shade, food trucks and
small kiosks along the edge, string lights hanging between trunks, sunlight filtering
through the canopy in warm beams, families and friends relaxing and eating, dirt and
grass ground, Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + dense jungle, dark forest, tropical rainforest, pine forest, snow
```

---

## 09 · Recinto de Leilões
**Letreiro:** *Recinto de Leilões* · **Movimento:** `Crane Down` entrando no recinto

```
PROMPT
Cattle auction in progress at a Brazilian rural society arena, a single prize bull
being walked in a small sand ring, auctioneer at an elevated podium with microphone,
buyers seated in tiered ringside seats holding paddles, focused attention, wooden
rails around the ring, warm overhead lighting mixed with late afternoon daylight from
the open sides, Brazilian rural crowd of ranchers in hats,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + art auction, indoor gallery, rodeo, bucking bull, empty seats
```

---

## 10 · Exposição de Animais — 2 quadros
**Letreiro:** *Exposição de Animais* · **Movimento:** `Dolly In` pelo corredor
central dos pavilhões

Ordem ditada, confirmada contra a planta: 1 gado de leite · 2 núcleo cara branca
(Hereford/Braford) · 3 diversas raças / Nelore · 4 ovinos e caprinos ·
5 pequenos animais · 6 equinos.

**Quadro A — bovinos (cobre pavilhões 1, 2 e 3)**
```
PROMPT
Interior of a covered livestock barn at a Brazilian agricultural expo, long central
aisle with cattle tied in individual stalls on both sides, groomed dairy cows on one
side and Hereford cattle with red bodies and distinctive white faces further down,
white Nelore cattle with humps at the far end, clean straw bedding, handlers brushing
and preparing the animals, feed buckets and show halters, high open metal roof with
warm light coming through the open ends, visitors walking the aisle admiring the
animals, Brazilian rural crowd,
[LOOK LOCK]
```

**Quadro B — ovinos, pequenos animais e equinos (pavilhões 4, 5 e 6)**
```
PROMPT
Interior of a covered animal pavilion at a Brazilian agricultural expo, pens with
sheep and goats, small animal cages with rabbits and poultry, and horse stalls with
groomed saddle horses at the far end, children and families looking at the animals
over the rails, clean straw, wooden pen dividers, high open metal roof, warm side
light, Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO (ambos)
[NEGATIVO base] + zoo, wild animals, dirty neglected animals, cramped cages, mud,
industrial feedlot
```

---

## 11 · Pista de Julgamentos
**Letreiro:** *Pista de Julgamentos* · **Movimento:** `360 Orbit` lento em volta
do animal em julgamento

O áudio: "aquela área de pasto verde".

```
PROMPT
Livestock judging ring on open green pasture at a Brazilian agricultural fair,
handlers walking prize cattle in a circle on short green grass, judges in the center
inspecting the animals and taking notes, spectators standing along a simple wooden
rail fence watching, wide open field with the fair pavilions in the background,
Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + rodeo, grandstand, dry dusty ground, indoor arena
```

---

## 12 · Expositores Externos
**Letreiro:** *Expositores Externos* · **Movimento:** `Drone Fly Over` baixo,
seguindo a fileira de estandes

```
PROMPT
Outdoor exhibitor area at a Brazilian agricultural fair, a long row of open-sided
tents and modular booths on grass, agribusiness companies displaying products and
services, flags and plain banners without readable text, visitors walking between the
stands on gravel paths, green lawn between the booths, wide open fairground with
hills on the horizon, Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + indoor, empty fairground, street market, food festival
```

---

## 13 · FAZENDINHA — diferencial · 2 quadros
**Letreiro:** *Fazendinha* grande + descrição pequena embaixo
**Movimento:** `Dolly In` atravessando a porteira, depois `Arc Left`

A palavra "Kids" é proibida no letreiro. No prompt não faz diferença — mas
mantenha o negativo abaixo para não vir parque de diversões.

**Quadro A — a porteira**
```
PROMPT
A big decorative wooden farm gate marking the entrance to a children's farm area at a
Brazilian agricultural fair, rustic timber posts and rail arch, hay bales and wooden
wagon wheels decorating the sides, colorful inflatable play structures visible
beyond, families with children walking through the gate, green grass, lasso arena
fence to the side, Brazilian rural crowd,
[LOOK LOCK]
```

**Quadro B — atividades**
```
PROMPT
Children's farm activity area at a Brazilian agricultural fair, colorful inflatable
bouncy castles on one side, children riding ponies led by handlers on a short trail,
a border collie herding a small flock of sheep in a fenced demonstration ring with
families watching and clapping, hay bales as seating, festive rural atmosphere,
green grass, Brazilian rural crowd of parents and children,
[LOOK LOCK]
```

```
NEGATIVO (ambos)
[NEGATIVO base] + amusement park, ferris wheel, roller coaster, carnival rides,
theme park mascot, plastic playground
```

---

## 14 · Máquinas, Equipamentos e Implementos Agrícolas
**Letreiro:** *Máquinas, Equipamentos e Implementos Agrícolas*
**Movimento:** `Crane Up` revelando a fileira inteira

O áudio situa aqui o "primeiro anel de cima" — filme de cima do patamar.

```
PROMPT
Agricultural machinery exhibition on the upper terrace of a Brazilian expo park, rows
of large modern tractors, combine harvesters, sprayers, planters and farm implements
lined up on green grass, polished paint reflecting the low sun, visitors walking
between the machines and climbing into cabs, the terrain stepping down to the fair
below in the background, Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + construction site, mining equipment, military vehicles, junkyard,
rusty machines
```

---

## 15 · Veículos e Motos
**Letreiro:** *Veículos e Motos* · **Movimento:** `Arc Right` acompanhando a curva
do anel

```
PROMPT
Vehicle exhibition area at a Brazilian agricultural fair, rows of new pickup trucks
and SUVs on display alongside motorcycles and quad bikes, dealership tents behind
them, polished vehicles catching the warm low sun, visitors inspecting the cars,
curving terrace layout following the ring of the fairground, Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + car showroom interior, race track, used car lot, traffic jam
```

---

## 16 · Área de Shows
**Letreiro:** *Área de Shows* · **Movimento:** `Crane Down` descendo o patamar em
direção ao palco

```
PROMPT
Wide view of a large open-air concert ground at a Brazilian agricultural fair seen
from the terrace above, a big stage with truss structure and lighting rig at the far
end, a vast open field in front of it filling with people at dusk, the terrain
stepping down from the terrace to the show area, stage lights just starting to glow
against the late afternoon sky, Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + stadium, grandstand, indoor arena, empty field
```

---

## 17 · ARENA DE RODEIO — diferencial · quadro crítico
**Letreiro:** *Arena de Rodeio* · **Movimento:** `Crash Zoom In` no touro

**LEIA ANTES DE GERAR.** O cliente foi explícito e repetiu: *"na arena de rodeio
não dá pra colocar arquibancada, tá? É sem arquibancada, é só a pista da arena e
dos lados camarote. E de frente, o palco de shows."*

Todo modelo de imagem gera arquibancada ao ler "rodeo arena" — é o
comportamento padrão. O negativo abaixo não é opcional, e **confira o quadro
gerado antes de animar**. Se aparecer arquibancada, descarte e gere de novo; não
tente consertar depois.

```
PROMPT
Rodeo arena at a Brazilian agricultural fair at dusk, a bucking bull mid-jump in the
dirt arena with a rider, sand and dust flying, the arena enclosed by simple metal
panel fencing, elevated VIP box suites with railings and tables lining both long
sides of the arena, the main concert stage standing directly in front at the far end
facing the arena, crowd watching from the VIP boxes on the sides only, warm arena
floodlights mixing with the last daylight, Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO (obrigatório — não edite)
[NEGATIVO base] + grandstand, bleachers, stadium seating, tiered seating, spectator
stands, amphitheatre, seating rows around the arena, packed stands, american rodeo
stadium
```

Se o modelo insistir, acrescente ao prompt: `no seating stands around the arena,
open sides, only two rows of private VIP boxes at ground and first floor level`.

---

## 18 · Palco Principal
**Letreiro:** *Palco Principal* · **Movimento:** `Crane Up` do público para o palco

O áudio: artista cantando, o pessoal comemorando, se divertindo, bebendo,
fazendo festa, e toda aquela área embaixo lotada de público.

```
PROMPT
Night concert at a Brazilian agricultural fair, a country music singer performing on
a large stage with a full lighting rig, beams of colored light cutting through haze,
LED screens behind the band showing abstract light patterns, an enormous crowd
packing the field in front of the stage with arms raised, people singing, celebrating
and holding drinks, confetti in the air, energetic festive atmosphere, seen from
above and behind the crowd, Brazilian rural crowd,
photorealistic, ultra detailed, cinematic wide-angle, shot on 24mm anamorphic,
no text, no logos, no watermark
```

> Este é o único plano que **não** leva o LOOK LOCK completo — é noite. É a
> transição natural do percurso: o vídeo começa de dia no portal e termina à
> noite no show. Mantenha o resto da sequência em fim de tarde para a passagem
> ficar coerente.

```
NEGATIVO
[NEGATIVO base] + daylight, empty field, small club, indoor venue, seated audience
```

---

## 19 · Assinatura — saindo pelo portal
**Letreiro:** *Aqui será um grande balcão de negócios*
**Movimento:** `Super Dolly Out` atravessando o vão do portal, de dentro para fora

Mesmo fechamento do último vídeo aprovado pelo cliente. Reaproveite o quadro do
bloco 01 gerado pelo lado de dentro — gere com este prompt:

```
PROMPT
View from inside a Brazilian countryside exposition park looking out through a wooden
barn-style entrance gate, dark treated vertical wood planks, sliding barn doors with
X cross bracing, black iron lanterns, the central passage framing the open access
road and the parking area beyond, visitors walking out at the end of the day, warm
low sun flaring through the opening, simple economical construction, not monumental,
Brazilian rural crowd,
[LOOK LOCK]
```

```
NEGATIVO
[NEGATIVO base] + monumental arch, ornate gate, stone castle, neon, futuristic
```

---

# Ordem de geração — o que fazer primeiro

O prazo não comporta gerar os 20 na mesma pressa. Esta é a fila por valor:

| Prioridade | Blocos | Por quê |
|---|---|---|
| 1 | 01, 19 | Portal. Primeiro e último quadro do vídeo. Gere 6–8 variações |
| 2 | 17, 18 | Rodeio e palco. O rodeio é o quadro que mais pode dar errado |
| 3 | 13 A+B | Fazendinha. Diferencial, e é o que o público comenta |
| 4 | 05, 07 A+B | Mercado do Produtor e Café Colonial. Diferenciais |
| 5 | 10 A+B | Animais. Bloco grande, ordem já validada contra a planta |
| 6 | 02/04, 03, 09, 14 | Corpo do percurso |
| 7 | 00, 06, 08, 11, 12, 15, 16 | Se o prazo apertar, viram mapa + letreiro sem imagem |

---

# Checklist antes de animar cada quadro

- [ ] Está em 21:9 e corta limpo para 2:1 sem perder o assunto?
- [ ] O assunto está no centro, com nada crítico a menos de 8% da borda?
- [ ] A luz bate com o LOOK LOCK (fim de tarde), exceto o bloco 18?
- [ ] O público parece brasileiro do interior, não figurante americano?
- [ ] Bloco 17: **tem arquibancada?** Se tiver, descarte e gere de novo.
- [ ] Bloco 01/19: o portal está mais simples que a foto, nunca mais ornamentado?
- [ ] Nenhum texto legível apareceu na imagem? Todo texto do vídeo é letreiro
      nosso, feito na edição, dentro da área de segurança de 90%.
