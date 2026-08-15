# DOUTRINA DE RENDER 3D — Sull Produções

> Documento de referência para agente de render.
> Escopo: Blender (Cycles) + integração com filmagem real (Sony A7III) + entrega para vídeo.
> Hardware de referência: Xeon E5-2680 v4 · 32GB RAM · RTX 4060 8GB VRAM · Windows.

**Como ler os marcadores de confiança:**
- `[Certo]` — evidência forte, regra técnica verificável.
- `[Provável]` — inferência forte, funciona na esmagadora maioria dos casos.
- `[Suposição]` — julgamento/opinião, preenchendo lacuna. Questionável.

---

## SUMÁRIO

1. [Princípios](#1-princípios)
2. [Modelagem](#2-modelagem)
3. [Posicionamento](#3-posicionamento)
4. [Materiais](#4-materiais)
5. [Iluminação](#5-iluminação)
6. [Câmera](#6-câmera)
7. [Render e output](#7-render-e-output)
8. [Pós-produção](#8-pós-produção)
9. [Decals, logos e letras (PNG)](#9-decals-logos-e-letras-png)
10. [Impressão física](#10-impressão-física-não-render)
11. [Integração com filmagem real](#11-integração-com-filmagem-real)
12. [Gestão de VRAM — RTX 4060 8GB](#12-gestão-de-vram--rtx-4060-8gb)
13. [Produção sob prazo curto](#13-produção-sob-prazo-curto)
14. [Checklist pré-render](#14-checklist-pré-render)
15. [Regras de ouro](#15-regras-de-ouro)

---

## 1. PRINCÍPIOS

### 1.1 As três camadas de qualidade

`[Suposição]` A maioria das discussões sobre "render bom" mistura problemas de camadas diferentes.

**Camada 1 — Plausibilidade física.** É o piso, não o teto. O Cycles já é fisicamente correto por construção: se não brigar com ele, a luz se comporta certo sozinha. Quase todo erro nessa camada é o artista *quebrando* a física — albedo fora da faixa real, metallic em 0.5, textura de roughness marcada como sRGB. Qualidade aqui não é o que se adiciona, é o que se para de estragar.

**Camada 2 — Plausibilidade fotográfica.** A diferença entre "parece real" e "parece uma foto" — são coisas distintas. O mundo real é fisicamente correto e mesmo assim uma foto dele tem limite de sensor, rolloff de highlight, lente específica, exposição escolhida. Render sem essa camada tem aparência de "correto e morto". É por isso que gerenciamento de cor (AgX) muda mais o resultado do que 200 horas de shader.

**Camada 3 — Intenção.** Separa portfólio de exercício. Um render de alto padrão comunica que *alguém decidiu* aquele enquadramento, aquela hora do dia, aquele objeto fora do lugar. Existe hierarquia: um assunto, um caminho de leitura, silêncio nas áreas que não importam. Render sem intenção vira catálogo de assets bem iluminados.

### 1.2 Convicções operacionais

`[Provável]` **Realismo é medido pelo elo mais fraco, não pela média.** O cérebro não faz média de qualidade — procura o erro. Um material de plástico no fundo destrói uma cena com 40 materiais impecáveis. Distribuir esforço igualmente é estratégia ruim; melhor é eliminar o pior elemento, repetidamente.

`[Certo]` **Imperfeição só funciona quando é causal.** Ruído aleatório não vira realismo. Poeira acumula em superfície horizontal voltada pra cima. Desgaste aparece onde a mão encosta e onde há atrito. Se a sujeira não responde "por que está aqui", lê como overlay e *piora* a imagem.

`[Suposição]` **Render de qualidade para vídeo é render que sobrevive ao pipeline.** Precisa aguentar grade no Resolve, compositing com chapa real, e compressão do Instagram. Render que só é bonito em PNG a 100% não serve. Isso muda decisões práticas: EXR com AOVs, exposição com headroom, nunca queimar grade no render.

### 1.3 Princípio de modelagem

`[Suposição]` **A malha precisa aguentar o que vai ser feito com ela depois.** Não existe "topologia boa" no abstrato. Um n-gon numa parede plana que nunca vai subdividir nem deformar é irrelevante. O mesmo n-gon num ombro que vai animar é defeito grave. Quase toda regra de modelagem que circula como dogma é regra condicional que perdeu a condição no caminho.

Perguntas antes de cada decisão: **vai subdividir? vai deformar? vai aparecer em close? vai ser instanciado? vai receber boolean?** A resposta define o que é erro.

### 1.4 Princípios de posicionamento

`[Provável]` **Contato é a coisa mais importante da cena.** O ponto onde o objeto encosta no chão é onde o olho decide se aquilo existe. Objeto flutuando ou afundando 2mm mata o realismo mesmo com o resto perfeito — destrói a sombra de contato, o sinal mais forte de peso e ancoragem que temos.

`[Certo]` **Posição não é onde o objeto está, é onde ele está em relação à câmera.** Uma cena pode estar impecável em vista perspectiva e desmontar na câmera, porque a projeção 2D cria adjacências que não existem no espaço 3D. Composição acontece na projeção, não no espaço.

`[Provável]` **Grid é o inimigo.** O Blender abre com tudo em 0,0,0 e rotação 0 — a posição mais improvável do universo real. Nada está perfeitamente alinhado ao eixo, equidistante e centralizado. Posicionamento de alto padrão é, em boa parte, sair do grid **com intenção**, não aleatoriamente.

### 1.5 Princípio de decals e marca

`[Certo]` **O canal alpha é onde mora o erro invisível.** Um PNG "com transparência" pode estar tecnicamente transparente e carregar informação errada nos pixels de borda. Não se vê no Photoshop nem no explorer — só aparece como halo no render.

`[Provável]` **Logo não é decalque, é impressão sobre um material.** Impressão em lona muda o comportamento óptico da superfície: roughness diferente do tecido cru e — o detalhe que mais vende — a lona é translúcida.

`[Certo]` **Cor de marca não sobrevive ao AgX por acidente.** Digita-se o hex da marca, o Blender converte pra linear, o AgX aplica rolloff e dessatura. O que sai **não é** o hex do manual. Não é bug, é o transform funcionando. Precisa de método, não de sorte.

### 1.6 Princípio de prazo

`[Provável]` **O custo não é qualidade, é retrabalho.** Não se perde por fazer coisa feia — perde-se por refazer. Avalie toda decisão por: *se isso mudar no último dia, quanto custa?*

`[Provável]` **Reversibilidade vale mais que acabamento.** O que importa no fim não é o quanto está bonito, é o quanto ainda dá pra mexer sem re-renderizar.

---

## 2. MODELAGEM

### 2.1 Antes de tocar na malha

- `[Certo]` **Não modelar sem referência dimensional.** Modelar "de olho" e corrigir escala depois quebra bevel width, radius de subsurface, DOF da câmera e física. Comece com `Scene Properties → Units → Metric, Unit Scale 1.0`.
- `[Certo]` **Não começar pelo detalhe.** Ordem: **blocking (proporção) → forma secundária → chanfro/detalhe**. Chanfrar antes da proporção fechar é retrabalho garantido.
- `[Provável]` **Não importar asset de biblioteca sem checar poly count e escala.** Quixel/BlenderKit frequentemente entregam milhões de tris e escala em centímetros.

### 2.2 Escala e transformações

- `[Certo]` **Não escalar em Object Mode sem `Ctrl+A → Scale`.** Escala não aplicada quebra Bevel, Solidify, normal maps, física e boolean — e o sintoma nunca aparece onde está a causa. Confira no N-panel: Scale deve estar `1,1,1`.
- `[Certo]` **Não deixar escala negativa** (resultado de mirror por escala -1). Inverte normais silenciosamente.
- `[Provável]` **Não deixar a origin no centro do mundo** em objeto que vai animar ou instanciar. Origin no ponto de rotação lógico: base do móvel, eixo da dobradiça, ponto de contato.

### 2.3 Topologia — onde importa e onde não

- `[Certo]` **Não tratar n-gon como pecado universal.** N-gon é problema em três casos: superfície que vai receber Subdivision Surface, superfície que vai deformar, superfície curva. Em face plana estática é inofensivo.
- `[Certo]` **Não deixar polos** (vértices com 3 ou 5+ arestas) **em área curva e visível.** É onde o subsurf faz pinching. Empurre polos para áreas planas ou escondidas.
- `[Provável]` **Não modelar densidade uniforme.** Densidade deve seguir **curvatura**, não estética. Face plana com 400 quads é desperdício de VRAM; curva sutil com 6 quads facetiza.
- `[Certo]` **Não ignorar direção de edge loop se vai deformar.** Loops perpendiculares ao eixo de dobra.
- `[Provável]` **Não usar Remesh como solução universal.** Resolve sculpt e volume, destrói edge flow de hard surface.

### 2.4 Geometria suja

- `[Certo]` **Não fechar o modelo sem rodar esta checagem:**
  - `M → Merge by Distance` — vértices duplicados. Threshold baixo, senão colapsa detalhe legítimo.
  - `Select → All by Trait → Interior Faces` — faces internas de extrude acidental.
  - `Select → All by Trait → Non Manifold` — obrigatório antes de boolean, solidify ou displacement.
- `[Certo]` **Não deixar faces coplanares sobrepostas.** Em still passa; em animação vira z-fighting piscando.

### 2.5 Normais

- `[Certo]` **Não confiar no olho.** Ligue `Overlay → Face Orientation` (azul = certo, vermelho = invertido) e rode `Shift+N`. Normal invertida quebra boolean, sombra e refração — e é invisível em Solid view.
- `[Certo]` **Não aplicar Shade Smooth puro em hard surface.** Use **Shade Auto Smooth** (4.1+, é o modificador Smooth by Angle).
- `[Provável]` **Não deixar Custom Split Normals de import CAD brigando com Bevel.** Se o bevel sair sujo: `Object Data → Geometry Data → Clear Custom Split Normals Data`.

### 2.6 Espessura

- `[Certo]` **Não modelar sólido com espessura zero.** Vidro, chapa metálica, parede, tampo de mesa precisam de espessura real — refração, cáustica e sombra dependem disso. Vidro single-sided se comporta errado no Cycles.
- `[Provável]` Solidify resolve, mas **cheque normais antes**, senão a espessura sai pra dentro.

### 2.7 Hard surface e ordem dos modificadores

**Ordem canônica:**
```
Mirror → Boolean → Bevel → Weighted Normal → Subdivision → (Triangulate só na exportação)
```

- `[Certo]` **Não colocar Bevel antes de Mirror** — dobra o chanfro na costura central.
- `[Certo]` **Não colocar Subsurf antes de Bevel** — explode a malha.
- `[Certo]` **Weighted Normal não funciona sem Shade Smooth + Auto Smooth ativos.** É a razão nº1 de "o modificador não faz nada".
- `[Provável]` **Não usar Bevel com Limit Method = Angle em malha complexa.** Use **Bevel Weight** e controle aresta por aresta.
- `[Provável]` **Bevel em unidades reais: 1–3mm.** 2 segments cobre a maioria; 3+ só em close real.
- `[Certo]` **Não deixar aresta viva.** Não existe canto com raio zero no mundo real — sem chanfro a aresta não pega highlight e o olho lê "CG" antes de qualquer outra coisa. **É o erro nº1 de todos.**

### 2.8 Booleans

- `[Certo]` **Não aplicar boolean em malha suja.** Exige manifold, normais corretas e sem doubles — nessa ordem.
- `[Certo]` **Não combinar Boolean + Subsurf sem retopologia.** Boolean gera n-gons e polos exatamente onde o subsurf mais sofre. Para superfície lisa em hard surface o caminho é **Boolean + Bevel + Weighted Normal, sem subsurf**.
- `[Provável]` **Não aplicar o boolean cedo.** Mantenha o cutter vivo em collection escondida — cliente muda de ideia.

### 2.9 Detalhe e economia

- `[Certo]` **Não modelar detalhe que normal/bump map resolve.** Geometria serve para **silhueta** e para o que pega highlight na borda. Parafuso a 3m da câmera é textura.
- `[Certo]` **Não modelar interior de objeto fechado**, nem face que encosta na parede.
- `[Certo]` **Não duplicar com `Shift+D` o que pode ser `Alt+D`** (linked duplicate) ou Collection Instance. Impacto direto e imediato na VRAM.
- `[Provável]` **Não deixar instâncias idênticas visíveis.** Varie rotação, escala e material em ±5%, senão o olho pega o padrão.

### 2.10 UV

- `[Provável]` **Não confiar em Generated/Box mapping para tudo.** Funciona em madeira genérica, quebra em qualquer textura com direção, logo ou desgaste posicionado.
- `[Certo]` **Não deixar texel density inconsistente entre objetos.** Grão de textura em escalas diferentes na mesma cena lê como erro mesmo que o observador não saiba nomear. Cheque com checker map.
- `[Provável]` **Não colocar seam em área central e visível.** Jogue para trás, para baixo, para dentro de canto.

### 2.11 Organização

- `[Certo]` **Não deixar `Cube.001`, `Cube.002`.** Nomeie. **Cryptomatte usa esses nomes** — um nome errado custa uma re-renderização no dia em que precisar isolar o objeto hero.
- `[Provável]` **Collections por função:** `SET`, `PROPS`, `HERO`, `LIGHTS`, `CAM`. Facilita Holdout, Indirect Only e render em passes.

---

## 3. POSICIONAMENTO

### 3.1 Contato e assentamento

- `[Certo]` **Não deixar objeto flutuando ou afundando.** Cheque em ortográfica lateral (`Numpad 1` / `Numpad 3`) com zoom real, não de olho na perspectiva.
- `[Certo]` **Não posicionar à mão em superfície irregular.** Use **Snap (`Shift+Tab`)** com `Snap To: Face`, `Snap With: Closest`, **`Align Rotation to Target`** e `Project Individual Elements` — assenta e alinha à normal de uma vez.
- `[Provável]` **Não deixar origin no centro geométrico** em objeto que vai ao chão. **Origin na base** (`Shift+S → Cursor to Selected` na face inferior → `Set Origin to 3D Cursor`) transforma posicionamento em operação de um clique.
- `[Provável]` **Não modelar assentamento de tecido à mão.** Almofada, manta, toalha, tapete amassado: **cloth sim + Apply** é mais rápido e mais crível do que esculpir dobra.
- `[Suposição]` **Não espalhar props "naturalmente" à mão.** **Rigid Body + deixar cair 30 frames + Apply Visual Transform** dá empilhamento e rotação que a mão não inventa.

### 3.2 Interpenetração e distância

- `[Certo]` **Não deixar geometria atravessando outra.** Cadeira dentro da mesa, tapete dentro do piso, quadro dentro da parede. Passa despercebido no viewport e aparece no render final.
- `[Certo]` **Não deixar faces coplanares encostadas** — quadro exatamente na parede, adesivo exatamente no vidro. Z-fighting. Afaste 1–2mm reais.
- `[Provável]` **Não ignorar distâncias funcionais em interior.** Cadeira a ~30cm da mesa, sofá a ~40cm da mesa de centro, circulação de ~70–90cm. Espaçamento errado lê como "showroom" sem que se saiba por quê.

### 3.3 Rotação e o grid

- `[Certo]` **Não deixar tudo em rotação 0°.** Livro, copo, controle, chinelo, cadeira — cada um tem ângulo de uso. 3° a 15° resolve, sem exagero.
- `[Certo]` **Não deixar espaçamento regular em série** (livros, cadeiras, luminárias pendentes). Ritmo perfeito é sinal de máquina.
- `[Provável]` **Não empilhar com alinhamento perfeito de aresta.** Pilha real tem deriva.
- `[Provável]` **Não usar Array modifier em elemento visível sem quebrar o padrão depois.** Array é ótimo para estrutura (ripado, brise, escada), péssimo para prop.

### 3.4 Composição — o que só aparece na câmera

- `[Certo]` **Não compor em vista perspectiva.** Componha **dentro da câmera** (`Numpad 0` + `Lock Camera to View`), sempre. Ligue **Passepartout em 1.0** para o fora-de-quadro escurecer de vez e parar de enganar.
- `[Certo]` **Não deixar tangências** — silhuetas que apenas se tocam ou quase se tocam. Quina de mesa encostando no batente, luminária tocando a linha do teto, vaso nascendo do encosto do sofá. Ou separa claramente, ou sobrepõe claramente: o "quase" é o que lê como erro.
- `[Certo]` **Não deixar objeto escuro na frente de fundo escuro sem separação de valor.** Silhueta precisa de contraste tonal, não só de espaço.
- `[Provável]` **Não deixar tudo no mesmo plano de profundidade.** Precisa de **primeiro plano, meio e fundo**. Um elemento em foreground (mesmo desfocado, mesmo parcialmente cortado) faz mais pela profundidade do que qualquer ajuste de luz.
- `[Provável]` **Não centralizar o assunto por default**, nem aplicar regra dos terços mecanicamente. Ligue `Camera → Viewport Display → Composition Guides` para conferir, mas a decisão é de hierarquia: um assunto dominante, o resto subordinado.
- `[Provável]` **Não encher os cantos.** Área de descanso não é desperdício — é o respiro do assunto.
- `[Provável]` **Não fazer asset dump.** Cada objeto responde: "quem mora/trabalha aqui e o que acabou de acontecer?"
- `[Certo]` **Não deixar ambiente estéril e alinhado ao grid.** Falta entropia: dobra no tecido, livro torto, copo fora do centro, marca de uso. Perfeição é o que trai.

### 3.5 Hierarquia e organização

- `[Certo]` **Não posicionar objeto de conjunto sem parentear** (`Ctrl+P → Object, Keep Transform`). Reposicionar o conjunto depois vira pesadelo se cada peça está solta.
- `[Provável]` **Não usar Empty como pivot só quando o problema aparece.** Empty na origem lógica (centro da mesa, eixo da porta) desde o começo economiza horas.
- `[Provável]` **Não aplicar rotação de objeto que ainda vai ser reposicionado.** Rotação aplicada some com a referência de "quanto eu já girei".

---

## 4. MATERIAIS

### 4.1 Fundamentos

- `[Certo]` **Não usar albedo em extremos.** Branco puro (255) e preto puro (0) não existem. Mantenha entre ~30 e ~240 em sRGB. Parede branca real fica em 220–235.
- `[Certo]` **Não usar Metallic intermediário.** É binário: 0 ou 1. Metal oxidado se resolve com **máscara** entre dois valores, não com 0.5.
- `[Certo]` **Não deixar Roughness como valor único.** Um valor no slider = plástico. No mínimo um `Noise Texture` com `Color Ramp` apertado em faixa curta (ex: 0.25–0.35). Idealmente mapa: impressão digital em vidro, poeira em superfície fosca, desgaste onde a mão encosta.
- `[Certo]` **Não mexer no Specular IOR Level sem motivo.** O default 0.5 equivale a IOR 1.45 — correto para quase todo dielétrico.

### 4.2 Erros de nó e configuração

- `[Certo]` **Não conectar textura sem checar Color Space.**
  - `Base Color` → **sRGB**
  - `Roughness`, `Metallic`, `Normal`, `Displacement`, `AO` → **Non-Color**

  É o erro mais comum e mais silencioso do Blender.
- `[Certo]` **Não empilhar Bump e Normal Map soltos.** Ordem: `Normal Map → entrada Normal do Bump → entrada Normal do Principled`.
- `[Provável]` **Não usar Subsurface sem ajustar o Radius à escala da cena.** Os defaults estão em metros; num objeto de 3cm o material vira translúcido total.
- `[Provável]` **Não deixar tiling visível nem escala de textura igual para tudo.** Madeira de piso e madeira de móvel não têm a mesma densidade de grão.

---

## 5. ILUMINAÇÃO

### 5.1 Estrutura de luz

- `[Certo]` **Não usar fill light demais.** Preencher toda sombra mata contraste e hierarquia. **Uma fonte dominante + rebatimento sutil** > seis luzes equilibradas.
- `[Certo]` **Não colocar a luz principal atrás da câmera.** Achata tudo. Fonte fora de eixo, **entre 30° e 60°** em relação ao eixo da câmera, é o que dá volume.
- `[Certo]` **Não deixar todas as luzes na mesma temperatura.** Use o nó **Blackbody**: janela ~6500K, luminária quente ~2700–3200K. Separação de temperatura faz metade do trabalho de profundidade. Tudo em 6500K é morto.
- `[Certo]` **Não somar World Strength alto com luzes práticas sem conferir.** Double lighting achata sombra — e você vai culpar o material.
- `[Certo]` **Não deixar luminária visível no quadro sem que a luz venha dela.** Prática visível e fonte real precisam coincidir em posição.

### 5.2 Parâmetros

- `[Certo]` **Não deixar Sun com Angle 0.** Real é **~0.526°**; céu levemente encoberto, 2–5°. Angle 0 dá sombra de laser e denuncia CG na hora.
- `[Certo]` **Não usar fonte minúscula esperando highlight bonito.** O tamanho do highlight **é** o tamanho da fonte — janela grande, softbox grande.
- `[Provável]` **Não posicionar Area Light rente à janela.** Recue um pouco pra fora e aumente o tamanho — o spread muda e a sombra fica mais crível.
- `[Provável]` **Não deixar HDRI na rotação padrão.** O ângulo do sol define a leitura da geometria — gire até as sombras trabalharem a favor da composição.
- `[Provável]` **Não usar HDRI de exterior como única fonte de interior sem ligar `Light Tree` e `Fast GI Approximation`.** O ruído fica impagável na 4060.

---

## 6. CÂMERA

- `[Certo]` **Não usar 16–24mm em ambiente.** Distorce e vira "foto de imobiliária". Arquitetura de alto padrão: **28–50mm**. Produto: **50–105mm**.
  - Sensor Size default do Blender = **36mm (full frame)**, então a focal corresponde direto à experiência com a A7III.
- `[Certo]` **Não deixar verticais tortas.** Linhas verticais paralelas. Câmera nivelada em Y; para mostrar mais teto ou chão use **`Shift Y`**, nunca tilt. Rotação X em exatamente 90° + correção por Shift = perspectiva de dois pontos, padrão de arquitetura de alto padrão.
- `[Provável]` **Não errar a altura.** Olho humano em pé **~1,55–1,65m**; sentado ~1,10–1,20m. Abaixo vira ponto de vista de criança; acima, planta baixa.
- `[Provável]` **Não usar F-Stop 2.8 em interior.** Equivalente realista: **f/5.6–f/11**. DOF forte em ambiente lê como miniatura.
- `[Provável]` **Não colar a câmera na parede pra "caber tudo".** Se não cabe, o problema é a lente ou o enquadramento. Puxar a câmera atravessando a parede + esconder a parede em `Holdout` é gambiarra aceitável; **grande angular pra compensar, não**.
- `[Provável]` **Não posicionar câmera em ângulo diagonal genérico.** Ou **frontal e centrada** (um ponto, deliberada), ou **claramente de dois pontos**. O ângulo indeciso, uns 15° torto, é o que parece amador.
- `[Provável]` **Não deixar Clip Start em 0.1 em cena grande** — gera z-fighting. Ajuste ao tamanho real.
- `[Certo]` **Não esquecer de travar a câmera** depois de fechada (cadeado nos Transforms do N-panel).

---

## 7. RENDER E OUTPUT

### 7.1 Gerenciamento de cor

- `[Certo]` **Não deixar View Transform em Standard.** Use **AgX** (4.0+). Standard estoura highlight e achata tudo. Para look neutro destinado a grading: **AgX + Look "None"**. Isso muda mais o resultado do que qualquer trabalho de shader.

### 7.2 Samples e ruído

- `[Certo]` **Não compensar samples baixos com denoise agressivo.** Vira cera, perde microdetalhe e, em animação, gera flicker temporal. Prefira:
  - **Noise Threshold 0.01** com Max Samples alto (deixa o adaptive decidir)
  - Denoise **OpenImageDenoise** com passes **Albedo e Normal** ligados
- `[Provável]` **Não usar Clamp Indirect baixo pra matar fireflies.** Remove GI legítima e escurece a cena. Ataque a origem: tamanho da fonte, `Light Tree` ligado, `Blur Glossy ~1.0`.

### 7.3 Bounces e caustics

- `[Certo]` **Não manter Max Bounces no default em interior.** Total 12 / Diffuse 4 é pouco: **Diffuse para 8**, Transmission conforme a quantidade de vidros empilhados. Cena escura sem motivo aparente quase sempre é bounce insuficiente.
- `[Certo]` **Não esquecer de habilitar Caustics Reflective/Refractive** em cena com vidro ou joia. Vêm desligados por padrão e o vidro fica sem vida.

### 7.4 Formato de saída

- `[Certo]` **Não renderizar direto em PNG/JPEG/8-bit.** Saída em **OpenEXR MultiLayer, Half Float, codec DWAA**, com **Cryptomatte Object/Material** ligados **antes** do render — não dá pra recuperar depois.
- `[Certo]` **Ligue os AOVs que dão margem:** Cryptomatte, Z-Depth, AO, Mist, luz separada. Sem isso não há margem no Resolve/After.
- `[Certo]` **Não deixar `Film → Transparent` desligado** se o plano vai ser composto sobre chapa real.

### 7.5 Arquivo

- `[Certo]` **Não deixar textura solta no Downloads.** Pasta `//textures/` **relativa** ao `.blend`, ou `File → External Data → Pack Resources` antes de arquivar. Textura rosa no dia de re-render é 100% evitável.
- `[Certo]` **Não trabalhar sem versionar.** `Ctrl+Alt+S` incremental a cada bloco fechado.

---

## 8. PÓS-PRODUÇÃO

- `[Certo]` **Não usar denoiser agressivo.** (ver 7.2)
- `[Provável]` **Não usar bloom, glare, aberração cromática e vignette com mão pesada.** Se dá pra perceber o efeito, está forte demais.
- `[Certo]` **Não queimar grade dentro do Blender quando o Resolve está no pipeline.** Saia neutro em AgX, grade uma vez, no fim.
- `[Provável]` **Não usar volumétrico/god rays no render** se der pra resolver em pós. Custo desproporcional — saia com **Mist pass** e faça a atmosfera no Resolve.

---

## 9. DECALS, LOGOS E LETRAS (PNG)

Aplicação típica: logo/patrocinador em tenda, lona, banner, placa.

### 9.1 O arquivo

- `[Certo]` **Não exportar PNG-8.** Alpha de 1 bit (liga/desliga) → toda borda serrilha. Sempre **PNG-24/32** (8 bits por canal + alpha).
- `[Certo]` **Não montar a arte sobre fundo branco e depois "tirar o branco".** Deixa **franja branca** nos pixels semitransparentes. Trabalhe com transparência desde o começo.
- `[Certo]` **Não exportar com RGB zerado sob a área transparente.** Onde alpha = 0, o RGB precisa ter a **cor do logo estendida (edge bleed / dilate)**. Se estiver preto ali, o filtro bilinear do Blender puxa preto pra dentro e gera contorno escuro sutil em todo lugar.
- `[Certo]` **Não exportar sem margem.** Deixe alguns pixels transparentes ao redor. Bounding box justa + filtragem de textura = borda cortada e streak nas extremidades.
- `[Certo]` **Illustrator:** não usar o default de 72dpi. `Export As → PNG`, fundo transparente, **Anti-aliasing: Art Optimized**, resolução calculada (ver 9.2).
- `[Certo]` **After Effects:** não exportar em **Premultiplied** por hábito. `Output Module → Channels: RGB + Alpha`, `Color: Straight (Unmatted)`. O default do AE é premultiplied e é fonte constante de halo.
- `[Provável]` **Não incorporar perfil Adobe RGB / ProPhoto no PNG.** O Blender ignora o perfil e assume sRGB → desvio de cor silencioso. **Converta pra sRGB antes de exportar.**
- `[Provável]` **Não exportar em 16-bit sem motivo.** Para logo é peso de VRAM sem ganho.

### 9.2 Resolução — o cálculo que substitui o chute

- `[Certo]` **Não escolher 4K "por segurança".** Regra: **quantos pixels a letra ocupa no frame mais fechado × 1,5.** Se numa 1920 a lona preenche ~700px de largura, 1024–1500px já sobra. 4K só em close real.
- `[Provável]` **Não subir resolução pra resolver serrilha em plano distante.** Letra fina longe **cintila** (aliasing temporal) mesmo em 8K. Resolve engrossando o traço ou usando versão simplificada da marca no plano aberto.
- `[Suposição]` Com 8GB de VRAM, decal em 4K é gasto que não aparece na imagem e aparece no tempo de render.

### 9.3 Dentro do Blender

- `[Certo]` **Não deixar o Alpha Mode no automático sem conferir.** No datablock da imagem: PNG de Photoshop/Illustrator = **Straight**. Se aparecer halo, é aqui — causa nº1, não o arquivo.
- `[Certo]` **Não deixar `Extension: Repeat` num decal.** Vai ladrilhar o logo por toda a superfície. Use **Clip**.
- `[Certo]` **Não deixar `Interpolation: Closest`.** Linear no geral; **Cubic** se a arte for pequena e ampliada.
- `[Certo]` **Não usar a saída Color como máscara.** Para máscara use a **saída Alpha** (que não passa por color management), nunca o canal de cor em sRGB.
- `[Certo]` **Não encaixar o logo dentro da UV principal.** Ou **segunda UV dedicada ao decal**, ou plano separado com **Shrinkwrap**. Espremer o logo na UV do tecido destrói o texel density do material base.
- `[Certo]` **Não deixar o plano do decal coplanar** com a superfície. Z-fighting. Offset do Shrinkwrap em 1–3mm reais.
- `[Provável]` **Não usar plano flutuante quando dá pra misturar no material.** `Alpha do PNG → Fac de um Mix Shader` entre shader do tecido e shader da tinta é mais limpo, aceita translucidez e não tem offset pra dar errado.
- `[Certo]` **Não aplicar o decal antes da deformação.** Ordem: **UV → deformação (cloth, catenária, vento)**. Ao contrário, o logo fica plano numa superfície enrugada.

### 9.4 A física da impressão em lona

- `[Certo]` **Não dar ao logo o mesmo roughness do tecido.** Serigrafia/impressão digital é levemente mais lisa. Diferença de **0,1–0,15** já cria a leitura de "impresso", não de "pintado no mapa".
- `[Provável]` **Não esquecer a translucidez.** Lona com sol atrás mostra o logo em silhueta pelo verso. Em plano com contraluz é obrigatório — sem isso a tenda vira placa opaca.
- `[Provável]` **Não deixar o logo com relevo.** Impressão em lona não tem espessura perceptível. Bump no decal é erro de mão pesada.
- `[Certo]` **Não usar branco puro (255) no logo.** Mesma regra de albedo: teto em ~240. Branco 255 estoura e chapa a letra.

### 9.5 Cor de marca

- `[Certo]` **Não aprovar cor de marca olhando o render em AgX.** Ele **vai** dessaturar. Método: renderize referência com **View Transform: Standard** só pra conferir o hex, e compense a saturação no Base Color até bater na versão AgX.
- `[Provável]` **Não converter arte CMYK pra RGB sem checar o hex resultante.** Pantone → CMYK → RGB acumula desvio; amarelos e laranjas sofrem mais. **Peça o hex oficial ao cliente** em vez de extrair do PDF.
- `[Provável]` **Não usar Emission pra "salvar" a cor da marca.** Placa que emite luz sem fonte lê como errado. Compense no Base Color.

### 9.6 Pipeline

- `[Provável]` **Não nomear `logo.png`.** Nomeie por marca e versão — e nomeie o **objeto** também, porque é o nome do objeto que o **Cryptomatte** entrega no Resolve.
- `[Provável]` **Não achatar o decal no render se o patrocinador pode mudar.** Objeto separado + Cryptomatte = troca em pós, sem re-render.

---

## 10. IMPRESSÃO FÍSICA (não render)

Se o destino é a gráfica e não a imagem, **PNG é o formato errado**.

- `[Certo]` **Não entregar PNG pra gráfica.** Grande formato pede **PDF/X-4, AI ou EPS** vetorial.
- `[Certo]` **Não entregar em RGB.** PNG **não suporta CMYK** por definição do formato. Converta e feche em CMYK no perfil que a gráfica pedir.
- `[Certo]` **Não usar 300dpi em tamanho real.** Grande formato roda entre **72–150dpi no tamanho final**, ou **1:10 a 300dpi**. 300dpi numa lona de 3m gera arquivo inútil.
- `[Certo]` **Não entregar com fonte viva.** Converta em curvas.
- `[Provável]` **Não posicionar elemento crítico perto de costura, sanefa ou ponto de tensão da estrutura.** Margem de segurança generosa + sangria conforme a gráfica.

---

## 11. INTEGRAÇÃO COM FILMAGEM REAL

Contexto: composição de elemento CG sobre chapa da Sony A7III.

- `[Certo]` **Não modelar a luz do 3D primeiro.** Defina o **ângulo e a temperatura do sol da filmagem** e replique no Blender. Direção de luz divergente é o erro que nenhum grading conserta.
- `[Certo]` **Não estimar a câmera 3D.** Ela precisa **replicar a câmera real**: mesma altura de tripé, mesma focal, mesmo sensor (**36mm no Blender = full frame da A7III**).
- `[Certo]` **Não modelar sem a escala real do ambiente filmado.** Se o objeto 3D não tem dimensão correta, o parallax do tracking não fecha — e não existe correção em pós.
- `[Certo]` **Não posicionar o objeto 3D antes do plano de chão do tracking estar resolvido.** O ponto de contato é exatamente onde o erro de solve aparece.
- `[Provável]` **Não posicionar objeto sem shadow catcher no chão.** Sem sombra projetada na chapa, o objeto fica colado por cima, não dentro.
- `[Provável]` **Não colocar o objeto CG no centro exato do quadro em plano com movimento.** Elemento levemente descentrado tem parallax mais rico e denuncia menos o tracking.
- `[Provável]` **Não deixar geometria muito fina ou coplanar em plano com movimento de câmera.** Vira aliasing piscando que o denoiser não conserta.
- `[Provável]` **Não deixar topologia adaptativa** (Adaptive Subdiv, Remesh por frame) **em animação.** Topologia mudando frame a frame = flicker.
- `[Certo]` **Não queimar grade no Blender.** Saia neutro, grade uma vez no Resolve.

---

## 12. GESTÃO DE VRAM — RTX 4060 8GB

- `[Provável]` **Não texturizar tudo em 8K.** Padrão: **4K no hero, 2K no secundário, 1K no que está fora de foco.** Use `Simplify → Texture Limit` (viewport e render separados).
- `[Provável]` **Não ligar `Persistent Data` em cena pesada.** Acelera animação mas segura o BVH em VRAM — é o que causa o **fallback silencioso pra CPU** (render de 4min vira 40).
- `[Provável]` **Não deixar `Subsurf` com Viewport level = Render level.** Viewport 1, render 2.
- `[Provável]` **Não usar Adaptive Subdivision / microdisplacement por hábito.** Come VRAM de forma desproporcional; bump + normal resolve a maioria e não muda topologia por frame.
- `[Provável]` **Não jogar Subdivision Surface em tudo.** É o que tira o render da GPU sem aviso.
- `[Provável]` **Não deixar asset de background em resolução de hero.** Decimate ou LOD manual no que está fora de foco.
- `[Suposição]` **Não renderizar frame único gigante quando o destino é vídeo.** Renderize na resolução final de entrega e faça upscale no Resolve — ordem de grandeza mais barato.
- `[Certo]` **Não descobrir estouro de VRAM tarde.** Carregue a cena cheia cedo e confira.

---

## 13. PRODUÇÃO SOB PRAZO CURTO

Cenário de referência: **exposição/feira com tendas e ruas, entrega em 3 dias, artista sozinho, stills**.

### 13.1 Ideias que governam

`[Certo]` **Exposição é o assunto mais repetitivo que existe — e isso é sorte.** São talvez 8 assets únicos gerando 200 objetos: tenda 5×5, tenda 10×10, rua, poste, lixeira, grade, banner. Quem modela tenda por tenda perde o prazo no dia 1. Quem constrói 3 tendas bem-feitas e instancia com variação entrega tranquilo.

**Cronograma de referência:**
- **Dia 1** = planta + blocking + câmeras travadas + **aprovação do cliente**
- **Dia 2** = assets, materiais, luz, **render começa à noite**
- **Dia 3** = pós, ajuste, entrega **de manhã**

> Se a aprovação do layout não sair no fim do dia 1, o projeto já está atrasado.

### 13.2 Antes de abrir o Blender (primeiras 2 horas)

- `[Certo]` **Não começar sem planta baixa / mapa do evento.** DWG, PDF ou até print. Modelar de memória e descobrir no dia 2 que o palco é do outro lado é o erro mais caro possível.
- `[Certo]` **Não deixar o entregável vago.** Feche por escrito: **quantas imagens, quais ângulos, qual resolução, still ou vídeo.** "Uns renders da feira" é escopo infinito.
- `[Certo]` **Não prometer revisão de câmera.** Ofereça **3 câmeras fixas**, aprovadas no dia 1. Ângulo novo = escopo novo.
- `[Certo]` **Não deixar a lista de patrocinadores pra depois.** Peça agora, em vetor, com hex oficial. É o que sempre chega atrasado e sempre atrasa o render.
- `[Provável]` **Não aceitar sem saber as medidas padrão das tendas** (3×3, 5×5, 10×10). Errar isso invalida a planta inteira.

### 13.3 Escopo — o que NÃO vai ser modelado

- `[Certo]` **Não modelar antes de travar a câmera.** Em 3 dias, **a câmera define o que existe**. Fora do frustum não é feito.
- `[Certo]` **Não modelar tenda por tenda.** Uma de cada tipo → **Collection Instance** → varia rotação, escala ±3% e cor. `Alt+D` ou instância, nunca `Shift+D`.
- `[Certo]` **Não rodar cloth sim em cada lona.** Uma tenda com sim → `Apply` → vira asset. As outras herdam.
- `[Certo]` **Não modelar interior de tenda.** Se aparece, escurece e coloca uma silhueta. GI de 40 interiores estoura o tempo de render.
- `[Certo]` **Não esculpir terreno.** Plano + textura + leve displacement, se tanto. Feira é asfalto/grama batida — ninguém olha o chão.
- `[Certo]` **Não modelar pessoas, carros, árvores, tratores, mesas, cadeiras.** Biblioteca: PolyHaven, BlenderKit, Quixel. Orgulho custa caro no dia 3.
- `[Provável]` **Não colocar crowd 3D.** Com 8GB de VRAM isso derruba. Billboard/cutout ou pessoas compostas em pós.
- `[Certo]` **Não usar volumétrico / god rays.** Se quiser atmosfera: **Mist pass** + Resolve.
- `[Provável]` **Não usar Subdivision nem Adaptive Subdiv em nada.** Bevel resolve.

### 13.4 Técnica — onde o prazo morre silenciosamente

- `[Certo]` **Não descobrir o tempo de render no dia 3.** Na primeira noite, rode 1 frame na resolução e configuração finais. Esse número dita todas as decisões seguintes.
- `[Certo]` **Não descobrir estouro de VRAM tarde.** Fallback silencioso pra CPU transforma 6min em 60 — e só se percebe de manhã.
- `[Certo]` **Não renderizar direto em PNG.** EXR MultiLayer + Cryptomatte Object/Material ligados antes. É o seguro contra "muda a cor daquela tenda" no dia 3.
- `[Certo]` **Não achatar logo/patrocinador no material.** Objeto separado, nomeado, isolável por Cryptomatte.
- `[Certo]` **Não nomear `Cube.001`.** Se o Cryptomatte não dá nome legível, ele não salva ninguém.
- `[Provável]` **Não fazer arquivo monolítico.** Collections por função: `RUAS`, `TENDAS`, `PROPS`, `LOGOS`, `LIGHTS`, `CAM`.
- `[Provável]` **Não fazer golden hour em todas as imagens.** Sol baixo = sombra longa, mais bounce, mais ruído. **Uma hero em luz dourada, o resto em luz suave** — renderiza mais rápido e perdoa mais.

### 13.5 Cliente

- `[Certo]` **Não sumir por 3 dias.** **Blocking cinza no fim do dia 1**, com as câmeras. É o único momento barato pra ouvir "o palco não é aí".
- `[Certo]` **Não mandar WIP sem rotular.** Escreva "bloco de estudo, sem material nem luz", senão o cliente avalia como final.
- `[Provável]` **Não perguntar aberto** ("o que achou?"). Pergunte fechado: *"confirma esses 3 ângulos e este layout?"*. Pergunta aberta em prazo curto abre escopo.
- `[Certo]` **Não aceitar mudança de layout no dia 3 sem renegociar.** Fale a frase enquanto ainda dá: *"isso é possível, e move a entrega em X."*

### 13.6 Contingência

- `[Certo]` **Não deixar o render pra última noite.** Começa na **noite do dia 2**, deixando o dia 3 inteiro como margem.
- `[Certo]` **Não renderizar a fila sem conferir os primeiros frames.** 20 minutos de conferência salvam 8 horas.
- `[Provável]` **Não confiar numa máquina só.** Deixe conta de render em nuvem pronta (SheepIt, GarageFarm) **antes** de precisar.
- `[Certo]` **Não trabalhar sem versionar.** `Ctrl+Alt+S` incremental. Corrupção de `.blend` no dia 3 acaba com o projeto.
- `[Provável]` **Não deixar textura fora de `//textures/`.** Pack Resources antes de qualquer coisa.

### 13.7 Se for animação, e não still

- `[Provável]` **Não aceitar mais de 10–15 segundos.** Cada segundo = ~30 frames × tempo de frame. Faça a conta **antes** de dizer sim.
- `[Provável]` **Não fazer câmera livre.** Um movimento simples (dolly, orbital lento) renderiza previsível e esconde falha de asset.
- `[Certo]` **Não usar denoise agressivo** — flicker temporal. Ligue `Denoising Data` nos passes e denoise no compositing/Resolve.
- `[Certo]` **Não deixar nada com topologia adaptativa.** Malha mudando por frame = cintilação.
- `[Suposição]` **Feira inteira animada em 3 dias, sozinho, numa 4060, é escopo malcalibrado.** A conversa certa com o cliente é hoje, não no dia 3.

---

## 14. CHECKLIST PRÉ-RENDER

Rodar em ~2 minutos antes de mandar a fila.

**Geometria**
- [ ] `Ctrl+A → Scale` aplicado em tudo (N-panel = 1,1,1)
- [ ] `Overlay → Face Orientation` sem vermelho
- [ ] Merge by Distance rodado
- [ ] Non Manifold checado (se houve boolean/solidify)
- [ ] Nenhuma aresta viva — bevel 1–3mm em tudo

**Posicionamento**
- [ ] Contato conferido em ortográfica lateral (nada flutuando/afundando)
- [ ] Sem interpenetração
- [ ] Sem faces coplanares encostadas
- [ ] Nada em rotação 0°
- [ ] Nenhum espaçamento perfeitamente regular

**Composição (dentro da câmera, Passepartout 1.0)**
- [ ] Sem tangências de silhueta
- [ ] Foreground / meio / fundo presentes
- [ ] Separação tonal do assunto contra o fundo
- [ ] Verticais paralelas (Shift Y, não tilt)
- [ ] Altura de câmera ~1,55–1,65m
- [ ] Focal 28–50mm (ambiente) / 50–105mm (produto)
- [ ] Câmera travada (cadeado no N-panel)

**Materiais**
- [ ] Color Space: Non-Color em todos os mapas de dados
- [ ] Nenhum albedo em 0 ou 255
- [ ] Nenhum Metallic intermediário
- [ ] Roughness com variação (não valor único)

**Luz**
- [ ] Sun Angle ≠ 0
- [ ] Temperaturas de cor variadas (Blackbody)
- [ ] Luz principal fora do eixo da câmera (30–60°)
- [ ] Sem double lighting

**Render**
- [ ] View Transform = **AgX**
- [ ] Saída **EXR MultiLayer, Half, DWAA**
- [ ] **Cryptomatte Object + Material** ligados
- [ ] Denoise com passes Albedo/Normal
- [ ] Bounces: Diffuse ≥ 8 em interior
- [ ] Caustics ligadas (se há vidro)
- [ ] `Film → Transparent` se vai compor sobre chapa real
- [ ] VRAM conferida (rodou sem fallback pra CPU)
- [ ] Objetos nomeados (Cryptomatte legível)
- [ ] Texturas em `//textures/` ou packed

**Decals**
- [ ] Alpha Mode = **Straight**
- [ ] Extension = **Clip**
- [ ] Interpolation = Linear/Cubic
- [ ] Offset ≥ 1mm da superfície
- [ ] Cor de marca validada contra referência em **Standard**

---

## 15. REGRAS DE OURO

Se houver tempo para corrigir apenas quatro coisas em cada frente:

**Render em geral**
1. Bevel/chanfro em toda aresta
2. AgX no View Transform
3. Roughness com variação
4. Color Space Non-Color nos mapas de dados

**Modelagem**
1. Aplicar escala (`Ctrl+A`)
2. Rodar `Face Orientation` antes de fechar o modelo
3. Respeitar a ordem `Mirror → Boolean → Bevel → Weighted Normal`
4. Parar de modelar detalhe que a textura resolve

**Posicionamento**
1. Conferir contato em ortográfica antes de todo render
2. Compor sempre de dentro da câmera, Passepartout 1.0
3. Matar tangências de silhueta
4. Tirar tudo da rotação 0°

**Decals / PNG**
1. PNG-24 com straight alpha e edge bleed
2. Conferir Alpha Mode no Blender
3. Extension = Clip
4. Validar cor de marca contra referência em Standard

**Prazo curto**
1. Travar câmera antes de modelar
2. Aprovar blocking no dia 1
3. Instanciar tudo que se repete
4. Começar o render na noite do penúltimo dia, com Cryptomatte ligado

---

## OBSERVAÇÕES SOBRE ESTE DOCUMENTO

- `[Suposição]` As seções marcadas como Suposição são julgamento e podem ser refutadas por resultado prático. Priorize testar antes de adotar como regra.
- Números de versão de Blender citados: **4.0+** (AgX, Principled v2), **4.1+** (Shade Auto Smooth / Smooth by Angle).
- Recomendações de VRAM assumem **RTX 4060 8GB**. Em placa maior, os limites de textura e subdivisão sobem proporcionalmente.
- Este documento cobre **render fotorrealista**. Não cobre stylized, toon, motion graphics abstrato ou Eevee.
