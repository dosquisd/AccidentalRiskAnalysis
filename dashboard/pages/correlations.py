from typing import TypedDict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from dashboard.custom_utils import (
    DAY_OF_WEEK_MAP,
    FREQUENCY_OPTIONS,
    filter_data_by_date_range,
    select_dates,
)
from utils.load_data import load_processed_original_data, resample_data


class LoadDataResult(TypedDict):
    processed_data: pd.DataFrame
    resampled_data: pd.DataFrame
    freq: str


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
