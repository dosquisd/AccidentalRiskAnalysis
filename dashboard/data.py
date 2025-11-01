import streamlit as st


def data_overview(title: str = "Data Overview") -> None:
    st.markdown(f"# {title}")
    st.warning("""
        TODO: :red[Write about the data that are being used in this project.]  
        This includes sources, a description of the variables, and, finally, show
        a preview of the data, allowing the user explore all the dataset (>300k rows)
        and download it if desired.
    """)
