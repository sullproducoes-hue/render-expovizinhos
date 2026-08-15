# DECISÕES — registro de ambiguidade resolvida sem perguntar

**AGROSHOW 2026 · render-expovizinhos**

Este arquivo existe por ordem do Natan, 15/08/2026, literal:

> *"Trabalhe de forma autônoma até o fim. Não me pergunte nada: quando houver
> ambiguidade, escolha a opção mais conservadora, registre a decisão e o motivo
> em DECISOES.md e siga. Se algo travar de vez, pule para a próxima tarefa da
> fila e documente o bloqueio."*

Toda linha aqui é uma escolha que eu fiz no lugar dele. Ele pode reverter
qualquer uma — é para isso que o motivo está escrito.

**Precedência em vigor:** ordem do Natan → `reference/DOUTRINA-RENDER-3D.md` →
revisão do plano (15/08) → doutrina do projeto.

---

## 2026-08-15

### D001 · Snapshot antes da etapa destrutiva
**Ambiguidade:** o plano manda "snapshot versionado", sem dizer onde nem o quê.
**Decisão:** `out/_snapshots/2026-08-15_pre-formas-reais/` com `cena.blend` e
`cena-empacotada.blend`, md5 conferido (`57280DC6…` bate nos dois).
**Motivo:** conservador — copiar os dois custa 81 MB e devolve a cena inteira,
inclusive as texturas, se a etapa 3 der errado. `nada se apaga`.

### D002 · Onde a doutrina dele mora
**Ambiguidade:** o arquivo veio em `C:\Users\natan\Downloads`, que é pasta volátil.
**Decisão:** copiado para `reference/DOUTRINA-RENDER-3D.md` e citado na precedência
do agente. O original fica onde está — não apago nada dele.
**Motivo:** `Downloads` some numa faxina; doutrina que rege o processo não pode
depender de pasta temporária.

### D003 · Divergências entre a doutrina e o que já foi decidido por ele
A doutrina é ordem norteadora, mas **ordem direta dele vence**. Divergências
registradas, sem mudar nada por conta própria:

| ponto | doutrina | o que vale aqui | por quê |
|---|---|---|---|
| Golden hour | *"não fazer golden hour em todas as imagens"* `[Provável]` | **golden hour fica** | ordem do cliente; e a regra da doutrina é para stills de prazo curto, não para um filme com hora declarada e HDRI casado por medição |
| Samples | Noise Threshold 0,01 + max alto `[Certo]` | **128 / 0,1 continua** | config ditada por ele em 14/08. Medido no passo 0.4 e levado como número — não mudo sozinho |
| Saída | EXR MultiLayer + Cryptomatte `[Certo]` | **EXR + Cryptomatte** | ele decidiu em 15/08; supera o PNG-8 de 14/08. O espelho PNG continua para o `encode.sh` |
| Crowd 3D | *"não colocar crowd 3D, use billboard"* `[Provável]` | **proxies ficam por ora** | a decisão 14b (Plano A vs B) é dele e ainda está aberta; billboard vira proposta dentro da 14b |

### D004 · Cryptomatte Levels 2 — conferido, não assumido
**Ambiguidade:** a revisão manda "2, no máximo 3", contra o default 6, com o
argumento de que arquitetura opaca não precisa de mais.
**Decisão:** **2**, e agora está medido: dos pixels que têm objeto,
**99,69% fecham cobertura em 1,0**; os 0,16% parciais do quadro inteiro são
borda de folhagem. **Fecha.** Prova em `scripts/conferir_matte.py`.
**Motivo:** o argumento estava certo, mas argumento não é medida — e o custo de
descobrir tarde era a fila inteira.

### D005 · `Position` e `Vector` fora do slot de dado
**Ambiguidade:** o plano listava os quatro passes de dado; medido, o total dos
três slots deu **266 GB de 299 GB livres** no F:. 33 GB de folga para um render
de 47 s/quadro que roda dias é folga que não existe.
**Decisão:** cortados os dois. Restam Cryptomatte, Depth e Normal — e o total
caiu para **199 GB**, com 100 GB de folga.
**Motivo, item a item:** `Vector` serve para borrar em pós o que saiu nítido, e
**o motion blur já é renderizado na câmera** — guardar os dois é pagar duas
vezes pelo mesmo borrão. `Position` é recuperável de `Depth` mais a matriz da
câmera, que está no `.blend` e no `planos.json`. Nenhum dos dois entrega nada
que já não esteja lá.
**Bônus da mesma rodada:** `Normal` e `Position` estavam declarados como RGBA e
gravavam um quarto canal morto. Agora são `VECTOR` (XYZ).

### D006 · A armadilha do `save_as_render`, provada nos dois lados
Não bastava configurar: o defeito (AgX assado dentro do EXR, ou PNG lavado) é
invisível até tarde. Medido no quadro do smoke:

| | evidência | veredito |
|---|---|---|
| **beauty EXR** | **18,5% dos pixels acima de 1,0**, máximo 6,80 | linear de cena, headroom inteiro. Nenhum view transform aplicado — AgX comprime tudo abaixo de 1,0 |
| **preview PNG** | máximo 0,922; mediana 0,549 contra 0,705 do sRGB ingênuo do mesmo pixel | AgX aplicado, e é AgX mesmo, não gama 2,2 |

### D007 · Nome de arquivo com 5 dígitos
**Ambiguidade:** o File Output do Blender 5.x nomeia sozinho, e o primeiro
smoke gravou `Untitled.exr` e `Image.png` — o mesmo arquivo por cima a cada
quadro.
**Decisão:** `saida.nomear()` crava `{quadro:05d}` antes de cada render, e o
item do slot PNG tem nome vazio.
**Motivo:** cinco dígitos é o que o `encode.sh` procura (`%05d.png`); quatro
entregariam PNG que o ffmpeg não enxerga. E nome repetido quebra a retomada do
`render_shots.py`, que decide o que já foi feito olhando o disco.

### D009 · ACHADO — o render vinha na CPU, e ninguém sabia

Não é decisão minha, é defeito encontrado, e é o maior desta sessão.

A cena guarda `cycles.device = "GPU"`. **O dispositivo, não.** Ele mora nas
*preferências*, que são da instalação do Blender e não do arquivo `.blend`.
Aberto numa sessão limpa, o `cena.blend` anunciava GPU e as preferências vinham
com `compute_device_type = NONE`, **nenhum dispositivo marcado**. É o fallback
silencioso da doutrina §12, acontecendo há sessões.

| | tempo do quadro | filme (4.635 quadros) |
|---|---|---|
| como estava (CPU, sem saber) | 47 s a 100% | **~60 h** |
| com OptiX ligado | ~11,6 s a 100% | **14,9 h** |

O `RETOMAR.md` declara *"36–38 s/quadro → 46–49 h o filme"*. **Esse número é de
CPU** e nunca foi de GPU. Vai corrigido.

**Conserto:** `medir_render.garantir_gpu()` liga OptiX, marca as duas entradas
da RTX 4060 e **desliga a CPU** — com os dois marcados o Cycles divide o
trabalho e o tempo medido deixa de ser o da placa. O mesmo tem que entrar no
`render_shots.py` antes da fila. Achou a placa: `NVIDIA GeForce RTX 4060`.

### D010 · Samples: a config dele de 14/08 se sustenta, e agora está medida
Medido no P08 (Café Colonial, 50 mm, câmera a 4,5 m — o plano mais fechado, com
luz indireta de dentro de estrutura), a 50%, os quatro cruzamentos:

| config | tempo | ruído local |
|---|---|---|
| 128 / 0,1 **sem** denoise | 3,9 s | 0,00765 |
| **128 / 0,1 com denoise** | **2,9 s** | **0,00261** |
| max / 0,01 sem denoise | 10,1 s | 0,00374 |
| max / 0,01 com denoise | 10,3 s | 0,00262 |

**0,01 custa +255% de tempo e entrega −0,4% de ruído.** Empatam. O OpenImage
Denoise já resolveu o granulado; baixar o limiar é 38 horas a mais por uma
diferença que não existe na imagem — e o filme sairia em 53 h no lugar de 14,9 h.

**A doutrina pede 0,01 `[Certo]` e aqui ela não se aplica**, e o motivo é o que
ela mesma diz na §7.2: a regra existe contra *compensar samples baixos com
denoise agressivo*. O denoise aqui não é agressivo — é OIDN com prefilter Fast e
qualidade Balanced, e a medida mostra que 128 samples **já converge** nesta cena.
Nada muda sem ele; o número está aqui para ele decidir.

### D011 · O denoise fica no render, e agora por medida
O contrato de saída já declarava `denoise.onde = "render"` por herança da ordem
dele. Medido: com denoise o quadro fica **26% mais rápido** (2,9 s contra 3,9 s
— o denoise deixa o amostrador adaptativo parar mais cedo) e o ruído cai 66%.
Não há caso para mover para post: seria mais lento e exigiria guardar os passes
de denoise em float 32 no slot de dado.

### D012 · A projeção de disco de um plano só estava 43% errada
**Ambiguidade:** o critério de aceite pedia "tabela de disco recalculada com
números reais". Recalculei — de **um** quadro, o P01.
**O que aconteceu:** o P01 é o plano mais aberto do filme, com metade do quadro
em céu liso, e céu comprime quase de graça. Amostrados **seis** planos, a média
real deu **63 MB/quadro** e o filme **285 GB de 300 GB livres**. Quinze GB de
folga para um render de horas é um render que morre em 90%.
**Decisão:** projeção de disco só vale com pelo menos seis planos amostrados, e
o pior caso medido à parte. `scripts/medir_compressao.py` faz isso.
**Motivo:** é a mesma falha que o `RETOMAR.md` já registra duas vezes nesta
sessão — medir uma coisa e chamar de outra. Um quadro não é o filme.

### D013 · Os passes de difuso e glossy saíram do beauty
Medido no P11, quadro fechado, custo do slot beauty:

| arranjo | MB/quadro |
|---|---|
| 8 camadas | 19,8 |
| Combined + Diff + Gloss (5) | 18,2 |
| **só Combined** | **2,2** |

Os quatro passes de difuso/glossy custam **16,0 MB**; Emit, Env e AO custam
**1,6 MB somados**. O peso do beauty são eles, e o resto é troco.

**Decisão:** beauty = `Combined + Emit + Env + AO`. Resultado medido nos mesmos
seis planos: **38,9 MB/quadro, 176 GB no filme, 124 GB de folga** — e o quadro
ficou mais rápido, **10,0 s** contra 13,6 s, porque são menos passes a compor.

**Divergência consciente com a doutrina §7.4**, que pede "luz separada" entre os
AOVs que dão margem: o que ela protege — mexer sem re-renderizar — segue
protegido por Cryptomatte (isolar qualquer objeto), Depth (atmosfera, separação
de plano) e Normal (relight de superfície). O que se perde é rebalancear difuso
contra especular no filme inteiro, que ninguém pediu. O que se ganha é o render
caber no disco. **AO fica** porque a doutrina o nomeia e custa quase nada.

### D014 · `write_still=False` no render de verdade
O Blender gravava, além dos três slots, um `_descartar_.png` de 5 MB por quadro
que ninguém usa — **23 GB no filme**. Os File Output gravam durante a
composição, independente do `write_still`. Desligado.

### D015 · O footage de quinta NÃO é HDR — e isso era a suposição perigosa
`ffprobe` nos 17: **3840×2160, yuv420p10le, bt709** em transferência, primárias
e matriz. **SDR de ponta a ponta.**

Isto contraria o que o material antigo deste mesmo cliente ensinou: os `IMG_91xx`
da triagem de 14/08 são HLG bt2020 / Dolby Vision e exigiram tonemap, e a
memória do projeto guarda *"material do AgroShow é HDR"* como armadilha. **Aqui
não.** Aplicar a cadeia de HLG neste material destruiria a cor — e em silêncio,
porque a imagem sai, só sai errada.

O `extrair_linear.py` **lê o ffprobe de cada arquivo e monta a cadeia a partir
dele**, em vez de aplicar uma receita fixa; e recusa transferência que não
conhece em vez de inventar. Conferido: a mediana do quadro linear dá **0,0174**
contra **0,1588** se fosse sRGB — está linear de verdade.

**E o 4:2:0 tem consequência prática:** croma subamostrado, e os dois materiais
mais críticos do parque são o pior caso — parede/chapa **vermelha** saturada e
coluna **azul** saturada. Regra escrita no contrato: medir só em região grande e
chapada, longe de borda de cor.

### D016 · Regra de desempate footage × planta
A ordem dele — *"os locais que já estão lá não mudam"* — não diz o que fazer
quando o footage contradiz o footprint. Sem regra, a etapa 3 vira decisão ad hoc
quadro a quadro. Declarada em `data/footage-quinta.json`:

- **forma e proporção → footage vence.** A planta é bitmap reamostrado e não
  desenha forma; a câmera desenha.
- **posição e footprint → planta vence.** É a ordem dele, e a conferência de
  14/08 foi validada contra satélite.
- **altura → footage, por datum declarado em quadro.** Altura de *patamar*
  continua com o cliente (pendência 8) — patamar não aparece em quadro.
- **divergência acima de 5 m → não escolho.** Vira pendência com o quadro
  recortado. O limiar é maior que a incerteza de medir por imagem e menor que um
  erro que muda a leitura do plano.

### D017 · Os três achados dele, avaliados e declarados

| achado | o que é | veredito |
|---|---|---|
| **`85-grasss.zip`** | contém `grasss.c4d` — um arquivo **Cinema 4D** — e três JPEGs | **não entra.** O Blender não importa `.c4d`; é formato proprietário e fechado, e não há C4D nesta máquina. Não é falta de vontade: não há caminho. A grama da cena continua vindo do `aerial_grass_rock` CC0 com cor medida no footage dele, e agora ganha o reforço do footage de quinta |
| **`workbook_v1.xlsx`** | três abas — Checklist Geral, Bibliotecas de Assets, Parâmetros de Render. Checklist genérica de pipeline 3D | **referência, não doutrina.** O que ela pede e que já está feito: OptiX, AgX, unidades métricas, Cycles GPU. O que ela pede e **não se aplica**: RTX 3090/4090 (a máquina é 4060 e o projeto já está dimensionado para ela), Quixel Bridge e BlenderKit premium (a verba de asset é **zero** e só CC0 entra). Fica em `reference/` como registro |
| **`blosm`** (addon + repo) | importa OpenStreetMap e terreno para o Blender | **não entra no caminho crítico.** O entorno já vem de fonte melhor e medida: SRTM até 12 km conferido em ±5 m contra segunda fonte, e ESA WorldCover a 10 m para a cobertura. O que o blosm somaria é edificação urbana de Dois Vizinhos a 3–8 km — que aparece como silhueta de poucos pixels num filme cujo assunto é o recinto. E `RETOMAR.md` já fixa que **nenhum addon entra no caminho crítico do gerador**, porque addon derrubado deixa o render sair errado em silêncio. Fica como proposta, com o custo dito |

### D008 · Nota de API — Blender 5.2 não é 4.x
Custou duas rodadas e fica escrito: o compositor virou
`scene.compositing_node_group` (era `scene.node_tree`); o File Output trocou
`layer_slots`/`file_slots` por `file_output_items` + `directory`/`file_name`;
`format.media_type` **filtra** o enum de `file_format` e tem que ser atribuído
antes; e os sockets de passe viraram nome por extenso (`Diffuse Direct`, não
`DiffDir`). O passe `Shadow` não existe mais no Cycles daqui — foi removido do
contrato em vez de virar slot preto.

---

## 2026-08-15 — sexta sessão (etapa 2: medir os materiais do footage novo)

### D018 · A âncora de 14/08 não serve neste footage, e o erro é de ORIENTAÇÃO
**Ambiguidade:** o plano diz *"estender `medir_materiais.py` para os quadros
lineares"*, e o método de 14/08 é âncora de albedo conhecido no mesmo quadro.
Não diz o que fazer quando não há superfície branca de albedo conhecido no
quadro — e nos 17 vídeos de 13/08 não há.

**O que eu tentei primeiro, e como o número denunciou.** Declarei a telha
metálica clara em 0,70, mesma lógica da lona 0,75. O tijolo saiu com **albedo
1,000 no vermelho** — a parede refletiria mais vermelho do que o branco reflete.
Isso não existe.

**A causa é física e não é escolha de caixa.** O footage de 13/08 é de **dia
encoberto**, e em céu encoberto a irradiância depende da **orientação** da
superfície: a água de telhado vê o hemisfério de céu inteiro, a parede vertical
vê metade dele. Âncora no telhado mede uma luz que a parede não recebe, e todo
albedo de parede sai inflado — 85% inflado, medido. A doutrina de 14/08 já
avisava disso numa linha (*"superfície de âncora tem que estar iluminada como as
que se quer medir"*), e naquele quadro havia a sorte de a lona estar virada para
o sol junto com o resto.

**Decisão: o céu do próprio quadro vira o fotômetro.**

    E_horizontal = pi * L_ceu
    E_orientacao = E_horizontal * FATOR_VISTA[orientacao]
    albedo       = pi * L_superficie / E_orientacao

`FATOR_VISTA` está declarado valor por valor em `medir_materiais_quinta.py`:
horizontal 1,00 · vertical aberta 0,54 · vertical sob beiral 0,32 · telhado de
baixa inclinação 0,96 — cada um com a conta atrás.

**Motivo de ser a opção conservadora:** é um modelo derivável, escrito e
**conferível**, contra um número que eu escolheria porque a imagem "parecia
branca". E só foi possível porque o quadro `1 (17)__0006s` tem o céu **não
estourado** — 99,9% dos pixels em 0,957, só 0,06% no teto. Nos outros o céu está
saturado e o método não se aplica; está dito no JSON.

**E ele passou em dois controles independentes**, contra a medição de 14/08 que
saiu de outro quadro, outro dia, outra luz e outro método:

| controle | 14/08 | agora | razão de luminância |
|---|---|---|---|
| mata (perene) | 0,132 / 0,154 / 0,046 | 0,135 / 0,144 / 0,066 | **0,96×** |
| terra batida | 0,266 / 0,188 / 0,155 | 0,339 / 0,240 / 0,159 | 1,27× |

Duas medições que não se falam concordando é o que separa medida de conta.

### D019 · O tijolo estourou no vermelho, e a cadeia carrega só o nível
**Ambiguidade:** a coluna azul larga e o portão de chapa só aparecem grandes e
chapados no plano fechado `1 (17)__0037s` — que **não tem céu no quadro** e tem
8,7% dos pixels no teto.

**Decisão:** o quadro fechado entra por **âncora transferida** do quadro aberto,
usando a mesma alvenaria — mas **só nos canais G e B**. No plano fechado a
câmera expôs para o interior escuro do vão e **41% dos pixels do tijolo estão no
teto do vermelho**. Então a cadeia carrega só o **nível** (fator k = 4,665,
medido em G e B) e reusa a **cor** do iluminante do quadro aberto — mesmo dia,
mesmo céu encoberto, mesmo balanço de branco da câmera.

**Motivo:** ancorar num canal saturado transporta um valor que a câmera não viu.
Ancorar só nos limpos transporta o que ela viu. E a conferência fecha: o tijolo
medido pelos dois caminhos dá **0,564/0,073/0,071** e **0,551/0,083/0,061**.

**Trava nova em código, não em parágrafo:** `ESTOURO_MAXIMO = 0,5%` — amostra
com mais que isso de pixel no teto é **recusada com o número impresso**. Foi ela
que pegou as duas caixas erradas desta sessão; nenhuma delas dava erro na tela.

### D020 · Rotulei uma amostra de `grama` e ela era chão batido
**Ambiguidade:** nenhuma — foi erro meu, e fica escrito porque é o terceiro
desta série (o anel bege do entorno em 14/08, o centro da arena em 14/08).

Declarei uma caixa como `grama` e ela devolveu 0,339/0,240/0,159, que é bege. O
debug em quadro mostrou terra pisada entre as árvores. **Renomeada para
`chao_batido` em vez de forçada para outro lugar** — rótulo errado sobre medida
certa é pior que medida faltando —, e promovida a segundo controle, onde bate
com a classe `terra` de 14/08.

**O que se repete e vale como regra:** três vezes nesta série eu li a imagem e o
número desmentiu, e nas três o que pegou foi **desenhar a caixa no quadro e
olhar**. O `--debug` deixou de ser conveniência: nenhuma amostra entra em
contrato sem a folha de prova gerada.

### D021 · O que NÃO deu para medir, e por que fica sem número
**Ambiguidade:** o plano lista sete classes novas. Três delas só aparecem em
quadro sem fotômetro ou em peça fina, e a saída fácil seria arbitrar um albedo.

**Decisão: entregar o que está medido e nomear o que não está.**

| classe | estado | motivo |
|---|---|---|
| tijolo vermelho | **medido** 0,564/0,073/0,071 | céu não estourado no quadro |
| chapa azul (telhado) | **medido** 0,036/0,274/0,592 | idem |
| coluna azul | **medido** 0,018/0,060/0,165 | cadeia por canal limpo |
| portão de chapa | **medido** 0,066/0,077/0,098 | idem |
| terra batida (interna) | **medido** 0,097/0,033/0,016 | idem |
| brita / estrada | **medido** 0,261/0,189/0,162 | e confere com `terra` de 14/08 |
| concreto, grade, piso de curral | **só a cor** | não há céu medível nas mangueiras |
| estrutura de telhado vermelha | **sem medida** | só existe em terça e rufo, peças de 20–40 px. Croma 4:2:0 de peça fina é mistura inventada pelo decodificador, e a caixa que tentei ainda vinha com 1,25% no teto |

**E um achado que muda como se lê o quadro das mangueiras:** ali a luz não é
uniforme — o primeiro plano recebe céu pelos vãos abertos e o fundo coberto não.
A coluna que eu havia escolhido como referência lê **3× mais escura** que as
grades, e isso **não é albedo, é iluminação**. A referência passou para a grade,
que está no mesmo regime do piso, e o JSON carrega o campo
`_a_razao_NAO_e_reflectancia_entre_regimes` dizendo exatamente isso.

**Correção de decupagem, de quebra:** `footage-quinta.json` descrevia o piso das
mangueiras como *"piso de brita"*. O quadro mostra **terra com maravalha**. A cor
sai do quadro, não do rótulo.

### D022 · A ferradura da bacia, conferida contra foto de drone
**Ambiguidade:** a pendência 4 foi fechada em 14/08 por **inferência sobre o
desenho** — duas testemunhas indiretas (nenhum dos 15 `Talude` e nenhum dos 93
estandes da série C no setor de 240° a 360°). Inferência boa, mas indireta. O
vídeo `1 (2)` é nadir de drone e mostra a ferradura **direto**.

**O problema:** foto não sabe onde é o norte.

**Decisão: medir o ÂNGULO ENTRE duas direções dentro da própria imagem** — o
eixo da fileira de pavilhões (cujo rumo o desenho já dá, azimute 108°) e a boca
da bacia. Ângulo entre direções não depende de saber o norte; e o quadro é
nadir, então ângulo na imagem é ângulo no mundo.

| | |
|---|---|
| ângulo entre, medido na imagem | **56,8°** |
| eixo dos pavilhões, do desenho | azimute 108,0° |
| abertura da bacia | rumo de mapa **164,8°** ou 344,8° |
| o que `data/bacia.json` diz, derivado | rumo de mapa **150,0°** |
| desvio | **14,8°**, com tolerância de 20° |

**A ambiguidade de 180° é real e está declarada:** a reta dos pavilhões tem dois
sentidos e a foto não os separa. Quem desempata é a planta — que já havia dito
que não há talude nenhum entre 240° e 360°. **Duas fontes que não se falam
concordando é o resultado; não é uma fonte só com duas contas.**

**Correção, no mesmo turno em que o erro apareceu:** a primeira versão deste
registro dizia **0,2° de desvio** contra "os 165,0° que a planta já dizia".
**Os 165 eram meus, não do arquivo.** A convenção de `data/bacia.json` está
escrita nele e não é a da bússola — *"0 graus = +x (leste do mapa), 90 = +y
(norte do mapa), anti-horário"*. Derivando em vez de afirmar, o centro da boca
de lá dá **rumo de mapa 150°**, e o desvio verdadeiro é **14,8°**.

**O veredito não muda: CONFERE.** 14,8° é grande para uma linha e pequeno para
uma boca de 120° — as duas fontes apontam para o mesmo quadrante, que era o que
estava em questão. O que muda é a honestidade do número, e o erro é o mesmo dos
outros três desta semana: eu escrevi de cabeça uma coisa que o arquivo tinha
escrita, e não abri o arquivo.

**Trava que entrou por causa disso:** o script agora **lê `bacia.json` e faz a
conversão em código**, com a conta no docstring. Número de referência que mora
numa constante escrita à mão é número que ninguém confere.

### D023 · O que o footage prova de forma, e o que ele ainda não prova
**Ambiguidade:** o plano manda "corrigir a forma de todos os prédios que têm
footage". Fazer isso agora significaria trocar geometria a partir de leitura de
quadro sem o footprint casado — e `construir sobre footprint errado é pior que
não construir` já está escrito.

**Decisão: separar o que a câmera prova do que ela não prova, e entregar
`data/formas-quinta.json` como registro antes de mexer em geometria.**

O que ficou **provado** e não estava:

- o **prédio redondo é POLÍGONO REGULAR de ~10 faces**, não círculo, e tem dois
  pavimentos com o superior recuado, varanda em volta, guarda-corpo de 1,10 m e
  telhado de quatro águas de baixa inclinação sobre polígono. Contado nas
  quebras da saia do telhado inferior e do guarda-corpo em `1 (6)__0012s` e
  `1 (10)__0041s`. **Confiança média** — os segmentos aparecem desiguais no
  quadro, e isso é perspectiva de polígono regular, mas uma vista de topo
  fecharia a contagem;
- há um **anexo retangular** encostado nele, que é outro volume. Modelar junto
  deformaria o polígono;
- o **PALCO é branco sobre base azul**, e na cena ele herdou **madeira**.

O que **não** ficou provado, e por isso não virou geometria: qual zona da planta
é cada prédio (sem isso a forma medida não sabe onde pousar), a contagem exata
das faces, e as alturas por datum. Os datums estão listados no JSON — pessoas na
varanda (1,70 m), guarda-corpo (1,10 m, norma), carro (4,4 m).

### D024 · Correção: eu errei sobre o palco, e o erro descobriu uma contradição
**O que eu escrevi em D023 e está errado:** *"o PALCO é branco sobre base azul,
e na cena ele herdou MADEIRA"*. Duas coisas erradas numa frase só.

1. `estruturas.palco` não usa `MAT_MADEIRA` — usa `MAT_PRETO`. `MAT_MADEIRA` é
   do **Portal**. Eu li a linha errada do `grep` e não abri a função.
2. E, mais importante: **`1 (4)` não mostra o palco da cena.** Olhando os oito
   quadros, é uma **concha permanente de alvenaria** — base azul de ~1,2 m,
   paredes claras, cobertura inclinada escura — plantada num gramado ao lado de
   uma pista de terra. O que `estruturas.palco` constrói é outra coisa:
   deck de 16 × 11 m, quatro torres de treliça de 10,5 m, cobertura tensionada,
   telão de LED e caixas empilhadas. É o **palco de evento**, montado, e a
   procedência dele está citada na própria função:
   `DJI_20251127184447_0110_D` 00:00:02, de novembro.

**A contradição que apareceu no caminho, e ela não é minha:**
`data/estimativas.json` afirma, sobre a Praça de Alimentação Coberta, que *"não
usa `estruturas.palco` porque aquele é o **palco fixo** da arena"*. Mas
`estruturas.py` documenta o mesmo objeto como o palco **de evento**, de
novembro, e o código constrói treliça e telão. **Os dois não podem estar certos.**

**Decisão, conservadora:** não reescrevo geometria nenhuma por causa disso. O
que faço é:

- **corrigir o comentário** em `estimativas.json`, que é documentação e é
  reversível — `estruturas.palco` é o palco **de evento**;
- **registrar o palco fixo como estrutura que a cena NÃO tem.** Ele é um "local
  que já está lá", e a ordem dele diz que esses não mudam — mas não existir é
  diferente de mudar. Vira pendência com o quadro apontado;
- **não medir a cota dele agora.** O `ESTADO.md` já dizia que a pessoa em pé no
  `1 (4)` 00:00:02 dá 1,70 m *"no mesmo quadro que o palco fixo"* — só que ela
  está no primeiro plano e o palco a uns 40 m atrás. **Altura em pixel de coisa
  a outra profundidade não escala**, e é exatamente a armadilha que a série de
  erros desta semana tem em comum. Fica pendente por falta de datum na mesma
  profundidade, não por falta de vontade.

**O que se repete e vira regra:** eu afirmei sobre um arquivo a partir de uma
linha de `grep` e sobre uma estrutura a partir de uma folha de contato. Nas duas
vezes o conserto foi **abrir o arquivo e olhar o quadro inteiro**. É o mesmo que
a memória do projeto já guarda como *ver antes de afirmar*, e é a terceira vez
nesta semana.

### D025 · A sobreposição das vias não certifica as 42 — e mostra por quê
**Ambiguidade:** a pendência 9 diz que as 42 vias estão `conferido_pelo_natan:
false` e que o aéreo nadir "destrava" a conferência. Destrava, mas não do jeito
que eu esperava.

**Feito:** `scripts/sobrepor_aereo.py` projeta as vias sobre `1 (2)__0076s` por
uma semelhança (escala, rotação, translação), com cada parte tirada de coisa já
medida — centro da arena `(−74,7 / −3,2)` marcado por ele, rotação do eixo dos
pavilhões (rumo de mapa 108°), escala do raio dos patamares.

**A validação é honesta porque o validador não entra no ajuste:** centro, escala
e rotação saem da arena e dos pavilhões; quem confere são as **vias**, que não
foram usadas em nada disso.

**O que a folha mostra:**

- a **escala e o centro fecham bem** — os anéis de 45 e 62 m do modelo pousam em
  cima dos terraços que aparecem na foto. A primeira leitura do centro estava
  470 px fora, e foi a própria sobreposição que denunciou;
- **e boa parte das "vias" cai em cima dos terraços da arena.** V19, V24, V27,
  V32, V35, V43, V50 e vizinhas desenham arcos concêntricos dentro da bacia. Isso
  não é estrada: **é a curva de nível da arquibancada, lida como linha pelo
  Hough**. O `vias.json` já avisava que o traçado é leitura de bitmap; a foto
  mostra o que ele leu.

**Decisão: não marcar nenhuma como conferida.** O campo se chama
`conferido_pelo_natan` e o nome diz de quem é. O que fica escrito é uma
suspeita **com prova em quadro** — que um subconjunto das 42 é contorno de
patamar, não via — e ela é acionável: quem for usar `vias.json` para geometria
precisa separar isso antes.

**O que fecharia:** classificar por forma. Traçado que é arco concêntrico ao
centro da arena, dentro de r < 150 m, é candidato a patamar; o resto é candidato
a via. É conta sobre dado que já está no arquivo — não precisa dele.

---

## 2026-08-15 — as quatro respostas dele

Ele respondeu a folha de prova: *"a concha entra na cena, a paleta de cores está
ok. O prédio é polígono mesmo. Isso mesmo é curva de nível a estrada fica um
pouco acima. É concreto envelhecido, o albedo o daquela coluna"*.

### D026 · O concreto fecha uma classe e denuncia as outras duas
Com `MAT_CONCRETO = 0,25` (faixa de mercado 0,20–0,30, meio dela), a coluna sai
em albedo absoluto. **E as outras duas saem impossíveis:** a grade dá 0,773 /
0,841 / 1,000 e o piso 0,685 / 0,664 / 0,794. Tinta cinza clara de mercado não
passa de ~0,60.

**Isso não é erro do número, é o número provando o que eu já suspeitava:** o
excesso não é cor, é luz. A grade do primeiro plano recebe céu pelos vãos
abertos e a coluna do fundo coberto não. Então o valor delas entra no JSON com
`_ressalva` dizendo que é **teto, não medida** — e o teto ainda é útil, porque
limita por cima.

### D027 · As 19 curvas de nível, separadas por geometria
Ele confirmou: *"Isso mesmo é curva de nível, a estrada fica um pouco acima"*.
`scripts/classificar_vias.py` separa por dois testes duros, sem parâmetro de
gosto — desvio relativo do raio abaixo de 18% (menos que a distância entre dois
patamares vizinhos, que é 27–35% do raio) e raio médio dentro dos 150 m de
alcance da bacia. Piso de 25 m de comprimento, porque traço curto parece arco
por acidente.

**19 curva de nível · 14 estrada · 9 indeterminado.** Nenhuma marcada como
conferida — `conferido_pelo_natan` continua dele. E a palavra *"a estrada fica
um pouco acima"* ficou gravada no arquivo: quem for tirar geometria de via
precisa dessa oposição, porque o arco marca a cota e a estrada está um pouco
além dela.

### D028 · A concha entrou, e onde ela pousa resolve a contradição do palco
`estruturas.concha()`, quatro peças sob um pai: porão azul de 2,4 m com laje,
caixa cênica clara de 8,9 m de pé-direito, cobertura caindo de 11,0 para 9,6 m.

**Footprint da planta, alturas do footage** — a regra de desempate que já estava
escrita. A zona é `PALCO PALCO` (20,28 × 17,67 m): o rótulo aparece **duas
vezes** na prancha, a 5 m um do outro, e é a mesma palavra escrita duas vezes,
não dois palcos. As alturas saem de proporção medida em `1 (4)__0012s` contra a
largura conhecida, e carregam ~20% de incerteza — está declarado, não vendido
como cota.

**E isso fecha a contradição da D024:** a zona PALCO da planta é a concha
permanente. O palco de evento estava construído em cima dela. Ele **não foi
apagado** — `nada se apaga` —, foi para a **ÁREA DE ESPERA**, que é o mecanismo
que o próprio Natan pediu para peça que existe mas cuja posição é dele.

**Duas ressalvas, e as duas ele vê no quadro:**

1. **as três cores da concha são PROPOSTA, não medida.** O `1 (4)` é o único dos
   dezessete filmado em golden hour, e o método do céu (D018) só vale em dia
   encoberto. Trocar é uma linha em `MATERIAIS`;
2. **`rumo_confiavel: false`** no footprint dela — preenchimento 0,816 e partição
   por watershed. Entrou assim mesmo porque a alternativa era chutar, e fica
   dito: se a concha aparecer torta contra o aéreo, é daqui que vem.

### D029 · Armadilha 34 — marcador de câmera vence `scene.camera`
As duas provas da concha saíram **idênticas** na primeira tentativa, e sem erro
nenhum. Os 22 planos do filme estão presos a **marcadores de timeline**, e
marcador de câmera vence `scene.camera` na hora do render — então as duas
câmeras que eu criei foram ignoradas e o Blender renderizou o plano do
marcador, duas vezes.

`prova_concha.py` limpa os marcadores na sessão (o `.blend` em disco não muda).
Vale para qualquer prova futura nesta cena.

### D030 · Plano A **e** B, e o que isso muda na régua
Ordem dele em 15/08: *"Vou utilizar os dois planos o A e o B, depois de o
restante estiver concluído"*.

**A pendência 14b deixa de ser bifurcação e vira ordem.** Não é "escolher entre
render local e IA generativa" — é os dois, e os dois depois que o resto fechar.

**Consequência dura, e ela é a régua de agora em diante:** vale o teto do Plano
B. Proxy de gente e de gado **não** é entrega — no Plano A ele serve, mas o
Plano B pede modelo e animação de verdade. Então a pendência 14 continua aberta
com o padrão mais alto, e a estimativa de conclusão desce, não sobe: era ~66%
pelo Plano A e ~55% pelo Plano B, e agora vale **~55%**.

### D031 · A paleta medida entrou nos 52 prédios — e o efeito é menor do que eu disse
Ordem dele: *"Aplica o efeito mais barato"*, depois de eu dizer que era o passo
com mais efeito por menos trabalho.

**Feito:** `vestir_com_a_paleta()` em `build_scene.py`. Os 52 prédios com
`footprint_medido` deixaram de sair no cinza `MAT_PAVILHAO` (0,55 / 0,56 /
0,58), que ninguém mediu e que eu inventei numa sessão anterior — o *design
system default* que o `CLAUDE.md` proíbe, repetido em dezenas de objetos.

**Dois materiais por prédio, não um.** Caixa com material único pintaria o
telhado de tijolo. Quem decide é `normal.z`, não o nome do objeto — a mesma
correção do portal de 14/08. Parede `MAT_TIJOLO` (medido), telhado `MAT_TELHA`.
As zonas da coleção ESTIMADO continuam no cinza **de propósito**: elas são
estimativa e precisam ler como tal.

**E agora a parte que me desmente.** Eu disse que isto *"muda o quadro inteiro"*.
**Não muda.** As duas provas mostram por quê:

- **o filme é quase todo aéreo, e do alto se vê TELHADO.** O tijolo medido só
  aparece nas laterais, e as laterais quase não entram em quadro;
- **o anel de mata tapa o rasante.** No quadro a 32 m de altura o recinto quase
  não aparece atrás das copas.

**O que isso ensina, e vale mais que a paleta:** num filme aéreo o material que
manda é a **cobertura** — e `MAT_TELHA` é justamente o que **não está medido**.
A medição de 14/08 estourou nele (albedo 1,00 / 1,00 / 0,95, no teto) porque
telha metálica reflete o céu de forma especular: o que a câmera vê não é a cor
dela, é o céu. Ficou um cinza galvanizado com metallic 0,55, que é decisão
técnica, não medida.

**Próximo passo que isto abre, e é barato:** o footage de 13/08 tem telhado em
quadro fechado e em dia encoberto — que é a luz em que o método do céu funciona,
e sem sol direto o reflexo especular é muito menor. Dá para medir a telha de
verdade pela primeira vez.

### D032 · A skill `blender-assembly` foi instalada, contra a minha recomendação
Ele mandou o repositório e disse *"instala se fizer sentido"*. Eu li os três
arquivos, conferi regra por regra contra o código e **recomendei não instalar**.
Ele respondeu *"instala a skill"*. **Decisão dele, e está feita** — o
`CLAUDE.md` diz que discordar faz parte, uma vez, e que se ele bater o pé
registra e segue.

**O que foi instalado:** `SKILL.md`, `README.md` e a imagem, verbatim, do commit
`afad3b18`. Markdown puro — **nenhum código executável, nenhum addon, nenhum
servidor MCP**. Instalar não tinha risco técnico; a objeção era de adequação.

**Onde:** `render-expovizinhos/.claude/skills/blender-assembly/`, e **não** no
`.claude/skills/` do cofre, onde moram as 91 outras. Ela é de Blender, e os
outros nove sistemas da casa não têm nada com isso — `CLAUDE.md`: *"nove
sistemas convivem aqui e não devem se misturar"*. Se ele quiser no cofre
inteiro, é mover uma pasta.

**Não editei uma linha do `SKILL.md`.** Skill de terceiro se instala como está
ou não se instala. O que esta casa pensa dela ficou em `PROCEDENCIA.md`, ao
lado, com a procedência, o que serve, o que não serve e por quê.

**As duas regras que quebram a cena estão marcadas como veto naquele arquivo:**
`finalize()` chama `shade_smooth()` em tudo (arredonda quina de caixa de
arquitetura; o conserto certo da etapa 5 é **bevel**), e `audit_all()` exige
`rotation = (0,0,0)` (a cena inteira depende de rotação em Z, e esse audit
reprovaria todo prédio que está certo). A precedência do `CLAUDE.md` já resolve
isso sozinha — **skill é o último elo** —, mas fica escrito para não depender de
alguém lembrar.

**E há um erro dentro dela que é o nosso erro de 14/08:** o `verify_bounds()`
lê `matrix_world` sem `view_layer.update()` antes. É a **armadilha 18** deste
projeto, a que afastou 33 objetos em 20 m cada sem erro na tela. Está avisado no
`PROCEDENCIA.md`, porque a skill não avisa.

**O que dela vale, e eu vou usar:** o mapa de conexões. Este projeto testa
colisão e não testa contato — o que *tem* que se encostar. Não fez falta
enquanto tudo era caixa solta; passa a fazer agora que há laje sobre porão,
cobertura sobre parede e grade em série.

### D033 · A telha não se mede neste material — e eu tinha dito o contrário
**Eu propus isto como o passo mais barato e mais valioso:** `MAT_TELHA` é o
material que mais aparece num filme aéreo e é o único grande da cena sem
medição. E eu escrevi que a medição de 14/08 estourou por **reflexo especular
do sol**, e que num quadro de dia encoberto daria para medir.

**Falhou, e a explicação que eu tinha dado estava errada.**

Tentei no nadir `1 (2)__0076s` — que é a melhor condição que este acervo
oferece: telhado horizontal, fator de vista 1,00, dia encoberto, a água inteira
em quadro. As três caixas que tentei voltaram com **2,2%**, **0,9%** e **4,8%**
de pixel no teto.

**E aqui eu quase cometi a armadilha 16.** Estava mexendo na caixa e tentando de
novo — que é exatamente *"parâmetro que muda a resposta não é medida"*. Parei e
medi o problema: `scripts/varrer_estouro.py`.

Num nadir de parque os **3% de pixel mais claros do quadro SÃO o telhado** — não
há outra superfície grande e clara ali. Que fração deles está saturada:

| | |
|---|---|
| mediana entre **30 quadros** de `1 (2)` e `1 (3)` | **29,8%** |
| pior caso | 40,4% |
| melhor quadro (`1 (2)__0009s`, oblíquo e distante) | 0,1% |

**O estouro não é do sol, é de exposição.** O drone expôs para o chão, e a chapa
metálica — a coisa mais clara do parque — saturou em dia encoberto, sem disco
solar em lugar nenhum. Enquanto o material for este, `MAT_TELHA` não se mede.

**O que fica:** o quadro nadir saiu do contrato de medição e no lugar dele ficou
o comentário com o número, para a próxima sessão não repetir a tentativa.
`data/estouro-telhado.json` guarda a varredura dos 30 quadros.

**O que fecharia, e é barato quando alguém estiver lá:** um quadro **exposto
para o telhado**, nem que o chão vá a preto. Meia parada de diafragma. Material
de medição não precisa ser bonito — e essa é a única coisa que falta para a
paleta do parque ficar inteira.

**A ressalva que sobrevive de tudo isso:** `MAT_TELHA` continua sendo o cinza
galvanizado com metallic 0,55, que é decisão técnica declarada, não medida. E
ele é o material que mais aparece no filme.

### D034 · "Primeiro os quadros" — o que eu entendi, e por que a leitura conservadora
Ordem dele, 15/08: *"Levante as melhores imagens para criar com IA, para usar
essas imagens reais e colocar tipo uma exposição nesse lugar, primeiro os
quadros e depois crio os vídeos."*

**Duas ambiguidades, e as duas resolvidas pelo lado mais barato de desfazer.**

**1. "Essas imagens reais" — footage ou render?** Podia ser qualquer um dos dois.
Resolvi por **os dois, com papel declarado**, e não escolhendo um:

- **`real`** = quadro do footage do próprio recinto, resolução nativa. É o que a
  frase dele descreve literalmente — *pôr uma exposição **nesse lugar***
  pressupõe um lugar que já existe na imagem. Um render de caixa branca não é
  "imagem real" em nenhuma leitura.
- **`3d`** = quadro da cena, na moldura exata do plano. Entra como **guia de
  composição**, não como concorrente: é ele que diz de onde a câmera olha, a que
  altura, com que lente e o que cabe no quadro.

Entregar os dois custa uma sessão e não fecha porta nenhuma. Entregar só um
obrigaria a refazer se eu tivesse lido errado.

**2. Ele está antecipando o Plano A, ou só pedindo material?** O D030 diz que os
dois planos entram *"depois de o restante estar concluído"*, e o restante está em
~55%. **Não arbitrei.** O que fiz não antecipa o Plano A nem atrapalha o B:
nenhuma imagem foi gerada por IA, nenhum quadro do filme foi renderizado, a
decupagem não mudou e `planos.json` está intacto. O que existe é o **material de
entrada, catalogado e pronto para ele aprovar** — que é o que "primeiro os
quadros" pede em qualquer uma das duas leituras.

**O que NÃO foi feito, de propósito:** o render master (4.635 quadros, 12,9 h,
176 GB). Ele pediu quadros, não o filme, e o filme é o passo 4 dele — *"quem
exporta é ele, no Blender dele"*.

**Custo real:** 52 quadros de cena a 2760×1380 (~9,4 s cada, 8 min de GPU) e 44
quadros de footage em resolução nativa. Contra 12,9 h do filme.

**Onde está:** `data/quadros-ia.json` (o catálogo, versionado),
`out/quadros-ia/` (as imagens) e `out/quadros-ia/INDICE.html` (a página que ele
abre para aprovar).

### D035 · O portão de câmera, e os 6 planos que sairiam quebrados
**Este é o achado que paga a sessão inteira.** Ao medir os 44 quadros-chave por
pixel, seis planos dos 22 vieram inutilizáveis:

| plano | o que aconteceu |
|---|---|
| P12 fim, P19 fim | **quadro preto** — câmera dentro de geometria |
| P08 fim, P09 ini | **chapado** — desvio 3,4 e 3,2 num quadro de 2760×1380 |
| P09 (inteiro), P12 (meio) | a câmera corre **dentro da copa do bosque** |
| P10 ini/fim, P20 ini/fim | prédio ocupando a tela inteira a poucos metros |

**O conferidor que já existia não pega isso.** `planos.py --conferir` mede
**velocidade**, e os seis estão todos dentro da faixa cinematográfica. São duas
checagens diferentes e faltava a segunda.

Virou código, não parágrafo (delta `0029`): **`scripts/conferir_camera.py`**, com
três testes — câmera abaixo do solo (raycast para baixo), câmera dentro de sólido
fechado (paridade de cruzamentos em 4 direções) e superfície a menos de `--folga`
metros na mira. Ele sai com código 1 e **é para rodar antes de qualquer fila de
render**.

**A causa provável, e ela não é da câmera.** Os 22 planos foram decupados quando
a cena era caixa solta; as **418 árvores** entraram depois. Ninguém reconferiu.
P09 e P12 correm dentro do bosque do começo ao fim.

**E há uma parte que a medição não pega, registrada como tal.** P10 e P20 passam
no desvio — parede de tijolo e água de telhado são duas cores fortes. Quem
reprovou foi o olho, e a reprovação está escrita em
`_quadros_3d_reprovados` no catálogo, item a item, com o motivo. Medição e olho
não se substituem, e o arquivo diz qual foi qual.

**O que NÃO fiz:** mexer em `data/planos.json`. Consertar seis câmeras é
re-decupagem, cascateia no `alvo_fim` e na velocidade (o `PLANOS.md` já avisa) e
é enquadramento — decisão de quem dirige. No lugar disso rendeirizei o **quadro
do meio** dos planos afetados, que salvou P06, P08, P14, P15, P19 e P20 com a
decupagem intacta. P09 e P12 continuam sem placa 3D possível: os dois estão
dentro da vegetação no plano inteiro.

### D036 · Nenhuma imagem foi gerada por IA nesta sessão
Registrado porque a ordem dele contém a palavra IA e alguém vai ler este
repositório procurando o que foi gerado. **Nada foi.**

A frase é *"primeiro os quadros e depois **crio** os vídeos"* — primeira pessoa.
A geração é passo dele, e um passo que gasta crédito dele. O que este agente faz
é entregar a entrada catalogada e pronta.

Vale também o que a doutrina do projeto já dizia e continua valendo: **a IA não
conhece a planta, não mantém continuidade entre planos e não escreve português
confiável.** Placa, totem e logo são compostos com máscara de Cryptomatte, nunca
gerados — e é o texto que vende espaço físico.

### D037 · Três dos quatro diferenciais não têm uma única imagem confirmada
Levantado ao montar o catálogo, e é o dado mais duro que saiu dele.

| diferencial | imagem confirmada por placa |
|---|---|
| Arena de Rodeio | a bacia existe, mas a placa que aparece diz **ARENA DE EVENTOS** |
| **Fazendinha** | **nenhuma** |
| **Café Colonial** | **nenhuma** |
| **Mercado do Produtor** | **nenhuma** |

Existem candidatos — casinhas de madeira no `DJI_0962_stabilized`, área infantil
em uso no `0140_D`, fogo de chão com costelas no `DJI_0964_stabilized_1`,
pavilhão vazio de pilar azul no `1 (16)` — e **os quatro estão marcados
`nao_confirmado` no catálogo**, com o bloqueio escrito por local.

**Não arbitro nomenclatura nem posição de área: é material de venda de espaço
físico.** O pedido que isso gera é barato e está na lista: uma foto de cada, do
ano passado, com placa em quadro.

Isso pesa mais do que parece porque o cliente pediu **mais tempo de tela** para
esses quatro, e o roteiro dá 9 a 16 s a cada um. São os planos mais longos do
filme apoiados no material mais fraco do acervo.

### D034 · O mapa 3D comprado: onde ele ajuda e onde não
Ele comprou em 15/08 um mapa do `maps3d.io` de 1,97 × 1,42 km centrado no
parque e perguntou se ajuda. **Ajuda numa coisa só, e não é a que parece.**

**O que ele NÃO é:** fotogrametria. É construção procedural, e o
`metadata.json` diz cada fonte. Conferido no OBJ, não deduzido:

| parte | o que veio | contra o que o projeto já tem |
|---|---|---|
| relevo | canvas 52×37 sobre 1973 m → **37,9 m por amostra** | SRTM de **30 m até 12 km**, conferido ±5 m contra segunda fonte. **Pior e cobre 6× menos** |
| prédios | **1.351 caixas** de OSM, **uma cor chapada** (0,945/0,925/0,882), altura inventada entre 6 e 10 m (`heightRandomnessPercent: 0`, `detailed: false`) | footprint **medido** da planta + forma medida no footage. **Substituir seria trocar medida por chute** |
| vias | 185 segmentos de OSM | 42 lidas do bitmap, já classificadas em 19 curva de nível / 14 estrada |
| chão | imagem Satlas, **2,39 m/px reais** (826×594 px) | ESA WorldCover a 10 m + cor medida no footage |

**A tentativa de usar as vias de OSM para fechar a pendência 9 foi
inconclusiva**, e o motivo não é o mapa: **OSM mapeia rua pública, e as 42 vias
do projeto são a circulação INTERNA do recinto.** Os dois conjuntos quase não
descrevem as mesmas coisas, então não podem se confirmar. A folha está em
`out/mapa-comprado/vias-osm-x-planta.png`, e ela carrega uma suposição declarada
que também não se pôde validar: o mundo da cena tem origem no **centro da
prancha**, que é ponto de desenho e não geográfico — não há lat/lon guardado
para ele.

**Onde ele ajuda de verdade, e isso vale:** é uma **imagem de satélite
LICENCIADA para uso comercial**, a 2,39 m/px, com a ferradura da arena visível.
A conferência de posição de 14/08 usou o **satélite do Google** como segunda
fonte (`data/luz.json`: *"169,0 no satélite do Google"*) — e isso é entrega de
cliente. Trocar a referência por esta remove uma dependência de imagem sem
licença. **É mais grossa** (o espaçamento entre pavilhões, que foi a medida que
validou a escala, dá 9,6 px aqui contra muito mais no Google), então serve como
**segunda fonte, não como substituta da medição**.

**Atribuição obrigatória, e entrou em `assets/MANIFESTO.md`:** Satlas / Allen
Institute for AI, e © OpenStreetMap contributors. Mesma regra do ESA WorldCover.

**O que eu NÃO fiz, de propósito:** não importei nada para a cena. Trazer os
1.351 prédios de OSM colidiria com a geometria medida do recinto, e trazer o
relevo de 38 m rebaixaria o SRTM de 30 m que já está conferido. **Se ele quiser
a silhueta urbana no horizonte, isso é decisão dele** — e vale lembrar que a
D017 recusou o `blosm` por este mesmo motivo, e o mapa comprado tem o mesmo
problema com um agravante: cobre só ~1 km de raio, e a silhueta que apareceria
nos planos está a 3–8 km, fora dele.
