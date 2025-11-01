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


def data_index(title: str = "Data Overview") -> None:
    st.markdown(f"# {title}")
    st.warning("""
        TODO: :red[Write about the data that are being used in this project.]  
        This includes sources, a description of the variables, and, finally, show
        a preview of the data, allowing the user explore all the dataset (>300k rows)
        and download it if desired.
    """)

    # Show raw data preview
    st.subheader("Raw Data Preview")
    raw_df = load_data_preview(raw=True)
    st.dataframe(raw_df)
    download_button_data(
        raw_df,
        label="Download Raw Data as CSV",
        filename="raw_accident_data.csv",
    )

    # Show processed data preview
    st.subheader("Processed Data Preview")
    processed_df = load_data_preview(raw=False)
    st.dataframe(processed_df)
    download_button_data(
        processed_df,
        label="Download Processed Data as CSV",
        filename="processed_accident_data.csv",
    )
