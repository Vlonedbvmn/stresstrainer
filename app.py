import streamlit as st

st.set_page_config(
    page_title="НМТ Тренажер - Українська мова",
    page_icon="ukrlogonew.png",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown(
    """
    <style>
    [alt=Logo] {
        padding: 15 px;
        height: 70px; /* Adjust this value for your desired size */
        width: auto; /* Maintains aspect ratio */
    }

     [data-testid="stSidebarHeader"] {
            margin-top: 1rem; /* Adjust the top margin as needed (e.g., 20px) */
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.logo("ukrlogonew.png")

pages = {
    "Головне меню": [  
        st.Page("pages/home.py", title="Головна", icon="🏠"),
        st.Page("pages/trainer.py", title="Тренажер наголосів", icon="📚"),
    ],
    # "Додатково": 
    #     st.Page("pages/about.py", title="Про застосунок", icon="ℹ️"),
    # ]
}

nav = st.navigation(pages)
nav.run()
