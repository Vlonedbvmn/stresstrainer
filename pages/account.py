import streamlit as st
import pathlib
import mysql.connector
import sys
import os

# Ensure root is on path so we can import db helpers
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ── CSS ────────────────────────────────────────────────────────────────────────
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_path = pathlib.Path("assets/styles.css")
if css_path.exists():
    load_css(css_path)

# ── DB connection ──────────────────────────────────────────────────────────────
def get_connection():
    try:
        conn = mysql.connector.connect(
            host=st.secrets["base_host"],
            port=3306,
            database=st.secrets["base_name"],
            user=st.secrets["base_user"],
            password=st.secrets["base_pass"],
            charset='utf8mb4'
        )
        if conn.is_connected():
            return conn
    except Exception as e:
        st.error(f"❌ Помилка підключення до БД: {e}")
        return None

def login_user(connection, username_or_email: str, password: str):
    """
    Перевіряє логін.
    Повертає (True, user_dict) або (False, повідомлення_помилки).
    """
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (username_or_email, username_or_email)
        )
        user = cursor.fetchone()
        if not user:
            cursor.close()
            return False, "Користувача не знайдено."

        pw_hash, _ = hash_password(password, user['salt'])
        if pw_hash != user['password_hash']:
            cursor.close()
            return False, "Невірний пароль."

        # Оновлюємо час останнього входу
        cursor.execute(
            "UPDATE users SET last_login = NOW() WHERE id = %s",
            (user['id'],)
        )
        connection.commit()
        cursor.close()
        return True, user

    except Error as e:
        cursor.close()
        return False, str(e)


# ============================================
# СЕСІЇ ТРЕНУВАНЬ
# ============================================

def start_training_session(connection, user_id: int):
    """Починає нову сесію тренування. Повертає session_id."""
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO training_sessions (user_id) VALUES (%s)",
            (user_id,)
        )
        connection.commit()
        session_id = cursor.lastrowid
        cursor.close()
        return session_id
    except Error as e:
        print(f"❌ Помилка старту сесії: {e}")
        cursor.close()
        return None


def save_answer(connection, session_id: int, word: str, is_correct: bool):
    """Зберігає одну відповідь у сесії."""
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO session_answers (session_id, word, is_correct) VALUES (%s, %s, %s)",
            (session_id, word, is_correct)
        )
        connection.commit()
        cursor.close()
    except Error as e:
        print(f"❌ Помилка збереження відповіді: {e}")
        cursor.close()


def finish_training_session(connection, session_id: int,
                             total: int, correct: int, wrong: int,
                             accuracy: float, grade: int):
    """Завершує сесію та зберігає підсумкову статистику."""
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE training_sessions
            SET ended_at = NOW(),
                total_count = %s,
                correct_count = %s,
                wrong_count = %s,
                accuracy = %s,
                grade = %s
            WHERE id = %s
        """, (total, correct, wrong, accuracy, grade, session_id))
        connection.commit()
        cursor.close()
    except Error as e:
        print(f"❌ Помилка завершення сесії: {e}")
        cursor.close()


# ============================================
# СТАТИСТИКА ДАШБОРДУ
# ============================================

def get_last_sessions(connection, user_id: int, limit: int = 5):
    """Повертає останні N сесій користувача."""
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, started_at, ended_at, total_count, correct_count,
                   wrong_count, accuracy, grade
            FROM training_sessions
            WHERE user_id = %s AND ended_at IS NOT NULL
            ORDER BY started_at DESC
            LIMIT %s
        """, (user_id, limit))
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Error as e:
        print(f"❌ Помилка отримання сесій: {e}")
        cursor.close()
        return []


def get_overall_stats(connection, user_id: int):
    """Повертає загальну статистику користувача."""
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                COUNT(*) AS total_sessions,
                COALESCE(SUM(total_count), 0) AS total_answers,
                COALESCE(SUM(correct_count), 0) AS total_correct,
                COALESCE(SUM(wrong_count), 0) AS total_wrong,
                COALESCE(ROUND(AVG(accuracy), 1), 0) AS avg_accuracy,
                COALESCE(ROUND(AVG(grade), 1), 0) AS avg_grade,
                COALESCE(MAX(accuracy), 0) AS best_accuracy,
                COALESCE(MAX(grade), 0) AS best_grade
            FROM training_sessions
            WHERE user_id = %s AND ended_at IS NOT NULL
        """, (user_id,))
        stats = cursor.fetchone()
        cursor.close()
        return stats
    except Error as e:
        print(f"❌ Помилка статистики: {e}")
        cursor.close()
        return None

# ── Helpers ────────────────────────────────────────────────────────────────────
def grade_color(grade):
    if grade >= 10:
        return "#4ade80"
    elif grade >= 7:
        return "#fbbf24"
    else:
        return "#f87171"


def accuracy_bar(accuracy):
    color = "#4ade80" if accuracy >= 70 else ("#fbbf24" if accuracy >= 40 else "#f87171")
    return f"""
    <div style="background:#1e293b;border-radius:6px;height:8px;width:100%;margin-top:4px;">
      <div style="background:{color};border-radius:6px;height:8px;width:{min(accuracy,100):.0f}%;"></div>
    </div>"""


def logout():
    for key in ['user_id', 'username', 'user_email',
                'user_first_name', 'user_last_name', 'user_school', 'user_grade_class']:
        st.session_state.pop(key, None)
    for key in ['session_id', 'correct_count', 'wrong_count', 'total_count',
                'correct_answers', 'wrong_answers']:
        st.session_state.pop(key, None)
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# NOT LOGGED IN  →  Login / Register tabs
# ══════════════════════════════════════════════════════════════════════════════
def show_auth():
    st.markdown("""
    <div style="max-width:460px;margin:0 auto;padding-top:20px;">
      <h2 style="text-align:center;color:#f1f5f9;margin-bottom:4px;">👤 Акаунт</h2>
      <p style="text-align:center;color:#64748b;margin-bottom:24px;">
        Увійдіть, щоб зберігати прогрес та бачити статистику
      </p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_reg = st.tabs(["🔑 Увійти", "✏️ Реєстрація"])

    # ── LOGIN ──────────────────────────────────────────────────────────────────
    with tab_login:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            identifier = st.text_input("Ім'я користувача або Email",
                                       placeholder="example або example@email.com")
            password = st.text_input("Пароль", type="password",
                                     placeholder="Введіть пароль")
            submitted = st.form_submit_button("Увійти", use_container_width=True)

        if submitted:
            if not identifier or not password:
                st.warning("⚠️ Заповніть усі поля.")
            else:
                conn = get_connection()
                if conn:
                    ok, result = login_user(conn, identifier, password)
                    conn.close()
                    if ok:
                        st.session_state['user_id'] = result['id']
                        st.session_state['username'] = result['username']
                        st.session_state['user_email'] = result['email']
                        st.session_state['user_first_name'] = result.get('first_name') or ''
                        st.session_state['user_last_name'] = result.get('last_name') or ''
                        st.session_state['user_school'] = result.get('school') or ''
                        st.session_state['user_grade_class'] = result.get('grade_class') or ''
                        st.success(f"✅ Ласкаво просимо, **{result['username']}**!")
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")

    # ── REGISTER ───────────────────────────────────────────────────────────────
    with tab_reg:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("register_form", clear_on_submit=True):

            st.markdown("**👤 Особисті дані**")
            col_fn, col_ln = st.columns(2)
            with col_fn:
                new_first_name = st.text_input("Ім'я", placeholder="Іван")
            with col_ln:
                new_last_name = st.text_input("Прізвище", placeholder="Петренко")

            st.markdown("**🏫 Навчання**")
            col_school, col_class = st.columns([3, 1])
            with col_school:
                new_school = st.text_input("Школа", placeholder="ЗОШ №1, м. Київ")
            with col_class:
                new_grade_class = st.text_input("Клас", placeholder="11-А")

            st.markdown("**🔐 Акаунт**")
            new_username = st.text_input("Ім'я користувача (логін)",
                                         placeholder="мінімум 3 символи")
            new_email = st.text_input("Email", placeholder="your@email.com")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                new_pass = st.text_input("Пароль", type="password",
                                         placeholder="мінімум 6 символів")
            with col_p2:
                new_pass2 = st.text_input("Повторіть пароль", type="password",
                                          placeholder="повторіть пароль")

            reg_submitted = st.form_submit_button("Зареєструватись",
                                                  use_container_width=True)

        if reg_submitted:
            errors = []
            if not new_first_name:
                errors.append("Введіть ім'я.")
            if not new_last_name:
                errors.append("Введіть прізвище.")
            if not new_username or len(new_username) < 3:
                errors.append("Логін — мінімум 3 символи.")
            if not new_email or "@" not in new_email:
                errors.append("Введіть коректний email.")
            if not new_pass or len(new_pass) < 6:
                errors.append("Пароль — мінімум 6 символів.")
            if new_pass != new_pass2:
                errors.append("Паролі не збігаються.")

            if errors:
                for err in errors:
                    st.warning(f"⚠️ {err}")
            else:
                conn = get_connection()
                if conn:
                    ok, result = register_user(
                        conn, new_username, new_email, new_pass,
                        first_name=new_first_name,
                        last_name=new_last_name,
                        school=new_school or None,
                        grade_class=new_grade_class or None
                    )
                    conn.close()
                    if ok:
                        st.success("✅ Акаунт створено! Тепер увійдіть у вкладці **Увійти**.")
                    else:
                        st.error(f"❌ {result}")


# ══════════════════════════════════════════════════════════════════════════════
# LOGGED IN  →  Dashboard
# ══════════════════════════════════════════════════════════════════════════════
def show_dashboard():
    user_id = st.session_state['user_id']
    username = st.session_state['username']
    first_name = st.session_state.get('user_first_name', '')
    last_name = st.session_state.get('user_last_name', '')
    school = st.session_state.get('user_school', '')
    grade_class = st.session_state.get('user_grade_class', '')

    full_name = f"{first_name} {last_name}".strip() or username

    # Meta info pills
    meta_parts = []
    if school:
        meta_parts.append(f"🏫 {school}")
    if grade_class:
        meta_parts.append(f"📋 {grade_class} клас")
    meta_html = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(
        f'<span style="background:#1e3a5f;color:#93c5fd;padding:3px 10px;'
        f'border-radius:20px;font-size:0.8rem;">{p}</span>'
        for p in meta_parts
    ) if meta_parts else ""

    # ── Header ────────────────────────────────────────────────────────────────
    col_title, col_logout = st.columns([5, 1])
    with col_title:
        st.markdown(f"""
        <h2 style="color:#f1f5f9;margin-bottom:2px;">
            👤 {full_name}
        </h2>
        <p style="color:#64748b;margin-top:0;margin-bottom:{'8px' if meta_html else '0'};">
            @{username}
        </p>
        {f'<div style="margin-bottom:4px;">{meta_html}</div>' if meta_html else ''}
        """, unsafe_allow_html=True)
    with col_logout:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Вийти 🚪", use_container_width=True):
            logout()

    st.markdown("---")

    conn = get_connection()
    if not conn:
        return

    overall = get_overall_stats(conn, user_id)
    sessions = get_last_sessions(conn, user_id, limit=5)
    conn.close()

    # ── Overall stats cards ───────────────────────────────────────────────────
    st.markdown("### 📊 Загальна статистика")

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "🎯 Сесій", overall['total_sessions'], "#60a5fa"),
        (c2, "📝 Відповідей", overall['total_answers'], "#a78bfa"),
        (c3, "✅ Правильних", overall['total_correct'], "#4ade80"),
        (c4, "❌ Помилок", overall['total_wrong'], "#f87171"),
    ]
    for col, label, value, color in cards:
        with col:
            st.markdown(f"""
            <div style="background:#1e293b;border-radius:12px;padding:20px;text-align:center;">
              <div style="font-size:1.9rem;font-weight:800;color:{color};">{value}</div>
              <div style="color:#94a3b8;font-size:0.82rem;margin-top:4px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c5, c6, c7 = st.columns(3)
    with c5:
        acc = float(overall['avg_accuracy'] or 0)
        bar = accuracy_bar(acc)
        st.markdown(f"""
        <div style="background:#1e293b;border-radius:12px;padding:20px;">
          <div style="color:#94a3b8;font-size:0.82rem;">📈 Середня точність</div>
          <div style="font-size:1.6rem;font-weight:800;color:#fbbf24;">{acc:.1f}%</div>
          {bar}
        </div>
        """, unsafe_allow_html=True)
    with c6:
        avg_g = float(overall['avg_grade'] or 0)
        st.markdown(f"""
        <div style="background:#1e293b;border-radius:12px;padding:20px;">
          <div style="color:#94a3b8;font-size:0.82rem;">🏅 Середня оцінка</div>
          <div style="font-size:1.6rem;font-weight:800;color:{grade_color(avg_g)};">
            {avg_g:.1f} / 12
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c7:
        best_g = int(overall['best_grade'] or 0)
        best_acc = float(overall['best_accuracy'] or 0)
        st.markdown(f"""
        <div style="background:#1e293b;border-radius:12px;padding:20px;">
          <div style="color:#94a3b8;font-size:0.82rem;">🌟 Найкращий результат</div>
          <div style="font-size:1.6rem;font-weight:800;color:{grade_color(best_g)};">
            {best_g} / 12
          </div>
          <div style="color:#64748b;font-size:0.8rem;">точність {best_acc:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Last 5 sessions table ─────────────────────────────────────────────────
    st.markdown("### 🕐 Останні 5 сесій")

    if not sessions:
        st.info("📭 Ви ще не завершили жодної сесії. Перейдіть до **Тренажера** та почніть!")
    else:
        # Table header
        st.markdown("""
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr;
                    gap:8px;padding:10px 16px;background:#0f172a;border-radius:8px 8px 0 0;
                    color:#64748b;font-size:0.8rem;font-weight:600;text-transform:uppercase;">
          <div>Дата</div>
          <div style="text-align:center;">Відповідей</div>
          <div style="text-align:center;">✅</div>
          <div style="text-align:center;">❌</div>
          <div style="text-align:center;">Точність</div>
          <div style="text-align:center;">Оцінка</div>
        </div>
        """, unsafe_allow_html=True)

        for i, s in enumerate(sessions):
            bg = "#1e293b" if i % 2 == 0 else "#172032"
            date_str = s['started_at'].strftime('%d.%m.%Y %H:%M') if s['started_at'] else "—"
            acc_val = float(s['accuracy'] or 0)
            g_val = int(s['grade'] or 0)
            bar = accuracy_bar(acc_val)
            acc_color = "#4ade80" if acc_val >= 70 else ("#fbbf24" if acc_val >= 40 else "#f87171")

            st.markdown(f"""
            <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr;
                        gap:8px;padding:12px 16px;background:{bg};align-items:center;
                        {'border-radius:0 0 8px 8px;' if i == len(sessions)-1 else ''}">
              <div style="color:#cbd5e1;font-size:0.9rem;">{date_str}</div>
              <div style="text-align:center;color:#60a5fa;font-weight:700;">{s['total_count']}</div>
              <div style="text-align:center;color:#4ade80;font-weight:700;">{s['correct_count']}</div>
              <div style="text-align:center;color:#f87171;font-weight:700;">{s['wrong_count']}</div>
              <div style="text-align:center;">
                <span style="color:{acc_color};font-weight:700;">{acc_val:.1f}%</span>
                {bar}
              </div>
              <div style="text-align:center;font-size:1.1rem;font-weight:800;
                          color:{grade_color(g_val)};">{g_val}/12</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <p style="text-align:center;color:#475569;font-size:0.85rem;">
        💡 Щоб накопичувати статистику, тренуйтесь та завершуйте сесії кнопкою
        <strong style="color:#60a5fa;">Завершити сесію</strong> у тренажері.
    </p>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if 'user_id' in st.session_state and st.session_state['user_id']:
    show_dashboard()
else:
    show_auth()
