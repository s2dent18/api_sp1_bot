import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
    encoding='utf-8',
    handlers=[
        RotatingFileHandler('program.log', maxBytes=50000000, backupCount=5),
    ]
)


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    statuses_dict = {
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'reviewing': 'Работа взята на проверку',
        'approved': (
            'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
        ),
    }
    homework_name = homework.get('homework_name')
    homework_statuses = homework.get('status')
    if homework_name is None or homework_statuses not in statuses_dict:
        logging.error('Неверный статус или имя работы не найдено')
        return 'Неверный статус или имя работы не найдено'
    verdict = statuses_dict[homework_statuses]
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            API_URL,
            headers=headers,
            params=params
        )
        return homework_statuses.json()
    except requests.exceptions.RequestException as e:
        logging.error(f'Ошибка запроса: {e}')
        return {}


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logging.debug('Бот запущен')

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client
                )
                logging.info('Бот отправил сообщение')
            current_timestamp = new_homework.get(
                'current_date'
            )
            time.sleep(60)

        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.error(message)
            send_message(message, bot_client)
            time.sleep(60)


if __name__ == '__main__':
    main()
