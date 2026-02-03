# region Imports
import os
import asyncio
from aiogram import Bot, Dispatcher, filters, F
from aiogram.types import (
    Message, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from db import Users, Student, Courses, engine
from sqlalchemy.orm import sessionmaker
from texts import lang
from student_manager import *
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
# endregion

# region Iitializations
load_dotenv()
my_token = os.getenv('TOKEN')

Session = sessionmaker(engine)
session = Session()

bot_commands = [
    BotCommand(command='start', description='starting bot')
]

dp = Dispatcher(storage=MemoryStorage())
courses = []

def home_kb(user):
    if user.is_admin:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=lang[user.language]['admin_menu_btn'])],
                [KeyboardButton(text=f"{lang[user.language]['language']} 🌍")]
            ],
            resize_keyboard=True
        )
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{lang[user.language]['menu']} ⚙️")],
            [KeyboardButton(text=f"{lang[user.language]['language']} 🌍")]
        ],
        resize_keyboard=True
    )

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
    waiting_for_admin_approval = State()
    conversation_process = State()

class AdminPanel(StatesGroup):
    waiting_for_course_name = State()
    waiting_for_course_desc = State()
    waiting_for_new_course_name = State()
    waiting_for_username = State()

# endregion

# region User Features
@dp.message(filters.Command('start'))
async def start_bot(message: Message):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if user == None:
        try:
            user = Users(
                tg_id=message.from_user.id,
                username=message.from_user.username
            )
            session.add(user)
            session.commit()
        except Exception as e:
            print(f'Exception = {e}')
            session.rollback()

    await message.answer(lang[user.language]['welcome'], reply_markup=home_kb(user))

@dp.message(F.text.in_([lang['en']['cancel'], lang['ru']['cancel'], lang['tj']['cancel']]))
async def cancel_process(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{lang[user.language]['menu']} ⚙️")],
            [KeyboardButton(text=f"{lang[user.language]['language']} 🌍")]
        ],
        resize_keyboard=True
    )
    await state.clear()
    await message.answer(lang[user.language]['process_canceled'], reply_markup=home_kb(user))

@dp.message(F.text.in_([f"{lang['en']['language']} 🌍", f"{lang['ru']['language']} 🌍", f"{lang['tj']['language']} 🌍"]))
async def change_language(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lang[user.language]['lang_btn_tj'], callback_data='TAJIK')],
            [InlineKeyboardButton(text=lang[user.language]['lang_btn_ru'], callback_data='RUSSIA')],
            [InlineKeyboardButton(text=lang[user.language]['lang_btn_en'], callback_data='ENGLISH')]
        ]
    )
    ans = await message.answer(lang[user.language]['choose_language'], reply_markup=markup)
    await state.update_data(lang_msg_id=ans.message_id)

@dp.callback_query(F.data == 'TAJIK')
async def tajik_language(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    user.language = 'tj'
    session.add(user)
    session.commit()
    await call.message.answer(lang[user.language]['lan_chose'], reply_markup=home_kb(user))

@dp.callback_query(F.data == 'RUSSIA')
async def russia_language(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    user.language = 'ru'
    session.add(user)
    session.commit()
    await call.message.answer(lang[user.language]['lan_chose'], reply_markup=home_kb(user))

@dp.callback_query(F.data == 'ENGLISH')
async def english_language(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    user.language = 'en'
    session.add(user)
    session.commit()
    await call.message.answer(lang[user.language]['lan_chose'], reply_markup=home_kb(user))

@dp.message(F.text.in_([f"{lang['en']['menu']} ⚙️", f"{lang['ru']['menu']} ⚙️", f"{lang['tj']['menu']} ⚙️"]))
async def menu(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if user and user.is_admin:
        await open_admin_panel(message, state)
        return

    await clean_bot_messages(message=message, state=state)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lang[user.language]['btn_register'], callback_data='REGISTER')],
            [InlineKeyboardButton(text=lang[user.language]['btn_profile'], callback_data='PROFILE')],
            [InlineKeyboardButton(text=lang[user.language]['btn_edit_profile'], callback_data='EDITPROFILE')],
            [InlineKeyboardButton(text=lang[user.language]['btn_courses'], callback_data='COURSES')],
            [InlineKeyboardButton(text=lang[user.language]['btn_help'], callback_data='HELP')]
        ]
    )
    ans = await message.answer(lang[user.language]['menu_title'], reply_markup=markup)
    await state.update_data(menu_msg_id=ans.message_id)

@dp.callback_query(F.data == 'REGISTER')
async def register_user(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()

    if user and user.is_admin:
        await call.message.answer(lang[user.language]['admin_only'])
        await call.answer()
        return
    
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[user.language]['cancel'])]],
        resize_keyboard=True
    )

    if user.student is None:
        await call.message.answer(lang[user.language]['enter_name'], reply_markup=markup)
        await state.set_state(Register.waiting_for_name)
    else:
        await call.message.answer(lang[user.language]['already_registered'])
    await call.answer()

@dp.message(Register.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()

    if await name_validation(message.text):
        await state.update_data(name=message.text)
        await state.set_state(Register.waiting_for_surname)
        await message.answer(lang[user.language]['enter_surname'])
    else:
        await message.answer(lang[user.language]['name_invalid'])

@dp.message(Register.waiting_for_surname)
async def get_surname(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()

    if await surname_validation(message.text):
        await state.update_data(surname=message.text)
        await state.set_state(Register.waiting_for_age)
        await message.answer(lang[user.language]['enter_age'])
    else:
        await message.answer(lang[user.language]['surname_invalid'])

@dp.message(Register.waiting_for_age)
async def get_age(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()

    if await age_validation(message.text):
        await state.update_data(age=int(message.text))
        await state.set_state(Register.waiting_for_number)
        await message.answer(lang[user.language]['enter_phone'])
    else:
        await message.answer(lang[user.language]['age_invalid'])

@dp.message(Register.waiting_for_number)
async def get_phone_number(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()

    if await phone_validation(message.text):
        data = await state.get_data()
        student = Student(
            user_id=user.id,
            name=data['name'],
            surname=data['surname'],
            age=data['age'],
            phone_number=message.text
        )
        session.add(student)
        session.commit()

        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"{lang[user.language]['menu']} ⚙️")],
                [KeyboardButton(text=f"{lang[user.language]['language']} 🌍")]
            ],
            resize_keyboard=True
        )
        await message.answer(lang[user.language]['registered_success'], reply_markup=markup)
        await state.clear()
    else:
        await message.answer(lang[user.language]['phone_invalid'])

@dp.callback_query(F.data == 'PROFILE')
async def show_user_profile(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()

    if user and user.is_admin:
        await call.message.answer(lang[user.language]['admin_only'])
        await call.answer()
        return
    
    if user is None or user.student is None:
        await call.message.answer(lang['en']['not_registered_profile'] if user is None else lang[user.language]['not_registered_profile'])
        await call.answer()
        return

    current_course = lang[user.language]['profile_no_course']
    if user.student.current_course_id is not None:
        course = session.query(Courses).filter_by(id=user.student.current_course_id).first()
        if course:
            current_course = course.name

    full_name = f"{user.student.surname} {user.student.name}".strip()
    phone = user.student.phone_number or "—"
    age = user.student.age if user.student.age is not None else "—"

    text = f"""
<b>{lang[user.language]['profile_title']}</b>
━━━━━━━━━━━━━━━━

<b>{lang[user.language]['profile_name']}:</b> {full_name}
<b>{lang[user.language]['profile_age']}:</b> {age}

<b>{lang[user.language]['profile_phone']}:</b> <code>{phone}</code>
<b>{lang[user.language]['profile_course']}:</b> {current_course}

━━━━━━━━━━━━━━━━
<i>{lang[user.language]['profile_phone_tip']}</i>
"""
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data == "EDITPROFILE")
async def edit_my_profile(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()

    if user and user.is_admin:
        await call.message.answer(lang[user.language]['admin_only'])
        await call.answer()
        return

    if user is None or user.student is None:
        await call.message.answer(lang['en']['not_registered_edit'] if user is None else lang[user.language]['not_registered_edit'])
        await call.answer()
        return

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👤 {lang[user.language]['profile_name']}: {user.student.name}", callback_data='Edit name')],
            [InlineKeyboardButton(text=f"👤 Surname: {user.student.surname}", callback_data='Edit surname')],
            [InlineKeyboardButton(text=f"{lang[user.language]['profile_age']}: {user.student.age}", callback_data='Edit age')],
            [InlineKeyboardButton(text=f"{lang[user.language]['profile_phone']}: {user.student.phone_number}", callback_data='Edit phone number')]
        ]
    )
    markup2 = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[user.language]['cancel'])]],
        resize_keyboard=True
    )
    await call.message.answer(lang[user.language]['edit_choose'], reply_markup=markup2)
    ans = await call.message.answer(lang[user.language]['edit_profile_title'], reply_markup=markup)
    await state.update_data(edit_profile=ans.message_id)
    await call.answer()

@dp.callback_query(F.data == 'Edit name')
async def edit_username(call: CallbackQuery, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    await clean_bot_messages(message=call.message, state=state)
    await call.message.answer(lang[user.language]['edit_enter_new_name'])
    await state.set_state(EditProfile.waiting_for_new_name)
    await call.answer()

@dp.message(EditProfile.waiting_for_new_name)
async def change_username(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if await name_validation(message.text):
        user.student.name = message.text
        session.add(user)
        session.commit()
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"{lang[user.language]['menu']} ⚙️")],
                [KeyboardButton(text=f"{lang[user.language]['language']} 🌍")]
            ],
            resize_keyboard=True
        )
        await state.clear()
        await message.answer(lang[user.language]['edit_success_name'], reply_markup=markup)
    else:
        await message.answer(lang[user.language]['invalid_input'])

@dp.callback_query(F.data == 'Edit surname')
async def edit_surname(call: CallbackQuery, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    await clean_bot_messages(message=call.message, state=state)
    await call.message.answer(lang[user.language]['edit_enter_new_surname'])
    await state.set_state(EditProfile.waiting_for_new_surname)
    await call.answer()

@dp.message(EditProfile.waiting_for_new_surname)
async def change_surname(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if await surname_validation(message.text):
        user.student.surname = message.text
        session.add(user)
        session.commit()
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"{lang[user.language]['menu']} ⚙️")],
                [KeyboardButton(text=f"{lang[user.language]['language']} 🌍")]
            ],
            resize_keyboard=True
        )
        await state.clear()
        await message.answer(lang[user.language]['edit_success_surname'], reply_markup=markup)
    else:
        await message.answer(lang[user.language]['invalid_input'])

@dp.callback_query(F.data == 'Edit age')
async def edit_age(call: CallbackQuery, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    await clean_bot_messages(message=call.message, state=state)
    await call.message.answer(lang[user.language]['edit_enter_new_age'])
    await state.set_state(EditProfile.waiting_for_new_age)
    await call.answer()

@dp.message(EditProfile.waiting_for_new_age)
async def change_age(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if await age_validation(message.text):
        user.student.age = int(message.text)
        session.add(user)
        session.commit()
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"{lang[user.language]['menu']} ⚙️")],
                [KeyboardButton(text=f"{lang[user.language]['language']} 🌍")]
            ],
            resize_keyboard=True
        )
        await state.clear()
        await message.answer(lang[user.language]['edit_success_age'], reply_markup=markup)
    else:
        await message.answer(lang[user.language]['invalid_input'])

@dp.callback_query(F.data == 'Edit phone number')
async def edit_phone(call: CallbackQuery, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    await clean_bot_messages(message=call.message, state=state)
    await call.message.answer(lang[user.language]['edit_enter_new_phone'])
    await state.set_state(EditProfile.waiting_for_new_number)
    await call.answer()

@dp.message(EditProfile.waiting_for_new_number)
async def change_phone(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if await phone_validation(message.text):
        user.student.phone_number = message.text
        session.add(user)
        session.commit()
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"{lang[user.language]['menu']} ⚙️")],
                [KeyboardButton(text=f"{lang[user.language]['language']} 🌍")]
            ],
            resize_keyboard=True
        )
        await state.clear()
        await message.answer(lang[user.language]['edit_success_phone'], reply_markup=markup)
    else:
        await message.answer(lang[user.language]['invalid_input'])

@dp.callback_query(F.data == 'COURSES')
async def show_courses(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()

    if user and user.is_admin:
        await call.message.answer(lang[user.language]['admin_only'])
        await call.answer()
        return
    
    global courses
    courses.clear()
    c = session.query(Courses).all()
    for course in c:
        courses.append(course.name)

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
    msg = await call.message.answer(lang[user.language]['courses_title'], reply_markup=markup)
    await state.update_data(course_msg_id=msg.message_id)
    await call.answer()

@dp.callback_query(F.data.in_(courses))
async def chose_course(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()

    course_name = call.data
    course = session.query(Courses).filter_by(name=course_name).first()

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=lang[user.language]['back'], callback_data='COURSES'),
                InlineKeyboardButton(text=lang[user.language]['register_course'], callback_data=f'REGISTER_{course.id}')
            ]
        ]
    )
    ans = await call.message.answer(
        f"{course_name} 📖\n\n{course.description}",
        reply_markup=markup
    )
    await state.update_data(course_info=ans.message_id)
    await call.answer()

@dp.callback_query(F.data.startswith('REGISTER_'))
async def register_to_course(call: CallbackQuery, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    if user is None or user.student is None:
        await call.message.answer(lang['en']['not_registered_courses'] if user is None else lang[user.language]['not_registered_courses'])
        await call.answer()
        return

    await clean_bot_messages(message=call.message, state=state)
    course_id = int(call.data.split('REGISTER_')[1])
    user.student.current_course_id = course_id
    session.add(user)
    session.commit()
    await call.message.answer(lang[user.language]['registered_course_success'])
    await call.answer()

@dp.callback_query(F.data == 'HELP')
async def help_user(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)
    user = session.query(Users).filter_by(tg_id=call.from_user.id).first()

    if user and user.is_admin:
        await call.message.answer(lang[user.language]['admin_only'])
        await call.answer()
        return
    
    admin = session.query(Users).filter_by(is_admin=True, admin_in_conversation=False).first()
    if admin is None:
        await call.message.answer(lang[user.language]['admins_busy'])
        await call.answer()
        return

    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[user.language]['leave'])]],
        resize_keyboard=True
    )
    await state.set_state(HelpUser.waiting_for_admin_approval)

    admin_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Accept {user.student.name}' request", callback_data=f'ADMINACCEPTED_{user.tg_id}')]
        ]
    )
    await call.message.bot.send_message(
        chat_id=admin.tg_id,
        text=f"{lang[admin.language]['admin_new_request']} {user.student.name} (@{user.username})",
        reply_markup=admin_markup
    )
    await call.message.answer(lang[user.language]['help_request_sent'], reply_markup=markup)
    await call.answer()

@dp.message(HelpUser.waiting_for_admin_approval)
async def waiting_message(message: Message, state: FSMContext):
    if message.text in [lang['en']['leave'], lang['ru']['leave'], lang['tj']['leave']]:
        await leave_conversation(message, state)
        return
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    await message.answer(lang[user.language]['help_wait'])

@dp.callback_query(F.data.startswith('ADMINACCEPTED_'))
async def admin_approved(call: CallbackQuery, state: FSMContext):
    user_id = int(call.data.split('ADMINACCEPTED_')[1])

    admin = session.query(Users).filter_by(tg_id=call.from_user.id, is_admin=True).first()
    user = session.query(Users).filter_by(tg_id=user_id).first()
    if admin is None or user is None:
        await call.answer("Error", show_alert=True)
        return

    if admin.admin_in_conversation:
        await call.answer(lang[admin.language]['you_already_in_conversation'], show_alert=True)
        return

    admin.admin_in_conversation = True
    admin.connected_user_id = user.tg_id
    user.connected_admin_id = admin.tg_id
    session.commit()

    admin_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[admin.language]['leave'])]],
        resize_keyboard=True
    )

    await state.set_state(HelpUser.conversation_process)
    await call.message.answer(lang[admin.language]['connected'], reply_markup=admin_markup)

    key = StorageKey(bot_id=call.bot.id, chat_id=user_id, user_id=user_id)
    await dp.storage.set_state(key=key, state=HelpUser.conversation_process)

    user_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[user.language]['leave'])]],
        resize_keyboard=True
    )
    await call.message.bot.send_message(
        chat_id=user_id,
        text=lang[user.language]['admin_accepted_user'],
        reply_markup=user_markup
    )
    await call.answer()

@dp.message(F.text.in_([lang['en']['leave'], lang['ru']['leave'], lang['tj']['leave']]))
async def leave_conversation(message: Message, state: FSMContext):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if user is None:
        return

    markup = home_kb(user)


    if user.is_admin:
        other_id = user.connected_user_id
        await message.answer(lang[user.language]['conversation_ended'], reply_markup=markup)
        if other_id:
            other = session.query(Users).filter_by(tg_id=other_id).first()
            other_markup = home_kb(other)
            await message.bot.send_message(chat_id=other_id, text=lang[other.language]['conversation_ended'], reply_markup=other_markup)

        user.admin_in_conversation = False
        user.connected_user_id = None

        if other_id:
            other_db = session.query(Users).filter_by(tg_id=other_id).first()
            if other_db:
                other_db.connected_admin_id = None

    else:
        other_id = user.connected_admin_id
        await message.answer(lang[user.language]['conversation_ended'], reply_markup=markup)
        if other_id:
            other = session.query(Users).filter_by(tg_id=other_id).first()
            other_markup = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=f"{lang[other.language]['menu']} ⚙️")],
                    [KeyboardButton(text=f"{lang[other.language]['language']} 🌍")]
                ],
                resize_keyboard=True
            )
            await message.bot.send_message(chat_id=other_id, text=lang[other.language]['conversation_ended'], reply_markup=other_markup)

        if other_id:
            admin_db = session.query(Users).filter_by(tg_id=other_id).first()
            if admin_db:
                admin_db.admin_in_conversation = False
                admin_db.connected_user_id = None

        user.connected_admin_id = None

    session.commit()
    await state.clear()

    key1 = StorageKey(bot_id=message.bot.id, chat_id=user.tg_id, user_id=user.tg_id)
    await dp.storage.set_state(key=key1, state=None)

    if other_id:
        key2 = StorageKey(bot_id=message.bot.id, chat_id=other_id, user_id=other_id)
        await dp.storage.set_state(key=key2, state=None)

@dp.message(HelpUser.conversation_process)
async def conversation(message: Message):
    user = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if user is None:
        return

    if message.text in [lang['en']['leave'], lang['ru']['leave'], lang['tj']['leave']]:
        await leave_conversation(message, FSMContext(storage=dp.storage, key=StorageKey(bot_id=message.bot.id, chat_id=message.chat.id, user_id=message.from_user.id)))
        return

    if user.is_admin and user.admin_in_conversation and user.connected_user_id:
        await message.bot.send_message(chat_id=user.connected_user_id, text=message.text)
        return

    if (not user.is_admin) and user.connected_admin_id:
        await message.bot.send_message(chat_id=user.connected_admin_id, text=message.text)
        return

async def clean_bot_messages(message: Message, state: FSMContext):
    data = await state.get_data()
    keys = ["edit_profile", "course_msg_id", "menu_msg_id", "lang_msg_id", "course_info", "waiting_for_admin"]
    for key in keys:
        msg_id = data.get(key)
        if not msg_id:
            continue
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"delete failed for {key}={msg_id}: {e}")
        await state.update_data(**{key: None})
# endregion

# region Admin Features

@dp.message(F.text.in_([lang['en']['admin_menu_btn'], lang['ru']['admin_menu_btn'], lang['tj']['admin_menu_btn']]))
async def open_admin_panel(message: Message, state: FSMContext):
    await clean_bot_messages(message=message, state=state)

    admin = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if admin is None or not admin.is_admin:
        await message.answer(lang['en']['admin_only'] if admin is None else lang[admin.language]['admin_only'])
        return

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lang[admin.language]['admin_courses'], callback_data='ADMIN_COURSES')],
            [InlineKeyboardButton(text=lang[admin.language]['admin_users'], callback_data='ADMIN_USERS')],
            [InlineKeyboardButton(text=lang[admin.language]['admin_chat'], callback_data='ADMIN_START_CHAT')],
        ]
    )
    msg = await message.answer(lang[admin.language]['admin_panel'], reply_markup=markup)
    await state.update_data(menu_msg_id=msg.message_id)

@dp.callback_query(F.data == 'ADMIN_COURSES')
async def admin_courses(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    admin = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    if admin is None or not admin.is_admin:
        await call.message.answer(lang['en']['admin_only'] if admin is None else lang[admin.language]['admin_only'])
        return

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lang[admin.language]['admin_add_course'], callback_data='ADMIN_ADD_COURSE')],
            [InlineKeyboardButton(text=lang[admin.language]['admin_del_course'], callback_data='ADMIN_DEL_COURSE')],
            [InlineKeyboardButton(text=lang[admin.language]['admin_edit_course'], callback_data='ADMIN_EDIT_COURSE')],
        ]
    )
    msg = await call.message.answer(lang[admin.language]['admin_courses'], reply_markup=markup)
    await state.update_data(menu_msg_id=msg.message_id)
    await call.answer()

@dp.callback_query(F.data == 'ADMIN_ADD_COURSE')
async def admin_add_course(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    admin = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    if admin is None or not admin.is_admin:
        await call.message.answer(lang['en']['admin_only'] if admin is None else lang[admin.language]['admin_only'])
        return

    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[admin.language]['cancel'])]],
        resize_keyboard=True
    )
    await call.message.answer(lang[admin.language]['admin_enter_course_name'], reply_markup=markup)
    await state.set_state(AdminPanel.waiting_for_course_name)
    await call.answer()

@dp.message(AdminPanel.waiting_for_course_name)
async def admin_get_course_name(message: Message, state: FSMContext):
    admin = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if admin is None or not admin.is_admin:
        return

    if message.text in [lang['en']['cancel'], lang['ru']['cancel'], lang['tj']['cancel']]:
        await cancel_process(message, state)
        return

    await state.update_data(course_name=message.text)
    await state.set_state(AdminPanel.waiting_for_course_desc)
    await message.answer(lang[admin.language]['admin_enter_course_desc'])

@dp.message(AdminPanel.waiting_for_course_desc)
async def admin_get_course_desc(message: Message, state: FSMContext):
    admin = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if admin is None or not admin.is_admin:
        return

    if message.text in [lang['en']['cancel'], lang['ru']['cancel'], lang['tj']['cancel']]:
        await cancel_process(message, state)
        return

    data = await state.get_data()
    name = data.get('course_name')

    course = Courses(name=name, description=message.text)
    session.add(course)
    session.commit()

    await message.answer(lang[admin.language]['admin_course_added'], reply_markup=home_kb(admin))
    await state.clear()

@dp.callback_query(F.data == 'ADMIN_DEL_COURSE')
async def admin_del_course(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    admin = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    if admin is None or not admin.is_admin:
        await call.message.answer(lang['en']['admin_only'] if admin is None else lang[admin.language]['admin_only'])
        return

    c = session.query(Courses).all()
    if not c:
        await call.message.answer("No courses.")
        return

    kb = []
    for course in c:
        kb.append([InlineKeyboardButton(text=f"🗑️ {course.name}", callback_data=f"ADMIN_DEL_{course.id}")])

    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    msg = await call.message.answer(lang[admin.language]['admin_choose_course_del'], reply_markup=markup)
    await state.update_data(course_msg_id=msg.message_id)
    await call.answer()

@dp.callback_query(F.data.startswith('ADMIN_DEL_'))
async def admin_del_course_confirm(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    admin = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    if admin is None or not admin.is_admin:
        await call.message.answer(lang['en']['admin_only'] if admin is None else lang[admin.language]['admin_only'])
        return

    course_id = int(call.data.split('ADMIN_DEL_')[1])
    course = session.query(Courses).filter_by(id=course_id).first()
    if course:
        session.delete(course)
        session.commit()

    await call.message.answer(lang[admin.language]['admin_course_deleted'])
    await call.answer()

@dp.callback_query(F.data == 'ADMIN_EDIT_COURSE')
async def admin_edit_course(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    admin = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    if admin is None or not admin.is_admin:
        await call.message.answer(lang['en']['admin_only'] if admin is None else lang[admin.language]['admin_only'])
        return

    c = session.query(Courses).all()
    if not c:
        await call.message.answer("No courses.")
        return

    kb = []
    for course in c:
        kb.append([InlineKeyboardButton(text=f"✏️ {course.name}", callback_data=f"ADMIN_EDIT_{course.id}")])

    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    msg = await call.message.answer(lang[admin.language]['admin_choose_course_edit'], reply_markup=markup)
    await state.update_data(course_msg_id=msg.message_id)
    await call.answer()

@dp.callback_query(F.data.startswith('ADMIN_EDIT_'))
async def admin_edit_pick(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    admin = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    if admin is None or not admin.is_admin:
        await call.message.answer(lang['en']['admin_only'] if admin is None else lang[admin.language]['admin_only'])
        return

    course_id = int(call.data.split('ADMIN_EDIT_')[1])
    await state.update_data(edit_course_id=course_id)

    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[admin.language]['cancel'])]],
        resize_keyboard=True
    )
    await call.message.answer(lang[admin.language]['admin_enter_new_course_name'], reply_markup=markup)
    await state.set_state(AdminPanel.waiting_for_new_course_name)
    await call.answer()

@dp.message(AdminPanel.waiting_for_new_course_name)
async def admin_set_new_course_name(message: Message, state: FSMContext):
    admin = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if admin is None or not admin.is_admin:
        return

    if message.text in [lang['en']['cancel'], lang['ru']['cancel'], lang['tj']['cancel']]:
        await cancel_process(message, state)
        return

    data = await state.get_data()
    course_id = data.get('edit_course_id')

    course = session.query(Courses).filter_by(id=course_id).first()
    if course:
        course.name = message.text
        session.add(course)
        session.commit()

    await message.answer(lang[admin.language]['admin_course_renamed'], reply_markup=home_kb(admin))
    await state.clear()

@dp.callback_query(F.data == 'ADMIN_USERS')
async def admin_show_users(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    admin = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    if admin is None or not admin.is_admin:
        await call.message.answer(lang['en']['admin_only'] if admin is None else lang[admin.language]['admin_only'])
        return

    users = session.query(Users).all()

    text = lang[admin.language]['admin_users_list'] + "\n\n"
    for u in users[:50]:
        uname = f"@{u.username}" if u.username else "—"
        text += f"👤 {uname} | <code>{u.tg_id}</code>\n"

    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data == 'ADMIN_START_CHAT')
async def admin_start_chat(call: CallbackQuery, state: FSMContext):
    await clean_bot_messages(message=call.message, state=state)

    admin = session.query(Users).filter_by(tg_id=call.from_user.id).first()
    if admin is None or not admin.is_admin:
        await call.message.answer(lang['en']['admin_only'] if admin is None else lang[admin.language]['admin_only'])
        return

    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[admin.language]['cancel'])]],
        resize_keyboard=True
    )
    await call.message.answer(lang[admin.language]['admin_enter_username'], reply_markup=markup)
    await state.set_state(AdminPanel.waiting_for_username)
    await call.answer()

@dp.message(AdminPanel.waiting_for_username)
async def admin_connect_by_username(message: Message, state: FSMContext):
    admin = session.query(Users).filter_by(tg_id=message.from_user.id).first()
    if admin is None or not admin.is_admin:
        return

    if message.text in [lang['en']['cancel'], lang['ru']['cancel'], lang['tj']['cancel']]:
        await cancel_process(message, state)
        return

    username = message.text.replace("@", "").strip()
    user = session.query(Users).filter_by(username=username).first()
    if user is None:
        await message.answer(lang[admin.language]['admin_user_not_found'])
        return

    if admin.admin_in_conversation:
        await message.answer(lang[admin.language]['you_already_in_conversation'])
        return

    admin.admin_in_conversation = True
    admin.connected_user_id = user.tg_id
    user.connected_admin_id = admin.tg_id
    session.commit()

    admin_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[admin.language]['leave'])]],
        resize_keyboard=True
    )
    await message.answer(lang[admin.language]['admin_connected'], reply_markup=admin_markup)

    key = StorageKey(bot_id=message.bot.id, chat_id=user.tg_id, user_id=user.tg_id)
    await dp.storage.set_state(key=key, state=HelpUser.conversation_process)

    user_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang[user.language]['leave'])]],
        resize_keyboard=True
    )
    await message.bot.send_message(
        chat_id=user.tg_id,
        text=lang[user.language]['admin_accepted_user'],
        reply_markup=user_markup
    )

    await state.set_state(HelpUser.conversation_process)

# endregion

# region Main
async def main():
    bot = Bot(token=my_token)
    await bot.set_my_commands(commands=bot_commands)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
# endregion
