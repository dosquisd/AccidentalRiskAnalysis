from datetime import date
from typing import TypeVar

import geopandas as gpd
import pandas as pd
import streamlit as st

T = TypeVar("T", pd.DataFrame, gpd.GeoDataFrame)

FREQUENCY_OPTIONS = {
    "Daily": "1D",
    "Weekly": "1W",
    "Biweekly": "2W",
    "Monthly": "1ME",
    "Quarterly": "3ME",
    "Yearly": "1Y",
    "Biennial": "2Y",
}

DAY_OF_WEEK_MAP = {
    1: "MONDAY",
    2: "TUESDAY",
    3: "WEDNESDAY",
    4: "THURSDAY",
    5: "FRIDAY",
    6: "SATURDAY",
    7: "SUNDAY",
}


def transform_resample_data_for_boxplot(
    df: pd.DataFrame,
    col: str,
    multi_index: bool = False,
) -> pd.DataFrame:
    filtered_df: pd.DataFrame

    if multi_index:
        filtered_df = df[col]
        if isinstance(filtered_df, pd.Series):
            filtered_df = filtered_df.to_frame()
    else:
        interest_columns = list(
            filter(lambda df_col: df_col.startswith(col), df.columns)
        )
        columns = list(
            map(
                lambda df_col: df_col.split("-")[1].replace("_", " ").strip(),
                interest_columns,
            )
        )
        filtered_df = pd.DataFrame()
        for i in range(len(interest_columns)):
            filtered_df[columns[i]] = df[interest_columns[i]]

    col_type = []
    values = []
    indexes = []
    for index, row in filtered_df.iterrows():
        for c in filtered_df.columns:
            col_type.append(c)
            values.append(row[c])
            indexes.append(index)

    new_df = pd.DataFrame(
        {
            col: col_type,
            "value": values,
        },
        index=indexes,
    )

    return new_df


def filter_data_by_date_range(df: T, start_date: date, end_date: date) -> T:
    """Filters the DataFrame by the selected date range."""
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)

    # Filter the DataFrame
    if (
        df.index.name == "FECHA_OCURRENCIA"
        or "FECHA_OCURRENCIA" in df.index.names
    ):
        # If the date is in the index
        mask = (df.index >= start_datetime) & (df.index <= end_datetime)
        return df.loc[mask]
    else:
        # If the date is in a column
        if "FECHA_OCURRENCIA" in df.columns:
            mask = (df["FECHA_OCURRENCIA"] >= start_datetime) & (
                df["FECHA_OCURRENCIA"] <= end_datetime
            )
            return df.loc[mask]

    return df


def select_dates(
    df: T,
    key_prefix: str,
    show_total_days: bool = True,
    min_date: date = None,
    max_date: date = None,
) -> tuple[date, date] | None:
    """Creates date input widgets to select start and end dates.

    Args:
        df (T): The DataFrame containing the date information.
        key_prefix (str): The prefix for the Streamlit widget keys.
        show_total_days (bool, optional): Whether to show the total number of days selected. Defaults to True.
        min_date (date, optional): Minimum selectable date. If None, uses the minimum date in df. Defaults to None.
        max_date (date, optional): Maximum selectable date. If None, uses the maximum date

    Returns:
        tuple[date, date] | None: The selected start and end dates.
    """
    if min_date is None:
        min_date = df.index.min().date()

    if max_date is None:
        max_date = df.index.max().date()

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            label="Start Date:",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_start_date_input",
            on_change=lambda: st.session_state.update(
                {f"{key_prefix}_date_filter_changed": True}
            ),
        )

    with col2:
        end_date = st.date_input(
            label="End Date:",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_end_date_input",
            on_change=lambda: st.session_state.update(
                {f"{key_prefix}_date_filter_changed": True}
            ),
        )

    if start_date > end_date:
        st.error("⚠️ The start date must be earlier than the end date.")
        return None

    if show_total_days:
        total_days = (end_date - start_date).days + 1
        st.info(
            f"📅 Selected range: **{total_days} days** ({start_date} to {end_date})"
        )

    return start_date, end_date
