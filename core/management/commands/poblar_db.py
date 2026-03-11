import random
from django.core.management.base import BaseCommand
from core.models import Liga, Equipo, Jugador, Clasificacion, Jornada, Partido


EQUIPOS_PREMIER = [
    {"nombre": "Arsenal FC",                  "nombre_corto": "Arsenal",       "abreviatura": "ARS", "ciudad": "Londres",        "estadio": "Emirates Stadium",          "capacidad_estadio": 60704, "color_principal": "#EF0107", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 90_000_000,  "nivel": 88},
    {"nombre": "Aston Villa FC",              "nombre_corto": "Aston Villa",   "abreviatura": "AVL", "ciudad": "Birmingham",     "estadio": "Villa Park",                "capacidad_estadio": 42785, "color_principal": "#95BFE5", "color_secundario": "#670E36", "presupuesto_fichajes": 55_000_000,  "nivel": 80},
    {"nombre": "AFC Bournemouth",             "nombre_corto": "Bournemouth",   "abreviatura": "BOU", "ciudad": "Bournemouth",    "estadio": "Vitality Stadium",          "capacidad_estadio": 11307, "color_principal": "#DA291C", "color_secundario": "#000000", "presupuesto_fichajes": 20_000_000,  "nivel": 65},
    {"nombre": "Brentford FC",               "nombre_corto": "Brentford",     "abreviatura": "BRE", "ciudad": "Londres",        "estadio": "Gtech Community Stadium",   "capacidad_estadio": 17250, "color_principal": "#D20000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 22_000_000,  "nivel": 67},
    {"nombre": "Brighton & Hove Albion",     "nombre_corto": "Brighton",      "abreviatura": "BHA", "ciudad": "Brighton",       "estadio": "Amex Stadium",              "capacidad_estadio": 31800, "color_principal": "#0057B8", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 40_000_000,  "nivel": 74},
    {"nombre": "Chelsea FC",                 "nombre_corto": "Chelsea",       "abreviatura": "CHE", "ciudad": "Londres",        "estadio": "Stamford Bridge",           "capacidad_estadio": 40341, "color_principal": "#034694", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 100_000_000, "nivel": 83},
    {"nombre": "Crystal Palace FC",          "nombre_corto": "Crystal Palace","abreviatura": "CRY", "ciudad": "Londres",        "estadio": "Selhurst Park",             "capacidad_estadio": 25486, "color_principal": "#1B458F", "color_secundario": "#C4122E", "presupuesto_fichajes": 18_000_000,  "nivel": 64},
    {"nombre": "Everton FC",                 "nombre_corto": "Everton",       "abreviatura": "EVE", "ciudad": "Liverpool",      "estadio": "Goodison Park",             "capacidad_estadio": 39414, "color_principal": "#003399", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 20_000_000,  "nivel": 63},
    {"nombre": "Fulham FC",                  "nombre_corto": "Fulham",        "abreviatura": "FUL", "ciudad": "Londres",        "estadio": "Craven Cottage",            "capacidad_estadio": 25700, "color_principal": "#FFFFFF", "color_secundario": "#000000", "presupuesto_fichajes": 22_000_000,  "nivel": 66},
    {"nombre": "Ipswich Town FC",            "nombre_corto": "Ipswich",       "abreviatura": "IPS", "ciudad": "Ipswich",        "estadio": "Portman Road",              "capacidad_estadio": 29312, "color_principal": "#0044A9", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 15_000_000,  "nivel": 60},
    {"nombre": "Leicester City FC",          "nombre_corto": "Leicester",     "abreviatura": "LEI", "ciudad": "Leicester",      "estadio": "King Power Stadium",        "capacidad_estadio": 32261, "color_principal": "#003090", "color_secundario": "#FDBE11", "presupuesto_fichajes": 18_000_000,  "nivel": 62},
    {"nombre": "Liverpool FC",               "nombre_corto": "Liverpool",     "abreviatura": "LIV", "ciudad": "Liverpool",      "estadio": "Anfield",                   "capacidad_estadio": 61276, "color_principal": "#C8102E", "color_secundario": "#F6EB61", "presupuesto_fichajes": 95_000_000,  "nivel": 90},
    {"nombre": "Manchester City FC",         "nombre_corto": "Man. City",     "abreviatura": "MCI", "ciudad": "Manchester",     "estadio": "Etihad Stadium",            "capacidad_estadio": 53400, "color_principal": "#6CABDD", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 110_000_000, "nivel": 91},
    {"nombre": "Manchester United FC",       "nombre_corto": "Man. United",   "abreviatura": "MUN", "ciudad": "Manchester",     "estadio": "Old Trafford",              "capacidad_estadio": 74310, "color_principal": "#DA291C", "color_secundario": "#FBE122", "presupuesto_fichajes": 85_000_000,  "nivel": 82},
    {"nombre": "Newcastle United FC",        "nombre_corto": "Newcastle",     "abreviatura": "NEW", "ciudad": "Newcastle",      "estadio": "St. James Park",            "capacidad_estadio": 52305, "color_principal": "#241F20", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 70_000_000,  "nivel": 81},
    {"nombre": "Nottingham Forest FC",       "nombre_corto": "Nottingham Forest", "abreviatura": "NFO", "ciudad": "Nottingham",     "estadio": "City Ground",               "capacidad_estadio": 30332, "color_principal": "#DD0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 25_000_000,  "nivel": 68},
    {"nombre": "Southampton FC",             "nombre_corto": "Southampton",   "abreviatura": "SOU", "ciudad": "Southampton",    "estadio": "St. Mary's Stadium",        "capacidad_estadio": 32384, "color_principal": "#D71920", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 14_000_000,  "nivel": 59},
    {"nombre": "Tottenham Hotspur FC",       "nombre_corto": "Tottenham",     "abreviatura": "TOT", "ciudad": "Londres",        "estadio": "Tottenham Hotspur Stadium", "capacidad_estadio": 62850, "color_principal": "#132257", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 75_000_000,  "nivel": 84},
    {"nombre": "West Ham United FC",         "nombre_corto": "West Ham",      "abreviatura": "WHU", "ciudad": "Londres",        "estadio": "London Stadium",            "capacidad_estadio": 62500, "color_principal": "#7A263A", "color_secundario": "#1BB1E7", "presupuesto_fichajes": 30_000_000,  "nivel": 69},
    {"nombre": "Wolverhampton Wanderers FC", "nombre_corto": "Wolves",        "abreviatura": "WOL", "ciudad": "Wolverhampton",  "estadio": "Molineux Stadium",          "capacidad_estadio": 32050, "color_principal": "#FDB913", "color_secundario": "#231F20", "presupuesto_fichajes": 20_000_000,  "nivel": 63},
]

EQUIPOS_DIVISION = [
    {"nombre": "Leeds United FC",      "nombre_corto": "Leeds",         "abreviatura": "LEE", "ciudad": "Leeds",          "estadio": "Elland Road",                     "capacidad_estadio": 37792, "color_principal": "#FFCD00", "color_secundario": "#1D428A", "presupuesto_fichajes": 12_000_000, "nivel": 58},
    {"nombre": "Burnley FC",           "nombre_corto": "Burnley",       "abreviatura": "BUR", "ciudad": "Burnley",        "estadio": "Turf Moor",                       "capacidad_estadio": 21944, "color_principal": "#6C1D45", "color_secundario": "#99D6EA", "presupuesto_fichajes": 10_000_000, "nivel": 55},
    {"nombre": "Sheffield United FC",  "nombre_corto": "Sheffield Utd", "abreviatura": "SHU", "ciudad": "Sheffield",      "estadio": "Bramall Lane",                    "capacidad_estadio": 32125, "color_principal": "#EE2737", "color_secundario": "#000000", "presupuesto_fichajes": 10_000_000, "nivel": 56},
    {"nombre": "Middlesbrough FC",     "nombre_corto": "Middlesbrough", "abreviatura": "MID", "ciudad": "Middlesbrough",  "estadio": "Riverside Stadium",               "capacidad_estadio": 34742, "color_principal": "#EF3B33", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 9_000_000,  "nivel": 54},
    {"nombre": "Coventry City FC",     "nombre_corto": "Coventry",      "abreviatura": "COV", "ciudad": "Coventry",       "estadio": "Coventry Building Society Arena", "capacidad_estadio": 32609, "color_principal": "#59CBFF", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 8_000_000,  "nivel": 53},
    {"nombre": "Millwall FC",          "nombre_corto": "Millwall",      "abreviatura": "MIL", "ciudad": "Londres",        "estadio": "The Den",                         "capacidad_estadio": 20146, "color_principal": "#001D5E", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 7_000_000,  "nivel": 52},
    {"nombre": "Preston North End FC", "nombre_corto": "Preston",       "abreviatura": "PRE", "ciudad": "Preston",        "estadio": "Deepdale",                        "capacidad_estadio": 23404, "color_principal": "#FFFFFF", "color_secundario": "#002D62", "presupuesto_fichajes": 7_000_000,  "nivel": 51},
    {"nombre": "Queens Park Rangers",  "nombre_corto": "QPR",           "abreviatura": "QPR", "ciudad": "Londres",        "estadio": "Loftus Road",                     "capacidad_estadio": 18360, "color_principal": "#005CAB", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 8_000_000,  "nivel": 53},
    {"nombre": "Stoke City FC",        "nombre_corto": "Stoke",         "abreviatura": "STK", "ciudad": "Stoke-on-Trent", "estadio": "Bet365 Stadium",                  "capacidad_estadio": 30089, "color_principal": "#E03A3E", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 8_000_000,  "nivel": 52},
    {"nombre": "Watford FC",           "nombre_corto": "Watford",       "abreviatura": "WAT", "ciudad": "Watford",        "estadio": "Vicarage Road",                   "capacidad_estadio": 22200, "color_principal": "#FBEE23", "color_secundario": "#ED2127", "presupuesto_fichajes": 9_000_000,  "nivel": 54},
]

NOMBRES = ["James","Oliver","Harry","Jack","George","Noah","Liam","Ethan","Lucas","Mason",
           "Logan","Aiden","Elijah","Ryan","Nathan","Dylan","Tyler","Connor","Jordan","Marcus",
           "Kai","Zion","Andre","Leon","Malik","Carlos","Diego","Pablo","Mateo","Sergio",
           "Ivan","Alexei","Mohamed","Yusuf","Amadou","Sadio","Ismaila","Lautaro","Emre","Kerem"]
APELLIDOS = ["Smith","Jones","Williams","Brown","Taylor","Davies","Evans","Wilson","Thomas","Roberts",
             "Johnson","White","Walker","Hall","Wright","Green","Hughes","Lewis","Harris","Clarke",
             "Martinez","Garcia","Fernandez","Lopez","Diaz","Silva","Costa","Santos","Oliveira","Pereira",
             "Muller","Schmidt","Fischer","Weber","Becker","Diallo","Traore","Camara","Keita","Nkunku",
             "Tchouameni","Bellingham","Saka","Rashford","Foden","Palmer","Gordon","Mbeumo","Watkins","Salah"]
NACIONALIDADES = ["Ingles","Espanol","Frances","Aleman","Brasileno","Argentino","Portugues",
                  "Holandes","Belga","Italiano","Senegales","Nigeriano","Turco","Noruego","Escoces"]

ESTRUCTURA_PLANTILLA = [("POR", 2), ("DEF", 7), ("MED", 7), ("DEL", 4)]
DORSALES = {"POR": [1,13], "DEF": [2,3,4,5,6,12,18], "MED": [7,8,10,11,14,15,16], "DEL": [9,17,19,20]}


def generar_atributos(posicion, nivel, es_titular=True):
    base = nivel if es_titular else nivel - random.randint(8, 18)
    base = max(base, 35)
    def attr(offset=0): return max(1, min(99, base + offset + random.randint(-8, 8)))
    if posicion == "POR":
        return {"velocidad": attr(-15), "regate": attr(-20), "disparo": attr(-25), "pase": attr(-5), "defensa": attr(-10), "fisico": attr(-5), "porteria": attr(+10)}
    elif posicion == "DEF":
        return {"velocidad": attr(-5), "regate": attr(-15), "disparo": attr(-15), "pase": attr(-5), "defensa": attr(+10), "fisico": attr(+5), "porteria": attr(-40)}
    elif posicion == "MED":
        return {"velocidad": attr(0), "regate": attr(+5), "disparo": attr(-5), "pase": attr(+10), "defensa": attr(-5), "fisico": attr(0), "porteria": attr(-40)}
    else:
        return {"velocidad": attr(+5), "regate": attr(+8), "disparo": attr(+10), "pase": attr(-5), "defensa": attr(-20), "fisico": attr(0), "porteria": attr(-40)}


def generar_plantilla(equipo, nivel):
    jugadores = []
    dc = {pos: 0 for pos in ["POR","DEF","MED","DEL"]}
    for pos, cantidad in ESTRUCTURA_PLANTILLA:
        for i in range(cantidad):
            es_titular = i < (1 if pos == "POR" else cantidad // 2 + 1)
            dorsal = DORSALES[pos][dc[pos]] if dc[pos] < len(DORSALES[pos]) else None
            dc[pos] += 1
            jugadores.append(Jugador(
                nombre=random.choice(NOMBRES), apellidos=random.choice(APELLIDOS),
                nacionalidad=random.choice(NACIONALIDADES), edad=random.randint(18, 35),
                posicion=pos, pie_dominante=random.choice(["D","D","D","I","A"]),
                dorsal=dorsal, equipo=equipo,
                salario=random.randint(200_000, 8_000_000) if es_titular else random.randint(80_000, 500_000),
                temporadas_contrato=random.randint(1, 4),
                **generar_atributos(pos, nivel, es_titular),
            ))
    return jugadores


def generar_calendario_premier(liga, equipos):
    """
    Round-robin para exactamente 20 equipos → 38 jornadas, 10 partidos/jornada.
    Vuelta empieza en jornada 20.
    """
    n     = 20
    mitad = 10
    fijos     = [equipos[0]]
    rotativos = list(equipos[1:])   # 19 equipos rotativos
    partidos_ida = []

    for ronda in range(19):         # 19 rondas de ida
        circulo = fijos + rotativos
        ronda_partidos = []
        for i in range(mitad):
            loc = circulo[i]
            vis = circulo[n - 1 - i]
            ronda_partidos.append((loc, vis) if ronda % 2 == 0 else (vis, loc))
        partidos_ida.append(ronda_partidos)
        rotativos = [rotativos[-1]] + rotativos[:-1]

    # Guardar ida (jornadas 1-19)
    for idx, rp in enumerate(partidos_ida):
        j = Jornada.objects.create(liga=liga, numero=idx + 1)
        Partido.objects.bulk_create([
            Partido(jornada=j, equipo_local=l, equipo_visitante=v, estadio=l.estadio)
            for l, v in rp
        ])

    # Guardar vuelta (jornadas 20-38), invirtiendo local/visitante
    for idx, rp in enumerate(partidos_ida):
        j = Jornada.objects.create(liga=liga, numero=idx + 20)
        Partido.objects.bulk_create([
            Partido(jornada=j, equipo_local=v, equipo_visitante=l, estadio=v.estadio)
            for l, v in rp
        ])


class Command(BaseCommand):
    help = "Pobla la BD con Premier League + Division Inferior 2025/26"

    def handle(self, *args, **kwargs):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  FUTMASTER — Inicializando temporada 2025/26")
        self.stdout.write("=" * 60 + "\n")

        # Limpiar todo
        self.stdout.write("Limpiando datos anteriores...")
        Partido.objects.all().delete()
        Jornada.objects.all().delete()
        Clasificacion.objects.all().delete()
        Jugador.objects.all().delete()
        Equipo.objects.all().delete()
        Liga.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("   OK\n"))

        # ── PREMIER LEAGUE ────────────────────────────────────
        self.stdout.write("Creando Premier League (20 equipos)...")
        premier = Liga.objects.create(
            nombre="Premier League", temporada="2025-26",
            jornadas_totales=38, jornada_actual=1,
        )
        equipos_p = []
        for _datos in EQUIPOS_PREMIER:
            datos = dict(_datos)
            nivel = datos.pop("nivel")
            eq = Equipo.objects.create(liga=premier, **datos)
            equipos_p.append(eq)
            Jugador.objects.bulk_create(generar_plantilla(eq, nivel))
            self.stdout.write(f"   + {eq.nombre_corto}")

        Clasificacion.objects.bulk_create([
            Clasificacion(liga=premier, equipo=eq, posicion=i + 1)
            for i, eq in enumerate(equipos_p)
        ])
        generar_calendario_premier(premier, equipos_p)

        j_p = Jornada.objects.filter(liga=premier).count()
        p_p = Partido.objects.filter(jornada__liga=premier).count()
        self.stdout.write(self.style.SUCCESS(f"\n   {j_p} jornadas · {p_p} partidos\n"))

        # Verificar que son exactamente 38 jornadas
        if j_p != 38:
            self.stdout.write(self.style.ERROR(f"   ERROR: se esperaban 38 jornadas, hay {j_p}"))
        else:
            self.stdout.write(self.style.SUCCESS("   Verificacion OK: 38 jornadas correctas\n"))

        # ── DIVISIÓN INFERIOR (sin calendario, solo equipos) ──
        self.stdout.write("Creando Division Inferior (10 equipos, sin calendario)...")
        division = Liga.objects.create(
            nombre="Division Inferior", temporada="2025-26",
            jornadas_totales=0, jornada_actual=1,
        )
        equipos_d = []
        for _datos in EQUIPOS_DIVISION:
            datos = dict(_datos)
            nivel = datos.pop("nivel")
            eq = Equipo.objects.create(liga=division, **datos)
            equipos_d.append(eq)
            Jugador.objects.bulk_create(generar_plantilla(eq, nivel))
            self.stdout.write(f"   + {eq.nombre_corto}")

        # Clasificación inicial vacía para División Inferior
        Clasificacion.objects.bulk_create([
            Clasificacion(liga=division, equipo=eq, posicion=i + 1)
            for i, eq in enumerate(equipos_d)
        ])
        self.stdout.write(self.style.SUCCESS("\n   Division Inferior creada (bolsa de ascensos)\n"))

        # ── RESUMEN ───────────────────────────────────────────
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("  LISTO"))
        self.stdout.write(f"  Ligas     : {Liga.objects.count()}")
        self.stdout.write(f"  Equipos   : {Equipo.objects.count()} (20 Premier + 10 Division)")
        self.stdout.write(f"  Jugadores : {Jugador.objects.count()}")
        self.stdout.write(f"  Jornadas  : {Jornada.objects.count()}")
        self.stdout.write(f"  Partidos  : {Partido.objects.count()}")
        self.stdout.write("=" * 60 + "\n")