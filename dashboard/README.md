# Dashboard - Estructura Interna

Este archivo describe la organización interna del código fuente de la aplicación interactiva Streamlit, que permite explorar todos los hallazgos del análisis de accidentalidad en Bogotá.

## 📁 Archivos Principales

| Archivo | Descripción |
| :--- | :--- |
| `01_Context_&_Data.py` | **Punto de Entrada:** Archivo principal de la aplicación. Contiene la página inicial de Contexto y Datos y configura el *layout* y la navegación general del Dashboard. |
| `pages/` | Directorio que contiene los módulos para cada página de análisis detallado, las cuales se listan en la barra lateral del Dashboard. |
| `data.py` | Módulo de utilidades fundamental para la **carga eficiente** y el almacenamiento en caché (`@st.cache_data`) de los *datasets* procesados, asegurando velocidad en la navegación y la reactividad de la aplicación. |
| `custom_utils.py` | Funciones auxiliares específicas para el dashboard, como la configuración de estilos, creación de métricas clave o el manejo de llamadas a las visualizaciones. |

---

## ⚙️ Flujo de la Aplicación

La aplicación Streamlit sigue un flujo lógico y secuencial de análisis, reflejado en el orden numerado de los archivos en el directorio `pages/`:

1. **Carga de Datos:** El módulo `data.py` se encarga de importar de manera única los archivos procesados (`data/processed/*.csv`).
2. **Contexto (Página 1):** El archivo `01_Context_&_Data.py` actúa como la página de inicio, estableciendo el alcance y la fuente de datos.
3. **Visualización Secuencial (Páginas 2 a 6):** El resto de las páginas en `pages/` (`02_Summary_...` hasta `06_Conclusions_...`) guían al usuario a través del proceso completo de análisis exploratorio, desde la visión general hasta las conclusiones.

---

## 🚀 Ejecución

Para iniciar la aplicación, es necesario ejecutar el archivo principal desde la raíz del repositorio. Para la instalación de las dependencias, consulta la sección **Instalación y Ejecución Local** en el [README.md](../README.md) principal.

**Comando de ejecución (usando uv):**

```bash
uv run streamlit run dashboard/01_Context_\&_Data.py
```
