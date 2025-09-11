from aiogram import types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.routers import router
from app.db import *
from app.keyboard import generate_options_keyboard
import app.question_loader as question_loader

quiz_data = question_loader.open_questions_file('questions.json')

async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']

    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(quiz_data[current_question_index]['question'], reply_markup=kb)

@router.callback_query(F.data.in_({"right_answer", "wrong_answer"}))
async def handle_answer(callback: types.CallbackQuery):
    user_answer = None

    for row in callback.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data == callback.data:
                user_answer = button.text
                break
        if user_answer:
            break

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']
    correct_answer = quiz_data[current_question_index]['options'][correct_option]

    current_score = await get_user_score(callback.from_user.id)

    if callback.data == "right_answer":
        await callback.message.answer(f"Your choice: {user_answer}. Right! ✔️")
        current_score += 1
    else:
        await callback.message.answer(f"Your choice: {user_answer}.Wrong. ❌ Right answer: {correct_answer}")

    await update_user_score(callback.from_user.id, current_score)

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        username = callback.from_user.username or callback.from_user.first_name

        await update_leaderboard(callback.from_user.id, username, current_score)
        await show_leaderboard(callback.message)
        await reset_user_score(callback.from_user.id)

        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="Start quiz!"))

        await callback.message.answer(
            "Quiz finished! 🧐\n\nWant to try again?",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )    