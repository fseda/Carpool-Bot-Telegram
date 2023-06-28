import os
import telebot
from models import Carpool, session
from functions import check_available_seats, check_time, format_time, schedule_ride, get_all_rides, get_rides_by_dir
from background import keep_alive

BOT_TOKEN = os.environ['BOT_TOKEN']
tb = telebot.TeleBot(token=BOT_TOKEN)


@tb.message_handler(commands=['ida', 'volta'])
def ride(message):
  chat_id = message.chat.id
  username = message.from_user.username

  parsed_message = message.text.split()
  command = parsed_message[0]

  direction = command[1:].split('@')[0]

  # Get Rides
  if len(parsed_message) == 1:
    rides = get_rides_by_dir(chat_id, direction)
    if len(rides) == 0:
      return tb.send_message(
        chat_id, text=f"Não há ofertas de carona de {direction} :(")

    return tb.send_message(chat_id, str(rides), parse_mode='HTML')

  if not 3 < len(parsed_message) < 6:
    return tb.send_message(chat_id,
                           text=f"Uso: {command} [horario] [vagas] [local]\n\
Ex: {command} 8:00 3 Barra Shopping")

  time = parsed_message[1]
  available_seats = parsed_message[2]
  place = ' '.join(parsed_message[3:])

  if not check_available_seats(available_seats):
    return tb.send_message(chat_id, text='Número de vagas inválido')

  if not check_time(time):
    return tb.send_message(chat_id, text='Horário Invalido.')

  time = format_time(time)

  return_message = schedule_ride(chat_id, username, direction, time,
                                 available_seats, place)

  return tb.send_message(message.chat.id, return_message)


@tb.message_handler(commands=['caronas'])
def list_rides(message):
  chat_id = message.chat.id

  message = get_all_rides(chat_id)
  return tb.send_message(chat_id, text=message, parse_mode='HTML')


@tb.message_handler(commands=['remover'])
def remove_ride(message):
  chat_id = message.chat.id
  username = message.from_user.username

  parsed_message = message.text.split()
  if len(parsed_message) != 2:
    return tb.send_message(chat_id,
                           text='Uso: /remover [ida|volta]\nEx: /remover ida')

  direction = parsed_message[1]
  if direction not in ['ida', 'volta']:
    return tb.send_message(chat_id,
                           text='Uso: /remover [ida|volta]\nEx: /remover ida')

  carpool_type = 'going' if direction == 'ida' else 'returning'
  session.query(Carpool).filter_by(chat_id=str(chat_id),
                                   telegram_username=username,
                                   carpool_type=carpool_type).delete()

  return tb.send_message(chat_id,
                         text=f'@{username} removeu a carona de {direction}')


@tb.message_handler(commands=['vagas'])
def update_available_seats(message):
  chat_id = message.chat.id
  username = message.from_user.username

  warning_message_use = f'Uso: /vagas [ida|volta] [vagas]\nEx: /vagas ida 2'

  parsed_message = message.text.split()
  if len(parsed_message) != 3:
    return tb.send_message(chat_id, text=warning_message_use)

  direction = parsed_message[1]
  available_seats = parsed_message[2]

  if direction not in ['ida', 'volta']:
    return tb.send_message(chat_id, text=warning_message_use)

  if not check_available_seats(available_seats):
    return tb.send_message(chat_id, text='Número de vagas inválido')

  direction = 'going' if direction == 'ida' else 'returning'

  ride = session.query(Carpool).filter_by(chat_id=str(chat_id),
                                          telegram_username=username,
                                          carpool_type=direction).first()

  if not ride:
    return

  ride.available_seats = available_seats
  ride.save()

  return tb.send_message(
    chat_id,
    text=f'@{username} atualizou o número de vagas para {available_seats}')


@tb.message_handler(commands=['lotou'])
def set_ride_to_full(message):
  chat_id = message.chat.id
  username = message.from_user.username

  warning_message_use = f'Uso: /lotou [ida|volta]\nEx: /lotou ida'

  parsed_message = message.text.split()
  if len(parsed_message) != 2:
    return tb.send_message(chat_id, text=warning_message_use)

  direction = parsed_message[1]

  if direction not in ['ida', 'volta']:
    return tb.send_message(chat_id, text=warning_message_use)

  carpool_type = 'going' if direction == 'ida' else 'returning'

  ride = session.query(Carpool).filter_by(chat_id=str(chat_id),
                                          telegram_username=username,
                                          carpool_type=carpool_type).first()

  ride.available_seats = 0
  ride.save()

  return tb.send_message(
    chat_id, f'@{username} atualizou o número de vagas de {direction} para 0')


keep_alive()
tb.polling(non_stop=True, interval=0)
