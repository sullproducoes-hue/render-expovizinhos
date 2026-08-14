# Triagem do footage de drone — AGROSHOW 2026

Registro corrido da avaliação do material aéreo. Preenchido lote a lote,
conforme as folhas de contato chegam. **Este arquivo é a memória da triagem** —
o que não estiver aqui se perde quando a conversa for compactada.

---

## O que estamos triando

**Os arquivos estão na máquina do cliente, em `E:\Projetos todos\Mapa -
agroshow\Brutos Expo`** — não é preciso esperar o envio para o Drive terminar. O Drive é
cópia: envio por rclone de **186 arquivos, ~168 GiB**, começado às 11h52 de
13/08, com fim previsto por volta das 16h. Os arquivos são DJI (alguns com
sufixo `_stabilized`), mais pelo menos um `.MOV` de celular e um `FPV.mp4`.

Comandos, no Windows, a partir da pasta do projeto:

```bat
python scripts\extrair_quadros.py --metadados --pasta "E:\Projetos todos\Mapa - agroshow\Brutos Expo"
python scripts\extrair_quadros.py --triagem   --pasta "E:\Projetos todos\Mapa - agroshow\Brutos Expo"
python scripts\extrair_quadros.py --densa DJI_0960-015.MP4 --intervalo 2 ^
    --pasta "E:\Projetos todos\Mapa - agroshow\Brutos Expo"
```

Precisa da build completa do ffmpeg (`winget install Gyan.FFmpeg`). A enxuta
não traz `drawtext`, e aí as folhas saem sem o timecode gravado no quadro — o
script avisa no arranque quando isso acontece. `--triagem` pode rodar várias
vezes: ele pula o que já tem folha pronta.

Nem tudo é do mesmo voo nem do mesmo dia: há pelo menos um arquivo de novembro
de 2025 (`DJI_20251128230040_0165_D`), gravado às 23h — noturno. Data e hora
entram na ficha porque **o LOOK LOCK é golden hour**: material de meio-dia ou
de noite serve para geometria, não para cor.

---

## Método

Três passadas, da mais barata para a mais cara. Roda tudo na máquina do
cliente com `scripts/extrair_quadros.py` — aqui não há ffmpeg, não há disco
para 168 GiB e o proxy bloqueia o domínio do Drive.

**1. Metadados.** `--metadados` despeja `ffprobe` em JSON, tenta a faixa de
legenda embutida e, se houver exiftool, os átomos DJI. Custa segundos por
arquivo. Se a telemetria aparecer, ela responde por medida o que os quadros
responderiam por proporção: altitude relativa dá a cota dos patamares, e
altitude com distância focal dá a escala do recinto.

**2. Triagem — 10 quadros por vídeo, por mediana.** `--triagem` divide o
trecho útil do vídeo em 10 fatias iguais e, dentro de cada fatia, amostra 3
candidatos e fica com o **mediano por peso do JPEG** — nem o maior, nem o
menor. Um corte de plano, um quadro preto de transição ou um pan borrado
comprimem para um arquivo bem menor que um quadro nítido com detalhe de
verdade; a mediana descarta esses extremos sem decodificar o vídeo inteiro.
`--candidatos-mediana 1` desliga isso e volta a pegar o meio exato de cada
fatia. O resultado é **uma folha de contato por vídeo**, grade 5×2, com nome e
timecode gravados em cada célula. Uma imagem por fita em vez de dez soltas: é
o que permite passar por 186 arquivos sem estourar o contexto. O timecode
gravado é o que me deixa pedir depois "o trecho de 01:23 do DJI_0960" em vez
de descrever o quadro.

**3. Passada densa.** Só nos aprovados: `--densa <arquivo> --intervalo 2`,
resolução cheia, folhas em lotes de 12. É o "máximo de quadros possível" na
prática — reviso em lotes e **anoto o achado a cada lote**, aqui e em
`docs/achados-drone.md`.

---

## Os sete eixos

Cada vídeo recebe 0 a 3 em cada eixo. Os eixos não são qualidade de imagem —
são o que o projeto precisa e ainda não tem.

| Eixo | Para que serve na cena | Estado hoje |
|---|---|---|
| **TOP** Topografia | cotas da bacia da arena, `PATAMARES` | estimadas: 3,5 / 7 / 10 m |
| **ESC** Escala | confere 0,5611 m/pt, `ESCALA` | nunca conferida em campo |
| **EST** Estruturas | portal, pavilhões, leilões, camarotes | caixas com proporção assumida |
| **MAT** Materiais | grama, brita, telha, lona | procedurais, sem referência |
| **LUZ** Luz e cor | casa o LOOK LOCK com o real | golden hour por decisão |
| **ENT** Entorno | vias, estacionamento, mata | terreno vazio fora do recinto |
| **MOV** Movimento | cadência do voo, `PERCURSO` | ritmo definido no olho |

**Veredito:**

- **P — prioritário**: entra na passada densa.
- **A — apoio**: consulta pontual, por timecode.
- **D — descartar**: decolagem, pouso, take repetido, exposição perdida,
  enquadramento sem informação nova.

Entre duas versões do mesmo voo, a `_stabilized` ganha — menos micro-tremor,
leitura melhor de linha reta, que é o que importa para medir.

---

## Fichas

Nenhuma folha de contato chegou ainda. A tabela abaixo é preenchida lote a
lote; a coluna "achado" resume o que aquele vídeo entregou de concreto.

| Vídeo | Dur. | Res. | TOP | ESC | EST | MAT | LUZ | ENT | MOV | Veredito | Achado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| _(aguardando)_ | | | | | | | | | | | |

---

## Prioridade de leitura

Quando as folhas chegarem, procuro nesta ordem — é a ordem em que o achado
corrige código:

1. **Arena vista de lado.** Resolve a maior incerteza aberta da cena: as três
   cotas da bacia são estimativa por proporção, e um quadro lateral com
   elemento de altura conhecida fecha isso em minutos.
2. **Portal de frente e de três quartos.** Ele é o primeiro e o último plano
   do vídeo; qualquer erro nele custa caro.
3. **Qualquer estrutura medível** contra a planta, para confirmar a escala.
4. **Pavilhões e Recinto de Leilões** — cor de telha, altura real, beiral.
5. **Além do recinto** — o plano final olha para fora, e lá hoje não há nada.
6. **Chão** — grama viva, grama pisada, brita, terra da pista. É o que separa
   material procedural de material com referência.
7. **A Fazendinha**, se ela aparecer. Não existe rótulo dela na planta, e um
   quadro que mostre a pista de tiro de laço resolve uma pendência de cliente.
