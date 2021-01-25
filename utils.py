from config import client, MONGO_BD_NAME

KIND_SMILE = '😊'
SAD_SMILE = '☹'


def get_weather_advice(temp):
    if temp <= -15:
        answer = 'Очень холодно.'
    elif temp > -15 and temp <= 5:
        answer = 'Довольно прохладно.'
    elif temp > 5 and temp <= 24:
        answer = 'Вполне благоприятная температура.'
    else:
        answer = 'Очень жарко.'

    return answer


db = client.tg_bot
doings_collection = db['doings']
rates_collection = db['rates']


def insert_into_db(collection, data):
    collection.insert_one(data)


def get_many_from_db(collection, data):
    return collection.find(data)


def get_one_from_db(collection, data):
    return collection.find_one(data)


help_text = '''
Список доступных команд:
/weather - погода
/doings - добавление и просмотр дел
/creator - инфо о разработчике
/rate - оценка
'''
