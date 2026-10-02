import sys
import time
from io import StringIO
import pandas as pd
import requests
from sqlalchemy import create_engine, text

# 1. Parámetros de conexión (desde el host hacia el contenedor expuesto en 3306)
DB_USER = "root"
DB_PASS = "root"
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "astronomia"

print("[1/5] Conectando con la base de datos MySQL...")
engine_root = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/")

# Esperar a que MySQL acepte conexiones
conectado = False
for _ in range(30):
    try:
        with engine_root.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};"))
            conn.commit()
        conectado = True
        break
    except Exception:
        time.sleep(1)

if not conectado:
    print("Error: No se pudo conectar a MySQL en localhost:3306")
    sys.exit(1)

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# 2. Creación de Tablas (DDL)
print("[2/5] Creando tablas con integridad referencial...")
ddl_statements = [
    """
    CREATE TABLE IF NOT EXISTS estrella (
        id_estrella INT AUTO_INCREMENT,
        nombre VARCHAR(100) NOT NULL,
        masa DECIMAL(10,4),
        radio DECIMAL(10,4),
        temperatura INT,
        PRIMARY KEY (id_estrella),
        UNIQUE (nombre)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS telescopio (
        id_telescopio INT AUTO_INCREMENT,
        nombre VARCHAR(150),
        instalacion VARCHAR(150),
        instrumento VARCHAR(150),
        PRIMARY KEY (id_telescopio)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS planeta (
        id_planeta INT AUTO_INCREMENT,
        id_estrella INT NOT NULL,
        nombre VARCHAR(100) NOT NULL,
        masa DECIMAL(12,5),
        radio DECIMAL(10,5),
        periodo_orbital DECIMAL(15,6),
        semieje_mayor DECIMAL(15,6),
        PRIMARY KEY (id_planeta),
        UNIQUE (nombre),
        FOREIGN KEY (id_estrella) REFERENCES estrella(id_estrella)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS descubrimiento (
        id_descubrimiento INT AUTO_INCREMENT,
        id_planeta INT NOT NULL,
        id_telescopio INT,
        año INT,
        metodo VARCHAR(100),
        PRIMARY KEY (id_descubrimiento),
        FOREIGN KEY (id_planeta) REFERENCES planeta(id_planeta),
        FOREIGN KEY (id_telescopio) REFERENCES telescopio(id_telescopio)
    );
    """
]

with engine.connect() as conn:
    for stmt in ddl_statements:
        conn.execute(text(stmt))
    conn.commit()

# 3. Descarga de datos desde la API de la NASA
print("[3/5] Consultando la API de la NASA (TAP sync)...")
query_nasa = """
SELECT
    pl_name, hostname, pl_masse, pl_rade, pl_orbper, pl_orbsmax,
    st_mass, st_rad, st_teff, sy_snum, sy_pnum, disc_year,
    discoverymethod, disc_facility, disc_telescope, disc_instrument
FROM pscomppars
"""
url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
response = requests.get(url, params={"query": query_nasa, "format": "csv"})

if response.status_code != 200:
    print(f"Error al descargar datos de la NASA (HTTP {response.status_code})")
    sys.exit(1)

df = pd.read_csv(StringIO(response.text))

# 4. Transformaciones y Modelado Relacional
print("[4/5] Transformando y normalizando datos...")

# A. Estrellas
estrellas = df[["hostname", "st_mass", "st_rad", "st_teff"]].drop_duplicates(subset=["hostname"]).copy()
estrellas = estrellas.reset_index(drop=True)
estrellas.insert(0, "id_estrella", range(1, len(estrellas) + 1))
estrellas = estrellas.rename(columns={
    "hostname": "nombre",
    "st_mass": "masa",
    "st_rad": "radio",
    "st_teff": "temperatura"
})

# B. Planetas
planetas = df[["pl_name", "hostname", "pl_masse", "pl_rade", "pl_orbper", "pl_orbsmax"]].copy()
planetas = planetas.rename(columns={
    "pl_name": "nombre",
    "pl_masse": "masa",
    "pl_rade": "radio",
    "pl_orbper": "periodo_orbital",
    "pl_orbsmax": "semieje_mayor"
})
planetas = planetas.merge(estrellas[["id_estrella", "nombre"]], left_on="hostname", right_on="nombre", how="left")
planetas = planetas.drop(columns=["nombre_y", "hostname"])
planetas = planetas.rename(columns={"nombre_x": "nombre"}).reset_index(drop=True)
planetas.insert(0, "id_planeta", range(1, len(planetas) + 1))

# C. Telescopios
telescopios = df[["disc_facility", "disc_telescope", "disc_instrument"]].drop_duplicates().copy()
telescopios = telescopios.rename(columns={
    "disc_facility": "instalacion",
    "disc_telescope": "nombre",
    "disc_instrument": "instrumento"
}).reset_index(drop=True)
telescopios.insert(0, "id_telescopio", range(1, len(telescopios) + 1))

# D. Descubrimientos
descubrimientos = df[["pl_name", "disc_year", "discoverymethod", "disc_facility", "disc_telescope", "disc_instrument"]].copy()
descubrimientos = descubrimientos.rename(columns={
    "pl_name": "planeta",
    "disc_year": "año",
    "discoverymethod": "metodo",
    "disc_facility": "instalacion",
    "disc_telescope": "telescopio",
    "disc_instrument": "instrumento"
})
descubrimientos = descubrimientos.merge(planetas[["id_planeta", "nombre"]], left_on="planeta", right_on="nombre", how="left")
descubrimientos = descubrimientos.merge(
    telescopios[["id_telescopio", "nombre", "instalacion", "instrumento"]],
    left_on=["telescopio", "instalacion", "instrumento"],
    right_on=["nombre", "instalacion", "instrumento"],
    how="left"
)
descubrimientos = descubrimientos.reset_index(drop=True)
descubrimientos.insert(0, "id_descubrimiento", range(1, len(descubrimientos) + 1))
descubrimientos = descubrimientos[["id_descubrimiento", "id_planeta", "id_telescopio", "año", "metodo"]]

# 5. Inserción respetando el orden Padre -> Hijo
print("[5/5] Insertando datos en MySQL...")

with engine.connect() as conn:
    conteo = conn.execute(text("SELECT COUNT(*) FROM estrella;")).scalar()

if conteo > 0:
    print("La base de datos ya contiene datos. Saltando inserción.")
else:
    estrellas.to_sql(name="estrella", con=engine, if_exists="append", index=False)
    telescopios.to_sql(name="telescopio", con=engine, if_exists="append", index=False)
    planetas.to_sql(name="planeta", con=engine, if_exists="append", index=False)
    descubrimientos.to_sql(name="descubrimiento", con=engine, if_exists="append", index=False)
    print("Base de datos cargada con éxito.")

print("Base de datos cargada")