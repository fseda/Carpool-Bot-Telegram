from models import Carpool, session
from datetime import datetime, timedelta
import time

def get_rides_by_dir(chat_id, direction):
    set_rides_inactive(chat_id)

    carpool_type = 'going' if direction == 'ida' else 'returning'
    rides = session.query(Carpool).filter_by(chat_id=str(chat_id), carpool_type=carpool_type, is_active=True)

    yesterday_rides, today_rides, tomorrow_rides = separate_rides(rides)

    weekdays = ['Domingo', 'Segunda-Feira', 'Terça-Feira', 'Quarta-Feira', 'Quinta-Feira', 'Sexta-Feira', 'Sábado']
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    today_weekday_index = datetime.today().isoweekday()

    yesterday_weekday = weekdays[(today_weekday_index - 1) % 7]
    today_weekday = weekdays[today_weekday_index]
    tomorrow_weekday = weekdays[(today_weekday_index + 1) % 7]

    message = ''

    if len(yesterday_rides) > 0:
        message += f'{yesterday_weekday} - {yesterday.day:02d}/{yesterday.month:02d}\n\n'
        message += get_rides_message(yesterday_rides, direction)
        message += '\n'

    if len(today_rides) > 0:
        message += f'{today_weekday} - {today.day:02d}/{today.month:02d}\n\n'
        message += get_rides_message(today_rides, direction)
        message += '\n'
    
    if len(tomorrow_rides) > 0:
        message += f'{tomorrow_weekday} - {tomorrow.day:02d}/{tomorrow.month:02d}\n\n'
        message += get_rides_message(tomorrow_rides, direction)
            
    return message

def get_all_rides(chat_id):
    set_rides_inactive(chat_id)

    rides_going = session.query(Carpool).filter_by(chat_id=str(chat_id), carpool_type='going', is_active=True)
    yesterday_rides_going, today_rides_going, tomorrow_rides_going = separate_rides(rides_going)
    
    rides_returning = session.query(Carpool).filter_by(chat_id=str(chat_id), carpool_type='returning', is_active=True)
    yesterday_rides_returning, today_rides_returning, tomorrow_rides_returning = separate_rides(rides_returning)

    weekdays = ['Domingo', 'Segunda-Feira', 'Terça-Feira', 'Quarta-Feira', 'Quinta-Feira', 'Sexta-Feira', 'Sábado']
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    today_weekday_index = datetime.today().isoweekday()

    yesterday_weekday = weekdays[(today_weekday_index - 1) % 7]
    today_weekday = weekdays[today_weekday_index]
    tomorrow_weekday = weekdays[(today_weekday_index + 1) % 7]

    message = '' 

    if (len(yesterday_rides_going) or len(yesterday_rides_returning)) > 0:
        message += f'{yesterday_weekday} - {yesterday.day:02d}/{yesterday.month:02d}\n\n'
        going = get_rides_message(yesterday_rides_going, 'ida')
        message += going + '\n' if going != '' else ''
        returning = get_rides_message(yesterday_rides_returning, 'volta')
        message += returning + '\n' if returning != '' else ''

    if (len(today_rides_going) or len(today_rides_returning)) > 0:
        message += f'{today_weekday} - {today.day:02d}/{today.month:02d}\n\n'
        going = get_rides_message(today_rides_going, 'ida')
        message += going + '\n' if going != '' else ''
        returning = get_rides_message(today_rides_returning, 'volta')
        message += returning + '\n' if returning != '' else ''

    if (len(tomorrow_rides_going) or len(tomorrow_rides_returning)) > 0:
        message += f'{tomorrow_weekday} - {tomorrow.day:02d}/{tomorrow.month:02d}\n\n'
        going = get_rides_message(tomorrow_rides_going, 'ida')
        message += going + '\n' if going != '' else ''
        returning = get_rides_message(tomorrow_rides_returning, 'volta')
        message += returning + '\n' if returning != '' else ''

    return message if message != '' else 'Não há ofertas de carona :('

def separate_rides(rides: list[Carpool]) -> tuple[list[Carpool], list[Carpool], list[Carpool]]:
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    yesterday_rides = []
    today_rides = []
    tomorrow_rides = []

    for ride in rides:
        ride_date = ride.departure_datetime

        if ride_date.day == yesterday.day:
            yesterday_rides.append(ride)
        if ride_date.day == today.day:
            today_rides.append(ride)
        if ride_date.day == tomorrow.day:
            tomorrow_rides.append(ride)
    
    return yesterday_rides, today_rides, tomorrow_rides
    
def get_rides_message(rides, direction):
    if len(rides) == 0:
        return ''

    if direction == 'ida':
        to_or_from_message = 'Ida ao'
    elif direction == 'volta':
        to_or_from_message = 'Volta do'

    message = f'<b>{to_or_from_message} Fundão</b>\n'

    for ride in rides:
        available_seats_message = get_available_seats_message(ride)

        hour = ride.departure_datetime.hour
        minutes = ride.departure_datetime.minute
        time = f'{hour}:{minutes}'
        parsed_time = format_time(time)

        message += f'@{ride.telegram_username} - {parsed_time} de {ride.place} ({available_seats_message})\n'
    return message

def schedule_ride(chat_id, username, direction, time, available_seats, place):
    clear_old_rides()

    carpool_type = 'going' if direction == 'ida' else 'returning'
    session.query(Carpool).filter_by(chat_id=str(chat_id), telegram_username=username, carpool_type=carpool_type, is_active=True).delete()

    new_ride = Carpool()
    new_ride.created_at = datetime.now()
    new_ride.departure_datetime = calculate_carpool_datetime(time)
    new_ride.available_seats = available_seats
    new_ride.place = place
    new_ride.carpool_type = 'going' if direction == 'ida' else 'returning'
    new_ride.is_active = True
    new_ride.telegram_username = username
    new_ride.chat_id = chat_id
    new_ride.save()

    available_seats_formatted = 'vaga' if int(available_seats) == 1 else 'vagas'
    direction_formatted = 'indo até' if direction == 'volta' else 'saindo de'

    return f"@{username} oferece carona de {direction} às {time} com {available_seats} {available_seats_formatted} {direction_formatted} {place}"

def check_available_seats(input):
    try:
        available_seats = int(input)
    except ValueError:
        return False
    
    if available_seats < 0:
        return False
    return True

def get_available_seats_message(ride):
    available_seats = ride.available_seats
    if available_seats == 0:
        available_seats_message = 'lotado'
    elif available_seats == 1:
        available_seats_message = '1 vaga'
    else:
        available_seats_message = f'{available_seats} vagas'

    return available_seats_message

def check_time(input):
    try:
        if ':' in input:
            time.strptime(input, '%H:%M')
        else: 
            time.strptime(input, '%H')
        return True
    except ValueError:
        return False
    
def format_time(input):
    if ':' in input:
        hour, minute = input.split(':')
        return datetime(2020, 1, 1, hour=int(hour), minute=int(minute)).strftime('%H:%M')
    return datetime(2020, 1, 1, hour=int(input)).strftime('%H:%M')

def calculate_carpool_datetime(input):
    current_datetime = datetime.now()
    current_time = current_datetime.strftime('%H:%M')

    year = current_datetime.date().year
    month = current_datetime.date().month
    day = current_datetime.date().day

    try:
        if current_time > input:
            day += 1
        hour, minute = input.split(':')
        carpool_datetime = datetime(year, month, day, int(hour), int(minute))
    except ValueError:
        try:
            carpool_datetime = datetime(year, month + 1, 1, int(hour), int(minute))
        except ValueError:
            carpool_datetime = datetime(year + 1, 1, 1, int(hour), int(minute))

    return carpool_datetime

def clear_old_rides():
    today = datetime.now()
    _36_hours = timedelta(hours=36)
    _36_hours_ago = today - _36_hours
    session.query(Carpool).filter(Carpool.created_at <= _36_hours_ago).delete()

def set_rides_inactive(chat_id):
    current_time = datetime.now()
    _30_minutes = timedelta(minutes=30)

    rides = session.query(Carpool).filter(
        Carpool.chat_id==str(chat_id),
        Carpool.is_active==True,
        Carpool.departure_datetime + _30_minutes < current_time
    )

    for ride in rides:
        ride.is_active = False
    
    session.commit()
