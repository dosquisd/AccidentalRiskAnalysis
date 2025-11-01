from datetime import date

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from dashboard.custom_utils import filter_data_by_date_range
from utils.constants import RAW_DATA_DIR
from utils.load_data import load_processed_original_data

LOCALIDAD_SHAPEFILE = RAW_DATA_DIR / "poligonos-localidades.zip"


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
    st.dataframe(metrics_df[column].sort_values(ascending=False))
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


def localities_index(title: str = "Grouped by Localities") -> None:
    st.markdown(f"# {title}")
    st.warning("""
        TODO: :red[Write about the map that will be shown here. Explain what it represents,
        the data source, and any relevant information for the user to understand the map.]
    """)

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
                {
                    1: "MONDAY",
                    2: "TUESDAY",
                    3: "WEDNESDAY",
                    4: "THURSDAY",
                    5: "FRIDAY",
                    6: "SATURDAY",
                    7: "SUNDAY",
                }
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

    # Get the available date range in the data
    min_date = gdf.index.min().date()
    max_date = gdf.index.max().date()

    # Create columns for date controls
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            label="Start Date:",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="localities_start_date_input",
            on_change=lambda: st.session_state.update(
                {"localities_date_filter_changed": True}
            ),
        )

    with col2:
        end_date = st.date_input(
            label="End Date:",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="localities_end_date_input",
            on_change=lambda: st.session_state.update(
                {"localities_date_filter_changed": True}
            ),
        )

    # Validate that the start date is earlier than the end date
    if start_date > end_date:
        st.error("⚠️ The start date must be earlier than the end date.")
        return

    # Show information about the selected range
    days_selected = (end_date - start_date).days + 1
    st.info(
        f"📅 Selected range: **{days_selected} days** ({start_date} to {end_date})"
    )

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
        return

    metric_count_per_locality(
        filtered_gdf, start_date=start_date, end_date=end_date
    )
