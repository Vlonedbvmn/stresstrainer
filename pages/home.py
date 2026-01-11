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
st.sidebar.markdown("Підготовка до НМТ")
st.sidebar.markdown("---")
st.sidebar.info("👈 Оберіть сторінку в меню вище")

st.title("Ласкаво просимо до НМТ Тренажера!")

st.markdown("""
Цей застосунок допоможе вам підготуватися до НМТ з української мови. 
Практикуйте визначення правильних наголосів у словах та покращуйте свої знання!
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📚 Слів у базі", "200+")
    
with col2:
    st.metric("🎯 Спроб", "∞")
    
with col3:
    st.metric("💰 Ціна", "Безкоштовно")

st.markdown("---")

st.subheader("✨ Можливості")

col1, col2 = st.columns(2)

with col1:
    st.info("📚 **Інтерактивний тренажер**\n\nОбирайте правильний наголос та отримуйте миттєвий зворотний зв'язок")
    st.info("🎯 **Актуальна база**\n\nСлова відповідають вимогам НМТ")

with col2:
    st.info("📊 **Відстеження прогресу**\n\nСлідкуйте за результатами")
    st.info("⚡ **Швидкий старт**\n\nПочніть без реєстрації")

st.markdown("---")

st.success("🚀 **Готові почати?** Перейдіть до **📚 Тренажер** у меню зліва!")
