from django.urls import path
from core import views

urlpatterns = [
    path("",               views.index,            name="index"),
    path("dashboard/",     views.dashboard,         name="dashboard"),
    path("seguir/",        views.seguir,            name="seguir"),
    path("plantilla/",     views.plantilla,         name="plantilla"),
    path("clasificacion/", views.clasificacion,     name="clasificacion"),
    path("estadisticas/",  views.estadisticas,      name="estadisticas"),
    path("resultados/",    views.resultados,        name="resultados"),
    path("fichajes/",      views.mercado_fichajes,  name="mercado_fichajes"),
    path("historico/",     views.historico,         name="historico"),
    path("renovar/<int:jugador_id>/",  views.renovar_jugador,  name="renovar_jugador"),
    path("despedir/<int:jugador_id>/", views.despedir_jugador, name="despedir_jugador"),
    path("noticia/<int:noticia_id>/borrar/", views.borrar_noticia, name="borrar_noticia"),
    path("fichaje/<int:oferta_id>/fichar/",  views.fichar_jugador, name="fichar_jugador"),
    path("reset/", views.reset_juego, name="reset_juego"),
    path("aviso-legal/", views.aviso_legal, name="aviso_legal"),
]
