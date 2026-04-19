import streamlit as st
import pathlib
import mysql.connector
from mysql.connector import Error
import re

# ── CSS ────────────────────────────────────────────────────────────────────────
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_path = pathlib.Path("assets/styles.css")
if css_path.exists():
    load_css(css_path)

# ── Credentials ────────────────────────────────────────────────────────────────
TEACHER_LOGIN    = "teacher"
TEACHER_PASSWORD = "dtllicej"

# ── DB connection ──────────────────────────────────────────────────────────────
def get_conn():
    try:
        conn = mysql.connector.connect(
            host=st.secrets["base_host"],
            port=3306,
            database=st.secrets["base_name"],
            user=st.secrets["base_user"],
            password=st.secrets["base_pass"],
            charset="utf8mb4"
        )
        if conn.is_connected():
            return conn
    except Exception as e:
        st.error(f"❌ Помилка підключення до БД: {e}")
    return None


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def grade_color(g):
    g = float(g or 0)
    if g >= 10: return "#4ade80"
    if g >= 7:  return "#fbbf24"
    return "#f87171"

def accuracy_bar(acc, width="100%"):
    acc = float(acc or 0)
    color = "#4ade80" if acc >= 70 else ("#fbbf24" if acc >= 40 else "#f87171")
    return f"""<div style="background:#0f172a;border-radius:6px;height:7px;width:{width};margin-top:5px;">
      <div style="background:{color};border-radius:6px;height:7px;width:{min(acc,100):.0f}%;"></div></div>"""

def pill(text, color="#1e3a5f", text_color="#93c5fd"):
    return (f'<span style="background:{color};color:{text_color};padding:2px 10px;'
            f'border-radius:20px;font-size:0.78rem;white-space:nowrap;">{text}</span>')

def validate_stressed_word(word: str) -> tuple[bool, str]:
    """
    Перевіряє, що слово написане у форматі НМТ-тренажера:
    - лише українські літери (+ апостроф, дефіс)
    - рівно одна велика (наголошена) голосна
    """
    if not word:
        return False, "Слово не може бути порожнім."
    if not re.match(r"^[а-яіїєґА-ЯІЇЄҐ'\-]+$", word):
        return False, "Слово може містити лише українські літери, апостроф або дефіс."
    vowels_ua  = "аеєиіїоуюя"
    upper_vowels = [c for c in word if c.lower() in vowels_ua and c.isupper()]
    if len(upper_vowels) == 0:
        return False, "Позначте наголос — одна голосна має бути ВЕЛИКОЮ літерою (напр. прИклад)."
    if len(upper_vowels) > 1:
        return False, "Тільки одна голосна може бути великою (наголошеною)."
    return True, ""


# ══════════════════════════════════════════════════════════════════════════════
# DB QUERIES
# ══════════════════════════════════════════════════════════════════════════════

# ── Students ──────────────────────────────────────────────────────────────────
def get_all_students(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.id, u.username, u.first_name, u.last_name,
               u.school, u.grade_class, u.created_at, u.last_login,
               COUNT(ts.id)                          AS total_sessions,
               COALESCE(SUM(ts.total_count),  0)     AS total_answers,
               COALESCE(SUM(ts.correct_count),0)     AS total_correct,
               COALESCE(ROUND(AVG(ts.accuracy),1),0) AS avg_accuracy,
               COALESCE(ROUND(AVG(ts.grade),1),0)    AS avg_grade,
               COALESCE(MAX(ts.grade),0)              AS best_grade
        FROM users u
        LEFT JOIN training_sessions ts
               ON ts.user_id = u.id AND ts.ended_at IS NOT NULL
        GROUP BY u.id
        ORDER BY u.last_name, u.first_name
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

def get_student_sessions(conn, user_id: int):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT started_at, ended_at, total_count, correct_count,
               wrong_count, accuracy, grade
        FROM training_sessions
        WHERE user_id = %s AND ended_at IS NOT NULL
        ORDER BY started_at DESC
        LIMIT 20
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    return rows

def delete_student(conn, user_id: int):
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()

# ── Words ─────────────────────────────────────────────────────────────────────
def get_all_words(conn, search: str = ""):
    cur = conn.cursor(dictionary=True)
    if search:
        cur.execute("""
            SELECT id, word, poem,
                   CASE WHEN poem IS NOT NULL THEN 1 ELSE 0 END AS has_poem
            FROM words_poems
            WHERE LOWER(word) LIKE %s
            ORDER BY word
        """, (f"%{search.lower()}%",))
    else:
        cur.execute("""
            SELECT id, word, poem,
                   CASE WHEN poem IS NOT NULL THEN 1 ELSE 0 END AS has_poem
            FROM words_poems
            ORDER BY word
        """)
    rows = cur.fetchall()
    cur.close()
    return rows

def add_word(conn, word: str, poem: str = None):
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO words_poems (word, poem) VALUES (%s, %s)",
            (word, poem or None)
        )
        conn.commit()
        cur.close()
        return True, None
    except Error as e:
        cur.close()
        return False, str(e)

def update_word(conn, word_id: int, word: str, poem: str):
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE words_poems SET word = %s, poem = %s WHERE id = %s",
            (word, poem or None, word_id)
        )
        conn.commit()
        cur.close()
        return True, None
    except Error as e:
        cur.close()
        return False, str(e)

def delete_word(conn, word_id: int):
    cur = conn.cursor()
    cur.execute("DELETE FROM words_poems WHERE id = %s", (word_id,))
    conn.commit()
    cur.close()

def get_words_stats(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COUNT(*) AS total,
               SUM(poem IS NOT NULL) AS with_poem,
               SUM(poem IS NULL)     AS without_poem
        FROM words_poems
    """)
    row = cur.fetchone()
    cur.close()
    return row


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN GATE
# ══════════════════════════════════════════════════════════════════════════════
def show_teacher_login():
    st.markdown("""
    <div style="max-width:400px;margin:60px auto 0;">
      <div style="text-align:center;margin-bottom:28px;">
        <div style="font-size:3rem;">🎓</div>
        <h2 style="color:#f1f5f9;margin:8px 0 4px;">Панель вчителя</h2>
        <p style="color:#64748b;font-size:0.9rem;">Введіть облікові дані для доступу</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        with st.form("teacher_login_form"):
            login_in = st.text_input("Логін", placeholder="teacher")
            pass_in  = st.text_input("Пароль", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Увійти як вчитель", use_container_width=True)

        if submitted:
            if login_in == TEACHER_LOGIN and pass_in == TEACHER_PASSWORD:
                st.session_state["teacher_auth"] = True
                st.rerun()
            else:
                st.error("❌ Невірний логін або пароль.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TEACHER PANEL
# ══════════════════════════════════════════════════════════════════════════════
def show_teacher_panel():

    # ── Top bar ────────────────────────────────────────────────────────────────
    col_h, col_out = st.columns([6, 1])
    with col_h:
        st.markdown("""
        <h2 style="color:#f1f5f9;margin-bottom:2px;">🎓 Панель вчителя</h2>
        <p style="color:#64748b;margin-top:0;">Управління учнями та базою слів</p>
        """, unsafe_allow_html=True)
    with col_out:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Вийти 🚪", use_container_width=True):
            st.session_state["teacher_auth"] = False
            st.rerun()

    st.markdown("---")

    tab_students, tab_words = st.tabs(["👨‍🎓 Учні", "📖 Слова та підказки"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — STUDENTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_students:
        conn = get_conn()
        if not conn:
            return

        students = get_all_students(conn)
        conn.close()

        if not students:
            st.info("📭 Ще жодного учня не зареєстровано.")
            return

        # ── Summary row ──────────────────────────────────────────────────────
        total_s  = len(students)
        active_s = sum(1 for s in students if (s["total_sessions"] or 0) > 0)
        avg_all  = (sum(float(s["avg_accuracy"] or 0) for s in students) / total_s) if total_s else 0

        c1, c2, c3 = st.columns(3)
        for col, label, val, color in [
            (c1, "👨‍🎓 Всього учнів",    total_s,         "#60a5fa"),
            (c2, "🏃 Активних",          active_s,        "#4ade80"),
            (c3, "📈 Середня точність",  f"{avg_all:.1f}%","#fbbf24"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:#1e293b;border-radius:12px;padding:18px;text-align:center;">
                  <div style="font-size:1.8rem;font-weight:800;color:{color};">{val}</div>
                  <div style="color:#94a3b8;font-size:0.82rem;margin-top:4px;">{label}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Filters ──────────────────────────────────────────────────────────
        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            search_s = st.text_input("🔍 Пошук учня",
                                     placeholder="Прізвище, ім'я або логін...",
                                     label_visibility="collapsed")
        with col_f2:
            sort_by = st.selectbox("Сортувати", ["За прізвищем", "За точністю ↓", "За сесіями ↓"],
                                   label_visibility="collapsed")

        filtered = [s for s in students
                    if search_s.lower() in (s["last_name"] or "").lower()
                    or search_s.lower() in (s["first_name"] or "").lower()
                    or search_s.lower() in (s["username"] or "").lower()] \
                   if search_s else students

        if sort_by == "За точністю ↓":
            filtered = sorted(filtered, key=lambda x: float(x["avg_accuracy"] or 0), reverse=True)
        elif sort_by == "За сесіями ↓":
            filtered = sorted(filtered, key=lambda x: int(x["total_sessions"] or 0), reverse=True)

        st.markdown(f"<p style='color:#64748b;font-size:0.85rem;margin-bottom:8px;'>"
                    f"Показано {len(filtered)} з {total_s} учнів</p>", unsafe_allow_html=True)

        # ── Student cards ─────────────────────────────────────────────────────
        for s in filtered:
            full_name = f"{s['last_name'] or ''} {s['first_name'] or ''}".strip() or s["username"]
            acc       = float(s["avg_accuracy"] or 0)
            avg_g     = float(s["avg_grade"] or 0)
            sessions  = int(s["total_sessions"] or 0)
            answers   = int(s["total_answers"] or 0)
            correct   = int(s["total_correct"] or 0)
            school    = s.get("school") or ""
            grade_cl  = s.get("grade_class") or ""

            meta_pills = ""
            if school:    meta_pills += pill(f"🏫 {school}") + " "
            if grade_cl:  meta_pills += pill(f"📋 {grade_cl} клас")

            bar = accuracy_bar(acc)

            with st.expander(f"**{full_name}** · @{s['username']}  —  "
                             f"{sessions} сес. · {acc:.0f}% · {avg_g:.1f}/12"):

                col_info, col_stats, col_act = st.columns([3, 3, 1])

                with col_info:
                    st.markdown(f"""
                    <div style="color:#94a3b8;font-size:0.82rem;margin-bottom:6px;">👤 Профіль</div>
                    <div style="color:#f1f5f9;font-weight:600;font-size:1rem;">{full_name}</div>
                    <div style="color:#64748b;font-size:0.82rem;">@{s['username']}</div>
                    <div style="margin-top:6px;">{meta_pills}</div>
                    <div style="margin-top:8px;color:#64748b;font-size:0.78rem;">
                      Зареєстрований: {s['created_at'].strftime('%d.%m.%Y') if s['created_at'] else '—'}<br>
                      Останній вхід: {s['last_login'].strftime('%d.%m.%Y %H:%M') if s['last_login'] else '—'}
                    </div>
                    """, unsafe_allow_html=True)

                with col_stats:
                    st.markdown(f"""
                    <div style="color:#94a3b8;font-size:0.82rem;margin-bottom:6px;">📊 Статистика</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                      <div style="background:#0f172a;border-radius:8px;padding:10px;text-align:center;">
                        <div style="font-size:1.3rem;font-weight:800;color:#60a5fa;">{sessions}</div>
                        <div style="color:#64748b;font-size:0.72rem;">сесій</div>
                      </div>
                      <div style="background:#0f172a;border-radius:8px;padding:10px;text-align:center;">
                        <div style="font-size:1.3rem;font-weight:800;color:#a78bfa;">{answers}</div>
                        <div style="color:#64748b;font-size:0.72rem;">відповідей</div>
                      </div>
                      <div style="background:#0f172a;border-radius:8px;padding:10px;text-align:center;">
                        <div style="font-size:1.3rem;font-weight:800;color:#4ade80;">{correct}</div>
                        <div style="color:#64748b;font-size:0.72rem;">правильних</div>
                      </div>
                      <div style="background:#0f172a;border-radius:8px;padding:10px;text-align:center;">
                        <div style="font-size:1.3rem;font-weight:800;color:{grade_color(avg_g)};">
                          {avg_g:.1f}/12
                        </div>
                        <div style="color:#64748b;font-size:0.72rem;">сер. оцінка</div>
                      </div>
                    </div>
                    <div style="margin-top:8px;color:#94a3b8;font-size:0.78rem;">
                      Точність {acc:.1f}%{bar}</div>
                    """, unsafe_allow_html=True)

                with col_act:
                    st.markdown("<div style='color:#94a3b8;font-size:0.82rem;margin-bottom:6px;'>⚙️ Дії</div>",
                                unsafe_allow_html=True)

                    # View sessions button
                    if st.button("📋 Сесії", key=f"sess_{s['id']}", use_container_width=True):
                        st.session_state[f"show_sessions_{s['id']}"] = \
                            not st.session_state.get(f"show_sessions_{s['id']}", False)

                    # Delete student
                    if st.button("🗑️ Видалити", key=f"del_s_{s['id']}", use_container_width=True):
                        st.session_state[f"confirm_del_student_{s['id']}"] = True

                # Confirm delete
                if st.session_state.get(f"confirm_del_student_{s['id']}"):
                    st.warning(f"⚠️ Видалити учня **{full_name}** та всі його дані?")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("✅ Так, видалити", key=f"yes_del_s_{s['id']}",
                                     use_container_width=True):
                            c2 = get_conn()
                            if c2:
                                delete_student(c2, s['id'])
                                c2.close()
                            st.session_state.pop(f"confirm_del_student_{s['id']}", None)
                            st.success("✅ Учня видалено.")
                            st.rerun()
                    with cc2:
                        if st.button("❌ Скасувати", key=f"no_del_s_{s['id']}",
                                     use_container_width=True):
                            st.session_state.pop(f"confirm_del_student_{s['id']}", None)
                            st.rerun()

                # Session history table
                if st.session_state.get(f"show_sessions_{s['id']}"):
                    c2 = get_conn()
                    sess_rows = get_student_sessions(c2, s['id']) if c2 else []
                    if c2: c2.close()

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color:#94a3b8;font-size:0.85rem;font-weight:600;"
                                f"margin-bottom:6px;'>🕐 Останні сесії ({len(sess_rows)})</div>",
                                unsafe_allow_html=True)

                    if not sess_rows:
                        st.caption("Сесій ще немає.")
                    else:
                        # Header
                        st.markdown("""
                        <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr;
                                    gap:6px;padding:8px 12px;background:#0f172a;border-radius:6px 6px 0 0;
                                    color:#475569;font-size:0.75rem;font-weight:600;text-transform:uppercase;">
                          <div>Дата</div><div style="text-align:center;">Всього</div>
                          <div style="text-align:center;">✅</div><div style="text-align:center;">❌</div>
                          <div style="text-align:center;">Точність</div><div style="text-align:center;">Оцінка</div>
                        </div>""", unsafe_allow_html=True)

                        for idx, sr in enumerate(sess_rows):
                            bg = "#1e293b" if idx % 2 == 0 else "#172032"
                            a  = float(sr["accuracy"] or 0)
                            g  = int(sr["grade"] or 0)
                            ac = "#4ade80" if a >= 70 else ("#fbbf24" if a >= 40 else "#f87171")
                            date_s = sr["started_at"].strftime("%d.%m.%Y %H:%M") if sr["started_at"] else "—"
                            rr = "border-radius:0 0 6px 6px;" if idx == len(sess_rows)-1 else ""
                            st.markdown(f"""
                            <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr;
                                        gap:6px;padding:10px 12px;background:{bg};align-items:center;{rr}">
                              <div style="color:#cbd5e1;font-size:0.85rem;">{date_s}</div>
                              <div style="text-align:center;color:#60a5fa;font-weight:700;">{sr['total_count']}</div>
                              <div style="text-align:center;color:#4ade80;font-weight:700;">{sr['correct_count']}</div>
                              <div style="text-align:center;color:#f87171;font-weight:700;">{sr['wrong_count']}</div>
                              <div style="text-align:center;">
                                <span style="color:{ac};font-weight:700;">{a:.1f}%</span>
                                {accuracy_bar(a)}
                              </div>
                              <div style="text-align:center;font-weight:800;color:{grade_color(g)};">{g}/12</div>
                            </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — WORDS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_words:
        conn = get_conn()
        if not conn:
            return

        wstats = get_words_stats(conn)
        conn.close()

        # ── Word stats row ────────────────────────────────────────────────────
        c1, c2, c3 = st.columns(3)
        for col, label, val, color in [
            (c1, "📚 Всього слів",       wstats["total"] or 0,       "#60a5fa"),
            (c2, "📖 З підказками",      wstats["with_poem"] or 0,    "#4ade80"),
            (c3, "📝 Без підказок",      wstats["without_poem"] or 0, "#f87171"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:#1e293b;border-radius:12px;padding:18px;text-align:center;">
                  <div style="font-size:1.8rem;font-weight:800;color:{color};">{val}</div>
                  <div style="color:#94a3b8;font-size:0.82rem;margin-top:4px;">{label}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Add new word ──────────────────────────────────────────────────────
        with st.expander("➕ Додати нове слово", expanded=False):
            st.markdown("""
            <div style="background:#1e3a5f;border-radius:8px;padding:10px 14px;
                        color:#93c5fd;font-size:0.83rem;margin-bottom:12px;">
              💡 <strong>Формат:</strong> Позначте наголошену голосну ВЕЛИКОЮ літерою.<br>
              Приклад: <code>прИклад</code>, <code>вірнОсть</code>, <code>олІвець</code>
            </div>
            """, unsafe_allow_html=True)

            with st.form("add_word_form", clear_on_submit=True):
                col_w, col_p = st.columns([1, 2])
                with col_w:
                    new_word = st.text_input("Слово*", placeholder="прИклад")
                with col_p:
                    new_poem = st.text_area("Підказка / прислів'я (необов'язково)",
                                            placeholder="Короткий текст для запам'ятовування наголосу...",
                                            height=80)
                add_submitted = st.form_submit_button("➕ Додати слово", use_container_width=True)

            if add_submitted:
                ok_v, err_v = validate_stressed_word(new_word.strip())
                if not ok_v:
                    st.error(f"❌ {err_v}")
                else:
                    c2 = get_conn()
                    if c2:
                        ok, err = add_word(c2, new_word.strip(), new_poem.strip() or None)
                        c2.close()
                        if ok:
                            st.success(f"✅ Слово **{new_word.strip()}** додано!")
                            st.rerun()
                        else:
                            st.error(f"❌ Помилка: {err}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Search / filter ───────────────────────────────────────────────────
        col_s, col_f = st.columns([3, 1])
        with col_s:
            search_w = st.text_input("🔍 Пошук слова", placeholder="Введіть частину слова...",
                                     label_visibility="collapsed")
        with col_f:
            filter_poem = st.selectbox("Фільтр", ["Всі", "З підказкою", "Без підказки"],
                                       label_visibility="collapsed")

        conn = get_conn()
        words = get_all_words(conn, search_w) if conn else []
        if conn: conn.close()

        def _has_real_poem(w):
            raw = (w["poem"] or "").strip()
            return bool(raw) and raw != "---"

        if filter_poem == "З підказкою":
            words = [w for w in words if _has_real_poem(w)]
        elif filter_poem == "Без підказки":
            words = [w for w in words if not _has_real_poem(w)]

        st.markdown(f"<p style='color:#64748b;font-size:0.85rem;margin-bottom:8px;'>"
                    f"Показано {len(words)} слів</p>", unsafe_allow_html=True)

        # ── Word list ─────────────────────────────────────────────────────────
        for w in words:
            # Treat None, empty string, or "---" all as no poem
            raw_poem = (w["poem"] or "").strip()
            has_poem = bool(raw_poem) and raw_poem != "---"
            poem_icon = "📖" if has_poem else "📝"
            poem_status = "є підказка" if has_poem else "немає підказки"

            with st.expander(f"{poem_icon}  {w['word']}  —  {poem_status}", expanded=False):

                # ── Edit form ──────────────────────────────────────────────
                with st.form(f"edit_word_{w['id']}"):
                    st.markdown("<div style='color:#94a3b8;font-size:0.82rem;margin-bottom:6px;'>"
                                "✏️ Редагувати</div>", unsafe_allow_html=True)
                    st.markdown("""
                    <div style="background:#1e3a5f;border-radius:6px;padding:8px 12px;
                                color:#93c5fd;font-size:0.78rem;margin-bottom:10px;">
                      Наголошена голосна — ВЕЛИКОЮ літерою (напр. <code>прИклад</code>)
                    </div>""", unsafe_allow_html=True)

                    col_ew, col_ep = st.columns([1, 2])
                    with col_ew:
                        edited_word = st.text_input("Слово", value=w["word"],
                                                    key=f"ew_{w['id']}")
                    with col_ep:
                        # Sanitise: treat "---" same as empty
                        current_poem = (w["poem"] or "").strip()
                        if current_poem == "---":
                            current_poem = ""
                        edited_poem = st.text_area("Підказка / прислів'я",
                                                   value=current_poem,
                                                   height=100,
                                                   key=f"ep_{w['id']}")

                    col_save, col_del = st.columns([2, 1])
                    with col_save:
                        save_btn = st.form_submit_button("💾 Зберегти зміни",
                                                         use_container_width=True)
                    with col_del:
                        del_btn = st.form_submit_button("🗑️ Видалити слово",
                                                        use_container_width=True)

                if save_btn:
                    ok_v, err_v = validate_stressed_word(edited_word.strip())
                    if not ok_v:
                        st.error(f"❌ {err_v}")
                    else:
                        c2 = get_conn()
                        if c2:
                            ok, err = update_word(c2, w["id"],
                                                  edited_word.strip(),
                                                  edited_poem.strip())
                            c2.close()
                            if ok:
                                st.success("✅ Збережено!")
                                st.rerun()
                            else:
                                st.error(f"❌ {err}")

                if del_btn:
                    st.session_state[f"confirm_del_word_{w['id']}"] = True

                if st.session_state.get(f"confirm_del_word_{w['id']}"):
                    st.warning(f"⚠️ Видалити слово **{w['word']}**?")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("✅ Так", key=f"yes_dw_{w['id']}",
                                     use_container_width=True):
                            c2 = get_conn()
                            if c2:
                                delete_word(c2, w["id"])
                                c2.close()
                            st.session_state.pop(f"confirm_del_word_{w['id']}", None)
                            st.success("✅ Слово видалено.")
                            st.rerun()
                    with cc2:
                        if st.button("❌ Ні", key=f"no_dw_{w['id']}",
                                     use_container_width=True):
                            st.session_state.pop(f"confirm_del_word_{w['id']}", None)
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.get("teacher_auth"):
    show_teacher_panel()
else:
    show_teacher_login()