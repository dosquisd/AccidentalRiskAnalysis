from datetime import date
from typing import TypeVar

import geopandas as gpd
import pandas as pd

T = TypeVar("T", pd.DataFrame, gpd.GeoDataFrame)


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
