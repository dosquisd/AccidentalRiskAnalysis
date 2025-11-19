import streamlit as st


def index(title: str) -> None:
    st.markdown(f"# {title}")

    st.markdown("""
        ### 🎯 Síntesis del Análisis
        
        Tras procesar y visualizar más de 330.000 registros de siniestralidad vial en Bogotá (2007-2017), podemos afirmar que la accidentalidad **no es un fenómeno aleatorio**, sino un problema **estructural, cíclico y territorialmente desigual**.
        
        A continuación, se presentan los hallazgos definitivos clasificados por dimensiones:

        ---

        ### 1. 🌍 La Paradoja Espacial: Frecuencia vs. Severidad

        Existe una desconexión clara entre dónde ocurren más accidentes y dónde son más graves.
        
        * **Zona Norte (Alta Frecuencia):** Localidades como **Engativá, Suba y Usaquén** lideran en cantidad total de eventos. Sin embargo, la gran mayoría son choques simples (solo daños).
        * **Zona Sur/Occidente (Alta Severidad):** Localidades como **Kennedy, Bosa, Rafael Uribe Uribe y Usme** presentan menos eventos totales, pero concentran la mayor cantidad de **heridos y fallecidos**.
        * **El Caso Kennedy:** Es la localidad más crítica del sistema, actuando como un "hub" de accidentalidad que influye fuertemente en todo el suroccidente de la ciudad.

        > **Conclusión:** La infraestructura y políticas en el Norte deben enfocarse en la *fluidez y reducción de choques*, mientras que en el Sur la prioridad absoluta debe ser la *protección de la vida y seguridad peatonal*.

        ---

        ### 2. ⏳ Patrones Temporales y Ciclos de Riesgo

        El tiempo es un factor determinante en la probabilidad de un siniestro.
        
        * **Ciclo Semanal:** El riesgo escala progresivamente desde el lunes, alcanzando su pico máximo los **viernes y sábados**.
        * **El "Domingo Peligroso":** Aunque los domingos hay menos accidentes en total, la variabilidad y la proporción de eventos graves aumentan, probablemente asociado a excesos de velocidad en vías más vacías y consumo de alcohol.
        * **Horarios Críticos:** * *Congestión:* 9:00 a.m. - 6:00 p.m. (Choques simples).
            * *Fatalidad:* 10:00 p.m. - 3:00 a.m. (Eventos con muertos).

        ---

        ### 3. 🔗 Clústeres y Conectividad (Análisis de Red)

        El análisis de correlaciones y Árbol de Expansión Mínima (MST) reveló cómo se agrupan las localidades:
        
        * **Clúster Oriental:** Orbitando alrededor de **Chapinero** (Teusaquillo, Barrios Unidos, Usaquén). Dinámica de centro financiero y comercial.
        * **Clúster Occidental:** Orbitando alrededor de **Kennedy** (Bosa, Ciudad Bolívar, Tunjuelito). Dinámica residencial densa y popular.
        * **El Puente:** **Puente Aranda** actúa como el conector estadístico entre el oriente y el occidente de la ciudad.

        ---

        ### 💡 Recomendaciones Basadas en Datos

        1.  **Intervención Focalizada:** No se pueden aplicar las mismas estrategias en toda la ciudad. 
            * *En Kennedy y el Sur:* Implementar pacificación vial, reductores de velocidad y pasos peatonales seguros para reducir la severidad.
            * *En Chapinero y el Norte:* Mejorar la señalización y gestión del tráfico para reducir la frecuencia de choques.
        2.  **Vigilancia Horaria:** Reforzar los controles de alcoholemia y velocidad específicamente en la franja **viernes/sábado noche (10pm - 3am)**, donde ocurre la mortalidad, y no solo en horas pico diurnas.
        3.  **Gestión de Eventos Atípicos:** Los "outliers" detectados en los diagramas de caja sugieren que eventos específicos (lluvia, festivos, obras) disparan la accidentalidad. Se requieren protocolos de respuesta rápida para días de alta variabilidad.
    """)


if __name__ == "__main__":
    title = "🏁 Conclusiones"
    st.set_page_config(page_title=title, layout="wide")
    index(title)
