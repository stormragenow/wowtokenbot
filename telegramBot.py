import json
import string
import threading
import requests
from datetime import datetime
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from pandas import to_datetime

import config
from dbController import get_user_info, update_region_users, add_user

access_token = {}
result_price = []

telegram_bot_ = Bot(token=config.secret_token_bot_telegram)
dp = Dispatcher(telegram_bot_)

regions = {'us': 'us',
           'eu': 'eu',
           'cn': 'cn',
           'tw': 'tw',
           'kr': 'kr'}
fullname_region = {'us': 'United States',
                   'eu': 'Europe',
                   'cn': 'China',
                   'tw': 'Taiwan',
                   'kr': 'Korea'}


def create_access_token(client_id, client_secret, region='us'):
    # start = datetime.datetime.now()
    if not access_token:
        data = {'grant_type': 'client_credentials'}
        response = requests.post('https://%s.battle.net/oauth/token' % region, data=data,
                                 auth=(client_id, client_secret))
        access_token.update(response.json())
        token = access_token['access_token']
        print(f"{datetime.now():}created token on blizzard app")
        return token
    else:
        # print(datetime.datetime.now()-start)
        print(f"{datetime.now():}return token on blizzard app")
        return access_token['access_token']


def blizzard_get_response(region, access):
    if region == 'cn':
        get_tok_price = f'https://gateway.battlenet.com.cn/data/wow/token/index?namespace=dynamic-cn&locale=zh_CN' \
                        f'&access_token={access}'
    else:
        get_tok_price = f'https://{regions[region]}.api.blizzard.com/' \
                        f'data/wow/token/index?namespace=dynamic-{region}&locale=en_US&access_token=' \
                        f'{access}'
    return get_tok_price


def wow_token_price(region):
    snd_msg = ''
    access = create_access_token(client_id=config.api_id_blizzard, client_secret=config.api_key_blizzard)
    if region in regions:
        get_tok_price = blizzard_get_response(region=region, access=access)
        r = requests.get(get_tok_price)
        if r.status_code == 200:
            result = json.loads(r.text)
            price = result['price']
            date_price = result['last_updated_timestamp']
            result_ms = to_datetime(date_price, unit='ms')
            snd_msg += f'{fullname_region[region]}:{int(price / 10000)}g, {result_ms} \n'
        else:
            snd_msg += f' blizzard server error 📤, region:{region} \n'
    else:
        snd_msg += 'region not available'
    result_price.append(snd_msg)
    print(f"{datetime.now():}return price on token")
    return snd_msg
    # json "parse" end


def __multi_thread_price():
    create_access_token(client_id=config.api_id_blizzard, client_secret=config.api_key_blizzard)
    result_price.clear()
    threads = []
    for region in regions:
        threads.append(threading.Thread(target=wow_token_price, args=(region,)))
    for th in threads:
        th.start()
    for thread in threads:
        thread.join()
    return result_price


def keyboard_price_create(region=None):
    keyboard = types.InlineKeyboardMarkup()
    if region:
        token_button = types.InlineKeyboardButton(text=wow_token_price(region), callback_data=region)
        keyboard.add(token_button)
    else:
        snd_msg = __multi_thread_price()
        call_d = ''
        for ms in snd_msg:
            if ms[0] == 'E':
                call_d = regions['eu']
            elif ms[0] == 'U':
                call_d = regions['us']
            elif ms[0] == 'C':
                call_d = regions['cn']
            elif ms[0] == 'T':
                call_d = regions['tw']
            elif ms[0] == 'K':
                call_d = regions['kr']
            token_button = types.InlineKeyboardButton(text=ms, callback_data=call_d)
            keyboard.add(token_button)
    token_button = types.InlineKeyboardButton(text='Update all', callback_data='all')
    keyboard.add(token_button)
    return keyboard


@dp.callback_query_handler()
async def callback_inline(callback):
    # bot message
    try:
        if callback.message.chat:
            if callback.data == 'all':
                keyboard = keyboard_price_create()
                await telegram_bot_.edit_message_reply_markup(chat_id=callback.message.chat.id,
                                                              message_id=callback.message.message_id,
                                                              reply_markup=keyboard)
                user = get_user_info(callback.message.chat.id)
                print(f"{datetime.now():}send all regions info for user")
                if callback.message.chat.id in user:
                    update_region_users(callback.message.chat.id, None)
                else:
                    add_user(callback.message.chat.id, None)
            elif regions[callback.data]:
                user = get_user_info(callback.message.chat.id)
                print(f"{datetime.now():}send region info for user")
                if callback.message.chat.id in user:
                    update_region_users(callback.message.chat.id, regions[callback.data])
                else:
                    add_user(callback.message.chat.id, regions[callback.data])
                keyboard = keyboard_price_create(regions[callback.data])
                await telegram_bot_.edit_message_reply_markup(chat_id=callback.message.chat.id,
                                                              message_id=callback.message.message_id,
                                                              reply_markup=keyboard)
        # inline message
        elif callback.inline_message_id:
            if callback.data in regions:
                keyboard = keyboard_price_create(regions[callback.data])
                await telegram_bot_.edit_message_reply_markup(inline_message_id=callback.inline_message_id,
                                                              reply_markup=keyboard)
                update_region_users(callback.message.chat.id, regions[callback.data])
    except IndexError:
        return


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await telegram_bot_.send_message(message.chat.id,
                                     "Hello! if you need know current price"
                                     " on token world of warcraft or not need , welcome! 👌 "
                                     "available command /start /wow token /region"
                                     "\n developer @StormrageNow ")
    await process_region_command(message)


@dp.message_handler(commands=['wowtoken'])
async def process_wowtoken_command(message: types.Message):
    region = message.text.split()
    region.remove('/wowtoken')
    if 'all' in region:
        keyboard = keyboard_price_create()
        await message.reply('pick button if you need one region', reply_markup=keyboard)
    else:
        db_region = get_user_info(message.chat.id)
        if region:
            keyboard = keyboard_price_create(region[0])
            await message.reply("update or view all", reply_markup=keyboard)
        elif db_region:
            keyboard = keyboard_price_create(db_region[0])
            await message.reply("update or view all", reply_markup=keyboard)
        else:
            keyboard = keyboard_price_create()
            await message.reply('pick button if you need one region', reply_markup=keyboard)


@dp.message_handler(commands=['region'])
async def process_region_command(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    for reg in fullname_region:
        button = types.InlineKeyboardButton(text=f'⭐️{fullname_region[reg]}⭐️', callback_data=reg)
        keyboard.add(button)
    button = types.InlineKeyboardButton(text='View all', callback_data='all')
    keyboard.add(button)
    await telegram_bot_.send_message(message.chat.id, 'select', reply_markup=keyboard)


@dp.message_handler(content_types=["text"])
async def echo_message(message: types.Message):
    if not ('/' in message.text):
        await process_region_command(message)


thread_telegram = threading.Thread(target=executor.start_polling(dp),
                                   name="proc_telegram_thread_bot")

if __name__ == '__main__':
    # telegram bot start
    thread_telegram.start()
    thread_telegram.join()
