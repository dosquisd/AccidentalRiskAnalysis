from datetime import date
from typing import TypedDict

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from dashboard.custom_utils import (
    DAY_OF_WEEK_MAP,
    filter_data_by_date_range,
    select_dates,
)
from utils.constants import RAW_DATA_DIR
from utils.load_data import load_processed_original_data

LOCALIDAD_SHAPEFILE = RAW_DATA_DIR / "poligonos-localidades.zip"


class LoadDataResult(TypedDict):
    gdf: gpd.GeoDataFrame
    start_date: date
    end_date: date


def plot_localities_map(
    gdf: gpd.GeoDataFrame, metric_col: str, start_date: date, end_date: date
) -> None:
    st.markdown("### Localities Map")

    start_year, end_year = start_date.year, end_date.year

    mid_point = gdf.geometry.centroid.union_all().centroid.coords[0][::-1]
    bogota_map = folium.Map(
        location=mid_point,
        zoom_start=10,
        tiles="openstreetmap",
    )

    # Add metric layer
    choropleth = folium.Choropleth(
        geo_data=gdf,
        data=gdf,
        columns=["LOCALIDAD", "ACCIDENTES"],
        key_on="feature.properties.LOCALIDAD",
        fill_color="YlOrRd",
        fill_opacity=0.9,
        line_opacity=0.5,
        legend_name=f"{metric_col} ({start_year}-{end_year})",
        nan_fill_color="white",
        nan_fill_opacity=0.4,
    ).add_to(bogota_map)

    # Add tooltips
    folium.GeoJsonTooltip(
        fields=["LOCALIDAD", "ACCIDENTES"],
        aliases=["Localidad:", "Accidentes:"],
        localize=True,
    ).add_to(choropleth.geojson)

    st_folium(
        bogota_map,
        width=None,
        height=800,
        returned_objects=[],
    )


def metric_count_per_locality(
    gdf: gpd.GeoDataFrame, start_date: date, end_date: date
) -> None:
    st.markdown("## Metric Count per Locality")

    if (
        st.session_state.localities_grouped_data is None
        or st.session_state.localities_date_filter_changed
    ):
        metrics_df = (
            gdf.groupby("LOCALIDAD")
            .agg(
                {
                    "GRAVEDAD": lambda x: x.value_counts().to_dict(),
                    "CLASE": lambda x: x.value_counts().to_dict(),
                    "DIA_SEMANA_OCURRENCIA": lambda x: x.value_counts().to_dict(),
                    "OBJECTID": "size",
                    "localidad_geometry": "first",
                },
            )
            .rename(columns={"OBJECTID": "TOTAL_ACCIDENTES"})
        )

        dict_columns = ["GRAVEDAD", "CLASE", "DIA_SEMANA_OCURRENCIA"]
        for col in dict_columns:
            expanded_cols = (
                metrics_df[col].apply(pd.Series).fillna(0).astype(int)
            )
            expanded_cols.columns = [
                f"{col}-{str(c).replace(' ', '_')}"
                for c in expanded_cols.columns
            ]
            metrics_df = pd.concat(
                [metrics_df.drop(columns=[col]), expanded_cols], axis=1
            )

        metrics_df = gpd.GeoDataFrame(metrics_df, geometry="localidad_geometry")
        st.session_state.localities_grouped_data = metrics_df
    else:
        metrics_df = st.session_state.localities_grouped_data

    col1, col2 = st.columns([3, 1])
    metrics_options = [
        "TOTAL_ACCIDENTES",
        "GRAVEDAD",
        "CLASE",
        "DIA_SEMANA_OCURRENCIA",
    ]
    with col1:
        selected_metric = st.selectbox(
            "Select Metric to Display:",
            list(map(lambda x: x.replace("_", " ").title(), metrics_options)),
            key="localities_metric_selectbox",
        )
        selected_metric = selected_metric.replace(" ", "_").upper()

    with col2:
        if selected_metric == "TOTAL_ACCIDENTES":
            st.markdown("No aplicable")
            selected_submetric = ""
        else:
            metric_values = metrics_df.filter(
                regex=f"^{selected_metric}-"
            ).columns.tolist()
            selected_submetric = st.selectbox(
                "Select Sub-metric:",
                list(
                    map(
                        lambda x: x.split("-", 1)[1].replace("_", " ").title(),
                        metric_values,
                    )
                ),
                key="localities_submetric_selectbox",
            )
            selected_submetric = selected_submetric.replace(" ", "_").upper()

    column = (
        f"{selected_metric}-{selected_submetric}"
        if selected_submetric
        else selected_metric
    )
    metrics_df = metrics_df[[column, "localidad_geometry"]]
    plot_localities_map(
        gdf=(
            metrics_df.rename(columns={column: "ACCIDENTES"})
            .reset_index()
            .set_crs("EPSG:4326")
        ),
        metric_col=column,
        start_date=start_date,
        end_date=end_date,
    )


def load_data() -> LoadDataResult | None:
    if (
        not st.session_state.localities_geopandas_loaded
        or st.session_state.localities_gdf is None
    ):
        with st.spinner("Loading data..."):
            gdf: gpd.GeoDataFrame = load_processed_original_data(
                as_geopandas=True,
                parse_dates=True,
                date_as_index=False,
            )

            gdf["DIA_SEMANA_OCURRENCIA"] = gdf["DIA_SEMANA_OCURRENCIA"].map(
                DAY_OF_WEEK_MAP
            )

            localities_cols = list(gdf["LOCALIDAD"].unique())

            # Load the locality shapefile
            localities = gpd.read_file(LOCALIDAD_SHAPEFILE).to_crs("EPSG:4326")

            # Filter localities to only those present in the original data
            localities = localities[
                localities["Nombre_de_l"].isin(localities_cols)
            ]

            # Drop unnecesary columns and rename
            localities.drop(
                columns=["Acto_admini", "Area_de_la_", "Identificad"],
                inplace=True,
            )
            localities.rename(
                columns={"Nombre_de_l": "LOCALIDAD"}, inplace=True
            )

            gdf = gdf.merge(
                localities[["LOCALIDAD", "geometry"]], on="LOCALIDAD"
            )

            gdf.rename(
                columns={
                    "geometry_x": "geometry",
                    "geometry_y": "localidad_geometry",
                },
                inplace=True,
            )

            gdf.set_index("FECHA_OCURRENCIA", inplace=True)
            gdf.set_geometry("localidad_geometry")

            st.session_state.localities_geopandas_loaded = True
            st.session_state.localities_gdf = gdf
            st.session_state.localities_grouped_data = None
    else:
        gdf = st.session_state.localities_gdf

    start_date, end_date = select_dates(
        gdf,
        key_prefix="localities",
        show_total_days=True,
    ) or (None, None)

    if start_date is None or end_date is None:
        return None

    if (
        st.session_state.localities_date_filter_changed
        or st.session_state.localities_filtered_gdf is None
    ):
        with st.spinner("Filtering data by date range..."):
            filtered_gdf = filter_data_by_date_range(
                gdf,
                start_date,
                end_date,
            )
            st.session_state.localities_filtered_gdf = filtered_gdf
            st.session_state.localities_date_filter_changed = False
            st.session_state.localities_grouped_data = None
    else:
        filtered_gdf = st.session_state.localities_filtered_gdf

    if filtered_gdf.empty:
        st.warning("No accident data available for the selected date range.")
        return None

    return {
        "gdf": filtered_gdf,
        "start_date": start_date,
        "end_date": end_date,
    }


def index(title: str = "Summary") -> None:
    st.markdown(f"# {title}")

    # Initialize session states
    if "localities_geopandas_loaded" not in st.session_state:
        st.session_state.localities_geopandas_loaded = False
    if "localities_gdf" not in st.session_state:
        st.session_state.localities_gdf = None
    if "localities_date_filter_changed" not in st.session_state:
        st.session_state.localities_date_filter_changed = True
    if "localities_filtered_gdf" not in st.session_state:
        st.session_state.localities_filtered_gdf = None
    if "localities_grouped_data" not in st.session_state:
        st.session_state.localities_grouped_data = None

    data_loaded = load_data()
    print(data_loaded)

    if data_loaded is None:
        return None
    
    filtered_gdf = data_loaded["gdf"]
    start_date = data_loaded["start_date"]
    end_date = data_loaded["end_date"]

    metric_count_per_locality(
        filtered_gdf, start_date=start_date, end_date=end_date
    )

    st.markdown("---")

    st.markdown("""
        ## ¿Cuáles son las localidades con mayor cantidad de accidentes en Bogotá?

        La mayor concentración de accidentes durante el periodo de 2007 y 2017 se ubicó en la zona norte de la ciudad.

        * Engativá es la localidad con mayor número de accidentes registrados en el periodo analizado, con un total de 35.128 casos. Le siguen Suba, Usaquén y Kennedy, que también presentan altos niveles de accidentalidad.

        ## ¿Cómo cambia la distribución de accidentes si filtramos por gravedad, clase o día de la semana?

        Respecto a la gravedad, los patrones cambian:

        * Kennedy presenta la mayor cantidad de accidentes con heridos, así como con muertos seguido de Engativá y Suba.
        * Cuando se analizan los accidentes solo con daños, Usaquén es la localidad que cuenta con más casos, seguida de Suba y Engativá.

        En cuanto a la clase, se logró observar que:

        * Kennedy es la localidad con mayor número de atropellos, así como de volcamientos, caídas del ocupante y autolesiones, seguida de Engativá y Suba.
        * En el caso de los choques, la localidad predominante es Usaquén, seguida por Engativá y suba.
        * La cantidad de incendios alrededor de los años es mínima respecto al resto de clases; sin embargo, Santa Fe con 4 casos registrados, la cantidad más alta en una localidad, seguida de Kennedy y Chapinero con 3 cada una.

        Por último, la distribución según los días de semana es la siguiente:

        * De martes a viernes, el orden de accidentalidad por localidad es estable y constante, con un orden de Usaquén, Engativá, Suba y Kennedy.
        * Los lunes, el patrón cambia ligeramente, Engativá se convierte en la localidad con más accidentes, seguida por Usaquén, Suba y Kennedy.
        * Durante los fines de semana, la dinámica cambia de forma más marcada:
        * Sábados: Suba, Kennedy, Engativá y Usaquén.
        * Domingos: Kennedy pasa a ser la localidad con mayor accidentalidad, seguida por Engativá, Suba y Usaquén.
                
        ## Conclusiones

        A pesar de que Engativá es la localidad con mayor cantidad de accidentes registrados en el periodo analizado, Kennedy concentra los incidentes más graves, tanto con heridos como con fallecidos, además, predomina en la mayoría de las clases. Por otro lado, Usaquén sobresale al ser la localidad con mayor número de eventos que solo involucran daños, así como por registrar la mayor cantidad de choques.

        En cuanto a la distribución por días de la semana, durante los días laborales predominan Usaquén, Engativá y Suba en número total de accidentes, mientras que Kennedy toma mayor relevancia los fines de semana, llegando a ser la localidad con más siniestros los domingos.

        Este contraste evidencia que la frecuencia de accidentes no necesariamente se asocia a mayor severidad y que la dinámica de accidentalidad depende también del comportamiento y movilidad según el día de la semana.
    """)


if __name__ == "__main__":
    title = "Summary"
    st.set_page_config(page_title=title, layout="wide")
    index(title)
