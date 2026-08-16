# ENTREGA — NOITE-3-QUADROS, 16/08/2026

Portão a portão. **N/A não é vermelho** — é escopo que o contrato tirou desta
sessão de propósito.

---

## Os portões

| portão | onde mede | estado | número |
|---|---|---|---|
| **render roda** | `scripts/prova_cycles.py` | ✅ **verde** | 7,5 s a 960×540/64 · `NVIDIA GeForce RTX 4060 [OPTIX]` · saída 659.302 bytes |
| **dispositivo é GPU** | idem, aborta se não for | ✅ **verde** | OptiX ativo, CPU desligada. A armadilha do D009 não pegou |
| **configuração gravada** | `data/render-config.json` | ✅ **verde** | adaptativa 10/50, denoise OptiX, ordem de sacrifício da VRAM, armadilha 34 |
| **preset × cheio** | `out/heroi/Q1-preset-x-cheio.jpg` | ✅ **verde** | sem diferença visível · 13 s contra 18 s · **preset mantido** (D076) |
| **fotogrametria lida** | `model_analyzer` nos 6 modelos | ✅ **verde** | 100/100 e 150/150 imagens · erro 0,60 a 0,89 px · todos ≤ 1,5 (D072) |
| **Q1 · forma** | `out/heroi/Q1.jpg` | 🔴 **REPROVADO 2×, consertado 2×** | 1ª rodada: 8 divergências, 7 corrigidas · 2ª rodada: o enquadramento **não tinha sido corrigido** (câmera mirava x=0) e o frontão é **assimétrico** — remedido, e as duas inclinações agora saem sozinhas batendo a foto (21,3°/31,0° contra 22,3°/30,9°) |
| **Q2 · forma** | `out/heroi/Q2.jpg` | 🔴 **REPROVADO, consertado** | 7 divergências · caixa cênica **60% alta demais** (razão 4,06 medida contra 6,51) e **1,0 a 2,1 m de céu aberto** entre parede e cobertura · **6 corrigidas**, a 7ª virou proposta (D084) |
| **Q3** | — | ⬜ **não aberto, e corretamente** | o gatilho do adendo é "zero reprovação em aberto nos dois". O Q1 foi reprovado, então as horas do Q3 foram para ele — que é o que a regra manda |
| **textura** | `./.venv/Scripts/python.exe scripts/conferir_texturas.py` | ✅ **verde, conferido por mim** | exit 0 · albedo dos 6 materiais com erro de 0,01% a 0,37% contra a cor medida · Diffuse neutro, normal OpenGL |
| **asset com licença** | `assets/_procedencia.json` | ✅ **verde, conferido por mim** | 46 entradas · **0 sem licença, 0 sem URL, 0 arquivo faltando** · 44 CC0, 1 domínio público (SRTM), 1 CC-BY 4.0 com atribuição · nenhum muro de login atravessado, nenhuma conta criada |
| `provas_luz.py` | — | **N/A** | fora do escopo desta sessão, por contrato |
| `conferir_sol.py` | — | **N/A** | idem |
| `enquadramento.py` | — | **N/A** | idem |

---

## O que está na mesa

| arquivo | o que é |
|---|---|
| `out/heroi/Q1.jpg` | **folha `real \| 3D` do portal** — a foto do cliente ao lado do 3D, mesma proporção |
| `out/heroi/Q2.jpg` | **folha `real \| 3D` da arena** |
| `out/heroi/Q2-antes-depois.jpg` | **o antes/depois da arena** — é a imagem que mais vende |
| `out/heroi/Q1-preset-x-cheio.jpg` | a prova de que o preset basta |
| `out/cena-heroi-q1.blend` · `out/cena-heroi-q2.blend` | para abrir e conferir, que é como você confere |
| `F:\heroi\Q1\final-2560.png` · `F:\heroi\Q2\final-2560.png` | entrega 2560×1440 |
| `out/heroi/_materiais-amostra.jpg` | os materiais, cru → deiluminado → mapa final |
| `out/heroi/_nuvens-o-que-cobrem.jpg` | o que cada nuvem de pontos reconstruiu de verdade |

---

## Uma armadilha que vale mais que os números

**Portão só vale rodado com o `.venv` do projeto** (D082). Com o `python` do PATH
— que é o venv do Hermes — `conferir_texturas.py` morre em `cv2` no meio da
execução. E pior: eu li `EXIT=0` logo abaixo do traceback, porque o `$?` era do
`tail` do pipe, não do Python. **Portão dentro de pipe não reporta o próprio
código de saída**, e portão que parece verde é pior que portão vermelho.

---

## Os números que mudaram a noite

- **Render é barato nesta cena.** 7,5 s a 960×540. O Q1 fechou em sete
  iterações porque cada teste custava dez segundos — e é isso que permitiu
  olhar contra a foto real toda vez, em vez de adivinhar.
- **A fotogrametria já tinha fechado desde 15/08 às 21h47.** 42.090 pontos,
  erro de 0,80 px. Ninguém tinha aberto o arquivo.
- **A telha do recinto é ondulada, não trapezoidal.** Passo de 2,432 m, medido
  por autocorrelação. O asset CC0 que estava no contrato era o perfil errado.
- **O vão entre pilar e telhado dos pavilhões é de 16 a 26 cm**, e nenhum portão
  cobria isso — `CONTATOS_EXIGIDOS` só declara os 3 pares da concha. Fica na
  fila; não era escopo desta noite.

---

## O que eu errei, e está registrado

1. **Li a pasta, não o dado** (D072). Declarei seis fracassos de fotogrametria
   sem abrir um único arquivo de modelo.
2. **Quase repeti o erro pelo avesso** (D073). A nuvem `fazendinha` tem a melhor
   métrica do lote — e reconstruiu uma multidão à noite, inútil como geometria.
   Métrica boa medindo a coisa errada continua sendo a coisa errada.
3. **Booleano sobre face coincidente** comeu o corpo central inteiro do portal,
   sem erro na tela. Trocado por montagem em partes.
4. **Sinal de rotação invertido** no coroamento e na treliça — as tábuas viraram
   asas acima do telhado. É a armadilha de Euler que a skill do próprio projeto
   nomeia.
5. **Sol apontado ao contrário**: eu iluminava na direção do sol em vez de dele
   para a cena. Não dá erro, só deixa a fachada chapada.
6. **A cortina de árvores caiu em cima do palco** quando encolhi o oval da
   arena — ela era posicionada relativa ao centro do oval.

7. **Não portei uma correção de um arquivo para o outro.** O filtro de asset que
   consertou a árvore dentro do vão no Q1 **não foi para o `heroi_arena.py`** —
   e lá os 16 cartões-fonte viraram gravetos de pé sobre a grama, instanciados
   19 vezes. Consertar num lugar e esquecer o outro é o custo de ter dois
   construtores com o mesmo problema.

8. **A mesma família de erro, três vezes na mesma noite.** Pilar e telhado do
   pavilhão divergindo 16–26 cm; mourão encostando rente no portal; parede e
   cobertura da concha deixando 2,1 m de céu aberto. **Quando duas peças se
   encontram, UMA função decide a cota das duas** — e eu escrevi essa regra no
   começo da noite antes de violá-la duas vezes.

9. **E sete que a folha lado a lado NÃO pegou** (D081). O verificador abriu os
   arquivos e mediu: o chanfro da cumeeira estava **3,8× estreito**, o letreiro
   **58% largo**, a ala direita **cortada pelo quadro**, a treliça do frontão
   **enterrada no coroamento**, e uma **árvore de 12 m plantada dentro do vão de
   passagem** — que é justamente o plano de fechamento do filme.

   Eu tinha olhado esse quadro contra a foto **sete vezes**. Olhar lado a lado
   pega o que está grosseiramente errado; **medir em pixel os dois** pega o que
   está 20% errado — e 20% errado é o que faz a imagem parecer *quase* o lugar.

   **Quadro-herói não fecha sem alguém medindo, e esse alguém não pode ser quem
   construiu.** É o argumento inteiro a favor do verificador separado.

Os seis primeiros não apareceram em log nenhum — apareceram **olhando o quadro
contra a foto**. O sétimo grupo não apareceu nem assim: só caiu quando alguém
**mediu os dois em pixel**. São dois instrumentos diferentes, e nenhum substitui
o outro.
