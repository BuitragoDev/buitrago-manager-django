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
    """
    Simula todos los partidos de una jornada, actualiza la
    clasificación y genera noticias para el manager.
    """
    partidos = Partido.objects.filter(
        jornada=jornada, jugado=False
    ).select_related("equipo_local", "equipo_visitante")

    for partido in partidos:
        simular_partido(partido, manager)

    # Marcar jornada como disputada
    jornada.disputada = True
    jornada.save()

    # Recalcular clasificación completa
    recalcular_clasificacion(jornada.liga)


def simular_partido(partido: Partido, manager):
    """
    Simula un partido individual:
    1. Calcula fuerza de cada equipo según valoración media de jugadores
    2. Genera goles con distribución de Poisson simplificada
    3. Crea EstadisticaJugador para los jugadores convocados
    4. Genera noticias si es el equipo del manager
    """
    local     = partido.equipo_local
    visitante = partido.equipo_visitante

    # ── Calcular fuerza de cada equipo ────────────────────────
    fuerza_local     = _fuerza_equipo(local)
    fuerza_visitante = _fuerza_equipo(visitante)

    # Ventaja de jugar en casa: +5%
    fuerza_local *= 1.05

    # ── Generar resultado ─────────────────────────────────────
    media_goles_local     = _media_goles(fuerza_local, fuerza_visitante)
    media_goles_visitante = _media_goles(fuerza_visitante, fuerza_local)

    goles_local     = _poisson(media_goles_local)
    goles_visitante = _poisson(media_goles_visitante)

    # Asistencia aleatoria entre 40% y 95% del aforo
    asistencia = int(local.capacidad_estadio * random.uniform(0.40, 0.95))

    partido.goles_local     = goles_local
    partido.goles_visitante = goles_visitante
    partido.asistencia      = asistencia
    partido.jugado          = True
    partido.save()

    # ── Generar estadísticas de jugadores ─────────────────────
    _generar_estadisticas(partido, local, goles_local, goles_visitante, es_local=True)
    _generar_estadisticas(partido, visitante, goles_visitante, goles_local, es_local=False)

    # ── Reducir lesiones existentes ───────────────────────────
    _reducir_lesiones(local)
    _reducir_lesiones(visitante)

    # ── Generar posibles nuevas lesiones ──────────────────────
    _generar_lesiones(partido, manager)

    # ── Noticias para el manager ──────────────────────────────
    _generar_noticias_partido(partido, manager)


# ══════════════════════════════════════════════════════════════════
#  HELPERS DE SIMULACIÓN
# ══════════════════════════════════════════════════════════════════

def _fuerza_equipo(equipo):
    """
    Calcula la fuerza de un equipo como la media de valoración
    de sus 11 mejores jugadores disponibles (no lesionados).
    """
    jugadores = Jugador.objects.filter(
        equipo=equipo, lesionado=False
    ).order_by("-posicion")  # portero primero

    titulares = _seleccionar_once(jugadores)
    if not titulares:
        return 50.0

    total = sum(j.valoracion_media for j in titulares)
    return total / len(titulares)


def _seleccionar_once(jugadores):
    """
    Selecciona los 11 jugadores para el partido:
    1 POR + 4 DEF + 4 MED + 2 DEL (si hay suficientes).
    Si falta en alguna posición, rellena con los disponibles.
    """
    por = [j for j in jugadores if j.posicion == "POR"][:1]
    def_ = [j for j in jugadores if j.posicion == "DEF"][:4]
    med = [j for j in jugadores if j.posicion == "MED"][:4]
    del_ = [j for j in jugadores if j.posicion == "DEL"][:2]
    once = por + def_ + med + del_

    # Si no llegamos a 11, añadir los que falten
    if len(once) < 11:
        resto = [j for j in jugadores if j not in once]
        once += resto[:11 - len(once)]

    return once[:11]


def _media_goles(fuerza_ataque, fuerza_defensa):
    """
    Calcula la media de goles esperados para un equipo.
    Escala entre 0.5 y 3.5 goles por partido.
    """
    ratio = fuerza_ataque / max(fuerza_defensa, 1)
    media = 0.5 + (ratio - 0.8) * 2.5
    return max(0.3, min(3.5, media))


def _poisson(media):
    """
    Genera un número de goles usando aproximación de Poisson.
    """
    import math
    L = math.exp(-media)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def _generar_estadisticas(partido, equipo, goles_favor, goles_contra, es_local):
    """
    Crea registros EstadisticaJugador para los jugadores del equipo en este partido.
    Distribuye goles y asistencias entre los jugadores de forma realista.
    """
    jugadores = Jugador.objects.filter(
        equipo=equipo, lesionado=False
    )
    once = _seleccionar_once(list(jugadores))
    suplentes = [j for j in jugadores if j not in once][:7]
    convocados = once + suplentes

    # Determinar valoración base según resultado
    if goles_favor > goles_contra:
        base_val = Decimal("7.0")
    elif goles_favor == goles_contra:
        base_val = Decimal("6.5")
    else:
        base_val = Decimal("5.5")

    stats_bulk = []
    goles_repartir = goles_favor
    asist_repartir = goles_favor  # max 1 asistencia por gol

    # Delanteros y mediocampistas más propensos a marcar
    candidatos_gol   = [j for j in once if j.posicion in ("DEL", "MED")]
    candidatos_asist = [j for j in once if j.posicion in ("MED", "DEF")]

    goles_jugadores = {j.pk: 0 for j in convocados}
    asist_jugadores = {j.pk: 0 for j in convocados}

    for _ in range(goles_repartir):
        if candidatos_gol:
            # Peso por atributo disparo
            pesos = [j.disparo for j in candidatos_gol]
            goleador = random.choices(candidatos_gol, weights=pesos, k=1)[0]
            goles_jugadores[goleador.pk] += 1

    for _ in range(asist_repartir):
        if candidatos_asist:
            pesos = [j.pase for j in candidatos_asist]
            asistente = random.choices(candidatos_asist, weights=pesos, k=1)[0]
            asist_jugadores[asistente.pk] += 1

    for j in convocados:
        es_titular = j in once
        minutos = random.randint(60, 90) if es_titular else random.randint(0, 30)

        # Variación de valoración individual
        variacion = Decimal(str(round(random.uniform(-1.5, 1.5), 1)))
        val = base_val + variacion
        val = max(Decimal("1.0"), min(Decimal("10.0"), val))

        # Tarjetas
        amarillas = 1 if random.random() < 0.08 else 0
        roja      = True if (amarillas == 1 and random.random() < 0.05) else False

        stats_bulk.append(EstadisticaJugador(
            jugador=j,
            partido=partido,
            minutos_jugados=minutos if es_titular else minutos,
            goles=goles_jugadores.get(j.pk, 0),
            asistencias=asist_jugadores.get(j.pk, 0),
            tarjetas_amarillas=amarillas,
            tarjetas_rojas=int(roja),
            valoracion=val,
        ))

    EstadisticaJugador.objects.bulk_create(stats_bulk, ignore_conflicts=True)


def _reducir_lesiones(equipo):
    """Reduce en 1 jornada la baja de jugadores lesionados."""
    lesionados = Jugador.objects.filter(equipo=equipo, lesionado=True)
    for j in lesionados:
        j.jornadas_baja = max(0, j.jornadas_baja - 1)
        if j.jornadas_baja == 0:
            j.lesionado = False
        j.save()


def _generar_lesiones(partido, manager):
    """
    Genera lesiones aleatorias con baja probabilidad.
    Probabilidad: ~5% por jugador titular.
    """
    for equipo in [partido.equipo_local, partido.equipo_visitante]:
        jugadores = Jugador.objects.filter(equipo=equipo, lesionado=False)
        once = _seleccionar_once(list(jugadores))
        for j in once:
            if random.random() < 0.05:
                j.lesionado     = True
                j.jornadas_baja = random.randint(1, 6)
                j.save()

                # Noticia solo si es del equipo del manager
                if equipo == manager.equipo:
                    Noticia.objects.create(
                        manager=manager,
                        tipo="LES",
                        texto=(
                            f"{j.nombre_completo} se ha lesionado y estará "
                            f"{j.jornadas_baja} jornada(s) de baja."
                        ),
                        jornada=partido.jornada.numero,
                    )


def _generar_noticias_partido(partido, manager):
    """Genera la noticia de resultado para el partido del manager."""
    equipo = manager.equipo

    if partido.equipo_local != equipo and partido.equipo_visitante != equipo:
        return

    es_local = partido.equipo_local == equipo
    rival    = partido.equipo_visitante if es_local else partido.equipo_local
    gf       = partido.goles_local if es_local else partido.goles_visitante
    gc       = partido.goles_visitante if es_local else partido.goles_local
    lugar    = "en casa" if es_local else "a domicilio"

    if gf > gc:
        intro = f"¡Victoria {lugar}!"
    elif gf == gc:
        intro = f"Empate {lugar}."
    else:
        intro = f"Derrota {lugar}."

    texto = (
        f"{intro} {equipo.nombre_corto} {gf} - {gc} {rival.nombre_corto}. "
        f"Partido disputado en {partido.estadio} "
        f"ante {partido.asistencia:,} espectadores."
    )

    Noticia.objects.create(
        manager=manager,
        tipo="RES",
        texto=texto,
        jornada=partido.jornada.numero,
    )


# ══════════════════════════════════════════════════════════════════
#  RECALCULAR CLASIFICACIÓN
# ══════════════════════════════════════════════════════════════════

def recalcular_clasificacion(liga):
    """Recalcula la clasificación completa de la liga."""
    clasificaciones = Clasificacion.objects.filter(liga=liga)
    for c in clasificaciones:
        c.recalcular()