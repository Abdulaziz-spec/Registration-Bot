from telebot.types import ReplyKeyboardMarkup, KeyboardButton
# ReplyKeyboardMarkup - Это класс для создания области под кнопки
# KeyboardButton - Это класс для создания кнопки


def menu_buttons():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)  # Создали область под кнопки
    btn1 = KeyboardButton(text='Регистрация')  # Создали Кнопку
    btn2 = KeyboardButton(text='Авторизация☀')  # Создали Кнопку
    btn3 = KeyboardButton(text='Генерация QR-Code')  # Создали Кнопку
    markup.add(btn1, btn2, btn3)
    return markup