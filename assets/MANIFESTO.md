# assets/ — o que entrou, de onde, e sob que licença

Verba zero: só entra CC0 ou equivalente.

Gerado por `python scripts/assets.py --manifesto` a partir de
`assets/_procedencia.json`. **Não edite à mão.**

Os binários não são versionados (ver `assets/.gitignore`) — este
manifesto é que vai para o git, e `scripts/assets.py` rebaixa tudo
a partir dele. Quem clonar o repositório roda o script e tem os
mesmos arquivos, conferidos por md5.

## Céu

| arquivo | asset | fonte | licença | autores | URL | md5 |
|---|---|---|---|---|---|---|
| `assets/hdri/belfast_sunset_puresky_4k.hdr` | Belfast Sunset (Pure Sky) | Poly Haven | CC0 | Dimitrios Savva, Greg Zaal, Jarod Guest | https://polyhaven.com/a/belfast_sunset_puresky | `52d2339c1606` |
| `assets/hdri/kloppenheim_06_puresky_4k.hdr` | Kloppenheim 06 (Pure Sky) | Poly Haven | CC0 | Greg Zaal, Jarod Guest | https://polyhaven.com/a/kloppenheim_06_puresky | `63e9826c43b9` |

## Texturas

| arquivo | asset | fonte | licença | autores | URL | md5 |
|---|---|---|---|---|---|---|
| `assets/textura/aerial_grass_rock_Rough_2k.jpg` | Aerial Grass Rock — Rough | Poly Haven | CC0 | Rob Tuytel | https://polyhaven.com/a/aerial_grass_rock | `8d181000237d` |
| `assets/textura/aerial_grass_rock_nor_gl_2k.jpg` | Aerial Grass Rock — nor_gl | Poly Haven | CC0 | Rob Tuytel | https://polyhaven.com/a/aerial_grass_rock | `0c5423ce3651` |
| `assets/textura/corrugated_iron_02_Rough_2k.jpg` | Corrugated Iron 02 — Rough | Poly Haven | CC0 | Jenelle van Heerden, Sergej Majboroda | https://polyhaven.com/a/corrugated_iron_02 | `cd1a30895816` |
| `assets/textura/corrugated_iron_02_nor_gl_2k.jpg` | Corrugated Iron 02 — nor_gl | Poly Haven | CC0 | Jenelle van Heerden, Sergej Majboroda | https://polyhaven.com/a/corrugated_iron_02 | `7ce1e415161d` |
| `assets/textura/dirt_aerial_03_Diffuse_2k.jpg` | Dirt Aerial 03 — Diffuse | Poly Haven | CC0 | Rob Tuytel | https://polyhaven.com/a/dirt_aerial_03 | `d67e26f08c08` |
| `assets/textura/dirt_aerial_03_Rough_2k.jpg` | Dirt Aerial 03 — Rough | Poly Haven | CC0 | Rob Tuytel | https://polyhaven.com/a/dirt_aerial_03 | `1afbf952422c` |
| `assets/textura/dirt_aerial_03_nor_gl_2k.jpg` | Dirt Aerial 03 — nor_gl | Poly Haven | CC0 | Rob Tuytel | https://polyhaven.com/a/dirt_aerial_03 | `cd63c161d011` |
| `assets/textura/gravel_road_Diffuse_2k.jpg` | Gravel Road — Diffuse | Poly Haven | CC0 | Amal Kumar | https://polyhaven.com/a/gravel_road | `5d024d27bc8f` |
| `assets/textura/gravel_road_Rough_2k.jpg` | Gravel Road — Rough | Poly Haven | CC0 | Amal Kumar | https://polyhaven.com/a/gravel_road | `bbd4f6c7c1b8` |
| `assets/textura/gravel_road_nor_gl_2k.jpg` | Gravel Road — nor_gl | Poly Haven | CC0 | Amal Kumar | https://polyhaven.com/a/gravel_road | `7c25211b3cf3` |

## Modelos 3D

| arquivo | asset | fonte | licença | autores | URL | md5 |
|---|---|---|---|---|---|---|
| `assets/modelo/plastic_monobloc_chair_01/plastic_monobloc_chair_01_1k.blend` | Plastic Monobloc Chair 01 | Poly Haven | CC0 | Kuutti Siitonen | https://polyhaven.com/a/plastic_monobloc_chair_01 | `c5c2ee7961ad` |
| `assets/modelo/wooden_picnic_table/wooden_picnic_table_1k.blend` | Wooden Picnic Table | Poly Haven | CC0 | Ulan Cabanilla | https://polyhaven.com/a/wooden_picnic_table | `09183939c50b` |
| `assets/modelo/wooden_table_02/wooden_table_02_1k.blend` | Wooden Table 02 | Poly Haven | CC0 | Serhii Khromov | https://polyhaven.com/a/wooden_table_02 | `929cb0272746` |

## Dado geográfico (relevo e cobertura do solo)

| arquivo | asset | fonte | licença | autores | URL | md5 |
|---|---|---|---|---|---|---|
| `assets/relevo/entorno_alturas.npy` | Relevo do entorno (desnivel em relacao ao sitio) | AWS Terrain Tiles (terrarium) — dado SRTM sobre o Brasil | dominio publico (SRTM) — sem chave, sem cadastro | NASA/NGA (SRTM), Mapzen/Linux Foundation (tiles) | https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png | `e303501cc0ab` |
| `assets/relevo/entorno_cobertura.png` | Cobertura do solo do entorno, pintada com as cores medidas no footage | ESA WorldCover 10 m 2021 v200 | CC-BY 4.0 — ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) | ESA WorldCover project | https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ | `493c8f4cbe2c` |

## Por que estes HDRIs

A latitude do céu decide: um HDRI capturado perto de −25,7°
tem o mesmo arco solar de Dois Vizinhos (−25,73144).
Hemisfério norte tem o arco espelhado e denuncia.

| asset | latitude | longitude | `evs_cap` |
|---|---|---|---|
| Belfast Sunset (Pure Sky) | -25.688 | 30.113 | 12 |
| Kloppenheim 06 (Pure Sky) | -25.648 | 30.152 | 12 |

`evs_cap` baixo (10–12) quer dizer disco solar estourado e
macio: o HDRI entrega céu, ambiente e reflexo, e a luz SUN
entrega a chave. Um HDRI de sol íntegro somado a uma SUN
produz **duas sombras**.
