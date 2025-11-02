import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from dashboard.custom_utils import filter_data_by_date_range
from utils.load_data import load_processed_original_data, resample_data


def contingency_heatmap(df: pd.DataFrame) -> None:
    st.markdown("## Contingency Heatmap")

    interesting_columns = ["GRAVEDAD", "CLASE", "DIA_SEMANA_OCURRENCIA"]
    for col in interesting_columns:
        col_alias = col.replace("_", " ")
        st.markdown(f"### {col_alias} vs GRAVEDAD")

        contingency_table = pd.crosstab(
            df["LOCALIDAD"],
            df[col],
        )
        contingency_pct = (
            contingency_table.div(contingency_table.sum(axis=1), axis=0) * 100
        )

        fig, ax = plt.subplots(figsize=(8, 14))

        sns.heatmap(
            contingency_pct,
            annot=True,
            fmt=".1f",
            cmap="RdYlBu_r",
            ax=ax,
            linewidths=0.5,
            cbar_kws={"label": r"Pecentage (\%)"},
        )

        ax.set_title(rf"Perfil de {col_alias} por LOCALIDAD (\% por fila)")
        ax.set_xlabel(col_alias)
        ax.set_ylabel("LOCALIDAD")
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


def index(title: str = "Heat Maps") -> None:
    st.markdown(f"# {title}")
    st.warning("""
        TODO: :red[Write about the heat maps that will be shown here. Explain what they represent,
        the data source, and any relevant information for the user to understand the visualizations.]
    """)

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
        ].map(
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

        st.session_state.heatmap_cached_processed_data = processed_data
        st.session_state.heatmap_processed_data_needs_update = False

        print("Recalculating processed data")
    else:
        processed_data = st.session_state.heatmap_cached_processed_data
        print("Using cached processed data")

    # Get the available date range in the data
    min_date = processed_data.index.min().date()
    max_date = processed_data.index.max().date()

    # Create columns for date controls
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            label="Start Date:",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="start_date_input",
            on_change=lambda: st.session_state.update(
                {"heatmap_date_filter_changed": True}
            ),
        )

    with col2:
        end_date = st.date_input(
            label="End Date:",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="end_date_input",
            on_change=lambda: st.session_state.update(
                {"heatmap_date_filter_changed": True}
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

    frequency_options = {
        "Daily": "1D",
        "Weekly": "1W",
        "Biweekly": "2W",
        "Monthly": "1ME",
        "Quarterly": "3ME",
        "Yearly": "1Y",
        "Biennial": "2Y",
    }

    selected_frequency = st.selectbox(
        label="Select Resampling Frequency:",
        options=list(frequency_options.keys()),
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
            freq=frequency_options[selected_frequency],
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

    correlation_heatmap(resampled_data, freq_unit=selected_frequency)

    st.markdown("---")

    contingency_heatmap(processed_data)
