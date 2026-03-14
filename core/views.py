from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Avg, Max, Q, F
import json

from .models import (
    Liga, Equipo, Jugador, Manager,
    Jornada, Partido, Clasificacion,
    EstadisticaJugador, Noticia, Mercado, HistorialFichaje
)
from .simulacion import simular_jornada  # lo crearemos después


# ══════════════════════════════════════════════════════════════════
#  INDEX — Selección de equipo y nombre de mánager
# ══════════════════════════════════════════════════════════════════

def index(request):
    if request.session.get("manager_id"):
        return redirect("dashboard")

    if request.method == "POST":
        nombre    = request.POST.get("nombre", "").strip()
        equipo_id = request.POST.get("equipo_id")

        if not nombre or not equipo_id:
            ligas   = Liga.objects.all().order_by("nivel")
            equipos = Equipo.objects.select_related("liga").order_by("liga__nivel", "nombre")
            return render(request, "core/index.html", {
                "ligas": ligas, "equipos": equipos,
                "error": "Debes introducir tu nombre y elegir un equipo.",
            })

        equipo = get_object_or_404(Equipo, pk=equipo_id)
        liga   = equipo.liga

        manager = Manager.objects.create(
            nombre=nombre,
            equipo=equipo,
            liga=liga,
            temporada_inicio=liga.temporada,
        )
        request.session["manager_id"] = manager.pk
        return redirect("dashboard")

    ligas   = Liga.objects.all().order_by("nivel")
    equipos = Equipo.objects.select_related("liga").order_by("liga__nivel", "nombre")
    return render(request, "core/index.html", {"ligas": ligas, "equipos": equipos})


# ══════════════════════════════════════════════════════════════════
#  DASHBOARD — Pantalla principal
# ══════════════════════════════════════════════════════════════════

def dashboard(request):
    manager = _get_manager(request)
    if not manager:
        return redirect("index")

    liga   = manager.liga
    equipo = manager.equipo

    # ── Último y próximo partido ──────────────────────────────
    partidos_equipo = Partido.objects.filter(
        Q(equipo_local=equipo) | Q(equipo_visitante=equipo),
        jornada__liga=liga
    ).select_related("equipo_local", "equipo_visitante", "jornada").order_by("jornada__numero")

    ultimo_partido  = partidos_equipo.filter(jugado=True).last()
    proximo_partido = partidos_equipo.filter(jugado=False).first()

    # ── Clasificación ─────────────────────────────────────────
    clasificacion = Clasificacion.objects.filter(liga=liga).select_related("equipo").order_by(
        "-puntos", "-goles_favor", "goles_contra"
    )

    # Asignar posiciones dinámicamente
    clasificacion_list = list(clasificacion)
    for i, c in enumerate(clasificacion_list):
        c.pos = i + 1

    # ── Noticias ──────────────────────────────────────────────
    noticias = Noticia.objects.filter(manager=manager).order_by("-creada_en")[:20]

    # ── Estadísticas de mi equipo ─────────────────────────────
    max_goleador  = _max_goleador(equipo, liga)
    max_asistente = _max_asistente(equipo, liga)
    mejor_valoracion = _mejor_valoracion(equipo, liga)
    max_amarillas = _max_amarillas(equipo, liga)
    max_rojas     = _max_rojas(equipo, liga)
    max_minutos   = _max_minutos(equipo, liga)

    # ── Fecha ficticia del juego ──────────────────────────────
    fecha_juego = _fecha_jornada(liga.jornada_actual, liga.temporada)

    context = {
        "manager":          manager,
        "equipo":           equipo,
        "liga":             liga,
        "ultimo_partido":   ultimo_partido,
        "proximo_partido":  proximo_partido,
        "clasificacion":    clasificacion_list,
        "noticias":         noticias,
        "max_goleador":     max_goleador,
        "max_asistente":    max_asistente,
        "mejor_valoracion": mejor_valoracion,
        "max_amarillas":    max_amarillas,
        "max_rojas":        max_rojas,
        "max_minutos":      max_minutos,
        "fecha_juego":      fecha_juego,
    }
    return render(request, "core/dashboard.html", context)


# ══════════════════════════════════════════════════════════════════
#  SEGUIR / SIMULAR — reemplaza la vista seguir existente en views.py
# ══════════════════════════════════════════════════════════════════

def seguir(request):
    manager = _get_manager(request)
    if not manager:
        return redirect("index")

    liga = manager.liga

    # ── Temporada terminada: comprobar destitución antes de continuar ─
    if liga.jornada_actual > liga.jornadas_totales:

        equipo = manager.equipo

        # Posición final en la clasificación
        posicion_final = None
        try:
            clasif = Clasificacion.objects.filter(liga=liga).order_by(
                "-puntos", "-goles_favor", "goles_contra"
            )
            equipos_ordenados = [c.equipo for c in clasif]
            posicion_final = equipos_ordenados.index(equipo) + 1
        except Exception:
            posicion_final = 0

        # ── Procesar contratos ANTES de contar jugadores ──────────
        import random as _r
        jugadores_manager = list(Jugador.objects.filter(equipo=equipo))
        liberados = []
        for jugador in jugadores_manager:
            jugador.temporadas_contrato -= 1
            if jugador.temporadas_contrato <= 0:
                otros_equipos = list(Equipo.objects.exclude(pk=equipo.pk))
                if otros_equipos:
                    jugador.equipo = _r.choice(otros_equipos)
                jugador.temporadas_contrato = 0
                liberados.append(jugador.nombre_completo)
                Mercado.objects.get_or_create(
                    jugador=jugador,
                    defaults={"liga": liga, "disponible": True, "dificultad_fichaje": 50}
                )
            jugador.save()

        # Ahora sí: contar jugadores reales tras expirar contratos
        jugadores_plantilla = equipo.jugadores.count()

        # Condiciones de destitución (descenso tiene prioridad)
        # Premier/Championship/League One: zona descenso = pos >= 18 (últimos 3)
        # League Two: zona peligro = pos >= 17 (últimos 4, descenso a National League)
        motivo = None
        nivel_liga = liga.nivel
        umbral_descenso = 17 if nivel_liga == 4 else 18
        zona_nombre = "zona de descenso a la National League" if nivel_liga == 4 else "zona de descenso"

        if posicion_final and posicion_final >= umbral_descenso:
            motivo = (
                f"El equipo ha finalizado la temporada en <strong>{posicion_final}ª posición</strong>, "
                f"en {zona_nombre}. Los resultados no han sido los esperados por la directiva."
            )
        elif jugadores_plantilla < 11:
            motivo = (
                f"Tras la expiración de contratos, el equipo cuenta con solo "
                f"<strong>{jugadores_plantilla} jugadores</strong> en plantilla, "
                f"por debajo del mínimo de 11 requerido para competir."
            )

        if motivo:
            return render(request, "core/destituido.html", {
                "manager":             manager,
                "equipo":              equipo,
                "liga":                liga,
                "motivo":              motivo,
                "posicion_final":      posicion_final or "—",
                "jugadores_plantilla": jugadores_plantilla,
            })

        # Sin destitución: registrar noticias de contratos expirados y continuar
        for nombre in liberados:
            Noticia.objects.create(
                manager=manager, tipo="FIC", jornada=liga.jornada_actual,
                texto=f"{nombre} ha abandonado el club al expirar su contrato.",
            )

        ligas_pendientes = request.session.pop("ligas_pendientes_cierre", [])

        if ligas_pendientes:
            # Todas las ligas terminaron en la misma jornada 38.
            # DOS PASADAS para garantizar 20 equipos por liga:
            # Pasada 1: ascensos/descensos en todas las ligas (League Two → League One → Championship → Premier)
            todas_ligas_a_cerrar = list(Liga.objects.filter(pk__in=ligas_pendientes).order_by("-nivel")) + [liga]
            resultados = {}
            for l in todas_ligas_a_cerrar:
                resultados[l.pk] = _cerrar_temporada_liga(l)

            # Tras los ascensos/descensos, el equipo del manager puede haber cambiado de liga.
            # Actualizamos manager.liga para que apunte a la nueva liga correcta.
            manager.equipo.refresh_from_db()
            nueva_liga = manager.equipo.liga
            manager.liga = nueva_liga
            manager.save()

            # Asegurar que la liga de destino del manager está en la lista a regenerar
            pks_a_cerrar = {l.pk for l in todas_ligas_a_cerrar}
            if nueva_liga.pk not in pks_a_cerrar:
                todas_ligas_a_cerrar.append(nueva_liga)

            # Pasada 2: regenerar calendarios y clasificaciones (ahora sí 20 equipos por liga)
            for l in todas_ligas_a_cerrar:
                # contratos_procesados=True solo para la liga de origen del manager (ya se procesaron arriba)
                _regenerar_liga(l, manager, contratos_procesados=(l.pk == liga.pk))

            # Noticias solo de la liga del manager (ya actualizada)
            from .models import Noticia as _N
            _N.objects.filter(manager=manager).delete()
            campeon_liga_anterior = resultados[liga.pk]["campeon"]
            nueva_liga.refresh_from_db()
            _N.objects.create(
                manager=manager, tipo="GEN", jornada=1,
                texto=(
                    f"Comienza la {nueva_liga.nombre} {nueva_liga.temporada}. "
                    + (f"Campeón de {liga.nombre} la temporada anterior: {campeon_liga_anterior.nombre_corto}." if campeon_liga_anterior else "")
                ),
            )
            for texto in resultados[liga.pk]["noticias_movimientos"]:
                _N.objects.create(manager=manager, tipo="GEN", texto=texto, jornada=1)
        else:
            # Solo la liga del manager termina esta temporada
            _iniciar_nueva_temporada(liga, manager, contratos_procesados=True, crear_noticias=True)

            # También aquí: si el manager ascendió/descendió, actualizar manager.liga
            manager.equipo.refresh_from_db()
            nueva_liga = manager.equipo.liga
            if nueva_liga.pk != liga.pk:
                manager.liga = nueva_liga
                manager.save()

        return redirect("dashboard")

    # ── Simular la jornada actual ─────────────────────────────
    jornada_num = liga.jornada_actual
    jornada = get_object_or_404(Jornada, liga=liga, numero=jornada_num)
    simular_jornada(jornada, manager)

    liga.jornada_actual += 1
    liga.save()

    # Guardar jornadas simuladas de otras ligas
    jornadas_otras = {}
    ligas_terminadas = []  # ligas ajenas que acabaron jornada 38 — se procesan al pulsar Continuar
    otras_ligas = Liga.objects.exclude(pk=liga.pk)
    for otra_liga in otras_ligas:
        otra_jornada = Jornada.objects.filter(
            liga=otra_liga, numero=otra_liga.jornada_actual
        ).first()
        if otra_jornada and not otra_jornada.disputada:
            jornadas_otras[otra_liga.pk] = otra_liga.jornada_actual
            simular_jornada(otra_jornada, manager)
            otra_liga.jornada_actual += 1
            otra_liga.save()
            # Si la otra liga terminó, la marcamos para procesarla después
            if otra_liga.jornada_actual > otra_liga.jornadas_totales:
                ligas_terminadas.append(otra_liga.pk)

    # Guardar en sesión qué jornadas mostrar y qué ligas hay que cerrar
    request.session["ultima_jornada"] = {
        str(liga.pk): jornada_num,
        **{str(pk): num for pk, num in jornadas_otras.items()}
    }
    request.session["ligas_pendientes_cierre"] = ligas_terminadas

    return redirect("jornada_resultado")


# ══════════════════════════════════════════════════════════════════
#  JORNADA RESULTADO — Pantalla de resultados tras simular
# ══════════════════════════════════════════════════════════════════

def jornada_resultado(request):
    manager = _get_manager(request)
    if not manager:
        return redirect("index")

    ultima_jornada = request.session.get("ultima_jornada", {})
    if not ultima_jornada:
        return redirect("dashboard")

    todas_ligas = Liga.objects.all().order_by("nivel")
    datos_ligas = []

    for liga_obj in todas_ligas:
        jornada_num = ultima_jornada.get(str(liga_obj.pk))
        if jornada_num is None:
            continue
        jornada_obj = Jornada.objects.filter(
            liga=liga_obj, numero=jornada_num
        ).first()
        if not jornada_obj:
            continue

        partidos = Partido.objects.filter(
            jornada=jornada_obj, jugado=True
        ).select_related("equipo_local", "equipo_visitante").order_by("pk")

        partidos_data = []
        for p in partidos:
            # Usar _id para evitar que select_related rompa la comparación ORM
            goles_local = list(EstadisticaJugador.objects.filter(
                partido=p, jugador__equipo_id=p.equipo_local_id, goles__gt=0
            ).select_related("jugador").order_by("-goles"))
            goles_visit = list(EstadisticaJugador.objects.filter(
                partido=p, jugador__equipo_id=p.equipo_visitante_id, goles__gt=0
            ).select_related("jugador").order_by("-goles"))

            # MVP del partido (mejor valoración)
            mvp = EstadisticaJugador.objects.filter(
                partido=p
            ).select_related("jugador").order_by("-valoracion").first()

            partidos_data.append({
                "partido":      p,
                "goles_local":  goles_local,
                "goles_visit":  goles_visit,
                "mvp":          mvp,
                "es_mi_partido": (
                    p.equipo_local_id == manager.equipo_id or
                    p.equipo_visitante_id == manager.equipo_id
                ),
            })

        datos_ligas.append({
            "liga":     liga_obj,
            "jornada":  jornada_num,
            "partidos": partidos_data,
        })

    context = {
        "manager":     manager,
        "equipo":      manager.equipo,
        "liga":        manager.liga,
        "datos_ligas": datos_ligas,
        "fecha_juego": _fecha_jornada(manager.liga.jornada_actual, manager.liga.temporada),
    }
    return render(request, "core/jornada_resultado.html", context)


# ══════════════════════════════════════════════════════════════════
#  BORRAR NOTICIA (llamada AJAX desde el botón ✕)
# ══════════════════════════════════════════════════════════════════

@require_POST
def borrar_noticia(request, noticia_id):
    manager = _get_manager(request)
    if not manager:
        return JsonResponse({"ok": False}, status=403)

    Noticia.objects.filter(pk=noticia_id, manager=manager).delete()
    return JsonResponse({"ok": True})


# ══════════════════════════════════════════════════════════════════
#  PLANTILLA
# ══════════════════════════════════════════════════════════════════

def plantilla(request):
    manager = _get_manager(request)
    if not manager:
        return redirect("index")

    liga   = manager.liga
    equipo = manager.equipo

    # Stats de la temporada actual para cada jugador del equipo.
    stats_qs = EstadisticaJugador.objects.filter(
        jugador__equipo=equipo,
        partido__jornada__liga=liga,
    ).values("jugador_id").annotate(
        goles=Sum("goles"),
        asistencias=Sum("asistencias"),
        valoracion=Avg("valoracion"),
        amarillas=Sum("tarjetas_amarillas"),
        rojas=Sum("tarjetas_rojas"),
        minutos=Sum("minutos_jugados"),
    )
    stats_map = {s["jugador_id"]: s for s in stats_qs}

    jugadores = list(Jugador.objects.filter(equipo=equipo).order_by("posicion", "apellidos"))
    for j in jugadores:
        s = stats_map.get(j.id, {})
        j.stats_goles       = s.get("goles", 0) or 0
        j.stats_asistencias = s.get("asistencias", 0) or 0
        j.stats_valoracion  = s.get("valoracion", None)
        j.stats_amarillas   = s.get("amarillas", 0) or 0
        j.stats_rojas       = s.get("rojas", 0) or 0
        j.stats_minutos     = s.get("minutos", 0) or 0

    plantilla_dict = {
        "POR": [j for j in jugadores if j.posicion == "POR"],
        "DEF": [j for j in jugadores if j.posicion == "DEF"],
        "MED": [j for j in jugadores if j.posicion == "MED"],
        "DEL": [j for j in jugadores if j.posicion == "DEL"],
    }

    context = {
        "manager":        manager,
        "equipo":         equipo,
        "liga":           liga,
        "jugadores":      jugadores,
        "plantilla_dict": plantilla_dict,
        "fecha_juego":    _fecha_jornada(liga.jornada_actual, liga.temporada),
    }
    return render(request, "core/plantilla.html", context)


# ══════════════════════════════════════════════════════════════════
#  RENOVAR JUGADOR
# ══════════════════════════════════════════════════════════════════

@require_POST
def renovar_jugador(request, jugador_id):
    manager = _get_manager(request)
    if not manager:
        return JsonResponse({"ok": False}, status=403)

    jugador = get_object_or_404(Jugador, pk=jugador_id, equipo=manager.equipo)

    # 4 temporadas si menor de 30, 2 si mayor o igual
    anios = 4 if jugador.edad < 30 else 2
    jugador.temporadas_contrato += anios
    jugador.save()

    Noticia.objects.create(
        manager=manager,
        tipo="REN",
        texto=f"{jugador.nombre} {jugador.apellidos} ha renovado por {anios} temporadas más.",
        jornada=manager.liga.jornada_actual,
    )

    return JsonResponse({
        "ok": True,
        "temporadas_contrato": jugador.temporadas_contrato,
    })


# ══════════════════════════════════════════════════════════════════
#  DESPEDIR JUGADOR
# ══════════════════════════════════════════════════════════════════

@require_POST
def despedir_jugador(request, jugador_id):
    manager = _get_manager(request)
    if not manager:
        return JsonResponse({"ok": False}, status=403)

    jugador = get_object_or_404(Jugador, pk=jugador_id, equipo=manager.equipo)
    liga    = manager.liga

    # No permitir despedir si la plantilla quedaría con menos de 11 jugadores
    num_jugadores = Jugador.objects.filter(equipo=manager.equipo).count()
    if num_jugadores <= 11:
        return JsonResponse({
            "ok": False,
            "mensaje": "No puedes despedir más jugadores. Necesitas al menos 11."
        })

    nombre = f"{jugador.nombre} {jugador.apellidos}"

    # Buscar un equipo neutral al que asignar al jugador (cualquiera que no sea el del manager)
    import random as _rand
    equipos_otros = list(Equipo.objects.exclude(pk=manager.equipo.pk))
    if equipos_otros:
        nuevo_equipo = _rand.choice(equipos_otros)
        jugador.equipo = nuevo_equipo
        jugador.save()
        # Añadirlo al mercado para que pueda ser fichado
        Mercado.objects.get_or_create(
            jugador=jugador, liga=liga,
            defaults={"disponible": True, "dificultad_fichaje": 50}
        )
    else:
        # Si no hay otros equipos (no debería pasar), simplemente lo desvinculamos
        jugador.equipo = None
        jugador.save()

    Noticia.objects.create(
        manager=manager,
        tipo="FIC",
        texto=f"{nombre} ha sido despedido y está libre en el mercado.",
        jornada=liga.jornada_actual,
    )

    return JsonResponse({"ok": True, "mensaje": f"{nombre} ha sido despedido."})



def mercado_fichajes(request):
    manager = _get_manager(request)
    if not manager:
        return redirect("index")

    liga   = manager.liga
    equipo = manager.equipo

    ofertas_qs = Mercado.objects.filter(liga=liga, disponible=True).exclude(jugador__equipo=equipo)
    if not ofertas_qs.exists():
        _generar_mercado(liga)
        ofertas_qs = Mercado.objects.filter(liga=liga, disponible=True).exclude(jugador__equipo=equipo)

    ofertas = list(ofertas_qs.select_related("jugador", "jugador__equipo"))

    media_equipo = Jugador.objects.filter(equipo=equipo).aggregate(
        m=Avg((F("velocidad") + F("regate") + F("pase") + F("disparo") + F("defensa") + F("fisico")) / 6.0)
    )["m"] or 60

    jugadores_equipo = Jugador.objects.filter(equipo=equipo).count()

    for o in ofertas:
        j = o.jugador
        media_j = (j.velocidad + j.regate + j.pase + j.disparo + j.defensa + j.fisico) / 6
        j.media = round(media_j, 1)
        diff = _calcular_dificultad(media_j, media_equipo, liga.jornada_actual, liga.jornadas_totales)
        o.dificultad_real = diff
        if diff >= 80:
            o.dif_label = "MUY DIFÍCIL"; o.dif_clase = "dif-muy-dificil"
        elif diff >= 60:
            o.dif_label = "DIFÍCIL";     o.dif_clase = "dif-dificil"
        elif diff >= 40:
            o.dif_label = "POSIBLE";     o.dif_clase = "dif-posible"
        else:
            o.dif_label = "PROBABLE";    o.dif_clase = "dif-probable"

    ofertas.sort(key=lambda o: o.jugador.media, reverse=True)

    context = {
        "manager":          manager,
        "equipo":           equipo,
        "liga":             liga,
        "ofertas":          ofertas,
        "jugadores_equipo": jugadores_equipo,
        "limite_plantilla": 22,
        "media_equipo":     round(media_equipo, 1),
        "fecha_juego":      _fecha_jornada(liga.jornada_actual, liga.temporada),
    }
    return render(request, "core/mercado.html", context)


# ══════════════════════════════════════════════════════════════════
#  INTENTAR FICHAR JUGADOR
# ══════════════════════════════════════════════════════════════════

import random as _random

def _calcular_dificultad(media_jugador, media_equipo, jornada_actual, jornadas_totales):
    """
    Calcula dificultad real (0-100) para fichar a un jugador.
    Factores:
    - Diferencia de nivel: jugador mejor que mi equipo → más difícil
    - Progreso de temporada: a más jornadas jugadas, mercado más cerrado
    """
    # Base por diferencia de nivel
    diff = media_jugador - media_equipo
    if diff >= 20:
        base = 92          # estrella inalcanzable
    elif diff >= 12:
        base = 80          # muy por encima de mi nivel
    elif diff >= 6:
        base = 65          # algo mejor que mi equipo
    elif diff >= -3:
        base = 48          # nivel similar, negociable
    elif diff >= -10:
        base = 30          # por debajo de mi nivel
    else:
        base = 18          # muy por debajo, fácil de convencer

    # Modificador de jornada: mercado más cerrado según avanza la temporada
    # Primeras 10 jornadas: -8 (más fácil)
    # Jornadas 11-28: neutro
    # Últimas 10 jornadas: +15 (mercado casi cerrado)
    progreso = jornada_actual / max(jornadas_totales, 1)
    if progreso <= 0.25:
        mod_jornada = -8
    elif progreso >= 0.75:
        mod_jornada = +15
    else:
        mod_jornada = 0

    # Siempre hay un componente de aleatoriedad de ±5 fijo en el modelo
    return max(10, min(95, int(base + mod_jornada)))


@require_POST
def fichar_jugador(request, oferta_id):
    manager = _get_manager(request)
    if not manager:
        return JsonResponse({"ok": False}, status=403)

    liga   = manager.liga
    equipo = manager.equipo

    # Comprobar límite de plantilla
    num_jugadores = Jugador.objects.filter(equipo=equipo).count()
    if num_jugadores >= 22:
        return JsonResponse({
            "ok": False,
            "tipo": "limite",
            "mensaje": "No puedes fichar más jugadores. Tienes el máximo de 22."
        })

    oferta  = get_object_or_404(Mercado, pk=oferta_id, disponible=True)
    jugador = oferta.jugador

    # Calcular dificultad real en el momento del intento
    media_equipo = Jugador.objects.filter(equipo=equipo).aggregate(
        m=Avg((F("velocidad") + F("regate") + F("pase") + F("disparo") + F("defensa") + F("fisico")) / 6.0)
    )["m"] or 60
    media_j = (jugador.velocidad + jugador.regate + jugador.pase +
               jugador.disparo + jugador.defensa + jugador.fisico) / 6
    dificultad = _calcular_dificultad(media_j, media_equipo, liga.jornada_actual, liga.jornadas_totales)

    # La tirada: dado de 1-100, necesitas sacar <= (100 - dificultad) + varianza ±5
    umbral = 100 - dificultad + _random.randint(-5, 5)
    umbral = max(5, min(90, umbral))
    tirada = _random.randint(1, 100)
    exito  = tirada <= umbral

    if exito:
        equipo_origen   = jugador.equipo
        jugador.equipo  = equipo
        jugador.save()
        oferta.disponible = False
        oferta.save()
        HistorialFichaje.objects.create(
            manager=manager, jugador=jugador,
            equipo_origen=equipo_origen, equipo_destino=equipo,
            tipo="F", jornada=liga.jornada_actual, temporada=liga.temporada, exito=True,
        )
        Noticia.objects.create(
            manager=manager, tipo="FIC",
            texto=f"¡Fichaje completado! {jugador.nombre_completo} llega procedente de {equipo_origen}.",
            jornada=liga.jornada_actual,
        )
        # Recalcular media del equipo tras el fichaje
        nueva_media = Jugador.objects.filter(equipo=equipo).aggregate(
            m=Avg((F("velocidad") + F("regate") + F("pase") + F("disparo") + F("defensa") + F("fisico")) / 6.0)
        )["m"] or 0
        return JsonResponse({
            "ok": True,
            "tipo": "exito",
            "mensaje": f"¡Fichado! {jugador.nombre_completo} ya es de {equipo.nombre_corto}.",
            "nueva_media": round(float(nueva_media), 1),
        })
    else:
        # Rechazado → quitarlo del mercado, solo hay una oportunidad
        oferta.disponible = False
        oferta.save()
        HistorialFichaje.objects.create(
            manager=manager, jugador=jugador,
            equipo_origen=jugador.equipo, equipo_destino=equipo,
            tipo="F", jornada=liga.jornada_actual, temporada=liga.temporada, exito=False,
        )
        Noticia.objects.create(
            manager=manager, tipo="FIC",
            texto=f"Negociación fallida. {jugador.equipo} rechazó la oferta por {jugador.nombre_completo}.",
            jornada=liga.jornada_actual,
        )
        return JsonResponse({
            "ok": False,
            "tipo": "rechazo",
            "mensaje": f"Oferta rechazada. {jugador.equipo} no quiere vender."
        })


# ══════════════════════════════════════════════════════════════════
#  CLASIFICACIÓN COMPLETA
# ══════════════════════════════════════════════════════════════════

def clasificacion(request):
    manager = _get_manager(request)
    if not manager:
        return redirect("index")

    liga = manager.liga

    # Construir tablas de todas las ligas para el template
    todas_ligas = Liga.objects.all().order_by("nivel")
    tablas_ctx = []
    for l in todas_ligas:
        tabla = Clasificacion.objects.filter(liga=l).select_related("equipo").order_by(
            "-puntos", "-goles_favor", "goles_contra"
        )
        tabla_list = list(tabla)
        for i, c in enumerate(tabla_list):
            c.pos = i + 1
        tablas_ctx.append({
            "liga":  l,
            "tabla": tabla_list,
        })

    context = {
        "manager":     manager,
        "equipo":      manager.equipo,
        "liga":        liga,
        "todas_ligas": todas_ligas,
        "tablas_ctx":  tablas_ctx,
        "fecha_juego": _fecha_jornada(liga.jornada_actual, liga.temporada),
    }
    return render(request, "core/clasificacion.html", context)


# ══════════════════════════════════════════════════════════════════
#  ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════════

def estadisticas(request):
    manager = _get_manager(request)
    if not manager:
        return redirect("index")

    liga = manager.liga
    todas_ligas = Liga.objects.all().order_by("nivel")

    def get_stats(l):
        top_goleadores = EstadisticaJugador.objects.filter(
            partido__jornada__liga=l
        ).values(
            "jugador__nombre", "jugador__apellidos",
            "jugador__equipo__nombre_corto",
            "jugador__equipo__abreviatura",
        ).annotate(total_goles=Sum("goles")).filter(total_goles__gt=0).order_by("-total_goles")[:25]

        top_asistentes = EstadisticaJugador.objects.filter(
            partido__jornada__liga=l
        ).values(
            "jugador__nombre", "jugador__apellidos",
            "jugador__equipo__nombre_corto",
            "jugador__equipo__abreviatura",
        ).annotate(total_asistencias=Sum("asistencias")).filter(total_asistencias__gt=0).order_by("-total_asistencias")[:25]

        top_valoracion = EstadisticaJugador.objects.filter(
            partido__jornada__liga=l, minutos_jugados__gt=0
        ).values(
            "jugador__nombre", "jugador__apellidos",
            "jugador__equipo__nombre_corto",
            "jugador__equipo__abreviatura",
        ).annotate(
            media_valoracion=Avg("valoracion"),
            partidos=Sum("minutos_jugados")
        ).filter(partidos__gte=3).order_by("-media_valoracion")[:25]

        return {
            "liga":           l,
            "top_goleadores": top_goleadores,
            "top_asistentes": top_asistentes,
            "top_valoracion": top_valoracion,
        }

    ligas_stats = [get_stats(l) for l in todas_ligas]

    context = {
        "manager":     manager,
        "equipo":      manager.equipo,
        "liga":        liga,
        "ligas_stats": ligas_stats,
        "fecha_juego": _fecha_jornada(liga.jornada_actual, liga.temporada),
    }
    return render(request, "core/estadisticas.html", context)


# ══════════════════════════════════════════════════════════════════
#  RESULTADOS
# ══════════════════════════════════════════════════════════════════

def resultados(request):
    manager = _get_manager(request)
    if not manager:
        return redirect("index")

    liga = manager.liga
    todas_ligas = Liga.objects.all().order_by("nivel")

    ligas_data = []
    for l in todas_ligas:
        jornadas = Jornada.objects.filter(liga=l).prefetch_related(
            "partidos__equipo_local", "partidos__equipo_visitante"
        ).order_by("numero")
        ligas_data.append({
            "liga":          l,
            "jornadas":      jornadas,
            "jornada_actual": max(l.jornada_actual - 1, 1),
        })

    context = {
        "manager":     manager,
        "equipo":      manager.equipo,
        "liga":        liga,
        "ligas_data":  ligas_data,
        "fecha_juego": _fecha_jornada(liga.jornada_actual, liga.temporada),
    }
    return render(request, "core/resultados.html", context)

# ══════════════════════════════════════════════════════════════════
#  HISTÓRICO — Palmarés por temporadas
# ══════════════════════════════════════════════════════════════════

def historico(request):
    manager = _get_manager(request)
    if not manager:
        return redirect("index")

    from .models import HistoricoTemporada
    from collections import Counter
    liga = manager.liga
    equipo = manager.equipo
    todas_ligas = Liga.objects.all().order_by("nivel")

    def _stats_liga(l):
        registros = list(HistoricoTemporada.objects.filter(liga=l).select_related(
            "campeon", "subcampeon", "max_goleador", "mejor_jugador"
        ).order_by("-temporada"))

        # Si la temporada actual está terminada y aún no guardada, calcularla al vuelo
        if l.jornada_actual > l.jornadas_totales:
            temporadas_guardadas = {r.temporada for r in registros}
            if l.temporada not in temporadas_guardadas:
                datos = _datos_temporada(l)
                registros.insert(0, datos)

        registros_obj = [r for r in registros if hasattr(r, 'campeon')]
        total_temporadas = len(registros_obj)

        mi_campeonatos = sum(1 for r in registros_obj if r.campeon    and r.campeon.pk    == equipo.pk)
        mi_goleadores  = sum(1 for r in registros_obj if r.max_goleador  and r.max_goleador.equipo_id  == equipo.pk)
        mi_mejores     = sum(1 for r in registros_obj if r.mejor_jugador and r.mejor_jugador.equipo_id == equipo.pk)

        campeonatos_por_equipo = Counter(r.campeon.pk for r in registros_obj if r.campeon)
        mejor_equipo_pk = campeonatos_por_equipo.most_common(1)[0][0] if campeonatos_por_equipo else None

        if mejor_equipo_pk:
            from .models import Equipo as EQ
            mejor_equipo        = EQ.objects.get(pk=mejor_equipo_pk)
            mejor_equipo_camps  = campeonatos_por_equipo[mejor_equipo_pk]
            mejor_equipo_gol    = sum(1 for r in registros_obj if r.max_goleador  and r.max_goleador.equipo_id  == mejor_equipo_pk)
            mejor_equipo_mejor  = sum(1 for r in registros_obj if r.mejor_jugador and r.mejor_jugador.equipo_id == mejor_equipo_pk)
        else:
            mejor_equipo = None
            mejor_equipo_camps = mejor_equipo_gol = mejor_equipo_mejor = 0

        return {
            "liga":               l,
            "registros":          registros,
            "total_temporadas":   total_temporadas,
            "mi_campeonatos":     mi_campeonatos,
            "mi_goleadores":      mi_goleadores,
            "mi_mejores":         mi_mejores,
            "mejor_equipo":       mejor_equipo,
            "mejor_equipo_camps": mejor_equipo_camps,
            "mejor_equipo_gol":   mejor_equipo_gol,
            "mejor_equipo_mejor": mejor_equipo_mejor,
        }

    ligas_historico = [_stats_liga(l) for l in todas_ligas]

    context = {
        "manager":        manager,
        "equipo":         equipo,
        "liga":           liga,
        "ligas_historico": ligas_historico,
        "fecha_juego":    _fecha_jornada(liga.jornada_actual, liga.temporada),
    }
    return render(request, "core/historico.html", context)


def _datos_temporada(liga):
    """
    Calcula el palmarés de una temporada:
    campeón, subcampeón, máximo goleador y mejor valoración.
    """
    from .models import EstadisticaJugador
    from django.db.models import Sum, Avg

    # Campeón y subcampeón desde la clasificación final
    tabla = Clasificacion.objects.filter(liga=liga).select_related("equipo").order_by(
        "-puntos", "-goles_favor", "goles_contra"
    )
    campeon    = tabla[0].equipo if tabla.count() > 0 else None
    subcampeon = tabla[1].equipo if tabla.count() > 1 else None

    # Máximo goleador de la temporada (toda la liga)
    max_goleador = EstadisticaJugador.objects.filter(
        partido__jornada__liga=liga
    ).values(
        "jugador__nombre", "jugador__apellidos", "jugador__equipo__nombre_corto"
    ).annotate(
        total=Sum("goles")
    ).order_by("-total").first()

    # Mejor valoración media (mínimo 10 partidos jugados)
    mejor_jugador = EstadisticaJugador.objects.filter(
        partido__jornada__liga=liga,
        minutos_jugados__gt=0
    ).values(
        "jugador__nombre", "jugador__apellidos", "jugador__equipo__nombre_corto"
    ).annotate(
        media=Avg("valoracion"),
        partidos=Sum("minutos_jugados")
    ).filter(partidos__gte=10).order_by("-media").first()

    return {
        "temporada":     liga.temporada,
        "campeon":       campeon,
        "subcampeon":    subcampeon,
        "max_goleador":  max_goleador,
        "mejor_jugador": mejor_jugador,
    }

# ══════════════════════════════════════════════════════════════════
#  NUEVA TEMPORADA
# ══════════════════════════════════════════════════════════════════

def _cerrar_temporada_liga(liga):
    """
    PASADA 1: guarda palmarés y ejecuta ascensos/descensos para UNA liga.
    Devuelve dict con campeon y lista de noticias de movimientos.
    NO toca calendarios ni clasificaciones todavía.
    """
    from .models import EstadisticaJugador, HistoricoTemporada
    from .models import Jugador as J
    from django.db.models import Sum, Avg

    tabla = list(
        Clasificacion.objects.filter(liga=liga)
        .select_related("equipo")
        .order_by("-puntos", "-goles_favor", "goles_contra")
    )
    campeon    = tabla[0].equipo if len(tabla) > 0 else None
    subcampeon = tabla[1].equipo if len(tabla) > 1 else None

    max_gol = EstadisticaJugador.objects.filter(
        partido__jornada__liga=liga
    ).values("jugador").annotate(total=Sum("goles")).order_by("-total").first()

    mejor_val = EstadisticaJugador.objects.filter(
        partido__jornada__liga=liga, minutos_jugados__gt=0
    ).values("jugador").annotate(
        media=Avg("valoracion"), partidos=Sum("minutos_jugados")
    ).filter(partidos__gte=10).order_by("-media").first()

    jugador_goleador = J.objects.get(pk=max_gol["jugador"])   if max_gol   else None
    jugador_mejor    = J.objects.get(pk=mejor_val["jugador"]) if mejor_val else None

    HistoricoTemporada.objects.create(
        liga=liga,
        temporada=liga.temporada,
        campeon=campeon,
        subcampeon=subcampeon,
        max_goleador=jugador_goleador,
        mejor_jugador=jugador_mejor,
        goles_max_goleador=max_gol["total"] if max_gol else 0,
        valoracion_mejor_jugador=mejor_val["media"] if mejor_val else None,
    )

    noticias_movimientos = []
    nivel_actual = liga.nivel

    # Los 3 últimos descienden (salvo League Two, nivel 4)
    if nivel_actual < 4:
        descendidos = [c.equipo for c in tabla[-3:]]
        liga_inferior = Liga.objects.filter(nivel=nivel_actual + 1).first()
        if liga_inferior:
            for eq in descendidos:
                eq.liga = liga_inferior
                eq.save()
                noticias_movimientos.append(f"{eq.nombre_corto} desciende a {liga_inferior.nombre}.")

    # Los 3 primeros ascienden (salvo Premier League, nivel 1)
    if nivel_actual > 1:
        ascendidos = [c.equipo for c in tabla[:3]]
        liga_superior = Liga.objects.filter(nivel=nivel_actual - 1).first()
        if liga_superior:
            for eq in ascendidos:
                eq.liga = liga_superior
                eq.save()
                noticias_movimientos.append(f"{eq.nombre_corto} asciende a {liga_superior.nombre}.")

    return {
        "campeon":              campeon,
        "noticias_movimientos": noticias_movimientos,
    }


def _regenerar_liga(liga, manager, contratos_procesados=False):
    """
    PASADA 2: limpia datos y genera calendario + clasificación nuevos.
    Se llama DESPUÉS de que TODAS las ligas hayan ejecutado _cerrar_temporada_liga,
    garantizando que cada liga tiene exactamente 20 equipos.
    """
    from .models import EstadisticaJugador
    from .models import Jugador as J
    from .models import Mercado
    import random as _r

    EstadisticaJugador.objects.filter(partido__jornada__liga=liga).delete()
    Partido.objects.filter(jornada__liga=liga).delete()
    Jornada.objects.filter(liga=liga).delete()
    Clasificacion.objects.filter(liga=liga).delete()

    # Curar lesiones de todos los equipos de esta liga
    J.objects.filter(equipo__liga=liga).update(lesionado=False, jornadas_baja=0)

    # Contratos del manager (solo si no se procesaron ya)
    if not contratos_procesados:
        jugadores_manager = list(J.objects.filter(equipo=manager.equipo))
        for jugador in jugadores_manager:
            jugador.temporadas_contrato -= 1
            if jugador.temporadas_contrato <= 0:
                otros_equipos = list(Equipo.objects.exclude(pk=manager.equipo.pk))
                if otros_equipos:
                    jugador.equipo = _r.choice(otros_equipos)
                jugador.temporadas_contrato = 0
                Mercado.objects.get_or_create(
                    jugador=jugador,
                    defaults={"liga": liga, "disponible": True, "dificultad_fichaje": 50}
                )
            jugador.save()

    liga.refresh_from_db()
    liga.temporada      = _calcular_nueva_temporada(liga.temporada)
    liga.jornada_actual = 1
    liga.jornadas_totales = 38
    liga.save()

    equipos = list(Equipo.objects.filter(liga=liga))
    _generar_calendario_premier(liga, equipos)
    Clasificacion.objects.bulk_create([
        Clasificacion(liga=liga, equipo=eq, posicion=i + 1)
        for i, eq in enumerate(equipos)
    ])


def _iniciar_nueva_temporada(liga, manager, contratos_procesados=False, crear_noticias=False):
    """
    Punto de entrada para cerrar la temporada cuando SOLO la liga del manager termina.
    Cuando todas las ligas terminan a la vez, usar el bloque de dos pasadas en seguir().
    """
    resultado = _cerrar_temporada_liga(liga)
    _regenerar_liga(liga, manager, contratos_procesados=contratos_procesados)

    from .models import Noticia
    if crear_noticias:
        Noticia.objects.filter(manager=manager).delete()
        campeon = resultado["campeon"]
        liga.refresh_from_db()
        Noticia.objects.create(
            manager=manager, tipo="GEN", jornada=1,
            texto=(
                f"Comienza la {liga.nombre} {liga.temporada}. "
                f"Campeón de la temporada anterior: {campeon.nombre_corto if campeon else 'desconocido'}."
            ),
        )
        for texto in resultado["noticias_movimientos"]:
            Noticia.objects.create(manager=manager, tipo="GEN", texto=texto, jornada=1)

def _generar_calendario_premier(liga, equipos):
    """
    Round-robin para exactamente 20 equipos.
    19 jornadas de ida (1-19) + 19 de vuelta (20-38).
    """
    n     = len(equipos)   # siempre 20
    mitad = n // 2
    fijos     = [equipos[0]]
    rotativos = list(equipos[1:])
    partidos_ida = []

    for ronda in range(n - 1):
        circulo = fijos + rotativos
        ronda_partidos = []
        for i in range(mitad):
            loc = circulo[i]
            vis = circulo[n - 1 - i]
            ronda_partidos.append((loc, vis) if ronda % 2 == 0 else (vis, loc))
        partidos_ida.append(ronda_partidos)
        rotativos = [rotativos[-1]] + rotativos[:-1]

    # Ida: jornadas 1 a 19
    for idx, rp in enumerate(partidos_ida):
        j = Jornada.objects.create(liga=liga, numero=idx + 1)
        Partido.objects.bulk_create([
            Partido(jornada=j, equipo_local=l, equipo_visitante=v, estadio=l.estadio)
            for l, v in rp
        ])

    # Vuelta: jornadas 20 a 38
    for idx, rp in enumerate(partidos_ida):
        j = Jornada.objects.create(liga=liga, numero=idx + 20)
        Partido.objects.bulk_create([
            Partido(jornada=j, equipo_local=v, equipo_visitante=l, estadio=v.estadio)
            for l, v in rp
        ])

# ══════════════════════════════════════════════════════════════════
#  RESET DEL JUEGO
# ══════════════════════════════════════════════════════════════════

def reset_juego(request):
    """Borra la sesión, resetea la BD y redirige al index como la primera vez."""
    from .models import (EstadisticaJugador, HistoricoTemporada,
                         Noticia, Mercado, HistorialFichaje, Renovacion)

    # Limpiar sesión
    request.session.flush()

    # Borrar todos los datos de juego (manager, partidos, stats, etc.)
    EstadisticaJugador.objects.all().delete()
    Noticia.objects.all().delete()
    Mercado.objects.all().delete()
    HistorialFichaje.objects.all().delete()
    HistoricoTemporada.objects.all().delete()
    Partido.objects.all().delete()
    Jornada.objects.all().delete()
    Clasificacion.objects.all().delete()
    Jugador.objects.all().delete()
    Manager.objects.all().delete()
    Equipo.objects.all().delete()
    Liga.objects.all().delete()

    # Repoblar la BD desde cero ejecutando el comando poblar_db
    from django.core.management import call_command
    call_command("poblar_db", verbosity=0)

    return redirect("index")

# ══════════════════════════════════════════════════════════════════
#  HELPERS PRIVADOS
# ══════════════════════════════════════════════════════════════════

def _get_manager(request):
    manager_id = request.session.get("manager_id")
    if not manager_id:
        return None
    try:
        return Manager.objects.select_related("equipo", "liga").get(pk=manager_id)
    except Manager.DoesNotExist:
        # Limpiar la sesión si el manager ya no existe en la BD
        del request.session["manager_id"]
        return None


def _max_goleador(equipo, liga):
    resultado = EstadisticaJugador.objects.filter(
        jugador__equipo=equipo,
        partido__jornada__liga=liga
    ).values(
        "jugador__id", "jugador__nombre", "jugador__apellidos", "jugador__posicion"
    ).annotate(
        total=Sum("goles")
    ).order_by("-total").first()
    return resultado


def _max_asistente(equipo, liga):
    resultado = EstadisticaJugador.objects.filter(
        jugador__equipo=equipo,
        partido__jornada__liga=liga
    ).values(
        "jugador__id", "jugador__nombre", "jugador__apellidos", "jugador__posicion"
    ).annotate(
        total=Sum("asistencias")
    ).order_by("-total").first()
    return resultado


def _mejor_valoracion(equipo, liga):
    resultado = EstadisticaJugador.objects.filter(
        jugador__equipo=equipo,
        partido__jornada__liga=liga,
        minutos_jugados__gt=0
    ).values(
        "jugador__id", "jugador__nombre", "jugador__apellidos", "jugador__posicion"
    ).annotate(
        media=Avg("valoracion")
    ).order_by("-media").first()
    return resultado


def _max_amarillas(equipo, liga):
    resultado = EstadisticaJugador.objects.filter(
        jugador__equipo=equipo,
        partido__jornada__liga=liga
    ).values(
        "jugador__id", "jugador__nombre", "jugador__apellidos", "jugador__posicion"
    ).annotate(
        total=Sum("tarjetas_amarillas")
    ).filter(total__gt=0).order_by("-total").first()
    return resultado


def _max_rojas(equipo, liga):
    resultado = EstadisticaJugador.objects.filter(
        jugador__equipo=equipo,
        partido__jornada__liga=liga
    ).values(
        "jugador__id", "jugador__nombre", "jugador__apellidos", "jugador__posicion"
    ).annotate(
        total=Sum("tarjetas_rojas")
    ).filter(total__gt=0).order_by("-total").first()
    return resultado


def _max_minutos(equipo, liga):
    resultado = EstadisticaJugador.objects.filter(
        jugador__equipo=equipo,
        partido__jornada__liga=liga
    ).values(
        "jugador__id", "jugador__nombre", "jugador__apellidos", "jugador__posicion"
    ).annotate(
        total=Sum("minutos_jugados")
    ).order_by("-total").first()
    return resultado


def _fecha_jornada(numero_jornada, temporada="2025-26"):
    """Calcula una fecha ficticia a partir de la jornada y la temporada."""
    from datetime import date, timedelta
    try:
        anio_inicio = int(temporada.split("-")[0])
    except (ValueError, IndexError):
        anio_inicio = 2025
    inicio = date(anio_inicio, 8, 9)
    return inicio + timedelta(weeks=numero_jornada - 1)


def _generar_mercado(liga):
    """
    Genera 50 jugadores disponibles en el mercado.
    Toma jugadores de TODOS los equipos (no solo de la liga del manager)
    para tener variedad de nivel. Excluye jugadores del equipo del manager
    (eso se filtra en la vista).
    """
    import random
    Mercado.objects.filter(liga=liga).delete()
    # Tomar jugadores de todas las ligas para tener variedad
    todos = list(Jugador.objects.select_related("equipo").all())
    random.shuffle(todos)
    seleccionados = todos[:50]
    Mercado.objects.bulk_create([
        Mercado(jugador=j, liga=liga, disponible=True, dificultad_fichaje=50)
        for j in seleccionados
    ])

def _calcular_nueva_temporada(temporada_actual):
    """
    '2025-26' → '2026-27'
    '2026-27' → '2027-28'
    '2029-30' → '2030-31'  (maneja el cambio de siglo correctamente)
    """
    try:
        anio = int(temporada_actual.split("-")[0])
        anio_fin = anio + 2
        return f"{anio + 1}-{str(anio_fin)[-2:]}"
    except (ValueError, IndexError):
        return temporada_actual + "+"

def aviso_legal(request):
    return render(request, "core/aviso_legal.html")