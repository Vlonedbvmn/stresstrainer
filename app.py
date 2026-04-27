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
        padding: 15px;
        height: 70px;
        width: auto;
    }
    [data-testid="stSidebarHeader"] {
        margin-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.logo("ukrlogonew.png")

account_label = (
    f"{st.session_state['username']}"
    if st.session_state.get('username')
    else "Акаунт"
)

teacher_label = (
    "Панель вчителя"
    if st.session_state.get("teacher_auth")
    else "Панель вчителя"
)

pages = {
    "Головне меню": [
        st.Page("pages/Maintained.py", title="Головна", icon="🏠")
        #st.Page("pages/trainer.py", title="Тренажер наголосів", icon="📚"),
        #st.Page("pages/account.py", title=account_label, icon="👤"),
    ]
    #"Адміністрування": [
    #    st.Page("pages/teacher.py", title=teacher_label, icon="🎓"),
    #],
}

nav = st.navigation(pages)
nav.run()
