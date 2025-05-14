import os
from typing import Dict

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from dotenv import load_dotenv
from database import Database

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Command handlers
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "⚽ Welcome to Open Football Games Bot!\n\n"
        "Available commands:\n"
        "/games - View available games\n"
        "/my_games - View games you've joined\n"
        "/game_info [id] - Get info about specific game"
    )

@dp.message(Command("games"))
async def show_games(message: types.Message):
    slots = Database.get_available_slots()
    if not slots:
        await message.answer("No available games at the moment.")
        return
    
    builder = InlineKeyboardBuilder()
    for slot in slots:
        players_count = len(slot["players"])
        builder.button(
            text=f"{slot['time']} ({players_count}/{slot['max_players']})", 
            callback_data=f"join_{slot['id']}"
        )
    builder.adjust(1)
    
    await message.answer("Available games (players/max):", reply_markup=builder.as_markup())

@dp.message(Command("my_games"))
async def my_games(message: types.Message):
    data = Database.read()
    user_games = []
    
    for slot in data["time_slots"]:
        if message.from_user.id in slot["players"]:
            players_count = len(slot["players"])
            user_games.append(
                f"Game {slot['id']}: {slot['time']} "
                f"({players_count}/{slot['max_players']} players)"
            )
    
    if user_games:
        await message.answer("Games you've joined:\n\n" + "\n".join(user_games))
    else:
        await message.answer("You haven't joined any games yet.")

@dp.message(Command("game_info"))
async def game_info(message: types.Message):
    try:
        slot_id = int(message.text.split()[1])
        slot = Database.get_slot_info(slot_id)
        if not slot:
            await message.answer("Game not found.")
            return
        
        players_info = []
        data = Database.read()
        for user_id in slot["players"]:
            user = data["users"].get(str(user_id))
            players_info.append(f"- {user['name']} (ID: {user_id})")
        
        await message.answer(
            f"Game {slot['id']} Info:\n"
            f"Time: {slot['time']}\n"
            f"Players: {len(slot['players'])}/{slot['max_players']}\n\n"
            "Participants:\n" + "\n".join(players_info)
        )
    except (IndexError, ValueError):
        await message.answer("Usage: /game_info [game_id]")

# Callback handlers
@dp.callback_query(F.data.startswith("join_"))
async def join_game(callback: types.CallbackQuery):
    slot_id = int(callback.data.split("_")[1])
    slot = Database.join_slot(
        slot_id,
        callback.from_user.id,
        callback.from_user.full_name
    )
    
    if not slot:
        await callback.answer("Game not found!")
        return
    
    players_count = len(slot["players"])
    if players_count > slot["max_players"]:
        await callback.answer("Game is already full!")
        return
    
    await callback.answer(f"You joined the {slot['time']} game!")
    
    # Update the message
    builder = InlineKeyboardBuilder()
    for s in Database.get_available_slots():
        players_count = len(s["players"])
        builder.button(
            text=f"{s['time']} ({players_count}/{s['max_players']})", 
            callback_data=f"join_{s['id']}"
        )
    builder.adjust(1)
    
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())