# Decupagem — a câmera virou dado

Este documento existe porque o percurso original (16 pontos numa única curva
bezier, 128 s) foi medido contra a planta e não segura: **1.152 m em 128 s dão
9,0 m/s — 32 km/h.** A faixa cinematográfica de drone é 1,3–2,2 m/s em órbita
e push-in, e 3,6–6,7 m/s em sobrevoo. O percurso antigo rodava de 1,3 a 7×
acima disso. Nessa velocidade não se lê placa, não se reconhece área, não se
sente escala — e é isso que o cliente comprou: reconhecer o parque dele.

A saída é cortar em planos. Cada plano tem alvo, lente, altura, movimento e
duração próprios, declarados em `data/planos.json` — não improvisados numa
curva única. Isso também resolve o resto: os quatro diferenciais ganham mais
tela sem esticar o filme, só se renderiza o que está em quadro (decisivo com
8–12 GB de VRAM), e um plano que quebra se re-renderiza sozinho.

Confira sempre com:

```bash
python3 scripts/planos.py --conferir
```

O conferidor mede a velocidade real de cada plano (amostrando o movimento, não
confiando na declaração) e falha se algum passar da faixa cinematográfica, se
um diferencial tiver menos de 8 s, ou se um movimento não for reconhecido.
Isso roda em qualquer Python — não precisa de `bpy` nem de GPU.

---

## A decupagem

22 planos, 5.280 quadros, **176 s (2,9 min) a 30 fps.** Os 19 títulos do
`docs/BRIEFING.md` mapeiam 1:1 nos planos com título; os que não têm título
(P15, P22) são continuação do plano anterior, sem letreiro novo.

| # | Título na tela | Movimento | Lente | Dur. | m/s | Âncora |
|---|---|---|---|---|---|---|
| P01 | Estacionamento | subida | 24 mm | 7.0 s | 2.8 | planta |
| P02 | É daqui que sai o alimento que sustenta o mundo | push-in | 35 mm | 9.0 s | 2.1 | planta |
| P03 | Pavilhão 1 — Indústria, Comércio e Prestação de Serviços | orbita | 35 mm | 6.0 s | 1.7 | planta |
| P04 | Praça de Alimentação Coberta | push-in | 35 mm | 7.0 s | 2.0 | planta |
| P05 | Pavilhão 2 — Indústria, Comércio e Prestação de Serviços | orbita | 35 mm | 5.0 s | 1.7 | planta |
| P06 **·** | Mercado do Produtor | push-in | 50 mm | 17.5 s | 2.0 | planta |
| P07 | Agroindústrias | travelling | 35 mm | 5.0 s | 1.6 | planta |
| P08 **·** | Café Colonial | push-in | 50 mm | 13.5 s | 2.0 | planta |
| P09 | Praça de Alimentação Aberta | sobrevoo | 35 mm | 9.0 s | 6.0 | planta |
| P10 | Recinto de Leilões | push-in | 35 mm | 8.0 s | 2.0 | planta |
| P11 | Exposição de Animais | sobrevoo | 35 mm | 11.0 s | 6.3 | planta |
| P12 | Pista de Julgamentos | orbita | 50 mm | 5.0 s | 1.7 | planta |
| P13 | Expositores Externos | sobrevoo | 35 mm | 5.5 s | 6.4 | planta |
| P14 **·** | Fazendinha | push-in | 35 mm | 12.0 s | 1.9 | planta |
| P15 | — | orbita | 50 mm | 7.0 s | 1.8 | planta |
| P16 | Máquinas, Equipamentos e Implementos Agrícolas | sobrevoo | 35 mm | 6.0 s | 5.9 | planta |
| P17 | Veículos e Motos Náuticas | travelling | 50 mm | 5.0 s | 1.4 | planta |
| P18 | Área de Shows | sobrevoo | 35 mm | 5.5 s | 5.3 | planta |
| P19 **·** | Arena de Rodeio | orbita | 35 mm | 12.0 s | 1.8 | planta |
| P20 | Palco Principal | push-in | 50 mm | 7.0 s | 1.8 | planta |
| P21 | Aqui será um grande balcão de negócios | subida | 24 mm | 7.0 s | 5.1 | planta |
| P22 | — | push-in | 35 mm | 6.0 s | 2.0 | planta |

> **Refeita em 15/08/2026, à noite.** Sete planos mudaram de duração porque
> o reenquadramento afastou a câmera e a velocidade saiu da faixa — e a escolha
> foi **alongar o plano, não encurtar o percurso**, porque o cliente pediu mais
> tempo de tela para os diferenciais (`DECISOES.md` D064). O filme foi de 4.635
> para **5.280 quadros — 154 s para 176 s**. As câmeras de 11 planos foram
> reenquadradas por medida (D063); cada um guarda `camera_antes_1508` e
> `conserto_1508` em `data/planos.json`, com o número de antes e o de depois.
>
> **Um portão novo entrou junto:** `scripts/enquadramento.py` mede se o plano
> MOSTRA o lugar que promete — 9 amostras ao longo do movimento, 45 raios pelo
> frustum, e reprova quando **uma única superfície** toma mais de 40% do quadro.
> O conferidor de velocidade e o de câmera não viam isso.

**·** marca os quatro diferenciais (P06 Mercado do Produtor, P08 Café
Colonial, P14/P15 Fazendinha, P19 Arena de Rodeio) — todos com 9–16 s de tela
somada, acima dos 5–7 s do corpo do filme, como o cliente pediu.

Regenere esta tabela com:

```bash
python3 scripts/planos.py --tabela
```

---

## Altura de câmera: quem manda é o ambiente

Ordem do Natan, **14/08/2026**, e ela não se negocia com estatística:

| onde a câmera está | altura |
|---|---|
| por dentro de pavilhão | **~2 m** |
| lugar aberto | **4–15 m** |
| plano de conjunto do rodeio | **40–50 m**, e só um |

**A telemetria dos 62 voos serve para aperfeiçoar o mapa, não para definir
altura de câmera.** Ela mede o que ele fez filmando o recinto real, com drone;
aqui a câmera é virtual e o enquadramento se decide pelo que precisa caber no
quadro. Foi por isso que 13 planos desceram em 14/08 — o mais alto ia a 72 m.

O plano de conjunto é o **P21**, a subida final sobre a arena (15 → 48 m), que
é também a assinatura do filme. Nenhum plano entra em pavilhão hoje, porque os
pavilhões ainda são caixa sem interior; quando tiverem, a faixa de dentro é a
de ~2 m.

---

## As âncoras — todas viraram `planta` em 14/08

Cada plano declara `ancora`, e isso não é decoração — é o nível de confiança
da posição. Até 14/08 havia três níveis; hoje há um só:

- **`planta`** — o alvo é um rótulo real do mapa. **Os 22 planos.**

O que mudou: o extrator antigo só aceitava rótulo que estivesse numa lista
branca escrita à mão, e descartava o resto em silêncio — 50 dos 118 nomes do
mapa. Entre os descartados estavam justamente os lugares que não tinham
âncora: **Fazendinha**, **Área de Show**, **Expositores Externo** (dois deles)
e a **Exposição de Máquinas, Equipamentos e Veículos e Implementos**.

O mapa tem uma **camada vermelha** (`#ff3131`, 36 spans) que é o roteiro do
cliente desenhado por cima da planta técnica — a mesma ordem que ele ditou no
áudio, já posicionada. `scripts/auditar_mapa.py` lê essa camada e
`scripts/terreno.py` a injeta nas zonas, então `alvo: {tipo: rotulo}` passou a
encontrar todos eles.

A **Fazendinha**, que era a única posição do filme sem apoio em dado nenhum,
está no mapa em **(-164,4 · -18,6) m**. Decisão do Natan em 14/08: *vale o
mapa*, e não a descrição do áudio (*"desce pro lado da pista de tiro de laço"*),
que aponta para outro lugar.

**P17 (Veículos e Motos Náuticas)** é o único alvo em `xy`: o rótulo vermelho
junta máquinas e veículos num nome só, e quem separa os dois é a cor com que a
planta pinta cada estande. Os 12 estandes azuis dão o centroide (-34,2 · 58,4) m
— ver `scripts/classificar_estandes.py`.

**Cuidado ao mexer no `alvo` de um plano:** o `alvo_fim` não acompanha sozinho.
Quando as seis âncoras subiram para `planta`, três sobrevoos passaram a varrer
da posição real até a posição chutada antiga e estouraram a faixa de velocidade
— P16 chegou a 21,2 m/s. O conferidor pegou; sem ele, teria ido para o render.

---

## Regras que o conferidor aplica

Vindas da pesquisa de cinematografia de drone, viram checagem automática:

- **Velocidade de pico** dentro de 1,3–2,2 m/s (órbita, push-in, travelling)
  ou 3,6–6,7 m/s (sobrevoo). Medida por amostragem do movimento real, não
  pela declaração do plano.
- **Uma lente por plano**, sem zoom dentro do plano — muda de lente, muda de
  plano.
- **Diferencial com pelo menos 8 s** de tela.
- **Movimento linear dentro do plano** (t linear em `amostra()`, com
  suavização opcional via `suavizacao`) — a pesquisa é explícita: velocidade
  constante é o que faz o movimento parecer deliberado. Aceleração dentro do
  plano só entra se for declarada.

---

## Como um plano é montado

Cada plano tem `alvo` (o que a câmera mira) e `camera` (de onde ela mira, em
coordenadas polares ao redor do alvo — azimute, distância, altura). A câmera
sempre mira o alvo por constraint (`Track To`), nunca por inclinação fixa: era
esse o defeito do percurso antigo, 18° fixos que faziam a câmera ver telhado
de estande.

```json
{ "id": "P19", "titulo": "Arena de Rodeio", "peso": "diferencial",
  "duracao_s": 10.0, "lente_mm": 35, "movimento": "orbita",
  "alvo": { "tipo": "rotulo", "rotulo": "ARENA DE RODEIO" },
  "camera": { "azimute_deg": 120, "dist_ini_m": 62, "dist_fim_m": 54,
              "alt_ini_m": 20, "alt_fim_m": 9, "giro_deg": 14 },
  "mira_alt_m": 2.0, "ancora": "planta" }
```

Quatro tipos de alvo, em ordem de confiabilidade: `rotulo` (posição real),
`polar` (raio/azimute em volta do centro da arena), `relativo` (deslocamento a
partir de um rótulo, usado nas âncoras estimadas) e `xy` (coordenada crua,
último recurso).

`alvo_fim` é opcional: quando presente, o alvo se desloca de `alvo` para
`alvo_fim` ao longo do plano — é o que faz o sobrevoo dos animais (P11)
percorrer do Gado Leite até Ovinos e Caprinos, em vez de orbitar um ponto
fixo.

## Onde isso vira geometria

`scripts/planos.py`:

- `carregar()` — lê o JSON, resolve cada `alvo`/`alvo_fim` contra a planta,
  crava a faixa de quadros absoluta de cada plano (contígua, filme inteiro).
- `medir()` / `conferir()` — a checagem de velocidade, sem `bpy`.
- `montar_cameras()` — só aqui o `bpy` entra: uma câmera por plano, duas
  chaves lineares (início e fim), marcador na timeline, Camera Shakify se
  estiver instalado.
- `montar_marcos()` — um cone por ponta de plano (início e fim), na coleção
  `MARCOS_CAMERA`. É a ponte para o Twinmotion: ele importa geometria mas
  **não importa câmera animada**, então os cones viajam no FBX e dizem onde
  cravar cada chave lá dentro.

`scripts/build_scene.py` chama tudo isso e ganha `--plano` (constrói só a
região dos planos pedidos, com 80 m de margem — o que segura a cena em 8–12 GB
de VRAM) e `--export-fbx` (BASE + EVENTO + MARCOS_CAMERA, sem as câmeras
animadas, para o Plano A no Twinmotion).
