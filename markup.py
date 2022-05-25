from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

btn_bet = KeyboardButton('\U0001F680 Сделать ставку')
btn_balance = KeyboardButton('\U0001F4B0 Посмотреть баланс')
btn_active = KeyboardButton('\U0001F630 Активные ставки')
btn_bet_result = KeyboardButton('\U00002705 Результаты ставок')
btn_ratings = KeyboardButton('\U0001F3C6 Турнирная таблица')
btn_ads = KeyboardButton('\U0001F4B0 Призы от DMarket')
btn_live = KeyboardButton('\U0001F3AE Текущие матчи')
btn_results = KeyboardButton('\U0001F3C1 Итоги матчей')
btn_back = KeyboardButton('\U0001F519 В главное меню')
btn_reg = KeyboardButton('\U00002714 Регистрация')
button_list = ReplyKeyboardMarkup(resize_keyboard=True).add(btn_bet)

button_list.add(btn_balance)
button_list.add(btn_active)
button_list.add(btn_bet_result)
button_list.add(btn_ratings)
button_list.add(btn_ads)
button_list.add(btn_live)
button_list.add(btn_results)

reg_button = ReplyKeyboardMarkup(resize_keyboard=True).add(btn_reg)
back_button = ReplyKeyboardMarkup(resize_keyboard=True).add(btn_back)
