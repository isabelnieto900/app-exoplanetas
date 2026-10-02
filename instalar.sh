#!/bin/bash
set -e

echo "=========================================="
echo "   INSTALACIÓN SISTEMA DE "
echo "   ANÁLISIS EXOPLANETARIO"
echo "=========================================="

# 1. Dependencias del sistema
echo ""
echo "[1/6] Verificando dependencias del sistema..."
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -y >/dev/null 2>&1 || true
sudo apt-get install -y python3 python3-venv python3-pip curl >/dev/null 2>&1 || true

# 2. Entorno virtual
echo ""
echo "[2/6] Configurando entorno virtual Python (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 3. Librerías Python
echo ""
echo "[3/6] Instalando librerías Python requeridas..."
pip install --upgrade pip >/dev/null 2>&1
pip install --quiet streamlit pandas numpy plotly requests sqlalchemy pymysql mysql-connector-python

# 4. Contenedor MySQL
echo ""
echo "[4/6] Configurando contenedor MySQL 8.4..."
NETWORK="ciencia-net"
MYSQL_CONTAINER="mysql84"

sudo docker network create "$NETWORK" 2>/dev/null || true

if [ ! "$(sudo docker ps -q -f name=^/${MYSQL_CONTAINER}$)" ]; then
    if [ "$(sudo docker ps -aq -f status=exited -f name=^/${MYSQL_CONTAINER}$)" ]; then
        echo "Iniciando contenedor existente $MYSQL_CONTAINER..."
        sudo docker start "$MYSQL_CONTAINER" >/dev/null
    else
        echo "Creando contenedor nuevo $MYSQL_CONTAINER..."
        sudo docker run -d \
            --name "$MYSQL_CONTAINER" \
            --network "$NETWORK" \
            -p 3306:3306 \
            -e MYSQL_ROOT_PASSWORD=root \
            -e MYSQL_DATABASE=astronomia \
            mysql:8.4 >/dev/null
    fi
    echo "Esperando 10 segundos a que MySQL acepte conexiones..."
    sleep 10
fi

# 5. Poblar datos
echo ""
echo "[5/6] Verificando / Poblando la base de datos 'astronomia'..."
python bd.py

# 6. Lanzar Streamlit
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
    echo "Error: No se encontró el archivo de la aplicación Streamlit."
    exit 1
fi