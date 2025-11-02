from typing import Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from dashboard.custom_utils import (
    DAY_OF_WEEK_MAP,
    FREQUENCY_OPTIONS,
    transform_resample_data_for_boxplot,
)
from utils.load_data import load_processed_original_data, resample_data


def show_boxplot(
    df: pd.DataFrame,
    metric: Optional[str] = None,
    labels_kwargs: Dict[str, str] = None,
    y: Optional[str] = None,
    palette: Optional[str] = None,
    show_violin: bool = False,
    show_points: bool = False,
    parse_metric: bool = True,
) -> None:
    if not y:
        y = "value"

    if labels_kwargs is None:
        labels_kwargs = {}

    if not palette:
        palette = "Set2"

    if parse_metric and metric:
        df[metric] = df[metric].apply(
            lambda x: x.strip().replace("_", " ").title()
        )

    palette = sns.color_palette(palette)
    fig, ax = plt.subplots(figsize=(10, 6))

    if show_violin:
        sns.violinplot(
            data=df,
            x=metric,
            y=y,
            ax=ax,
            inner=None,
            palette=palette,
            linewidth=0.5,
            alpha=0.3,
        )

    if show_points:
        sns.stripplot(
            data=df,
            x=metric,
            y=y,
            color="black",
            alpha=0.4,
            jitter=True,
            ax=ax,
        )

    sns.boxplot(data=df, x=metric, y=y, ax=ax, width=0.3, palette=palette)
    ax.set(**labels_kwargs)
    ax.grid(True, linestyle="--", alpha=0.6)

    xticks_labels = ax.get_xticklabels()
    n_labels = len(xticks_labels)
    rotation = 15
    ha = "center"
    if n_labels < 4:
        rotation = 0
    elif n_labels < 10:
        if all(len(label.get_text()) < 10 for label in xticks_labels):
            rotation = 0
    else:
        rotation = 45
        ha = "right"

    ax.set_xticklabels(xticks_labels, rotation=rotation, ha=ha)

    st.pyplot(fig)

    fig.clf()
    plt.close(fig)


def show_distrubution_over_time(
    df: pd.DataFrame,
    selected_frequency: str,
    columns_options: list[str],
) -> None:
    st.markdown("## Distribution of Accidents Over Time")

    selected_metric = st.selectbox(
        label="Select Metric for Box Plot:",
        options=columns_options,
        index=0,
        key="boxplots_metric_selectbox",
        on_change=lambda: st.session_state.update(
            {"boxplots_transformed_data_needs_update": True}
        ),
    )

    if (
        st.session_state.boxplots_transformed_data_needs_update
        or st.session_state.boxplots_cached_transformed_data is None
    ):
        transformed_data = transform_resample_data_for_boxplot(
            df=df,
            col=selected_metric,
            multi_index=True,
        )

        st.session_state.boxplots_transformed_data_needs_update = False
        st.session_state.boxplots_cached_transformed_data = transformed_data
    else:
        transformed_data = st.session_state.boxplots_cached_transformed_data

    col1, col2 = st.columns([2, 2])
    with col1:
        show_violin = st.checkbox(
            label="Show Violin Plot",
            value=False,
            key="distribution_boxplots_show_violin_checkbox",
        )

    with col2:
        show_points = st.checkbox(
            label="Show Data Points",
            value=False,
            key="distribution_boxplots_show_points_checkbox",
        )

    show_boxplot(
        df=transformed_data,
        metric=selected_metric,
        labels_kwargs={
            "title": f"Box Plot of {selected_metric} ({selected_frequency})",
            "xlabel": "",
            "ylabel": "",
        },
        y="value",
        palette="Set2",
        show_violin=show_violin,
        show_points=show_points,
        parse_metric=True,
    )


def compare_boxplots_between_hours(
    df: pd.DataFrame,
    columns_options: list[str],
) -> None:
    st.markdown("## Variable vs Hour of Day")

    selected_metric = st.selectbox(
        label="Select Metric for Box Plot:",
        options=columns_options,
        index=0,
    )

    if selected_metric == "TOTAL_ACCIDENTES":
        selected_metric = None

    show_violin = st.checkbox(
        label="Show Violin Plot",
        value=False,
        key="hours_boxplots_show_violin_checkbox",
    )

    show_boxplot(
        df=df,
        metric=selected_metric,
        labels_kwargs={
            "title": "Box Plot of Variables vs Hour of Day",
            "ylabel": "Hour of Day",
            "xlabel": "",
        },
        y="HORA",
        palette="Set2",
        show_violin=show_violin,
        show_points=False,
        parse_metric=True,
    )


def index(title: str = "Box Plots") -> None:
    st.markdown(f"# {title}")
    st.warning("""
        TODO: :red[Write about the box plots that will be shown here. Explain what they represent,
        the data source, and any relevant information for the user to understand the visualizations.]
    """)

    # Initialize session state
    if "boxplots_processed_data_needs_update" not in st.session_state:
        st.session_state.boxplots_processed_data_needs_update = True
    if "boxplots_cached_processed_data" not in st.session_state:
        st.session_state.boxplots_cached_processed_data = None
    if "boxplots_resample_data_needs_update" not in st.session_state:
        st.session_state.boxplots_resample_data_needs_update = True
    if "boxplots_cached_resampled_data" not in st.session_state:
        st.session_state.boxplots_cached_resampled_data = None
    if "boxplots_date_filter_changed" not in st.session_state:
        st.session_state.boxplots_date_filter_changed = True
    if "boxplots_transformed_data_needs_update" not in st.session_state:
        st.session_state.boxplots_transformed_data_needs_update = True
    if "boxplots_cached_transformed_data" not in st.session_state:
        st.session_state.boxplots_cached_transformed_data = None

    if (
        st.session_state.boxplots_processed_data_needs_update
        or st.session_state.boxplots_cached_processed_data is None
    ):
        processed_data = load_processed_original_data(
            as_geopandas=False,
            date_as_index=True,
            parse_dates=True,
        )

        processed_data["DIA_SEMANA_OCURRENCIA"] = processed_data[
            "DIA_SEMANA_OCURRENCIA"
        ].map(DAY_OF_WEEK_MAP)

        processed_data["HORA"] = processed_data.index.hour

        st.session_state.boxplots_cached_processed_data = processed_data
        st.session_state.boxplots_processed_data_needs_update = False
    else:
        processed_data = st.session_state.boxplots_cached_processed_data

    selected_frequency = st.selectbox(
        label="Select Resampling Frequency:",
        options=list(FREQUENCY_OPTIONS.keys()),
        index=1,
        key="resample_frequency_selectbox",
        on_change=lambda: st.session_state.update(
            {"boxplots_resample_data_needs_update": True}
        ),
    )

    if (
        st.session_state.boxplots_resample_data_needs_update
        or st.session_state.boxplots_cached_resampled_data is None
    ):
        resampled_data = resample_data(
            freq=FREQUENCY_OPTIONS[selected_frequency],
            multi_index=True,
            day_of_week_map=DAY_OF_WEEK_MAP,
        )

        st.session_state.boxplots_cached_resampled_data = resampled_data
        st.session_state.boxplots_resample_data_needs_update = False
        st.session_state.boxplots_transformed_data_needs_update = True
        st.session_state.boxplots_cached_transformed_data = None
    else:
        resampled_data = st.session_state.boxplots_cached_resampled_data

    if resampled_data.empty:
        st.info("No data available for the selected date range and frequency.")
        return

    columns_options = list(
        set(map(lambda item: item[0], resampled_data.columns.tolist()))
    )

    show_distrubution_over_time(
        resampled_data,
        selected_frequency,
        columns_options,
    )

    st.markdown("---")

    compare_boxplots_between_hours(processed_data, columns_options)
