import streamlit as st
import pathlib

st.set_page_config(
    page_title="НМТ Тренажер",
    page_icon="ukrlogonew.png",
    layout="wide",
    initial_sidebar_state="expanded"  
)

def load_css(file_path):
    """Load external CSS file"""
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



css_path = pathlib.Path("assets/styles.css")
load_css(css_path)

st.sidebar.title("НМТ Тренажер")
st.sidebar.markdown("Зараз працюемо над відновленням бази даних) \n Вибачте за незручності")

