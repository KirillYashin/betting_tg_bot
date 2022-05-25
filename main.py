import json
import api
import os
from datetime import datetime
import threading
from github import Github
from etc import bot_token, git_token, admins
from markup import button_list, reg_button, back_button
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.markdown import hlink

'''
VARIABLES
'''

updater = False
msg_flag = False
donate_flag = False
donate_id = 0
rating = []
helper = []
upcoming_matches = []
results = []
live_matches = []
coefficients_index = -1
msg = ''

g = Github(git_token())
repo = g.get_user().get_repo('petr1k_bot')

'''
DATA UPDATER
'''


def check_sub(member):
    if member['status'] == 'member':
        return True
    else:
        return False


def get_matches():
    threading.Timer(180.0, get_matches).start()
    global updater, upcoming_matches

    try:
        with open('data/tournament.txt', 'r') as file:
            tournament_id = int(file.readline())

        with open('data/matches.json', 'w') as matches:
            matches_info = api.get_matches(tournament_id)
            for match in matches_info:
                match['time'] = str(int(match['time'].split(':')[0]) + 1) + ':' + str(int(match['time'].split(':')[1]))
                if match['team1'] and match['team2']:
                    coefficients = api.get_coefficients(match['link'])
                    if coefficients:
                        match['c1'] = coefficients['c1']
                        match['c2'] = coefficients['c2']
                    else:
                        match['c1'] = None
                        match['c2'] = None
                else:
                    match['c1'] = None
                    match['c2'] = None

            json.dump(matches_info, matches, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            _log_file.write(str(e) + ' upd matches ' + str(datetime.now().time()) + '\n')

    updater = True
    upcoming_matches = matches_info
    updater = False


def get_live_matches():
    threading.Timer(300.0, get_live_matches).start()
    global updater, live_matches
    updater = True

    try:
        with open('data/tournament.txt', 'r') as file:
            tournament_id = int(file.readline())

        live_matches = api.get_live_matches(tournament_id)

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            _log_file.write(str(e) + ' upd matches ' + str(datetime.now().time()) + '\n')

    updater = False


def get_results():
    threading.Timer(240.0, get_results).start()
    global updater, results

    try:
        with open('data/tournament.txt', 'r') as file:
            tournament_id = int(file.readline())

        with open('data/results.json', 'w') as matches_results:
            results_info = api.get_results(tournament_id)
            json.dump(results_info, matches_results, sort_keys=False,
                      indent=4, ensure_ascii=False, separators=(',', ': '))

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            _log_file.write(str(e) + ' upd res ' + str(datetime.now().time()) + '\n')

    updater = True
    results = results_info
    updater = True


def update_variables():
    threading.Timer(600.0, update_variables).start()
    global updater, upcoming_matches, results, users, rating
    updater = True

    try:
        '''_checker = os.stat('data/matches.json')
        if _checker.st_size:
            with open('data/matches.json', 'r') as _load_file:
                upcoming_matches = json.load(_load_file)

        _checker = os.stat('data/results.json')
        if _checker.st_size:
            with open('data/results.json', 'r') as _load_file:
                results = json.load(_load_file)'''
        # ЕСЛИ ПЕРЕСТАНЕТ РАБОТАТЬ РАСКОММЕНТЬ
        '''_checker = os.stat('data/balance.json')
        if _checker.st_size:
            with open('data/balance.json', 'r') as _load_file:
                users = json.load(_load_file)'''

        '''_checker = os.stat('data/top.txt')
        if _checker.st_size:
            with open('data/top.txt', 'r') as _load_file:
                rating = []
                temp = _load_file.readlines()
                for tmp in temp:
                    tmp = tmp.strip()
                    rating.append((int(tmp.split()[1]), tmp.split()[0], tmp.split()[2], bool(tmp.split()[3])))'''

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            _log_file.write(str(e) + ' upd var ' + str(datetime.now().time()) + '\n')

    updater = False


def update_bets():
    threading.Timer(120.0, update_bets).start()
    global updater, users
    updater = True

    try:
        for user_id, info in users.items():
            bets_info = info['bets']

            for bet in bets_info:
                match = bet['team1'] + ' - ' + bet['team2']
                if match in results.keys():
                    if not bet['checker']:
                        if not bet['win']:
                            with open('logs.txt', 'a') as _log_file:
                                _log_file.write('NONE BET ' + str(datetime.now().time()) + ' ' + users[user_id]['nick'] + '\n')
                            continue
                        if bet['choice'] == results[match]['winner']:
                            users[user_id]['balance'] += bet['win']
                            bet['checker'] = True
                            bet['result'] = True
                        else:
                            bet['checker'] = True
                            bet['result'] = False

        with open('data/balance.json', 'w', encoding='utf-8') as user_list:
            json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            _log_file.write(str(e) + ' upd user bets ' + str(datetime.now().time()) + '\n')

    updater = False


def update_rating():
    threading.Timer(420.0, update_rating).start()
    global updater, rating
    updater = True

    try:
        temp = []
        for user_id, info in users.items():
            cur_user = (info['balance'], info['nick'], int(user_id), info['sub'])
            temp.append(cur_user)

        temp.sort(key=lambda x: (x[0], x[1]), reverse=True)
        rating = temp

        with open('data/top.txt', 'w') as rating_file:
            counter = 1
            for top_user in temp:
                rating_file.write(top_user[1] + ' ' + str(top_user[0]) + ' '
                                  + str(top_user[2]) + ' ' + str(top_user[3]) + '\n')
                counter += 1

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            _log_file.write(str(e) + ' upd user ratings ' + str(datetime.now().time()) + '\n')

    updater = False


'''
UNICODE
'''


def code(number: int):
    temp = []
    while number > 0:
        last = number % 10
        if last == 0:
            temp.append('\U00000030\U0000FE0F\U000020E3')
        elif last == 1:
            temp.append('\U00000031\U0000FE0F\U000020E3')
        elif last == 2:
            temp.append('\U00000032\U0000FE0F\U000020E3')
        elif last == 3:
            temp.append('\U00000033\U0000FE0F\U000020E3')
        elif last == 4:
            temp.append('\U00000034\U0000FE0F\U000020E3')
        elif last == 5:
            temp.append('\U00000035\U0000FE0F\U000020E3')
        elif last == 6:
            temp.append('\U00000036\U0000FE0F\U000020E3')
        elif last == 7:
            temp.append('\U00000037\U0000FE0F\U000020E3')
        elif last == 8:
            temp.append('\U00000038\U0000FE0F\U000020E3')
        elif last == 9:
            temp.append('\U00000039\U0000FE0F\U000020E3')
        number //= 10

    res = ''
    for t in temp[::-1]:
        res += t

    return res


'''
ADS
'''


def get_ads():
    ads_link = hlink('DMarket.com', 'https://go.dmarket.com/hdh')
    ads = '\U0001F4B0 Призы:\n\n'
    link1 = hlink('★ Bowie Knife | Marble Fade (Factory New)', 'https://go.dmarket.com/dad0de')
    ads += '\U0001F947 1 место - ' + link1 + '\n\n'
    link2 = hlink('★ Bloodhound Gloves | Snakebite (Minimal Wear)', 'https://go.dmarket.com/9f0887')
    ads += '\U0001F948 2 место - ' + link2 + '\n\n'
    link3 = hlink('★ Gut Knife | Doppler (Factory New)', 'https://go.dmarket.com/f188ae')
    ads += '\U0001F949 3 место - ' + link3 + '\n\n'
    link4 = hlink('AK-47 | Bloodsport (Factory New)', 'https://go.dmarket.com/b6d153')
    ads += '\U0001F3C5 4 место - ' + link4 + '\n\n'
    link5 = hlink('AK-47 | Neon Rider (Field-Tested)', 'https://go.dmarket.com/ad2d05')
    ads += '\U0001F3C5 5 место - ' + link5 + '\n\n'
    link6 = hlink('AK-47 | Orbit Mk01 (Factory New)', 'https://go.dmarket.com/84af01')
    ads += '\U0001F3C5 6-15 места - ' + link6 + '\n\n'
    ads += 'Конец турнира - 19 декабря, после финала Blast World Final.\n\n'
    ads += 'За призовой фонд этого турнира отсылаю лучи благодарности ребятам из DMarket. ' \
           'Это торговая площадка, на которой можно обменять, купить и продать скины по отличной цене, ' \
           'вывести деньги себе на карту или другим удобным способом.\n'
    ads += (ads_link + ' — респект, уважуха и благодарность!')

    return ads


'''
INITIALIZATION
'''

token = bot_token()
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())

'''
STATES
'''


class Betting(StatesGroup):
    bet_start = State()
    team_choice = State()
    confirm = State()
    bet_done = State()


class UpdTournament(StatesGroup):
    upd_start = State()
    upd_end = State()


class UpdCoefficients(StatesGroup):
    match_choice = State()
    get_new = State()


class Notify(StatesGroup):
    text = State()
    pic = State()
    notify = State()


class Reset(StatesGroup):
    start_reset = State()
    confirm = State()


class Donate(StatesGroup):
    start_donate = State()
    enter_info = State()
    confirm = State()


class DonateCheck(StatesGroup):
    check_start = State()
    check_end = State()


'''
BUTTONS
'''


async def buttons(names):
    btn_list = ReplyKeyboardMarkup(resize_keyboard=True)
    for button in names:
        btn_list.add(button)
    return btn_list


'''
START AND RESTART COMMAND
'''


async def back(user_id: int):
    await bot.send_message(user_id, '\U00002714 Возвращаюсь назад.', reply_markup=button_list)


@dp.message_handler(commands=['start'], state=None)
async def start(message: types.Message):
    ans = 'Привет! Это бот, в котором проходит турнир прогнозистов среди подписчиков телеграм-канала Петрика. ' \
          'Всем участникам на старте выдается одинаковый банк, который к концу турнира нужно преумножить. ' \
          'Кто закончит турнир с наибольшим банком, тот и забирает приз. ' \
          'Чтобы вступить в турнир, жми "Регистрация" или пропиши команду /register'
    await message.answer(ans, reply_markup=reg_button)


@dp.message_handler(commands=['help'], state='*')
async def show_help(message: types.Message, state: FSMContext):
    ans = 'Вывожу доступные действия. Если у тебя нет меню, нажми вот на эту кнопку справа от окна ввода сообщения :)'
    await bot.send_photo(message.from_user.id, types.InputFile('data/1.png'))
    await message.answer(ans, reply_markup=button_list)
    await state.finish()


'''
REGISTRATION
'''


@dp.message_handler(commands=['register'], state=None)
async def registration_b(message: types.Message):
    global users, updater
    print(message.text, message.from_user.id)
    if updater:
        ans = '\U000023F3 Идёт обновление, подождите минуту.'
    else:
        try:
            _checker = os.stat('data/balance.json')
            if _checker.st_size:
                with open('data/balance.json', 'r', encoding='utf-8') as user_list:
                    users = json.load(user_list)
                    current_user = message.from_user.id

                nickname = str(message.from_user.id)
                if message.from_user.username:
                    nickname = message.from_user.username

                sub = check_sub(await bot.get_chat_member(chat_id='@petr1ktv', user_id=message.from_user.id))

                if str(current_user) not in users.keys():
                    users[str(current_user)] = {'balance': 1000, 'bets': [], 'confirm': None,
                                                'value': None, 'nick': nickname, 'sub': sub}

                    ans = '\U00002714 Удачной игры!\n' \
                          '\U0001F4B0 Баланс - 1000'
                else:
                    ans = '\U00002714 Вы уже зарегистрированы в игре'
            else:
                nickname = str(message.from_user.id)
                if message.from_user.username:
                    nickname = message.from_user.username

                sub = check_sub(await bot.get_chat_member(chat_id='@petr1ktv', user_id=message.from_user.id))

                users = {str(message.from_user.id): {'balance': 1000, 'bets': [], 'confirm': None,
                                                     'value': None, 'nick': nickname, 'sub': sub}}
                ans = '\U00002714 Удачной игры!\n' \
                      '\U0001F4B0 Баланс - 1000'

            with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

        except Exception as e:
            await bot.send_message(int(admins().split()[0]), str(e) + ' reg')
            ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                  '\nНажмите /register, если еще не зарегистрированы в игре.\n'

    await message.answer(ans, reply_markup=button_list)


# @dp.message_handler(state=None)
async def registration(message: types.Message):
    global users, updater
    if message.text != '\U00002714 Регистрация':
        return
    if updater:
        ans = '\U000023F3 Идёт обновление, подождите минуту.'
    else:
        try:
            _checker = os.stat('data/balance.json')
            if _checker.st_size:
                with open('data/balance.json', 'r', encoding='utf-8') as user_list:
                    users = json.load(user_list)
                    current_user = message.from_user.id

                nickname = str(message.from_user.id)
                if message.from_user.username:
                    nickname = message.from_user.username

                sub = check_sub(await bot.get_chat_member(chat_id='@petr1ktv', user_id=message.from_user.id))

                if str(current_user) not in users.keys():
                    users[str(current_user)] = {'balance': 1000, 'bets': [], 'confirm': None,
                                                'value': None, 'nick': nickname, 'sub': sub}

                    ans = '\U00002714 Удачной игры!\n' \
                          '\U0001F4B0 Баланс - 1000'
                else:
                    ans = '\U00002714 Вы уже зарегистрированы в игре'
            else:
                nickname = str(message.from_user.id)
                if message.from_user.username:
                    nickname = message.from_user.username

                sub = check_sub(await bot.get_chat_member(chat_id='@petr1ktv', user_id=message.from_user.id))

                users = {str(message.from_user.id): {'balance': 1000, 'bets': [], 'confirm': None,
                                                     'value': None, 'nick': nickname, 'sub': sub}}
                ans = '\U00002714 Удачной игры!\n' \
                      '\U0001F4B0 Баланс - 1000'

            with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

        except Exception as e:
            await bot.send_message(int(admins().split()[0]), str(e) + ' reg')
            ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                  '\nНажмите /register, если еще не зарегистрированы в игре.\n'

    await message.answer(ans, reply_markup=button_list)


'''
ADMIN FUNCTIONS
'''


'''@dp.message_handler(state=None)
async def all_aggregator(message: types.Message):
    if str(message.from_user.id) in admins().split():
        if message.text == '/don':
            await check_donate_start(message.from_user.id)
        await message.answer('admin', reply_markup=button_list)
    else:
        await message.answer('not admin', reply_markup=button_list)'''


# @dp.message_handler(commands=['donate'], state=['*'])
async def check_donate_start(admin_id):
    if str(admin_id) in admins().split():
        ans = 'Есть новые донаты?'
        names = ['Да', 'Нет']
        b = await buttons(names)
        await bot.send_message(admin_id, ans, reply_markup=b)
        # await bot.send_message(chat_id=338152217, text='teper tut', reply_markup=ReplyKeyboardRemove())
        await DonateCheck.check_start.set()
        # await cycle_donate(admin_id)
    else:
        await bot.send_message(chat_id=338152217, text='teper tut 1', reply_markup=ReplyKeyboardRemove())


@dp.message_handler(commands=['admin'], state=None)
async def admin_mode(message: types.Message):
    if str(message.from_user.id) in admins().split():
        ans = '/sw - показать текущих победителей.\n' \
              '/nw - уведомить победителей о призе.\n' \
              '/c - обновить вручную коэффициенты.\n' \
              '/t - обновить турнир.\n' \
              '/n - сообщение пользователю.\n' \
              '/r - ресет базы данных игроков (когда турнир обновляется)\n'
        names = ['/don']
        b = await buttons(names)
        await message.answer(ans, reply_markup=b)
    else:
        message_for_user = 'Данная функция предназначена для администраторов.'
        await message.answer(message_for_user, reply_markup=button_list)


@dp.message_handler(commands=['r'], state=None)
async def reset_start(message: types.Message):
    global updater
    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)

        else:
            if str(message.from_user.id) in admins().split():
                message_for_user = 'Вы точно хотите совершить ресет базы данных?\n'
                await Reset.confirm.set()
                names = ['Да', 'Нет']
                b = await buttons(names)
                await message.answer(message_for_user, reply_markup=b)
            else:
                message_for_user = 'Данная функция предназначена для администраторов.'
                await message.answer(message_for_user, reply_markup=button_list)

    except Exception as e:
        message_for_user = 'Что-то пошло не так.'
        await bot.send_message(int(admins().split()[0]), str(e) + ' tour')

        await message.answer(message_for_user, reply_markup=button_list)


@dp.message_handler(state=Reset.confirm)
async def reset_start(message: types.Message, state: FSMContext):
    global users
    if message.text.lower() == 'да':
        for user in users.keys():
            users[user]['balance'] = 1000
            users[user]['bets'] = []
            users[user]['confirm'] = None
            users[user]['value'] = None
            '''try:
                sub = check_sub(await bot.get_chat_member(chat_id='@petr1ktv', user_id=int(user)))
                users[user]['sub'] = sub
            except Exception:
                continue'''
        with open('data/balance.json', 'w', encoding='utf-8') as user_list:
            json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

        ans = 'У всех снова по 1000 на балансе.'
        await message.answer(ans, reply_markup=button_list)
        await state.finish()

    else:
        ans = 'Ресет отменён.'
        await message.answer(ans, reply_markup=button_list)
        await state.finish()


@dp.message_handler(commands=['t'], state=None)
async def start_upd(message: types.Message):
    global updater
    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)

        else:
            if str(message.from_user.id) in admins().split():
                message_for_user = 'Введите ID турнира.\n'
                await UpdTournament.upd_start.set()
                await message.answer(message_for_user, reply_markup=ReplyKeyboardRemove())
            else:
                message_for_user = 'Данная функция предназначена для администраторов.'
                await message.answer(message_for_user, reply_markup=button_list)

    except Exception as e:
        message_for_user = 'Что-то пошло не так.'
        await bot.send_message(int(admins().split()[0]), str(e) + ' tour')

        await message.answer(message_for_user, reply_markup=button_list)


@dp.message_handler(state=UpdTournament.upd_start)
async def end_upd(message: types.Message, state: FSMContext):
    global updater
    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)
            await state.finish()

        else:
            with open('data/tournament.txt', 'w') as new_tournament:
                new_tournament.write(message.text.strip())

            message_for_user = 'Турнир обновлен.'
            await message.answer(message_for_user, reply_markup=button_list)
            await state.finish()

    except Exception as e:
        message_for_user = 'Что-то пошло не так.'
        await bot.send_message(int(admins().split()[0]), str(e) + ' tour')

        await message.answer(message_for_user, reply_markup=button_list)
        await state.finish()


@dp.message_handler(commands=['save'], state='*')
async def update_data(message: types.Message):
    try:
        if str(message.from_user.id) in admins().split():
            git_prefix = 'data/'
            git_file = git_prefix + 'saver.txt'
            contents = repo.get_contents(git_file)
            ans = 'Данные обновлены.'

            with open('data/saver.txt', 'r') as file:
                content = file.read()

            repo.update_file(contents.path, 'saving-bets', content, contents.sha, branch="master")
        else:
            ans = 'Данная функция предназначена для администраторов.'

    except Exception as e:
        ans = 'Что-то пошло не так.'
        await bot.send_message(int(admins().split()[0]), str(e) + ' save')

    await message.answer(ans, reply_markup=button_list)


@dp.message_handler(commands=['nw'], state=None)
async def notify_winners(message: types.Message):
    global updater
    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)
        elif str(message.from_user.id) in admins().split():
            counter = 1
            for winner in rating:
                if counter <= 15:
                    if check_sub(await bot.get_chat_member(chat_id='@petr1ktv', user_id=winner[2])):
                        await bot.send_message(winner[2], 'Привет! Поздравляю с попаданием в призы на турнире '
                                                          'прогнозистов от Петрика! Чтобы получить свою '
                                                          'награду, напиши в личку @petr1k.')
                        counter += 1
                        await bot.send_message(admins().split()[0], str(counter) + ' - ' + winner[1])
                else:
                    break

            message_for_user = 'Рассылка готова.'
            await message.answer(message_for_user, reply_markup=button_list)

        else:
            message_for_user = 'Данная функция предназначена для администраторов.'
            await message.answer(message_for_user, reply_markup=button_list)

    except Exception as e:
        await bot.send_message(int(admins().split()[0]), str(e) + ' win')

        message_for_user = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                           '\nНажмите /register, если еще не зарегистрированы в игре.'
        await message.answer(message_for_user, reply_markup=button_list)


@dp.message_handler(commands=['sw'], state=None)
async def show_winners(message: types.Message):
    global updater
    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)
        elif str(message.from_user.id) in admins().split():
            counter = 1
            message_for_user = ''
            for winner in rating:
                if counter <= 15:
                    sub = check_sub(await bot.get_chat_member(chat_id='@petr1ktv', user_id=winner[2]))
                    message_for_user += ('Имя: ' + winner[1] + '\nБаланс: ' + str(winner[0]) +
                                         '\nПодписан: ' + str(sub) + '\n\n\n')
                    if sub:
                        counter += 1
                else:
                    break

            await message.answer(message_for_user, reply_markup=button_list)

        else:
            message_for_user = 'Данная функция предназначена для администраторов.'
            await message.answer(message_for_user, reply_markup=button_list)

    except Exception as e:
        await bot.send_message(int(admins().split()[0]), str(e) + ' s_win')

        message_for_user = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                           '\nНажмите /register, если еще не зарегистрированы в игре.'
        await message.answer(message_for_user, reply_markup=button_list)


@dp.message_handler(commands=['c'], state=None)
async def update_coefficients(message: types.Message):
    global updater, helper

    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)
        elif str(message.from_user.id) in admins().split():
            temp = []
            message_for_user = 'Выбери с помощью кнопки матч, на который ты хочешь обновить коэффициенты. \n'
            keyboard = []

            for match in upcoming_matches:
                if not match['team1'] and not match['team2']:
                    helper.append(match)
                    continue

                helper.append(match)
                current_time = datetime.now()

                date = match['date'].split('-')[::-1]

                ans = match['team1'] + ' - ' + match['team2'] + '\n'
                ans += ('   Дата: ' + date[0] + '.' + date[1] + '.' + date[2] + '\n')
                ans += ('   Время начала (МСК): ' + match['time'] + '\n')

                match_time = datetime(int(date[2]), int(date[1]), int(date[0]), int(match['time'].split(':')[0]),
                                      int(match['time'].split(':')[1]), 0)

                difference = match_time - current_time

                ans += ('   Время до начала: ' + str(difference.days) + ' д. ' + str(difference.seconds // 3600) +
                        ' ч. ' + str((difference.seconds % 3600) // 60) + ' м.\n')
                if match['c1'] and match['c2']:
                    ans += ('   Коэффициенты на матч от нашего спонсора parimatch: ' +
                            match['c1'] + ' --- ' + match['c2'] + '\n')
                else:
                    continue
                temp.append(ans)

            if not temp:
                message_for_user = 'Нет доступных матчей\n'
                await message.answer(message_for_user, reply_markup=button_list)

            else:
                for i in range(len(temp)):
                    message_for_user += (str(i + 1) + '. ' + temp[i] + '\n')
                    keyboard.append(str(i + 1))

                b = await buttons(keyboard)
                await message.answer(message_for_user, reply_markup=b)
                await UpdCoefficients.match_choice.set()

        else:
            message_for_user = 'Данная функция предназначена для администраторов.'
            await message.answer(message_for_user, reply_markup=button_list)

    except Exception as e:
        await bot.send_message(int(admins().split()[0]), str(e) + ' coef_s')
        message_for_user = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                           '\nНажмите /register, если еще не зарегистрированы в игре.'

        await message.answer(message_for_user, reply_markup=button_list)


@dp.message_handler(state=UpdCoefficients.match_choice)
async def get_new_coefficients(message: types.Message, state: FSMContext):
    global coefficients_index

    try:
        coefficients_index = int(message.text) - 1

        message_for_user = 'Введите через пробел новые коэффициенты, ' \
                           'разделитель между целой и дробной частью - точка.\n(пример: 1.87 1.89)'
        await message.answer(message_for_user, reply_markup=ReplyKeyboardRemove())
        await UpdCoefficients.get_new.set()

    except Exception as e:
        await bot.send_message(int(admins().split()[0]), str(e) + ' coef_g')
        message_for_user = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                           '\nНажмите /register, если еще не зарегистрированы в игре.'

        await message.answer(message_for_user, reply_markup=button_list)
        await state.finish()


@dp.message_handler(state=UpdCoefficients.get_new)
async def set_new_coefficients(message: types.Message, state: FSMContext):
    global updater, upcoming_matches

    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)
            await state.finish()

        else:
            helper[coefficients_index]['c1'] = message.text.split()[0]
            helper[coefficients_index]['c2'] = message.text.split()[1]
            upcoming_matches = helper

            message_for_user = 'Коэффициент на матч обновлён.'
            await message.answer(message_for_user, reply_markup=button_list)
            await state.finish()

    except Exception as e:
        await bot.send_message(int(admins().split()[0]), str(e) + ' coef_s')
        message_for_user = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                           '\nНажмите /register, если еще не зарегистрированы в игре.'

        await message.answer(message_for_user, reply_markup=button_list)
        await state.finish()


@dp.message_handler(commands=['n'], state=None)
async def notify_users_start(message: types.Message):
    if str(message.from_user.id) in admins().split():
        ans = 'Введите сообщение, которое хотите отправить всем зарегистрировавшимся игрокам.'
        await message.answer(ans, reply_markup=ReplyKeyboardRemove())
        await Notify.text.set()
    else:
        ans = 'Эта функция предназначена для администраторов'
        await message.answer(ans, reply_markup=button_list)


@dp.message_handler(state=Notify.text)
async def notify_users(message: types.Message):
    global msg
    msg = message.text

    ans = 'Вы хотите прикрепить фото к сообщению?'
    keyboard = ['Да', 'Нет']
    b = await buttons(keyboard)
    await message.answer(ans, reply_markup=b)

    await Notify.pic.set()


@dp.message_handler(state=Notify.pic)
async def notify_users(message: types.Message, state: FSMContext):
    global msg

    if message.text.lower() == 'да':
        ans = 'Отправьте мне эту фотографию'
        await message.answer(ans, reply_markup=ReplyKeyboardRemove())
        await Notify.notify.set()
    else:
        '''link = hlink('DMarket', 'https://go.dmarket.com/fmm')
        text = msg.replace('DMarket', link)'''
        counter = 0
        keys = list(users.keys())
        for user_id in keys:
            try:
                counter += 1
                if counter % 100 == 0:
                    await bot.send_message(int(admins().split()[0]),
                                           f'\U00002714\U00002714\U00002714 РАССЫЛКУ ПОЛУЧИЛО: {counter}')
                await bot.send_message(int(user_id), msg, parse_mode='HTML', disable_notification=True)
            except Exception as e:
                await asyncio.sleep(1)
                print('|  logs  |' + str(e))
                with open('logs.txt', 'a') as _log_file:
                    _log_file.write(str(e) + ' notify wo ph ' + str(datetime.now().time()) + '\n')

            await asyncio.sleep(0.1)

        ans = f'\U00002714\U00002714\U00002714 Рассылка проведена. Получило {counter} человек.'
        await message.answer(ans, reply_markup=button_list)
        await state.finish()


@dp.message_handler(content_types=['photo'], state=Notify.notify)
async def notify_users(message: types.Message, state: FSMContext):
    global msg
    await message.photo[-1].download(destination_file='data/ad.jpg')
    # await message.animation.download(destination_file='data/gf.gif')
    counter, real_counter = 0, 0
    keys = list(users.keys())
    await bot.send_message(int(admins().split()[0]),
                           f'\U00002714\U00002714\U00002714 КЛЮЧИ СЧИТАЛ: {counter}')
    await bot.send_message(int(admins().split()[0]),
                           f'\U00002714\U00002714\U00002714 ФОТО ЗАГРУЗИЛ: {counter}')
    for user_id in keys:
        try:
            counter += 1
            if counter % 100 == 0:
                await bot.send_message(int(admins().split()[0]),
                                       f'\U00002714\U00002714\U00002714 РАССЫЛКУ ПОЛУЧИЛО: {counter}')
            with open('data/ad.jpg', 'rb') as photo:
                await bot.send_photo(chat_id=int(user_id), photo=photo, caption=msg,
                                     parse_mode='HTML', disable_notification=True)
                real_counter += 1
        except Exception as e:
            await asyncio.sleep(1)
            print('|  logs  |' + str(e))
            with open('logs.txt', 'a') as _log_file:
                _log_file.write(str(e) + ' notify wt ph ' + str(datetime.now().time()) + '\n')
        await asyncio.sleep(0.1)

    ans = f'\U00002714\U00002714\U00002714 Рассылка проведена. Получило {counter} человек. ' \
          f'Реально получило {real_counter} человек'
    await message.answer(ans, reply_markup=button_list)
    await state.finish()


'''async def cycle_donate(admin_id):
    ans = 'Есть новые донаты?'
    names = ['Да', 'Нет']
    b = await buttons(names)
    await bot.send_message(admin_id, ans, reply_markup=b)
    for user_id in second_data.keys():
        await bot.send_message(admin_id, str(user_id))
        if not second_data[user_id]['admin']:
            await donate_checker_question(user_id, admin_id)
            return
    await bot.send_message(admin_id, 'Все донаты проверены')'''


@dp.message_handler(state=DonateCheck.check_end)
async def donate_checker_question(message: types.Message, state: FSMContext):
    global users
    try:
        users[message.text]['balance'] += 1000
        with open('data/balance.json', 'w', encoding='utf-8') as user_list:
            json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))
        await state.finish()
        await bot.send_message(message.from_user.id, 'Монеты начислены')
        await bot.send_message(int(message.text), 'Монеты начислены, спасибо за донат!')
        await check_donate_start(message.from_user.id)
    except Exception:
        await state.finish()
        await bot.send_message(message.from_user.id, 'Нет такого id')
        await check_donate_start(message.from_user.id)


@dp.message_handler(state=DonateCheck.check_start)
async def donate_checker_answer(message: types.Message, state: FSMContext):
    global users, second_data
    if message.text.lower() == 'да':
        ans = 'Отправь его ID из сообщения от бота'
        await message.answer(ans, reply_markup=ReplyKeyboardRemove())
        await DonateCheck.check_end.set()
        '''users[donate_id]['balance'] += 1000
        second_data[donate_id]['donated'] = True
        second_data[donate_id]['admin'] = True
        ans = f'Пользователю с id {donate_id} +1000'
        with open('data/balance.json', 'w', encoding='utf-8') as user_list:
            json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))'''
    else:
        '''second_data[donate_id]['donated'] = False
        second_data[donate_id]['admin'] = True
        ans = f'Пользователю с id {donate_id} баланс не меняем'''
        ans = 'Донаты проверены'
        await message.answer(ans, reply_markup=button_list)
        await state.finish()

    '''with open('data/second_chance.json', 'w', encoding='utf-8') as user_list:
        json.dump(second_data, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))
    await message.answer(ans, reply_markup=ReplyKeyboardRemove())
    await state.finish()
    await cycle_donate(message.from_user.id)
'''

'''
REDIRECT
'''


@dp.message_handler(state=None)
async def handler(message: types.Message):
    if message.text == '\U0001F680 Сделать ставку':
        await start_betting_mode(message)
    if message.text == '\U0001F4B0 Посмотреть баланс':
        await show_balance(message)
    if message.text == '\U0001F630 Активные ставки':
        await show_active_bets(message)
    if message.text == '\U00002705 Результаты ставок':
        await show_bets_results(message)
    if message.text == '\U0001F3C6 Турнирная таблица':
        await show_ratings(message)
    if message.text == '\U0001F3AE Текущие матчи':
        await show_live_matches(message)
    if message.text == '\U0001F3C1 Итоги матчей':
        await show_results(message)
    if message.text == '\U00002714 Регистрация':
        await registration(message)
    if message.text == '\U0001F519 В главное меню':
        await message.answer('\U0001F519 Возвращаюсь в главное меню', reply_markup=button_list)
    if message.text == '\U0001F4B0 Призы от DMarket':
        await message.answer(get_ads(), reply_markup=button_list, parse_mode='HTML',
                             disable_web_page_preview=True)
    if message.text == '/don':
        await message.answer('ya tut', reply_markup=button_list)
        await check_donate_start(message.from_user.id)


'''
SHOW LIVE MATCHES
'''


# @dp.message_handler(state=None)
async def show_live_matches(message: types.Message):
    global updater
    if message.text != '\U0001F3AE Текущие матчи':
        return
    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)
        else:
            temp = []
            message_for_user = ''

            with open('data/tournament.txt', 'r') as file:
                tournament_id = int(file.readline())

            _live_matches = api.get_live_matches(tournament_id)
            for live_match in _live_matches:
                text = hlink('ссылка на HLTV', live_match['link'])
                ans = live_match['team1'] + ' - ' + live_match['team2'] + ' (' + text + ')\n'
                temp.append(ans)

            counter = 1
            for i in range(len(temp)):
                message_for_user += (code(counter) + ' ' + temp[i] + '\n')
                counter += 1

            if message_for_user == '':
                message_for_user = '\U0000274C Сейчас нет live-матчей.'

            await message.answer(message_for_user, reply_markup=button_list, parse_mode='HTML',
                                 disable_web_page_preview=True)

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            log_file.write(str(e) + ' live matches\n')
        message_for_user = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                           '\nНажмите /register, если еще не зарегистрированы в игре.'
        await message.answer(message_for_user, reply_markup=button_list)


'''
SHOW RESULTS
'''


# @dp.message_handler(state=None)
async def show_results(message: types.Message):
    global updater
    if message.text != '\U0001F3C1 Итоги матчей':
        return

    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)
        else:
            current_date = datetime.now().day
            temp = []
            message_for_user = ''

            for result in results.values():
                if current_date - int(result['date'].split()[1][:-2]) <= 1:
                    ans = result['team1'] + ' - ' + result['team2'] + ' '
                    ans += (str(result['team1score']) + ':' + str(result['team2score']) + ' (')
                    text = hlink('ссылка на HLTV', result['link'])
                    ans += (text + ')\n')
                    temp.append(ans)

            counter = 1
            for i in range(len(temp)):
                message_for_user += (code(counter) + ' ' + temp[i] + '\n')
                counter += 1

            if message_for_user == '':
                message_for_user = '\U0000274C На данный момент результатов матчей ещё нет.'

            await message.answer(message_for_user, reply_markup=button_list, parse_mode='HTML',
                                 disable_web_page_preview=True)

    except Exception as e:
        await bot.send_message(int(admins().split()[0]), str(e) + ' res')
        with open('logs.txt', 'a') as _log_file:
            log_file.write(str(e) + ' results\n')
        message_for_user = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                           '\nНажмите /register, если еще не зарегистрированы в игре.'
        await message.answer(message_for_user, reply_markup=button_list)


'''
BETTING
'''


# @dp.message_handler(state=None)
async def start_betting_mode(message: types.Message):
    global updater, users
    if message.text != '\U0001F680 Сделать ставку':
        return
    try:
        if updater:
            message_for_user = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(message_for_user, reply_markup=button_list)
        else:
            sub = check_sub(await bot.get_chat_member(chat_id='@petr1ktv', user_id=message.from_user.id))
            users[str(message.from_user.id)]['sub'] = sub
            users[str(message.from_user.id)]['confirm'] = None
            users[str(message.from_user.id)]['value'] = None

            temp = []
            temp_dict = []
            message_for_user = '\U00002714 Выбери с помощью кнопки матч, на который ты хочешь сделать ставку. \n\n\n'
            keyboard = []
            counter = 0

            for match in upcoming_matches:
                if not match['team1'] and not match['team2']:
                    continue

                if not match['c1'] and not match['c2']:
                    continue

                current_time = datetime.now()

                date = match['date'].split('-')[::-1]
                '''if current_time.tm_mday != date[0]:
                    continue'''
                # ans = '\U0001F4CD'
                ans = code(counter + 1) + ' '
                ans += (match['team1'] + ' - ' + match['team2'] + '\n')
                temp_dict.append({})
                temp_dict[counter]['match'] = match['team1'] + ' - ' + match['team2']

                ans += ('   Коэффициенты: ' +
                        match['c1'] + ' --- ' + match['c2'] + '\n')
                temp_dict[counter]['coef'] = match['c1'] + ' --- ' + match['c2']

                match_time = datetime(int(date[2]), int(date[1]), int(date[0]), int(match['time'].split(':')[0]),
                                      int(match['time'].split(':')[1]), 0)

                difference = match_time - current_time

                ans += ('   Время до начала: ' + str(difference.days) + ' д. ' + str(difference.seconds // 3600) +
                        ' ч. ' + str((difference.seconds % 3600) // 60) + ' м.\n')

                message_for_user += ans

                keyboard.append(str(counter + 1) + '. ' + match['team1'] + ' - ' + match['team2'])
                counter += 1
                temp.append(ans)

            if not temp:
                message_for_user = 'К сожалению, доступных матчей для ставок нет.\n'
                await message.answer(message_for_user, reply_markup=button_list)

            else:
                keyboard.append('\U0001F519 В главное меню')
                users[str(message.from_user.id)]['confirm'] = temp_dict

                b = await buttons(keyboard)
                await message.answer(message_for_user, reply_markup=b)
                await Betting.bet_start.set()

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            log_file.write(str(e) + ' bet start @' + users[str(message.from_user.id)]['nick'] + '\n')
        message_for_user = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                           '\nНажмите /register, если еще не зарегистрированы в игре.'

        await message.answer(message_for_user, reply_markup=button_list)


@dp.message_handler(state=Betting.bet_start)
async def team_choice(message: types.Message, state: FSMContext):
    global updater

    try:
        if message.text == '\U0001F519 В главное меню':
            users[str(message.from_user.id)]['confirm'] = None
            users[str(message.from_user.id)]['value'] = None

            await back(message.from_user.id)
            await state.finish()

        elif not message.text:
            users[str(message.from_user.id)]['confirm'] = None
            users[str(message.from_user.id)]['value'] = None

            ans = 'Что-то пошло не так, поставьте снова'
            await message.answer(ans, reply_markup=button_list)
            await state.finish()

        else:
            _helper = users[str(message.from_user.id)]['confirm'][int(message.text.split('. ')[0]) - 1]
            team1 = _helper['match'].split(' - ')[0]
            team2 = _helper['match'].split(' - ')[1]
            coef1 = _helper['coef'].split(' --- ')[0]
            coef2 = _helper['coef'].split(' --- ')[1]
            temp_bet = {'team1': team1,
                        'team2': team2,
                        'coef1': coef1,
                        'coef2': coef2,
                        'value': None,
                        'win': None,
                        'checker': False,
                        'result': None}

            already_bet = False
            for bet in users[str(message.from_user.id)]['bets']:
                if temp_bet['team1'] == bet['team1'] and temp_bet['team2'] == bet['team2'] and not bet['checker']:
                    already_bet = True

            if updater:
                ans = '\U000023F3 Идёт обновление, подождите минуту.'

                users[str(message.from_user.id)]['confirm'] = None
                users[str(message.from_user.id)]['value'] = None

                with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                    json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

                await message.answer(ans, reply_markup=button_list)
                await state.finish()

            elif already_bet:
                ans = 'Вы уже ставили на этот матч.'

                users[str(message.from_user.id)]['confirm'] = None
                users[str(message.from_user.id)]['value'] = None

                await message.answer(ans, reply_markup=button_list)
                await state.finish()

            else:
                ans = '\U00002753 Выберите команду'
                users[str(message.from_user.id)]['confirm'] = temp_bet

                b = await buttons([team1 + ' - ' + coef1, team2 + ' - ' + coef2, '\U0001F519 В главное меню'])
                await message.answer(ans, reply_markup=b)
                await Betting.team_choice.set()

    except Exception as e:
        users[str(message.from_user.id)]['confirm'] = None
        users[str(message.from_user.id)]['value'] = None

        with open('logs.txt', 'a') as _log_file:
            log_file.write(str(e) + ' team choice @' + users[str(message.from_user.id)]['nick'] + '\n')
        ans = 'Что-то пошло не так, нажмите /help и поставьте снова'
        await message.answer(ans, reply_markup=button_list)
        await state.finish()


@dp.message_handler(state=Betting.team_choice)
async def bet_value(message: types.Message, state: FSMContext):
    global updater
    if message.text == '\U0001F519 В главное меню':
        users[str(message.from_user.id)]['confirm'] = None
        users[str(message.from_user.id)]['value'] = None

        await back(message.from_user.id)
        await state.finish()

    else:
        if message.text.split(' - ')[0] != users[str(message.from_user.id)]['confirm']['team1'] \
                and message.text.split(' - ')[0] != users[str(message.from_user.id)]['confirm']['team2']:

            users[str(message.from_user.id)]['confirm'] = None
            users[str(message.from_user.id)]['value'] = None

            ans = 'Не знаю такой команды.'
            await message.answer(ans, reply_markup=button_list)
            await state.finish()
        else:
            try:
                if updater:
                    ans = '\U000023F3 Идёт обновление, подождите минуту.'

                    users[str(message.from_user.id)]['confirm'] = None
                    users[str(message.from_user.id)]['value'] = None

                    with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                        json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False,
                                  separators=(',', ': '))

                    await message.answer(ans, reply_markup=button_list)
                    await state.finish()

                else:
                    ans = '\U00002757 Вы собираетесь поставить на '
                    ans += (message.text.split(' - ')[0] + '\n \U0001F4B0 Баланс - ')
                    ans += (str(users[str(message.from_user.id)]['balance']) + '\n')
                    ans += '\U00002753 Введите сумму, которую хотите поставить.'

                    users[str(message.from_user.id)]['confirm']['choice'] = message.text.split(' - ')[0]

                    with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                        json.dump(users, user_list, sort_keys=False, indent=4,
                                  ensure_ascii=False, separators=(',', ': '))

                    await message.answer(ans, reply_markup=back_button)
                    await Betting.confirm.set()

            except Exception as e:
                users[str(message.from_user.id)]['confirm'] = None
                users[str(message.from_user.id)]['value'] = None

                with open('logs.txt', 'a') as _log_file:
                    log_file.write(str(e) + ' b_val @' + users[str(message.from_user.id)]['nick'] + '\n')
                ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                      '\nНажмите /register, если еще не зарегистрированы в игре.'
                await message.answer(ans, reply_markup=button_list)
                await state.finish()


@dp.message_handler(state=Betting.confirm)
async def confirm_bet(message: types.Message, state: FSMContext):
    global updater, users
    if message.text == '\U0001F519 В главное меню':
        users[str(message.from_user.id)]['confirm'] = None
        users[str(message.from_user.id)]['value'] = None

        await back(message.from_user.id)
        await state.finish()

    else:
        try:
            if updater:
                ans = '\U000023F3 Идёт обновление, подождите минуту.'

                users[str(message.from_user.id)]['confirm'] = None
                users[str(message.from_user.id)]['value'] = None

                await message.answer(ans, reply_markup=button_list)
                await state.finish()

            elif int(message.text) > users[str(message.from_user.id)]['balance']:
                ans = '\U0001F6D1 У вас недостаточно монет на счету.\nНажмите \U0001F680 Сделать ставку'

                users[str(message.from_user.id)]['confirm'] = None
                users[str(message.from_user.id)]['value'] = None

                await message.answer(ans, reply_markup=button_list)
                await state.finish()

            elif int(message.text) == 0:
                ans = '\U0001F6D1 Нельзя поставить 0.\nНажмите \U0001F680 Сделать ставку'

                users[str(message.from_user.id)]['confirm'] = None
                users[str(message.from_user.id)]['value'] = None

                await message.answer(ans, reply_markup=button_list)
                await state.finish()

            elif not message.text.isdigit():
                ans = '\U0001F6D1 Введите, пожалуйста, число.\nНажмите \U0001F680 Сделать ставку'

                users[str(message.from_user.id)]['confirm'] = None
                users[str(message.from_user.id)]['value'] = None

                await message.answer(ans, reply_markup=button_list)
                await state.finish()
            else:
                if message.text.isdigit():
                    users[str(message.from_user.id)]['value'] = int(message.text)
                    choice = users[str(message.from_user.id)]['confirm']['choice']
                    if users[str(message.from_user.id)]['confirm']['team1'] == choice:
                        potential_win = int(
                            int(message.text) * float(users[str(message.from_user.id)]['confirm']['coef1']))
                    else:
                        potential_win = int(
                            int(message.text) * float(users[str(message.from_user.id)]['confirm']['coef2']))
                    users[str(message.from_user.id)]['confirm']['win'] = potential_win

                    ans = '\U00002757 Вы собираетесь поставить '
                    ans += (message.text + ' на ' + users[str(message.from_user.id)]['confirm']['choice'] + '.\n')
                    ans += ('\U0001F4C8 Потенциальный выигрыш: ' + str(potential_win) + '.\n' +
                            '\U00002753 Подтверждаем ставку?')
                    keyboard = ['Да', 'Нет', '\U0001F519 В главное меню']
                    b = await buttons(keyboard)
                    await message.answer(ans, reply_markup=b)
                    await Betting.bet_done.set()

                else:
                    users[str(message.from_user.id)]['confirm'] = None
                    users[str(message.from_user.id)]['value'] = None

                    ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                          '\nНажмите /register, если еще не зарегистрированы в игре.'
                    await message.answer(ans, reply_markup=button_list)
                    await state.finish()

        except Exception as e:
            users[str(message.from_user.id)]['confirm'] = None
            users[str(message.from_user.id)]['value'] = None

            with open('logs.txt', 'a') as _log_file:
                log_file.write(str(e) + ' bet conf @' + users[str(message.from_user.id)]['nick'] + '\n')
            ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                  '\nНажмите /register, если еще не зарегистрированы в игре.'
            await message.answer(ans, reply_markup=button_list)
            await state.finish()


@dp.message_handler(state=Betting.bet_done)
async def bet_done(message: types.Message, state: FSMContext):
    global updater, users
    f = False
    if message.text == '\U0001F519 В главное меню':
        users[str(message.from_user.id)]['confirm'] = None
        users[str(message.from_user.id)]['value'] = None

        await back(message.from_user.id)
        await state.finish()

    else:
        try:
            if updater:
                ans = '\U000023F3 Идёт обновление, подождите минуту.'

                users[str(message.from_user.id)]['confirm'] = None
                users[str(message.from_user.id)]['value'] = None

                with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                    json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

                await message.answer(ans, reply_markup=button_list)
                await state.finish()

            elif message.text.strip().lower() == 'да':

                for match in upcoming_matches:
                    if users[str(message.from_user.id)]['confirm']['team1'] == match['team1'] and \
                            users[str(message.from_user.id)]['confirm']['team2'] == match['team2']:
                        f = True

                if f:
                    if users[str(message.from_user.id)]['value']:
                        users[str(message.from_user.id)]['confirm']['value'] = users[str(message.from_user.id)]['value']
                        users[str(message.from_user.id)]['bets'].append(users[str(message.from_user.id)]['confirm'])
                        users[str(message.from_user.id)]['balance'] -= users[str(message.from_user.id)]['value']
                        users[str(message.from_user.id)]['confirm'] = None
                        users[str(message.from_user.id)]['value'] = None

                        with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                            json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

                        ans = '\U00002714 Ставка сделана!\n\U0001F440 Желаем удачи!'
                        await message.answer(ans, reply_markup=button_list)
                        await state.finish()

                    else:
                        users[str(message.from_user.id)]['confirm'] = None
                        users[str(message.from_user.id)]['value'] = None

                        with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                            json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False,
                                      separators=(',', ': '))

                        ans = 'Что-то пошло не так, сделайте ставку снова\n'
                        await message.answer(ans, reply_markup=button_list)
                        await state.finish()

                else:
                    users[str(message.from_user.id)]['confirm'] = None
                    users[str(message.from_user.id)]['value'] = None
                    ans = '\U0000274C На этот матч уже нельзя поставить'
                    await message.answer(ans, reply_markup=button_list)
                    await state.finish()

            else:
                users[str(message.from_user.id)]['confirm'] = None
                users[str(message.from_user.id)]['value'] = None

                with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                    json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

                ans = '\U0000274C Ставка отменена!'
                await message.answer(ans, reply_markup=button_list)
                await state.finish()

        except Exception as e:
            users[str(message.from_user.id)]['confirm'] = None
            users[str(message.from_user.id)]['value'] = None

            with open('data/balance.json', 'w', encoding='utf-8') as user_list:
                json.dump(users, user_list, sort_keys=False, indent=4, ensure_ascii=False, separators=(',', ': '))

            with open('logs.txt', 'a') as _log_file:
                log_file.write(str(e) + ' b_done @' + users[str(message.from_user.id)]['nick'] + '\n')
            ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
                  '\nНажмите /register, если еще не зарегистрированы в игре.'
            await message.answer(ans, reply_markup=button_list)
            await state.finish()


'''
SHOWING BETS
'''


# @dp.message_handler(state=None)
async def show_active_bets(message: types.Message):
    global updater
    if message.text != '\U0001F630 Активные ставки':
        return

    try:
        if updater:
            ans = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(ans, reply_markup=button_list)

        else:
            bets = users[str(message.from_user.id)]['bets']
            message_for_user = ''
            temp = []
            counter = 1

            for bet in bets:
                if not bet['checker']:
                    # ans = '\U0001F4CD'
                    ans = code(counter) + ' '
                    ans += (bet['team1'] + ' (' + bet['coef1'] + ') - ' + bet['team2'] + ' (' + bet['coef2'] + ')\n')
                    ans += ('\U0001F4B5 Ставка: ' + str(bet['value']) + ' на ' + bet['choice'] + '\n')
                    ans += ('\U0001F4C8 Потенциальный выигрыш: ' + str(bet['win']) + '\n\n')
                    temp.append(ans)
                    counter += 1

            for i in range(len(temp)):
                message_for_user += temp[i]

            if message_for_user == '':
                message_for_user = 'Ты еще не делал ставок. Чего ждёшь?\n'
                message_for_user += ('\U0001F4B0 Баланс: ' + str(users[str(message.from_user.id)]['balance']))
            else:
                message_for_user += ('\U0001F4B0 Баланс: ' + str(users[str(message.from_user.id)]['balance']))

            await message.answer(message_for_user, reply_markup=button_list)

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            log_file.write(str(e) + ' show active bets\n')
        ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
              '\nНажмите /register, если еще не зарегистрированы в игре.'
        await message.answer(ans, reply_markup=button_list)


# @dp.message_handler(state=None)
async def show_bets_results(message: types.Message):
    global updater, users
    if message.text != '\U00002705 Результаты ставок':
        return

    try:
        if updater:
            ans = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(ans, reply_markup=button_list)

        else:
            bets = users[str(message.from_user.id)]['bets'][::-1]
            message_for_user = '\U0001F525 Последние 10 ставок\n\n'
            temp = []
            # new_bets = []
            counter = 1

            for bet in bets:
                if counter <= 10:
                    if bet['checker']:
                        # ans = '\U0001F4CD'
                        ans = code(counter) + ' '
                        ans += (bet['team1'] + ' (' + bet['coef1'] + ') - '
                                + bet['team2'] + ' (' + bet['coef2'] + ')\n')
                        ans += ('\U0001F4B5 Ставка: ' + str(bet['value']) + ' на ' + bet['choice'] + '\n')

                        if bet['result']:
                            ans += '\U00002705 Результат: выигрыш\n'
                            ans += ('\U0001F4C8 Изменение баланса: +' + str(bet['win']) + '\n\n')
                            # ans += ('\U0001F4B0 Баланс: ' + str(users[str(message.from_user.id)]['balance']))
                        else:
                            ans += '\U0000274C Результат: проигрыш\n'
                            ans += ('\U0001F4C8 Изменение баланса: -' + str(bet['value']) + '\n\n')
                            # ans += ('\U0001F4B0 Баланс: ' + str(users[str(message.from_user.id)]['balance']))
                        temp.append(ans)
                        counter += 1
                    '''else:
                        new_bets.append(bet)'''
                else:
                    break

            for i in range(len(temp)):
                message_for_user += temp[i]

            if counter == 1:
                message_for_user = '\U0001F440 Результатов ставок нет.\n'
                message_for_user += ('\U0001F4B0 Баланс: ' +
                                     str(users[str(message.from_user.id)]['balance']) + ' монет.\n')
            else:
                # message_for_user += '\U0001F440 Результаты ставок просмотрены, очищаю список.\n'
                message_for_user += ('\U0001F4B0 Баланс: ' +
                                     str(users[str(message.from_user.id)]['balance']) + ' монет.\n')

            await message.answer(message_for_user, reply_markup=button_list)

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            log_file.write(str(e) + ' show bet results\n')
        ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
              '\nНажмите /register, если еще не зарегистрированы в игре.'
        await message.answer(ans, reply_markup=button_list)


'''
SHOW BALANCE
'''


# @dp.message_handler(state=None)
async def show_balance(message: types.Message):
    global updater
    if message.text != '\U0001F4B0 Посмотреть баланс':
        return

    try:
        if updater:
            ans = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(ans, reply_markup=button_list)

        else:
            ans = '\U0001F4B0 Ваш баланс: '
            ans += (str(users[str(message.from_user.id)]['balance']) + '\n')
            await message.answer(ans, reply_markup=button_list)

    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            log_file.write(str(e) + ' show balance\n')
        ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
              '\nНажмите /register, если еще не зарегистрированы в игре.'
        await message.answer(ans, reply_markup=button_list)


'''
SHOW RATINGS
'''


# @dp.message_handler(state=None)
async def show_ratings(message: types.Message):
    global updater
    if message.text != '\U0001F3C6 Турнирная таблица':
        return

    try:
        if updater:
            ans = '\U000023F3 Идёт обновление, подождите минуту.'
            await message.answer(ans, reply_markup=button_list)
        else:
            counter = 1
            ans = ''
            place = 0

            if message.from_user.username:
                current_user = message.from_user.username
            else:
                current_user = str(message.from_user.id)

            for top_user in rating:
                if counter <= 15:
                    if top_user[1] == current_user:
                        place = counter
                    if check_sub(await bot.get_chat_member(chat_id='@petr1ktv', user_id=top_user[2])) \
                            or top_user[2] == 47563592:
                        if counter == 1:
                            ans += '\U0001F947'
                        elif counter == 2:
                            ans += '\U0001F948'
                        elif counter == 3:
                            ans += '\U0001F949'
                        elif counter == 10:
                            ans += '\U0001F51F'
                        else:
                            ans += code(counter)
                        ans += (' ' + top_user[1] +
                                ' (' + str(top_user[0]) + ')\n')
                        counter += 1
                else:
                    if top_user[1] == current_user:
                        place = counter
                    counter += 1

            if str(place) == 0:
                ans += '\nВаc еще нет в рейтинге, зарегестрируйся (/register) и играй!\n\n'
            else:
                ans += ('\nВаше место в рейтинге - ' + str(place) + '\n\n')
            ans += '\nЕсли вас нет в топе, то проверьте, подписаны ли вы на Тетрадку Петрика (@petr1ktv). ' \
                   'Подпишитесь, сделайте любую ставку в боте - и вы появитесь в рейтинге.\n'

            await message.answer(ans, reply_markup=button_list)
            
    except Exception as e:
        with open('logs.txt', 'a') as _log_file:
            log_file.write(str(e) + ' show ratings\n')
        ans = 'Что-то пошло не так, багрепорт уже отправлен разработчику.' \
              '\nНажмите /register, если еще не зарегистрированы в игре.'
        await message.answer(ans, reply_markup=button_list)

# run long-polling
if __name__ == "__main__":
    with open('logs.txt', 'a') as log_file:
        log_file.write('I am here at' + str(datetime.now().time()) + '\n')

    try:
        checker = os.stat('data/matches.json')
        if checker.st_size:
            with open('data/matches.json', 'r') as load_file:
                upcoming_matches = json.load(load_file)
    except Exception as _e:
        with open('logs.txt', 'a') as log_file:
            log_file.write(str(_e) + ' load matches\n')

    try:
        checker = os.stat('data/results.json')
        if checker.st_size:
            with open('data/results.json', 'r') as load_file:
                results = json.load(load_file)
    except Exception as _e:
        with open('logs.txt', 'a') as log_file:
            log_file.write(str(_e) + ' load results\n')

    try:
        checker = os.stat('data/balance.json')
        if checker.st_size:
            with open('data/balance.json', 'r') as load_file:
                users = json.load(load_file)
    except Exception as _e:
        with open('logs.txt', 'a') as log_file:
            log_file.write(str(_e) + ' load balance\n')

    except Exception as _e:
        with open('logs.txt', 'a') as log_file:
            log_file.write(str(_e) + ' load second data\n')

    get_matches()
    get_results()
    update_variables()
    update_bets()
    update_rating()

    executor.start_polling(dp, skip_updates=True)
