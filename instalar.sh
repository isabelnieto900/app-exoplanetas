#!/bin/bash
set -e

echo "=========================================="
echo "   INSTALACIÓN SISTEMA DE "
echo "   ANÁLISIS EXOPLANETARIO"
echo "=========================================="

# 1. Dependencias del sistema operativo (Debian/Ubuntu)
echo ""
echo "[1/6] Verificando dependencias del sistema..."
sudo apt update -y >/dev/null
sudo apt install -y python3 python3-venv python3-pip docker.io curl >/dev/null

# 2. Configurar y activar el entorno virtual
echo ""
echo "[2/6] Configurando entorno virtual Python (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 3. Instalar librerías de Python
echo ""
echo "[3/6] Instalando librerías Python requeridas..."
pip install --upgrade pip >/dev/null
pip install streamlit pandas numpy plotly requests sqlalchemy pymysql mysql-connector-python >/dev/null

# 4. Levantar la base de datos MySQL en Docker
echo ""
echo "[4/6] Configurando contenedor MySQL 8.4..."
NETWORK="ciencia-net"
MYSQL_CONTAINER="mysql84"
MYSQL_PASSWORD="root"
MYSQL_DB="astronomia"

sudo docker network create "$NETWORK" 2>/dev/null || true

if [ ! "$(sudo docker ps -q -f name=^/${MYSQL_CONTAINER}$)" ]; then
    if [ "$(sudo docker ps -aq -f status=exited -f name=^/${MYSQL_CONTAINER}$)" ]; then
        echo "Iniciando contenedor existente $MYSQL_CONTAINER..."
        sudo docker start "$MYSQL_CONTAINER"
    else
        echo "Creando contenedor nuevo $MYSQL_CONTAINER..."
        sudo docker run -d \
            --name "$MYSQL_CONTAINER" \
            --network "$NETWORK" \
            -p 3306:3306 \
            -e MYSQL_ROOT_PASSWORD="$MYSQL_PASSWORD" \
            -e MYSQL_DATABASE="$MYSQL_DB" \
            mysql:8.4
    fi
    echo "Esperando 12 segundos a que el motor MySQL inicie..."
    sleep 12
fi

# 5. Ejecutar la descarga de datos de la NASA y poblar la base de datos
echo ""
echo "[5/6] Verificando / Poblando la base de datos 'astronomia'..."
python bd.py

# 6. Lanzar la aplicación
echo ""
echo "[6/6] Iniciando la aplicación Streamlit..."
echo "=========================================="
echo "Accede en tu navegador a: http://localhost:8501"
echo "=========================================="

if [ -f "4astronomia_app.py" ]; then
    streamlit run 4astronomia_app.py
elif [ -f "4.GUI/3Exoplanetas_Full/4astronomia_app.py" ]; then
    streamlit run 4.GUI/3Exoplanetas_Full/4astronomia_app.py
else
    echo "Error: No se encontró el archivo de la app Streamlit."
    exit 1
fi