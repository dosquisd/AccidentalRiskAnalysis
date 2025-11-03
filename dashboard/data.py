import pandas as pd
import streamlit as st

from utils.constants import DAY_OF_WEEK_MAP
from utils.load_data import load_processed_original_data, load_raw_data


@st.cache_data
def load_data_preview(raw: bool) -> pd.DataFrame:
    if raw:
        return load_raw_data(as_geopandas=False).drop(
            columns=["latitude", "longitude"]
        )

    df = load_processed_original_data(
        as_geopandas=False,
        date_as_index=False,
        parse_dates=True,
    )
    df["DIA_SEMANA_OCURRENCIA"] = df["DIA_SEMANA_OCURRENCIA"].map(
        DAY_OF_WEEK_MAP
    )
    return df


def download_button_data(df: pd.DataFrame, label: str, filename: str) -> None:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv",
    )
