# Os lugares do filme — posição e conteúdo

**AGROSHOW 2026 · Parque de Exposições de Dois Vizinhos, PR**
Escrito em 14/08/2026, depois da auditoria completa dos rótulos do mapa.

Este documento responde duas perguntas por lugar: **onde ele fica** e **o que
tem dentro dele**. A posição vem do mapa; o conteúdo vem do áudio do cliente
(`docs/brief-audios.md`), que é a régua — se ele descreveu, tem que aparecer.

Inventário em `data/locais.json` (142 locais), gerado por
`scripts/auditar_mapa.py`. Coordenadas em metros no mundo do Blender, origem no
centro da prancha, y para o norte.

---

## A camada vermelha é o roteiro do cliente

O mapa tem duas camadas de texto, e o PDF as separa pela cor:

| cor | spans | o que é |
|---|---|---|
| `#000000` | 706 | planta técnica do arquiteto |
| **`#ff3131`** | **36** | **o roteiro do cliente, desenhado por cima** |
| `#767676` | 8 | rosa dos ventos |
| `#0000ff` | 1 | SANEPAR |
| `#dcdcdc` | 1 | ANTENA |

Os 21 rótulos vermelhos são exatamente a ordem que ele ditou no áudio, já
posicionada no desenho. **O extrator antigo descartava essa camada inteira** —
ele só aceitava rótulo que estivesse numa lista branca escrita à mão, e nenhum
nome do roteiro estava nela. Era por isso que a Fazendinha, a Área de Show, os
Expositores Externos e a Exposição de Máquinas apareciam no projeto como
"posição não existe na planta".

---

## Os 21 lugares do roteiro

Ordem do percurso. `plano` é o plano da decupagem que cobre o lugar
(`docs/PLANOS.md`); `♦` marca os quatro diferenciais.

| # | Lugar | (x, y) m | plano | o que o áudio pede dentro |
|---|---|---|---|---|
| 00 | Estacionamento (norte) | 79,9 · 126,4 | P01 | Dois estacionamentos em frente ao parque. Ponto de vista de quem chega |
| 00b | Estacionamento (leste) | 120,6 · 66,7 | — | O segundo dos dois |
| 01 | **Portal de Entrada** | 68,3 · 89,2 | P02 · P22 | Conceito celeiro, versão econômica. Primeiro e último plano do filme |
| — | *frase de campanha* | 75,2 · 91,2 | P02 | *É daqui que sai o alimento que sustenta o mundo* — já escrita no mapa |
| 02 | Pavilhão 1 | 14,7 · 135,2 | P03 | Expositores: indústria, comércio e prestação de serviços |
| 03 | Praça de Alimentação Coberta | −51,4 · 128,9 | P04 | Mesas, cadeiras, guichês do pessoal vendendo comida e bebida, do lado da churrasqueira |
| 04 | Pavilhão 2 | −104,0 · 139,0 | P05 | Indústria, comércio e prestação de serviços |
| 05 ♦ | **Mercado do Produtor** | −165,2 · 132,9 | P06 | Na entrada do Pavilhão 3 |
| 06 | Agroindústrias | (Pavilhão 3) | P07 | Guichês dos expositores, primeira metade do pavilhão |
| 07 ♦ | **Café Colonial** | −158,0 · 137,0 | P08 | Fundos do Pavilhão 3, depois de uma divisão de meia parede de TS. De um lado a cozinha que atende o café |
| 07b | Cozinha Didática | −153,8 · 135,2 | P08 | Do outro lado da meia parede, com aula acontecendo |
| 08 | Praça de Alimentação Aberta | −202,3 · 77,0 | P09 | Embaixo do bosque. O percurso passa por dentro do bosque |
| 09 | Recinto de Leilões | −311,9 · −7,3 | P10 | **Leilão acontecendo.** Sai em frente à Sociedade Rural |
| 10 | Pavilhões de Animais | −327,6 · −49,4 | P11 | Seis pavilhões cobertos — ver a tabela abaixo |
| 11 | Pista de Julgamentos | −272,6 · −91,9 | P12 | Área de pasto verde |
| 12 | Expositores Externo (norte) | −233,3 · −53,1 | P13 | Toda a área de expositores externos |
| 12b | Expositores Externo (sul) | −220,2 · −85,5 | P13 | A segunda mancha — o sobrevoo vai de uma à outra |
| 13 ♦ | **Fazendinha** | −164,4 · −18,6 | P14 · P15 | Porteira bacana na entrada. Brinquedos infláveis, passeio a cavalo, pônei, apresentação de Border Collie com ovelhas |
| 14 | Exposição de Máquinas, Equipamentos e Veículos e Implementos | −108,5 · 75,5 | P16 | Primeiro anel de cima. Máquinas, equipamentos e implementos agrícolas |
| 15 | Veículos e Motos Náuticas | −34,2 · 58,4 | P17 | Depois das máquinas, na volta do mesmo anel |
| 16 | Área de Show | −94,0 · 41,5 | P18 | Segundo patamar descendo |
| 17 ♦ | **Arena de Rodeio** | −77,1 · 4,4 | P19 | Touro pulando. **Sem arquibancada** — só pista, camarotes dos dois lados, palco de frente |
| 18 | Palco | −62,2 · −20,9 | P20 | Artista cantando, público comemorando, se divertindo, bebendo, fazendo festa. Toda a área embaixo lotada |
| 19 | Espaço É CHURRASCO! | −278,9 · 4,2 | — | Não citado no áudio; está no mapa |

Fechamento, sobre o P21: *Aqui será um grande balcão de negócios*.

---

## Os seis pavilhões de animais, na ordem que ele ditou

A ordem física norte→sul do mapa bate exatamente com a ordem falada. Um
briefing anterior travou este bloco alegando conflito; o conflito não existe —
o briefing tinha lido os rótulos na ordem de extração do texto, não na espacial.

| # | Pavilhão | (x, y) m | área | o que o áudio pede |
|---|---|---|---|---|
| 1 | Gado Leite | −333,9 · −58,9 | 720 m² | Gado de leite |
| 2 | Núcleo Cara Branca | −326,6 · −80,8 | 720 m² | Hereford e Braford: **corpo vermelho, cabeça branca** |
| 3 | Gado Corte | −319,5 · −102,6 | 720 m² | "Diversas raças" — pode usar Nelore, o gado branco |
| 4 | Ovinos e Caprinos | −314,1 · −123,4 | 720 m² | — |
| 5 | Pequenos Animais | −305,0 · −146,3 | 720 m² | — |
| 6 | Equinos | −293,9 · −166,7 | 560 m² | Cavalos |

Perto deles, e citados na planta: **Mangueiras** (−305,5 · 43,6),
**Ordenhadeira** (−331,9 · −42,1), **Lavagem Animais** (−356,4 · −117,0),
**Julgamento Rústico** (−328,5 · 7,9) e a **Casa do Médico Veterinário**
(−253,4 · 34,6).

---

## O que a arena tem, e o que ela não tem

Confirmado por imagem no footage do próprio recinto
(`docs/MATERIAIS-referencia.md`), não só por ordem do cliente:

| elemento | (x, y) m | nota |
|---|---|---|
| Arena de Rodeio | −77,1 · 4,4 | Pista, sem arquibancada |
| Camarotes — Lado A | −30,5 · 9,2 | Deck de madeira elevado, gradil branco de tubo |
| Camarotes — Lado B | −107,7 · −22,9 | O outro lado |
| Palco | −62,2 · −20,9 | De frente para a arena |
| Palco After | −19,6 · 20,1 | — |
| Área de Show | −94,0 · 41,5 | Os anéis de talude, onde o público senta na grama |

**Não há arquibancada em nenhum quadro do recinto inteiro.** Em todos os
eventos filmados o público senta no talude gramado. A restrição do cliente não
é só uma ordem: é como o parque funciona.

Os **15 rótulos "Talude"** do mapa caem nas faixas de transição entre os
patamares, e os arcos concêntricos traçados em `data/vias.json` dão a forma
real da bacia — hoje o terreno usa anéis perfeitos com raio estimado.

---

## Os estandes, por categoria

`data/estandes.json`, gerado por `scripts/classificar_estandes.py`: 134
estandes com a categoria lida da cor com que a planta os pinta.

| categoria | estandes | centroide (x, y) m | confiança |
|---|---|---|---|
| Agricultura | 43 | −215,6 · −130,3 | roxo, inequívoco |
| Veículos e Motos Náuticas | 12 | −34,2 · 58,4 | azul, inequívoco |
| família laranja/rosa | 37 | — | **ambíguo** |
| sem preenchimento (série A) | 41 | — | círculos pequenos em volta da Praça |
| tom magenta, fora da legenda | 1 | — | é o estande de Apicultura |

**A ambiguidade é honesta e tem causa medida:** a legenda usa a mesma tinta
duas vezes em densidades diferentes — *Alimentação e Bebidas* é o mesmo rosa de
*Máquinas e Equipamentos*, e *Galpão do Produtor* é o mesmo laranja de
*Avicultura*. O matiz diz a família; separar dentro dela exigiria comparar
densidade de hachura entre a legenda e o estande, e as duas são desenhadas de
jeitos diferentes. Para a modelagem isso não atrapalha: todos são estande de
expositor. Para povoar com o produto certo, precisa do "sim" do cliente.

---

## O que continua em aberto

1. **Escala.** Os 0,5611 m/pt vêm dos 39 estandes de 100 m² da série C em
   fileira. Tentei conferir pelas 282 cotas em metros que o mapa carrega, e deu
   **inconclusivo** — a dispersão ficou larga demais (q1 0,357 / q3 0,557).
   Não confirma nem derruba. Continua valendo a pendência de uma medida real
   em campo.
2. **Alturas dos patamares** (0 → 3,5 → 7 → 10 m) seguem estimadas por
   proporção. A telemetria não resolve; falta um voo lateral rasante.
3. **Pista de tiro de laço** não tem rótulo no mapa. O áudio a usa como
   referência da Fazendinha, mas a Fazendinha tem posição própria no mapa, e
   foi essa que o Natan mandou usar.
4. **Portão da Fazendinha** ("faz uma porteira bacana") — o mapa não desenha.
   Vira modelagem por descrição.
5. Quatro rótulos **PORTAL** internos além do Portal de Entrada:
   (−171,1 · 109,5), (−230,7 · 95,9), (−217,2 · 20,6) e (48,5 · 88,3). O
   último é o pórtico atual, ao lado do Portal de Entrada.
