import streamlit as st


def index(title: str) -> None:
    st.title(title)

    st.markdown("Supuestamente aquí van las conclusiones generales del dashboard.")


if __name__ == "__main__":
    title = "Conclusiones"
    st.set_page_config(page_title=title, layout="wide")
    index(title)
