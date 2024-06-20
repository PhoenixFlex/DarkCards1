import sqlite3

# Функция для получения новой карты
async def receive_card(user_id, card_name):
    # Подключение к базе данных
    conn = sqlite3.connect('cards.db')
    c = conn.cursor()
    
    # Получение карт пользователя из базы данных
    c.execute("SELECT card_name, num_duplicates FROM user_cards WHERE user_id=?", (user_id,))
    user_cards = dict(c.fetchall())
    
    if card_name in user_cards:
        user_cards[card_name] += 1
    else:
        user_cards[card_name] = 1

    # Обновление данных о картах пользователя в базе данных
    for card_name, num_duplicates in user_cards.items():
        c.execute("INSERT OR REPLACE INTO user_cards (user_id, card_name, num_duplicates) VALUES (?, ?, ?)",
                  (user_id, card_name, num_duplicates))
        
    conn.commit()
    conn.close()

    return f"Вы получили новую карту {card_name}."

# Функция для крафта попыток
async def craft_attempts(user_id, card_name, num_duplicates):
    # Подключение к базе данных
    conn = sqlite3.connect('cards.db')
    c = conn.cursor()
    
    # Получение карт пользователя из базы данных
    c.execute("SELECT card_name, num_duplicates FROM user_cards WHERE user_id=?", (user_id,))
    user_cards = dict(c.fetchall())
    
    if card_name not in user_cards or user_cards[card_name] < num_duplicates:
        return "У вас недостаточно дубликатов для крафта указанного количества попыток."

    user_cards[card_name] -= num_duplicates
 
    # Обновление данных о картах пользователя в базе данных
    for card_name, num_duplicates in user_cards.items():
        c.execute("INSERT OR REPLACE INTO user_cards (user_id, card_name, num_duplicates) VALUES (?, ?, ?)", 
                  (user_id, card_name, num_duplicates))
        
    conn.commit()
    conn.close()

    return f"Вы успешно скрафтили {num_duplicates} попыток для карты {card_name}."
