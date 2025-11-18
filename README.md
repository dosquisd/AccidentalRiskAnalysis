# Análisis Exploratorio de Patrones de Accidentalidad Vial en Bogotá (2007-2017)

## 📋 Descripción del Proyecto

Este proyecto analiza la accidentalidad vial en Bogotá (2007-2017), procesando más de 330.000 registros para identificar patrones clave. Mediante limpieza y visualización de datos, se determinó que el fenómeno es territorialmente desigual: Engativá lidera en frecuencia total, pero Kennedy concentra la mayor severidad con más heridos y fallecidos. Se detectaron ciclos recurrentes con picos los viernes y sábados, predominando los choques simples (cerca del 80%) sobre los atropellos, que generan más víctimas. El análisis revela clústeres diferenciados entre el norte (alta frecuencia, baja gravedad) y el sur (alta severidad), evidenciando la necesidad de estrategias de prevención adaptadas a las dinámicas específicas de cada localidad.

El repositorio incluye un Dashboard interactivo desarrollado en **Streamlit** para explorar estos hallazgos.

---

**Para más información sobre el análisis completo de los resultados, metodologías aplicadas y conclusiones en detalle, ver [aquí](./docs/AnalisisAccidentalibilidadEnBogota.pdf)**

---

## 📂 Estructura del Repositorio

El proyecto está organizado de manera modular para facilitar la reproducibilidad y el escalamiento:

```text
.
├── dashboard/           # Código fuente del Dashboard interactivo (Streamlit)
│   ├── pages/           # Páginas individuales de la aplicación (Análisis temporal, correlaciones, etc.)
│   └── ...              # Scripts de contexto y utilidades de visualización
├── data/                # Almacenamiento de datos (Git-ignored por defecto las fuentes grandes)
│   ├── raw/             # Datos crudos originales (CSV, GeoJSON)
│   └── processed/       # Datos limpios y transformados listos para análisis
├── deployment/          # Configuración para despliegue en producción
│   ├── docker-compose.yml  # Orquestación de servicios (Traefik + Dashboard)
│   ├── .env.example     # Plantilla de variables de entorno
│   └── README.md        # Guía técnica de despliegue
├── figures/             # Visualizaciones estáticas generadas (PDF, HTML)
│   ├── barplots/        # Gráficos de barras
│   ├── maps/            # Mapas interactivos y estáticos de localidades
│   └── ...              # Boxplots, Heatmaps, etc.
├── notebooks/           # Jupyter Notebooks numerados secuencialmente (ETL y EDA)
│   ├── 001_...          # Carga de datos
│   ├── ...              # Limpieza y transformación
│   └── 013_...          # Generación de mapas y gráficos finales
├── utils/               # Módulos auxiliares de Python (Carga de datos, configuración de plots)
├── dashboard.Dockerfile # Configuración para contenedorizar la aplicación
├── pyproject.toml       # Definición de dependencias y configuración del proyecto
└── uv.lock              # Archivo de bloqueo de versiones (para uv)
```

---

## 🚀 Instalación y Ejecución Local

Este proyecto utiliza uv para una gestión de dependencias extremadamente rápida y eficiente.

### Prerrequisitos

* Python 3.12+
* Git
* [uv](https://docs.astral.sh/uv/getting-started/installation/) (Recomendado) o Docker.

### Opción A: Ejecución local con `uv` (Recomendada)

1. **Clonar el repositorio:**

```bash
git clone https://github.com/dosquisd/AccidentalRiskAnalysis.git
cd AccidentalRiskAnalysis
```

2. **Instalar dependencias y sincronizar el entorno:** `uv` creará un entorno virtual y gestionará todas las librerías automáticamente basándose en `uv.lock`.

```bash
uv sync
```

3. **Ejecutar el Dashboard:** Utiliza `uv` run para lanzar Streamlit dentro del entorno gestionado.

```bash
uv run -m streamlit run dashboard/01_Context_\&_Data.py
```

### Opción B: Ejecución con Docker

Si prefieres usar contenedores, el proyecto incluye un `Dockerfile` optimizado.

1. **Construir la imagen:**

```bash
docker build -t bogota-accidents-dashboard -f dashboard.Dockerfile .
```

2. **Correr el contenedor:** El dashboard estará disponible en el puerto 8501.

```bash
docker run -p 8501:8501 bogota-accidents-dashboard
```

Una vez ejecutado (por cualquier método), abre tu navegador en: `http://localhost:8501`

## 🌐 Despliegue en Producción

Para desplegar el dashboard en un entorno de producción con HTTPS, reverse proxy y alta disponibilidad, consulta la guía técnica completa en [deployment/README.md](./deployment/README.md).

La configuración de despliegue incluye:

* Orquestación con Docker Compose
* Reverse proxy con Traefik
* Certificados SSL automáticos con Let's Encrypt
* Configuración lista para servidores en la nube

## 🛠️ Tecnologías Utilizadas

* Lenguaje: Python 3.12
* Gestión de Paquetes: uv
* Visualización: Matplotlib, Seaborn, Folium (Mapas).
* Dashboard: Streamlit
* Procesamiento de Datos: Pandas, GeoPandas.

---

## 📊 Origen de los Datos

La fuente de información corresponde al conjunto de datos abiertos **Movilidata Bogotá**, disponible en el siguiente enlace: [https://transport.opendatasoft.com/pages/home/](https://transport.opendatasoft.com/pages/home/). Para más información de los datos descargados, ver [data/raw/README.md](./data/raw/README.md).

* **Volumen:** Más de 330.000 registros procesados.
* **Variables principales:**
  * `FECHA_OCURRENCIA`: Fecha y hora del siniestro.
  * `LOCALIDAD`: Ubicación administrativa y coordenadas [latitud/longitud].
  * `CLASE`: Tipo de accidente [choque, atropello, volcamiento, etc.].
  * `GRAVEDAD`: Nivel de impacto [solo daños, heridos, muertos].

## 🛠️ Metodología

El flujo de trabajo incluyó las siguientes etapas de procesamiento:

1. **Limpieza de Datos:** Eliminación de registros nulos e inconsistencias.
2. **Ingeniería de Características:** Descomposición de variables temporales y codificación numérica de variables categóricas (`CLASE_code`, `GRAVEDAD_code`).
3. **Análisis Espacial:** Estudio de concentración de accidentes por localidad.
4. **Correlación:** Uso de matrices de Pearson para evaluar la relación entre localidades.

## 🔍 Hallazgos Clave

### 1. Distribución Espacial y Severidad

Existe una desconexión entre la frecuencia y la gravedad de los accidentes:

* **Engativá** es la localidad con mayor número absoluto de accidentes [35.128 casos].
* **Kennedy**, sin embargo, concentra los incidentes más graves (heridos y fallecidos) y la mayor cantidad de atropellos.
* **Usaquén** lidera en "Choques" simples y eventos de solo daños.

### 2. Patrones Temporales

* **Ciclo Semanal:** Los accidentes aumentan progresivamente de lunes a viernes/sábado. Los domingos, aunque baja la frecuencia total, aumenta la variabilidad y el riesgo relativo.
* **Horarios:** La mayor concentración de eventos ocurre en horario diurno (9:00 a.m. - 6:00 p.m.), coincidiendo con la movilidad laboral. Los accidentes fatales tienden a concentrarse en horarios nocturnos [10:00 p.m. - 3:00 a.m.].

### 3. Tipología de Accidentes

* Los **Choques** representan cerca del 80% de los casos y están asociados casi exclusivamente a daños materiales.
* Los **Atropellos**, aunque menos frecuentes, son los principales causantes de lesiones y muertes.

## 📈 Dashboard

Este repositorio incluye el código fuente para un dashboard interactivo desarrollado con **Streamlit**, que presenta de forma navegable e intuitiva todo el análisis exploratorio del proyecto.

El dashboard está dividido en las siguientes secciones, que corresponden a los archivos en la carpeta `dashboard/pages/`:

* **Contexto y Datos**: Presentación del objetivo del proyecto y detalles de la fuente de datos.
* **Resumen y Visión General**: Estadísticas clave sobre frecuencia y gravedad de accidentes por localidad (Ejemplo: Engativá vs. Kennedy).
* **Evolución Temporal**: Análisis detallado de las tendencias, picos y ciclos (anual, mensual, semanal) de la accidentalidad.
* **Correlación entre Variables**: Visualización de las matrices de correlación (Pearson) para entender la relación entre la actividad de las distintas localidades.
* **Análisis de Distribución**: Estudio espacial y categórico que compara la tipología de accidentes (Choques vs. Atropellos) y la disparidad Norte/Sur.
* **Conclusiones**: Recapitulación de los hallazgos y su impacto en la toma de decisiones para la seguridad vial.

Para ejecutar la aplicación, consulta la sección [Instalación y Ejecución Local](#-instalación-y-ejecución-local) del `README.md` principal.

Para más información sobre la estructura interna, ver [dashboard/README.md](./dashboard/README.md)

---

## 👥 Autores

Proyecto realizado para la asignatura **Programación para Ciencia de Datos** de la Universidad Tecnológica de Bolívar:

* Isabella Márquez Vides
* Ana Sofía Meza Herrera
* Zulianys Liseth Orozco Chávez
* Juan Diego Pérez Navarro
