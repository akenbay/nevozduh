import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import FSInputFile, URLInputFile

from dotenv import load_dotenv
from database import Database

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Initialize games with levels and addresses
Database.initialize_games()

# States
class RegistrationStates(StatesGroup):
    entering_name = State()
    entering_phone = State()
    selecting_level = State()
    selecting_date = State()
    selecting_game= State()
    payment = State()

# Keyboards
def get_dates_keyboard():
    dates = Database.get_available_dates()
    builder = ReplyKeyboardBuilder()
    for date in dates:
        builder.button(text=date)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_levels_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Beginner")
    builder.button(text="Intermediate")
    builder.button(text="Professional")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Start command
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer(
        "⚽ Welcome to Football Game Booking!\n\n"
        "Please register to join games.\n"
        "Enter your full name:"
    )
    await state.set_state(RegistrationStates.entering_name)

# Registration flow
@dp.message(RegistrationStates.entering_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Great! Now please enter your phone number:")
    await state.set_state(RegistrationStates.entering_phone)

@dp.message(RegistrationStates.entering_phone) 
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer(
        "Select your skill level:",
        reply_markup=get_levels_keyboard()
    )
    await state.set_state(RegistrationStates.selecting_level)

@dp.message(
    RegistrationStates.selecting_level,
    F.text.in_(["Beginner", "Intermediate", "Professional"])
)
async def process_level(message: types.Message, state: FSMContext):
    await state.update_data(level=message.text.lower())
    await message.answer(
        "Now choose a date for your game:",
        reply_markup=get_dates_keyboard()
    )
    await state.set_state(RegistrationStates.selecting_date)

@dp.message(RegistrationStates.selecting_date)
async def process_date(message: types.Message, state: FSMContext):
    date = message.text
    if date not in Database.get_available_dates():
        await message.answer("Please select a valid date from the keyboard.")
        return
    
    await state.update_data(selected_date=date)
    await state.set_state(RegistrationStates.selecting_game)

@dp.message(RegistrationStates.selecting_game)
async def process_game(message: types.Message, state: FSMContext):
    data = await state.get_data()
    date = data["selected_date"]
    
    # Get games matching both date and level
    games = [g for g in Database.get_games_by_date(date)]
    
    if not games:
        await message.answer("No level games available for this date.")
        return
    
    # Save user profile
    Database.create_user(
        message.from_user.id,
        data["name"],
        data["phone"],
        data["level"]
    )
    
    # Show each matching game
    for game in games:
        players = [Database.get_user(p) for p in game["players"]]
        player_names = [p["name"] for p in players if p]
        
        caption = (
            f"⚽ {game['field']}\n"
            f"📅 {game['date']} {game['time']}\n"
            f"📍 {game['address']}\n"
            f"🏆 Level: {game['level'].capitalize()}\n"
            f"💵 Price: {game['price']} RUB\n"
            f"👥 Players: {len(game['players'])}/{game['max_players']}\n"
            f"📝 {game['description']}\n\n"
            f"Registered players:\n" + "\n".join(player_names)
        )
        
        photo = types.FSInputFile(path=f"images/{game['photo']}")
            
        builder = InlineKeyboardBuilder()
        builder.button(
            text="Register for this game", 
            callback_data=f"register_{game['id']}"
        )
        
        await message.answer_photo(
            photo,
            caption=caption,
            reply_markup=builder.as_markup()
        )

# Game registration
@dp.callback_query(F.data.startswith("register_"))
async def register_game(callback: types.CallbackQuery, state: FSMContext):
    game_id = int(callback.data.split("_")[1])
    game = Database.get_game(game_id)
    user = Database.get_user(callback.from_user.id)
    
    if not game:
        await callback.answer("Game not found!")
        return
    
    if not user:
        await callback.answer("Please complete registration first!")
        return
    
    if len(game["players"]) >= game["max_players"]:
        await callback.answer("This game is already full!")
        return
    
    # Create payment
    # payment_id = Database.create_payment(game_id, callback.from_user.id)
    
    # Payment button
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Pay {game['price']} RUB", 
        callback_data=f"pay_{game_id}"
    )
    
    await callback.message.answer(
        f"Please complete payment of {game['price']} RUB to register for:\n"
        f"{game['field']} - {game['date']} {game['time']}\n"
        f"Address: {game['address']}\n"
        f"Level: {game['level'].capitalize()}",
        reply_markup=builder.as_markup()
    )
    
    await callback.answer()

# Payment simulation
@dp.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: types.CallbackQuery):
    # payment_id = callback.data.split("_")[1]
    game_id=int(callback.data.split("_")[1])
    payment_id=game_id
    
    # if Database.confirm_payment(payment_id):
    # payment = Database._read()["payments"][payment_id]
    # game = Database.get_game(payment["game_id"])
    game = Database.get_game(game_id)
    user = Database.get_user(callback.from_user.id)
    
    await callback.message.answer(
        f"✅ Payment successful!\n"
        f"You are now registered for:\n"
        f"🏟 {game['field']}\n"
        f"📅 {game['date']} {game['time']}\n"
        f"📍 {game['address']}\n"
        f"🏆 Level: {game['level'].capitalize()}\n\n"
        f"Your booking reference: {payment_id}\n"
        f"We'll see you there, {user['name']}!"
        )
    # else:
    #     await callback.message.answer("Payment failed. Please try again.")
    Database.register_player(game_id,callback.from_user.id,user)
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())