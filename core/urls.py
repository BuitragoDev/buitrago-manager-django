from django.urls import path
from . import views

urlpatterns = [
    # ── Inicio y dashboard ──────────────────────────────────
    path("",              views.index,     name="index"),
    path("dashboard/",    views.dashboard, name="dashboard"),

    # ── Acción principal ────────────────────────────────────
    path("seguir/",       views.seguir,    name="seguir"),
    path("jornada/",       views.jornada_resultado,   name="jornada_resultado"),

    # ── Secciones del juego ─────────────────────────────────
    path("plantilla/",    views.plantilla,    name="plantilla"),
    path("clasificacion/",views.clasificacion,name="clasificacion"),
    path("estadisticas/", views.estadisticas, name="estadisticas"),
    path("resultados/",   views.resultados,   name="resultados"),
    path("fichajes/",     views.mercado_fichajes, name="mercado_fichajes"),
    path("historico/", views.historico, name="historico"),
    path("reset/", views.reset_juego, name="reset_juego"),
    path("renovar/<int:jugador_id>/", views.renovar_jugador, name="renovar_jugador"),
    path("despedir/<int:jugador_id>/", views.despedir_jugador, name="despedir_jugador"),
    path("aviso-legal/", views.aviso_legal, name="aviso_legal"),

    # ── Acciones AJAX ───────────────────────────────────────
    path("noticia/<int:noticia_id>/borrar/", views.borrar_noticia,  name="borrar_noticia"),
    path("jugador/<int:jugador_id>/renovar/",views.renovar_jugador, name="renovar_jugador"),
    path("fichaje/<int:oferta_id>/fichar/",  views.fichar_jugador,  name="fichar_jugador"),
]