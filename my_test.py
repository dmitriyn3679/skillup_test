import os
from pathlib import Path
from dataclasses import dataclass
from pprint import pprint
from typing import Any
from datetime import datetime
import operator
import calendar

COEFFICIENT_HAPPY_BIRTHDAY = 3
COEFFICIENT_1 = 0.9
COEFFICIENT_2 = 0.8
COEFFICIENT_3 = 0.7
YEAR_2020_WORK_DAYS = 251
DATETIME_PATTERN = '%Y-%m-%d %H:%M:%S'

ROOT = Path().parent.resolve()

hr_data_file = ROOT / 'files/hr/data.txt'
acc_data_file = ROOT / 'files/accounts/data.txt'
security_path = ROOT / 'files/security'


def read_file(path):
    with open(path, encoding='UTF-8') as f:
        return f.readlines()


def split_data(line):
    return list(map(str.strip, line.split('|')))


def parse_data(filepath):
    raw_data = list(read_file(filepath))
    return list(map(split_data, raw_data))


@dataclass
class Person:
    id: str
    name: str
    birthdate: str
    start_work: str
    phone: str
    security: Any
    position: str = ''
    rate: int = 0

    def __str__(self):
        return self.name


def get_persons():
    persons = parse_data(hr_data_file)
    persons = [Person(*item, security={}) for item in persons]
    acc_data = {person_id: {'position': position, 'rate': int(rate)} for person_id, position, rate in
                parse_data(acc_data_file)}

    security_dict = get_date_time(security_path)

    for person in persons:
        account_persons = acc_data.get(person.id)
        if account_persons:
            person.position = account_persons.get('position')
            person.rate = account_persons.get('rate')

        entrance_person = security_dict.get(person.id)
        if entrance_person:
            person.security = entrance_person

        for year in person.security.values():
            for month in year.values():
                for day in month.values():
                    entrance1, entrance2, exit1, exit2 = day
                    first_half = datetime.strptime(exit1, DATETIME_PATTERN) - datetime.strptime(entrance1,
                                                                                                DATETIME_PATTERN)
                    first_half = round(first_half.seconds / 3600, 2)
                    second_half = datetime.strptime(exit2, DATETIME_PATTERN) - datetime.strptime(entrance2,
                                                                                                 DATETIME_PATTERN)
                    second_half = round(second_half.seconds / 3600, 2)
                    day.clear()
                    day.extend([first_half, second_half])

    return persons


def get_date_time(path):
    dict_ = {}
    for dir_ in os.listdir(path):
        for file in os.listdir(f'{security_path}/{dir_}'):
            for person_id, datetime_ in parse_data(f'{security_path}/{dir_}/{file}'):
                date_, time_ = datetime_.split(' ')
                year, month, day = date_.split('-')
                dict_.setdefault(person_id, {}).setdefault(year, {}).setdefault(month, {}).setdefault(day, []).append(
                    datetime_)
    return dict_


def stats_for_year(year, person_id):
    for person in persons:
        if person.id == person_id:
            for year in person.security.values():
                return year


def stats_for_month(year_month, person_id):
    year, month = year_month.split('-')
    month_stats = stats_for_year(year, person_id).get(month)
    return month_stats


def stats_for_day(year_month_day, person_id):
    list_calc = []
    year, month, day = year_month_day.split('-')
    try:
        return stats_for_month(f'{year}-{month}', person_id).get(day)
    except (AttributeError, TypeError):
        return f'Статистики за {year}-{month}-{day} нет!'


# 1. Посчитать сколько времени часов и минут работал сотрудник каждый день.
def working_hours_per_day(year, person_id):
    work_time = {}
    for month in stats_for_year(year, person_id).keys():
        for day in stats_for_month(f'{year}-{month}', person_id).keys():
            work_time.setdefault(month, []).append(round(sum(stats_for_day(f"{year}-{month}-{day}", person_id)), 2))
    return work_time


# Вспомагательная функция
def rate_person(person_id):
    for person in persons:
        if person.id == person_id:
            rate = person.rate
            return rate


def work_days_in_month(date):
    cal = calendar.Calendar()
    weekday_count = 0
    year, month = date.split('-')
    for week in cal.monthdayscalendar(int(year), int(month)):
        for i, day in enumerate(week):
            # not this month's day or a weekend
            if day == 0 or i >= 5:
                continue
            # or some other control if desired...
            weekday_count += 1
    return weekday_count


# CMD -----------------------------------------------------------------------------------------
def list_():
    for person in persons:
        pprint(f"ID: {person.id}, ФИО: {person}")


# 5. Средняя длительность рабочего дня для каждого сотрудника и для всего коллектива
def average_length_of_the_day(person_list):
    dict_work_time = {}
    for person_id in person_list:
        for value in working_hours_per_day('2020', person_id).values():
            dict_work_time.setdefault(person_id, []).append(round(sum(value) / len(value), 2))
    for person_id in dict_work_time.keys():
        dict_work_time[person_id] = round(
            sum(dict_work_time.get(person_id)) / len(dict_work_time.get(person_id)), 2)
    return dict_work_time


# 4. Шаблон для вычислений по з/п
def big_salary(year, person_list):
    salary_dict = {}
    for person_id in person_list:
        work_time_dict = working_hours_per_day(year, person_id)
        for month in work_time_dict.keys():
            salary_for_month = []
            for time_ in work_time_dict.get(month):
                rate = rate_person(person_id)
                salary = rate * time_
                if 8 > time_ > 7.5:
                    salary = salary * COEFFICIENT_1
                elif 7.5 > time_ > 7:
                    salary = salary * COEFFICIENT_2
                elif time_ < 7:
                    salary = salary * COEFFICIENT_3
                salary_for_month.append(round(salary, 2))
            salary_dict.setdefault(month, []).append(round(sum(salary_for_month), 2))
    return salary_dict


# 1. Общее количество сотрудников
# 2. Количество сотрудников по должностям и оплата за час работы для каждой должности
def calc_position():
    calc_position_dict = {'president': 0, 'vice president': 0, 'assistant': 0, 'secure': 0, 'accountant': 0,
                          'department head': 0, 'employee': 0}
    for person in persons:
        if person.position:
            calc_position_dict[person.position] += 1
    return f"""
    Количество сотрудников: {len(persons)} человек.
    {'-' * 100}
    Количество сотрудников по должностям: {calc_position_dict}"""


# 4. Сумма всех выплат по месяцам
def salary(year, person_list):
    salary_dict = big_salary(year, person_list)
    for key in salary_dict.keys():
        salary_dict[key] = round(sum(salary_dict.get(key)), 2)
    return f"""
    {'-' * 100}
    Сумма всех выплат по месяцам за {year} год: {salary_dict}
    """


# 6. Лучшие показатели и худшие - 5 лучших и 5 худших сотрудников.
# 7. Найти двух сотрудников которые больше всех работали и меньше всех работали.
def best_worst_employees_2(persons_list):
    dict_work_time = average_length_of_the_day(persons_list)
    sorted_tuples = sorted(dict_work_time.items(), key=operator.itemgetter(1))
    dict_work_time.clear()
    dict_work_time = {k: v for k, v in sorted_tuples}
    print('-' * 100)
    return f"""
    Средняя длительность рабочего дня для каждого сотрудника: {sorted_tuples[::-1]}
    {'-' * 100}
    Средняя длительность рабочего дня для всего коллектива:
    {round(sum(dict_work_time.values()) / len(dict_work_time.values()), 2)} часов.
    5 лучших сотрудников {sorted_tuples[:-6:-1]}
    5 худших сотрудников {sorted_tuples[:5]}
    2 лучших сотрудников {sorted_tuples[:-3:-1]}
    2 худших сотрудников {sorted_tuples[:2]}
    """


# <id>, ФИО, дата рождения, должность, зарплата за месяц
def get_info(person_id):
    for person in persons:
        if person.id == person_id:
            # print(f'{person.id}, {person.name}, {person.birthdate}, {person.position}')
            # print()
            return f"""
            {person.id}, {person.name}, {person.birthdate}, {person.position}\
            {'-' * 100}
            Зарплата за месяц:
            {big_salary('2020', [person_id])}
            {'-' * 100}
            """


def work_day_hours_for_person(person_id):
    work_days = []
    work_hours_list = []
    work_hours = working_hours_per_day('2020', person_id)
    for value in work_hours.values():
        work_days.append(len(value))
        work_hours_list.append(sum(value))
    # print(f'Количиество отработаных дней: {sum(work_days)}')
    # print(f'Количиество пропущеных дней: {YEAR_2020_WORK_DAYS - sum(work_days)}')
    # print(f'Количиество отработаных часов: {round(sum(work_hours_list), 2)}')
    return f"""
    Количиество отработаных дней: {sum(work_days)}
    Количиество пропущеных дней: {YEAR_2020_WORK_DAYS - sum(work_days)}
    Количиество отработаных часов: {round(sum(work_hours_list), 2)}
    {'-' * 100}
    Cредняя продолжительность рабочего дня: {average_length_of_the_day([person_id]).get(person_id)} часов'
    """


def big_stats(person_id=None):
    persons_list = [person.id for person in persons]
    if person_id == None:
        return calc_position(), salary('2020', persons_list), best_worst_employees_2(persons_list)
    elif person_id:
        try:
            return get_info(person_id), work_day_hours_for_person(person_id)
        except AttributeError:
            return f'Введите корректные данные!'


def statistic(date, person_id):
    condition = len(date.split('-'))
    if condition == 1:
        if date == '2020':
            work_hours_list = []
            for value in working_hours_per_day(date, person_id).values():
                work_hours_list.extend(value)
            # print(f'Количиество отработаных дней: {len(work_hours_list)}')
            # print(f'Количиество отработаных часов: {round(sum(work_hours_list), 2)}')
            # print(f'Количиество пропущеных дней: {YEAR_2020_WORK_DAYS - len(work_hours_list)}')
            # print(f'Cредняя продолжительность рабочего дня: {round(sum(work_hours_list) / len(work_hours_list), 2)} часов')
            return f"""
            Количиество отработаных дней: {len(work_hours_list)}
            Количиество отработаных часов: {round(sum(work_hours_list), 2)}
            Количиество пропущеных дней: {YEAR_2020_WORK_DAYS - len(work_hours_list)}
            Cредняя продолжительность рабочего дня: {round(sum(work_hours_list) / len(work_hours_list), 2)} часов     
            """
        else:
            return f'Статистики за {date} нет!'

    elif condition == 2:
        try:
            work_hours_list = []
            for day in stats_for_month(date, person_id).values():
                work_hours_list.append(sum(day))
            # print(f'Количиество отработаных дней: {len(work_hours_list)}')
            # print(f'Количиество отработаных часов: {round(sum(work_hours_list), 2)}')
            # print(f'Количиество пропущеных дней: {work_days_in_month(date) - len(work_hours_list)}')
            # print(f'Cредняя продолжительность рабочего дня: {round(sum(work_hours_list) / len(work_hours_list), 2)} часов')
            return f"""
            Количиество отработаных дней: {len(work_hours_list)}
            Количиество отработаных часов: {round(sum(work_hours_list), 2)}
            Количиество пропущеных дней: {work_days_in_month(date) - len(work_hours_list)}
            Cредняя продолжительность рабочего дня: {round(sum(work_hours_list) / len(work_hours_list), 2)} часов
            """
        except AttributeError:
            return f'Статистики за {date} нет!'

    elif condition == 3:
        try:
            stats_day = stats_for_day(date, person_id)
            rate = rate_person(person_id)
            # print(f'{date} - работал: {round(sum(stats_day), 2)} часов.')
            # print(f'Работал до обеда: {stats_day[0]} часов / после обеда: {stats_day[1]}')
            # print(f'Оплата за день {round(sum(stats_day) * rate, 2)}')
            return f"""
            {date} - работал: {round(sum(stats_day), 2)} часов.
            Работал до обеда: {stats_day[0]} часов / после обеда: {stats_day[1]}
            Оплата за день {round(sum(stats_day) * rate, 2)}
            """
        except TypeError:
            return f'Статистики за {date} нет!'


def search(person_lastname):
    persons_info_list = []
    for person in persons:
        if person_lastname in person.name:
            persons_info_list.append(
                f"""
                {person.id} - {person.name} 
                День народження: {person.birthdate} 
                Початок роботи: {person.start_work} 
                Номер телефону: {person.phone} 
                Посада: {person.position} 
                Оплата за годину роботи: {person.rate}
                """
            )
    return persons_info_list


if __name__ == '__main__':
    persons = get_persons()

    while True:
        args = input('Enter command: ')

        if args == 'exit':
            break

        elif args == 'list':
            list_()

        elif args == 'info':
            print(big_stats())

        elif len(args.split(' ')) == 2:
            command, params = args.split()
            if command == 'info':
                print(big_stats(params))

            elif command == 'search':
                print(search(params))

        elif len(args.split(' ')) == 3:
            command, date, person_id = args.split(' ')
            if command == 'statistic':
                print(statistic(date, person_id))
