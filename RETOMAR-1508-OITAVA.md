# RETOMAR — oitava sessão (15/08/2026, noite)

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**

> Este arquivo é o handoff da **oitava** sessão. O `RETOMAR.md` (972 linhas)
> continua valendo para tudo que veio antes — as 34 armadilhas, o histórico e a
> entrega da sétima sessão. **Leia este primeiro; ele diz o que mudou e o que
> está aberto.**

---

## Estado agora, em uma linha

A cena passou a obedecer o **layout que o Natan desenhou à mão**, não a planta
extraída. Arquivo vivo: **`out/cena-1508b.blend`**. Os 22 stills estão em
`out/entrega-1508/planos/`. **Há um defeito aberto:** 9 dos 16 letreiros ficam
fora do quadro.

---

## As duas ordens dele que AINDA NÃO foram implementadas

Ele deu as duas no fim da sessão, e nenhuma entrou no gerador. **Começar por
aqui.**

### 1. A entrega vira 16:9 — a especificação mudou

Palavras dele: *"sobre o painel de led eu vou exportar em 16:9 não se
preocupa."*

Isso derruba o que o `ESTADO.md` tinha como **"não negociar"**: proporção 2:1,
master 2760×1380, e a régua de tipografia de 8%/4% derivada dos 4 m de painel
LED. A cena inteira ainda está em 2:1.

**Atenção, e é contra-intuitivo:** 16:9 (1,778) é **menos largo** que 2:1
(2,000). Trocar a proporção **piora** o corte lateral dos letreiros, não
resolve. Antes de mexer, confirmar com ele o que "exportar em 16:9" quer dizer:
render nativo em 16:9, ou master 2:1 que ele reencaixa depois?

### 2. "A letra embutida no painel" + usar as imagens extraídas

Palavras dele: *"inclui a letra embutida no painel usa as imagens extraídas que
todas as resposta ou quase todas estarão lá."*

Leitura provável — **não confirmada, perguntar**: em vez de texto flutuando no
espaço 3D (que é o que existe hoje e é o que corta), o letreiro deve ser uma
**placa/painel dentro da cena**, como os letreiros reais do evento aparecem no
footage. E as respostas de como eles são estão nas imagens extraídas.

**Onde estão as imagens** (ele indicou, e foram conferidas):

| pasta | conteúdo |
|---|---|
| `F:\Extração quadros expo 2025` | **8.066 JPG, 8,2 GB** — quadros por voo (`DJI_*`) |
| `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente` | **2.108 JPG + 138 PNG + 17 MP4, 14,6 GB** — subpasta `extracao` |

Elas **não foram lidas ainda**. Ele diz que ali está a resposta de quase tudo.

---

## O defeito aberto: 9 letreiros fora do quadro

Portão novo: **`scripts/conferir_letreiro_no_quadro.py`**. Ele projeta os cantos
do letreiro na câmera do plano e compara com a área de segurança de 90%.

```
P02   a frase ocupa 138% da largura do quadro   CORTADO
P22   110%                                      CORTADO  <- é o plano final
P11   letreiro ATRÁS DA CÂMERA
P09, P16, P18   fora do enquadramento, para o lado
P06, P08, P14   cabem, mas invadem a área de 90%
```

**Não é erro de tipografia.** O tamanho da letra já passa na regra dos 8%/4% —
`letreiros.py` conferia isso. O que ninguém conferia era se a **linha inteira
cabe no enquadramento daquele plano**.

P02 e P22 pioraram porque o portal mudou de lugar, girou 92° e foi de 20 para
35 m por ordem dele. Os outros seis já estavam assim.

**A pergunta de como consertar foi feita e ele respondeu com as duas ordens
acima** — ou seja, o conserto provavelmente passa por "letra embutida no
painel", não por quebrar linha. Confirmar antes de mexer.

---

## O que esta sessão fez

### O achado grande: o rumo dos footprints estava espelhado

`cv2.minAreaRect` mudou de convenção entre OpenCV 4 e 5, e a conversão em
`extrair_footprints.py` pressupunha a antiga. **Todo rumo oblíquo era gravado
espelhado em 90°** — 70 virava 110, 108 virava 72. Os seis pavilhões de animais
estavam **37° girados**, cruzando os retângulos do desenho.

Sobreviveu tantas sessões porque **0° e 90° são os pontos fixos do espelho**:
todo prédio ortogonal passava certo.

Três fontes independentes concordaram com o valor novo (71,6°): Hough no bitmap
(71,5), perpendicular da fileira dos centros (70,3) e a sobreposição. Corrigido
medindo pelos **cantos** do `boxPoints`, que não depende de convenção.
`footprints.json` regerado; o anterior está em
`data/footprints-v2-rumo-espelhado-1508.json`.

### O ajustador visual — e o layout virou dele

`scripts/ajustar_posicoes.py` gera **`out/ajustar/ajustar.html`**, auto-contido
(planta em base64, abre com dois cliques). Move, gira, redimensiona, **cria**
blocos de 4 formas (retângulo, círculo, tenda, polígono) e **anota** cada um.

Ele usou e passou o recinto a limpo: **12 peças corrigidas e 85 blocos novos**
(51 tendas, 16 áreas, 12 retângulos, 6 círculos), quase todos anotados.
Arquivo: `data/ajustes-manuais.json`. **Manda acima de qualquer medição.**

### As nove decisões dele (registradas em `DECISOES.md` D043)

| # | resposta dele |
|---|---|
| 1 | **"pode substituir"** — bloco dele vence, peça velha vai para `DESCARTADO` |
| 2 | viu o casamento e disse **"estão certos"** |
| 3 | áreas são **superfície**; a arena de rodeio também |
| 4 | a estrada nova vence; estrada dentro de área é de chão |
| 5 | **"o portal agora está na posição correta"** |
| 6 | ditou as 5 notas que faltavam |
| 7 | **ele vai providenciar os modelos** (gado, gente, trator, foodtruck) |
| 8 | as imagens estão nas duas pastas acima |
| 9 | "recado ao redor" = **cercado** |

### Outros consertos

- **A cobertura da concha flutuava 50 cm** e, depois de corrigida, as paredes
  **furavam o telhado** em 1,45 m — altura constante sob telhado inclinado.
  Agora a empena acompanha a caída.
- **Teste de contato virou portão** que aborta o build (`CONTATOS_EXIGIDOS`).
- Portal e estrada de asfalto digitalizados do print dele
  (`data/correcao-posicao-1508.json`).

---

## Ferramentas novas desta sessão

| script | o que faz |
|---|---|
| `ajustar_posicoes.py` | gera o ajustador visual (o que ele usa) |
| `casar_blocos.py` | casa bloco dele × peça existente, em 5 classes |
| `sobrepor_planta.py` | pontos: onde a planta diz × onde o objeto está |
| `topo_planta.py` | vista de topo no referencial da prancha |
| `compor_sobreposicao.py` | junta as duas em sobreposto/contorno/lado-a-lado |
| `prova_rumo.py` | antes/depois do rumo, desenhado sobre a planta |
| `medir_rumo_no_desenho.py` | mede rumo por Hough, sem tocar no extrator |
| `stills_dos_planos.py` | 1 still por plano, com GPU exigida |
| `conferir_letreiro_no_quadro.py` | **o portão que achou os 9 letreiros** |

**Como conferir depois de mexer** (é o ciclo que pega erro de posição):

```bash
cd "E:\I.A Edit\render-expovizinhos" && "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" out\cena-1508b.blend --background --python scripts\topo_planta.py && .venv\Scripts\python.exe scripts\compor_sobreposicao.py
```

---

## Armadilhas aprendidas hoje (somam às 34 do RETOMAR.md)

**35. `minAreaRect` mudou de convenção entre cv2 4 e 5.** Medir ângulo pelos
cantos do `boxPoints`, nunca pela fórmula do ângulo. Um espelho em 90° passa
despercebido porque 0 e 90 são pontos fixos.

**36. A armadilha 34 morde mesmo estando escrita.** A primeira vista de topo
saiu em perspectiva, de lado, **sem erro na tela**, porque marcador de timeline
vence `scene.camera`. Prova que sai de câmera não conferida não é prova.

**37. JSON que vem do navegador tem BOM.** `json.loads` morre no primeiro
caractere e o build para no meio sem dizer por quê. Ler com `utf-8-sig`.

**38. Rótulo da planta é ambíguo.** "PORTAL" existe como zona estimada, como
letreiro e como estrutura. Mover pelo rótulo movia o homônimo errado — 226 m de
desvio. O JSON carrega `objeto_na_cena`.

**39. Cubo não faz duas águas.** Deslocar os vértices de cima por `1-|y|/ly`
dá zero em todo canto, e a tenda sai caixa. Pegou porque o teste mediu
**volume** (400 m³ = 10×10×4 exato), não porque alguém olhou o quadro.

**40. Casar peça por distância sozinha aprova o vizinho.** Uma tenda a 28 m
virava "substituta" do PAVILHÃO 1. E casar com `Talude`/`Poste` mandaria relevo
medido para o descarte. Ver `NAO_CASAM` em `casar_blocos.py`.

---

## Próximos passos, em ordem

1. **Perguntar a ele** o que "letra embutida no painel" quer dizer, e o que
   "exportar em 16:9" implica para o render (nativo ou reencaixe).
2. **Ler as imagens extraídas** das duas pastas — ele diz que a resposta de
   quase tudo está lá. 10 GB de JPG; começar pela subpasta `extracao`.
3. Consertar os **9 letreiros**, pelo caminho que ele definir.
4. Rodar `conferir_letreiro_no_quadro.py` até dar 0 fora do quadro.
5. Re-render dos 22 stills e conferência plano a plano.
6. Só então promover a cena para `out/cena.blend`.

## O que segue aberto, e não é desta sessão

- **Conteúdo de dentro** (gado, gente, trator, foodtruck, máquinas): ele vai
  providenciar os modelos. Até lá as áreas saem vazias **com a nota dele
  gravada no objeto** — é por ali que se sabe o que pôr.
- Cotas dos patamares (pendência 3 com o cliente): seguem estimadas.
- Escala 0,5611 m/pt: **nunca conferida com medida em campo** (pendência 4).
- Aviso `alvo de P17 não existe na planta`: **é anterior a tudo isto e é
  inofensivo** — o P17 mira uma coordenada fixa, não um rótulo.
