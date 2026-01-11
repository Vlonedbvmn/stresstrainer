import streamlit as st
import random
import re
from datetime import datetime

# ============================================
# CUSTOM CSS - PROPER STREAMLIT BUTTON STYLING
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main {
        background: #0f172a;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
    }
    
    /* Header */
    .trainer-header {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        padding: 30px 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 20px 40px rgba(59, 130, 246, 0.3);
    }
    
    .trainer-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
    }
    
    .trainer-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin: 10px 0 0 0;
    }
    
    /* Stats */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin-bottom: 30px;
    }
    
    @media (max-width: 768px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    .stat-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        border: 1px solid #475569;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    
    .stat-number.blue { color: #60a5fa; }
    .stat-number.green { color: #4ade80; }
    .stat-number.red { color: #f87171; }
    .stat-number.yellow { color: #fbbf24; }
    
    .stat-label {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    /* Word container */
    .word-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 50px 30px;
        border-radius: 24px;
        text-align: center;
        margin: 30px 0;
        border: 2px solid #334155;
        box-shadow: 0 25px 50px rgba(0,0,0,0.3);
    }
    
    .word-label {
        color: #64748b;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 20px;
    }
    
    /* Letters row */
    .letters-row {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin: 20px 0;
    }
    
    /* Letter styling */
    .letter {
        width: 60px;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: 800;
        border-radius: 16px;
        transition: all 0.3s ease;
    }
    
    /* Consonant letter */
    .letter-consonant {
        color: #64748b;
        background: transparent;
    }
    
    /* Correct answer */
    .letter-correct {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        color: white;
        box-shadow: 0 4px 20px rgba(34, 197, 94, 0.5);
        animation: pulse-green 0.5s ease;
    }
    
    /* Wrong answer */
    .letter-wrong {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        box-shadow: 0 4px 20px rgba(239, 68, 68, 0.5);
        animation: shake 0.5s ease;
    }
    
    /* Disabled vowel */
    .letter-disabled {
        background: #334155;
        color: #64748b;
    }
    
    @keyframes pulse-green {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    /* Hint */
    .hint-box {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        padding: 15px 25px;
        color: #94a3b8;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .hint-box strong {
        color: #60a5fa;
    }
    
    /* Result */
    .result-box {
        padding: 25px 40px;
        border-radius: 16px;
        text-align: center;
        margin: 25px 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    .result-correct {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        color: white;
        box-shadow: 0 10px 30px rgba(34, 197, 94, 0.3);
    }
    
    .result-wrong {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        box-shadow: 0 10px 30px rgba(239, 68, 68, 0.3);
    }
    
    /* ============================================
       VOWEL BUTTONS - STREAMLIT STYLE
       ============================================ */
    
    /* Hide button text wrapper and use only the button */
    div[data-testid="stButton"] > button p {
        font-size: 2rem !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Style vowel buttons to look exactly like result tiles */
    div[data-testid="stButton"] > button {
        width: 60px !important;
        height: 70px !important;
        min-width: 60px !important;
        min-height: 70px !important;
        
        padding: 0 !important;
        margin: 0 auto !important;
        
        font-size: 2rem !important;
        font-weight: 800 !important;
        
        border-radius: 16px !important;
        border: none !important;
        
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.35) !important;
        
        transition: all 0.3s ease !important;
        
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-5px) scale(1.05) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.45) !important;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    }
    
    div[data-testid="stButton"] > button:active,
    div[data-testid="stButton"] > button:focus {
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.3), 0 4px 20px rgba(59, 130, 246, 0.35) !important;
    }
</style>
""", unsafe_allow_html=True)


def load_words():
    """Load words from data.txt"""
    words_list = []
    ukrainian_vowels = 'аеєиіїоуюяАЕЄИІЇОУЮЯ'
    
    with open('data/words.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        word_match = re.match(r'^([а-яА-ЯіІїЇєЄґҐ\'\-]+)', line)
        if not word_match:
            continue
            
        word = word_match.group(1)
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
                'hint': line.replace(word, '').strip() if line != word else ''
            })
    
    return words_list


def calculate_grade(percentage):
    """Calculate grade from 1 to 12 based on percentage"""
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
    """Mark stress position in word with capital letter"""
    result = ""
    for i, char in enumerate(word):
        if i == position:
            result += char.upper()
        else:
            result += char
    return result


def export_statistics():
    """Generate statistics text file"""
    if st.session_state.total_count == 0:
        return None
    
    # Calculate statistics
    accuracy = (st.session_state.correct_count / st.session_state.total_count) * 100
    grade = calculate_grade(accuracy)
    
    # Generate report
    report = []
    report.append("=" * 60)
    report.append("СТАТИСТИКА ТРЕНУВАННЯ НАГОЛОСІВ НМТ")
    report.append("=" * 60)
    report.append(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    report.append("")
    
    # Summary
    report.append("ЗАГАЛЬНА СТАТИСТИКА:")
    report.append("-" * 60)
    report.append(f"Всього спроб: {st.session_state.total_count}")
    report.append(f"Правильних відповідей: {st.session_state.correct_count}")
    report.append(f"Неправильних відповідей: {st.session_state.wrong_count}")
    report.append(f"Точність: {accuracy:.1f}%")
    report.append(f"ОЦІНКА: {grade}")
    report.append("")
    
    # Grade interpretation
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
    
    # Correct answers
    if st.session_state.correct_answers:
        report.append("✅ ПРАВИЛЬНІ ВІДПОВІДІ:")
        report.append("-" * 60)
        for i, answer in enumerate(st.session_state.correct_answers, 1):
            word_with_stress = mark_stress_in_word(answer['word'], answer['stress_position'])
            report.append(f"{i}. {word_with_stress}")
        report.append("")
    
    # Wrong answers
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
    
    # Recommendations
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


# Initialize session state
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

# NEW: Detailed tracking
if 'correct_answers' not in st.session_state:
    st.session_state.correct_answers = []
    
if 'wrong_answers' not in st.session_state:
    st.session_state.wrong_answers = []


def next_word():
    """Load next word"""
    st.session_state.current_word = random.choice(st.session_state.words)
    st.session_state.answered = False
    st.session_state.selected_position = None


def check_answer(position):
    """Check if answer is correct"""
    st.session_state.selected_position = position
    st.session_state.answered = True
    st.session_state.total_count += 1
    
    word = st.session_state.current_word['clean']
    correct_position = st.session_state.current_word['stress_position']
    
    if position == correct_position:
        st.session_state.correct_count += 1
        # Track correct answer
        st.session_state.correct_answers.append({
            'word': word,
            'stress_position': correct_position
        })
    else:
        st.session_state.wrong_count += 1
        # Track wrong answer with details
        st.session_state.wrong_answers.append({
            'word': word,
            'correct_position': correct_position,
            'selected_position': position
        })


# ===== SIDEBAR =====
st.sidebar.title("НМТ Тренажер")
st.sidebar.markdown("Підготовка до НМТ")
st.sidebar.markdown("---")

# Sidebar stats
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

# Export button
if st.session_state.total_count > 0:
    if st.sidebar.button("📥 Експортувати статистику", use_container_width=True):
        stats_text = export_statistics()
        if stats_text:
            # Generate filename with timestamp
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


# ===== MAIN CONTENT =====

# Header
st.markdown("""
<div class="trainer-header">
    <h1>📚 Тренажер наголосів</h1>
    <p>Натисніть на голосну букву, на яку падає наголос</p>
</div>
""", unsafe_allow_html=True)

# Stats
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

# Hint
st.markdown("""
<div class="hint-box">
    💡 <strong>Підказка:</strong> Натисніть на синю букву, яка є наголошеною
</div>
""", unsafe_allow_html=True)

# Get current word
word_data = st.session_state.current_word
word = word_data['clean']
stress_pos = word_data['stress_position']
vowel_positions = word_data['vowel_positions']

# Word container header
st.markdown("""
<div class="word-container">
    <div class="word-label">Визначте наголос</div>
""", unsafe_allow_html=True)

# Display word
if st.session_state.answered:
    # AFTER ANSWERING: Use pure HTML/CSS
    letters_html = '<div class="letters-row">'
    
    for i, char in enumerate(word):
        is_vowel = i in vowel_positions
        
        if i == stress_pos:
            # Correct answer - always green
            letters_html += f'<div class="letter letter-correct">{char.upper()}</div>'
        elif i == st.session_state.selected_position and i != stress_pos:
            # Wrong selection - red
            letters_html += f'<div class="letter letter-wrong">{char.upper()}</div>'
        elif is_vowel:
            # Other vowels - gray
            letters_html += f'<div class="letter letter-disabled">{char.upper()}</div>'
        else:
            # Consonants - gray text
            letters_html += f'<div class="letter letter-consonant">{char.upper()}</div>'
    
    letters_html += '</div>'
    st.markdown(letters_html, unsafe_allow_html=True)
    
else:
    # BEFORE ANSWERING: Use Streamlit buttons with proper styling
    # Create columns for letters
    num_empty = max(0, (15 - len(word)) // 2)
    cols = st.columns([0.5] * num_empty + [1] * len(word) + [0.5] * num_empty)
    
    for i, char in enumerate(word):
        is_vowel = i in vowel_positions
        col_idx = num_empty + i
        
        with cols[col_idx]:
            if is_vowel:
                # Vowel - use Streamlit button
                if st.button(char.upper(), key=f"vowel_{i}"):
                    check_answer(i)
                    st.rerun()
            else:
                # Consonant - use HTML div
                st.markdown(f'<div class="letter letter-consonant">{char.upper()}</div>', unsafe_allow_html=True)

# Close word container
st.markdown('</div>', unsafe_allow_html=True)

# Hint under word
if word_data['hint']:
    st.markdown(f"""
    <div style="text-align: center; color: #64748b; margin-top: 15px; font-size: 0.9rem;">
        {word_data['hint']}
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Result
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
    
    # Next word button - with custom styling
    st.markdown("""
    <style>
    /* Style ONLY the next word button differently */
    .element-container:has(.next-word-btn) button {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
        width: auto !important;
        height: auto !important;
        padding: 15px 40px !important;
        font-size: 1.1rem !important;
        border-radius: 16px !important;
    }
    .element-container:has(.next-word-btn) button:hover {
        transform: translateY(-2px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="next-word-btn">', unsafe_allow_html=True)
        if st.button("➡️ Наступне слово", use_container_width=True):
            next_word()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div style="text-align: center; color: #475569; padding: 30px 0; margin-top: 30px; border-top: 1px solid #334155;">
    📚 В базі: <strong style="color: #60a5fa;">{len(st.session_state.words)}</strong> слів для практики
</div>
""", unsafe_allow_html=True)