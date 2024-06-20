import sqlite3
import random
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
# Создание базы данных и таблицы для хранения информации о картах
def create_database(id):
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()

    # Создание таблицы cards с полями id, user_id, card_name, card_info
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS cards_{id} (card_name TEXT, rarity TEXT, card_info TEXT,hp INTEGER,attack INTEGER,defense INTEGER,crit_rate INTEGER,speed INTEGER, enhance_level INTEGER,verse TEXT,photo TEXT) ''')
                  
                  
                  

                  
                  

    conn.commit()
    conn.close()

# Пример использования функции для удаления дубликатов из таблицы "cards"

# Функция для добавления карты в базу данных
def add_card(user_id,card_name,rarity,hp,attack,defense,crit_rate,speed,photo):

    conn_data = sqlite3.connect("user_data.db")
    curs_data = conn_data.cursor()
    curs_data.execute(f'''SELECT verse FROM user_data WHERE telegram_id = ?''',(user_id,))
    verse = [result[0] for result in curs_data.fetchall()][0]
    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    cursor.execute(f'''SELECT * FROM cards_{user_id} WHERE card_name = ?''',(card_name,))
    res_raw = cursor.fetchall()
    res = [result[0] for result in res_raw]
    if res == []:

        cursor.execute(f"INSERT INTO cards_{user_id} ( card_name, rarity, hp,attack,defense,crit_rate,speed,enhance_level,verse,photo) VALUES (?,?,?,?,?,?,?,?,?,?)", (card_name,rarity, hp,attack,defense,crit_rate,speed,0,verse,photo))
    else:
        cursor.execute(f'''UPDATE cards_{user_id} SET enhance_level = enhance_level + 1 WHERE card_name = ?''',(card_name,))
        if rarity == "Basic":
            shards = random.randint(1,10)
        elif rarity == "Unusual":
            shards = random.randint(5,15)
        elif rarity == "Epic":
            shards = random.randint(15,30)
        elif rarity == "Legendary":
            shards = random.randint(30,60)
        elif rarity == "Mythic":
            shards = random.randint(75,150)
        
        curs_data.execute(f'''UPDATE user_data SET shards = shards + ? WHERE telegram_id = ?''',(shards,user_id))
        

    conn.commit()
    conn.close()
    conn_data.commit()
    conn_data.close()

# Функция для получения всех карт пользователя
def get_user_cards(user_id,rarity):
    results_rarity = []



    conn = sqlite3.connect('cards.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT card_name FROM cards_{user_id} WHERE rarity = ?",(rarity,))
    results = cursor.fetchall()
    cursor.execute(f"SELECT enhance_level FROM cards_{user_id}")
    result_enhancelevel_raw = cursor.fetchall()
    conn.close()

    
    card_names = [result[0] for result in results]
    result_enhancelevel = [result[0] for result in result_enhancelevel_raw]
    
    counter = 0
    collection_buttons = []
    for card in card_names:
        if counter < len(result_enhancelevel):
            collection_buttons.append([InlineKeyboardButton(text=f"{card}",callback_data=f"collection_{rarity.lower()}_{card}")]) 
        counter += 1
    collection = InlineKeyboardMarkup(inline_keyboard=collection_buttons)
    return collection

# Создание базы данных и таблицы при запуске программы


# Пример

