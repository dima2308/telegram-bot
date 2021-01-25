import logging
from datetime import datetime

import requests
import telebot
from emoji import emojize
from requests.api import get

from config import TG_TOKEN, WEATHERSTACK_API_KEY
from utils import (KIND_SMILE, SAD_SMILE, db, doings_collection,
                   get_many_from_db, get_one_from_db, get_weather_advice,
                   help_text, insert_into_db, rates_collection)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log')


def main():
    bot = telebot.TeleBot(TG_TOKEN)

    default_kb = telebot.types.ReplyKeyboardMarkup(True)
    default_kb.row('Погода', 'Дела')
    default_kb.row('Оценка', 'Инфо', 'Помощь')

    @bot.message_handler(commands=['start'])
    def start_handler(message):
        bot.send_message(message.chat.id, 'Привет, {}!'.format(
            message.from_user.first_name), reply_markup=default_kb)

    @bot.message_handler(commands=['doings'])
    def select_doing(message):
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row('Добавить', 'Вывести список')
        keyboard.row('Назад')
        doing = bot.send_message(
            message.chat.id, 'Что ты хочешь сделать?', reply_markup=keyboard)
        bot.register_next_step_handler(doing, doings_controller)

    def doings_controller(message):
        if message.text == 'Добавить':
            keyboard = telebot.types.ReplyKeyboardMarkup(True)
            keyboard.row('Отмена')
            doing = bot.send_message(
                message.chat.id, 'Что ты сегодня уже сделал(а)?', reply_markup=keyboard)
            bot.register_next_step_handler(doing, add_doing)
        elif message.text == 'Вывести список':
            get_doings(message)
        elif message.text == 'Назад':
            bot.send_message(
                message.chat.id, 'Хорошо', reply_markup=default_kb)
            return

    def add_doing(message):
        if message.text == 'Отмена':
            bot.send_message(
                message.chat.id, 'Хорошо', reply_markup=default_kb)
            return

        data = {
            "user_id": message.from_user.id,
            "doing": message.text.strip().capitalize(),
            "date": str(datetime.date(datetime.today()))
        }

        try:
            insert_into_db(doings_collection, data)
            bot.send_message(
                message.chat.id, 'Отлично! Добавил в список.', reply_markup=default_kb)
        except:
            bot.send_message(
                message.chat_id, 'Не могу добавить... Попробуй позже.', reply_markup=default_kb)

    def get_doings(message):
        today = str(datetime.date(datetime.today()))
        data = get_many_from_db(doings_collection, data={
            "user_id": message.from_user.id,
            "date": today})

        res = ''

        for key, value in enumerate(data):
            res += str(key+1) + '. ' + value['doing'] + '\n'

        bot.send_message(message.chat.id, '{}\nЗа сегодня ты: \n'.format(today) +
                         res, reply_markup=default_kb)

    @bot.message_handler(commands=['rate'])
    def rate_bot(message):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            text='Круто!', callback_data='yes'))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Плохо', callback_data='no'))
        bot.send_message(message.chat.id,
                         'Оцени мою работу', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def query_handler(call):
        bot.answer_callback_query(
            callback_query_id=call.id, text='Спасибо за ответ!')

        answer = ''

        if call.data == 'yes':
            answer = 'Здорово, спасибо {}'.format(emojize(KIND_SMILE))
        elif call.data == 'no':
            answer = 'Жаль {}'.format(emojize(SAD_SMILE))

        user_id = call.message.from_user.id
        user_name = call.message.chat.username

        existed_rate = get_one_from_db(
            rates_collection, data={"user_id": user_id})

        if not existed_rate:
            data = {
                "user_id": user_id,
                "user_name": user_name,
                "liked": call.data,
                "date": datetime.now()
            }

            try:
                insert_into_db(rates_collection, data)
                bot.send_message(call.message.chat.id, answer)
            except:
                bot.send_message(call.message.chat_id,
                                 'Не могу добавить... Попробуй позже.')

        else:
            bot.send_message(call.message.chat.id,
                             'Твоя оценка уже была учтена!')

        bot.edit_message_reply_markup(
            call.message.chat.id, call.message.message_id)

    @ bot.message_handler(commands=['weather'])
    def get_city(message):
        city = bot.send_message(
            message.chat.id, 'Какой город тебя интересует?')
        bot.register_next_step_handler(city, get_info_about_city)

    def get_info_about_city(message):
        bot.send_message(
            message.chat.id, 'Ищу погоду в городе {}.'.format(message.text.capitalize()))
        params = {'access_key': WEATHERSTACK_API_KEY, 'query': message.text}
        api_result = requests.get(
            'http://api.weatherstack.com/current', params)
        api_response = api_result.json()

        if api_response.get('request'):
            temp = api_response['current']['temperature']
            country = api_response['location']['country']
            answer = get_weather_advice(temp)
            bot.send_message(message.chat.id,
                             'Сейчас за окном {}°'.format(temp))
            bot.send_message(message.chat.id, answer)
            bot.send_message(message.chat.id,
                             'P.S. Для справки, это {}.'.format(country))
        else:
            bot.send_message(
                message.chat.id, 'Информации по такому городу, к сожалению, нет. Попробуй другой.')

    @bot.message_handler(commands=['creator'])
    def get_creator_info(message):
        bot.send_message(
            message.chat.id, 'Создателем меня является @dmitry_rt\nНапиши ему, если есть вопросы и предложения.')

    @bot.message_handler(content_types=['text'])
    def text_message_controller(message):
        msg = message.text.lower()
        if msg == 'погода':
            get_city(message)
        elif msg == 'оценка':
            rate_bot(message)
        elif msg == 'инфо':
            get_creator_info(message)
        elif msg == 'дела':
            select_doing(message)
        elif msg == '/help' or msg == 'помощь':
            bot.send_message(message.chat.id, help_text)
        else:
            bot.send_message(message.chat.id,
                             'Я пока не могу тебя понять. Напиши мне /help')

    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    main()
