import random
from decimal import Decimal
from .models import (
    Partido, Jornada, Clasificacion,
    EstadisticaJugador, Jugador, Noticia
)


# ══════════════════════════════════════════════════════════════════
#  MOTOR DE SIMULACIÓN DE PARTIDOS
# ══════════════════════════════════════════════════════════════════

def simular_jornada(jornada: Jornada, manager):
    partidos = Partido.objects.filter(
        jornada=jornada, jugado=False
    ).select_related("equipo_local", "equipo_visitante")

    for partido in partidos:
        simular_partido(partido, manager)

    jornada.disputada = True
    jornada.save()
    recalcular_clasificacion(jornada.liga)


def simular_partido(partido: Partido, manager):
    local     = partido.equipo_local
    visitante = partido.equipo_visitante

    fuerza_local     = _fuerza_equipo(local)
    fuerza_visitante = _fuerza_equipo(visitante)
    fuerza_local    *= 1.05  # ventaja local

    goles_local     = _poisson(_media_goles(fuerza_local,     fuerza_visitante))
    goles_visitante = _poisson(_media_goles(fuerza_visitante, fuerza_local))

    partido.goles_local     = goles_local
    partido.goles_visitante = goles_visitante
    partido.asistencia      = int(local.capacidad_estadio * random.uniform(0.40, 0.95))
    partido.jugado          = True
    partido.save()

    _generar_estadisticas(partido, local,     goles_local,     goles_visitante)
    _generar_estadisticas(partido, visitante, goles_visitante, goles_local)

    _reducir_lesiones(local)
    _reducir_lesiones(visitante)
    _generar_lesiones(partido, manager)
    _generar_noticias_partido(partido, manager)


# ══════════════════════════════════════════════════════════════════
#  SELECCIÓN DE JUGADORES
# ══════════════════════════════════════════════════════════════════

def _fuerza_equipo(equipo):
    # Convertir a lista UNA sola vez para evitar múltiples queries
    jugadores = list(Jugador.objects.filter(equipo=equipo, lesionado=False))
    once = _seleccionar_once(jugadores)
    if not once:
        return 50.0
    return sum(j.valoracion_media for j in once) / len(once)


def _seleccionar_once(jugadores):
    """
    Elige el mejor 11 en formación 1-4-3-3.
    Siempre compara por PK, nunca por identidad de objeto.
    """
    por  = sorted([j for j in jugadores if j.posicion == "POR"],
                  key=lambda j: j.porteria, reverse=True)[:1]
    def_ = sorted([j for j in jugadores if j.posicion == "DEF"],
                  key=lambda j: j.defensa, reverse=True)[:4]
    med  = sorted([j for j in jugadores if j.posicion == "MED"],
                  key=lambda j: j.pase + j.regate, reverse=True)[:3]
    del_ = sorted([j for j in jugadores if j.posicion == "DEL"],
                  key=lambda j: j.disparo, reverse=True)[:3]

    once = por + def_ + med + del_

    # Rellenar hasta 11 si faltan posiciones
    if len(once) < 11:
        pks_once = {j.pk for j in once}
        resto = sorted(
            [j for j in jugadores if j.pk not in pks_once],
            key=lambda j: j.valoracion_media, reverse=True
        )
        once += resto[:11 - len(once)]

    return once[:11]


# ══════════════════════════════════════════════════════════════════
#  GENERACIÓN DE ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════════

def _generar_estadisticas(partido, equipo, goles_favor, goles_contra):
    """
    Genera EstadisticaJugador para 11 titulares + 3-5 suplentes.

    REGLA CLAVE: jugadores se convierte a lista UNA sola vez.
    Todas las comparaciones de pertenencia usan PKs, nunca
    identidad de objeto, para evitar bugs con instancias Django.
    """
    # ── Lista única de jugadores disponibles ─────────────────────
    jugadores = list(Jugador.objects.filter(equipo=equipo, lesionado=False))
    if not jugadores:
        return

    once     = _seleccionar_once(jugadores)
    pks_once = {j.pk for j in once}

    # Suplentes: entre 3 y 5, los mejores no titulares
    num_cambios = random.randint(3, 5)
    suplentes = sorted(
        [j for j in jugadores if j.pk not in pks_once],
        key=lambda j: j.valoracion_media, reverse=True
    )[:num_cambios]

    # ── Minutos con cambios coherentes ───────────────────────────
    # Cada suplente sustituye a un titular distinto entre el min 46-85
    titulares_a_sustituir = random.sample(once, min(num_cambios, len(once)))
    minuto_salida = {t.pk: random.randint(46, 85) for t in titulares_a_sustituir}

    # ── Distribución de goles y asistencias ──────────────────────
    candidatos_gol   = [j for j in once if j.posicion in ("DEL", "MED")]
    candidatos_asist = [j for j in once if j.posicion in ("MED", "DEF")]

    # Fallback: si no hay delanteros/medios, cualquier titular puede marcar
    if not candidatos_gol:
        candidatos_gol = once[:]
    if not candidatos_asist:
        candidatos_asist = once[:]

    goles_map = {}   # pk → goles
    asist_map = {}   # pk → asistencias

    for _ in range(goles_favor):
        pesos    = [j.disparo for j in candidatos_gol]
        goleador = random.choices(candidatos_gol, weights=pesos, k=1)[0]
        goles_map[goleador.pk] = goles_map.get(goleador.pk, 0) + 1

    for _ in range(goles_favor):
        if random.random() < 0.75:   # 75% de los goles tienen asistencia
            pesos     = [j.pase for j in candidatos_asist]
            asistente = random.choices(candidatos_asist, weights=pesos, k=1)[0]
            asist_map[asistente.pk] = asist_map.get(asistente.pk, 0) + 1

    # ── Valoración base según resultado ──────────────────────────
    if goles_favor > goles_contra:
        base_val = Decimal("7.0")
    elif goles_favor == goles_contra:
        base_val = Decimal("6.5")
    else:
        base_val = Decimal("5.5")

    # ── Construir registros — sin duplicados, sin ignore_conflicts ─
    stats_bulk = []
    pks_vistos = set()   # garantía extra anti-duplicados

    for j in once:
        if j.pk in pks_vistos:
            continue
        pks_vistos.add(j.pk)

        minutos   = minuto_salida.get(j.pk, random.randint(87, 90))
        variacion = Decimal(str(round(random.uniform(-1.5, 1.5), 1)))
        val       = max(Decimal("1.0"), min(Decimal("10.0"), base_val + variacion))
        amarillas = 1 if random.random() < 0.08 else 0
        roja      = 1 if (amarillas and random.random() < 0.05) else 0

        stats_bulk.append(EstadisticaJugador(
            jugador=j, partido=partido,
            minutos_jugados=minutos,
            goles=goles_map.get(j.pk, 0),
            asistencias=asist_map.get(j.pk, 0),
            tarjetas_amarillas=amarillas,
            tarjetas_rojas=roja,
            valoracion=val,
        ))

    for i, s in enumerate(suplentes):
        if s.pk in pks_vistos:
            continue
        pks_vistos.add(s.pk)

        titular_out = titulares_a_sustituir[i] if i < len(titulares_a_sustituir) else None
        minutos_sup = (90 - minuto_salida[titular_out.pk]) if titular_out else random.randint(5, 20)

        variacion = Decimal(str(round(random.uniform(-1.0, 1.0), 1)))
        val       = max(Decimal("1.0"), min(Decimal("10.0"), base_val + variacion))

        stats_bulk.append(EstadisticaJugador(
            jugador=s, partido=partido,
            minutos_jugados=minutos_sup,
            goles=goles_map.get(s.pk, 0),
            asistencias=asist_map.get(s.pk, 0),
            tarjetas_amarillas=0,
            tarjetas_rojas=0,
            valoracion=val,
        ))

    # Sin ignore_conflicts: si hay duplicados los detectamos antes
    EstadisticaJugador.objects.bulk_create(stats_bulk)


# ══════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════

def _media_goles(fuerza_ataque, fuerza_defensa):
    ratio = fuerza_ataque / max(fuerza_defensa, 1)
    return max(0.3, min(3.5, 0.5 + (ratio - 0.8) * 2.5))


def _poisson(media):
    import math
    L = math.exp(-media)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def _reducir_lesiones(equipo):
    for j in Jugador.objects.filter(equipo=equipo, lesionado=True):
        j.jornadas_baja = max(0, j.jornadas_baja - 1)
        if j.jornadas_baja == 0:
            j.lesionado = False
        j.save()


def _generar_lesiones(partido, manager):
    for equipo in [partido.equipo_local, partido.equipo_visitante]:
        jugadores = list(Jugador.objects.filter(equipo=equipo, lesionado=False))
        once      = _seleccionar_once(jugadores)
        for j in once:
            if random.random() < 0.05:
                j.lesionado     = True
                j.jornadas_baja = random.randint(1, 6)
                j.save()
                if equipo == manager.equipo:
                    Noticia.objects.create(
                        manager=manager, tipo="LES",
                        texto=(
                            f"{j.nombre_completo} se ha lesionado y estará "
                            f"{j.jornadas_baja} jornada(s) de baja."
                        ),
                        jornada=partido.jornada.numero,
                    )


def _generar_noticias_partido(partido, manager):
    equipo = manager.equipo
    if partido.equipo_local != equipo and partido.equipo_visitante != equipo:
        return

    es_local = partido.equipo_local == equipo
    rival    = partido.equipo_visitante if es_local else partido.equipo_local
    gf       = partido.goles_local      if es_local else partido.goles_visitante
    gc       = partido.goles_visitante  if es_local else partido.goles_local
    lugar    = "en casa" if es_local else "a domicilio"

    intro = "¡Victoria!" if gf > gc else ("Empate." if gf == gc else "Derrota.")
    Noticia.objects.create(
        manager=manager, tipo="RES",
        texto=(
            f"{intro} {equipo.nombre_corto} {gf} - {gc} {rival.nombre_corto} {lugar}. "
            f"Partido en {partido.estadio} ante {partido.asistencia:,} espectadores."
        ),
        jornada=partido.jornada.numero,
    )


# ══════════════════════════════════════════════════════════════════
#  CLASIFICACIÓN
# ══════════════════════════════════════════════════════════════════

def recalcular_clasificacion(liga):
    for c in Clasificacion.objects.filter(liga=liga):
        c.recalcular()