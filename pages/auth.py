import streamlit as st
import hashlib

# Стили
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    .auth-header {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .auth-icon {
        font-size: 4rem;
        margin-bottom: 20px;
    }
    
    .auth-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 10px;
    }
    
    .auth-subtitle {
        color: #94A3B8;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input {
        background: #0F172A;
        border: 2px solid #475569;
        border-radius: 12px;
        color: #F8FAFC;
        padding: 15px;
        font-size: 1rem;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 15px 30px;
        font-weight: 600;
        font-size: 1.1rem;
        margin-top: 20px;
    }
    
    .user-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        margin: 30px auto;
        max-width: 400px;
        border: 1px solid #475569;
    }
    
    .user-avatar {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #3B82F6 0%, #A78BFA 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        margin: 0 auto 20px auto;
        line-height: 80px;
    }
    
    .user-name {
        font-size: 1.5rem;
        font-weight: 600;
        color: #F8FAFC;
        margin-bottom: 5px;
    }
    
    .user-email {
        color: #94A3B8;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# База пользователей
if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        'demo@example.com': {
            'password': hashlib.sha256('demo123'.encode()).hexdigest(),
            'name': 'Демо Користувач'
        }
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    
if 'current_user' not in st.session_state:
    st.session_state.current_user = None


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login(email, password):
    if email in st.session_state.users_db:
        if st.session_state.users_db[email]['password'] == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.current_user = {
                'email': email,
                'name': st.session_state.users_db[email]['name']
            }
            return True, "Успішний вхід!"
        return False, "Неправильний пароль"
    return False, "Користувача не знайдено"


def register(name, email, password):
    if email in st.session_state.users_db:
        return False, "Користувач з такою поштою вже існує"
    
    st.session_state.users_db[email] = {
        'password': hash_password(password),
        'name': name
    }
    return True, "Реєстрація успішна!"


def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = None


# Контент
if st.session_state.logged_in:
    st.markdown(f"""
    <div class="user-card">
        <div class="user-avatar">👤</div>
        <div class="user-name">{st.session_state.current_user['name']}</div>
        <div class="user-email">{st.session_state.current_user['email']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.success("✅ Ви успішно авторизовані!")
        st.markdown("Перейдіть до **📚 Тренажер наголосів** для практики!")
        
        if st.button("🚪 Вийти з акаунту", use_container_width=True):
            logout()
            st.rerun()

else:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="auth-header">
            <div class="auth-icon">🔐</div>
            <h1 class="auth-title">Авторизація</h1>
            <p class="auth-subtitle">Увійдіть або створіть новий акаунт</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Вхід", "📝 Реєстрація"])
        
        with tab1:
            login_email = st.text_input("📧 Email", key="login_email")
            login_password = st.text_input("🔒 Пароль", type="password", key="login_password")
            
            if st.button("Увійти", key="login_btn", use_container_width=True):
                if login_email and login_password:
                    success, message = login(login_email, login_password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Заповніть всі поля")
            
            st.info("**Демо:** demo@example.com / demo123")
        
        with tab2:
            reg_name = st.text_input("👤 Ім'я", key="reg_name")
            reg_email = st.text_input("📧 Email", key="reg_email")
            reg_password = st.text_input("🔒 Пароль", type="password", key="reg_password")
            reg_password2 = st.text_input("🔒 Підтвердження", type="password", key="reg_password2")
            
            if st.button("Зареєструватися", key="reg_btn", use_container_width=True):
                if reg_name and reg_email and reg_password and reg_password2:
                    if reg_password != reg_password2:
                        st.error("Паролі не співпадають")
                    elif len(reg_password) < 6:
                        st.error("Пароль має бути не менше 6 символів")
                    else:
                        success, message = register(reg_name, reg_email, reg_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.warning("Заповніть всі поля")
