#!/usr/bin/env python3
"""Posicao do sol, direcao no mundo da cena, e cor por temperatura.

Sem `bpy` e sem dependencia externa, igual `terreno.py`: roda no venv e dentro
do Python do Blender. Existe porque o addon Sun Position **nao esta instalado**
nesta build (13 addons, nenhum de sol) -- e mesmo instalado, o
`read_factory_settings()` do `limpar_cena()` o derrubaria. Nenhum addon pode
estar no caminho critico do gerador.

Algoritmo NOAA Solar Calculator. Erro < 0,1 grau na faixa que interessa, uma
ordem de grandeza abaixo da incerteza do norte do mapa (ver ESTADO.md).

Convencao de azimute: **compasso** -- 0 = norte, 90 = leste, sentido horario.
Convencao do mundo, herdada de `terreno.para_mundo`: **+Y = norte, +X = leste**.

Uso:
    python scripts/sol.py --data 2026-11-27 --hora 18:15
    python scripts/sol.py --tabela 2026-11-27
"""

import argparse
import math

# Dois Vizinhos/PR -- R. Jorge Amado, Jardim Marcante
LAT = -25.73144
LON = -53.07627
TZ = -3.0


# --------------------------------------------------------------------------
# Posicao

def _juliano(ano, mes, dia, hora_decimal):
    """Dia juliano. Meses 1 e 2 contam como 13 e 14 do ano anterior."""
    if mes <= 2:
        ano -= 1
        mes += 12
    a = ano // 100
    b = 2 - a + a // 4
    jd = (int(365.25 * (ano + 4716)) + int(30.6001 * (mes + 1))
          + dia + b - 1524.5)
    return jd + hora_decimal / 24.0


def _elementos(jd):
    """Declinacao (graus) e equacao do tempo (minutos)."""
    t = (jd - 2451545.0) / 36525.0

    # longitude media geometrica e anomalia media
    l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360.0
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    mr = math.radians(m)
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

    # equacao do centro -> longitude verdadeira -> aparente
    c = (math.sin(mr) * (1.914602 - t * (0.004817 + 0.000014 * t))
         + math.sin(2 * mr) * (0.019993 - 0.000101 * t)
         + math.sin(3 * mr) * 0.000289)
    omega = 125.04 - 1934.136 * t
    lamb = l0 + c - 0.00569 - 0.00478 * math.sin(math.radians(omega))

    # obliquidade da ecliptica, corrigida
    eps0 = 23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813)))
                   / 60.0) / 60.0
    eps = math.radians(eps0 + 0.00256 * math.cos(math.radians(omega)))

    decl = math.degrees(math.asin(math.sin(eps) * math.sin(math.radians(lamb))))

    # equacao do tempo -- e ela que desloca o meio-dia solar do meio-dia do relogio
    y = math.tan(eps / 2.0) ** 2
    l0r = math.radians(l0)
    eot = 4.0 * math.degrees(
        y * math.sin(2 * l0r)
        - 2 * e * math.sin(mr)
        + 4 * e * y * math.sin(mr) * math.cos(2 * l0r)
        - 0.5 * y * y * math.sin(4 * l0r)
        - 1.25 * e * e * math.sin(2 * mr))
    return decl, eot


def posicao(ano, mes, dia, hora_decimal, lat=LAT, lon=LON, tz=TZ):
    """(elevacao_graus, azimute_graus). Azimute de compasso: 0=N, 90=L, horario.

    Elevacao **geometrica**, sem refracao atmosferica. Perto do horizonte a
    refracao levanta o sol aparente em ate ~0,57 grau; para posicionar uma luz
    no Blender o que vale e a geometria, e o HDRI ja traz a refracao embutida
    na propria fotografia.
    """
    jd = _juliano(ano, mes, dia, hora_decimal - tz)   # -> UTC
    decl, eot = _elementos(jd)

    # tempo solar verdadeiro, em minutos
    tst = (hora_decimal * 60.0 + eot + 4.0 * lon - 60.0 * tz) % 1440.0
    ha = tst / 4.0 - 180.0
    if ha < -180.0:
        ha += 360.0

    latr, dr, har = math.radians(lat), math.radians(decl), math.radians(ha)
    cos_z = (math.sin(latr) * math.sin(dr)
             + math.cos(latr) * math.cos(dr) * math.cos(har))
    cos_z = max(-1.0, min(1.0, cos_z))
    zen = math.acos(cos_z)
    elev = 90.0 - math.degrees(zen)

    sz = math.sin(zen)
    if abs(sz) < 1e-9:                      # sol no zenite exato
        return elev, 180.0
    razao = ((math.sin(latr) * cos_z - math.sin(dr))
             / (math.cos(latr) * sz))
    az = math.degrees(math.acos(max(-1.0, min(1.0, razao))))
    az = (az + 180.0) % 360.0 if ha > 0 else (540.0 - az) % 360.0
    return elev, az


def meio_dia_solar(ano, mes, dia, lat=LAT, lon=LON, tz=TZ):
    """Hora local do transito, em horas decimais. Nao e 12:00 -- a equacao do
    tempo e a distancia ao meridiano padrao do fuso deslocam."""
    jd = _juliano(ano, mes, dia, 12.0 - tz)
    _, eot = _elementos(jd)
    return (720.0 - 4.0 * lon - eot) / 60.0 + tz


# --------------------------------------------------------------------------
# Direcao no mundo

def direcao(elevacao_graus, azimute_graus, norte_do_mapa_graus=0.0):
    """Vetor unitario que aponta DA cena PARA o sol.

    +Y = norte, +X = leste. `norte_do_mapa_graus` e quanto o norte verdadeiro
    esta girado em relacao ao +Y do mundo -- se a prancha do PDF nao estiver
    alinhada com o norte, e aqui que se corrige, num lugar so.

    Confere sozinho: azimute 90 (leste) da +X, azimute 0 (norte) da +Y.
    """
    a = math.radians(azimute_graus - norte_do_mapa_graus)
    e = math.radians(elevacao_graus)
    ce = math.cos(e)
    return (ce * math.sin(a), ce * math.cos(a), math.sin(e))


def comprimento_da_sombra(elevacao_graus):
    """Multiplo da altura do objeto. A 3,7 graus, um palco de 10,5 m projeta
    158 m -- e isso decide enquadramento, nao so estetica."""
    if elevacao_graus <= 0.05:
        return float("inf")
    return 1.0 / math.tan(math.radians(elevacao_graus))


# --------------------------------------------------------------------------
# Cor

# Corpo negro em RGB **linear**, normalizado com R=1. Tabela interpolada em vez
# de ShaderNodeBlackbody porque a luz SUN quer uma tripla RGB, nao um shader.
_PLANCK = [
    (2700, (1.000, 0.457, 0.140)),
    (3000, (1.000, 0.513, 0.198)),
    (3300, (1.000, 0.560, 0.254)),
    (3500, (1.000, 0.588, 0.290)),
    (4000, (1.000, 0.653, 0.383)),
    (4500, (1.000, 0.708, 0.472)),
    (5000, (1.000, 0.755, 0.556)),
    (5500, (1.000, 0.796, 0.633)),
    (6000, (1.000, 0.832, 0.704)),
    (6500, (1.000, 0.863, 0.769)),
]


def cor_de_temperatura(kelvin):
    """RGB linear normalizado. Fora de 2700-6500 K, satura nas pontas."""
    if kelvin <= _PLANCK[0][0]:
        return _PLANCK[0][1]
    if kelvin >= _PLANCK[-1][0]:
        return _PLANCK[-1][1]
    for (k0, c0), (k1, c1) in zip(_PLANCK, _PLANCK[1:]):
        if k0 <= kelvin <= k1:
            f = (kelvin - k0) / (k1 - k0)
            return tuple(a + (b - a) * f for a, b in zip(c0, c1))
    return _PLANCK[-1][1]


# --------------------------------------------------------------------------

def _hhmm(texto):
    partes = [float(p) for p in str(texto).split(":")]
    while len(partes) < 3:
        partes.append(0.0)
    return partes[0] + partes[1] / 60.0 + partes[2] / 3600.0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="2026-11-27", help="AAAA-MM-DD")
    ap.add_argument("--hora", help="HH:MM local")
    ap.add_argument("--tabela", metavar="AAAA-MM-DD",
                    help="varre a tarde inteira de meia em meia hora")
    args = ap.parse_args()

    data = args.tabela or args.data
    ano, mes, dia = (int(p) for p in data.split("-"))

    transito = meio_dia_solar(ano, mes, dia)
    el_pico, _ = posicao(ano, mes, dia, transito)
    hh, mm = int(transito), round((transito % 1) * 60)
    print(f"Dois Vizinhos  {data}   lat {LAT}  lon {LON}  UTC{TZ:+.0f}")
    print(f"meio-dia solar: {hh:02d}:{mm:02d}   pico {el_pico:.1f} graus\n")

    if args.tabela:
        horas = [12.0 + i * 0.5 for i in range(15)]
    elif args.hora:
        horas = [_hhmm(args.hora)]
    else:
        horas = [17.5, 18.0, 18.25, 18.5, 18.75, 19.0]

    print(f"{'hora':>6}  {'elev':>7}  {'azim':>7}  {'sombra':>8}")
    for h in horas:
        el, az = posicao(ano, mes, dia, h)
        if el < -1.0:
            continue
        s = comprimento_da_sombra(el)
        sombra = "  -" if s == float("inf") else f"{s:6.1f}x"
        print(f"{int(h):02d}:{round((h % 1) * 60):02d}  {el:6.1f}   "
              f"{az:6.1f}   {sombra}")


if __name__ == "__main__":
    main()
