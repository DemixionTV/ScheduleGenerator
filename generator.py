
from deap import base, creator, tools, algorithms
import random
import numpy as np
from typing import List, Tuple, Dict
from datetime import date
import datetime

schedule_matrices = []

TIME_SLOTS = {
    0:'8:00',
    1:'9:40',
    2:'11:20',
    3:'13:20',
    4:'15:00',
    5:'16:40',
    6:'18:20',
    7:'20:00',
}

class Group:
    def __init__(self, name, is_disabled = False, size = 20, start_date = datetime.date(datetime.datetime.now().year, 9, 1), end_date = datetime.date(datetime.datetime.now().year, 12, 31), start_time = 0):
        self.name = name
        self.is_disabled = is_disabled
        self.start_date = start_date if type(start_date) == datetime.date else start_date.date()
        self.end_date = end_date if type(end_date) == datetime.date else end_date.date()
        self.size = size
        self.start_time = start_time

class Auditory:
    def __init__(self, name, size, software, is_disabled = False):
        self.name = name
        self.software = software
        self.is_disabled = is_disabled
        self.size = size
    def __repr__(self):
        return f'{self.name}'
class Subject:
    def __init__(self, name, requierements = []):
        self.name = name
        self.requierements = requierements



class SheduleSettings:
    def __init__(self, num_days = None, time_slots = {}, auditories = {}, groups = {}, shedule_items = [], subject_requierements = {}, start_date = datetime.datetime.now().date(), end_date = datetime.datetime.now().date()):
        self.num_days = num_days
        self.time_slots = time_slots
        self.num_times = len(self.time_slots.keys())
        self.shedule_items:List = shedule_items
        self.subject_requierements = subject_requierements
        self.groups:Dict[str,Group] = groups
        self.auditories:Dict[str,Auditory] = auditories
        self.start_date = start_date if type(start_date) == datetime.date else start_date.date()
        self.end_date = end_date if type(end_date) == datetime.date else end_date.date()
        self.update()
    def update(self):
        global schedule_matrices
        schedule_matrices = [np.empty((self.num_times, len(self.auditories)), dtype=object) for _ in range(self.num_days)]
        




    



num_days = 5  # Количество дней в расписании
num_times = 6  # Количество временных слотов в день

auditory_list = {"109":Auditory("109", 20, ["Проектор", "Экран", "Компьютеры","Аудиокурс"]),
                 "210":Auditory("210", 20, ["Проектор", "Экран", "Аудиосистема"]),
                 "312":Auditory("312", 20, ["Компьютеры", "Проектор", "Экран"]),
                 "313":Auditory("313", 20, ["Компьютеры", "Проектор", "Экран"]),
                 "315":Auditory("315", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"]),
                 "316":Auditory("316", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"]),
                 "318":Auditory("318", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"],True),
                 "319":Auditory("319", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"]),
                 "320":Auditory("320", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"]),
                 "321":Auditory("321", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"]),
                 "321":Auditory("321", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"],True),
                 "322":Auditory("322", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"]),
                 "323":Auditory("323", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"]),
                 "324":Auditory("324", 20, ["Компьютеры", "Проектор", "Экран","Аудиокурс"]),
                 "317":Auditory("317", 20, ["Компьютеры", "Аудиосистема", "Аудиокурс"])}


groups = {
    "ИБ-311": Group("ИБ-311", False, 20),
    "ИБ-321": Group("ИБ-321",False, 20),
    "ИБ-331": Group("ИБ-331",True, 20),
    "ИБ-341": Group("ИБ-341",False, 20),
    "ИБ-811": Group("ИБ-811",False, 20),
    "ИБ-821": Group("ИБ-821",False, 20)
}

subject_requierements = {"Английский": ["Аудиокурс"]}

# Создаем список занятий для примера (полный семестр)
example_schedule_items = []
for i in range(20):
    example_schedule_items += [
    ("ИБ-311", "Иванов", "Математика", "Лекция",i),
    ("ИБ-311", "Петров", "Физика", "Лабораторная",i),
    ("ИБ-311", "Сидоров", "История", "Семинар",i),
    ("ИБ-311", "Козлов", "Информатика", "Лекция",i),
    ("ИБ-311", "Иванов", "Химия", "Лабораторная",i),
    ("ИБ-311", "Петров", "Философия", "Семинар",i),
    ("ИБ-311", "Козлов", "Английский", "Практика",i),
    ("ИБ-321", "Сидоров", "География", "Лекция",i),
    ("ИБ-321", "Иванов", "Экономика", "Семинар",i),
    ("ИБ-331", "Петров", "Программирование", "Лабораторная",i),
    ("ИБ-321", "Козлов", "Биология", "Лекция",i),
    ("ИБ-331", "Сидоров", "Психология", "Семинар",i),
    ("ИБ-341", "Иванов", "Статистика", "Практика",i),
    ("ИБ-821", "Петров", "Социология", "Лекция",i),
    ("ИБ-811", "Козлов", "Маркетинг", "Семинар",i)
    ]
random.shuffle(example_schedule_items)


shedule_errors = {}


shedule_settings = SheduleSettings(2,TIME_SLOTS,auditory_list,groups,example_schedule_items,subject_requierements)

# Функция для проверки допустимости размещения занятия в расписании
def is_valid(matrix, time_slot, auditory_index, schedule_item, day, just_check = False):
    global shedule_settings
    if matrix[time_slot, auditory_index] is not None and not just_check:
        shedule_errors[schedule_item] = f"Аудитория уже занята {matrix[time_slot, auditory_index]}"
        return False
#    for aud in range(len(shedule_settings.auditories)):
#        if matrix[time_slot, aud] != None and matrix[time_slot, aud] != schedule_item:
#            if matrix[time_slot, aud][0] == schedule_item[0] or matrix[time_slot, aud][1] == schedule_item[1]:#Проверка на дублирование группы и преподавателя
#                shedule_errors[schedule_item] = f"Дублирование группы или преподавателя {day} {shedule_settings.time_slots[time_slot]} в {list(shedule_settings.auditories.keys())[aud]} {schedule_item} {matrix[time_slot,aud]}"
#                return False
    group_number, teacher, subject, lesson_type,less_num = schedule_item
    auditory_number = list(shedule_settings.auditories.keys())[auditory_index]
    if shedule_settings.groups[group_number].is_disabled and not shedule_settings.auditories[auditory_number].is_disabled: #Возможность для инвалидов
        shedule_errors[schedule_item] = "Недоступность аудитории для инвалидов"
        return False
#    print(subject, shedule_settings.subject_requierements.get(subject))
    if shedule_settings.subject_requierements.get(subject) != None:#Проверка ПО аудитории
        for requierement in shedule_settings.subject_requierements[subject]:
            if requierement not in shedule_settings.auditories[auditory_number].software:
                shedule_errors[schedule_item] = f"Нехватка ПО в аудитории {auditory_number}"
                return False
    date = shedule_settings.start_date + datetime.timedelta(days=day)
#    print(shedule_settings.groups[group_number].start_date)
    if date.weekday() == 6:#Воскресенье
        shedule_errors[schedule_item] = "Учеба недоступна в воскресенье"
        return False
    if date < shedule_settings.groups[group_number].start_date or date > shedule_settings.groups[group_number].end_date:#Проверка на рамки времени обучения
        shedule_errors[schedule_item] = "Недоступность аудитории вне рамок обучения группы"
        return False
    if shedule_settings.groups[group_number].size > shedule_settings.auditories[auditory_number].size:#Проверка вместимости аудитории
        shedule_errors[schedule_item] = "Аудитория слишком мала для группы"
        return False
#        print(group_number, date, shedule_settings.groups[group_number].start_date,shedule_settings.groups[group_number].end_date)
    return True


# Функция для заполнения расписания
def fill_schedule(schedule_matrices, schedule_items):
    available_slots = [(day, time_slot, auditory_index) for day in range(shedule_settings.num_days) for time_slot in range(shedule_settings.num_times) for auditory_index in range(len(shedule_settings.auditories))]
    random.shuffle(available_slots)
    for schedule_item in schedule_items:
        for day, time_slot, auditory_index in available_slots:
            if is_valid(schedule_matrices[day], time_slot, auditory_index, schedule_item, day):
                schedule_matrices[day][time_slot, auditory_index] = schedule_item
                available_slots.remove((day, time_slot, auditory_index))
                break
    return schedule_matrices


def count_schedule_cells() -> int:
    return shedule_settings.num_days * shedule_settings.num_times * len(shedule_settings.auditories)

def print_schedule(shedule):
    num_busy = 0
    busy = []
    for day in range(shedule_settings.num_days):
        print(f"День {shedule_settings.start_date + datetime.timedelta(days=day)}:")
        for time_slot in range(shedule_settings.num_times):
            for auditory_index in range(len(shedule_settings.auditories)):
                auditory_number = list(shedule_settings.auditories.keys())[auditory_index]
                if shedule[day][time_slot, auditory_index] is not None:
                    print(f"  Время {shedule_settings.time_slots[time_slot]}, Аудитория {shedule_settings.auditories[auditory_number]}: {shedule[day][time_slot, auditory_index]}")
                    num_busy += 1
                    busy.append(shedule[day][time_slot, auditory_index])
    print(f'Вставлено ячеек: {num_busy}/{len(shedule_settings.shedule_items)}')
    print(f'Свободные ячейки: {count_schedule_cells() - num_busy} / {count_schedule_cells()}')
    print('Не получилось вставить в расписание:')
    for elem in shedule_settings.shedule_items:
        if elem not in busy:
            print(elem, "Ошибка: ",shedule_errors[elem] if elem in shedule_errors.keys() else "Ошибка неизвестна")


def flatten_schedule(matrices):
    result = []
    for day in matrices:
        for row in day:
            for item in row:
                result.append(item)
    return result


def decode_schedule(individual, settings: SheduleSettings):
    times = settings.num_times
    auds = len(settings.auditories)
    days = settings.num_days
    size_per_day = times * auds
    total_size = days * size_per_day

    # Подгоняем под нужный размер: обрезаем или дополняем None
    fixed_individual = individual[:total_size] + [None] * (total_size - len(individual))

    schedule = []
    for i in range(days):
        flat_day = fixed_individual[i * size_per_day:(i + 1) * size_per_day]
        day_matrix = np.array(flat_day, dtype=object).reshape((times, auds))
        schedule.append(day_matrix)

    return schedule

def generate_valid_individual():
    while True:
        matrices = [np.full((shedule_settings.num_times, len(shedule_settings.auditories)), None) for _ in range(shedule_settings.num_days)]
        individual = fill_schedule(matrices, shedule_settings.shedule_items.copy())
        if individual is not None:
            return flatten_schedule(individual)


def set_shedule_settings(settings):
    global shedule_settings
    shedule_settings = settings

def count_missing_numbers(lst):
    if not lst:
        return 0
    min_val = min(lst)
    max_val = max(lst)
    expected_count = max_val - min_val + 1
    return expected_count - len(lst)



def check_valid_shedule(schedule):
    available_slots = [(day, time_slot, auditory_index) for day in range(shedule_settings.num_days) for time_slot in range(shedule_settings.num_times) for auditory_index in range(len(shedule_settings.auditories))]
    for schedule_item in shedule_settings.shedule_items.copy():
        for day, time_slot, auditory_index in available_slots:
            if not is_valid(schedule[day], time_slot, auditory_index, schedule_item, day, True):
                return False, (shedule_errors[schedule_item] if schedule_item in shedule_errors.keys() else "Ошибка неизвестна") + f" {day=} {time_slot=} {auditory_index=} {schedule_item=}"
            else:
                break
    return True, None


def evaluate(individual):
    shedule = decode_schedule(individual,shedule_settings)
#    print(shedule)
    valid = check_valid_shedule(shedule)
    if not valid[0]:
#        print(f'invalid mutant {valid[1]}')
        return -10000,
    conflicts = 0
    for day in range(shedule_settings.num_days):
        time_slots_busy_students = {}
        for time_slot in range(shedule_settings.num_times):
            for auditory_index in range(len(shedule_settings.auditories)):
                auditory_number = list(shedule_settings.auditories.keys())[auditory_index]
                if shedule[day][time_slot, auditory_index] is not None:
                    group_number, teacher, subject, lesson_type,less_num = shedule[day][time_slot, auditory_index]
                    if group_number not in time_slots_busy_students:
                        time_slots_busy_students[group_number] = {}
                    if time_slot not in time_slots_busy_students[group_number]:
                        time_slots_busy_students[group_number][time_slot] = True
                    if time_slot < shedule_settings.groups[group_number].start_time:
                        conflicts += (shedule_settings.groups[group_number].start_time - time_slot) * 15
        for group_number in time_slots_busy_students:
            if len(time_slots_busy_students[group_number]) > 4:
                conflicts += 10
            conflicts += 10 * count_missing_numbers(list(sorted(list(time_slots_busy_students[group_number].keys()))))
#        print(time_slots_busy_students)
                
#    used_slots = set()
#    index_placed = set()
#    conflicts = 0
#    all_invalid = True
#    for idx, (day, time, aud) in enumerate(individual):
#        slot = (day, time, aud)

        # конфликт — дублирование слотов
#        if slot in used_slots:
#            conflicts += 20
#        used_slots.add(slot)

        # проверка, удалось ли вообще разместить занятие
#        item = shedule_settings.shedule_items[idx]
#        dummy_matrix = np.empty((shedule_settings.num_times, len(shedule_settings.auditories)), dtype=object)
#        if is_valid(dummy_matrix, time, aud, item):
#            index_placed.add(idx)
#        else:
#            print(item, get_valid_error(dummy_matrix, time, aud, item))
#    placed_count = len(index_placed)
#    total = len(shedule_settings.shedule_items)
#    return placed_count - conflicts,  # максимум: total
    return -conflicts, 


creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

#toolbox.register("attr_slot", lambda: (
#    random.randint(0, shedule_settings.num_days - 1),
#    random.randint(0, shedule_settings.num_times - 1),
#    random.randint(0, len(shedule_settings.auditories) - 1)))

toolbox.register("individual", tools.initIterate, creator.Individual, generate_valid_individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", evaluate)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)

# === ГА выполнение ===
def run_ga():
    pop = toolbox.population(n=50)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("max", np.max)

    algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=100, stats=stats, halloffame=hof, verbose=True)
    global shedule_settings
#    best_schedule = decode(hof[0], shedule_settings)
    best_schedule = decode_schedule(hof[0], shedule_settings)
    return best_schedule

if __name__ == "__main__":
    s = generate_valid_individual()
    print_schedule(check_valid_shedule(s))
#    final_schedule = run_ga()
#    print_schedule(final_schedule)
#    shed = generate_valid_individual()
#    print_schedule(shed)
#    print(datetime.datetime.now().date().weekday())