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

22 planos, 4.635 quadros, **154 s (2,6 min) a 30 fps.** Os 19 títulos do
`docs/BRIEFING.md` mapeiam 1:1 nos planos com título; os que não têm título
(P15, P22) são continuação do plano anterior, sem letreiro novo.

| # | Título na tela | Movimento | Lente | Dur. | m/s | Âncora |
|---|---|---|---|---|---|---|
| P01 | Estacionamento | subida | 24 mm | 7.0 s | 3.6 | planta |
| P02 | É daqui que sai o alimento que sustenta o mundo | push-in | 35 mm | 9.0 s | 2.1 | planta |
| P03 | Pavilhão 1 — Indústria, Comércio e Prestação de Serviços | orbita | 35 mm | 6.0 s | 1.9 | planta |
| P04 | Praça de Alimentação Coberta | push-in | 35 mm | 5.5 s | 2.1 | planta |
| P05 | Pavilhão 2 — Indústria, Comércio e Prestação de Serviços | orbita | 35 mm | 5.0 s | 1.8 | planta |
| P06 **·** | Mercado do Produtor | push-in | 50 mm | 9.0 s | 2.1 | planta |
| P07 | Agroindústrias | travelling | 35 mm | 5.0 s | 1.6 | planta |
| P08 **·** | Café Colonial | push-in | 50 mm | 9.0 s | 2.0 | planta |
| P09 | Praça de Alimentação Aberta | sobrevoo | 35 mm | 9.0 s | 6.1 | planta |
| P10 | Recinto de Leilões | push-in | 35 mm | 6.0 s | 2.0 | planta |
| P11 | Exposição de Animais | sobrevoo | 35 mm | 11.0 s | 6.3 | planta |
| P12 | Pista de Julgamentos | orbita | 50 mm | 5.0 s | 1.5 | planta |
| P13 | Expositores Externos | sobrevoo | 35 mm | 5.5 s | 6.0 | derivada |
| P14 **·** | Fazendinha | push-in | 35 mm | 10.0 s | 2.2 | estimada |
| P15 | — (continua P14) | orbita | 50 mm | 6.0 s | 1.6 | estimada |
| P16 | Máquinas, Equipamentos e Implementos Agrícolas | sobrevoo | 35 mm | 6.0 s | 5.8 | derivada |
| P17 | Veículos e Motos Náuticas | travelling | 50 mm | 5.0 s | 1.3 | derivada |
| P18 | Área de Shows | sobrevoo | 35 mm | 5.5 s | 5.9 | derivada |
| P19 **·** | Arena de Rodeio | orbita | 35 mm | 10.0 s | 2.1 | planta |
| P20 | Palco Principal | push-in | 50 mm | 7.0 s | 1.9 | planta |
| P21 | Aqui será um grande balcão de negócios | subida | 24 mm | 7.0 s | 4.3 | planta |
| P22 | — (saída pelo portal) | push-in | 35 mm | 6.0 s | 2.1 | planta |

**·** marca os quatro diferenciais (P06 Mercado do Produtor, P08 Café
Colonial, P14/P15 Fazendinha, P19 Arena de Rodeio) — todos com 9–16 s de tela
somada, acima dos 5–7 s do corpo do filme, como o cliente pediu.

Regenere esta tabela com:

```bash
python3 scripts/planos.py --tabela
```

---

## As três âncoras

Cada plano declara `ancora`, e isso não é decoração — é o nível de confiança
da posição:

- **`planta`** — o alvo é um rótulo real de `data/mapa_agroshow26.json`.
  16 dos 22 planos. Confiável.
- **`derivada`** — não existe rótulo, mas existe dado: raio e azimute vêm da
  bacia (aglomerados reais de estandes da série C, mesma fonte de
  `PATAMARES`). P13, P16, P17, P18 — o anel de máquinas/veículos e a área de
  expositores externos, que o áudio descreve mas a planta não rotula.
- **`estimada`** — **não existe na planta.** P14 e P15, a Fazendinha, foram
  posicionados só pelo áudio do cliente (*"desce pro lado da pista de tiro de
  laço"*), entre a pista de julgamentos e o anel. **Confirmar com o cliente
  antes do render final** — é a única posição do filme que não tem apoio em
  dado nenhum, e a Fazendinha é um dos quatro diferenciais.

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
