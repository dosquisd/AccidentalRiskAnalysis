import streamlit as st

from dashboard.data import download_button_data, load_data_preview
from utils import configure_scienceplots

# This raise an exception if LaTeX is not installed
try:
    configure_scienceplots()
except Exception:
    pass


def index(title: str = "Context and Data") -> None:
    st.markdown(f"# {title}")

    st.markdown("""
        Welcome to the Accidental Risk Analysis Dashboard!
        This platform is designed to provide insights into accident data
        through interactive visualizations and analyses.
    """)

    st.warning("""
        :red[Maybe here write more about the project, data sources, about what
        users can find in the dashboard, etc.]
    """)

    col1, col2 = st.columns([2, 2])

    with col1:
        # Show raw data preview
        st.subheader("Raw Data Preview")
        raw_df = load_data_preview(raw=True)
        st.dataframe(raw_df)
        download_button_data(
            raw_df,
            label="Download Raw Data as CSV",
            filename="raw_accident_data.csv",
        )

    with col2:
        # Show processed data preview
        st.subheader("Processed Data Preview")
        processed_df = load_data_preview(raw=False)
        st.dataframe(processed_df)
        download_button_data(
            processed_df,
            label="Download Processed Data as CSV",
            filename="processed_accident_data.csv",
        )


if __name__ == "__main__":
    title = "Context and Data"
    st.set_page_config(page_title=title, layout="wide")
    index(title)
