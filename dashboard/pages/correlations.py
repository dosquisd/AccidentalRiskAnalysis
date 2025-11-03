from typing import Dict, TypedDict

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from folium import CircleMarker, PolyLine
from streamlit_folium import st_folium

from dashboard.custom_utils import (
    DAY_OF_WEEK_MAP,
    FOLIUM_COLORS,
    FREQUENCY_OPTIONS,
    filter_data_by_date_range,
    select_dates,
)
from utils.constants import RAW_DATA_DIR
from utils.load_data import load_processed_original_data, resample_data

LOCALIDAD_SHAPEFILE = RAW_DATA_DIR / "poligonos-localidades.zip"


class LoadDataResult(TypedDict):
    processed_data: pd.DataFrame
    resampled_data: pd.DataFrame
    freq: str


def load_locality_geopoints() -> gpd.GeoDataFrame:
    # Load the processed original data as a GeoDataFrame
    original_gdf = load_processed_original_data(
        as_geopandas=True, parse_dates=True
    )

    localities_cols = list(original_gdf["LOCALIDAD"].unique())

    # Load the locality shapefile
    localities = gpd.read_file(LOCALIDAD_SHAPEFILE).to_crs("EPSG:4326")
    localities["centroid"] = localities["geometry"].centroid.to_crs("EPSG:4326")

    # Filter localities to only those present in the original data
    localities = localities[localities["Nombre_de_l"].isin(localities_cols)]

    # Drop unnecesary columns and rename
    localities.drop(
        columns=["Acto_admini", "Area_de_la_", "Identificad"], inplace=True
    )
    localities.rename(columns={"Nombre_de_l": "LOCALIDAD"}, inplace=True)

    return localities


def get_folium_map(
    *,
    localities: gpd.GeoDataFrame,
    dist_matrix: pd.DataFrame,
    mst: nx.Graph,
    degree_centrality: Dict[str, float],
    betweenness_centrality: Dict[str, float],
    closeness_centrality: Dict[str, float],
) -> folium.Map:
    localities_centroids = (
        localities[["LOCALIDAD", "centroid"]]
        .set_index("LOCALIDAD")
        .to_dict()["centroid"]
    )

    localities_centroids = dict(
        map(
            lambda item: (item[0], (item[1].xy[0][0], item[1].xy[1][0])),
            localities_centroids.items(),
        )
    )

    mid_point = localities.centroid.union_all().centroid.coords[0][::-1]
    bogota_map = folium.Map(
        location=mid_point,
        zoom_start=10,
        tiles="openstreetmap",
    )
    geo_df_list = [
        [point.xy[1][0], point.xy[0][0]] for point in localities.centroid
    ]
    n_colors = len(FOLIUM_COLORS)
    locality_color = dict(
        (loc, FOLIUM_COLORS[i % n_colors])
        for i, loc in enumerate(localities.LOCALIDAD)
    )

    for i, coordinates in enumerate(geo_df_list):
        # Place the markers with the popup labels and data
        locality = localities["LOCALIDAD"].iloc[i]

        # Plot the locality polygons
        polygon = folium.vector_layers.Polygon(
            locations=[
                [coord[1], coord[0]]
                for coord in localities["geometry"].iloc[i].exterior.coords
            ],
            color=locality_color[locality],
            fill=True,
            fill_color=locality_color[locality],
            fill_opacity=0.2,
        )
        polygon.add_to(bogota_map)

    # Add edges from the MST to the map
    for edge in mst.edges():
        node1, node2 = edge
        coord1 = localities_centroids[node1]
        coord2 = localities_centroids[node2]

        # Obtener el peso de la arista (distancia)
        weight = mst[node1][node2].get("weight", dist_matrix.loc[node1, node2])

        # Draw the edge between the two nodes
        PolyLine(
            locations=[(coord1[1], coord1[0]), (coord2[1], coord2[0])],
            color="blue",
            weight=2,
            opacity=0.8,
            tooltip=f"{node1} - {node2}: {weight:.2f}",
        ).add_to(bogota_map)

    # Add node as markers to the map
    for node, coord in localities_centroids.items():
        CircleMarker(
            location=[coord[1], coord[0]],
            radius=8,
            popup=(
                f"{node}\n"
                f"Degree: {degree_centrality[node]:.2f}\n"
                f"Betweenness: {betweenness_centrality[node]:.2f}\n"
                f"Closeness: {closeness_centrality[node]:.2f}"
            ),
            color="red",
            fill=True,
            fillColor="red",
            fillOpacity=0.9,
        ).add_to(bogota_map)

    return bogota_map


def contingency_heatmap(df: pd.DataFrame) -> None:
    st.markdown("## Contingency Heatmap")

    relevant_columns = [
        "LOCALIDAD",
        "GRAVEDAD",
        "CLASE",
        "DIA_SEMANA_OCURRENCIA",
    ]

    col1, col2 = st.columns(2)
    with col1:
        selected_col1 = st.selectbox(
            "Select column for contingency heatmap",
            relevant_columns,
            index=0,
        )
        col_alias1 = selected_col1.replace("_", " ")

    with col2:
        selected_col2 = st.selectbox(
            "Select column to compare",
            [col for col in relevant_columns if col != selected_col1],
            index=0,
        )
        col_alias2 = selected_col2.replace("_", " ")

    contingency_table = pd.crosstab(
        df[selected_col1],
        df[selected_col2],
    )
    contingency_pct = (
        contingency_table.div(contingency_table.sum(axis=1), axis=0) * 100
    )

    # TODO: Adjust figure size based on data shape
    base_figsize = (8, 14)
    if contingency_pct.shape[0] < contingency_pct.shape[1]:
        base_figsize = base_figsize[::-1]

    fig, ax = plt.subplots(figsize=base_figsize)

    sns.heatmap(
        contingency_pct,
        annot=True,
        fmt=".1f",
        cmap="RdYlBu_r",
        ax=ax,
        linewidths=0.5,
        cbar_kws={"label": r"Pecentage (\%)"},
    )

    ax.set_title(rf"Distribution of {col_alias2} by {col_alias1} (\% per row)")
    ax.set_xlabel(col_alias2)
    ax.set_ylabel(col_alias1)
    plt.yticks(rotation=0)
    fig.tight_layout()

    st.pyplot(fig)

    fig.clf()
    plt.close(fig)


def correlation_heatmap(
    df: pd.DataFrame = None,
    title: str = "Correlation Heatmap",
    freq_unit: str = "Weekly",
) -> None:
    st.markdown(f"## {title}")

    if df is None:
        df = resample_data(freq="1W", multi_index=True)
        freq_unit = "Weekly"

    freq_unit = freq_unit.title()

    # ==============================

    st.markdown("### Correlation Matrix")

    # Create correlation matrix between LOCALIDAD columns
    corr_matrix = df["LOCALIDAD"].corr()

    # Optional: Apply threshold to highlight strong correlations
    threshold = st.slider("Correlation Threshold", 0.0, 1.0, 0.0, 0.01)
    mask = abs(corr_matrix) >= threshold
    filtered_corr = corr_matrix.where(mask)

    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(
        filtered_corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        ax=ax,
        square=True,
        linewidths=0.5,
        cbar_kws={"label": "Correlation Coefficient"},
    )

    ax.set_title(f"Correlation between Localities ({freq_unit} Patterns)")
    ax.set_xlabel("LOCALIDAD")
    ax.set_ylabel("LOCALIDAD")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    fig.tight_layout()

    st.pyplot(fig)

    fig.clf()
    plt.close(fig)

    # ==============================

    st.markdown("### MST applied to LOCALIDAD distance matrix")

    st.markdown("""
        La matriz de distancia se calculó de esta manera:
                
        $$
        D_{i, j} = \sqrt{2(1 - C_{i, j})}
        $$
    """)

    if st.session_state.localities_geometry_gpd is None:
        localities_geometry_gpd = load_locality_geopoints()
        st.session_state.localities_geometry_gpd = localities_geometry_gpd
    else:
        localities_geometry_gpd = st.session_state.localities_geometry_gpd

    # Create a cache key based on the correlation matrix
    cache_key = hash(corr_matrix.values.tobytes())

    # Check if we need to recompute the MST and centrality metrics
    if (
        "mst_cache_key" not in st.session_state
        or st.session_state.mst_cache_key != cache_key
        or "mst_data" not in st.session_state
    ):
        dist_matrix = np.sqrt(2 * (1 - corr_matrix))
        graph = nx.from_pandas_adjacency(dist_matrix)
        mst = nx.minimum_spanning_tree(graph)
        degree_centrality = nx.degree_centrality(mst)
        betweenness_centrality = nx.betweenness_centrality(mst)
        closeness_centrality = nx.closeness_centrality(mst)

        # Cache the results
        st.session_state.mst_cache_key = cache_key
        st.session_state.mst_data = {
            "dist_matrix": dist_matrix,
            "mst": mst,
            "degree_centrality": degree_centrality,
            "betweenness_centrality": betweenness_centrality,
            "closeness_centrality": closeness_centrality,
        }
    else:
        # Use cached data
        cached_data = st.session_state.mst_data
        dist_matrix = cached_data["dist_matrix"]
        mst = cached_data["mst"]
        degree_centrality = cached_data["degree_centrality"]
        betweenness_centrality = cached_data["betweenness_centrality"]
        closeness_centrality = cached_data["closeness_centrality"]

    folium_map = get_folium_map(
        localities=localities_geometry_gpd,
        dist_matrix=dist_matrix,
        mst=mst,
        degree_centrality=degree_centrality,
        betweenness_centrality=betweenness_centrality,
        closeness_centrality=closeness_centrality,
    )

    st_folium(folium_map, width=700, height=500, returned_objects=[])

    # ==============================

    st.markdown("### GRAVEDAD vs CLASE correlation")

    gravedad_cols = list(df["GRAVEDAD"].columns)
    clase_cols = list(df["CLASE"].columns)
    heatmap_data = []
    for gravedad in gravedad_cols:
        row = []
        for clase in clase_cols:
            valor = df["GRAVEDAD"][gravedad].corr(df["CLASE"][clase])
            row.append(valor)
        heatmap_data.append(row)

    heatmap_df = pd.DataFrame(
        heatmap_data, index=gravedad_cols, columns=clase_cols
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    sns.heatmap(
        heatmap_df, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax
    )
    ax.set_title(
        f"Correlation between GRAVEDAD and CLASE ({freq_unit} Patterns)"
    )
    ax.set_xlabel("CLASE")
    ax.set_ylabel("GRAVEDAD")
    plt.xticks(rotation=15)
    fig.tight_layout()

    st.pyplot(fig)

    fig.clf()
    plt.close(fig)


def load_data() -> LoadDataResult | None:
    if (
        st.session_state.heatmap_processed_data_needs_update
        or st.session_state.heatmap_cached_processed_data is None
    ):
        processed_data = load_processed_original_data(
            as_geopandas=False,
            date_as_index=True,
            parse_dates=True,
        )
        processed_data["DIA_SEMANA_OCURRENCIA"] = processed_data[
            "DIA_SEMANA_OCURRENCIA"
        ].map(DAY_OF_WEEK_MAP)

        st.session_state.heatmap_cached_processed_data = processed_data
        st.session_state.heatmap_processed_data_needs_update = False

        print("Recalculating processed data")
    else:
        processed_data = st.session_state.heatmap_cached_processed_data
        print("Using cached processed data")

    start_date, end_date = select_dates(
        processed_data,
        key_prefix="heatmap",
        show_total_days=True,
    ) or (None, None)

    if start_date is None or end_date is None:
        return None

    selected_frequency = st.selectbox(
        label="Select Resampling Frequency:",
        options=list(FREQUENCY_OPTIONS.keys()),
        index=1,
        key="resample_frequency_selectbox",
        on_change=lambda: st.session_state.update(
            {"heatmap_resampled_data_needs_update": True}
        ),
    )

    # Use cached data to avoid unnecessary recomputation
    if (
        st.session_state.heatmap_resampled_data_needs_update
        or st.session_state.heatmap_date_filter_changed
        or st.session_state.heatmap_cached_resampled_data is None
    ):
        # First filter by dates
        filtered_data = filter_data_by_date_range(
            processed_data, start_date, end_date
        )

        # Then resample the filtered data
        resampled_data = resample_data(
            df=filtered_data,
            freq=FREQUENCY_OPTIONS[selected_frequency],
            multi_index=True,
        )

        st.session_state.heatmap_cached_resampled_data = resampled_data
        st.session_state.heatmap_resampled_data_needs_update = False
        st.session_state.heatmap_date_filter_changed = False

        print(
            f"Recalculating data: {selected_frequency}, {start_date} to {end_date}"
        )
    else:
        resampled_data = st.session_state.heatmap_cached_resampled_data
        print(f"Using cached data: {selected_frequency}")

    return {
        "processed_data": processed_data,
        "resampled_data": resampled_data,
        "freq": selected_frequency,
    }


def index(title: str = "Correlation between variables") -> None:
    st.markdown(f"## {title}")

    # Initialize session state
    if "localities_geometry_gpd" not in st.session_state:
        st.session_state.localities_geometry_gpd = None
    if "mst_cache_key" not in st.session_state:
        st.session_state.mst_cache_key = None
    if "mst_data" not in st.session_state:
        st.session_state.mst_data = None
    if "heatmap_processed_data_needs_update" not in st.session_state:
        st.session_state.heatmap_processed_data_needs_update = True
    if "heatmap_cached_processed_data" not in st.session_state:
        st.session_state.heatmap_cached_processed_data = None
    if "heatmap_resampled_data_needs_update" not in st.session_state:
        st.session_state.heatmap_resampled_data_needs_update = True
    if "heatmap_cached_resampled_data" not in st.session_state:
        st.session_state.heatmap_cached_resampled_data = None
    if "heatmap_date_filter_changed" not in st.session_state:
        st.session_state.heatmap_date_filter_changed = True

    data_loaded = load_data()
    if data_loaded is None:
        return None

    processed_data = data_loaded["processed_data"]
    resampled_data = data_loaded["resampled_data"]
    selected_frequency = data_loaded["freq"]

    correlation_heatmap(resampled_data, freq_unit=selected_frequency)

    st.markdown("---")

    contingency_heatmap(processed_data)


if __name__ == "__main__":
    title = "Correlation Analysis"
    st.set_page_config(page_title=title, layout="centered")
    index(title)
