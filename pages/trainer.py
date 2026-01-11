import streamlit as st
import random
import re
from datetime import datetime
import pathlib
import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    'host': st.secrets["base_host"],
    'port': 3306,
    'database': st.secrets["base_name"],
    'user': st.secrets["base_user"],
    'password': st.secrets["base_pass"],  
    'charset': 'utf8mb4'
}

def load_css(file_path):

    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


css_path = pathlib.Path("assets/styles.css")
load_css(css_path)


def create_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"❌ Помилка підключення до БД: {e}")
        return None


def load_words():
    words_list = []
    ukrainian_vowels = 'аеєиіїоуюяАЕЄИІЇОУЮЯ'
    
    connection = create_db_connection()
    if not connection:
        st.error("❌ Не вдалось підключитись до бази даних")
        return words_list
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT word, poem FROM words_poems WHERE word IS NOT NULL")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        
        for row in rows:
            word = row['word']
            poem = row['poem']
            
            stress_positions = []
            clean_word = ""
            for char in word:
                if char in ukrainian_vowels:
                    if char.isupper():
                        stress_positions.append(len(clean_word))
                clean_word += char.lower()
            
            if len(stress_positions) != 1:
                continue
                
            vowel_indices = [i for i, c in enumerate(clean_word) if c in 'аеєиіїоуюя']
            
            if stress_positions[0] in vowel_indices:
                words_list.append({
                    'original': word,
                    'clean': clean_word,
                    'stress_position': stress_positions[0],
                    'vowel_positions': vowel_indices,
                    'hint': '',
                    'poem': poem 
                })
        
        return words_list
        
    except Error as e:
        st.error(f"❌ Помилка читання з БД: {e}")
        if connection and connection.is_connected():
            connection.close()
        return words_list


def calculate_grade(percentage):
    if percentage >= 96:
        return 12
    elif percentage >= 91:
        return 11
    elif percentage >= 86:
        return 10
    elif percentage >= 76:
        return 9
    elif percentage >= 71:
        return 8
    elif percentage >= 61:
        return 7
    elif percentage >= 51:
        return 6
    elif percentage >= 41:
        return 5
    elif percentage >= 31:
        return 4
    elif percentage >= 21:
        return 3
    elif percentage >= 11:
        return 2
    else:
        return 1


def mark_stress_in_word(word, position):
    result = ""
    for i, char in enumerate(word):
        if i == position:
            result += char.upper()
        else:
            result += char
    return result


def export_statistics():
    if st.session_state.total_count == 0:
        return None
    
    accuracy = (st.session_state.correct_count / st.session_state.total_count) * 100
    grade = calculate_grade(accuracy)
    
    report = []
    report.append("=" * 60)
    report.append("СТАТИСТИКА ТРЕНУВАННЯ НАГОЛОСІВ НМТ")
    report.append("=" * 60)
    report.append(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    report.append("")
    
    report.append("ЗАГАЛЬНА СТАТИСТИКА:")
    report.append("-" * 60)
    report.append(f"Всього спроб: {st.session_state.total_count}")
    report.append(f"Правильних відповідей: {st.session_state.correct_count}")
    report.append(f"Неправильних відповідей: {st.session_state.wrong_count}")
    report.append(f"Точність: {accuracy:.1f}%")
    report.append(f"ОЦІНКА: {grade} (з 12)")
    report.append("")
    
    report.append("ІНТЕРПРЕТАЦІЯ ОЦІНКИ:")
    report.append("-" * 60)
    if grade == 12:
        report.append("🌟 ВІДМІННО! Ви досягли найвищого рівня!")
    elif grade >= 10:
        report.append("✨ Дуже добре! Ви чудово орієнтуєтесь у наголосах!")
    elif grade >= 7:
        report.append("👍 Добре! Продовжуйте тренуватись!")
    elif grade >= 5:
        report.append("📚 Задовільно. Потрібно більше практики.")
    else:
        report.append("💪 Не зупиняйтесь! Регулярна практика допоможе!")
    report.append("")

    if st.session_state.correct_answers:
        report.append("✅ ПРАВИЛЬНІ ВІДПОВІДІ:")
        report.append("-" * 60)
        for i, answer in enumerate(st.session_state.correct_answers, 1):
            word_with_stress = mark_stress_in_word(answer['word'], answer['stress_position'])
            report.append(f"{i}. {word_with_stress}")
        report.append("")
    
    if st.session_state.wrong_answers:
        report.append("❌ ПОМИЛКИ:")
        report.append("-" * 60)
        for i, answer in enumerate(st.session_state.wrong_answers, 1):
            correct_word = mark_stress_in_word(answer['word'], answer['correct_position'])
            selected_word = mark_stress_in_word(answer['word'], answer['selected_position'])
            report.append(f"{i}. Слово: {answer['word']}")
            report.append(f"   Ви обрали: {selected_word}")
            report.append(f"   Правильно: {correct_word}")
            report.append("")
    
    report.append("РЕКОМЕНДАЦІЇ:")
    report.append("-" * 60)
    if accuracy >= 90:
        report.append("• Чудова робота! Продовжуйте підтримувати високий рівень!")
        report.append("• Спробуйте працювати зі складнішими словами.")
    elif accuracy >= 70:
        report.append("• Гарний результат! Зверніть увагу на слова, в яких помилилися.")
        report.append("• Повторіть складні випадки кілька разів.")
    elif accuracy >= 50:
        report.append("• Практикуйтесь регулярно - це ключ до успіху!")
        report.append("• Зверніть особливу увагу на слова з помилок.")
        report.append("• Вивчайте правила наголошування українських слів.")
    else:
        report.append("• Не переймайтесь! Кожен починав з нуля.")
        report.append("• Тренуйтесь щодня по 10-15 хвилин.")
        report.append("• Зверніть увагу на основні правила наголосів.")
        report.append("• Проаналізуйте слова з розділу помилок.")
    
    report.append("")
    report.append("=" * 60)
    report.append("Дякуємо за використання НМТ Тренажера!")
    report.append("Бажаємо успіхів на іспиті! 🇺🇦")
    report.append("=" * 60)
    
    return "\n".join(report)


if 'words' not in st.session_state:
    st.session_state.words = load_words()
    
if not st.session_state.words:
    st.stop()

if 'current_word' not in st.session_state:
    st.session_state.current_word = random.choice(st.session_state.words)
    
if 'answered' not in st.session_state:
    st.session_state.answered = False
    
if 'selected_position' not in st.session_state:
    st.session_state.selected_position = None
    
if 'correct_count' not in st.session_state:
    st.session_state.correct_count = 0
    
if 'wrong_count' not in st.session_state:
    st.session_state.wrong_count = 0
    
if 'total_count' not in st.session_state:
    st.session_state.total_count = 0

if 'correct_answers' not in st.session_state:
    st.session_state.correct_answers = []
    
if 'wrong_answers' not in st.session_state:
    st.session_state.wrong_answers = []


def next_word():
    st.session_state.current_word = random.choice(st.session_state.words)
    st.session_state.answered = False
    st.session_state.selected_position = None


def check_answer(position):
    st.session_state.selected_position = position
    st.session_state.answered = True
    st.session_state.total_count += 1
    
    word = st.session_state.current_word['clean']
    correct_position = st.session_state.current_word['stress_position']
    
    if position == correct_position:
        st.session_state.correct_count += 1
        st.session_state.correct_answers.append({
            'word': word,
            'stress_position': correct_position
        })
    else:
        st.session_state.wrong_count += 1
        st.session_state.wrong_answers.append({
            'word': word,
            'correct_position': correct_position,
            'selected_position': position
        })


st.sidebar.title("НМТ Тренажер")
st.sidebar.markdown("Підготовка до НМТ")
st.sidebar.markdown("---")

if st.session_state.total_count > 0:
    accuracy = (st.session_state.correct_count / st.session_state.total_count) * 100
    grade = calculate_grade(accuracy)
    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e293b, #334155); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 15px;">
        <div style="font-size: 2rem; font-weight: 800; color: #fbbf24;">{accuracy:.0f}%</div>
        <div style="color: #94a3b8; font-size: 0.85rem;">Точність</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #4ade80; margin-top: 10px;">{grade}/12</div>
        <div style="color: #94a3b8; font-size: 0.85rem;">Оцінка</div>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="display: grid; gap: 10px;">
    <div style="background: #1e293b; padding: 15px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center;">
        <span style="color: #94a3b8;">✅ Правильно</span>
        <span style="color: #4ade80; font-weight: 700; font-size: 1.3rem;">{st.session_state.correct_count}</span>
    </div>
    <div style="background: #1e293b; padding: 15px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center;">
        <span style="color: #94a3b8;">❌ Неправильно</span>
        <span style="color: #f87171; font-weight: 700; font-size: 1.3rem;">{st.session_state.wrong_count}</span>
    </div>
    <div style="background: #1e293b; padding: 15px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center;">
        <span style="color: #94a3b8;">📝 Всього</span>
        <span style="color: #60a5fa; font-weight: 700; font-size: 1.3rem;">{st.session_state.total_count}</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<br>", unsafe_allow_html=True)


if st.session_state.total_count > 0:
    if st.sidebar.button("📥 Експортувати статистику", use_container_width=True):
        stats_text = export_statistics()
        if stats_text:
            filename = f"nmt_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            st.sidebar.download_button(
                label="⬇️ Завантажити звіт",
                data=stats_text,
                file_name=filename,
                mime="text/plain",
                use_container_width=True
            )
            st.sidebar.success("✅ Звіт готовий до завантаження!")

if st.sidebar.button("🔄 Скинути статистику", use_container_width=True):
    st.session_state.correct_count = 0
    st.session_state.wrong_count = 0
    st.session_state.total_count = 0
    st.session_state.correct_answers = []
    st.session_state.wrong_answers = []
    st.rerun()


st.markdown("""
<div class="trainer-header">
    <h1>📚 Тренажер наголосів</h1>
    <p>Натисніть на голосну букву, на яку падає наголос</p>
</div>
""", unsafe_allow_html=True)

accuracy = (st.session_state.correct_count / st.session_state.total_count * 100) if st.session_state.total_count > 0 else 0

st.markdown(f"""
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-number blue">{st.session_state.total_count}</div>
        <div class="stat-label">Всього спроб</div>
    </div>
    <div class="stat-card">
        <div class="stat-number green">{st.session_state.correct_count}</div>
        <div class="stat-label">Правильно</div>
    </div>
    <div class="stat-card">
        <div class="stat-number red">{st.session_state.wrong_count}</div>
        <div class="stat-label">Неправильно</div>
    </div>
    <div class="stat-card">
        <div class="stat-number yellow">{accuracy:.0f}%</div>
        <div class="stat-label">Точність</div>
    </div>
</div>
""", unsafe_allow_html=True)


st.markdown("""
<div class="hint-box">
    💡 <strong>Підказка:</strong> Натисніть на синю букву, яка є наголошеною
</div>
""", unsafe_allow_html=True)


word_data = st.session_state.current_word
word = word_data['clean']
stress_pos = word_data['stress_position']
vowel_positions = word_data['vowel_positions']


st.markdown("""
<div class="word-container">
    <div class="word-label">Визначте наголос</div>
""", unsafe_allow_html=True)


if st.session_state.answered:

    letters_html = '<div class="letters-row">'
    
    for i, char in enumerate(word):
        is_vowel = i in vowel_positions
        
        if i == stress_pos:

            letters_html += f'<div class="letter letter-correct">{char.upper()}</div>'
        elif i == st.session_state.selected_position and i != stress_pos:

            letters_html += f'<div class="letter letter-wrong">{char.upper()}</div>'
        elif is_vowel:

            letters_html += f'<div class="letter letter-disabled">{char.upper()}</div>'
        else:

            letters_html += f'<div class="letter letter-consonant">{char.upper()}</div>'
    
    letters_html += '</div>'
    st.markdown(letters_html, unsafe_allow_html=True)
    
else:

    num_empty = max(0, (15 - len(word)) // 2)
    cols = st.columns([0.5] * num_empty + [1] * len(word) + [0.5] * num_empty)
    
    for i, char in enumerate(word):
        is_vowel = i in vowel_positions
        col_idx = num_empty + i
        
        with cols[col_idx]:
            if is_vowel:
                if st.button(char.upper(), key=f"vowel_{i}"):
                    check_answer(i)
                    st.rerun()
            else:
                st.markdown(f'<div class="letter letter-consonant">{char.upper()}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


if word_data['hint']:
    st.markdown(f"""
    <div style="text-align: center; color: #64748b; margin-top: 15px; font-size: 0.9rem;">
        {word_data['hint']}
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.answered:
    is_correct = st.session_state.selected_position == stress_pos
    
    if is_correct:
        st.markdown("""
        <div class="result-box result-correct">
            ✅ Правильно! Чудова робота! 🎉
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="result-box result-wrong">
            ❌ Неправильно. Правильна відповідь: <strong>{word_data['original']}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        if word_data.get('poem'):
            st.markdown(f"""
            <div class="poem-box">
                <div class="poem-title">📖 Текст для запам'ятовування:</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(" ")
            st.markdown(f"""
            <div class="poem-box">
                <div class="poem-text">{word_data['poem']}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("*** ")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("➡️ Наступне слово", use_container_width=True):
            next_word()
            st.rerun()

st.markdown(f"""
<div style="text-align: center; color: #475569; padding: 30px 0; margin-top: 30px; border-top: 1px solid #334155;">
    📚 В базі: <strong style="color: #60a5fa;">{len(st.session_state.words)}</strong> слів для практики
</div>
""", unsafe_allow_html=True)