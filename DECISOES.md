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

### D035 · As curvas de nível do mapa comprado — ele perguntou, e eu tinha passado batido
Ele leu o veredito da D034 e perguntou: *"nem as curvas de níveis?"*. **Pergunta
certa, e eu tinha ignorado o material `contour` no OBJ.** As cotas dos patamares
são a **pendência 8**, aberta com o cliente desde o começo — se as curvas
resolvessem, fechariam a mais antiga do projeto.

**Medido, não argumentado.** As curvas existem: **1.400 vértices em 9 alturas**,
intervalo constante de **11,10 m**:

> 550,5 · 561,6 · 572,7 · 583,8 · 594,9 · 606,0 · 617,1 · 628,2 · 639,3 m

**E é isso que mata a ideia:**

| | |
|---|---|
| patamares da arena | 0 → 3,5 → 7 → 10 m |
| profundidade da bacia **inteira** | **10 m** |
| intervalo entre curvas | **11,10 m** |

**A bacia inteira cabe dentro de 0,90 de um intervalo de curva.** Nenhum
patamar produz uma curva — nem o mais fundo. E o sítio, a 602 m, cai no vão
entre a curva de 594,9 e a de 606,0.

O horizontal confirma pelo outro lado: a malha do chão tem **38 m por quad**, e
os taludes têm de 17 a 30 m de largura radial. É a mesma limitação que o
`ESTADO.md` já registrava para o SRTM de 30 m — *"os taludes somem"* —, só que
pior.

**A pendência 8 continua com o cliente**, e continua precisando do que sempre
precisou: um quadro de drone **lateral**, ou a cota dita por quem construiu.

**O que as curvas dão, e é pouco mas é honesto:** uma **terceira fonte** de
altitude para o sítio. O mapa comprado põe o chão em **608,6 m** ali; o projeto
usa **602,0 m**, do SRTM conferido contra o opentopodata. A diferença de **6,6 m**
está dentro da incerteza da fonte mais grossa — que é esta, com 38 m de
amostragem. **Não muda nada**: o 602,0 continua valendo, porque veio da fonte
mais fina e já tem segunda testemunha.

---

### D038 · O rumo dos footprints estava espelhado em 90 graus — corrigido na raiz

**Como apareceu:** o Natan, olhando a cena aberta no Blender, disse que *"as
posições não estão corretas, tem coisa torta"*. A sobreposição contra o mapa
oficial (`scripts/sobrepor_planta.py` + `topo_planta.py`, novos) mostrou os seis
pavilhões de animais **cruzando em X** os retângulos desenhados na planta.

**Ambiguidade:** a cena obedecia `data/footprints.json` exatamente — rumo 108,4,
`rumo_confiavel: true`, confiança alta, e o `RETOMAR.md` marcava esse valor como
conferido. Ou o desenho estava errado, ou a medida.

**Decisão:** a medida estava errada. `medir_pontos()` em
`scripts/extrair_footprints.py` convertia o ângulo do `cv2.minAreaRect` por uma
fórmula que pressupunha a convenção antiga do OpenCV (ângulo em `[-90,0)`). O
**cv2 5.0 devolve `[0,90)`**, e o resultado saía espelhado em 90°.

**A prova, com retângulo sintético de rumo conhecido:**

| azimute real | o que gravava | o que grava agora |
|---|---|---|
| 70,0 | 110,0 | 70,0 |
| 108,0 | 72,0 | 108,0 |
| 20,0 | 160,0 | 20,0 |
| 90,0 | 90,0 | 90,0 |
| 0,0 | 0,0 | 0,0 |

**Por que sobreviveu tantas sessões:** 0° e 90° são os dois pontos fixos do
espelho. Todo prédio ortogonal passava certo, e só os oblíquos erravam — os seis
pavilhões de animais, que correm a 71,6°.

**Três fontes independentes concordam com o valor novo**, e nenhuma com o antigo:

| fonte | método | rumo |
|---|---|---|
| Hough no bitmap | retas longas do raster a 6x, sem tocar no extrator | 71,5 |
| perpendicular da fileira | regressão pelos 6 centros: fileira a 160,3 | 70,3 |
| `minAreaRect` pelos cantos | a correção | 71,6 |
| ~~fórmula antiga~~ | ~~convenção do cv2 4~~ | ~~108,4~~ |

**O conserto:** o rumo passou a sair dos **cantos** do `boxPoints`, não do ângulo.
Não depende de convenção nenhuma e sobrevive à próxima troca de versão — que já
mordeu este projeto uma vez (armadilha 10, mudança de `shape` do `HoughLinesP`
entre cv2 4 e 5).

**Prova visual:** `out/conferencia/_zoom-pavilhoes.png`. Antes as caixas cruzavam
os retângulos; agora coincidem, com o rótulo `PAVILHÃO - GADO LEITE 720,00 m²`
dentro da própria caixa.

**Alcance:** atinge **todo rumo medido**, não só os pavilhões. Dimensões não
mudaram (largura e profundidade não dependem do sinal). `footprints.json`
regerado; o anterior ficou em `data/footprints-v2-rumo-espelhado-1508.json` —
`nada se apaga`.

**O que o mapa comprado NÃO resolveu:** tentei usá-lo como quarta fonte e
**recusei o resultado**. Os 463 prédios a menos de 400 m do recinto são casas do
Jardim Marcante vindas do OSM, não os pavilhões; as alturas são inventadas pelo
próprio Maps3D (`minHeight: 6, maxHeight: 10, detailed: false`); e não consegui
identificar com segurança quais polígonos seriam os galpões. O rumo mediano que
saiu dali (102°) não é medida de pavilhão — é média de casa de bairro.

### D039 · A empena da concha passou a acompanhar o telhado

**Ambiguidade:** o teste de contato novo acusou a cobertura interpenetrando a
caixa cênica em 1,451 m. Duas leituras possíveis: telhado baixo demais, ou
parede alta demais.

**Decisão:** nenhuma das duas — a **parede tinha altura constante sob um telhado
inclinado**. Terminava em 11,65 m em toda a profundidade, enquanto a cobertura
cai de 11,65 (fundo) para 10,25 (frente). A ala atravessava o telhado.

**Motivo:** empena inclinada é o que uma concha acústica real tem, e mantém as
duas medidas do `1 (4)` intactas — o pé-direito de 8,9 m (que foi medido **no
fundo**) e a caída de 1,4 m. A face inferior da cobertura agora coincide com o
topo da parede em todo `y`, por construção, não por ajuste.

### D040 · O teste de contato virou portão, e mede por grade de raios

**Ambiguidade:** como provar que o que se apoia encosta, sem olhar quadro a
quadro.

**Decisão:** `CONTATOS_EXIGIDOS` em `build_scene.py`, com `sys.exit(1)`.
Três tentativas anteriores erraram, e o motivo de cada uma ficou escrito no
código:

1. **bounding box** — a bbox de um telhado inclinado tem a base na frente,
   1,4 m abaixo do fundo. Acusou −1,451 m numa concha já corrigida.
2. **vértices da peça de cima** — são 8 cantos, e a peça de cima quase sempre é
   maior (deck, beiral). Caem fora da outra: "SEM APOIO" em contato que existe.
3. **raio partindo da própria superfície** — com o épsilon o ponto entra dentro
   do sólido e o raio sai pela face de baixo. Mediu 0,350 m, que é a espessura
   do deck, não um vão.

O que ficou: grade de 14×14 raios verticais sobre a área em que as duas peças se
sobrepõem em planta. A pergunta é sempre a mesma — *nesta vertical, onde termina
a de baixo e onde começa a de cima?* — e não depende de onde estão os vértices.

### D041 · `topo_planta.py` limpa os marcadores de timeline

**Ambiguidade:** a primeira vista de topo saiu em perspectiva, de lado, **sem
erro nenhum na tela**.

**Decisão:** o script apaga `timeline_markers` na própria sessão antes de
renderizar. É a **armadilha 34** do `RETOMAR.md` — marcador vence `scene.camera`
—, e ela me pegou mesmo estando escrita. A cena em disco não muda.

**Motivo de registrar:** eu cheguei a ler uma sobreposição errada como se fosse
medida boa. Prova que sai de câmera não conferida não é prova.

### D042 · O ajustador virou ferramenta de layout, nao so de correcao

**Pedido dele, em tres tempos:** ajustar posicao e angulo -> *"quero poder
alterar o tamanho tbm"* -> *"quero adicionar blocos ali (de tendas e quadrada ou
circulares ou poligonos irregulares), e uma aba pra eu falar o que penso sobre o
bloco que crie por ex: area do estacionamento"*.

**O que existe:** `scripts/ajustar_posicoes.py` gera `out/ajustar/ajustar.html`,
auto-contido (planta em base64, abre com dois cliques). Move, gira,
redimensiona, **cria** blocos de quatro formas e **anota** cada um. O JSON vai
para `data/ajustes-manuais.json` e o gerador obedece **acima de qualquer
medicao** -- se ele mexeu olhando a planta, e porque a medida errou.

**A anotacao nao e decoracao.** `nota_do_natan` fica gravada como propriedade do
objeto no `.blend` e sai impressa no build. E por ela que a proxima sessao sabe
o que modelar de verdade no lugar do bloco bruto.

**Quatro defeitos que so apareceram porque testei em vez de entregar:**

1. o portal carregava a posicao antiga -- o arquivo guarda `novo_m`, e eu lia
   `x_m`;
2. JSON baixado do navegador vem com **BOM**, e `json.loads` morria no primeiro
   caractere, matando o build no meio sem dizer a causa. Agora le `utf-8-sig`;
3. o ajuste movia o **homonimo errado**: "PORTAL" existe como zona estimada,
   como letreiro e como estrutura. Movia 226 m em vez de 4,8. O JSON passou a
   carregar `objeto_na_cena`;
4. a **tenda saia caixa**. Eu deslocava os vertices de cima por `1 - |y|/ly`, e
   cubo so tem canto -- em todo canto `|y| = ly`, o fator dava zero. Pegou
   porque o teste mediu **volume** (400 m3 = 10x10x4 exato), nao porque alguem
   olhou o quadro. Agora a tenda tem cumeeira: 10 vertices, 9 faces, 320 m3 =
   240 da caixa + 80 do prisma do telhado.

**O risco que fica escrito:** este arquivo passa por cima da medicao por
desenho. E o que ele quer -- mas quer dizer que um ajuste errado nao tem quem o
pegue, porque nenhum portao confere posicao contra a planta. Quem confere e a
sobreposicao (`sobrepor_planta.py` + `topo_planta.py`), e ela e manual.

### D043 · O layout do recinto passou a ser dele, nao da planta

**O que ele fez:** abriu o ajustador e passou o recinto inteiro a limpo --
**12 pecas corrigidas e 85 blocos novos** (51 tendas, 16 areas, 12 retangulos,
6 circulos), quase todos com anotacao dizendo o que sao. Isso e informacao que a
planta do cliente nao tinha: ela mostra rotulo sobre chao onde o lugar tem
tenda, area de exposicao e estacionamento de verdade.

**O problema que isso criou:** 78 dos 85 blocos caiam a menos de 30 m de algo
que o gerador ja constroi. Construir tudo dava dois recintos de leiloes, dois
auditorios, duas mangueiras, tres estradas de asfalto.

**As nove decisoes dele, em 15/08:**

| # | pergunta | resposta dele |
|---|---|---|
| 1 | bloco dele x peca existente | **"pode substituir"** |
| 2 | os colados sao a mesma coisa? | pediu para ver -- imagem em `out/conferencia/casamento-blocos.png`, e depois: **"estao certos"** |
| 3 | areas com 3,2 m de altura | **superficie**, e a arena de rodeio tambem |
| 4 | estrada em triplicata | a nova vence, e **estrada dentro de area e de chao** |
| 5 | portal girado 92 graus | **"o portal agora esta na posicao correta"** |
| 6 | 5 blocos sem nota | ditou as cinco |
| 7 | conteudo (gado, gente, trator) | **ele vai providenciar os modelos** |
| 8 | referencias citadas | `F:\Extração quadros expo 2025` e `Brutos Expo\agroshow extrator somente` |
| 9 | "recado ao redor" | **cercado** |

**Como o casamento e feito** (`scripts/casar_blocos.py`): distancia sozinha nao
serve -- aprovaria uma tenda a 28 m como "substituta" do PAVILHAO 1. O criterio
e distancia pequena JUNTO com o texto da nota dele batendo com o rotulo da
planta. Saida em `data/casamento-blocos.json`, em cinco classes: SUBSTITUI (11),
SUBSTITUI? (12), ABSORVE ZONA (25), CONVIVE (34), NOVO (2).

**Dois erros meus, corrigidos antes de mostrar a ele:**

1. *"Saguao Aberto, para praca de alimentacao"* casava com `Praca de
   Alimentacao` a 11 m em vez do `SAGUAO ABERTO` colado a 3 m -- porque a nota
   citava a praca. Conserto: peca colada (<= 6 m) manda, e o texto so' desempata.
2. seis blocos casavam com **Talude** e **Poste**. Talude e RELEVO
   (`terreno.PATAMARES`) e poste e poste. Aplicar aquilo teria mandado relevo
   medido para o descarte para por uma tenda no lugar. Conserto: lista
   `NAO_CASAM`.

**A ARENA DE RODEIO ficou fora da substituicao, de proposito.** Na cena ela nao
e edificacao -- e a bacia do terreno com os patamares. A `Area 14` dele entrou
por cima como superficie, que e o que ele pediu, e o relevo continua embaixo.

**Superficie e chapa de 5 cm, nao volume.** O ajustador dava 3,2 m a todo bloco
e eu nao avisei; com isso o estacionamento de **15.042 m2** viraria um caixao
tapando a entrada do parque. As 12 areas marcadas saem com material da cena
(`MAT_SAIBRO`, `MAT_ASFALTO`, `MAT_ARENA`, `MAT_TERRENO`) -- nenhum material
novo nasceu para isso.

**Conferido, e nao no olho:** os 16 poligonos batem **exatamente** com a area
que ele desenhou (15.042 m2 no estacionamento, 2.812 m2 na estrada) -- nenhum
contorno concavo foi preenchido errado pelo bmesh. Os tres contatos da concha
continuam encostando.

**O que fica aberto:** o conteudo de dentro (gado, gente, trator, foodtruck,
maquinas) espera os modelos que ele vai providenciar. Ate la as areas saem
vazias **com a nota dele gravada no objeto**, que e por onde a proxima sessao
sabe o que por ali.

---

### D044 · A entrega vira 16:9 nativo, e a régua de tipografia se refaz

**Ordem dele, 15/08/2026:** *"sobre o painel de led eu vou exportar em 16:9 não
se preocupa."* Perguntado se isso queria dizer render nativo ou master 2:1
reencaixado, respondeu: **render nativo em 16:9**.

Isso derruba o "não negociar" que o `ESTADO.md` carregava desde a primeira
sessão: proporção 2:1 e master 2760×1380. Ele foi avisado, antes de decidir, de
que **16:9 (1,778) é mais estreito que 2:1 (2,000)** — a troca custa 11% de
largura e piora o corte lateral em vez de resolver. Decidiu assim mesmo, e a
decisão é dele.

**O que muda em cadeia, e não é só o número da resolução:** a conta da régua de
8%/4% usa o sensor vertical do Blender. Em 2:1 o vertical é 18,0 mm; em 16:9 é
**20,25 mm**. Todo letreiro dimensionado pela régua antiga fica **12,5% pequeno
demais** para a regra. Quem só trocar `resolution_y` entrega letreiro fora de
norma sem nenhum aviso na tela.

### D045 · O letreiro deixa de flutuar: a letra vai na superfície, e o modo desce do lugar

**Ordem dele, 15/08/2026:** *"inclui a letra embutida no painel usa as imagens
extraídas que todas as resposta ou quase todas estarão lá."*

As imagens foram lidas — 17 clipes do parque vazio e 152 pastas de quadros do
evento montado. Levantamento e prova em quadro:
`docs/COMO-O-PARQUE-ESCREVE.md` e
`out/referencia-letreiros/como-o-parque-escreve.jpg`.

**O que elas dizem:** o parque tem seis modos de escrever e em nenhum deles a
letra flutua. Ela mora numa superfície — placa pendurada por correntes no
portal, letra caixa aplicada no painel ACM da marquise, faixa de lona no
guarda-corpo curvo, chapa parafusada na parede do pavilhão, banner esticado no
vão de entrada, faixa na saia da tenda.

**Perguntado como aplicar nos 16, ele escolheu: pelo lugar, como o parque faz.**
Não é um padrão único — cada letreiro herda o modo do lugar que nomeia.

**Por que isso conserta os 9 letreiros fora do quadro, por construção:** o modo
`billboard` dimensiona por altura e não tem largura, então a frase de P02 dava
138% do quadro. Painel tem largura declarada: a linha quebra dentro dele, e o
que a câmera precisa enquadrar passa a ser um objeto de tamanho conhecido, que o
portão mede antes do render.

**Aviso registrado junto:** nem tudo em `F:\Extração quadros expo 2025` é Dois
Vizinhos. As pastas `DJI_20251126*` a `DJI_20251130*` são outro recinto —
autódromo oval, silos de grão, pavilhão de coberturas verdes. Referenciar
aquilo seria errar de cidade.

---

## 2026-08-15 · décima sessão — o levantamento do acervo inteiro

Ordem dele, literal:

> *"faça novamente o levantamento eu atualizei os arquivos de uma forma que eu
> possa avaliar e comentar e saber depois onde esta as que eu selecionei"*

### D046 · O que "de uma forma que eu possa avaliar" pediu, e o que eu li nele

**Ambiguidade:** ele descreveu o que quer da FERRAMENTA, não o formato dela.
Podia ser planilha, podia ser pasta de arquivos renomeados, podia ser página.

**Decisão: página HTML local, com estado em disco.** Três coisas na frase dele,
e a leitura foi literal, uma a uma:

| frase dele | o que virou |
|---|---|
| *"avaliar"* | marca de quatro estados — SIM / TALVEZ / NÃO / sem marca — clicável e por teclado (S/T/N), com pré-triagem por medida para o melhor vir primeiro |
| *"comentar"* | campo de texto livre por quadro, gravado junto da marca |
| *"saber depois onde está"* | cada quadro carrega **caminho absoluto**, vídeo de origem e timecode, e a exportação sai com os três |

**Motivo de não ser planilha:** 9.980 quadros só se julgam vendo. Planilha com
caminho não mostra imagem, e miniatura embutida em XLSX não abre rápido.

**Motivo de não ser pasta de arquivos:** renomear ou copiar 9.980 JPG para
organizar seria mexer no acervo dele. `nada se apaga`, e nada se move.

**O que a página é:** `out/acervo/ACERVO.html` — abre com dois cliques, sem
servidor, sem internet. Miniaturas em arquivo separado (`out/acervo/thumbs/`),
catálogo em `dados.js`, e o JPG original abre no visor a partir do disco.

### D047 · A seleção mora no navegador — e isso foi provado, não suposto

**Ambiguidade, e é a mais cara desta sessão:** *"saber depois"* exige que a
marca sobreviva a fechar a página. Sem servidor, sobram três caminhos:
localStorage, File System Access API, ou exportação manual a cada mudança.

**Decisão: localStorage como principal, exportação como garantia, importação
como volta.** Descartados:

- **File System Access API** — `showSaveFilePicker` só existe no Chrome, e em
  `file://` o comportamento não é garantido. Depender dela é apostar o trabalho
  dele num recurso que pode não existir no navegador que ele abrir.
- **exportação manual a cada mudança** — obriga a lembrar. Trabalho perdido por
  esquecimento é o modo de falha mais provável, não o mais raro.

**O risco real do localStorage, escrito porque é o que pode dar errado:** em
`file://` o Chrome dá **um armazenamento só para todos os arquivos locais**, e
limpar dados de navegação apaga tudo. Por isso a exportação existe e o contador
de "N sem exportar" fica vermelho no topo.

**Isto foi PROVADO em navegador de verdade, não deduzido:**
`scripts/provar_pagina_acervo.mjs` sobe um Chromium por `puppeteer-core`, abre a
página por `file://`, marca, comenta, **recarrega** e confere que a marca e o
comentário continuam lá. Treze testes, todos passando. Os que importam:

```
ok   localStorage NAO esta bloqueado em file://
ok   a marca SIM sobreviveu ao recarregar
ok   o comentario sobreviveu ao recarregar
ok   a exportacao traz o caminho ABSOLUTO do arquivo
ok   o visor carrega o JPG ORIGINAL do disco  -- 1512px de largura natural
```

Prometer persistência em markdown já falhou neste projeto (delta `0029`). Aqui
ela é portão em código, e roda em 20 segundos.

**Defeito achado e corrigido pela própria prova:** o aviso de `beforeunload`
disparava a cada recarga e **travava a navegação**. Como o localStorage funciona,
recarregar não perde nada — o aviso virou ruído. Passou a aparecer só quando há
risco real: armazenamento bloqueado, ou 25+ marcas sem nenhuma cópia em arquivo.

### D048 · Uma âncora marca UM quadro, não quarenta

**Ambiguidade:** os 44 quadros escolhidos à mão em 15/08 (D034) são a única
coisa conferida por olho neste acervo. Como estendê-los para 9.980?

**Primeira tentativa, e estava errada:** todo quadro a ±3 s de uma âncora
herdava o local como `ancora`. Deu **498 âncoras** de 42 escolhas. O motivo é
estrutural: voos como `DJI_0935_stabilized` têm **100 quadros em 2 segundos**, e
ali uma escolha à mão virava quarenta. Chamar aquilo de âncora é mentira
estatística — ninguém olhou 498 quadros.

**Decisão:** uma âncora marca **o quadro mais próximo dela no tempo**, e só. Deu
**40**. O resto do mesmo voo, até 12 s, sai como `perto_da_ancora`, com o texto
dizendo *"MESMO VOO, mas ninguém olhou este aqui"*. Todo o resto sai
`nao_classificado`.

**Por que a maioria sem local é a resposta certa, e não uma desistência:**
nenhum quadro foi reconhecido por conteúdo, e este material é venda de espaço
físico. Um quadro no local errado é pior que um quadro sem local. O que os não
classificados levam é **sugestão** — quais locais aquele *mesmo voo* toca em
algum instante —, e a página diz na cara que sugestão não é classificação.

### D049 · O período saiu do brilho e foi para o carimbo da câmera

**Ambiguidade:** o filme acontece às 18:20–18:55 (`data/luz.json`), e ele pediu
uma finalização *"anoitecendo"*. Separar dia de noite no acervo é filtro de
primeira necessidade. Por qual medida?

**Primeira versão: brilho mediano do voo.** Falhou de um jeito que só apareceu
ao cruzar as duas fontes — **13 voos gravados entre 21h e 23h saíam como
"crepúsculo"**. Noite de evento com iluminação artificial forte tem o mesmo
brilho de um fim de tarde, e o pixel não distingue.

**Decisão: o carimbo da câmera vence o brilho.** `DJI_20251126185022_…` é
26/11/2025 às 18:50, e isso é medida da própria câmera, não inferência. Faixas:
dia 6h–17h, **fim de tarde 17h–19h**, noite fora disso. Onde o nome não carrega
hora — **95 dos 173 voos**, os `DJI_09xx` e os `1 (N)` — o brilho volta a valer,
e o registro grava em `periodo_de_onde` qual dos dois decidiu.

| período | quadros |
|---|---|
| dia | ~2.900 |
| **fim de tarde — a luz declarada do filme** | **~4.400** |
| noite | ~2.500 |

**O que isso destrava:** a ordem dele sobre anoitecer tem ~2.500 quadros de
material real por trás, em 36 voos.

### D050 · Sobrescrevi o `INDICE.md` dele. Erro meu, e a armadilha fica escrita

**O que aconteceu:** extraí o `IMG_0706.MOV` para a pasta de extração com o
`extrair_quadros.py` dele. O script **regrava o `INDICE.md` inteiro** a cada
execução, só com os vídeos daquela rodada. O índice de **316 KB com 151 voos**
virou um de **1,2 KB com um voo**.

**Não é bug do script dele** — é o comportamento normal de quem escreve o índice
no fim de cada rodada. É armadilha de quem usa a ferramenta fora do fluxo
original, e o fluxo original é rodar tudo de uma vez.

**Conserto, e ele é completo:** `scripts/refazer_indice_extracao.py` reconstrói
o índice do disco. O nome de cada quadro carrega o timecode e a duração sai do
ffprobe do vídeo — o conteúdo é 100% recuperável. Está de volta com **~350 KB**,
maior que o original porque agora inclui os cinco vídeos novos.

**O que NÃO se recupera, e está declarado no cabeçalho do próprio arquivo:** a
**ordem** das seções, que era a ordem em que ele rodou a extração. Elas saem
ordenadas pela data da pasta, que é a melhor aproximação possível.

**Regra que fica:** antes de rodar ferramenta de terceiro sobre pasta do
cliente, conferir o que ela regrava. Custa um `grep write_text`.

### D051 · Extraí os 4 vídeos que faltavam — e dois eram âncora órfã

**Levantado, não suposto:** dos **173 vídeos** nas duas pastas, **4 não tinham
quadro extraído nenhum**. Dois deles eram exatamente as âncoras de **P16
(Máquinas)** e **P18 (Área de Shows)** — o catálogo de 15/08 apontava para
material que não existia em quadro.

| vídeo | quadros |
|---|---|
| `DJI_0937_stabilized` | 14 — âncora de P16 |
| `DJI_0937_stabilized_1` | 14 — âncora de P18 |
| `DJI_0938_stabilized` | 12 |
| `DJI_0938-001` | 100 |
| `IMG_0706` | 16 — o da ordem no nome da pasta |

**Decisão de usar o script dele e não escrever outro:** mesma convenção de nome,
mesmo timecode no arquivo, mesma folha de contato. Ferramenta nova produziria
material que não conversa com o resto do acervo.

**Agora os 173 vídeos têm quadros.** Cobertura fechada.

### D052 · Bloqueio: `docs/prompts-higgsfield.md` não existe

O `INDICE.md` manda preencher a coluna **Bloco** com *"o número do bloco de
`docs/prompts-higgsfield.md`"*. **Esse arquivo não existe** — procurado por nome
em `render-expovizinhos/`, em `Brutos Expo` e em toda a árvore de `E:\I.A Edit`.
O que existe com esse nome são as *skills* do HyperFrames, que são outra coisa.

**Diagnóstico:** o texto veio junto com o `extrair_quadros.py`, que é um script
genérico reaproveitado de outro fluxo. A numeração que ele pressupõe nunca foi
criada para este job.

**Decisão: não inventei a numeração.** Criar blocos de prompt é decidir o que
vai ser gerado por IA, e este projeto **não gerou uma única imagem** (D036) —
por ordem dele, a geração é passo dele. Inventar vinte blocos aqui seria
arbitrar o roteiro de geração inteiro.

**O que a coluna Bloco virou, na prática:** os **22 planos** de
`data/planos.json` e os **19 pontos** do `docs/BRIEFING.md`, que é numeração que
existe e é do cliente. A página organiza por eles.

**Fica como pendência dele:** se ele quiser mesmo a numeração Higgsfield, ela
precisa nascer antes — e é decisão de conteúdo, não de catálogo.

### D053 · A ordem que estava escrita num nome de pasta, e o conflito que ela cria

A pasta que ele criou se chama, literal:

> `Fala do drone colocar como finalização e anoitecendo depois entra a logo animada`

**Decisão: tratado como ordem do cliente, não como nome de pasta.** Está
registrado em `docs/ACERVO.md` e o vídeo (`IMG_0706.MOV`, 21,6 s, 4K, 120 fps,
com áudio) entrou no acervo com 16 quadros.

**E aqui há um conflito que eu NÃO resolvi, de propósito.** O `ESTADO.md` lista
como restrição de rejeição:

> **6.** Plano final saindo pelo portal.

A ordem nova diz que a finalização é o IMG_0706, anoitecendo, com logo animada
depois. As duas leituras cabem:

- **soma** — sai pelo portal, anoitece, entra a logo; ou
- **substituição** — o portal deixa de ser o plano final.

A primeira mantém a restrição do cliente e a segunda a quebra. **Pergunta
aberta**, e é barata de responder.

### D054 · Um quinto do acervo está EM PÉ

**Medido:** **2.116 quadros**, em **51 dos 173 voos**, são verticais —
1512×2688, 1080×1920, 1508×2680, 2160×3840. O drone gravou para vertical.

**Por que isso é decisão e não curiosidade:** o filme é deitado, e quadro em pé
não vira placa sem corte pesado. Se ele marcar cinquenta quadros verticais
achando que servem de referência de enquadramento, o trabalho é perdido depois.

**Decisão, e é conservadora nos dois sentidos:** a orientação **não penaliza a
nota** — quadro vertical é ótimo material para corte social, e a nota mede
qualidade de imagem, não adequação de formato. Ela entra como **filtro próprio**
e como etiqueta visível na carta. E a miniatura **não corta** o quadro: mostrar
o vertical inteiro numa grade irregular é feio e é honesto; cortar para a grade
ficar bonita esconderia justamente o que ele precisa julgar.

### D055 · Duas sessões de hoje discordam sobre a procedência de um terço do acervo — e eu não desempatei

**Este é o achado mais caro desta sessão, e ele não é meu:** já estava escrito,
em dois lugares que nunca foram cruzados.

| fonte, mesma data | o que diz sobre `DJI_2025112*` |
|---|---|
| `data/quadros-ia.json` (sétima sessão, manhã) | usa **12 desses voos como âncora**, oito delas marcadas `confirmado` |
| `docs/COMO-O-PARQUE-ESCREVE.md` (nona sessão, noite) | *"nem tudo em `F:` é Dois Vizinhos… outro recinto — autódromo oval, silos de grão… usar aquilo seria errar de cidade"* |

**O tamanho do problema, medido:** os voos com carimbo de câmera entre
**25 e 30/11/2025** são **74**, com **3.270 quadros — 33% do acervo**. E as 12
âncoras que caem neles cobrem **P01, P02, P09, P10, P11, P12, P13, P14, P15 e
P20** — dez dos vinte e dois planos, entre eles a Fazendinha, que é diferencial.

**O que eu olhei, e não fecha:** montei `out/acervo/_duvida-recinto.jpg` com
quatro quadros lado a lado. O `1 (3)` (quinta, Dois Vizinhos sem contestação)
mostra o recinto **cercado de lavoura**, com a bacia em anfiteatro. O
`DJI_20251127184025_0104_D` mostra um recinto **dentro de uma cidade**, com
torre de telecomunicação alta ao lado. **Isso empurra a favor da nona sessão,
mas um quadro de cada não é prova** — pode ser outro lado do mesmo terreno.

**Decisão: não desempatei, e sinalizei alto.** Arbitrar aqui é o pior tipo de
arbitragem — posição de área e nomenclatura são material de venda de espaço
físico, e as duas saídas são caras:

- tratar como outro recinto e estar errado joga fora 3.270 quadros e dez planos;
- tratar como Dois Vizinhos e estar errado põe a cidade errada no vídeo do
  cliente.

**O que fiz no lugar:** faixa fixa no alto da página com o número; **selo
vermelho "RECINTO EM DÚVIDA"** em cada carta dos 74 voos; filtro para separar os
dois grupos; e o campo `recinto` na exportação, para que a escolha dele já saia
carimbada. **É a pergunta mais barata desta lista e a que trava mais coisa.**

### D056 · O levantamento novo supera o anterior em cobertura, e não o substitui em julgamento

**Ambiguidade:** ele mandou *"faça novamente o levantamento"*. Refazer pode
querer dizer substituir.

**Decisão: os dois ficam, com papéis declarados.**

| | `out/quadros-ia/INDICE.html` (manhã) | `out/acervo/ACERVO.html` (agora) |
|---|---|---|
| quadros | 44 do footage + 52 da cena 3D | 9.980 do footage |
| conferido a olho | **todos os 44**, com o porquê escrito | nenhum |
| classificado por local | 22 locais, todos | 40 âncoras + vizinhança; o resto sem local |
| serve para | dizer sim ou não a uma escolha pronta | garimpar no acervo inteiro |

Os 44 são a única coisa olhada por gente neste acervo, e entram no novo como
**âncora**. Apagar a página antiga jogaria fora o único julgamento humano que
existe. `nada se apaga`.

### D057 · Dois voos dividiam a mesma identidade — quatro quadros, e silencioso

**Como apareceu:** conferi o número de miniaturas em disco contra o número de
quadros no catálogo. **9.976 contra 9.980.** Quatro a menos, e a checagem de
"quadro sem miniatura" dizia zero — porque as quatro *existiam*, só que
compartilhadas.

**A causa:** `DJI_0953_stabilized_1` e `DJI_0953_stabilized_1_` são duas pastas
diferentes — a segunda nasceu de `DJI_0953_stabilized_1(1).mp4`, e o
`nome_limpo` dele troca parêntese por `_`. As duas caem no **mesmo slug**,
`dji-0953-stabilized-1`. Com isso, quatro quadros dividiam `id` e miniatura.

**O que isso causaria na mão dele, que é o que importa:** marcar um marcaria o
outro, e a carta mostraria a imagem do voo errado. Quatro em 9.980 — o tipo de
erro que nunca aparece numa conferência por amostra.

**Conserto:** `mapa_de_slugs()`. Onde o slug básico se repete, todos os que o
dividem ganham 4 hex do md5 do nome original. Determinístico e estável, não
depende de ordem de leitura nem do que mais existe na pasta.

**E virou portão, não parágrafo** (delta `0029`): `pagina_acervo.py` **aborta**
se houver `id` repetido, miniatura compartilhada ou miniatura ausente. Custa
meio segundo e é a diferença entre um defeito conhecido e um defeito que sai
para o cliente.

**O que isso ensina sobre a checagem:** eu tinha escrito uma verificação de
"quadro sem miniatura" e ela passou com zero. A pergunta certa não era *"todo
quadro tem miniatura?"* — era *"cada miniatura pertence a um quadro só?"*.
Contagem de arquivo contra contagem de registro foi o que abriu o buraco.

---

## 2026-08-15 — resposta dele à pergunta do final

### D058 · O final é dele — a pergunta 2 está fechada, e fechada sem escolha minha
**A pergunta que eu tinha deixado aberta:** a pasta com a ordem no nome
(*"Fala do drone colocar como finalização e anoitecendo depois entra a logo
animada"*) **soma** ao plano final saindo pelo portal (restrição 6) ou
**substitui** ele?

**Resposta dele, literal:** *"final deixa comigo"*.

**Decisão: não decidir.** Não é ambiguidade a resolver pelo lado conservador —
é escopo tirado da minha mão e devolvido para a dele. A restrição 6 continua
escrita como está, e nada de finalização entra em geometria, decupagem ou
prompt sem ele dizer.

**O que isso não cancela:** o `IMG_0706.MOV` continua extraído (16 quadros) e os
2.535 quadros noturnos de 36 voos continuam no acervo e filtráveis — material
levantado é material disponível quando ele for montar o final. O que para é a
**decisão** sobre o final, não o levantamento dele.

**Consequência para as próximas sessões:** não repropor arranjo de final, não
sugerir corte de fechamento e não gastar rodada em "como o filme termina".
Quem pergunta isso é ele.

---

### D059 · O portal e a câmera de P02/P22 discordam em 77° — e eu não desempatei

**Como apareceu.** Com a letra na superfície, o portão novo de obliquidade
reprovou P02 e P22 com *"77 graus da fachada"*. Não era defeito do letreiro: é
que a **fachada do portal e a câmera dos dois planos apontam para lugares
diferentes**.

**As três medidas, e elas não fecham:**

| o quê | direção |
|---|---|
| normal da fachada do `PortalCeleiro` (rumo 73° aplicado ao vão) | **163° / 343°** |
| câmera do P02 / do P22 (`azimute_deg`) | **60° / 240°** |
| estrada de asfalto dele, no trecho junto ao portal | **34° / 214°** |

O comentário do próprio `RUMO_PORTAL = 73.0` diz *"de frente para quem chega
pela Dorvalino Tosi"* — ou seja, a **intenção escrita é que 73° seja a direção
que o portal ENCARA**. Mas `estruturas.portal()` aplica `rumo_graus` ao giro do
objeto, e o objeto nasce com o vão no eixo X: o resultado é que a fachada olha
para 163°, e não para 73°. As duas câmeras, a 60° e 240°, foram escritas
**straddling 73°/253°** — isto é, na convenção da intenção, não na do código.

**Por que não decidi sozinho.** Havia três consertos e nenhum é barato:

1. **Girar o portal** (`RUMO_PORTAL` de 73 para −17): mexe em geometria que ele
   olhou em 15/08. A pergunta daquela vez foi *"portal girado 92 graus"* e a
   resposta foi *"o portal agora está na **posição** correta"* — resposta sobre
   posição, anotada como aval da rotação. É frágil demais para eu me apoiar.
2. **Girar as câmeras de P02 e P22** para 163°/343°: reescreve o enquadramento
   de abertura e de fechamento do filme.
3. **Tirar a letra da fachada.**

**Fiz a 3, que é a única que não mexe em nada dele.** P02 e P22 saíram de
`placa_suspensa` para `painel_plantado` — painel gira para a câmera e não tem
fachada para ficar de esguelha. Os dois passaram no portão e as duas frases
agora leem inteiras, que é mais do que estava acontecendo: nos stills de 15/08
elas saíam cortadas nas duas bordas.

**O que se perde, e fica registrado como proposta:** a tábua pendurada no
portal é a referência A, o letreiro mais bonito do recinto, e é o modo certo
para uma entrada. `data/letreiros.json` guarda `proposta_em_aberto` nos dois,
esperando ele decidir entre girar o portal ou girar a câmera.

### D060 · A aproximação de 0,45 era a causa dos 9 letreiros cortados, não o portal

O `RETOMAR-1508-OITAVA.md` atribuía os 9 letreiros fora do quadro ao portal ter
mudado de lugar. **Medido, é outra coisa, e a conta fecha exata.**

`letreiros.py` puxava cada letreiro 45% na direção da câmera, para tirá-lo de
trás das árvores. Num **push-in** isso põe o objeto no caminho: no P02 a câmera
fecha de 42 m para 24 m do alvo, e o letreiro estava a 18,9 m do alvo — a
câmera passava a **5 m dele**. O tamanho era calculado para 23 m e a leitura
acontecia a 14 m: **138% da largura do quadro**, que é exatamente o número que o
portão acusou.

Confere com a lista inteira: **P02, P06, P08, P14 e P22 são todos push-in**. E
os quatro restantes — P09, P11, P16, P18 — são **sobrevoo com alvo que viaja**:
a mira anda até 45 m durante o plano e o letreiro plantado ficava para trás.

Dois consertos, e nenhum deles é "diminuir a letra":

- **aproximação zerada.** A oclusão passou a ser resolvida pela altura da faixa
  na fachada, que é como o parque resolve de verdade.
- **o letreiro acende só no trecho em que cabe no quadro.** `janela_em_quadro()`
  mede com a `world_to_camera_view` do Blender, a mesma função do portão, e as
  chaves de visibilidade saem dessa janela. Menos de 2 s em quadro reprova.

**Por isso `letreiros.construir` passou a rodar DEPOIS das câmeras.** Enquanto
rodava antes, a única coisa mensurável era distância — e distância não vê a mira
viajar.

---

## 2026-08-15, noite — a ordem de fechar hoje

> **Ordem literal:** *"Eu vou sair 4h00 tome todas as medidas necessárias pra
> finalizar hoje"*. Ela destrava duas coisas que eu vinha devolvendo para ele por
> serem decisão de quem dirige: o **reenquadramento dos planos** e o **desempate
> da procedência do acervo**. O que ela **não** destrava é o **final** — D058
> continua valendo, *"final deixa comigo"*, e nada de fechamento foi tocado.

### D061 · A procedência do acervo estava resolvida desde 14/08 e ninguém tinha aberto o metadado

**A dúvida (D055):** 71 pastas e 2.770 quadros, um terço do acervo, cobrindo dez
dos vinte e dois planos. A sétima sessão usava 12 desses voos como âncora
confirmada; a nona escreveu que eles são de *"outro recinto — autódromo oval,
silos de grão"*. Eu tinha deixado em aberto porque as duas saídas erradas são
caras.

**O que eu não tinha feito, e era o mais barato de todos: olhar o GPS.** A DJI
grava latitude e longitude amostra a amostra num stream `djmd` dentro do MP4.
`_triagem/telemetria/*.resumo.json` tem a mediana de cada voo **desde 14/08** —
faltava cruzar com a coordenada do recinto. Trinta linhas de código.

**O cruzamento**, em `scripts/provar_recinto.py`, contra
−25,73144 / −53,07627, num terreno de 808 × 454 m:

| | |
|---|---|
| pastas sob dúvida | **71** |
| com GPS, **dentro** do recinto | **60** pastas · **2.440** quadros |
| com GPS, **fora** | **0** |
| distância | **mín. 24 m · máx. 387 m** |
| sem GPS próprio | 11 pastas · 330 quadros |

**E o que mata o argumento da nona sessão:** as duas feições que ela citou
aparecem **dentro de voos com GPS confirmado**. O **oval** está em
`DJI_20251126155520_0054_D`, a **168 m**. Os **silos de grão** em
`DJI_20251129182345_0168_D`, a **336 m**. E o `DJI_20251127184025_0104_D`, que
ela leu como "recinto dentro de uma cidade", está a **79 m**. Não é outra
cidade: é o recinto e a cooperativa da esquina.

**As 11 sem GPS** são exports estabilizados — o estabilizador não copia o
`djmd`, e o MP4 original não está mais no disco (armadilha 47). Elas mostram a
mesma feira, o mesmo horizonte e o mesmo oval das provadas, do mesmo drone, no
mesmo dia, com numeração (0034–0046) intercalada com 0053/0054, que estão
provadas.

**Decisão: nada é descartado, e a dúvida está fechada.** Custo evitado: 2.770
quadros e dez planos. Na página, o selo vermelho *RECINTO EM DÚVIDA* virou a
etiqueta discreta **SEM GPS PRÓPRIO** — a resposta ser boa não apaga a diferença
entre medido e não medido.

**Propagado para:** `data/recinto-gps.json` (novo), `scripts/provar_recinto.py`
(novo), `docs/COMO-O-PARQUE-ESCREVE.md`, `docs/ACERVO.md`,
`data/quadros-ia.json`, `scripts/pagina_acervo.py` e `out/acervo/ACERVO.html`
regenerada e reprovada pelo portão do Chromium.

**O que isto ensina, e é o mais caro:** eu tinha a resposta no disco havia um
dia e escrevi três documentos discutindo a pergunta. Antes de registrar uma
dúvida como cara, procurar o metadado — a lista do que já foi extraído está no
`ESTADO.md` e ninguém a leu contra a pergunta.

### D062 · Quatro letreiros nomeavam um lugar e apareciam sobre outro

**Achado por cruzamento, não por olho:** o texto de cada letreiro contra o
**rótulo do alvo** do plano a que ele estava amarrado, em `data/planos.json`.

| letreiro | estava em | a câmera desse plano olha | vai para |
|---|---|---|---|
| Pista de Julgamentos | P16 | Exposição de Máquinas e Implementos | **P12** |
| Expositores Externos | P17 | um ponto xy do pátio de veículos | **P13** |
| Máquinas e Implementos | P18 | Área de Show | **P16** |
| Área de Shows | P20 | PALCO | **P18** |

P02 a P14 casavam. A partir de P16 havia deslocamento sistemático — sinal de
`planos.json` renumerado sem `letreiros.json` acompanhar.

**Por que é grave e não é detalhe:** o letreiro é o que vende espaço físico. Um
sobrevoo do pátio de máquinas com a placa "Pista de Julgamentos" por cima não é
um erro de gosto, é informação errada entregue ao cliente. **Nenhum dos três
portões de letreiro pegava isso** — eles medem se a letra cabe, não se ela diz a
verdade.

**Decisão: reamarrado pelo rótulo do ALVO, não pelo título.** Título é texto de
tela e pode divergir; o alvo é coordenada da planta. P17 e P20 ficam **sem
letreiro**, e isso é de propósito: escrever "Veículos e Motos Náuticas" e "Palco
Principal" seria inventar placa, e nomenclatura de área é material de venda. Vai
como pendência, não como suposição.

`data/letreiros.json` guarda `plano_antes_1508` e o motivo em cada um.
Backup em `data/letreiros.ANTES-1508d.json`.

### D063 · O reenquadramento virou medida, não gosto — e o portão que faltava mede DOMÍNIO

**A ordem destravou o que eu vinha devolvendo.** A forma honesta de destravar
não era eu escolher enquadramento a olho: foi medir o defeito, buscar o menor
ajuste que conserta e deixar o antes e o depois escritos.

**O portão de câmera existente não via o defeito.** Ele testa o primeiro e o
último quadro: enterrada, dentro de volume, superfície colada na mira. Passou
verde em planos cujo still é tela cheia de telhado branco. Foram criados dois
scripts:

- **`scripts/enquadramento.py`** — mede o movimento **inteiro** (9 amostras por
  plano) com uma grade de 45 raios pelo frustum. Devolve `perto` (fração do
  quadro a menos de 14 m), `ceu`, `dominio` (fração num **único objeto**),
  `vegetacao`, e se o assunto está atrás de outra coisa.
- **`scripts/consertar_camera.py`** — varre 891 candidatos por plano (altura
  −4…+44 m, distância ×1,0…×3,8, azimute ±75°), ordenados por **custo
  crescente**, e escolhe o primeiro que passa. Não busca o quadro bonito: busca
  o quadro que não está quebrado com o menor desvio do que já estava escrito.

**A medida que mudou tudo foi `dominio`.** Com teto em `perto` só, o telhado de
um pavilhão a 25 m enchia 70% do quadro e passava verde — 25 m não é perto. O
que mede o defeito é quanto do quadro é **uma superfície só**. Foram três
rodadas, e o teto desceu de 0,55 para **0,40** porque a folha de stills ainda
discordava do número. **Quem manda é o quadro, não o teto.**

**Resultado, medido:**

| | antes | depois |
|---|---|---|
| planos que o portão de câmera reprovava | 12 problemas em 10 planos | **0** |
| planos que o portão de enquadramento reprovava | **18 de 22** | **0** |
| pior `dominio` no filme | 1,00 (P08, tela 100% telhado) | 0,40 |

Cada plano mudado carrega `camera_antes_1508` e `conserto_1508` com o motivo e
os dois números. Relatórios em `out/conserto-camera{,-2,-3}.json`. Backup da
decupagem em `data/planos.ANTES-1508d.json`.

**O que continua imperfeito, e eu não vou fingir que não:** P04 e P08 ainda têm
telhado ocupando boa parte do quadro, e P12, P14 e P18 têm o letreiro em parte
atrás de copa. Passa nos portões e melhorou muito, mas o quadro ainda não está
onde eu gostaria. Folha para julgar: `out/entrega-1508f/contato-22.jpg`.

### D064 · Alongar o plano em vez de encurtar o percurso

Afastar a câmera num push-in alonga o caminho, e o mesmo caminho na mesma
duração dá **velocidade maior**: nove planos saíram da faixa cinematográfica ao
longo das três rodadas. Havia duas saídas e elas não são equivalentes.

**Decisão: alongar a duração** (`scripts/ajustar_duracao.py`). Encurtar o
percurso devolveria a velocidade e enfraqueceria justamente o movimento que faz
o assunto crescer na tela — e **o cliente pediu MAIS tempo de tela**, não menos.
Dos planos alongados, quatro são os diferenciais: Mercado do Produtor
(9,0 → 17,5 s), Café Colonial (9,0 → 13,5 s), Fazendinha (10,0 → 12,0 s) e
Arena de Rodeio (10,0 → 12,0 s).

O filme foi de **4.635 para 5.280 quadros — 154 s para 176 s, +13,9%**. Custa
1,7 h de render e entrega exatamente o que a restrição 5 pede.

### D065 · O render partiu com os três passes, e por quê — 13,5 h, ~08:15 de 16/08

**Medido nesta máquina, OptiX na RTX 4060, 2560×1440, 128 samples adaptativos,
com o mesmo plano duas vezes:**

| arranjo | s/quadro | filme (5.280) | disco |
|---|---|---|---|
| três slots (beauty + data + preview) | **11,6 s** | 17,0 h | 253 GB |
| só PNG | **7,1 s** | 10,4 h | 22 GB |

Os passes custam **4,5 s por quadro (39%)** e **231 GB**.

**Decisão: renderizar com os três slots.** O argumento que fecha não é doutrina,
é aritmética: **nenhum dos dois arranjos termina antes das 4h00**, que é quando
ele sai. 10,4 h também cai de madrugada. Se o relógio não se ganha de nenhum
jeito, otimiza-se o que dá para ganhar — o seguro de refino e o Cryptomatte.

Em regime, o render está saindo a **9,2 s/quadro** (mais rápido que a
calibração, que pegou um plano fechado): **~13,5 h**, término previsto
**~08:15 de 16/08**. Disco: ~43 MB/quadro, **~227 GB de 290 GB livres em F:**.

**A retomada é por quadro** e o render sai **na ordem do roteiro**, então a
qualquer momento existe um prefixo completo do filme em
`F:\render-agroshow\final\preview\` — dá para encodar o que já ficou pronto sem
esperar o fim.

**GPU garantida:** `placa.exigir()` roda antes de tudo e abortaria se caísse
para CPU. O log confirma `OPTIX: NVIDIA GeForce RTX 4060` e registra que *"as
preferências estavam em NONE"* — sem essa chamada o render sairia na CPU, quatro
vezes mais lento, calado (D009).

**O que ele está vendo neste render, e precisa estar dito:** o povoamento é
**proxy** — as 1.681 figuras não são gente nem gado de verdade (D030), e a régua
do Plano B pede que sejam. Não há logo do AGROSHOW 2026 (falta o vetor), as
cotas dos patamares continuam **estimadas**, e o portal segue com a divergência
de 77° do D059.

### D066 · Duas armadilhas novas achadas nesta sessão

**47. Estabilizador de vídeo apaga o GPS.** Os exports `_stabilized` só têm o
stream de vídeo: o `djmd` da DJI não é copiado, e o container guarda apenas
`comment = Original filename: …`. Onze voos ficaram sem coordenada por isso, e
os originais não estão mais no disco. **Extrair telemetria do original antes de
estabilizar** — depois não tem mais de onde tirar.

**48. `ray_cast` devolve o objeto no 5º campo, não no 6º.** A ordem é
`(ok, local, normal, índice, OBJETO, matriz)`. Trocar entrega uma `Matrix` onde
se espera um `Object`, e o erro só aparece em tempo de execução, no meio de uma
varredura de vinte minutos.

### D067b · O render caiu no quadro 238 e voltou — o que quebrou foi o laço com o shell, não a cena

**Registrado porque é o tipo de coisa que, não escrita, se repete.**

Às 19h19 o render parou no **quadro 238 de 5.280**, 36 minutos depois de começar.
Não houve crash: o log termina com um `Saved:` normal. **Morreu o processo pai** —
o shell que lançou o Blender foi encerrado, e o Blender caiu junto.

**O conserto foi pior que o defeito, por um tempo.** Ao tentar relançar de forma
destacada, três caminhos foram testados e dois falharam feio:

- `cmd //c start /B` do git-bash **trava a chamada** e só dispara quando o shell
  é encerrado — ou seja, dispara sozinho depois, sem ninguém esperando;
- `schtasks //Run` funcionou, mas somado ao `start` atrasado resultou em **dois
  renders gravando na mesma pasta**.

Dois renders na mesma pasta é **pior que nenhum**: os dois pulam o quadro que já
existe, mas os dois começam o quadro seguinte e escrevem o mesmo arquivo ao mesmo
tempo. Assim que foi detectado, os quadros do período de sobreposição
(**240 a 243**) foram **apagados e refeitos**. Quatro quadros custam quarenta
segundos; um EXR truncado no meio do filme custa a fila inteira e só apareceria
no encode.

**O que ficou, e é o que interessa:**

1. **Lançar com `nohup … &` a partir de um processo que sobrevive.** O vigia
   (`fechar_entrega.sh`) é esse processo, e é ele quem relança agora.
2. **Aliveness se mede pelo relógio do log, não pela lista de processos.** A
   checagem antiga — *"existe `blender.exe`?"* — foi enganada por um processo
   **vivo e mudo** que sobrou da queda, e o vigia se recusou a relançar por trinta
   minutos por causa da própria trava de segurança. Agora ele compara a hora da
   última escrita: mudo por mais de 7 minutos = morto, mata e relança.
3. **Contar `blender.exe` não conta renders.** Cada sessão do Blender 5.2 aparece
   como **dois** processos. Quem conta sessão é
   `grep -c "Read blend" out/render-final.log`.
4. **Não editar um `.sh` que está rodando.** O bash lê por offset de bytes; a
   instância antiga do vigia continuou com a lógica velha, e dava para ver no log
   dela. Depois de mexer, matar e relançar — e conferir no log que a nova lógica
   subiu.

**Custo real do incidente:** quinze minutos de GPU parada e quatro quadros
refeitos. **Custo evitado:** um render de treze horas terminando pela metade sem
ninguém por perto, ou terminando com arquivo corrompido no meio.

**Estado depois do conserto:** uma sessão só, **10,0 s/quadro** medidos em dois
minutos corridos, previsão de término por volta das **09:30 de 16/08**. O número
subiu em relação aos 9,1 s iniciais porque os primeiros planos são os mais
baratos do filme — a média real só se conhece no fim.

---

### D067 · Os nomes saem da cena 3D, e o portal girou

**Duas ordens dele em 15/08 à noite.**

**"Quero que deixe sem os nomes, na hora da câmera passar."** Os letreiros
saíram da cena. O padrão do `build_scene.py` agora é **sem**, e
`--com-letreiros` traz de volta. Nada foi apagado: o texto de cada um, o áudio
de origem e o suporte declarado continuam em `data/letreiros.json`, e os quatro
modos e os três portões continuam em `scripts/letreiros.py`.

**É a decisão certa e eu devia ter proposto.** Nome dentro do 3D custa
re-render inteiro para trocar uma palavra; nome por cima do filme se troca em
minutos, aceita a tipografia que ele escolher e não briga com a câmera. Foi
essa briga que consumiu a sessão: quatro portões novos e sete planos mexidos
para caber uma letra que sai mais barata em cima.

**"A fachada do Portal Celeiro pode girar e reordenar a câmera."** Isso fecha o
D059. `RUMO_PORTAL` foi de **73° para 124°**, e o número saiu da estrada de
asfalto que ele mesmo marcou: no trecho a 20 m do portal ela corre em 34°/214°,
e portal que se atravessa fica perpendicular à estrada. A câmera **não precisou
mudar** — P02 (azimute 60°) e P22 (240°) passaram de 77° para **26°** da
fachada. A autorização de mexer na câmera não foi usada.

### D068 · "Você faz tudo pela metade" — o que estava errado no meu método

Palavras dele, 15/08 à noite: *"parece que você faz tudo pela metade preciso
melhora consideravelmente o render"*, junto com *"não renderiza nada ainda"* e
*"sempre quero revisar no blender antes de pontos importantes"*.

**O que eu vinha fazendo, e é o defeito:** fechava cada etapa renderizando um
still e julgando por ele. Still de 1280×720 a 128 samples esconde exatamente o
que precisa de julgamento — material, escala, o que o povoamento proxy parece de
perto — e ainda gasta GPU que não estava autorizada. Pior: eu tratava o still
como prova de que a etapa estava pronta, quando ele nunca tinha visto a cena.

**Regra nova, e ela é dele:** ponto importante se revisa **no Blender**, abrindo
o `.blend`. Render só quando ele mandar. O que eu entrego é a cena, com as
câmeras montadas e os marcadores nos planos.

**O que "melhorar consideravelmente o render" quer dizer, medido:** hoje a cena
é caixa branca com povoamento proxy. Os pontos fracos, em ordem de peso —
edificação sem textura, 1.681 figuras que não são gente nem gado (D030),
vegetação genérica, e ausência do conteúdo de dentro que ele disse que ia
providenciar. Nada disso se resolve com sample nem com resolução.

---

### D069 · Parei o render por causa de uma ordem dele que eu não tinha visto

**O que eu estava fazendo:** o filme inteiro renderizando desde 18h43, 958 de
5.475 quadros no disco, com vigia programado para encodar a entrega sozinho de
madrugada. A ordem que eu tinha era *"tome todas as medidas necessárias pra
finalizar hoje"*.

**O que eu achei às 21h37,** ao reconstruir a cena e ler a saída do gerador:

> `letreiros .......... FORA da cena, por ordem dele de 15/08 a noite:`
> `'deixe sem os nomes, na hora da camera passar'.`

Puxando o fio, no `DECISOES.md` estavam **D067 e D068**, escritas por outra
sessão entre 19h28 e 19h40 — **depois** de o meu render começar — com três
frases literais dele:

- *"Quero que deixe sem os nomes, na hora da câmera passar."*
- *"A fachada do Portal Celeiro pode girar e reordenar a câmera."*
- ***"não renderiza nada ainda"***, junto de *"sempre quero revisar no blender
  antes de pontos importantes"* e *"parece que você faz tudo pela metade preciso
  melhora consideravelmente o render"*.

**Decisão: parei o render.** Três razões, e a primeira sozinha bastava.

1. **Ele mandou não renderizar.** Entre duas ordens dele, vale a mais recente. A
   minha era de umas 18h; essa é da mesma noite e chegou depois.
2. **O que estava saindo já estava errado, e não por qualidade.** Os 958 quadros
   têm **letreiro dentro da cena 3D** — exatamente o que ele mandou tirar — e o
   **portal no rumo antigo de 73°**, quando ele autorizou girar e o rumo virou
   124°. P02 e P22, que são a abertura e o fechamento, mudam de cara.
3. **Continuar custava 11 h de GPU** para produzir um arquivo que já se sabia
   recusado. Parar custa 2,6 h de GPU já gasta, e é reversível.

**Não apaguei nada.** Os 958 quadros foram para
`F:\render-agroshow\final-1508-SUPERADO-letreiros-em-3d\`, com um `LEIA-ME.txt`
dizendo por que não servem e avisando que a pasta **não** deve ser usada como
retomada — `render_shots.py` pularia quadro errado.

**O que eles ainda valem:** são a medida de custo real deste filme, e ela agora
está em regime e não em amostra — **10,0 s/quadro** e **35 MB/quadro**, OptiX na
RTX 4060, 2560×1440, com beauty + data + preview.

**O erro de método, meu, e ele é o mesmo que a D068 aponta:** eu disparei um
render de 13 horas e depois passei três horas escrevendo documentação sem reler
o `DECISOES.md`. A ordem estava lá havia duas horas. **Antes de deixar uma
máquina moendo a noite inteira, reler o arquivo de decisões** — num repositório
onde mais de uma sessão escreve, o estado muda debaixo do trabalho em curso, e
foi o `build_scene.py` que me avisou, não eu.

### D070 · O conserto de enquadramento sobreviveu à parada, e ficou melhor

O trabalho de câmera desta sessão continuou valendo, porque ele é sobre a
decupagem e não sobre o render. Mas teve de ser **refeito contra a geometria
nova**: com o portal em 124°, o portão de câmera passou a reprovar P04 e P07
("dentro de geometria fechada"), que antes passavam.

**Duas rodadas, e a primeira foi descartada por medida.** Rodando o solver no
modo normal — distância por **fator** — os 22 planos passaram, mas
`ajustar_duracao.py` teve de esticar onze deles para segurar a velocidade, e o
filme foi de **182 s para 273 s: +49,6%**. Quatro minutos e meio é outro
produto, e ninguém pediu. Ficou registrado em
`data/planos.DESCARTADO-solver5-273s.json`.

**A rodada que ficou usa distância por SOMA** (`--sem-renumerar`). Num push-in o
comprimento do caminho é `|dist_ini − dist_fim|`: somar o mesmo valor nas duas
pontas afasta a câmera e deixa o comprimento, a velocidade e a duração
exatamente onde estavam. **21 planos reenquadrados, duração de nenhum alterada,
filme intacto em 182 s.**

| portão | resultado |
|---|---|
| `conferir_camera.py` | **0 problemas** |
| `enquadramento.py` | **0 reprovados** em 22 |
| `planos.py --conferir` | todas as velocidades na faixa, 5.475 quadros |

**Três planos passaram por melhor-esforço, e eu não vou esconder qual:** P03,
P05 e P12. Nenhum candidato dos 891 passou em tudo; ficou o menos ruim, e o pior
deles é **P05, com domínio 0,62** — a fachada do Pavilhão 2 ainda toma boa parte
do quadro. Estão carimbados com `MELHOR ESFORCO` no campo `conserto_1508` de
`data/planos.json`.

**Não renderizei still para provar, de propósito.** A D068 é explícita: ponto
importante se revisa **no Blender**, e render só quando ele mandar. A prova aqui
são os três portões e o `.blend` aberto.

**Onde ele abre:** `out/cena-revisar.blend`. A versão de 19h40, sem o conserto de
câmera, virou `out/cena-revisar-1940-antes-do-conserto-de-camera.blend` — dá
para abrir as duas e comparar plano a plano pelos marcadores da timeline.

---

### D071 · A fotogrametria foi tentada e não fechou — o que ficou provado, e o erro que eu cometi

> **⚠ SUPERADA por D072, em 16/08/2026.** Esta decisão está ERRADA na conclusão
> e certa no método. A fotogrametria **fechou**: eu li o submodelo `0` — que é o
> descarte de duas imagens — em vez do `1`. Fica registrada porque **nada se
> apaga**, e porque o erro dela vale mais que o acerto dela:
> *ler a pasta não é ler o dado.*

**Pergunta dele, 15/08 à noite:** *"é possível criar um mapa 3d só usando as
imagem que tenho no extrator para com esse 3d melhorar esse render?"* Respondi
que sim com ressalvas; ele autorizou baixar a ferramenta e mandou seguir duas
vezes. **Não fechou.** Handoff em `RETOMAR-1608-FOTOGRAMETRIA.md`, log completo
em `docs/FOTOGRAMETRIA.md`.

**O achado que vale mais que o resultado: não existe voo de mapeamento neste
acervo.** Pitch do gimbal medido nos 62 voos com telemetria — **zero em nadir**,
5 entre −60° e −35°, 57 oblíquos ou de horizonte. Ortofoto e modelo de terreno
do recinto inteiro estão fora, e não por limitação de ferramenta. O que existe
são **32 órbitas**, e órbita reconstrói *um assunto*, não um sítio.

**O erro que eu cometi, e ele custou uma rodada inteira.** Ranqueei os voos pela
**hora no nome do arquivo** e propus a arena de rodeio como primeiro alvo. Fui
olhar os quadros: o voo que o nome diz 10h35 é **show noturno, com multidão e
fogos**. Refiz a triagem medindo **luminância no pixel** — 156 pastas — e
sobraram 15 candidatos reais. É o mesmo defeito que ele apontou em D068: eu
tinha construído um ranking inteiro sobre suposição não conferida.

**Regra que fica:** neste acervo, triagem se faz no pixel, nunca no nome do
arquivo.

**Seis tentativas, e o que cada uma descartou.** Duas versões do COLMAP (4.1.1 e
3.11.1, 513 MB baixados com autorização dele), dois conjuntos, focal varrida em
quatro valores, pose prior de GPS por quadro injetado no banco. Ficou descartado
por medida: material corrompido (100 arquivos distintos, mediana de 214 inliers
por par), versão da ferramenta (as duas falham igual), cena não-rígida (o
conjunto de dia tem só 3,4% de pares degenerados contra 42% do noturno) e
limiar de PnP. O melhor resultado foi com **focal 1792 px** — a wide de 24 mm do
**DJI Air 3 (`FC8282`)**, que o metadado do MP4 entregou: 13 imagens
registradas, mas com 2 pontos 3D. Modelo degenerado.

**A hipótese que sobra e que não testei: textura repetitiva.** Telha metálica
ondulada e chão de saibro geram casamento que passa no RANSAC como plano e não
triangula — é a única explicação que cobre "centenas de inliers, dois pontos".

**Próximo passo é trocar de ASSUNTO antes de trocar de ferramenta:** o voo
`DJI_20251129182345_0168_D`, com árvore e barraca em vez de telhado. Dez minutos
de máquina. Não rodei porque ele mandou salvar para retomar.

**Nenhuma GPU-hora foi gasta em render nesta frente**, e os bancos ficam com
features e casamentos calculados: retomar não repete o custo.

## 2026-08-16 — noite dos três quadros

### D072 · A fotogrametria fechou. Eu li a pasta, não o dado
**O que estava escrito e está errado:** `D071`, `RETOMAR-1608-FOTOGRAMETRIA.md` e
`docs/FOTOGRAMETRIA.md` dizem que as seis tentativas falharam, com o melhor
resultado em "13 imagens e 2 pontos 3D".

**O que o disco diz.** O COLMAP escreve VÁRIOS submodelos. O `0` é quase sempre o
descarte de duas imagens; a reconstrução boa é o `1`. Lido no cabeçalho binário
(`images.bin` e `points3D.bin`, uint64 little-endian nos 8 primeiros bytes) e
confirmado por `model_analyzer`:

| modelo | imagens | pontos | erro reproj. | trilha |
|---|---|---|---|---|
| `montagem/sparse/1` | 100/100 | 42.090 | 0,797 px | 5,67 |
| `montagem/sparse311/1` | 100/100 | 42.300 | 0,796 px | 5,65 |
| `montagem/sparse4/1` | 100/100 | 42.199 | 0,886 px | 5,75 |
| `montagem/sparsec/2` | 100/100 | 42.020 | 0,794 px | 5,67 |
| `fazendinha/sparse/1` | 150/150 | 37.730 | 0,602 px | 10,35 |
| `fazendinha/sparse3/0` | 150/150 | 37.945 | 0,616 px | 10,31 |

Os logs já diziam `num_reg_frames=99` e `Keeping successful reconstruction`.
**Todas ≤ 1,5 px → a nuvem entra como GABARITO DE MEDIDA.**

**Três consequências.** Cai a hipótese de textura repetitiva — o conjunto de
telhado reconstruiu com 42 mil pontos. Inverte-se a conclusão sobre focal: as
rodadas que fecharam partiram de 3.225,6 e a BA convergiu sozinha para ≈2.511;
declarar 1792 não ajudou. E a `sw_1792` não falhou — **foi morta em andamento**,
com 27 imagens e subindo, enquanto outro mapper rodava em paralelo.

**DELTA, e é o que mais importa aqui:** eu declarei seis fracassos sem abrir um
único arquivo de modelo. **Ler a pasta não é ler o dado.** Antes de dizer que
algo quebrou, abrir o arquivo.

### D073 · Erro de reprojeção baixo não quer dizer nuvem útil
**Ambiguidade:** `fazendinha` tem o melhor erro do lote (0,602 px) e trilha
dobrada (10,35 contra 5,67). Pela métrica, seria a melhor nuvem.

**Decisão: `montagem` é a nuvem que presta; `fazendinha` não entra como geometria.**
Olhei os quadros de origem antes de escolher. `fazendinha` (`0172_D`) é o evento
**à noite, com a arena tomada de gente**: o erro baixo e a trilha dobrada vêm de
multidão e luz darem feature demais. Ela reconstruiu um mar de pessoas.
`montagem` (`0053_D`) é **dia, montagem do evento** — prédio redondo poligonal com
telhado de quatro águas, galpões de telha metálica, pátio de saibro, mastro.

**Motivo de registrar:** é o mesmo erro do D072 pelo avesso. Lá eu confiei na
pasta sem ler o dado; aqui, quase confiei no número sem ver o conteúdo. **Métrica
boa medindo a coisa errada continua sendo a coisa errada.**

### D074 · A configuração de render saiu da conversa e virou arquivo
**Ambiguidade:** a configuração de Cycles dele só existia em conversa. Um contexto
novo às 4h da manhã não a tem, e a tentação é inventar preset.

**Decisão:** `data/render-config.json`, com a ordem dele literal — **adaptativa
mín 10 / máx 50, denoise OptiX, não inventar configuração de Cycles**. Junto, o
que foi medido: ordem de sacrifício da VRAM, armadilha 34, a armadilha do
`get_devices()` e o custo real.

**Medido em 16/08 02:30**, em `out/cena-revisar.blend`, câmera `CAM_P01`:
**7,5 s a 960×540 / 64 samples**, 659.302 bytes, em
`NVIDIA GeForce RTX 4060 [OPTIX]`. Render é **barato** nesta cena — cabe muito
mais ciclo de comparação contra a foto real do que o plano supunha.

Confirmado de passagem: a cena tem **22 marcadores de timeline**, então a
armadilha 34 é real e todo script de render limpa `timeline_markers` na sessão.

### D075 · O verificador nasceu como agente separado
**Ambiguidade:** o contrato manda um `render3d-verificador` que ele lembrava ter
construído. Procurei nos três registros de agente e na árvore inteira, por nome e
por conteúdo: **não existe.** Só existe `render-agroshow.md`.

**Decisão:** criado `.claude/agents/render3d-verificador.md`, com a instrução fixa
dele. **Não** se usa o `render-agroshow` no papel — ele é quem planeja a cena, e
seria a mesma voz conferindo o próprio plano, que é o vício que o subagente
separado existe para cortar. A regra dura ficou escrita no agente: **reprova
sozinho, nunca aprova sozinho.**

`check_entrega.py`, `conferir_texturas.py` e `ENTREGA.md` também não existiam.

### D076 · O preset da casa venceu o teste comparativo. Sem excecao no Q1
**O que o adendo mandou:** um render com bounces cheios e ~200 samples lado a
lado com o preset de 50, teto de 10 minutos, porque preset calibrado para plano
aereo a 24 m pode matar o contraluz da golden hour -- e o portal e' plano baixo.

**Medido em 16/08, no Q1, 1600x1200, RTX 4060 OptiX:**

| configuracao | tempo total | so o render |
|---|---|---|
| preset da casa (adaptativa 10/50) | 13 s | 8 s |
| cheio (200 samples, todos os bounces em 32) | 18 s | 13 s |
| so o build da cena, sem render | 5 s | -- |

**Decisao: mantem o preset.** A folha `out/heroi/Q1-preset-x-cheio.jpg` poe os
dois lado a lado e nao ha diferenca visivel -- mesma sombra, mesmo contraluz,
mesmo nivel de ruido depois do OptiX. O cheio custa 1,6x o tempo de render para
entregar a mesma imagem.

**O tempo economizado vai para ciclo de comparacao contra a foto real, nunca
para um quarto quadro** -- e' a ordem escrita.

**O que este numero muda alem do Q1:** render aqui e' BARATO. O Q1 fechou em
sete iteracoes porque cada teste custava ~10 s. A conta antiga do filme (10,0
s/quadro a 2560x1440 com os tres passes, D065) continua valendo para a cena
cheia do parque; esta cena-heroi tem 2,19 M de triangulos e cabe folgada.

### D077 · O Q1 tem luminaria, barril e vaso — e isso NAO contraria estruturas.py
**Ambiguidade:** `estruturas.py:107` diz, no proprio docstring, que barril, vaso,
luminaria e mastro **nao entram**, e justifica: *"sao adereco de foto, e a camera
passa por aqui em 9 s no P02 e 6 s no P22"*.

**Precedente aplicado, nao decisao nova.** A premissa daquela exclusao e' camera
em MOVIMENTO. O Q1 e' quadro **PARADO e PROXIMO**, entao a premissa nao vale.
Manda o que esta escrito em `reference/PORTAL-referencia.md:33`: **"Reproduza
esta fachada."** A ressalva do audio (*"nos vamos dar um jeito dele, fazer mais
barato"*, mesma referencia, linha 36) governa **leitura de detalhe ambiguo**, nao
omissao do que esta visivel na foto.

`estruturas.py` **nao foi alterado** -- ele continua certo para o filme. O Q1 mora
em `scripts/heroi_portal.py`, que e' outro arquivo, para outro uso.

### D078 · As medidas do portal deixaram de ser estimativa
**O que havia:** `estruturas.py:174` carimbava `"medidas": "ESTIMADAS por
proporcao -- ver pendencia 4"`, tiradas da pessoa de ~1,70 m do quadro `1 (4)`.

**O que foi feito:** medicao em PIXEL na propria foto do cliente (1448x1086), com
ancora no **vao de passagem**, que precisa liberar caminhao -- 4,2 m de altura
livre da' **47,6 px/m** no plano da fachada.

A estimativa antiga sobreviveu bem a conferencia, e vale registrar porque diz que
o metodo de proporcao presta:

| medida | estimada (estruturas.py) | medida na foto | erro |
|---|---|---|---|
| cumeeira do corpo central | 9,00 m | **9,10 m** | 1,1% |
| largura total | 24,00 m | **26,05 m** | 7,9% |
| corpo central | 11,00 m | **12,29 m** | 10,5% |
| ala mais baixa | 4,20 m | **4,94 m** | 15% |

Tres coisas que a foto mostrou e a estimativa nao tinha: a empena tem **topo
achatado** (1,68 m), ha um **degrau** entre o ombro do corpo e a ala direita, e a
fachada e' **assimetrica** -- a ala direita e' o dobro da esquerda.

**A pendencia 4 continua aberta para o RESTO do recinto.** O que fechou foi o
portal, e so porque existe foto frontal dele.

### D079 · O agente verificador nao pode ser registrado no meio da sessao
**Bloqueio encontrado:** `.claude/agents/render3d-verificador.md` foi criado, mas
o registro de agentes e' lido na ABERTURA da sessao. Chamar o tipo novo devolve
`Agent type not found`.

**Decisao:** rodar a verificacao com `general-purpose` e a instrucao do
verificador **embutida no prompt, literal**. O que o contrato exige e' que a voz
seja OUTRA -- e e', porque o subagente nasce sem nada do que eu construi. O
arquivo fica em disco e vale a partir da proxima sessao.

**O que NAO se fez, e por que:** usar o `render-agroshow` no papel. Ele e' o
diretor tecnico que planeja a cena; seria a mesma voz conferindo o proprio plano,
que e' exatamente o vicio que o subagente separado existe para cortar.

### D080 · Quatro erros de geometria que so a folha lado a lado pegou
Nenhum destes deu erro na tela. Todos apareceram olhando o render **contra a foto
real**, e por isso ficam escritos:

1. **Booleano sobre face coincidente comeu o corpo central inteiro.** A empena em
   prisma e as caixas das alas se tocavam em face exata; solver EXACT sobre isso
   devolve lixo em silencio. Trocado por **montagem em partes**, e cada peca
   sobrepoe a vizinha em 6 cm.
2. **Sinal de rotacao invertido** no coroamento e na trelica do frontao: as
   tabuas apontavam para fora e para cima e viraram asas acima do telhado. E' a
   armadilha de Euler que a skill `blender-assembly` do proprio projeto nomeia --
   e que `estruturas.py:148` ja tinha registrado uma vez, na primeira versao da
   trelica.
3. **Sol apontado ao contrario.** Eu usava `(-d).to_track_quat("Z","Y")`, que poe
   a luz viajando NA DIRECAO do sol. Nao da erro: so deixa a fachada chapada e
   sem sombra. A convencao certa esta em `build_scene.py:2338` e foi calibrada na
   cena real.
4. **A cortina de arvores caiu em cima do palco** no Q2, quando o oval da arena
   encolheu -- ela era posicionada relativa ao centro do oval, e o centro se
   moveu. Agora e' cota absoluta atras do palco, com filtro que exclui qualquer
   arvore dentro da pegada.

**O que os quatro tem em comum:** silencio. E' o argumento a favor da regra que
manda **olhar o teste contra a foto real, nunca sozinho**.

### D081 · O verificador reprovou o Q1, e estava certo em sete de oito
**O que aconteceu:** o Q1 foi dado como pronto depois de sete iteracoes minhas
contra a foto. O verificador -- voz separada, que nao construiu nada -- abriu os
arquivos e **REPROVOU**, com numero em cada item.

O que ele achou, e que eu tinha olhado sete vezes sem ver:

| # | divergencia | medido por ele | eu tinha |
|---|---|---|---|
| 1 | chanfro da cumeeira | x 596..907 px = **6,53 m** | 1,73 m -- **3,8x estreito** |
| 2 | trelica do frontao | invisivel: 14 de 24 raios batiam no coroamento antes | "ja esta la" |
| 3 | letreiro L1 | **6,28 m** na foto | 9,90 m -- **58% largo** |
| 4 | enquadramento | fachada centrada em **+2,26 m**, camera em 0 | 1,1 a 1,6 m da ala direita CORTADOS |
| 5 | arvore no vao | copia deslocada -7,71 m x 2,4 = **-18,5 m** | uma arvore de 12 m plantada no portao |
| 6 | inclinacao das aguas | 22,5° / 25,2° | 19,1° / 19,3° |
| 7 | emolduramento | banzo e montantes ausentes | parede lisa do chao ao telhado |

**O que isso prova, e por que fica escrito:** eu tinha **olhado o quadro contra a
foto sete vezes** e nao vi nenhum dos sete. A folha lado a lado pegou os erros
GROSSOS (booleano, sinal de rotacao, sol invertido, arvore no palco) e passou
batido em todos os erros de MEDIDA. Sao dois instrumentos diferentes:

- **olhar lado a lado** pega o que esta grosseiramente errado;
- **medir em pixel os dois** pega o que esta 20% errado.

E 20% errado e' justamente o que faz uma imagem parecer *quase* o lugar. A regra
que sobra: **quadro-heroi nao fecha sem alguem MEDINDO, e esse alguem nao pode
ser quem construiu.**

**Item 5 merece nota a parte.** A arvore dentro do vao nao veio de erro meu de
posicao: a colecao do Poly Haven traz LOD0 e LOD1 sobrepostos **mais um objeto
`geometry_nodes` com origem deslocada -7,71 m**. Instanciar a colecao inteira
carrega o deslocamento junto, e a escala 2,4 o multiplica. **Asset de biblioteca
nao entra inteiro: entra filtrado**, e o filtro esta em
`heroi_portal.py:vegetacao`. Descartou 16 de 17 objetos.

Sete correcoes entraram e o quadro voltou para reconferencia. O item 8 dele
(colarinho dos mouroes, densidade da folhagem dos vasos) fica em aberto, e esta
declarado como tal.

### D082 · Os portões só valem rodados com o `.venv` DO PROJETO
**Como apareceu:** marquei o portão de textura como verde com base no relato do
agente que o construiu. Depois rodei eu mesmo, para nao aceitar relato como
prova -- e ele **quebrou no meio**:

```
ModuleNotFoundError: No module named 'cv2'
```

**O disco tem tres Pythons, e eles nao sao equivalentes:**

| interpretador | cv2 | numpy | PIL |
|---|---|---|---|
| `python` do PATH = venv do **Hermes** | **nao** | sim | sim |
| `.venv` **do projeto** | **sim** | sim | sim |
| Python do Blender 5.2 | nao | sim | -- |

**Decisao: portao se roda com `./.venv/Scripts/python.exe`, nunca com `python`.**
Rodado assim, `conferir_texturas.py` fecha **TUDO OK, exit 0**, com o albedo dos
seis materiais batendo a cor medida com erro de 0,01% a 0,37%.

**A armadilha, e ela e' pior que a falta do modulo:** eu li `EXIT=0` na primeira
tentativa, logo abaixo de um traceback. O `$?` era do `tail` do pipe, nao do
Python. **Portao que roda dentro de pipe nao reporta o proprio codigo de saida** —
e um portao que parece verde e' pior que um portao vermelho.

Vale a regra de casa: `pip install` no `python` do PATH contamina o agente do
Hermes. Quem precisa de biblioteca usa o venv do projeto.

### D083 · O verificador reprovou o Q2, e achou o que eu nao teria achado
Sete divergencias, e duas graves. Uma delas so aparece com um metodo que eu nao
tinha usado.

**1. A caixa cenica estava ~60% alta demais, e ele mediu SEM DEPENDER DE ESCALA.**
A camera da foto esta nivelada (deriva de 1 grau em 200 px, conferida na aresta
da pilastra). Com camera nivelada, **a razao entre alturas na mesma vertical e
exata e independe de horizonte e de altura de camera**:

| | real (coluna x=930) | modelo |
|---|---|---|
| chao -> topo do deck | 124 px | 1,80 m |
| chao -> face de baixo da cobertura | 503 px | 11,72 m |
| **razao** | **4,06** | **6,51** |

`BOCA` foi de **8,90 para 5,50 m**, e a cobertura desceu junto.
**Guardar o metodo:** razao na mesma vertical vale mais que qualquer estimativa
de escala quando a camera esta nivelada -- e da' para conferir se ela esta.

**2. A caixa nao FECHAVA no topo.** A parede subia com altura CONSTANTE (`BOCA`)
e a cobertura e' INCLINADA: sobrava **1,02 m de ceu aberto na frente e 2,10 m no
fundo**, em todo o perimetro, com nuvem visivel no render. Ele achou por
amostragem de pixel; nenhum log acusaria.

E' a **terceira vez na mesma noite** que a mesma familia de erro aparece: pilar e
telhado do pavilhao divergindo 16-26 cm, mourao encostando rente no portal, e
agora parede e cobertura. **Quando duas pecas se encontram, UMA funcao decide a
cota das duas.** A parede passou a ler de `_cota_cobertura(y)`.

**3. Os cartoes-fonte do asset viraram gravetos de pe na grama.** Mesmo bug do
Q1, e eu **nao tinha portado o filtro** para o `heroi_arena.py` -- consertei num
arquivo e deixei o outro. A colecao tem 17 objetos e so 1 e' a arvore; os outros
16 sao `branches_a..d`, `leaves_a..c` em LOD0 e LOD1, mais o `geometry_nodes`
deslocado. Instanciados 19 vezes.

**4. A trelica era PLANA e nao afinava.** O docstring prometia tres banzos e o
codigo montava dois: cinco trelicas planas lado a lado nao sao uma trelica
espacial. Virou seccao TRIANGULAR (dois banzos inferiores + um superior) e virou
MISULA -- 1,35 m onde nasce, 0,42 m na ponta livre, como a foto mostra.

**5 a 7 (cor).** Azul da base: saturacao subiu de 0,49 para **0,68** (foto 0,88);
a matiz ja batia. Grama: ver D084.

### D084 · A hora da golden hour decide a cor do chao — e nao fecha a conta sozinha
**O que o verificador mediu:** grama do 3D com **matiz 157 graus** (ciano) contra
**78 na foto**, e o gramado lendo como AGUA PARADA, com as arvores parecendo
submersas.

**Causa 1, e essa e' erro meu:** eu tinha inventado um verde
(`MAT_GRAMA = 0.055/0.145/0.030`) em vez de usar `MAT_TERRENO`, que **tem cor
medida**. Trocado. Matiz agora em **88,9 graus contra 87,5 na foto** -- fecha.

**Causa 2, e essa e' fisica:** com o sol a 10,1 graus, uma superficie HORIZONTAL
recebe `sin(10,1) = 0,17` do disco solar e quase todo o resto do CEU, que e'
azul. O chao inteiro dessaturas e esfria. Medido nas tres horas que o proprio
`data/luz.json` ja listava:

| hora | elevacao | grama S | grama V |
|---|---|---|---|
| **18:15** (contrato) | 10,1° | **0,05** | 0,36 |
| 17:30 | 19,8° | 0,08 | 0,37 |
| 17:00 | 26,4° | 0,11 | 0,38 |
| **foto, meio-dia** | ~60° | **0,42** | **0,70** |

**A honestidade do numero:** subir a hora ajuda (0,05 -> 0,11) e **nao fecha a
distancia**. Sobra gap por duas razoes declaradas: o albedo medido da grama e'
escuro (0,1286/0,1239/0,0369, que em sRGB e' V≈0,39 -- nenhuma luz faz uma
superficie dessas chegar a V=0,70 sem estourar), e o AgX Punchy dessatura de
proposito.

**Isto e' PROPOSTA, nao conserto**, e vai para `PROPOSTAS.md`: o LOOK LOCK de
18:15 e' escolha dele, esta declarada em `data/luz.json` desde 14/08, e **vale
para o filme inteiro**, nao so para este quadro -- o parque e' todo chao
horizontal. A folha com as tres horas lado a lado esta em
`out/heroi/Q2-hora.jpg`.

### D085 · O antes/depois nao e' comparacao pareada, e isso fica dito
O verificador conferiu a honestidade do arquivo e ela esta certa: o ANTES e'
`out/quadros-ia/P19_arena-de-rodeio/3d/meio.png`, de **15/08 10:44**, nao uma
versao piorada de proposito.

**Mas ele apontou o que eu nao tinha dito:** nao e' a mesma camera. O ANTES e' um
aereo 3/4 de toda a arena; o DEPOIS e' um close do palco do nivel do chao.
**Parte do ganho aparente vem da troca de plano, nao da geometria.**

O titulo da folha passou a dizer isso na cara -- *"(planos diferentes)"*. Vender
troca de enquadramento como ganho de modelagem seria exatamente o tipo de
imagem que este sistema existe para nao produzir.

### D086 · O frontao do portal e ASSIMETRICO, e foi isso a noite inteira
**A segunda reprovacao do Q1** trouxe uma observacao que o verificador marcou
como "nao afirmo, vale remedir": *a juncao corpo/ala direita le na foto em px
~1043-1058, e `CORPO_X1` esta em px 955.*

**Remedi em recorte ampliado 3x das duas juntas** e ele estava certo. O que eu
lia como ombro direito, em px 935, e' um **MONTANTE**. O ombro esta em **px 1037**.

| | eu lia | medido |
|---|---|---|
| ombro esquerdo | px 375 (y 460) | px 375 (y 460) — estava certo |
| ombro direito | px 955 | **px 1037 (y 450)** |
| topo achatado | px 596..907 | px 596..907 |

**A prova de que agora esta certo nao e' o ajuste — e' a CONSEQUENCIA.** Com os
quatro pontos medidos, as inclinacoes saem sozinhas:

| agua | modelo | medido na foto |
|---|---|---|
| esquerda | 21,3° | 22,3° |
| direita | 31,0° | 30,9° |

**Frontao simetrico nunca daria os dois numeros.** Eu tinha tentado fechar essa
conta duas vezes mexendo em `CUMEEIRA_MEIA` — primeiro 6° raso, depois 7°
ingreme, "trocando de sinal e mantendo o tamanho", como o verificador escreveu.
Era o modelo que estava errado, nao o parametro.

**A licao, e ela e' de metodo:** quando um ajuste erra para os dois lados com a
mesma magnitude, **o parametro nao e' o problema — a forma e'.** Parei de ajustar
e fui remedir a geometria.

### D087 · A camera mirava x=0, entao mover o olho nao movia o quadro
**O conserto de enquadramento da primeira rodada NAO funcionou, e o verificador
provou pelo pixel:** `montar_camera` fazia `alvo = Vector((0.0, 0.0, alvo_z))`.

Mover so o `desloc_x` **gira** a camera; o eixo optico continua cruzando o plano
da fachada em x=0, que cai no centro exato do quadro. Resultado medido: o ponto
x=0 projetava em px 800,0 de 1600 e px 1280,0 de 2560 — os centros exatos — e
**25% da ala direita continuava cortada**, com o vazio a esquerda intacto em
13,0% da largura, **nas duas entregas**.

O alvo passou a andar junto (`--alvo-x`, mesmo padrao que o `heroi_arena.py` ja
usava). **Guardar:** deslocar a camera sem deslocar o alvo nao reenquadra, so
guina.

**Efeito colateral que o verificador previu:** a Arvore 1 atravessava a ala
direita e subia 2,92 m acima da cumeeira — e **so nao aparecia porque o
enquadramento estava errado**. Consertar o quadro revelaria a arvore. Ela foi
afastada antes de o quadro abrir. Bug escondido por outro bug e' o pior tipo.

### D088 · A caixa alta da ArchivoNarrow e 0,55 do em, nao 0,72
Detalhe pequeno com causa medida: eu assumi `size = caps / 0.72`. O verificador
mediu a letra entregue em **0,72 m** contra os **0,84 m** da foto, e a segunda
linha em 0,31 contra 0,42. A familia entrega ~0,55 de caixa alta por em.
Corrigido para `caps / 0.55`. A LARGURA ja estava exata (6,28 m contra 6,30
medidos na foto, −0,3%), porque essa eu tinha travado por alvo.
