# Sistema de Análisis Exoplanetario

Aplicación web desarrollada en Streamlit para el análisis y visualización de datos exoplanetarios provenientes de la API de la NASA.

## Requisitos previos

* Sistema operativo basado en Debian o Ubuntu.
* Docker instalado y con permisos para ejecutar sin `sudo` o acceso a `sudo`.
* Conexión a internet.

## Instalación y ejecución automática

El script `instalar.sh` automatiza la instalación de paquetes del sistema, la configuración del entorno virtual, el despliegue del contenedor MySQL 8.4, la extracción de datos y el inicio de la interfaz.

1. Clonar el repositorio:

```bash
git clone https://github.com/isabelnieto900/app-exoplanetas.git
cd app-exoplanetas

```

2. Otorgar permisos de ejecución:

```bash
chmod +x instalar.sh

```

3. Ejecutar el script:

```bash
./instalar.sh

```

4. Abrir la aplicación en el navegador:

```text
http://localhost:8501

```

## Estructura del proyecto

* `instalar.sh`: Script de instalación, configuración del contenedor MySQL e inicio de la aplicación.
* `bd.py`: Pipeline ETL que descarga los datos desde la NASA TAP API, normaliza el modelo relacional e inserta los registros en MySQL.


* `4astronomia_app.py`: Código de la interfaz visual y consultas analíticas en Streamlit.



## Parámetros de conexión a la base de datos

* Host: `localhost`

* Puerto: `3306`

* Base de datos: `astronomia`

* Usuario: `root`

* Contraseña: `root`
