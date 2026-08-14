# Proposta de estrutura — render em 3 dias

Prazo, a partir de 14/08/2026: **domingo 16/08, tudo ajustado; segunda 17/08 à
tarde, renderizado e exportado o `.mp4` para o cliente.** O que se orça em 4 a
8 semanas de estúdio de archviz, em 3 dias. Máquina: GPU de 8–12 GB de VRAM.
Verba de asset: **zero** — só CC0 e gratuito.

Este documento é a proposta que decidiu a estrutura do repositório a partir
de 14/08. Ver `ESTADO.md` para o que já está feito, `docs/PLANOS.md` para a
decupagem.

---

## O achado que mais mudou o filme

Medido contra a planta: o percurso antigo (16 pontos, curva bezier única,
128 s) fazia **1.152 m em 128 s = 9,0 m/s (32 km/h)**. A faixa cinematográfica
de drone é 1,3–2,2 m/s em órbita/push-in e 3,6–6,7 m/s em sobrevoo — o
percurso rodava de 1,3 a 7× acima disso. Nessa velocidade não se lê placa nem
se reconhece área.

A saída: a câmera virou dado. `data/planos.json` declara 22 planos, cada um
com alvo, lente, altura, movimento e duração, todos dentro da faixa
cinematográfica (`python3 scripts/planos.py --conferir`). Ver `docs/PLANOS.md`.

## Motor: decisão e portão de segurança

- **Cycles no filme inteiro não cabe.** 4.635 quadros em 2760×1380 numa GPU
  de 8–12 GB é trabalho de dias; em fazenda, archviz em animação sai a
  US$ 0,08–0,65/quadro (US$ 370–3.000 no total). Verba zero. Fica para uma
  imagem-chave, se sobrar tempo — não para o filme.
- **EEVEE Next só roda em GPU** e é rápido o bastante, mas com verba zero
  gente, vegetação e materiais viram semanas de garimpo CC0.
- **Twinmotion 2026 é gratuito com direito comercial abaixo de US$ 1 M de
  faturamento** e traz pronto o que falta: pessoas animadas, vegetação,
  veículos, materiais, LOD automático, a ferramenta *Populate*. Render em
  tempo real — dezenas de minutos, não uma noite inteira.

**Plano A — Blender é a fonte da geometria, Twinmotion veste e renderiza.**

```
build_scene.py --export-fbx  →  Twinmotion (vestir, popular, luz, render)  →  NLE (letreiros, cor, entrega)
   geometria + MARCOS_CAMERA            cones dizem onde cravar cada chave         3 arquivos + cartela
```

**Plano B — rede de segurança: EEVEE Next no Blender**, mesma geometria
(`build_scene.py --out`), mesma decupagem, sem sair do repositório.

**Portão de decisão: sábado 15/08, 12h.** Se até lá o Twinmotion não estiver
segurando a cena inteira com fluidez, cai para o Plano B e não se olha para
trás. O risco é real e medido: recomenda-se 12 GB+ de VRAM para site grande em
Twinmotion, e a máquina tem 8–12 GB.

**Calibração antes de fechar o cronograma de domingo:**

```bash
blender --background --python scripts/render_shots.py -- \
    --blend out/cena.blend --plano P19 --quadros 24 --cronometrar
```

Projeta o tempo do filme inteiro a partir do plano mais pesado. Acima de
~11 h não cabe na noite de domingo — nesse caso, corta samples, corta
vegetação distante, ou vai de Twinmotion.

## Ordem de trabalho na cena

1. **Luz antes de material.** Sol pelo addon Sun Position
   (−25,73144 / −53,07627, horário do evento) + HDRI CC0 de fim de tarde do
   Poly Haven no lugar de `construir_ceu()`. Sol errado denuncia CG mais
   rápido que polígono.
2. **Materiais: variação macro, não textura nova.** Ruído de baixa frequência
   (escala 1–3) em Overlay a 0,2–0,35 sobre a cor base quebra o padrão
   repetido visto do alto — o que mais entrega CG num terreno de 800 m.
   Textura PBR CC0 só onde a câmera desce.
3. **Gente:** Twinmotion *Populate* (Plano A) ou Mixamo + amostras gratuitas
   da Renderpeople em geometry nodes (Plano B). Nunca a mesma pose duas vezes
   no mesmo quadro; ao longe, billboard.
4. **Portal, palco e camarotes modelados** — hoje são caixa. O portal é o
   primeiro e o último plano do filme.

## Render e passes (Plano B)

EEVEE Next não tem passe Vector nem cryptomatte com motion blur. Efeitos de
tela somem na borda do quadro em câmera com movimento — por isso
`configurar_render()` liga Overscan em 7%. Motion blur por acumulação, 6
passos (equilíbrio entre gradiente limpo e tempo de render). `dither_intensity
= 1.0` de saída, porque um céu de fim de tarde em 2:1 é um degradê grande e um
painel LED em 8 bits bandeia.

## Entrega — três arquivos, sempre

| Arquivo | Uso |
|---|---|
| `2760x1380` ProRes 422 HQ `.mov` | master |
| `2760x1380` H.264 `.mp4` | principal do operador |
| `1380x690` H.264 `.mp4` | reserva leve |
| cartela de teste 10 s | marcas de canto + caixa de 90% |

Gerados por `scripts/encode.sh out/final out/entrega` a partir da sequência
de PNG renderizada por `render_shots.py`.

## Cronograma

| Quando | Entrega |
|---|---|
| **Sex 14, manhã** | `planos.json` com os planos; câmeras geradas; animatic cinza exportado |
| **Sex 14, tarde** | Animatic aprovado pelo cliente. Luz real (sol + HDRI). FBX exportado |
| **Sáb 15, manhã** | Twinmotion: importar, escala conferida, materiais |
| **Sáb 15, 12h** | **PORTÃO.** Segura? Segue. Não segura? Plano B, EEVEE |
| **Sáb 15, tarde** | Vegetação e gente. Portal, palco e camarotes modelados |
| **Dom 16** | Passada plano a plano. Diferenciais primeiro. Trava a imagem |
| **Dom 16, noite** | Render roda sozinho |
| **Seg 17, manhã** | Letreiros no NLE, cor, grão, cartela de teste |
| **Seg 17, tarde** | Os 3 arquivos + cartela para o cliente |

## Conferência antes de mandar

1. Arena de rodeio sem arquibancada — só pista, camarotes dos dois lados,
   palco de frente.
2. A palavra "Kids" não aparece em lugar nenhum.
3. Fazendinha: nome grande, descrição pequena embaixo.
4. Frases literais conferidas caractere a caractere.
5. Último plano sai pelo portal.
6. Quadro reduzido a 1379 px de largura, olhado de longe.
7. Todo texto dentro de 2484 × 1242 centralizados.
8. Nenhuma tarja embutida. 2:1 limpo, sempre.
9. Os 3 arquivos rodados até o fim antes de mandar.

## Riscos, com a saída de cada um

| Risco | Saída |
|---|---|
| VRAM estoura no Twinmotion | Portão de sábado 12h → Plano B |
| Render de domingo não fecha na noite | Calibração de 24 quadros decide antes, não depois |
| Escala nunca conferida em campo | Conferir contra pessoa de 1,75 m no primeiro plano vestido |
| Processador do telão desconhecido | Cartela de teste + 2:1 limpo + área de 90% |
| Banding no céu | Dither 1,0 + ProRes 10 bits + grão |
| Falha de reprodução ao vivo (já aconteceu) | Três arquivos, sempre, incluindo a reserva leve |

## O que fica de fora, e por quê

- **Fotorrealismo** — não foi pedido; a meta é qualidade de jogo.
- **Cycles no filme** — não cabe na janela de render.
- **DEM global** — 30 m de resolução apagam os patamares.
- **Alturas dos patamares confirmadas** — seguem estimadas; um quadro de
  drone lateral resolve, mas não chegou.
- **Redesenho vetorial da planta** — doutrina 2.5D, suspensa.
