from aiogram.filters.command import Command
from aiogram import types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import URLInputFile

from app.routers import router
from app.db import update_quiz_index
from app.db import show_leaderboard
from app.callbacks import get_question
from app.config import IMAGE_URL

async def new_quiz(message: types.Message):
    user_id = message.from_user.id
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)
    await get_question(message, user_id)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    start_image = URLInputFile(IMAGE_URL)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Start quiz!"))
    await message.answer_photo(
        photo=start_image,
        caption="🌈🌈🌈 Welcome to quiz! 🌈🌈🌈\nI am your bot, Tianna.\n\nPress the button below to start!",
                         reply_markup=builder.as_markup(resize_keyboard=True)
                         )


@router.message(F.text=="Start quiz!")
@router.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    remove_keyboard = types.ReplyKeyboardRemove()
    await message.answer("⏩ Let's start quiz!", 
                         reply_markup=remove_keyboard)
    await new_quiz(message)

@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: types.Message):
    await show_leaderboard(message)
