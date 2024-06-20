import random
from aiogram import Bot, Dispatcher, exceptions
from aiogram import Router, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command, CommandObject,CommandStart
import asyncio
import logging
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
from card import *
from collection import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime,timedelta
from aiogram.filters import StateFilter
from aiogram.filters.callback_data import CallbackData

# API токен вашего бота
API_TOKEN = '7128298940:AAGXI27KwwlJFHn7zol563OvsfbwPw3SoiQ'
#меню
get_card_btn = KeyboardButton(text = "🧧Получить карту")
collection_btn = KeyboardButton(text = "🗃Коллекция")
menu_btn = KeyboardButton(text = '📖Профиль')
kb = [[get_card_btn],[collection_btn],[menu_btn]]
keyboard = ReplyKeyboardMarkup(keyboard=kb,resize_keyboard=True)


#магазин



# Словарь с картами и их шансами выпадения
conn = sqlite3.connect("user_data.db")
curs = conn.cursor()
curs.execute('''CREATE TABLE IF NOT EXISTS user_data(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id INTEGER, nickname TEXT, gold INTEGER, gems INTEGER,pulls INTEGER,free_pulls INTEGER,points INTEGER,coins INTEGER,shards INTEGER, verse TEXT,last_free_pull DATETIME,daily_gift_cooldown DATETIME,weekly_gift_cooldown DATETIME, used_promos TEXT)''')

conn.commit()
conn.close()

# Пользовательская коллекция карт
router = Router()
# Создание бота
async def main():
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

class Form(StatesGroup):
    photo = State()
    name = State()
    rarity = State()

async def has_free_pull(user_id):
    conn = sqlite3.connect("user_data.db")
    curs = conn.cursor()
    curs.execute(f"SELECT free_pulls FROM user_data WHERE telegram_id = ?", (user_id,))
    result = curs.fetchone()
    conn.close()
    return result[0] if result else 0

# Function to update the last free pull time in the database
async def update_last_free_pull(user_id):
    conn = sqlite3.connect("user_data.db")
    curs = conn.cursor()
    curs.execute(f"UPDATE user_data SET last_free_pull = ? WHERE telegram_id = ?", (datetime.now().replace(microsecond=0), user_id))
    conn.commit()
    conn.close()

# Function to check if the free pull cooldown has passed for a specific user
async def free_pull_cooldown_passed(user_id):
    conn = sqlite3.connect("user_data.db")
    curs = conn.cursor()
    curs.execute(f"SELECT last_free_pull FROM user_data WHERE telegram_id = ?", (user_id,))
    last_free_pull_time = curs.fetchone()
    conn.close()
    if last_free_pull_time[0] != None:
        format_code = "%Y-%m-%d %H:%M:%S"

        last_free_pull_time = last_free_pull_time[0]
        return (datetime.now() - datetime.strptime(last_free_pull_time,format_code)) >= timedelta(hours=3)
    else:
        return True  # If no last free pull time, cooldown has passed

# Function to handle free pull cooldown for a specific user
async def handle_free_pull_cooldown(user_id):
    # Check if the cooldown has passed
    if await free_pull_cooldown_passed(user_id):
        # Check if the user already has a free pull
        current_free_pulls = await has_free_pull(user_id)
        if current_free_pulls == 0:  # Only set to 1 if no free pull available
            # Set free_pulls to 1
            conn = sqlite3.connect("user_data.db")
            curs = conn.cursor()
            curs.execute(f"UPDATE user_data SET free_pulls = 1 WHERE telegram_id = ?", (user_id,))
            conn.commit()
            conn.close()

        # Update the last free pull time
        await update_last_free_pull(user_id)

# Scheduled task to check for free pull cooldown for each user
async def schedule_free_pulls():
    while True:
        # Get all user IDs from the database
        conn = sqlite3.connect("user_data.db")
        curs = conn.cursor()
        curs.execute("SELECT telegram_id FROM user_data")
        user_ids = [row[0] for row in curs.fetchall()]
        conn.close()

        # Check for each user
        for user_id in user_ids:
            # Handle free pull cooldown for the user
            await handle_free_pull_cooldown(user_id)

        # Wait for 1 minute (adjust as needed)
        await asyncio.sleep(1)

# Start the scheduled task
async def main():
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    free_pull_task = asyncio.create_task(schedule_free_pulls())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()) # Start the task here!
    await free_pull_task
    


# Обработчик команды /start
@router.message(CommandStart())
async def start_handler(msg: Message):
    
    conn = sqlite3.connect("user_data.db")
    curs = conn.cursor()
    id = msg.chat.id
    curs.execute('''INSERT INTO user_data (telegram_id,nickname,gold,gems,pulls,free_pulls,points,coins,shards) VALUES (?,?,?,?,?,?,?,?,?)''',(id,msg.from_user.first_name,1000,1000,1000,1,0,1000,0))
    conn.commit()
    conn.close()

    await msg.answer(f"Привет, {msg.from_user.first_name}, введи свой никнейм в боте при помощи команды /nick, а командой /verse Выбери интересующую тебя вселенную:")

class DrawCard(StatesGroup):
    waiting = State()

class FreePullCooldown(StatesGroup):
    waiting = State()
@router.message(F.text.lower().contains("получить карту"))
async def draw_card(message: Message, state: FSMContext):
    # Get the current time
    current_time = datetime.now()

    # Check if the user is already in the waiting state
    if await state.get_state() == DrawCard.waiting.state:
        # Get the last time the command was used
        last_used_time = await state.get_data()
        last_used_time = last_used_time.get('last_used_time', None)

        # Check if 3 seconds have passed since the last use
        if last_used_time and (current_time - last_used_time).total_seconds() < 3:
            try:
                pass
            except:
                pass  # Ignore if the message can't be edited or deleted
            return

    # Set the waiting state and record the current time
    await state.set_state(DrawCard.waiting)
    await state.update_data(last_used_time=current_time)

    # Set the waiting state and record the current time
    
    conn = sqlite3.connect("user_data.db")
    curs = conn.cursor()
    id = message.chat.id
    curs.execute('''SELECT verse,pulls,free_pulls FROM user_data WHERE telegram_id = ?''', (id,))
    info = curs.fetchone()
    verse = info[0]
    pulls = info[1]
    free_pulls = info[2]
    conn.close()
    create_database(id)
    if verse != None:
        if free_pulls>0:
            card = Card(verse)
            card_get = card.generate_card()
            card_photo = card_get[1]
            add_card(id, card_get[0], card_get[2],card_get[3],card_get[4],card_get[5],card_get[6],card_get[7],card_photo)
            conn = sqlite3.connect("user_data.db")
            curs = conn.cursor()
            curs.execute('''UPDATE user_data SET free_pulls = free_pulls - 1 WHERE telegram_id = ? AND free_pulls > 0''', (id,))
            conn.commit()
            conn.close()
            conn = sqlite3.connect(f"user_data.db")
            curs = conn.cursor()
            curs.execute(f'''UPDATE user_data SET points = points + ? WHERE telegram_id = ?''', (card.point_values[card_get[2]], message.chat.id))
            conn.commit()
            curs.execute(f'''SELECT points FROM user_data WHERE telegram_id = ?''',(message.chat.id,))
            points_raw = curs.fetchall()
            points = [result[0] for result in points_raw]
            conn.close()
            await message.answer_photo(
                photo=card_photo, 
                caption=f"🃏Вам выпала карта: \n{card_get[0]} \n🔆Редкость: {card_get[2]} \n🌠DarkPoints: {points[0]}(+{card.point_values[card_get[2]]})")
        elif free_pulls==0:
            if pulls > 0:
                card = Card(verse)
                card_get = card.generate_card()
                card_photo = card_get[1]
                add_card(id, card_get[0], card_get[2],card_get[3],card_get[4],card_get[5],card_get[6],card_get[7],card_photo)
                conn = sqlite3.connect("user_data.db")
                curs = conn.cursor()
                curs.execute('''UPDATE user_data SET pulls = pulls - 1 WHERE telegram_id = ? AND pulls > 0''', (id,))
                conn.commit()
                conn.close()
                conn = sqlite3.connect(f"user_data.db")
                curs = conn.cursor()
                curs.execute(f'''UPDATE user_data SET points = points + ? WHERE telegram_id = ?''', (card.point_values[card_get[2]], message.chat.id))
                conn.commit()
                curs.execute(f'''SELECT points FROM user_data WHERE telegram_id = ?''',(message.chat.id,))
                points_raw = curs.fetchall()
                points = [result[0] for result in points_raw]
                conn.close()
                await message.answer_photo(
                    photo=card_photo, 
                    caption=f"🃏Вам выпала карта: \n{card_get[0]} \n🔆Редкость: {card_get[2]} \n🌠DarkPoints: {points[0]}(+{card.point_values[card_get[2]]})"
        )
        else:
            await message.answer("У вас нет попыток, чтобы получить карту.")
    else: await message.answer("У тебя не выбрана вселенная. Выбрать ее можно при помощи команды /verse")
    await state.set_state(DrawCard.waiting)
    await state.update_data(last_used_time=current_time)

    # Wait for 3 seconds
    await asyncio.sleep(3)

    # Clear the state to "finish" it
    await state.set_state(None) 


    


# Обработчик команды /collection
@router.message(F.text.lower().contains("коллекция"))
async def view_collection(message: Message):
    btn_collection_basic = InlineKeyboardButton(text ="🟩Basic",callback_data="collection_basic")
    btn_collection_unusual = InlineKeyboardButton(text ="🟦Unusual",callback_data="collection_unusual")
    btn_collection_epic = InlineKeyboardButton(text ="🟪Epic",callback_data="collection_epic")
    btn_collection_legendary = InlineKeyboardButton(text ="🟨Legendary",callback_data="collection_legendary")
    btn_collection_mythic = InlineKeyboardButton(text ="🟥Mythical",callback_data="collection_mythic")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_collection_basic],[btn_collection_unusual],[btn_collection_epic],[btn_collection_legendary],[btn_collection_mythic]])
    
    
    await message.answer(text="Ваши карты:",reply_markup=keyboard)

@router.message(F.text.lower().contains("профиль"))
async def profile_check(msg: Message):
    conn = sqlite3.connect("user_data.db")
    curs = conn.cursor()
    id = msg.chat.id
    curs.execute('''SELECT nickname,gold,gems,pulls,points,coins,verse,shards FROM user_data WHERE telegram_id = ?''',(id,))
    results = curs.fetchall()
    nickname = [result[0] for result in results]
    gold = [result[1] for result in results]
    gems = [result[2] for result in results]
    pulls = [result[3] for result in results]
    points = [result[4] for result in results]
    coins = [result[5] for result in results]
    verse = [result[6] for result in results]
    shards = [result[7] for result in results]
    button_rating = InlineKeyboardButton(text="🏆Рейтинг",callback_data="pts_rating")
    button_friends = InlineKeyboardButton(text="👥Друзья",callback_data="friends_list")
    button_verse_change = InlineKeyboardButton(text = "🏮Сменить вселенную",callback_data="verse_change")
    button_duels = InlineKeyboardButton(text = "⛩Дуэли",callback_data="duels_menu")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_rating,button_friends],[button_verse_change,button_duels]])


    await msg.answer(f"Твой профиль: \n👁‍🗨Nickname: {str(nickname[0])} \n🆔ID: {id} \n<strike>💰Золото: </strike>\n💎Кристаллы: {gems[0]}\n🧧Попытки: {pulls[0]}\n🌠Всего DarkPoints: {points[0]}\n💠DarkCoins: {coins[0]}\n♦️Осколки: {shards[0]}\n🏮Вселенная: {verse[0]}",reply_markup=keyboard)

@router.message(F.text.lower().contains("магазин"))
async def shop(msg:Message):
    donate_button = InlineKeyboardButton(text="$ Донат",callback_data="shop_donate")
    darkCoins_button = InlineKeyboardButton(text="DC DarkCoins",callback_data="shop_darkcoins")
    gems_button = InlineKeyboardButton(text="Кристаллы",callback_data="shop_gems")
    shard_button = InlineKeyboardButton(text="Осколки",callback_data="shop_shards")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[gems_button],[darkCoins_button],[donate_button],[shard_button]])
    await msg.answer("Добро пожаловать в магазин! \nВыберите интересующую вас категорию:",reply_markup=keyboard)
    
@router.message(Command('friend'))
async def friend_request(msg:Message,command:CommandObject):
    friend_id = command.args
    id = msg.chat.id
    conn = sqlite3.connect("user_data.db")
    curs = conn.cursor()
    curs.execute(f'''SELECT nickname FROM user_data WHERE telegram_id = ?''',(id))
    nickname = [result[0] for result in curs.fetchall()][0]
    try:
        if friend_id !=id:
            await msg.answer("Запрос в друзья отправлен!")  
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Принять", callback_data=f"accept_{id}_{friend_id}")],
                    [InlineKeyboardButton(text="Отклонить", callback_data=f"decline_{id}_{friend_id}")]
                ]
            )
            await msg.bot.send_message(text=f"Игрок {nickname} отправил вам заявку в друзья!", chat_id=friend_id, reply_markup=keyboard)
        else:
            await msg.answer("Нельзя добавить в друзья себя самого.")

    except exceptions.TelegramBadRequest:
        await msg.answer("Некорректный ID пользователя.")

@router.callback_query()
async def handle_friend_request(call: CallbackQuery):
    
    data = call.data.split("_")
    action = data[0]
    

    if action == "accept":
        user_id = data[1]
        friend_id = data[2] # Access friend_id here
        # Handle friend acceptance logic
        await call.message.edit_text(text="Запрос был принят!")
        conn = sqlite3.connect("friends.db")
        curs = conn.cursor()
        curs.execute(f"CREATE TABLE IF NOT EXISTS friends_{user_id}(telegram_id INTEGER)")
        conn.commit()
        curs.execute(f"INSERT INTO friends_{user_id} (telegram_id) VALUES (?)",(friend_id,))
        conn.commit()
        curs.execute(f"CREATE TABLE IF NOT EXISTS friends_{friend_id}(telegram_id INTEGER)")
        conn.commit()
        curs.execute(f"INSERT INTO friends_{friend_id} (telegram_id) VALUES (?)",(user_id,))
        conn.commit()
        conn.close()
    
    elif action == "decline":
        # Handle friend decline logic
        await call.message.edit_text(text="Запрос был отклонен.")
        # ... (Do something when declined, etc.)
    elif action == "shop":
        currency = data[1]
        if currency == "gems":
            try:
                currency_bought = data[2]
                if currency_bought == "pulls":
                    
                    try:
                        amount = int(data[3])
                        conn = sqlite3.connect("user_data.db")
                        curs = conn.cursor()
                        curs.execute(f'''SELECT gems FROM user_data WHERE telegram_id = ?''',(call.message.chat.id,))
                        gems_raw = curs.fetchall()
                        gems = [result[0] for result in gems_raw][0]
                        price = int(round(250*amount*amount**-0.062,2))
                        if gems>price:
                            
                            curs.execute(f'''UPDATE user_data SET gems = gems - ? WHERE telegram_id = ?''',(price,call.message.chat.id))
                            curs.execute(f'''UPDATE user_data SET pulls = pulls + ? WHERE telegram_id = ?''',(amount,call.message.chat.id))
                            conn.commit()
                            conn.close()
                            await call.message.bot.send_message(chat_id=call.message.chat.id, text=f"Вы успешно купили {amount} попыток!")
                        else:
                            
                            
                            await call.message.bot.send_message(chat_id=call.message.chat.id, text=f"Вам не хватает {price-gems} кристаллов для покупки.")
                    except Exception as e:
                        pulls_gems_buy_10 = InlineKeyboardButton(text="10🧧", callback_data="shop_gems_pulls_10")
                        pulls_gems_buy_50 = InlineKeyboardButton(text="50🧧", callback_data="shop_gems_pulls_50")
                        pulls_gems_buy_100 = InlineKeyboardButton(text="100🧧", callback_data="shop_gems_pulls_100")
                        pulls_gems_buy_1000 = InlineKeyboardButton(text="1000🧧", callback_data="shop_gems_pulls_1000")
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[[pulls_gems_buy_10],[pulls_gems_buy_50],[pulls_gems_buy_100],[pulls_gems_buy_1000]])
                        await call.message.bot.send_message(chat_id=call.message.chat.id, text="📋Текущие цены на попытки: \n10🧧  -  <strike>2500💎</strike> 2200💎 <b>|-12%|</b> \n50🧧 - <strike>12500💎</strike> 9800💎 <b>|-22%|</b> \n100🧧 - <strike>25000💎</strike> 18800💎 <b>|-25%|</b> \n1000🧧 - <strike>250000💎</strike> 163000💎 <b>|-35%|</b> \n", reply_markup=keyboard)
            except:
                pulls_gems_button = InlineKeyboardButton(text="Попытки", callback_data="shop_gems_pulls")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[pulls_gems_button]])
                await call.message.bot.send_message(chat_id=call.message.chat.id, text="За кристаллы ты можешь купить:", reply_markup=keyboard)
        elif currency == "darkcoins":
            try:
                currency_bought = data[2]
                if currency_bought == "pulls":
                    try:
                        
                        amount = int(data[3])
                        conn = sqlite3.connect("user_data.db")
                        curs = conn.cursor()
                        curs.execute(f'''SELECT coins FROM user_data WHERE telegram_id = ?''',(call.message.chat.id,))
                        dc_raw = curs.fetchall()
                        dc = [result[0] for result in dc_raw][0]
                        price = int(round(25*amount*amount**-0.062,0))
                        if dc>price:
                            curs.execute(f'''UPDATE user_data SET coins = coins - ? WHERE telegram_id = ?''',(price,call.message.chat.id))
                            curs.execute(f'''UPDATE user_data SET pulls = pulls + ? WHERE telegram_id = ?''',(amount,call.message.chat.id))
                            conn.commit()
                            conn.close()
                            await call.message.bot.send_message(chat_id=call.message.chat.id, text=f"Вы успешно купили {amount} попыток!")
                        else:   
                            await call.message.bot.send_message(chat_id=call.message.chat.id, text=f"Вам не хватает {price-dc} кристаллов для покупки.")
                    except:
                        pulls_dc_buy_10 = InlineKeyboardButton(text="10🧧", callback_data="shop_darkcoins_pulls_10")
                        pulls_dc_buy_50 = InlineKeyboardButton(text="50🧧", callback_data="shop_darkcoins_pulls_50")
                        pulls_dc_buy_100 = InlineKeyboardButton(text="100🧧", callback_data="shop_darkcoins_pulls_100")
                        pulls_dc_buy_1000 = InlineKeyboardButton(text="1000🧧", callback_data="shop_darkcoins_pulls_1000")
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[[pulls_dc_buy_10],[pulls_dc_buy_50],[pulls_dc_buy_100],[pulls_dc_buy_1000]])
                        await call.message.bot.send_message(chat_id=call.message.chat.id, text="📋Текущие цены на попытки: \n10🧧  -  <strike>250 DC</strike> 220 DC <b>|-12%|</b> \n50🧧 - <strike>1250 DC</strike> 980 DC <b>|-22%|</b> \n100🧧 - <strike>2500 DC</strike> 1880 DC <b>|-25%|</b> \n1000🧧 - <strike>25000 DC</strike> 16300 DC <b>|-35%|</b> \n", reply_markup=keyboard)
                elif currency_bought == "gems":
                    try:
                        amount = int(data[3])
                        price = int(round((0.1*amount)*0.8,2))
                        conn = sqlite3.connect("user_data.db")
                        curs = conn.cursor()
                        curs.execute(f'''SELECT coins FROM user_data WHERE telegram_id = ?''',(call.message.chat.id,))
                        dc_raw = curs.fetchall()
                        dc = [result[0] for result in dc_raw][0]
                        if dc>price:
                            curs.execute(f'''UPDATE user_data SET coins = coins - ? WHERE telegram_id = ?''',(price,call.message.chat.id))
                            curs.execute(f'''UPDATE user_data SET gems = gems + ? WHERE telegram_id = ?''',(amount,call.message.chat.id))
                            conn.commit()
                            conn.close()
                            await call.message.bot.send_message(chat_id=call.message.chat.id, text=f"Вы успешно купили {amount} кристаллов!")
                        else:   
                            await call.message.bot.send_message(chat_id=call.message.chat.id, text=f"Вам не хватает {price-dc} DC для покупки.")
                    except Exception as e:
                        print(e)
                        gems_dc_buy_2500 = InlineKeyboardButton(text="2500💎", callback_data="shop_darkcoins_gems_2500")
                        gems_dc_buy_10000 = InlineKeyboardButton(text="10000💎", callback_data="shop_darkcoins_gems_10000")
                        gems_dc_buy_15000 = InlineKeyboardButton(text="15000💎", callback_data="shop_darkcoins_gems_15000")
                        gems_dc_buy_50000 = InlineKeyboardButton(text="50000💎", callback_data="shop_darkcoins_gems_50000")
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[[gems_dc_buy_2500],[gems_dc_buy_10000],[gems_dc_buy_15000],[gems_dc_buy_50000]])
                        await call.message.bot.send_message(chat_id=call.message.chat.id, text="📋Текущие цены на кристаллы: \n2500💎  -  <strike>250 DC</strike> 200 DC <b>|-20%|</b> \n10000💎 - <strike>1000 DC</strike> 800 DC <b>|-20%|</b> \n15000💎 - <strike>1500 DC</strike> 1200 DC <b>|-20%|</b> \n50000💎 - <strike>5000 DC</strike> 4000 DC <b>|-20%|</b> \n", reply_markup=keyboard)
            except:
                pulls_darkcoins_button = InlineKeyboardButton(text="Попытки", callback_data="shop_darkcoins_pulls")
                gems_darkcoins_button = InlineKeyboardButton(text="Кристаллы", callback_data="shop_darkcoins_gems")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[pulls_darkcoins_button], [gems_darkcoins_button]])
                await call.message.bot.send_message(chat_id=call.message.chat.id, text="За DarkCoins ты можешь купить:", reply_markup=keyboard)
        elif currency == "donate":
            try:
                currency_bought = data[2]
                if currency_bought == "pulls":
                    try:
                        amount = int(data[3])
                        price = int(round((5*amount*amount**-0.062),0))
                        await call.message.bot.send_message(chat_id=call.message.chat.id,text=f"🛍Покупка: \n{amount}🧧 \n💰Стоимость:{price}₽ \n. -. -. -. -. -. -. -. -. -. -. -. -.  \n🛒Способы оплаты: \n-------------------------------- \n❇️<b><i>РСХБ</i></b>: \n5398770083952884 \n-------------------------------- \n🌐<b>Крипта</b>: \n<i><b>TON Space</b></i> \nUQCuaTShmNsOaR71WdWwfZh6fYBkZ50x1m3rpUf1JhzfUPkz \n-------------------------------- \n🥝<i><b>QIWI</b></i>: \n89158893180 \n-------------------------------- \n \n🧾Чеки присылать сюда -> @Phoenix_Flex")
                    except:
                        pulls_donate_buy_10 = InlineKeyboardButton(text="10🧧", callback_data="shop_donate_pulls_10")
                        pulls_donate_buy_50 = InlineKeyboardButton(text="50🧧", callback_data="shop_donate_pulls_50")
                        pulls_donate_buy_100 = InlineKeyboardButton(text="100🧧", callback_data="shop_donate_pulls_100")
                        pulls_donate_buy_1000 = InlineKeyboardButton(text="1000🧧", callback_data="shop_donate_pulls_1000")
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[[pulls_donate_buy_10],[pulls_donate_buy_50],[pulls_donate_buy_100],[pulls_donate_buy_1000]])
                        await call.message.bot.send_message(chat_id=call.message.chat.id, text="📋Текущие цены на попытки: \n10🧧  -  <strike>50₽ </strike> 43₽ <b>|-12%|</b> \n50🧧 - <strike>250₽</strike> 196₽ <b>|-22%|</b> \n100🧧 - <strike>500₽ DC</strike> 376₽ <b>|-25%|</b> \n1000🧧 - <strike>5000 DC</strike> 3258₽ <b>|-35%|</b> \n", reply_markup=keyboard)
            except:
                pulls_donate_button = InlineKeyboardButton(text="Попытки", callback_data="shop_donate_pulls")
                gems_donate_button = InlineKeyboardButton(text="Кристаллы", callback_data="shop_donate_gems")
                gold_donate_button = InlineKeyboardButton(text="Золото | В разработке", callback_data="shop_donate_gold")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[pulls_donate_button], [gems_donate_button], [gold_donate_button]])
                await call.message.bot.send_message(chat_id=call.message.chat.id, text="За донат ты можешь купить:", reply_markup=keyboard)
        
        elif currency == "shards":
            try:
                currency_bought = data[2]
                if currency_bought == "pulls":
                    
                    try:
                        amount = int(data[3])
                        conn = sqlite3.connect("user_data.db")
                        curs = conn.cursor()
                        curs.execute(f'''SELECT shards FROM user_data WHERE telegram_id = ?''',(call.message.chat.id,))
                        shards_raw = curs.fetchall()
                        shards = [result[0] for result in shards_raw][0]
                        price = 25*amount
                        if shards>price:
                            print(amount)
                            curs.execute(f'''UPDATE user_data SET shards = shards - ? WHERE telegram_id = ?''',(price,call.message.chat.id))
                            curs.execute(f'''UPDATE user_data SET pulls = pulls + ? WHERE telegram_id = ?''',(amount,call.message.chat.id))
                            conn.commit()
                            conn.close()
                            await call.message.bot.send_message(chat_id=call.message.chat.id, text=f"Вы успешно купили {amount} попыток!")
                        else:
                            
                            
                            await call.message.bot.send_message(chat_id=call.message.chat.id, text=f"Вам не хватает {price-shards} осколков для покупки.")
                    except Exception as e:
                        pulls_shards_buy_1 = InlineKeyboardButton(text="10🧧", callback_data="shop_shards_pulls_1")
                        pulls_shards_buy_10 = InlineKeyboardButton(text="50🧧", callback_data="shop_shards_pulls_10")
                        pulls_shards_buy_50 = InlineKeyboardButton(text="100🧧", callback_data="shop_shards_pulls_50")
                        pulls_shards_buy_100 = InlineKeyboardButton(text="1000🧧", callback_data="shop_shards_pulls_100")
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[[pulls_shards_buy_1],[pulls_shards_buy_10],[pulls_shards_buy_50],[pulls_shards_buy_100]])
                        await call.message.bot.send_message(chat_id=call.message.chat.id, text="📋Текущие цены на попытки: \n1🧧  -  25♦️ \n10🧧 - 250♦️ \n50🧧 - 1250♦️ \n100🧧 - 2500♦️ \n", reply_markup=keyboard)
            except:
                pulls_shards_button = InlineKeyboardButton(text="Попытки", callback_data="shop_shards_pulls")
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[pulls_shards_button]])
                await call.message.bot.send_message(chat_id=call.message.chat.id, text="За осколки ты можешь купить:", reply_markup=keyboard)
    elif call.data == "friends_list":
        friends_list = "Список ваших друзей: \n"
        conn = sqlite3.connect("friends.db")
        curs = conn.cursor()
        id = call.message.chat.id
        curs.execute(f"CREATE TABLE IF NOT EXISTS friends_{id}(telegram_id INTEGER)")
        curs.execute(f'''SELECT * FROM friends_{id}''')
        raw_friends_id = curs.fetchall()
        if raw_friends_id != None:
            friends_id = [result[0] for result in raw_friends_id]
        conn.close()
        conn = sqlite3.connect("user_data.db")
        curs = conn.cursor()

        for friend_id in friends_id:
            curs.execute(f'''SELECT nickname FROM user_data WHERE telegram_id = ?''',(friend_id,))
            nickname_raw = curs.fetchall()
            nickname = [result[0] for result in nickname_raw]
            friends_list += f"{nickname[0]} \n"
        await call.message.bot.send_message(chat_id=call.message.chat.id, text=friends_list)
        conn.close()
    elif call.data == "pts_rating":
        conn = sqlite3.connect("user_data.db")
        curs = conn.cursor()
        curs.execute("SELECT nickname, points FROM user_data ORDER BY points DESC LIMIT 10")
        top_players = curs.fetchall()

    # Create a string with the nicknames and points
        player_info = "\n".join([f"{player[0]} - {player[1]} DarkPoints" for player in top_players])

    # Send message with the player info
        await call.message.bot.send_message(chat_id=call.message.chat.id, text=f"Топ 10 игроков по очкам:\n{player_info}")
    elif call.data == "verse_change":
        button_verse_tokyo_revengers = InlineKeyboardButton(text="Токийские Мстители", callback_data="verse_set_tokyo_revengers")
        button_verse_onepunchman = InlineKeyboardButton(text="Ванпанчмен", callback_data="verse_set_onepunchman")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_verse_tokyo_revengers],[button_verse_onepunchman]])
        await call.message.bot.send_message(text="Добро пожаловать в меню выбора вселенных!",reply_markup=keyboard,chat_id = call.message.chat.id)
    elif action == "verse":
        if data[1] == "set":
            if call.data == "verse_set_tokyo_revengers":
                conn = sqlite3.connect("user_data.db")
                curs = conn.cursor()
                curs.execute(f'''UPDATE user_data SET verse = 'tokyo_revengers' WHERE telegram_id = ?''',(call.message.chat.id,))
                conn.commit()
                conn.close()

            elif call.data == "verse_set_onepunchman":
                conn = sqlite3.connect("user_data.db")
                curs = conn.cursor()
                curs.execute(f'''UPDATE user_data SET verse = 'onepunchman' WHERE telegram_id = ?''',(call.message.chat.id,))
                conn.commit()
                conn.close()
        
    elif action == "collection":
        rarity = data[1]

        if rarity == "basic":
            try:
                card_name = data[2]
                conn = sqlite3.connect(f'cards.db')
                curs = conn.cursor()
                curs.execute(f'SELECT verse,photo,enhance_level FROM cards_{call.message.chat.id} WHERE card_name = ?',(card_name,))
                results_raw = curs.fetchall()
                verse = [result[0] for result in results_raw][0]
                photo = [result[1] for result in results_raw][0]
                enhance_level = [result[2] for result in results_raw][0]
                await call.bot.send_photo(chat_id=call.message.chat.id,photo=photo,caption=f'🃏{card_name}\n\nВселенная:{verse}\nУровень усиления:+{enhance_level}')
        
            except Exception as e:
                print(e)
                collection_text = get_user_cards(call.message.chat.id,"Basic")
                await call.bot.send_message(chat_id=call.message.chat.id,text=f"Коллекция ваших Basic карт:",reply_markup=collection_text)
        if rarity == "unusual":
            try:
                card_name = data[2]
                conn = sqlite3.connect(f'cards.db')
                curs = conn.cursor()
                curs.execute(f'SELECT verse,photo,enhance_level FROM cards_{call.message.chat.id} WHERE card_name = ?',(card_name,))
                results_raw = curs.fetchall()
                verse = [result[0] for result in results_raw][0]
                photo = [result[1] for result in results_raw][0]
                enhance_level = [result[2] for result in results_raw][0]
                await call.bot.send_photo(chat_id=call.message.chat.id,photo=photo,caption=f'🃏{card_name}\n\nВселенная:{verse}\nУровень усиления:+{enhance_level}')
        
            except Exception as e:
                print(e)
                collection_text = get_user_cards(call.message.chat.id,"Unusual")
                await call.bot.send_message(chat_id=call.message.chat.id,text=f"Коллекция ваших Unusual карт:",reply_markup=collection_text)
        if rarity == "epic":
            try:
                card_name = data[2]
                conn = sqlite3.connect(f'cards.db')
                curs = conn.cursor()
                curs.execute(f'SELECT verse,photo,enhance_level FROM cards_{call.message.chat.id} WHERE card_name = ?',(card_name,))
                results_raw = curs.fetchall()
                verse = [result[0] for result in results_raw][0]
                photo = [result[1] for result in results_raw][0]
                enhance_level = [result[2] for result in results_raw][0]
                await call.bot.send_photo(chat_id=call.message.chat.id,photo=photo,caption=f'🃏{card_name}\n\nВселенная:{verse}\nУровень усиления:+{enhance_level}')
        
            except Exception as e:
                print(e)
                collection_text = get_user_cards(call.message.chat.id,"Epic")
                await call.bot.send_message(chat_id=call.message.chat.id,text=f"Коллекция ваших Epic карт:",reply_markup=collection_text)
        if rarity == "legendary":
            try:
                card_name = data[2]
                conn = sqlite3.connect(f'cards.db')
                curs = conn.cursor()
                curs.execute(f'SELECT verse,photo,enhance_level FROM cards_{call.message.chat.id} WHERE card_name = ?',(card_name,))
                results_raw = curs.fetchall()
                verse = [result[0] for result in results_raw][0]
                photo = [result[1] for result in results_raw][0]
                enhance_level = [result[2] for result in results_raw][0]
                await call.bot.send_photo(chat_id=call.message.chat.id,photo=photo,caption=f'🃏{card_name}\n\nВселенная:{verse}\nУровень усиления:+{enhance_level}')
        
            except Exception as e:
                print(e)
                collection_text = get_user_cards(call.message.chat.id,"Legendary")
                await call.bot.send_message(chat_id=call.message.chat.id,text=f"Коллекция ваших Legendary карт:",reply_markup=collection_text)
        if rarity == "mythic":
            try:
                card_name = data[2]
                conn = sqlite3.connect(f'cards.db')
                curs = conn.cursor()
                curs.execute(f'SELECT verse,photo,enhance_level FROM cards_{call.message.chat.id} WHERE card_name = ?',(card_name,))
                results_raw = curs.fetchall()
                verse = [result[0] for result in results_raw][0]
                photo = [result[1] for result in results_raw][0]
                enhance_level = [result[2] for result in results_raw][0]
                await call.bot.send_photo(chat_id=call.message.chat.id,photo=photo,caption=f'🃏{card_name}\n\nВселенная:{verse}\nУровень усиления:+{enhance_level}')
        
            except Exception as e:
                print(e)
                collection_text = get_user_cards(call.message.chat.id,"Mythic")
                await call.bot.send_message(chat_id=call.message.chat.id,text=f"Коллекция ваших Mythic карт:",reply_markup=collection_text)
        
    

    elif call.data == "duels_menu":
        await call.bot.send_message(text = "В разработке",chat_id=call.message.chat.id)



        


    await call.answer()








@router.message(Command('add_pulls'))
async def add_pulls(msg:Message,command:CommandObject):
    if msg.chat.id == 804897951 or msg.chat.id == 1237019598:
        info = command.args
        id = info.split(' ')[0]
        pulls = info.split(' ')[1]
        conn = sqlite3.connect("user_data.db")
        curs = conn.cursor()
        try:
            curs.execute(f'''UPDATE user_data SET pulls = pulls + ? WHERE telegram_id = ?''',(pulls,id))
            conn.commit()
            conn.close()
            await msg.reply("Начисление было успешно проведено!")
            await msg.bot.send_message(text=f"Вам было начислено {pulls} попыток!", chat_id=id, reply_markup=keyboard)
        except:
            await msg.reply("Некорректный ID.")
        #print(id,pulls)

@router.message(Command('add_gems'))
async def add_gems(msg:Message,command:CommandObject):
    if msg.chat.id == 804897951 or msg.chat.id == 1237019598:
        info = command.args
        id = info.split(' ')[0]
        gems = info.split(' ')[1]
        conn = sqlite3.connect("user_data.db")
        curs = conn.cursor()
        try:
            curs.execute(f'''UPDATE user_data SET gems = gems + ? WHERE telegram_id = ?''',(gems,id))
            conn.commit()
            conn.close()
            await msg.reply("Начисление было успешно проведено!")
            await msg.bot.send_message(text=f"Вам было начислено {gems} кристаллов!", chat_id=id, reply_markup=keyboard)
        except:
            await msg.reply("Некорректный ID.")
        #print(id,pulls)

@router.message(Command('add_gold'))
async def add_pulls(msg:Message,command:CommandObject):
    if msg.chat.id == 804897951 or msg.chat.id == 1237019598:
        info = command.args
        id = info.split(' ')[0]
        gold = info.split(' ')[1]
        conn = sqlite3.connect("user_data.db")
        curs = conn.cursor()
        try:
            curs.execute(f'''UPDATE user_data SET gold = gold + ? WHERE telegram_id = ?''',(gold,id))
            conn.commit()
            conn.close()
            await msg.reply("Начисление было успешно проведено!")
            await msg.bot.send_message(text=f"Вам было начислено {gold} золота!", chat_id=id, reply_markup=keyboard)
        except:
            await msg.reply("Некорректный ID.")
        #print(id,pulls)



@router.message(Command('promo'))
async def redeem_promo(msg:Message,command:CommandObject):
    promo = command.args
    conn_promo = sqlite3.connect("promo.db")
    curs_promo = conn_promo.cursor()
    curs_promo.execute(f'''SELECT activation_times,pulls_given,gems_given,gold_given,dc_given from promos WHERE promo_name = ?''',(promo,))
    promo_info = curs_promo.fetchall()
    if promo_info != []:
        promo_info = [result for result in promo_info][0]
        activation_times = promo_info[0]
        pulls_given = promo_info[1]
        gems_given = promo_info[2]
        gold_given = promo_info[3]
        dc_given = promo_info[4]
        conn =sqlite3.connect("user_data.db")
        curs = conn.cursor()
        curs.execute(f'''SELECT used_promos FROM user_data WHERE telegram_id=?''',(msg.chat.id,))
        
        used_promos_raw =curs.fetchall()
        used_promos = [result[0] for result in used_promos_raw][0]
        conn.close()

        if activation_times >0:
            if used_promos == None or used_promos !=None and promo not in used_promos.split(','):
                if used_promos == None:
                    used_promos = f'{promo},'
                else:
                    used_promos += f'{promo},'
                curs_promo.execute(f'''UPDATE promos SET activation_times = activation_times - 1 WHERE promo_name= ?''',(promo,))
                conn_promo.commit()
                conn_promo.close()
                conn =sqlite3.connect("user_data.db")
                curs = conn.cursor()
                text = f"🎐<b>Промокод успешно активирован!</b>\n🎁Вот твои награды:\n"
                curs.execute(f'''UPDATE user_data SET used_promos = ? WHERE telegram_id = ?''',(used_promos,msg.chat.id))
                if pulls_given != None:
                    curs.execute(f'''UPDATE user_data SET pulls = pulls + ? WHERE telegram_id = ?''',(pulls_given,msg.chat.id))
                    text += f"+{pulls_given} попыток🧧\n"
                if gems_given!= None:
                    curs.execute(f'''UPDATE user_data SET gems = gems + ? WHERE telegram_id = ?''',(gems_given,msg.chat.id))
                    text += f"+{gems_given} кристаллов💎\n"
                if gold_given != None:
                    curs.execute(f'''UPDATE user_data SET gold = gold + ? WHERE telegram_id = ?''',(gold_given,msg.chat.id))
                if dc_given != None:
                    curs.execute(f'''UPDATE user_data SET coins =coins + ? WHERE telegram_id = ?''',(dc_given,msg.chat.id))
                    text += f"+{dc_given} DarkCoins💠\n"
                conn.commit()
                conn.close()
                await msg.answer(text)
            else:
                await msg.answer("Вы уже использовали данный промокод.")
        else:
            await msg.answer("У промокода закончились попытки активации.")
        

    else:
        await msg.answer(text="Такого промокода не существует.")
@router.message(Command('nick'))
async def nickname_choose(msg: Message,command:CommandObject):
    data = command.args
    conn = sqlite3.connect("user_data.db")
    curs = conn.cursor()
    id = msg.chat.id
    if data != None:

        curs.execute('''UPDATE user_data SET nickname = ? WHERE telegram_id = ?''',(data,id))
        conn.commit()
        conn.close()
        return msg.answer(f"Удачи тебе в крутках,{data}!")


@router.message(Command('verse'))
async def verse_choose(msg:Message):  
    button_verse_tokyo_revengers = InlineKeyboardButton(text="Токийские Мстители", callback_data="verse_set_tokyo_revengers")
    button_verse_onepunchman = InlineKeyboardButton(text="Ванпанчмен", callback_data="verse_set_onepunchman")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_verse_tokyo_revengers],[button_verse_onepunchman]])
    await msg.answer("Добро пожаловать в меню выбора вселенных!",reply_markup=keyboard)

@router.message(Command("add_card"))
async def cmd_add_card(message: Message, state: FSMContext):
    if message.from_user.id == 1237019598 or message.from_user.id == 804897951:
        """
        Conversation's entry point.
        """
        await message.reply("Отправьте карту")
        await state.set_state(Form.photo)
    else:
        await message.reply("У вас недостаточно прав для использования команды.")


@router.message(F.photo)
async def process_photo(message: Message, state: FSMContext):
    # Check if the current state is Form.photo
    if await state.get_state() == Form.photo.state:
        # Get existing data from the state
        data = await state.get_data()

        # Update the data with the photo file ID
        data['photo'] = message.photo[0].file_id

        # Store the updated data in the state
        await state.update_data(**data)

        await message.reply("Теперь напишите название карты:")
        await state.set_state(Form.name)

@router.message(F.text,StateFilter(Form.name))
async def process_name(message: Message, state: FSMContext):
    if await state.get_state() == Form.name.state:
        """
        Process user's name.
        """
        # Get existing data from the state
        data = await state.get_data()

        # Update the data with the name
        data['name'] = message.text

        # Store the updated data in the state
        await state.update_data(**data)

        await message.reply("Напишите редкость карты")
        await state.set_state(Form.rarity)

@router.message(F.text,StateFilter(Form.rarity))
async def process_rarity(message: Message, state: FSMContext):
    
        """
        Process user's rarity.
        """
        if message.text == "Basic":
            hp = random.randint(1000,1200)
            atk = random.randint(200,300)
            defense = random.randint(100,150)
            crit_rate = random.randint(1,10)
            spd = random.randint(80,120)
        if message.text == "Unusual":
            hp = random.randint(1200,1500)
            atk = random.randint(300,400)
            defense = random.randint(150,225)
            crit_rate = random.randint(5,15)
            spd = random.randint(85,125)
        if message.text == "Epic":
            hp = random.randint(1450,1900)
            atk = random.randint(375,525)
            defense = random.randint(200,350)
            crit_rate = random.randint(10,20)
            spd = random.randint(90,130)
        if message.text == "Legendary":
            hp = random.randint(2000,2500)
            atk = random.randint(500,700)
            defense = random.randint(375,475)
            crit_rate = random.randint(15,25)
            spd = random.randint(95,135)
        if message.text == "Mythic":
            hp = random.randint(3000,4500)
            atk = random.randint(650,900)
            defense = random.randint(500,600)
            crit_rate = random.randint(20,30)
            spd = random.randint(100,140) 
        # Get existing data from the state
        data = await state.get_data()

        # Update the data with the rarity
        data['rarity'] = message.text

        conn = sqlite3.connect("verse_onepunchman.db")
        curs = conn.cursor()
        curs.execute(f"INSERT INTO onepunchman ( card_name, rarity, photo,hp,attack,defense,crit_rate,speed) VALUES (?,?,?,?,?,?,?,?)", (data["name"],data['rarity'], data["photo"],hp,atk,defense,crit_rate,spd))
        conn.commit()
        conn.close()

        
# Запуск бота
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())