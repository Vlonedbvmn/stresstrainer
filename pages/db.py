"""
НМТ ТРЕНАЖЕР - ПРОСТА БД
Таблиці: слово + вірш, користувачі, сесії
"""

import mysql.connector
from mysql.connector import Error
import re
import os
from groq import Groq
import time
import hashlib
import secrets


# ============================================
# КОНФІГУРАЦІЯ
# ============================================

DB_CONFIG = {
    'host': 'srv1395.hstgr.io',
    'port': 3306,
    'database': 'u422793380_ukrtest',
    'user': 'u422793380_ukrtestu',
    'password': 'OC2Ss=@Ub6$6',
    'charset': 'utf8mb4'
}

GROQ_API_KEY = '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'
WORDS_FILE = 'C:/Users/auspo/PycharmProjects/ukrmova/stress_trainer/data/words.txt'
GROQ_MODEL = 'llama-3.3-70b-versatile'
GENERATION_DELAY = 2


# ============================================
# ПІДКЛЮЧЕННЯ
# ============================================

def create_connection():
    """Підключення до MySQL"""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4")
            cursor.execute(f"USE {DB_CONFIG['database']}")
            cursor.close()
            print(f"✅ Підключено до БД: {DB_CONFIG['database']}")
            return connection

    except Error as e:
        print(f"❌ Помилка: {e}")
        return None


# ============================================
# СТВОРЕННЯ ТАБЛИЦЬ
# ============================================

def create_table(connection):
    """Створює таблицю слів і поем"""
    cursor = connection.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS words_poems (
            id INT AUTO_INCREMENT PRIMARY KEY,
            word VARCHAR(100) NOT NULL UNIQUE,
            poem TEXT,
            INDEX idx_word (word)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        connection.commit()
        cursor.close()
        print("✅ Таблиця 'words_poems' створена")
        return True
    except Error as e:
        print(f"❌ Помилка створення таблиці: {e}")
        cursor.close()
        return False


def create_user_tables(connection):
    """Створює таблиці для користувачів та їхньої статистики"""
    cursor = connection.cursor()
    try:
        # Таблиця користувачів
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(64) NOT NULL,
            salt VARCHAR(32) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            school VARCHAR(200),
            grade_class VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            INDEX idx_username (username),
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Таблиця сесій тренувань
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            total_count INT DEFAULT 0,
            correct_count INT DEFAULT 0,
            wrong_count INT DEFAULT 0,
            accuracy DECIMAL(5,2) DEFAULT 0.00,
            grade INT DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_started_at (started_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Таблиця детальних відповідей у сесії
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_answers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            word VARCHAR(100) NOT NULL,
            is_correct BOOLEAN NOT NULL,
            answered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES training_sessions(id) ON DELETE CASCADE,
            INDEX idx_session_id (session_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        connection.commit()
        cursor.close()
        print("✅ Таблиці користувачів створено")
        return True

    except Error as e:
        print(f"❌ Помилка створення таблиць користувачів: {e}")
        cursor.close()
        return False


# ============================================
# УТИЛІТИ ПАРОЛІВ
# ============================================

def hash_password(password: str, salt: str = None):
    """Хешує пароль із сіллю (SHA-256)"""
    if salt is None:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return pw_hash, salt


# ============================================
# РЕЄСТРАЦІЯ / ВХІД
# ============================================

def register_user(connection, username: str, email: str, password: str,
                  first_name: str = None, last_name: str = None,
                  school: str = None, grade_class: str = None):
    """
    Реєструє нового користувача.
    Повертає (True, user_id) або (False, повідомлення_помилки).
    """
    cursor = connection.cursor(dictionary=True)
    try:
        # Перевірка унікальності
        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email)
        )
        if cursor.fetchone():
            cursor.close()
            return False, "Користувач із таким іменем або email вже існує."

        pw_hash, salt = hash_password(password)
        cursor.execute(
            """INSERT INTO users
               (username, email, password_hash, salt, first_name, last_name, school, grade_class)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (username, email, pw_hash, salt,
             first_name or None, last_name or None,
             school or None, grade_class or None)
        )
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return True, new_id

    except Error as e:
        cursor.close()
        return False, str(e)


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


# ============================================
# РОБОТА ЗІ СЛОВАМИ (без змін)
# ============================================

def parse_words_from_file(file_path):
    words_list = []
    ukrainian_vowels = 'аеєиіїоуюяАЕЄИІЇОУЮЯ'

    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не знайдено!")
        return words_list

    with open(file_path, 'r', encoding='utf-8') as file:
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

        if stress_positions[0] not in vowel_indices:
            continue

        stressed_word = ""
        for i, char in enumerate(clean_word):
            if i == stress_positions[0]:
                stressed_word += char.upper()
            else:
                stressed_word += char

        words_list.append(stressed_word)

    print(f"✅ Завантажено {len(words_list)} слів")
    return words_list


def insert_words_to_db(connection, words_list):
    cursor = connection.cursor()
    insert_query = "INSERT IGNORE INTO words_poems (word) VALUES (%s)"
    inserted = 0
    for word in words_list:
        try:
            cursor.execute(insert_query, (word,))
            inserted += 1
        except Error as e:
            print(f"❌ Помилка: {e}")
    connection.commit()
    cursor.close()
    print(f"✅ Вставлено {inserted} слів")
    return inserted


def get_words_without_poems(connection, limit=None):
    cursor = connection.cursor(dictionary=True)
    query = "SELECT id, word FROM words_poems WHERE poem IS NULL"
    if limit:
        query += f" LIMIT {limit}"
    cursor.execute(query)
    words = cursor.fetchall()
    cursor.close()
    return words


# ============================================
# ГЕНЕРАЦІЯ ВІРШІВ (без змін)
# ============================================

def generate_poem(word, groq_client):
    stressed_letter = None
    for char in word:
        if char.isupper():
            stressed_letter = char
            break

    prompt = f"""Створи українське прислів'я для запам'ятовування наголосу в слові "{word}".

Вимоги:
- Прислів'я має бути коротким (1 рядок)
- Обов'язково використай слово "{word}" з наголосом на букві {stressed_letter}
- Прислів'я має бути змістовним та мати мораль або життєву мудрість
- Бажано використати риму для кращого запам'ятовування
- Прислів'я має звучати природно, як справжнє народне

Приклад:
Хто рано встає, той молокО п'є - здоров'я й силу собі здобуває.

Створи прислів'я для слова "{word}":"""

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ти - експерт з української мови..."},
                {"role": "user", "content": prompt}
            ],
            model=GROQ_MODEL,
            temperature=0.9,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return None


def update_poem_in_db(connection, word_id, poem):
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE words_poems SET poem = %s WHERE id = %s", (poem, word_id))
        connection.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"❌ Помилка: {e}")
        cursor.close()
        return False


def generate_poems_for_all(connection, groq_client, limit=None):
    words = get_words_without_poems(connection, limit)
    if not words:
        print("✅ Всі слова вже мають вірші!")
        return 0

    print(f"\n📝 Знайдено {len(words)} слів без віршів")
    generated = 0

    for i, word_data in enumerate(words, 1):
        word = word_data['word']
        print(f"[{i}/{len(words)}] {word}...")
        poem = generate_poem(word, groq_client)
        if poem:
            if update_poem_in_db(connection, word_data['id'], poem):
                generated += 1
        if i < len(words):
            time.sleep(GENERATION_DELAY)

    print(f"\n✅ Згенеровано {generated}/{len(words)} віршів")
    return generated


# ============================================
# ГОЛОВНА ФУНКЦІЯ (ініціалізація таблиць)
# ============================================

def main():
    print("=" * 60)
    print("НМТ ТРЕНАЖЕР - ІНІЦІАЛІЗАЦІЯ БД")
    print("=" * 60)

    connection = create_connection()
    if not connection:
        return

    try:
        create_table(connection)
        create_user_tables(connection)

        words = parse_words_from_file(WORDS_FILE)
        if words:
            insert_words_to_db(connection, words)

        groq_client = Groq(api_key=GROQ_API_KEY)
        limit_input = input("Скільки віршів згенерувати? (Enter = всі): ").strip()
        limit = int(limit_input) if limit_input.isdigit() else None
        generate_poems_for_all(connection, groq_client, limit)

    except KeyboardInterrupt:
        print("\n\n⚠️  Перервано")
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("✅ З'єднання закрито")


if __name__ == "__main__":
    main()