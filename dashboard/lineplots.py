import warnings

import pandas as pd
import streamlit as st

from dashboard.custom_utils import filter_data_by_date_range
from utils.load_data import load_processed_original_data, resample_data

warnings.filterwarnings("ignore")


def show_all_historic_data(
    resampled_data: pd.DataFrame,
    accidents_col: str = "TOTAL_ACCIDENTES",
    *,
    ewm_alpha: float = 0.0,
    resample_freq_units: str = "weekly",
) -> None:
    resample_freq_units = resample_freq_units.capitalize()

    tmp_df = resampled_data.reset_index()
    y_axis = [accidents_col]
    color_axis = None

    if ewm_alpha > 0.0:
        if (
            st.session_state.last_ewm_alpha_slider != ewm_alpha
            or st.session_state.ewm_alpha_calcs is None
        ):
            tmp_df["ewm"] = tmp_df[y_axis].ewm(alpha=ewm_alpha).mean()
            st.session_state.last_ewm_alpha_slider = ewm_alpha
            st.session_state.ewm_alpha_calcs = tmp_df["ewm"].copy()
            print(f"Calculating EWM with alpha={ewm_alpha}")
        else:
            tmp_df["ewm"] = st.session_state.ewm_alpha_calcs
            print(f"Using cached EWM with alpha={ewm_alpha}")

        y_axis = [accidents_col, "ewm"]
        color_axis = ["#00b7ffff", "#ff000089"]

    st.subheader(f"All Historic Data {resample_freq_units}")
    st.line_chart(
        tmp_df,
        x=resampled_data.index.name,
        y=y_axis,
        x_label="Date",
        y_label="Total Accidents",
        color=color_axis,
    )


def show_locality_data(
    resampled_data: pd.DataFrame,
    localities: list[str],
    *,
    ewm_alpha: float = 0.0,
    resample_freq_units: str = "weekly",
    separate_charts: bool = False,
) -> None:
    """Shows data for selected localities."""
    resample_freq_units = resample_freq_units.capitalize()

    if separate_charts:
        # Show each locality in a separate chart
        for locality in localities:
            locality_col = f"LOCALIDAD-{locality.replace(' ', '_')}"
            if locality_col not in resampled_data.columns:
                st.warning(f"⚠️ No data found for locality: {locality}")
                continue

            tmp_df = resampled_data.reset_index()
            y_axis = [locality_col]
            color_axis = None

            if ewm_alpha > 0.0:
                ewm_key = f"ewm_{locality}"
                tmp_df[ewm_key] = (
                    tmp_df[locality_col].ewm(alpha=ewm_alpha).mean()
                )
                y_axis = [locality_col, ewm_key]
                color_axis = ["#00b7ffff", "#ff000089"]

            st.subheader(f"📍 {locality} - {resample_freq_units}")
            st.line_chart(
                tmp_df,
                x=resampled_data.index.name,
                y=y_axis,
                x_label="Date",
                y_label="Total Accidents",
                color=color_axis,
            )
    else:
        # Show all localities in a single chart
        tmp_df = resampled_data.reset_index()
        y_axis = []

        for locality in localities:
            locality_col = f"LOCALIDAD-{locality.replace(' ', '_')}"
            if locality_col in resampled_data.columns:
                y_axis.append(locality_col)
            else:
                st.warning(f"⚠️ No data found for locality: {locality}")

        if not y_axis:
            st.error("❌ No valid localities selected.")
            return

        st.subheader(
            f"📍 Selected Localities Comparison - {resample_freq_units}"
        )
        st.line_chart(
            tmp_df,
            x=resampled_data.index.name,
            y=y_axis,
            x_label="Date",
            y_label="Total Accidents",
        )


def lineplots(
    df: pd.DataFrame,
    resample_freq_units: str = "week",
) -> None:
    ewm_alpha = st.slider(
        label=r"EWM Alpha ($\alpha=0 \Rightarrow$ No EWM; $\alpha>0 \Rightarrow$ EWM Smoothing)",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.01,
        key="ewm_alpha_slider",
        on_change=lambda: st.session_state.update({"ewm_alpha_calcs": None}),
    )

    # Total accidents chart
    st.markdown("## 📊 Total Accidents Overview")
    total_accidents_col = "TOTAL_ACCIDENTES"
    total_accidents_df = df[[total_accidents_col]]
    show_all_historic_data(
        total_accidents_df,
        accidents_col=total_accidents_col,
        ewm_alpha=ewm_alpha,
        resample_freq_units=resample_freq_units,
    )

    # Localities section
    st.markdown("---")
    st.markdown("## 🏙️ Localities Analysis")

    # Get all available localities from column names
    locality_columns = [
        col for col in df.columns if col.startswith("LOCALIDAD-")
    ]
    available_localities = sorted(
        [
            col.replace("LOCALIDAD-", "").replace("_", " ")
            for col in locality_columns
        ]
    )

    if not available_localities:
        st.warning("⚠️ No locality data available in the resampled dataset.")
        return

    # Locality selection
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_localities = st.multiselect(
            label="Select Localities to Display:",
            options=available_localities,
            default=available_localities[:3]
            if len(available_localities) >= 3
            else available_localities,
            key="localities_multiselect",
        )

    with col2:
        separate_charts = st.checkbox(
            label="Separate Charts",
            value=False,
            key="separate_charts_checkbox",
            help="Show each locality in its own chart",
        )

    if not selected_localities:
        st.info("ℹ️ Please select at least one locality to display the chart.")
        return

    # Show selected localities
    show_locality_data(
        df,
        selected_localities,
        ewm_alpha=ewm_alpha,
        resample_freq_units=resample_freq_units,
        separate_charts=separate_charts,
    )


def lineplot_index(title: str = "LinePlots") -> None:
    st.markdown(f"# {title}")
    st.warning("""
        TODO: :red[Write an introduction text about what the users can find in this section.]
    """)

    # Initialize session state
    if "processed_data_needs_update" not in st.session_state:
        st.session_state.processed_data_needs_update = True
    if "cached_processed_data" not in st.session_state:
        st.session_state.cached_processed_data = None
    if "resampled_data_needs_update" not in st.session_state:
        st.session_state.resampled_data_needs_update = True
    if "cached_resampled_data" not in st.session_state:
        st.session_state.cached_resampled_data = None
    if "date_filter_changed" not in st.session_state:
        st.session_state.date_filter_changed = True
    if "last_ewm_alpha_slider" not in st.session_state:
        st.session_state.last_ewm_alpha_slider = 0.0
    if "ewm_alpha_calcs" not in st.session_state:
        st.session_state.ewm_alpha_calcs = None

    if (
        st.session_state.processed_data_needs_update
        or st.session_state.cached_processed_data is None
    ):
        processed_data = load_processed_original_data(
            as_geopandas=False,
            date_as_index=True,
            parse_dates=True,
        )
        st.session_state.cached_processed_data = processed_data
        st.session_state.processed_data_needs_update = False

        # Force EWM recalculation
        st.session_state.last_ewm_alpha_slider = 0.0
        st.session_state.ewm_alpha_calcs = None
        print("Recalculating processed data")
    else:
        processed_data = st.session_state.cached_processed_data
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
                {"date_filter_changed": True}
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
                {"date_filter_changed": True}
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
            {"resampled_data_needs_update": True}
        ),
    )

    # Use cached data to avoid unnecessary recomputation
    if (
        st.session_state.resampled_data_needs_update
        or st.session_state.date_filter_changed
        or st.session_state.cached_resampled_data is None
    ):
        # First filter by dates
        filtered_data = filter_data_by_date_range(
            processed_data, start_date, end_date
        )

        # Then resample the filtered data
        resampled_data = resample_data(
            df=filtered_data,
            freq=frequency_options[selected_frequency],
            multi_index=False,
        )

        st.session_state.cached_resampled_data = resampled_data
        st.session_state.resampled_data_needs_update = False
        st.session_state.date_filter_changed = False

        print(
            f"Recalculating data: {selected_frequency}, {start_date} to {end_date}"
        )
    else:
        resampled_data = st.session_state.cached_resampled_data
        print(f"Using cached data: {selected_frequency}")

    # Check if there is data in the selected range
    if resampled_data.empty:
        st.warning(
            f"⚠️ No data available in the selected date range ({start_date} to {end_date})."
        )
        return

    lineplots(
        df=resampled_data,
        resample_freq_units=selected_frequency,
    )
