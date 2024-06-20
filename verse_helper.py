import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext  # Import FSMContext from here
from aiogram.fsm.state import State, StatesGroup  # Import from aiogram.fsm.state
import asyncio
from aiogram.enums.parse_mode import ParseMode
from aiogram import Router, F
from aiogram.filters import Command, CommandObject,CommandStart
from aiogram.filters import StateFilter
import sqlite3
# Configure logging

# Bot token
API_TOKEN = '7038219557:AAE7Xbu-0Ye2cSOMjQcwCoM8uy4F4Ttr4AU'

router = Router()
async def main():
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
# Initialize bot and dispatcher

class Form(StatesGroup):
    photo = State()
    name = State()
    rarity = State()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Conversation's entry point.
    """
    await message.reply("Отправьте фотографию")
    await state.set_state(Form.photo)

@router.message(F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    # Check if the current state is Form.photo
    if await state.get_state() == Form.photo.state:
        # Get existing data from the state
        data = await state.get_data()

        # Update the data with the photo file ID
        data['photo'] = message.photo[0].file_id

        # Store the updated data in the state
        await state.update_data(**data)

        await message.reply("Теперь напишите имя")
        await state.set_state(Form.name)

@router.message(F.text,StateFilter(Form.name))
async def process_name(message: types.Message, state: FSMContext):
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

        await message.reply("Напишите редкость")
        await state.set_state(Form.rarity)

@router.message(F.text,StateFilter(Form.rarity))
async def process_rarity(message: types.Message, state: FSMContext):
    
        """
        Process user's rarity.
        """
        # Get existing data from the state
        data = await state.get_data()

        # Update the data with the rarity
        data['rarity'] = message.text

        conn = sqlite3.connect("verse_test.db")
        curs = conn.cursor()
        curs.execute(f"INSERT INTO test ( card_name, rarity, photo) VALUES (?,?, ?)", (data["name"],data['rarity'], data["photo"]))
        conn.commit()
        conn.close()


        # Store the updated data in the state
        await state.update_data(**data)

        await message.answer(text=f"Фото: {data['photo']}\nИмя: {data['name']}\nРедкость: {data['rarity']}")
        await message.answer_photo(
            photo="AgACAgIAAxkBAAILjmZbUqjDKLBDjM45th52h742vvCLAAJv3zEb1-jhSun8qyaOF43JAQADAgADcwADNQQ")
        await state.set_state(None)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())