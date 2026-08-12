# Caminho fotorrealista — projeto futuro

Este documento **não descreve a entrega de domingo**. A AGROSHOW 2026 sai como
mapa animado em 2.5D, e o caminho abaixo não cabe nesse prazo.

Guardo aqui porque o Parque de Exposições de Dois Vizinhos sedia mais de um
evento por ano, e um modelo 3D do recinto é um ativo que se paga na segunda
temporada.

---

## A tese

Terreno, topografia, taludes, vias, bosque, mata nativa, os 6 pavilhões, o
Recinto de Leilões e o Centro de Convivência **não mudam de um ano para o
outro**. Tendas, estandes, palco, camarotes, sinalização e marca mudam todo ano.

Separe as duas camadas desde o primeiro dia e o modelo vira produto: constrói-se
uma vez, revende-se a cada edição com troca da camada variável. O mesmo recinto
atende AGROSHOW e ExpoVizinhos.

Modelo comercial que decorre disso: cobre a construção da base uma vez, e depois
licença anual de atualização. Não entregue o arquivo-fonte no contrato de
projeto — ele é o ativo.

---

## As quatro regras do realismo

O vídeo de referência do cliente (EXPOJARA, Tapejara, feito em Lumion) falha em
quatro pontos, nesta ordem de gravidade. Atacar fora de ordem é gastar caro no
lugar errado.

**1. Gente.** É o que entrega maquete, sozinho, antes de tudo. Nunca as pessoas
nativas de Lumion/Twinmotion — use humanos fotoscaneados. Escala conferida
contra elemento de altura conhecida; vestuário compatível com feira
agropecuária do interior do PR; nunca a mesma pose duas vezes no mesmo quadro;
pés com contato e sombra de contato. Multidão como sistema de partículas com
variação de rotação e escala, nunca bloco clonado.

**2. Luz.** GI de verdade. Diurno com HDRI de céu real e orientação solar
batendo com latitude e horário. Noturno com volumetria real nos refletores — o
cone chapado é a assinatura do Lumion. Superfície iluminada sem bounce no
entorno lê como videogame.

**3. Materiais.** Sem tile visível. Grama com variação de altura, cor e
densidade, e desgaste nas rotas de circulação — onde passa gente, a grama morre.
Lona de tenda com translucidez (SSS) e sujeira nas dobras. Piso e brita com
deslocamento real, não normal map sozinho.

**4. Câmera.** Movimento perfeito é falso. Inércia, micro-instabilidade de drone
ou gimbal, motion blur real, imperfeição de lente discreta. Uma distância focal
por plano, e consistência com ela.

Resolver 1 e 2 já entrega a maior parte do salto. Trocar de motor de render sem
resolver as pessoas não muda nada.

---

## Ponto de partida da modelagem

Os dados já extraídos em `data/mapa_agroshow26.json` mostram que **os módulos se
repetem**: 39 estandes de 100 m² (10×10) e 35 de 25 m² (5×5). São 74 dos 134 em
dois assets.

Modele dois módulos e instancie, com variação dirigida de lona, sinalização e
conteúdo interno. Modelar um a um é desperdício e ainda dá resultado pior,
porque a variação sai aleatória em vez de composta.

**A planta não tem vetor.** Nem o PDF nem o DWG contêm geometria (ver
`docs/BRIEFING.md`). Para modelar com precisão, o caminho é retraçado guiado
pelo JSON somado a ortomosaico de voo de drone dedicado — grid nadir com 70–80%
de sobreposição e exposição travada, não voo cinematográfico.

---

## Fases

1. **Base** — terreno, topografia, taludes, vias, estacionamentos, bosque, mata,
   pavilhões, Recinto de Leilões, Centro de Convivência. Ativo permanente.
2. **Camada do evento** — estandes instanciados, tendas, palco, arena, camarotes,
   portal, sinalização, marca. Coleções próprias, sem dependência cruzada com a
   Fase 1.
3. **População e luz** — regras 1 e 2 acima.
4. **Render em passes** — nunca só beauty. Beauty, depth, cryptomatte (objeto e
   material) e motion vectors. Sem esses passes, refino vira re-render.
5. **Refino por IA** — por cima do render, nunca no lugar dele. A IA não conhece
   a planta, não mantém continuidade entre planos e não escreve texto confiável
   em português — e aqui o texto é o que vende. Placas, totens e logos são
   compostos com máscara de cryptomatte, nunca gerados.
6. **Pós e entrega** — edição, color, sound design, trilha, letreiros, e os dois
   arquivos finais.

Dirija o Blender por script (`bpy`) e versione. Pipeline que só existe na
memória de quem montou não sobrevive à segunda temporada — e o valor está na
segunda.

Antes de render longo, valide em baixa amostragem: escala humana, contato de
sombra, orientação solar, legibilidade das placas em 2:1. Erro de escala
descoberto depois de 40 horas de render é o desperdício clássico.
