# Como o parque escreve — o vocabulário de letreiro medido no footage

**Procedência: registro.** Não é doutrina e não é gosto meu — é o que as imagens
extraídas mostram. Levantado em 15/08/2026, nona sessão, lendo as duas pastas que
o Natan indicou.

Prova em quadro: [`out/referencia-letreiros/como-o-parque-escreve.jpg`](../out/referencia-letreiros/como-o-parque-escreve.jpg)

## O que foi lido

| pasta | o que tem | o que serve |
|---|---|---|
| `E:\Projetos todos\Mapa - agroshow\Brutos Expo\agroshow extrator somente\extracao` | 17 clipes × 120 quadros — parque **vazio**, dia, chão e drone baixo | arquitetura, cor, letreiro fixo |
| `F:\Extração quadros expo 2025` | 152 pastas de quadros — evento **montado e acontecendo**, dia e noite | como o recinto se veste, público, palco |

**Aviso RETIRADO em 15/08/2026, por medida.** Esta seção dizia que as pastas
`DJI_20251126*` a `DJI_20251130*` mostravam outro recinto — "autódromo oval,
silos de grão, pavilhão moderno com coberturas verdes em cogumelo" — e que usar
aquilo seria errar de cidade. **Está errado, e o desmentido é o GPS do próprio
drone.**

As 71 pastas foram cruzadas com a coordenada do recinto
(−25,73144 / −53,07627) por `scripts/provar_recinto.py`: **60 delas, 2.440
quadros, têm GPS gravado e caem entre 24 m e 387 m do ponto de referência** —
dentro de um terreno de 808 × 454 m. **Nenhuma cai fora.** As 11 restantes
(330 quadros) são exports estabilizados que perderam o metadado, e mostram a
mesma feira, o mesmo horizonte e o mesmo dia das que têm GPS.

E as duas feições que levantaram a dúvida aparecem **dentro de voos com GPS
confirmado**: o **oval** está em `DJI_20251126155520_0054_D` (168 m) e os
**silos** em `DJI_20251129182345_0168_D` (336 m). Eles não são de outra cidade
— são o recinto e a cooperativa vizinha.

Provas: `data/recinto-gps.json`, `out/prova-recinto-gps.jpg`,
`out/prova-recinto-provados.jpg`, `out/prova-recinto-sem-gps.jpg`.
Decisão em `DECISOES.md` D061.

## Os seis modos de escrever que o parque usa

Nenhum deles é texto flutuando no ar. **Em todos, a letra mora numa superfície.**

**A. Portal — placa suspensa.** Duas colunas redondas pintadas de óxido, treliça
metálica com telha por cima, e uma **tábua curva pendurada por correntes** no vão.
Logo da Sociedade Rural à esquerda, nome em cursiva à direita, segunda linha menor
embaixo: *Pista de Laço / ~ Ivanir C. Pinzon*. É o letreiro mais bonito do recinto
e é exatamente "letra embutida no painel".

**B. Prédio — letra caixa no painel ACM.** No Recinto de Leilões: marquise com
faixa azul em cima, painel branco embaixo, e as letras **em relevo, azuis, caixa
alta, condensadas**, aplicadas no painel. O logo vem em letra-caixa também.
Duas linhas: nome do recinto grande, nome do patrono menor.

**C. Camarote — faixa contínua de lona.** O guarda-corpo redondo é fechado por uma
faixa branca com os logos dos patrocinadores repetidos em módulos. A escrita
acompanha a curva da estrutura.

**D. Pavilhão — placa aplicada na parede.** Chapa verde retangular parafusada na
parede vermelha, e bandeirolas verticais penduradas na tesoura do telhado.

**E. Evento montado — banner sobre a entrada.** Lona amarela esticada no vão de
entrada (*Vila Gastronômica*), mais totens verticais no chão e arcos infláveis
verdes nas passagens.

**F. Tenda — faixa na borda da cobertura.** A saia da tenda carrega Sicredi de um
lado, EXPO VIZINHOS 2025 do outro, e o *lockup* completo de patrocinadores no
rodapé — ACEDV/CDL, Sociedade Rural Vale do Iguaçu, Prefeitura, Sicredi, Paraná,
Itaipu, MBRF, Vizzari, DEZ.

## O que isso resolve

O defeito dos 9 letreiros fora do quadro nasce do modo `billboard`: texto solto no
espaço, dimensionado por altura, sem largura que o prenda. Painel tem **largura
declarada** — a linha quebra dentro dele, e o que a câmera precisa enquadrar deixa
de ser uma frase de comprimento imprevisível e passa a ser um objeto de tamanho
conhecido, que o portão de conferência mede antes do render.

## O que isto NÃO decide

Qual dos seis modos cada um dos 16 letreiros usa, e se a entrega é 16:9 nativo.
Isso é dele.
