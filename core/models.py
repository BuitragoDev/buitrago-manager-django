from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# ══════════════════════════════════════════════════════════════════
#  LIGA
# ══════════════════════════════════════════════════════════════════

class Liga(models.Model):
    nombre          = models.CharField(max_length=100)          # "La Liga EA Sports"
    temporada       = models.CharField(max_length=20)           # "2024-25"
    jornadas_totales = models.PositiveSmallIntegerField(default=38)
    jornada_actual  = models.PositiveSmallIntegerField(default=1)
    nivel           = models.PositiveSmallIntegerField(default=1)  # 1=Premier, 2=Championship, 3=League One, 4=League Two

    def __str__(self):
        return f"{self.nombre} · {self.temporada}"

    class Meta:
        verbose_name = "Liga"
        verbose_name_plural = "Ligas"


# ══════════════════════════════════════════════════════════════════
#  EQUIPO
# ══════════════════════════════════════════════════════════════════

class Equipo(models.Model):
    liga            = models.ForeignKey(Liga, on_delete=models.CASCADE, related_name="equipos")
    nombre          = models.CharField(max_length=100)
    nombre_corto    = models.CharField(max_length=30)           # "Atlético Madrid"
    abreviatura     = models.CharField(max_length=4)            # "ATM"
    ciudad          = models.CharField(max_length=80)
    estadio         = models.CharField(max_length=100)
    capacidad_estadio = models.PositiveIntegerField(default=30000)
    color_principal = models.CharField(max_length=7, default="#FFFFFF")   # hex
    color_secundario = models.CharField(max_length=7, default="#000000")  # hex
    presupuesto_fichajes = models.PositiveIntegerField(default=10_000_000)  # en euros

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ["nombre"]


# ══════════════════════════════════════════════════════════════════
#  JUGADOR
# ══════════════════════════════════════════════════════════════════

class Jugador(models.Model):

    class Posicion(models.TextChoices):
        PORTERO        = "POR", "Portero"
        DEFENSA        = "DEF", "Defensa"
        CENTROCAMPISTA = "MED", "Centrocampista"
        DELANTERO      = "DEL", "Delantero"

    class Pie(models.TextChoices):
        DERECHO   = "D", "Derecho"
        IZQUIERDO = "I", "Izquierdo"
        AMBOS     = "A", "Ambidiestro"

    # Datos personales
    nombre         = models.CharField(max_length=80)
    apellidos      = models.CharField(max_length=80)
    nacionalidad   = models.CharField(max_length=60)
    edad           = models.PositiveSmallIntegerField(
                        validators=[MinValueValidator(15), MaxValueValidator(45)])
    posicion       = models.CharField(max_length=3, choices=Posicion.choices)
    pie_dominante  = models.CharField(max_length=1, choices=Pie.choices, default=Pie.DERECHO)
    dorsal         = models.PositiveSmallIntegerField(
                        null=True, blank=True,
                        validators=[MinValueValidator(1), MaxValueValidator(99)])

    # Equipo actual (null si libre o en mercado sin equipo)
    equipo         = models.ForeignKey(
                        Equipo, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name="jugadores")

    # ── Atributos técnicos (1-100) ─────────────────────────────
    velocidad      = models.PositiveSmallIntegerField(default=50,
                        validators=[MinValueValidator(1), MaxValueValidator(100)])
    regate         = models.PositiveSmallIntegerField(default=50,
                        validators=[MinValueValidator(1), MaxValueValidator(100)])
    disparo        = models.PositiveSmallIntegerField(default=50,
                        validators=[MinValueValidator(1), MaxValueValidator(100)])
    pase           = models.PositiveSmallIntegerField(default=50,
                        validators=[MinValueValidator(1), MaxValueValidator(100)])
    defensa        = models.PositiveSmallIntegerField(default=50,
                        validators=[MinValueValidator(1), MaxValueValidator(100)])
    fisico         = models.PositiveSmallIntegerField(default=50,
                        validators=[MinValueValidator(1), MaxValueValidator(100)])
    # Específico porteros (ignorado en cálculo de medias si no es portero)
    porteria       = models.PositiveSmallIntegerField(default=50,
                        validators=[MinValueValidator(1), MaxValueValidator(100)])

    # ── Contrato ───────────────────────────────────────────────
    salario        = models.PositiveIntegerField(default=500_000)   # euros/año
    temporadas_contrato = models.PositiveSmallIntegerField(default=2)

    # ── Estado ────────────────────────────────────────────────
    lesionado      = models.BooleanField(default=False)
    jornadas_baja  = models.PositiveSmallIntegerField(default=0)

    # ── Propiedad: valoración media calculada ──────────────────
    @property
    def valoracion_media(self):
        if self.posicion == self.Posicion.PORTERO:
            atributos = [self.porteria, self.fisico, self.pase, self.velocidad]
        elif self.posicion == self.Posicion.DEFENSA:
            atributos = [self.defensa, self.fisico, self.velocidad, self.pase, self.disparo]
        elif self.posicion == self.Posicion.CENTROCAMPISTA:
            atributos = [self.pase, self.regate, self.fisico, self.velocidad, self.disparo, self.defensa]
        else:  # Delantero
            atributos = [self.disparo, self.velocidad, self.regate, self.pase, self.fisico]
        return round(sum(atributos) / len(atributos), 1)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}"

    def __str__(self):
        return f"{self.nombre_completo} ({self.posicion}) — {self.equipo}"

    class Meta:
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"
        ordering = ["apellidos", "nombre"]


# ══════════════════════════════════════════════════════════════════
#  MANAGER  (el usuario humano)
# ══════════════════════════════════════════════════════════════════

class Manager(models.Model):
    nombre         = models.CharField(max_length=80)
    equipo         = models.OneToOneField(
                        Equipo, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name="manager")
    liga           = models.ForeignKey(
                        Liga, on_delete=models.CASCADE, related_name="managers")
    temporada_inicio = models.CharField(max_length=20)          # "2024-25"
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} → {self.equipo}"

    class Meta:
        verbose_name = "Mánager"
        verbose_name_plural = "Mánagers"


# ══════════════════════════════════════════════════════════════════
#  JORNADA
# ══════════════════════════════════════════════════════════════════

class Jornada(models.Model):
    liga           = models.ForeignKey(Liga, on_delete=models.CASCADE, related_name="jornadas")
    numero         = models.PositiveSmallIntegerField()
    disputada      = models.BooleanField(default=False)
    fecha_simulada = models.DateField(null=True, blank=True)    # fecha ficticia del juego

    def __str__(self):
        return f"Jornada {self.numero} — {self.liga}"

    class Meta:
        verbose_name = "Jornada"
        verbose_name_plural = "Jornadas"
        ordering = ["liga", "numero"]
        unique_together = ("liga", "numero")


# ══════════════════════════════════════════════════════════════════
#  PARTIDO
# ══════════════════════════════════════════════════════════════════

class Partido(models.Model):
    jornada        = models.ForeignKey(Jornada, on_delete=models.CASCADE, related_name="partidos")
    equipo_local   = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="partidos_local")
    equipo_visitante = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="partidos_visitante")
    estadio        = models.CharField(max_length=100, blank=True)
    asistencia     = models.PositiveIntegerField(default=0)

    # Se rellenan al simular
    goles_local     = models.PositiveSmallIntegerField(null=True, blank=True)
    goles_visitante = models.PositiveSmallIntegerField(null=True, blank=True)
    jugado          = models.BooleanField(default=False)

    # ── Propiedades de resultado ───────────────────────────────
    @property
    def resultado(self):
        if not self.jugado:
            return None
        return f"{self.goles_local} - {self.goles_visitante}"

    def resultado_para_equipo(self, equipo):
        """Devuelve 'V', 'E' o 'D' desde la perspectiva del equipo dado."""
        if not self.jugado:
            return None
        if equipo == self.equipo_local:
            g_favor, g_contra = self.goles_local, self.goles_visitante
        else:
            g_favor, g_contra = self.goles_visitante, self.goles_local
        if g_favor > g_contra:
            return "V"
        elif g_favor == g_contra:
            return "E"
        return "D"

    def __str__(self):
        base = f"[J{self.jornada.numero}] {self.equipo_local} vs {self.equipo_visitante}"
        if self.jugado:
            return f"{base} ({self.resultado})"
        return base

    class Meta:
        verbose_name = "Partido"
        verbose_name_plural = "Partidos"
        ordering = ["jornada__numero"]


# ══════════════════════════════════════════════════════════════════
#  CLASIFICACIÓN
# ══════════════════════════════════════════════════════════════════

class Clasificacion(models.Model):
    liga           = models.ForeignKey(Liga, on_delete=models.CASCADE, related_name="clasificacion")
    equipo         = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="clasificacion")
    posicion       = models.PositiveSmallIntegerField(default=0)

    # Estadísticas acumuladas
    partidos_jugados  = models.PositiveSmallIntegerField(default=0)
    partidos_ganados  = models.PositiveSmallIntegerField(default=0)
    partidos_empatados = models.PositiveSmallIntegerField(default=0)
    partidos_perdidos = models.PositiveSmallIntegerField(default=0)
    goles_favor       = models.PositiveSmallIntegerField(default=0)
    goles_contra      = models.PositiveSmallIntegerField(default=0)
    puntos            = models.PositiveSmallIntegerField(default=0)

    @property
    def diferencia_goles(self):
        return self.goles_favor - self.goles_contra

    def recalcular(self):
        """Recalcula todos los campos a partir de los partidos jugados."""
        partidos = Partido.objects.filter(
            jugado=True,
            jornada__liga=self.liga
        ).filter(
            models.Q(equipo_local=self.equipo) | models.Q(equipo_visitante=self.equipo)
        )

        pj = pg = pe = pp = gf = gc = pts = 0

        for p in partidos:
            if p.equipo_local == self.equipo:
                gf += p.goles_local
                gc += p.goles_visitante
                if p.goles_local > p.goles_visitante:
                    pg += 1; pts += 3
                elif p.goles_local == p.goles_visitante:
                    pe += 1; pts += 1
                else:
                    pp += 1
            else:
                gf += p.goles_visitante
                gc += p.goles_local
                if p.goles_visitante > p.goles_local:
                    pg += 1; pts += 3
                elif p.goles_visitante == p.goles_local:
                    pe += 1; pts += 1
                else:
                    pp += 1
            pj += 1

        self.partidos_jugados   = pj
        self.partidos_ganados   = pg
        self.partidos_empatados = pe
        self.partidos_perdidos  = pp
        self.goles_favor        = gf
        self.goles_contra       = gc
        self.puntos             = pts
        self.save()

    def __str__(self):
        return f"{self.equipo} — {self.puntos} pts"

    class Meta:
        verbose_name = "Clasificación"
        verbose_name_plural = "Clasificaciones"
        ordering = ["-puntos", "-goles_favor", "goles_contra"]
        unique_together = ("liga", "equipo")


# ══════════════════════════════════════════════════════════════════
#  ESTADÍSTICA DE JUGADOR POR PARTIDO
# ══════════════════════════════════════════════════════════════════

class EstadisticaJugador(models.Model):
    jugador        = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name="estadisticas")
    partido        = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name="estadisticas")

    # Rendimiento en el partido
    minutos_jugados   = models.PositiveSmallIntegerField(default=0)
    goles             = models.PositiveSmallIntegerField(default=0)
    asistencias       = models.PositiveSmallIntegerField(default=0)
    tarjetas_amarillas = models.PositiveSmallIntegerField(default=0,
                            validators=[MaxValueValidator(2)])
    tarjetas_rojas = models.PositiveSmallIntegerField(default=0)
    valoracion        = models.DecimalField(
                            max_digits=3, decimal_places=1, default=5.0,
                            validators=[MinValueValidator(1.0), MaxValueValidator(10.0)])

    def __str__(self):
        return f"{self.jugador.nombre_completo} · {self.partido} · {self.valoracion}★"

    class Meta:
        verbose_name = "Estadística de Jugador"
        verbose_name_plural = "Estadísticas de Jugadores"
        unique_together = ("jugador", "partido")


# ══════════════════════════════════════════════════════════════════
#  MERCADO DE FICHAJES
# ══════════════════════════════════════════════════════════════════

class Mercado(models.Model):
    """
    Lista de jugadores disponibles para fichar en cada ventana.
    Se regenera aleatoriamente cuando el manager abre la pantalla de fichajes.
    """
    jugador           = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name="ofertas_mercado")
    liga              = models.ForeignKey(Liga, on_delete=models.CASCADE, related_name="mercado")
    disponible        = models.BooleanField(default=True)
    # 1 = muy fácil de fichar, 100 = casi imposible
    dificultad_fichaje = models.PositiveSmallIntegerField(
                            default=50,
                            validators=[MinValueValidator(1), MaxValueValidator(100)])
    fecha_expiracion  = models.PositiveSmallIntegerField(
                            help_text="Jornada en la que esta oferta expira",
                            null=True, blank=True)

    def __str__(self):
        return f"{self.jugador.nombre_completo} (dificultad: {self.dificultad_fichaje})"

    class Meta:
        verbose_name = "Oferta de Mercado"
        verbose_name_plural = "Mercado de Fichajes"


# ══════════════════════════════════════════════════════════════════
#  HISTORIAL DE FICHAJES
# ══════════════════════════════════════════════════════════════════

class HistorialFichaje(models.Model):
    """Registra cada fichaje o venta realizada por el manager."""

    class TipoMovimiento(models.TextChoices):
        FICHAJE = "F", "Fichaje"
        VENTA   = "V", "Venta"
        CESION  = "C", "Cesión"
        LIBRE   = "L", "Agente libre"

    manager          = models.ForeignKey(Manager, on_delete=models.CASCADE, related_name="fichajes")
    jugador          = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name="historial_fichajes")
    equipo_origen    = models.ForeignKey(Equipo, on_delete=models.SET_NULL,
                            null=True, blank=True, related_name="traspasos_salida")
    equipo_destino   = models.ForeignKey(Equipo, on_delete=models.SET_NULL,
                            null=True, blank=True, related_name="traspasos_entrada")
    tipo             = models.CharField(max_length=1, choices=TipoMovimiento.choices, default=TipoMovimiento.FICHAJE)
    jornada          = models.PositiveSmallIntegerField()
    temporada        = models.CharField(max_length=20)
    exito            = models.BooleanField(default=True)  # False si el intento de fichaje falló

    def __str__(self):
        return f"{self.tipo} · {self.jugador.nombre_completo} → {self.equipo_destino} (J{self.jornada})"

    class Meta:
        verbose_name = "Historial de Fichaje"
        verbose_name_plural = "Historial de Fichajes"
        ordering = ["-jornada"]


# ══════════════════════════════════════════════════════════════════
#  RENOVACIONES
# ══════════════════════════════════════════════════════════════════

class Renovacion(models.Model):
    """Registra cada renovación de contrato realizada."""
    manager          = models.ForeignKey(Manager, on_delete=models.CASCADE, related_name="renovaciones")
    jugador          = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name="renovaciones")
    temporadas_nuevas = models.PositiveSmallIntegerField(default=2)
    nuevo_salario    = models.PositiveIntegerField()
    jornada          = models.PositiveSmallIntegerField()
    temporada        = models.CharField(max_length=20)

    def __str__(self):
        return f"Renovación · {self.jugador.nombre_completo} · {self.temporadas_nuevas} años"

    class Meta:
        verbose_name = "Renovación"
        verbose_name_plural = "Renovaciones"
        ordering = ["-jornada"]


# ══════════════════════════════════════════════════════════════════
#  NOTICIAS / MENSAJES
# ══════════════════════════════════════════════════════════════════

class Noticia(models.Model):

    class TipoNoticia(models.TextChoices):
        RESULTADO = "RES", "Resultado"
        FICHAJE   = "FIC", "Fichaje"
        LESION    = "LES", "Lesión"
        RENOVACION = "REN", "Renovación"
        GENERAL   = "GEN", "General"

    manager    = models.ForeignKey(Manager, on_delete=models.CASCADE, related_name="noticias")
    tipo       = models.CharField(max_length=3, choices=TipoNoticia.choices, default=TipoNoticia.GENERAL)
    texto      = models.TextField()
    jornada    = models.PositiveSmallIntegerField()
    fecha_juego = models.DateField(null=True, blank=True)   # fecha ficticia del juego
    creada_en  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.tipo}] J{self.jornada} · {self.texto[:60]}"

    class Meta:
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"
        ordering = ["-jornada", "-creada_en"]

# ══════════════════════════════════════════════════════════════════
#  HISTÓRICO TEMPORADAS
# ══════════════════════════════════════════════════════════════════

class HistoricoTemporada(models.Model):
    """
    Guarda el palmarés de cada temporada finalizada.
    Se crea automáticamente al iniciar una nueva temporada.
    """
    liga       = models.ForeignKey(Liga, on_delete=models.CASCADE, related_name="historico")
    temporada  = models.CharField(max_length=10)  # ej. "2025-26"

    campeon    = models.ForeignKey(
        Equipo, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="temporadas_campeon"
    )
    subcampeon = models.ForeignKey(
        Equipo, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="temporadas_subcampeon"
    )
    max_goleador = models.ForeignKey(
        "Jugador", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="temporadas_goleador"
    )
    mejor_jugador = models.ForeignKey(
        "Jugador", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="temporadas_mejor"
    )
    goles_max_goleador       = models.PositiveIntegerField(default=0)
    valoracion_mejor_jugador = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ["-temporada"]
        verbose_name = "Histórico de Temporada"
        verbose_name_plural = "Histórico de Temporadas"

    def __str__(self):
        return f"{self.liga.nombre} {self.temporada}"