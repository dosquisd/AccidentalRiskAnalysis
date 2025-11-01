import streamlit as st

from dashboard.data import data_index
from dashboard.lineplots import lineplot_index


def introduction() -> None:
    st.markdown("# Introduction")

    st.markdown("""
        Welcome to the Accidental Risk Analysis Dashboard!
        This platform is designed to provide insights into accident data
        through interactive visualizations and analyses.
    """)

    st.warning("""
        :red[Maybe here write more about the project, data sources, about what
        users can find in the dashboard, etc.]
    """)


if __name__ == "__main__":
    index_pages = {
        "Introduction": introduction,
        "Data Overview": data_index,
        "Line Plots": lineplot_index,
    }

    page = st.sidebar.selectbox("Select a page:", list(index_pages.keys()))
    index_pages[page]()
