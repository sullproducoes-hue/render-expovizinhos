# RETOMAR — a noite do render que foi parado (15/08/2026)

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**

> Handoff da sessão de câmera e acervo de 15/08 à noite. Corre em paralelo à
> sessão que registrou **D067 e D068** — as duas mexeram no mesmo repositório na
> mesma noite, e é disso que trata a decisão mais importante daqui.

---

## Abra isto primeiro

| # | o quê | onde |
|---|---|---|
| 1 | **a cena, para revisar no Blender** | `out/cena-revisar.blend` |
| 2 | a mesma cena **sem** o conserto de câmera, para comparar plano a plano | `out/cena-revisar-1940-antes-do-conserto-de-camera.blend` |
| 3 | o que foi decidido | `DECISOES.md` **D061–D070** |

---

## O render foi parado, e por quê

Ele rodou das **18h43 às 21h39** e fez **958 de 5.475 quadros**. Parei.

Enquanto ele rodava, apareceram no `DECISOES.md` três ordens dele **da mesma
noite**, escritas por outra sessão **depois** de o render começar:

- *"Quero que deixe sem os nomes, na hora da câmera passar"* — os letreiros saem
  da cena 3D e entram por cima, na pós;
- *"A fachada do Portal Celeiro pode girar"* — `RUMO_PORTAL` foi de 73° para
  **124°**, e isso muda a cara de P02 e P22, que são a abertura e o fechamento;
- **"não renderiza nada ainda"**, junto de *"sempre quero revisar no blender
  antes de pontos importantes"*.

Os 958 quadros tinham **letreiro dentro do 3D** e o **portal no rumo antigo**.
Continuar custava **11 h de GPU** para produzir um arquivo já recusado. Parar
custou 2,6 h já gastas, e é reversível. Detalhe em **D069**.

**Nada foi apagado.** Os quadros estão em
`F:\render-agroshow\final-1508-SUPERADO-letreiros-em-3d\`, com `LEIA-ME.txt`.
**Não reaproveitar essa pasta como retomada** — `render_shots.py` pularia quadro
errado.

**O erro de método foi meu, e está escrito:** disparei treze horas de máquina e
passei as três horas seguintes escrevendo documentação sem reler o
`DECISOES.md`. A ordem estava lá havia duas horas. Quem me avisou foi a saída do
`build_scene.py`, não eu.

---

## O que a sessão entregou, e que continua valendo

### 1. A câmera reenquadrada por medida, sem alongar o filme (D070)

**21 planos** reenquadrados, **duração de nenhum alterada** — o filme continua em
**5.475 quadros, 182 s**.

Isso só foi possível com uma mudança no solver: a distância entra por **soma**,
não por fator. Num push-in o comprimento do caminho é `|dist_ini − dist_fim|`;
somar o mesmo valor nas duas pontas afasta a câmera e deixa comprimento,
velocidade e duração exatamente onde estavam.

| portão | resultado |
|---|---|
| `scripts/conferir_camera.py` | **0 problemas** |
| `scripts/enquadramento.py` | **0 reprovados em 22** |
| `scripts/planos.py --conferir` | todas as velocidades na faixa |

**Três planos passaram por melhor-esforço:** **P03, P05 e P12** — nenhum dos 891
candidatos passou em tudo. O pior é **P05, domínio 0,62**: a fachada do Pavilhão
2 ainda toma boa parte do quadro. Estão carimbados em `data/planos.json`.

**Uma tentativa foi descartada por medida:** com distância por *fator* os 22
planos passavam, mas a duração tinha de esticar e o filme ia a **273 s (+49,6%)**.
Ficou em `data/planos.DESCARTADO-solver5-273s.json`.

**Não renderizei still para provar, de propósito** — D068 manda revisar no
Blender e não renderizar. A prova são os portões e o `.blend`.

### 2. O portão que faltava: `enquadramento.py`

O `conferir_camera.py` testa só as **duas pontas** de cada plano, e por isso
aprovava planos cujo quadro é tela cheia de telhado branco. O portão novo mede o
**movimento inteiro** — 9 amostras, 45 raios pelo frustum — e a medida que pega
o defeito é **`dominio`**: quanto do quadro é **uma superfície só**. Reprovava
**18 dos 22** quando entrou.

### 3. Quatro letreiros estavam no plano errado (D062)

"Pista de Julgamentos" aparecia sobre o pátio de máquinas; "Área de Shows" sobre
o palco. Reamarrados pelo **rótulo do alvo**, não pelo título. Isso continua
valendo mesmo com os nomes fora do 3D: `data/letreiros.json` é a fonte do texto
que vai por cima na pós, e agora ele aponta para o plano certo.

**P17 e P20 ficaram sem letreiro**, de propósito — escrever "Veículos e Motos
Náuticas" e "Palco Principal" seria inventar placa, e nomenclatura de área é
material de venda. Vai como pendência, não como suposição.

### 4. A procedência do acervo está fechada (D061)

Um terço do acervo — **71 pastas, 2.770 quadros, dez planos** — estava marcado
como "pode ser de outro recinto". **O drone gravou GPS**, e a resposta estava no
disco desde 14/08.

| | |
|---|---|
| com GPS, **dentro** do recinto | **60 pastas · 2.440 quadros** |
| com GPS, **fora** | **0** |
| distância | **24 m a 387 m** (terreno de 808 × 454 m) |

O **oval** está em `DJI_20251126155520_0054_D` (168 m) e os **silos** em
`DJI_20251129182345_0168_D` (336 m) — os dois com GPS confirmado. **Nada foi
descartado.** Reprodutível: `python scripts/provar_recinto.py`.

### 5. A cadeia de entrega, ensaiada e conferida

`scripts/encode.sh` foi reescrito para **16:9 / 2560×1440** (D044) e **testado de
ponta a ponta** com o render pela metade — os três arquivos saíram, com
`_PARCIAL_<n>q` no nome. A **cartela de teste** está pronta e conferida em
`out/entrega/cartela_teste_10s.mp4`.

`scripts/fechar_entrega.sh` vigia o render, relança se ele cair e encoda no fim.
Ele **lê o total de quadros de `data/planos.json`** — não de constante: ficou
5.280 no script enquanto a decupagem passava para 5.475, e ele teria encodado
195 quadros antes do fim.

---

## O custo do filme, agora medido em regime

Os 958 quadros pagaram por um número que era estimativa: **10,0 s/quadro** e
**35 MB/quadro** — OptiX na RTX 4060, 2560×1440, beauty EXR + data EXR
(Cryptomatte, Normal, Depth) + preview PNG.

| | tempo | disco |
|---|---|---|
| filme com os três slots | **~15,2 h** | **~188 GB** |
| só PNG, sem passes | ~10,8 h | ~23 GB |

Os passes custam **39% do tempo e 165 GB**. Escolha registrada em D065.

---

## Quando ele autorizar o render

```bash
cd "E:\I.A Edit\render-expovizinhos"
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background \
    --python scripts/render_shots.py -- --blend out/cena.blend \
    --saida "F:/render-agroshow/final"
```

```bash
bash scripts/fechar_entrega.sh
```

O vigia conta os quadros, relança o render se ele morrer e roda `encode.sh` no
fim. **Pasta nova** — não reaproveitar a `final-1508-SUPERADO`.

---

## O que este projeto ainda não tem

1. **O povoamento é proxy.** 1.681 figuras que não são gente nem gado (D030). É
   o maior salto que sobrou, e nenhum ajuste de câmera compete com ele.
2. **Edificação sem textura** — o parque ainda é caixa branca.
3. **Sem logo do AGROSHOW 2026** — falta o vetor.
4. **Cotas dos patamares estimadas** (3,5 / 7 / 10 m). Um quadro de drone
   lateral resolve em minutos.
5. **P17 e P20 sem letreiro**, pelo motivo acima.
6. **P03, P05 e P12** em melhor-esforço de enquadramento.

**O final é dele** (D058) — não toquei e não vou tocar.


---

## Armadilhas novas (47 e 48)

**47. Estabilizador de vídeo apaga o GPS.** Os exports `_stabilized` só carregam
o stream de vídeo — o `djmd` da DJI não é copiado, e sobra só
`comment = Original filename: …`. Onze voos ficaram sem coordenada por isso, e os
originais não estão mais no disco. **Extrair telemetria do original antes de
estabilizar.**

**48. `ray_cast` devolve o objeto no 5º campo, não no 6º.** A ordem é
`(ok, local, normal, índice, OBJETO, matriz)`. Trocar entrega uma `Matrix` onde
se espera um `Object`, e o erro só aparece em tempo de execução — no meio de uma
varredura de vinte minutos.

**49. `drawtext` do ffmpeg e a letra da unidade no Windows.** Dentro de um
filtro, `:` é separador de opção, e todo caminho absoluto do Windows começa com
`C:`. Escapar é um pântano que varia por build, e o erro (*"No option name
near…"*) não diz que o problema é a unidade. A saída sem pântano: **copiar a
fonte para a pasta de saída e chamar por caminho relativo**, com o ffmpeg rodando
lá dentro. É o que `encode.sh` faz — e foi achado **ensaiando a cadeia de encode
com o render pela metade**, que é justamente para isso que se ensaia cedo.

**50. `metadata=print` do ffmpeg escreve em nível INFO.** Com `-v error` a linha
some, e um portão que lê essa saída **passa vazio** em vez de reprovar. O portão
da cartela agora aborta se não conseguir medir — portão que não mede não pode
passar em silêncio.
