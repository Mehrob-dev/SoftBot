# region Imported modules

import os
import asyncio
from aiogram import Bot, Dispatcher, filters, F
from aiogram.types import Message, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from db import Users, Student, Courses, StudentCourses, engine
from sqlalchemy.orm import sessionmaker
from texts import lang
from student_manager import *
from groq import Groq

# endregion

# region Initializations

load_dotenv()
my_token = os.getenv('TOKEN')
Session = sessionmaker(engine)
session = Session()
bot_commands = [
    BotCommand(command='start', description='starting bot')
]
dp = Dispatcher()
courses = []
admin_id = os.getenv('ADMINID')
groq_api = os.getenv('GROQ_API')
client = Groq(api_key=groq_api)

class Register(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()
    waiting_for_age = State()
    waiting_for_number = State()

class EditProfile(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_surname = State()
    waiting_for_new_age = State()
    waiting_for_new_number = State()

class HelpUser(StatesGroup):
    conversation_process = State()

# endregion

# region Features

@dp.message(filters.Command('start'))
async def start_bot(message: Message):
    global courses 
    courses.clear()
    c = session.query(Courses).all()
    for course in c:
        courses.append(course.name)
    
    try:
        user = Users(
           tg_id = message.from_user.id,
           username = message.from_user.username
        )
        session.add(user)
        session.commit()
    
    except Exception as e:
        print(f'Exception = {e}')
        session.rollback()
    
    user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
    print('Username =', lang[user.language]['menu'])
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{lang[user.language]['menu']} ⚙️")],
            [KeyboardButton(text=f"{lang[user.language]['language']} 🌍")]
        ]
    )

    await message.answer(lang[user.language]['welcome'], reply_markup=markup)

@dp.message(F.text.in_([f"{lang['en']['language']} 🌍", f"{lang['ru']['language']} 🌍", f"{lang['tj']['language']} 🌍"]))
async def change_language(message: Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Tajk 🇹🇯', callback_data='TAJIK')],
            [InlineKeyboardButton(text='Russia 🇷🇺', callback_data='RUSSIA')],
            [InlineKeyboardButton(text='English 🇺🇸', callback_data='ENGLISH')]
        ]
    )

    await message.answer('Choose a language !', reply_markup=markup)

@dp.callback_query(F.data == 'TAJIK')
async def tajik_language(call: CallbackQuery):
    await call.message.answer('Забони точики интихоб карда шуд')
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    user.language = 'tj'
    session.add(user)
    session.commit()

@dp.callback_query(F.data == 'RUSSIA')
async def tajik_language(call: CallbackQuery):
    await call.message.answer('Русский язык выбрана')
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    user.language = 'ru'
    session.add(user)
    session.commit()

@dp.callback_query(F.data == 'ENGLISH')
async def tajik_language(call: CallbackQuery):
    await call.message.answer('nglish language is chosen')
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    user.language = 'en'
    session.add(user)
    session.commit()

@dp.message(F.text.in_([f"{lang['en']['menu']} ⚙️", f"{lang['ru']['menu']} ⚙️", f"{lang['tj']['menu']} ⚙️"]))
async def menu(message: Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Register 📝', callback_data='REGISTER')],
            [InlineKeyboardButton(text='My profile 👤', callback_data='PROFILE')],
            [InlineKeyboardButton(text='Edit profile ✍️', callback_data='EDITPROFILE')],
            [InlineKeyboardButton(text='Courses 📚', callback_data='COURSES')],
            [InlineKeyboardButton(text='Help 🆘', callback_data='HELP')]
        ]
    )
    await message.answer('Menu ⚙️', reply_markup=markup)

@dp.callback_query(F.data == 'REGISTER')
async def register_user(call: CallbackQuery, state: FSMContext):
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    if user.student == None:
        await call.message.answer('Enter your name !')
        await state.set_state(Register.waiting_for_name)
        await state.update_data(user = user)
    
    else:
        await call.message.answer('You are already registered !')

@dp.message(Register.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    if await name_validation(message.text):
        await state.update_data(name = message.text)
        await state.set_state(Register.waiting_for_surname)
        await message.answer('Enter your surname !')

    else:
        await message.answer('Name must have at least 3 characters !')

@dp.message(Register.waiting_for_surname)
async def get_surname(message: Message, state: FSMContext):
    if await surname_validation(message.text):
        await state.update_data(surname = message.text)
        await state.set_state(Register.waiting_for_age)
        await message.answer('Enter your age !')

    else:
        await message.answer('Surname must have at least 3 characters !')

@dp.message(Register.waiting_for_age)
async def get_age(message: Message, state: FSMContext):
    if await age_validation(message.text):
        await state.update_data(age = int(message.text))
        await state.set_state(Register.waiting_for_number)
        await message.answer('Enter your phone number !')

    else:
        await message.answer('Age must be older than 6 !')

@dp.message(Register.waiting_for_number)
async def get_phone_number(message: Message, state: FSMContext):
    if await phone_validation(message.text):
        user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
        data = await state.get_data()
        student = Student(
            user_id = user.id,
            name = data['name'],
            surname = data['surname'],
            age = data['age'],
            phone_number = message.text
        )
        session.add(student)
        session.commit()
        await message.answer('You registered successfully !')
        await state.clear()
    else:
        await message.answer("Phone number must have at least 9 numbers and no characters except '+'' !")

@dp.callback_query(F.data == 'PROFILE')
async def show_user_profile(call: CallbackQuery):
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    current_course = 'Not in any courses yet !'
    if user.student.current_course != None:
        current_course = session.query(Courses).filter_by(id = user.student.current_course)

    await call.message.answer(
f"""
👤 User: {user.student.surname} {user.student.name}

📆 Age: {user.student.age}

📞 phone number: {user.student.phone_number}

📖 current_course: {current_course}
"""
)

@dp.callback_query(F.data == "EDITPROFILE")
async def edit_my_profile(call: CallbackQuery):
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    current_course = 'Not in any courses yet !'
    if user.student.current_course != None:
        current_course = session.query(Courses).filter_by(id = user.student.current_course)

    markup = InlineKeyboardMarkup(
        inline_keyboard = [ 
            [InlineKeyboardButton(text=f"👤 name: {user.student.name}", callback_data='Edit name')],
            [InlineKeyboardButton(text=f"👤 surname: {user.student.surname}", callback_data='Edit surname')],
            [InlineKeyboardButton(text=f"📆 Age: {user.student.age}", callback_data='Edit age')],
            [InlineKeyboardButton(text=f"📞 phone number: {user.student.phone_number}", callback_data='Edit phone number')]
        ]
    )

    await call.message.answer('Choose which data you want to edit !', reply_markup = markup)

@dp.callback_query(F.data == 'Edit name')
async def edit_username(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Enter new name !')
    await state.set_state(EditProfile.waiting_for_new_name)

@dp.message(EditProfile.waiting_for_new_name)
async def change_username(message: Message, state: FSMContext):
    if await name_validation(message.text):
        user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
        user.student.name = message.text
        session.add(user)
        session.commit()
        await state.clear()
        await message.answer('Name was edited successfully !')
    
    else:
        await message.answer('Invalid name input !')

@dp.callback_query(F.data == 'Edit surname')
async def edit_username(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Enter new surname !')
    await state.set_state(EditProfile.waiting_for_new_surname)

@dp.message(EditProfile.waiting_for_new_surname)
async def change_username(message: Message, state: FSMContext):
    if await surname_validation(message.text):
        user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
        user.student.surname = message.text
        session.add(user)
        session.commit()
        await state.clear()
        await message.answer('Surname was edited successfully !')
    
    else:
        await message.answer('Invalid surname input !')

@dp.callback_query(F.data == 'Edit age')
async def edit_username(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Enter new age !')
    await state.set_state(EditProfile.waiting_for_new_age)

@dp.message(EditProfile.waiting_for_new_age)
async def change_username(message: Message, state: FSMContext):
    if await age_validation(message.text):
        user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
        user.student.age = int(message.text)
        session.add(user)
        session.commit()
        await state.clear()
        await message.answer('Age was edited successfully !')
    
    else:
        await message.answer('Invalid age input !')

@dp.callback_query(F.data == 'Edit phone number')
async def edit_username(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Enter new phone number !')
    await state.set_state(EditProfile.waiting_for_new_number)

@dp.message(EditProfile.waiting_for_new_number)
async def change_username(message: Message, state: FSMContext):
    if await phone_validation(message.text):
        user = session.query(Users).filter_by(tg_id = message.from_user.id).first()
        user.student.phone_number = message.text
        session.add(user)
        session.commit()
        await state.clear()
        await message.answer('Phone number was edited successfully !')
    
    else:
        await message.answer('Invalid phone number input !')

@dp.callback_query(F.data == 'COURSES')
async def show_courses(call: CallbackQuery):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Python Programming 💻", callback_data='Python Programming')],
            [InlineKeyboardButton(text="Web Development 🌐", callback_data='Web Development')],
            [InlineKeyboardButton(text="Artificial Intelligence 🤖", callback_data='Artificial Intelligence')],
            [InlineKeyboardButton(text="Mobile App Developmen 📱", callback_data='Mobile App Development')],
            [InlineKeyboardButton(text="UI/UX Design 🎨", callback_data='UI/UX Design')],
            [InlineKeyboardButton(text="Databases & SQL 🗄️", callback_data='Databases & SQL')],
            [InlineKeyboardButton(text="Digital Marketing 📊", callback_data='Digital Marketing')]
        ]
    )

    await call.message.answer('Our courses 📚:', reply_markup=markup)

@dp.callback_query(F.data.in_(courses))
async def chose_course(call: CallbackQuery):
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    if user.student.current_course == None:
        
        await call.bot.send_message(
            chat_id=admin_id,
            text=f"""
New requeust for enrollment from {user.student.surname} {user.student.name}
Course: {call.data}
"""
        )

        await call.message.answer('Request was sent suuccessfully to administration. You will be registered as soon as your request be approved 🙂')
    
    else:
        course = session.query(Courses).filter_by(id = user.student.current_course).first()
        await call.message.answer(f'Sorry but you are already registered to course {course.name}. Finish this one to get registered to the next one !')

@dp.callback_query(F.data == 'HELP')
async def help_user(call: CallbackQuery, state: FSMContext):
    user = session.query(Users).filter_by(tg_id = call.from_user.id).first()
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Accept ✅', callback_data=f'ADMIN_ACCEPT_CONVERSATION_{call.from_user.id}')]
        ]
    )
    await call.message.answer('Request was sent, you will have conversation as soon as admin approves it 🙂')
    await call.bot.send_message(
        chat_id=admin_id,
        text=f'Conversation Request from {user.student.surname} {user.student.name}',
        reply_markup = markup
    )

@dp.callback_query(F.data.startswith('ADMIN_ACCEPT_CONVERSATION_'))
async def connect_to_admin(call: CallbackQuery, state: FSMContext):
    await state.set_state(HelpUser.conversation_process)

@dp.message(HelpUser.conversation_process)
async def conversation_admin(message: Message):
    if message.from_user.id == admin_id:
        await message.bot.send_message(
            
        )
AI_PROMPT_TEMPLATE = 'You are an assistant who gives an informatiom about programming !'
@dp.message()
async def ai_chat(message:Message):
    text = message.text

    try:
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content' : AI_PROMPT_TEMPLATE},
                {'role': 'user', 'content': text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        answer = response.choices[0].message.content
        await message.answer(text=answer)

    except:
        await message.answer('Error talking to AI')
# endregion

# region Main

async def main():
    bot = Bot(token = my_token)
    await bot.set_my_commands(commands=bot_commands)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

# endregion
