import random
from django.core.management.base import BaseCommand
from core.models import Liga, Equipo, Jugador, Clasificacion, Jornada, Partido

try:
    from .jugadores_reales import JUGADORES as JUGADORES_REALES
except ImportError:
    JUGADORES_REALES = {}


EQUIPOS_PREMIER = [
    {"nombre": "Arsenal FC",                  "nombre_corto": "Arsenal",        "abreviatura": "ARS", "ciudad": "Londres",        "estadio": "Emirates Stadium",          "capacidad_estadio": 60704, "color_principal": "#EF0107", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 90000000,  "nivel": 88},
    {"nombre": "Aston Villa FC",              "nombre_corto": "Aston Villa",    "abreviatura": "AVL", "ciudad": "Birmingham",     "estadio": "Villa Park",                "capacidad_estadio": 42785, "color_principal": "#95BFE5", "color_secundario": "#670E36", "presupuesto_fichajes": 55000000,  "nivel": 80},
    {"nombre": "AFC Bournemouth",             "nombre_corto": "Bournemouth",    "abreviatura": "BOU", "ciudad": "Bournemouth",    "estadio": "Vitality Stadium",          "capacidad_estadio": 11307, "color_principal": "#DA291C", "color_secundario": "#000000", "presupuesto_fichajes": 20000000,  "nivel": 65},
    {"nombre": "Brentford FC",               "nombre_corto": "Brentford",      "abreviatura": "BRE", "ciudad": "Londres",        "estadio": "Gtech Community Stadium",   "capacidad_estadio": 17250, "color_principal": "#D20000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 22000000,  "nivel": 67},
    {"nombre": "Brighton & Hove Albion",     "nombre_corto": "Brighton",       "abreviatura": "BHA", "ciudad": "Brighton",       "estadio": "Amex Stadium",              "capacidad_estadio": 31800, "color_principal": "#0057B8", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 40000000,  "nivel": 74},
    {"nombre": "Chelsea FC",                 "nombre_corto": "Chelsea",        "abreviatura": "CHE", "ciudad": "Londres",        "estadio": "Stamford Bridge",           "capacidad_estadio": 40341, "color_principal": "#034694", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 100000000, "nivel": 83},
    {"nombre": "Crystal Palace FC",          "nombre_corto": "Crystal Palace", "abreviatura": "CRY", "ciudad": "Londres",        "estadio": "Selhurst Park",             "capacidad_estadio": 25486, "color_principal": "#1B458F", "color_secundario": "#C4122E", "presupuesto_fichajes": 18000000,  "nivel": 64},
    {"nombre": "Everton FC",                 "nombre_corto": "Everton",        "abreviatura": "EVE", "ciudad": "Liverpool",      "estadio": "Goodison Park",             "capacidad_estadio": 39414, "color_principal": "#003399", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 20000000,  "nivel": 63},
    {"nombre": "Fulham FC",                  "nombre_corto": "Fulham",         "abreviatura": "FUL", "ciudad": "Londres",        "estadio": "Craven Cottage",            "capacidad_estadio": 25700, "color_principal": "#FFFFFF", "color_secundario": "#000000", "presupuesto_fichajes": 22000000,  "nivel": 66},
    {"nombre": "Ipswich Town FC",            "nombre_corto": "Ipswich",        "abreviatura": "IPS", "ciudad": "Ipswich",        "estadio": "Portman Road",              "capacidad_estadio": 29312, "color_principal": "#0044A9", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 15000000,  "nivel": 60},
    {"nombre": "Leicester City FC",          "nombre_corto": "Leicester",      "abreviatura": "LEI", "ciudad": "Leicester",      "estadio": "King Power Stadium",        "capacidad_estadio": 32261, "color_principal": "#003090", "color_secundario": "#FDBE11", "presupuesto_fichajes": 18000000,  "nivel": 62},
    {"nombre": "Liverpool FC",               "nombre_corto": "Liverpool",      "abreviatura": "LIV", "ciudad": "Liverpool",      "estadio": "Anfield",                   "capacidad_estadio": 61276, "color_principal": "#C8102E", "color_secundario": "#F6EB61", "presupuesto_fichajes": 95000000,  "nivel": 90},
    {"nombre": "Manchester City FC",         "nombre_corto": "Man. City",      "abreviatura": "MCI", "ciudad": "Manchester",     "estadio": "Etihad Stadium",            "capacidad_estadio": 53400, "color_principal": "#6CABDD", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 110000000, "nivel": 91},
    {"nombre": "Manchester United FC",       "nombre_corto": "Man. United",    "abreviatura": "MUN", "ciudad": "Manchester",     "estadio": "Old Trafford",              "capacidad_estadio": 74310, "color_principal": "#DA291C", "color_secundario": "#FBE122", "presupuesto_fichajes": 85000000,  "nivel": 82},
    {"nombre": "Newcastle United FC",        "nombre_corto": "Newcastle",      "abreviatura": "NEW", "ciudad": "Newcastle",      "estadio": "St. James Park",            "capacidad_estadio": 52305, "color_principal": "#241F20", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 70000000,  "nivel": 81},
    {"nombre": "Nottingham Forest FC",       "nombre_corto": "Nott. Forest", "abreviatura": "NFO", "ciudad": "Nottingham", "estadio": "City Ground",               "capacidad_estadio": 30332, "color_principal": "#DD0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 25000000,  "nivel": 68},
    {"nombre": "Southampton FC",             "nombre_corto": "Southampton",    "abreviatura": "SOU", "ciudad": "Southampton",    "estadio": "St. Mary's Stadium",        "capacidad_estadio": 32384, "color_principal": "#D71920", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 14000000,  "nivel": 59},
    {"nombre": "Tottenham Hotspur FC",       "nombre_corto": "Tottenham",      "abreviatura": "TOT", "ciudad": "Londres",        "estadio": "Tottenham Hotspur Stadium", "capacidad_estadio": 62850, "color_principal": "#132257", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 75000000,  "nivel": 84},
    {"nombre": "West Ham United FC",         "nombre_corto": "West Ham",       "abreviatura": "WHU", "ciudad": "Londres",        "estadio": "London Stadium",            "capacidad_estadio": 62500, "color_principal": "#7A263A", "color_secundario": "#1BB1E7", "presupuesto_fichajes": 30000000,  "nivel": 69},
    {"nombre": "Wolverhampton Wanderers FC", "nombre_corto": "Wolves",         "abreviatura": "WOL", "ciudad": "Wolverhampton",  "estadio": "Molineux Stadium",          "capacidad_estadio": 32050, "color_principal": "#FDB913", "color_secundario": "#231F20", "presupuesto_fichajes": 20000000,  "nivel": 63},
]

EQUIPOS_CHAMPIONSHIP = [
    {"nombre": "Blackburn Rovers FC",        "nombre_corto": "Blackburn",      "abreviatura": "BBR", "ciudad": "Blackburn",      "estadio": "Ewood Park",                "capacidad_estadio": 31367, "color_principal": "#009EE0", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 8000000,   "nivel": 58},
    {"nombre": "Bristol City FC",            "nombre_corto": "Bristol City",   "abreviatura": "BRV", "ciudad": "Bristol",        "estadio": "Ashton Gate",               "capacidad_estadio": 27000, "color_principal": "#E3001B", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 6000000,   "nivel": 55},
    {"nombre": "Burnley FC",                 "nombre_corto": "Burnley",        "abreviatura": "BUR", "ciudad": "Burnley",        "estadio": "Turf Moor",                 "capacidad_estadio": 21944, "color_principal": "#6C1D45", "color_secundario": "#99D6EA", "presupuesto_fichajes": 10000000,  "nivel": 62},
    {"nombre": "Cardiff City FC",            "nombre_corto": "Cardiff",        "abreviatura": "CAR", "ciudad": "Cardiff",        "estadio": "Cardiff City Stadium",      "capacidad_estadio": 33316, "color_principal": "#0070B5", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 5000000,   "nivel": 53},
    {"nombre": "Coventry City FC",           "nombre_corto": "Coventry",       "abreviatura": "COV", "ciudad": "Coventry",       "estadio": "Coventry Building Society Arena", "capacidad_estadio": 32609, "color_principal": "#59CBFF", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 7000000, "nivel": 56},
    {"nombre": "Derby County FC",            "nombre_corto": "Derby",          "abreviatura": "DER", "ciudad": "Derby",          "estadio": "Pride Park Stadium",        "capacidad_estadio": 33597, "color_principal": "#FFFFFF", "color_secundario": "#000000", "presupuesto_fichajes": 6000000,   "nivel": 55},
    {"nombre": "Hull City AFC",              "nombre_corto": "Hull City",      "abreviatura": "HUL", "ciudad": "Hull",           "estadio": "MKM Stadium",               "capacidad_estadio": 25400, "color_principal": "#F18A01", "color_secundario": "#000000", "presupuesto_fichajes": 5000000,   "nivel": 54},
    {"nombre": "Leeds United FC",            "nombre_corto": "Leeds",          "abreviatura": "LEE", "ciudad": "Leeds",          "estadio": "Elland Road",               "capacidad_estadio": 37792, "color_principal": "#FFCD00", "color_secundario": "#1D428A", "presupuesto_fichajes": 12000000,  "nivel": 64},
    {"nombre": "Luton Town FC",              "nombre_corto": "Luton",          "abreviatura": "LUT", "ciudad": "Luton",          "estadio": "Kenilworth Road",           "capacidad_estadio": 10356, "color_principal": "#F78F1E", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 5000000,   "nivel": 55},
    {"nombre": "Middlesbrough FC",           "nombre_corto": "Middlesbrough",  "abreviatura": "MID", "ciudad": "Middlesbrough",  "estadio": "Riverside Stadium",         "capacidad_estadio": 34742, "color_principal": "#EF3B33", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 7000000,   "nivel": 57},
    {"nombre": "Millwall FC",                "nombre_corto": "Millwall",       "abreviatura": "MIL", "ciudad": "Londres",        "estadio": "The Den",                   "capacidad_estadio": 20146, "color_principal": "#001D5E", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 5000000,   "nivel": 54},
    {"nombre": "Norwich City FC",            "nombre_corto": "Norwich",        "abreviatura": "NOR", "ciudad": "Norwich",        "estadio": "Carrow Road",               "capacidad_estadio": 27359, "color_principal": "#00A650", "color_secundario": "#FFF200", "presupuesto_fichajes": 7000000,   "nivel": 57},
    {"nombre": "Oxford United FC",           "nombre_corto": "Oxford Utd",     "abreviatura": "OXF", "ciudad": "Oxford",         "estadio": "Kassam Stadium",            "capacidad_estadio": 12500, "color_principal": "#FFD700", "color_secundario": "#000000", "presupuesto_fichajes": 4000000,   "nivel": 52},
    {"nombre": "Plymouth Argyle FC",         "nombre_corto": "Plymouth",       "abreviatura": "PLY", "ciudad": "Plymouth",       "estadio": "Home Park",                 "capacidad_estadio": 18600, "color_principal": "#007B5E", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 4000000,   "nivel": 52},
    {"nombre": "Preston North End FC",       "nombre_corto": "Preston",        "abreviatura": "PRE", "ciudad": "Preston",        "estadio": "Deepdale",                  "capacidad_estadio": 23404, "color_principal": "#FFFFFF", "color_secundario": "#002D62", "presupuesto_fichajes": 5000000,   "nivel": 54},
    {"nombre": "Queens Park Rangers FC",     "nombre_corto": "QPR",            "abreviatura": "QPR", "ciudad": "Londres",        "estadio": "Loftus Road",               "capacidad_estadio": 18360, "color_principal": "#005CAB", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 5000000,   "nivel": 54},
    {"nombre": "Sheffield United FC",        "nombre_corto": "Sheffield Utd",  "abreviatura": "SHU", "ciudad": "Sheffield",      "estadio": "Bramall Lane",              "capacidad_estadio": 32125, "color_principal": "#EE2737", "color_secundario": "#000000", "presupuesto_fichajes": 8000000,   "nivel": 60},
    {"nombre": "Stoke City FC",              "nombre_corto": "Stoke",          "abreviatura": "STK", "ciudad": "Stoke-on-Trent", "estadio": "Bet365 Stadium",            "capacidad_estadio": 30089, "color_principal": "#E03A3E", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 6000000,   "nivel": 55},
    {"nombre": "Sunderland AFC",             "nombre_corto": "Sunderland",     "abreviatura": "SUN", "ciudad": "Sunderland",     "estadio": "Stadium of Light",          "capacidad_estadio": 49000, "color_principal": "#EB172B", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 7000000,   "nivel": 57},
    {"nombre": "Watford FC",                 "nombre_corto": "Watford",        "abreviatura": "WAT", "ciudad": "Watford",        "estadio": "Vicarage Road",             "capacidad_estadio": 22200, "color_principal": "#FBEE23", "color_secundario": "#ED2127", "presupuesto_fichajes": 7000000,   "nivel": 57},
]

EQUIPOS_LEAGUE_ONE = [
    {"nombre": "Birmingham City FC",         "nombre_corto": "Birmingham",     "abreviatura": "BIR", "ciudad": "Birmingham",     "estadio": "St. Andrew's Stadium",     "capacidad_estadio": 29409, "color_principal": "#0000FF", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 3000000,   "nivel": 50},
    {"nombre": "Blackpool FC",               "nombre_corto": "Blackpool",      "abreviatura": "BLP", "ciudad": "Blackpool",      "estadio": "Bloomfield Road",          "capacidad_estadio": 16750, "color_principal": "#F68712", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 2000000,   "nivel": 46},
    {"nombre": "Bolton Wanderers FC",        "nombre_corto": "Bolton",         "abreviatura": "BOL", "ciudad": "Bolton",         "estadio": "Toughsheet Community Stadium", "capacidad_estadio": 28723, "color_principal": "#FFFFFF", "color_secundario": "#263C7E", "presupuesto_fichajes": 2500000, "nivel": 48},
    {"nombre": "Bristol Rovers FC",          "nombre_corto": "Bristol Rovers", "abreviatura": "BRV", "ciudad": "Bristol",        "estadio": "Memorial Stadium",         "capacidad_estadio": 12300, "color_principal": "#005CAB", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1500000,   "nivel": 44},
    {"nombre": "Burton Albion FC",           "nombre_corto": "Burton",         "abreviatura": "BAF", "ciudad": "Burton upon Trent", "estadio": "Pirelli Stadium",        "capacidad_estadio": 6912,  "color_principal": "#FFD700", "color_secundario": "#000000", "presupuesto_fichajes": 1000000,   "nivel": 43},
    {"nombre": "Cambridge United FC",        "nombre_corto": "Cambridge Utd",  "abreviatura": "CAM", "ciudad": "Cambridge",      "estadio": "Abbey Stadium",            "capacidad_estadio": 8000,  "color_principal": "#F58220", "color_secundario": "#000000", "presupuesto_fichajes": 1000000,   "nivel": 42},
    {"nombre": "Charlton Athletic FC",       "nombre_corto": "Charlton",       "abreviatura": "CHA", "ciudad": "Londres",        "estadio": "The Valley",               "capacidad_estadio": 27111, "color_principal": "#D4021D", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 2000000,   "nivel": 46},
    {"nombre": "Exeter City FC",             "nombre_corto": "Exeter",         "abreviatura": "EXE", "ciudad": "Exeter",         "estadio": "St James Park",            "capacidad_estadio": 8696,  "color_principal": "#D71920", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1000000,   "nivel": 43},
    {"nombre": "Huddersfield Town AFC",      "nombre_corto": "Huddersfield",   "abreviatura": "HUD", "ciudad": "Huddersfield",   "estadio": "John Smith's Stadium",     "capacidad_estadio": 24169, "color_principal": "#0E63AD", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 2500000,   "nivel": 48},
    {"nombre": "Leyton Orient FC",           "nombre_corto": "Leyton Orient",  "abreviatura": "LOR", "ciudad": "Londres",        "estadio": "Brisbane Road",            "capacidad_estadio": 9271,  "color_principal": "#D71920", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1000000,   "nivel": 43},
    {"nombre": "Lincoln City FC",            "nombre_corto": "Lincoln",        "abreviatura": "LIN", "ciudad": "Lincoln",        "estadio": "LNER Stadium",             "capacidad_estadio": 10120, "color_principal": "#D71920", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1000000,   "nivel": 43},
    {"nombre": "Northampton Town FC",        "nombre_corto": "Northampton",    "abreviatura": "NTH", "ciudad": "Northampton",    "estadio": "Sixfields Stadium",        "capacidad_estadio": 7798,  "color_principal": "#800000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1000000,   "nivel": 42},
    {"nombre": "Peterborough United FC",     "nombre_corto": "Peterborough",   "abreviatura": "PET", "ciudad": "Peterborough",   "estadio": "Weston Homes Stadium",     "capacidad_estadio": 14319, "color_principal": "#005BAC", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1500000,   "nivel": 45},
    {"nombre": "Reading FC",                 "nombre_corto": "Reading",        "abreviatura": "REA", "ciudad": "Reading",        "estadio": "Select Car Leasing Stadium", "capacidad_estadio": 24161, "color_principal": "#0044A9", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 2000000, "nivel": 47},
    {"nombre": "Rotherham United FC",        "nombre_corto": "Rotherham",      "abreviatura": "ROT", "ciudad": "Rotherham",      "estadio": "AESSEAL New York Stadium",  "capacidad_estadio": 12021, "color_principal": "#CC0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1500000,  "nivel": 45},
    {"nombre": "Shrewsbury Town FC",         "nombre_corto": "Shrewsbury",     "abreviatura": "SHR", "ciudad": "Shrewsbury",     "estadio": "Croud Meadow",             "capacidad_estadio": 9875,  "color_principal": "#003087", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1000000,   "nivel": 42},
    {"nombre": "Stevenage FC",               "nombre_corto": "Stevenage",      "abreviatura": "STE", "ciudad": "Stevenage",      "estadio": "Lamex Stadium",            "capacidad_estadio": 7800,  "color_principal": "#CC0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1000000,   "nivel": 42},
    {"nombre": "Stockport County FC",        "nombre_corto": "Stockport",      "abreviatura": "STO", "ciudad": "Stockport",      "estadio": "Edgeley Park",             "capacidad_estadio": 10641, "color_principal": "#1C4F9C", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1500000,   "nivel": 45},
    {"nombre": "Wigan Athletic FC",          "nombre_corto": "Wigan",          "abreviatura": "WIG", "ciudad": "Wigan",          "estadio": "DW Stadium",               "capacidad_estadio": 25138, "color_principal": "#1D59AF", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 1500000,   "nivel": 45},
    {"nombre": "Wrexham AFC",                "nombre_corto": "Wrexham",        "abreviatura": "WRE", "ciudad": "Wrexham",        "estadio": "Racecourse Ground",        "capacidad_estadio": 15500, "color_principal": "#CC0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 2000000,   "nivel": 47},
]

EQUIPOS_LEAGUE_TWO = [
    {"nombre": "AFC Wimbledon",              "nombre_corto": "Wimbledon",      "abreviatura": "WIM", "ciudad": "Londres",        "estadio": "Plough Lane",              "capacidad_estadio": 9315,  "color_principal": "#0000FF", "color_secundario": "#FFD700", "presupuesto_fichajes": 500000,     "nivel": 38},
    {"nombre": "Accrington Stanley FC",      "nombre_corto": "Accrington",     "abreviatura": "ACC", "ciudad": "Accrington",     "estadio": "Wham Stadium",             "capacidad_estadio": 5057,  "color_principal": "#CC0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 300000,     "nivel": 35},
    {"nombre": "Barrow AFC",                 "nombre_corto": "Barrow",         "abreviatura": "BAR", "ciudad": "Barrow",         "estadio": "Holker Street",            "capacidad_estadio": 4622,  "color_principal": "#003366", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 300000,     "nivel": 34},
    {"nombre": "Bradford City AFC",          "nombre_corto": "Bradford",       "abreviatura": "BRA", "ciudad": "Bradford",       "estadio": "Valley Parade",            "capacidad_estadio": 25136, "color_principal": "#801020", "color_secundario": "#FFFF00", "presupuesto_fichajes": 600000,     "nivel": 38},
    {"nombre": "Bromley FC",                 "nombre_corto": "Bromley",        "abreviatura": "BRO", "ciudad": "Bromley",        "estadio": "Hayes Lane",               "capacidad_estadio": 5000,  "color_principal": "#000000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 300000,     "nivel": 33},
    {"nombre": "Carlisle United FC",         "nombre_corto": "Carlisle",       "abreviatura": "CAL", "ciudad": "Carlisle",       "estadio": "Brunton Park",             "capacidad_estadio": 17949, "color_principal": "#1C4F9C", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 400000,     "nivel": 36},
    {"nombre": "Cheltenham Town FC",         "nombre_corto": "Cheltenham",     "abreviatura": "CHT", "ciudad": "Cheltenham",     "estadio": "Jonny-Rocks Stadium",      "capacidad_estadio": 7066,  "color_principal": "#CC0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 400000,     "nivel": 36},
    {"nombre": "Chesterfield FC",            "nombre_corto": "Chesterfield",   "abreviatura": "CHF", "ciudad": "Chesterfield",   "estadio": "SMH Group Stadium",        "capacidad_estadio": 10400, "color_principal": "#003087", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 500000,     "nivel": 37},
    {"nombre": "Colchester United FC",       "nombre_corto": "Colchester",     "abreviatura": "COL", "ciudad": "Colchester",     "estadio": "JobServe Community Stadium", "capacidad_estadio": 10105, "color_principal": "#003087", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 400000,  "nivel": 36},
    {"nombre": "Crawley Town FC",            "nombre_corto": "Crawley",        "abreviatura": "CRA", "ciudad": "Crawley",        "estadio": "Broadfield Stadium",       "capacidad_estadio": 5996,  "color_principal": "#CC0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 400000,     "nivel": 36},
    {"nombre": "Doncaster Rovers FC",        "nombre_corto": "Doncaster",      "abreviatura": "DON", "ciudad": "Doncaster",      "estadio": "Eco-Power Stadium",        "capacidad_estadio": 15231, "color_principal": "#CC0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 500000,     "nivel": 37},
    {"nombre": "Fleetwood Town FC",          "nombre_corto": "Fleetwood",      "abreviatura": "FLE", "ciudad": "Fleetwood",      "estadio": "Highbury Stadium",         "capacidad_estadio": 5327,  "color_principal": "#CC0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 300000,     "nivel": 34},
    {"nombre": "Gillingham FC",              "nombre_corto": "Gillingham",     "abreviatura": "GIL", "ciudad": "Gillingham",     "estadio": "MEMS Priestfield Stadium", "capacidad_estadio": 11582, "color_principal": "#003087", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 400000,     "nivel": 36},
    {"nombre": "Grimsby Town FC",            "nombre_corto": "Grimsby",        "abreviatura": "GRI", "ciudad": "Grimsby",        "estadio": "Blundell Park",            "capacidad_estadio": 9052,  "color_principal": "#000000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 400000,     "nivel": 35},
    {"nombre": "Harrogate Town AFC",         "nombre_corto": "Harrogate",      "abreviatura": "HAR", "ciudad": "Harrogate",      "estadio": "Wetherby Road",            "capacidad_estadio": 5000,  "color_principal": "#FFD700", "color_secundario": "#000000", "presupuesto_fichajes": 300000,     "nivel": 33},
    {"nombre": "Milton Keynes Dons FC",      "nombre_corto": "MK Dons",        "abreviatura": "MKD", "ciudad": "Milton Keynes",  "estadio": "Stadium MK",               "capacidad_estadio": 30500, "color_principal": "#FFD700", "color_secundario": "#000000", "presupuesto_fichajes": 500000,     "nivel": 38},
    {"nombre": "Morecambe FC",               "nombre_corto": "Morecambe",      "abreviatura": "MOR", "ciudad": "Morecambe",      "estadio": "Mazuma Mobile Stadium",    "capacidad_estadio": 6476,  "color_principal": "#CC0000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 300000,     "nivel": 34},
    {"nombre": "Newport County AFC",         "nombre_corto": "Newport",        "abreviatura": "NEP", "ciudad": "Newport",        "estadio": "Rodney Parade",            "capacidad_estadio": 7850,  "color_principal": "#F6A800", "color_secundario": "#000000", "presupuesto_fichajes": 300000,     "nivel": 33},
    {"nombre": "Notts County FC",            "nombre_corto": "Notts County",   "abreviatura": "NTC", "ciudad": "Nottingham",     "estadio": "Meadow Lane",              "capacidad_estadio": 20300, "color_principal": "#000000", "color_secundario": "#FFFFFF", "presupuesto_fichajes": 500000,     "nivel": 37},
    {"nombre": "Tranmere Rovers FC",         "nombre_corto": "Tranmere",       "abreviatura": "TRA", "ciudad": "Birkenhead",     "estadio": "Prenton Park",             "capacidad_estadio": 16587, "color_principal": "#FFFFFF", "color_secundario": "#003087", "presupuesto_fichajes": 400000,     "nivel": 35},
]

NOMBRES = [
"James","Oliver","Harry","Jack","George","Noah","Liam","Ethan","Lucas","Mason",
"Logan","Aiden","Elijah","Ryan","Nathan","Dylan","Tyler","Connor","Jordan","Marcus",
"Kai","Zion","Andre","Leon","Malik","Carlos","Diego","Pablo","Mateo","Sergio",
"Ivan","Alexei","Mohamed","Yusuf","Amadou","Sadio","Ismaila","Lautaro","Emre","Kerem",
"Adrian","Alan","Albert","Alejandro","Alessandro","Andres","Angel","Anthony","Antonio","Armin",
"Arthur","Asier","Benjamin","Bruno","Bryan","Caleb","Cesar","Christian","Christopher","Daniel",
"David","Denis","Dominic","Eduardo","Enzo","Eric","Erik","Fabian","Federico","Felix",
"Fernando","Francisco","Gabriel","Gael","Gonzalo","Guillermo","Hector","Hugo","Ian","Ignacio",
"Ismael","Javier","Joaquin","Joel","Jonathan","Jose","Juan","Julian","Kevin","Leo",
"Lorenzo","Luis","Manuel","Marco","Mario","Martin","Matias","Max","Maximiliano","Miguel",
"Nicolas","Oscar","Pau","Pedro","Rafael","Raul","Ricardo","Roberto","Rodrigo","Roman",
"Ruben","Salvador","Samuel","Santiago","Saul","Sebastian","Simon","Tomas","Valentin","Victor",
"Adil","Ahmed","Ali","Bilal","Hassan","Hussein","Ibrahim","Karim","Khalid","Mahmoud",
"Omar","Rachid","Samir","Tariq","Yassine","Youssef","Zakaria","Abdou","Bakary","Cheikh",
"Moussa","Nabil","Nasser","Said","Hamza","Imran","Farid","Nadir","Walid","Faris",
"Arda","Burak","Can","Deniz","Hakan","Kaan","Mehmet","Serkan","Tolga","Yilmaz",
"Minho","Jin","Hiro","Takumi","Ren","Yuki","Sora","Daichi","Kenji","Riku",
"Luca","Matteo","Alberto","Giovanni","Riccardo","Stefano","Alvaro","Borja","Ciro","Dario",
"Eloy","Fermin","Gerard","Iker","Jon","Kike","Lander","Mikel","Nestor","Oier",
"Unai","Yeray","Aitor","Brais","Yago","Thiago","Brayan","Cristian","Esteban","Leandro"
]

APELLIDOS = [
"Smith","Jones","Williams","Brown","Taylor","Davies","Evans","Wilson","Thomas","Roberts",
"Johnson","White","Walker","Hall","Wright","Green","Hughes","Lewis","Harris","Clarke",
"Martinez","Garcia","Fernandez","Lopez","Diaz","Silva","Costa","Santos","Oliveira","Pereira",
"Muller","Schmidt","Fischer","Weber","Becker","Diallo","Traore","Camara","Keita","Nkunku",
"Tchouameni","Bellingham","Saka","Rashford","Foden","Palmer","Gordon","Mbeumo","Watkins","Salah",
"Torres","Gomez","Vazquez","Ramos","Suarez","Ortega","Castro","Delgado","Morales","Ortiz",
"Guerrero","Mendez","Cruz","Herrera","Medina","Castillo","Vargas","Rojas","Navarro","Peña",
"Iglesias","Cortes","Serrano","Dominguez","Fuentes","Cabrera","Campos","Vega","Leon","Nieto",
"Bravo","Pascual","Parra","Reyes","Santos","Pardo","Benitez","Montoya","Cuevas","Valencia",
"Marquez","Escobar","Salazar","Villalba","Correa","Ledesma","Acosta","Figueroa","Molina","Montes",
"Roldan","Ibarra","Padilla","Zamora","Ponce","Carrasco","Calderon","Aguirre","Solano","Tapia",
"Lozano","Peralta","Bautista","Arellano","Cervantes","Cordero","Rosales","Galindo","Aranda","Bermudez",
"Campos","Arias","Santana","Ferrer","Montero","Soto","Soria","Barrios","Benavides","Blanco",
"Bravo","Cano","Cardenas","Carrillo","Cedeno","Cespedes","Cuellar","Duarte","Espinosa","Estrella",
"Farias","Franco","Galvez","Godoy","Granados","Hidalgo","Lara","Linares","Macias","Maldonado",
"Mora","Nava","Ocampo","Orozco","Pizarro","Quintero","Rangel","Salinas","Sepulveda","Tellez",
"Trejo","Urbina","Valle","Villanueva","Zarate","Zepeda","Zurita","Aldana","Alfaro","Alvarado",
"Amador","Arce","Avalos","Barragan","Beltran","Bustos","Carvajal","Casillas","Chavez","Coronado",
"Esquivel","Fajardo","Fajardo","Gallego","Garrido","Guillen","Hurtado","Lujan","Marin","Palacios"
]

NACIONALIDADES = [
"Afgano","Albanes","Aleman","Andorrano","Angoleno","Antiguano","Saudi","Argelino","Argentino","Armenio",
"Australiano","Austriaco","Azerbaiyano","Bahames","Bareini","Bangladesi","Barbadense","Belga","Beliceno","Benines",
"Butanes","Bielorruso","Birmano","Boliviano","Bosnio","Botsuano","Brasileno","Brunei","Bulgaro","Burkines",
"Burundi","CaboVerdiano","Camboyano","Camerunes","Canadiense","Catarí","Chileno","Chino","Chipriota","Colombiano",
"Comorense","Congoleno","Norcoreano","Surcoreano","Costarricense","Croata","Cubano","Danes","Dominicano","Ecuatoriano",
"Egipcio","Salvadoreno","Emirati","Eritreo","Eslovaco","Esloveno","Espanol","Estadounidense","Estonio","Etiope",
"Filipino","Finlandes","Fiyiano","Frances","Gabonés","Gambiano","Georgiano","Ghanes","Granadino","Griego",
"Guatemalteco","Guineano","Guineoecuatorial","Guineense","Guyanés","Haitiano","Hondureno","Hungaro","Indio","Indonesio",
"Irani","Iraqui","Irlandes","Islandes","Israeli","Italiano","Marfileño","Jamaicano","Japones","Jordano",
"Kazajo","Keniata","Kirguistaní","Kiribatiano","Kosovar","Kuwaiti","Laosiano","Lesotense","Leton","Libanes",
"Liberiano","Libio","Liechtensteiniano","Lituano","Luxemburgues","Macedonio","Malasio","Malaui","Maldivo","Maliense",
"Maltes","Marroqui","Marshallés","Mauriciano","Mauritano","Mexicano","Micronesio","Moldavo","Monegasco","Mongol",
"Montenegrino","Mozambiqueno","Namibio","Nauruano","Nepali","Nicaraguense","Nigerino","Nigeriano","Noruego","Neozelandes",
"Omani","Holandes","Pakistani","Palauano","Panameno","Papua","Paraguayo","Peruano","Polaco","Portugues",
"Britanico","Checo","Centroafricano","Congoles","Rumano","Ruso","Ruandes","Sancristobalense","Santalucense","Sanmarinense",
"Sanvicentino","Samoano","Senegales","Serbio","Seychellense","Sierraleones","Singapurense","Sirio","Somali","Srilankes",
"Suazi","Sudafricano","Sudanes","Surinames","Sueco","Suizo","Tailandes","Tanzano","Tayiko","Timorense",
"Togoles","Tongano","Trinitense","Tunecino","Turco","Turkmeno","Tuvaluano","Ucraniano","Ugandes","Uruguayo",
"Uzbeko","Vanuatuense","Vaticano","Venezolano","Vietnamita","Yemení","Yibutiano","Zambiano","Zimbabuense"
]

ESTRUCTURA_PLANTILLA = [("POR", 2), ("DEF", 7), ("MED", 7), ("DEL", 4)]
DORSALES = {"POR": [1,13], "DEF": [2,3,4,5,6,12,18], "MED": [7,8,10,11,14,15,16], "DEL": [9,17,19,20]}


def generar_atributos(posicion, nivel, es_titular=True):
    base = nivel if es_titular else nivel - random.randint(8, 18)
    base = max(base, 30)
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
    """
    Si el equipo tiene jugadores reales en jugadores_reales.py los usa.
    Si no, genera la plantilla aleatoriamente.
    """
    abrev = equipo.abreviatura
    if abrev in JUGADORES_REALES:
        return _plantilla_real(equipo, abrev)
    return _plantilla_aleatoria(equipo, nivel)


def _plantilla_real(equipo, abrev):
    """Crea jugadores a partir de los datos reales de jugadores_reales.py."""
    jugadores = []
    for datos in JUGADORES_REALES[abrev]:
        d = dict(datos)
        # pie_dominante viene como "D"/"I"/"A" en el archivo
        d["pie_dominante"] = d.pop("pie", "D")
        # temporadas_contrato aleatorio si no se especifica
        if "temporadas_contrato" not in d:
            d["temporadas_contrato"] = random.randint(1, 4)
        jugadores.append(Jugador(equipo=equipo, **d))
    return jugadores


def _plantilla_aleatoria(equipo, nivel):
    """Generación aleatoria original (sin cambios)."""
    jugadores = []
    dc = {pos: 0 for pos in ["POR", "DEF", "MED", "DEL"]}
    for pos, cantidad in ESTRUCTURA_PLANTILLA:
        for i in range(cantidad):
            es_titular = i < (1 if pos == "POR" else cantidad // 2 + 1)
            dorsal = DORSALES[pos][dc[pos]] if dc[pos] < len(DORSALES[pos]) else None
            dc[pos] += 1
            attrs = generar_atributos(pos, nivel, es_titular)
            jugadores.append(Jugador(
                nombre=random.choice(NOMBRES), apellidos=random.choice(APELLIDOS),
                nacionalidad=random.choice(NACIONALIDADES), edad=random.randint(18, 35),
                posicion=pos, pie_dominante=random.choice(["D", "D", "D", "I", "A"]),
                dorsal=dorsal, equipo=equipo,
                temporadas_contrato=random.randint(1, 4),
                **attrs,
            ))
    return jugadores


def generar_calendario(liga, equipos):
    n = len(equipos)
    fijos = equipos[:]
    jornadas_ida = []
    for r in range(n - 1):
        ronda = []
        for i in range(n // 2):
            local = fijos[i]
            visitante = fijos[n - 1 - i]
            if i == 0 and r % 2 == 1:
                local, visitante = visitante, local
            ronda.append((local, visitante))
        jornadas_ida.append(ronda)
        fijos = [fijos[0]] + [fijos[-1]] + fijos[1:-1]
    jornadas_vuelta = [[(v, l) for l, v in ronda] for ronda in jornadas_ida]
    todas = jornadas_ida + jornadas_vuelta
    for num, partidos in enumerate(todas, start=1):
        j = Jornada.objects.create(liga=liga, numero=num)
        Partido.objects.bulk_create([
            Partido(jornada=j, equipo_local=l, equipo_visitante=v)
            for l, v in partidos
        ])


class Command(BaseCommand):
    help = "Pobla la BD con las 4 divisiones inglesas 2025/26"

    def handle(self, *args, **kwargs):
        if Liga.objects.exists():
            self.stdout.write("La BD ya tiene datos. Usa reset para reiniciar.")
            return

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  TACTICAL ELEVEN — Inicializando temporada 2025/26")
        self.stdout.write("=" * 60 + "\n")

        divisiones = [
            ("Premier League", 1, EQUIPOS_PREMIER),
            ("Championship",   2, EQUIPOS_CHAMPIONSHIP),
            ("League One",     3, EQUIPOS_LEAGUE_ONE),
            ("League Two",     4, EQUIPOS_LEAGUE_TWO),
        ]

        for nombre_liga, nivel_liga, equipos_datos in divisiones:
            self.stdout.write(f"Creando {nombre_liga} ({len(equipos_datos)} equipos)...")
            liga = Liga.objects.create(
                nombre=nombre_liga, temporada="2025-26",
                jornadas_totales=38, jornada_actual=1,
                nivel=nivel_liga,
            )
            equipos = []
            for _datos in equipos_datos:
                datos = dict(_datos)
                nivel = datos.pop("nivel")
                eq = Equipo.objects.create(liga=liga, **datos)
                equipos.append(eq)
                Jugador.objects.bulk_create(generar_plantilla(eq, nivel))
                self.stdout.write(f"   + {eq.nombre_corto}")

            Clasificacion.objects.bulk_create([
                Clasificacion(liga=liga, equipo=eq, posicion=i + 1)
                for i, eq in enumerate(equipos)
            ])
            generar_calendario(liga, equipos)
            j_count = Jornada.objects.filter(liga=liga).count()
            p_count = Partido.objects.filter(jornada__liga=liga).count()
            self.stdout.write(self.style.SUCCESS(f"   {j_count} jornadas x {p_count} partidos\n"))

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("  LISTO"))
        self.stdout.write(f"  Ligas     : {Liga.objects.count()}")
        self.stdout.write(f"  Equipos   : {Equipo.objects.count()}")
        self.stdout.write(f"  Jugadores : {Jugador.objects.count()}")
        self.stdout.write(f"  Jornadas  : {Jornada.objects.count()}")
        self.stdout.write(f"  Partidos  : {Partido.objects.count()}")
        self.stdout.write("=" * 60 + "\n")