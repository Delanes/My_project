from engine import Engine
from datetime import datetime, timedelta
import gc
import json
import os
import sqlite3

e = Engine()

def convert_str_to_list(string):
    string = string.replace("[", "")
    string = string.replace("]", "")
    string = string.split(",")
    _list = []
    for c in string:
        try: _list.append(int(c.strip()))
        except: _list.append(c.strip())
    return _list


weekdays = [
    "Понеділок",
    "Вівторок",
    "Середа",
    "Четвер",
    "П'ятниця",
    "Субота",
    "Неділя"
]

_weekdays = [
    "понеділок",
    "вівторок",
    "середу",
    "четвер",
    "п'ятницю",
    "суботу",
    "неділю"
]

months = [
    "січня",
    "лютого",
    "березня",
    "квітня",
    "травня",
    "червня",
    "липня", 
    "серпня", 
    "вересня", 
    "жовтня", 
    "листопада", 
    "грудня" 
]

CONFIG_PATH = "config/config.json"
IMAGES_PATH = "config/images.json"
DB_PATH = "assets/data.db"

# Обертка базы данных (для удобного оперирования)
class DatabaseWrapper():

    def __init__(self): 
        pass

    def conn(self, query, fetch_mode = 1):
        try:
            db = sqlite3.connect(DB_PATH, check_same_thread = False)
            cursor = db.cursor()
            cursor.execute(query)
            db.commit()
            if fetch_mode == 1: return cursor.fetchall()
            elif fetch_mode == 2: return cursor.fetchone()
        except Exception as e: print(e)

    def list_tables(self):
        return self.conn(f"SELECT name FROM sqlite_master WHERE type = 'table'", 1)

    def select_all(self, table):
        return self.conn(f"SELECT * FROM {table}", 1)

    def select_by_id(self, table, id = 0):
        return self.conn(f"SELECT * FROM {table} WHERE id = '{id}'", 2)

    def insert(self, table, params, values = ""):
        return self.conn(f"INSERT INTO {table}({params}) VALUES({values})", 2)

    def update(self, table, set, condition):
        return self.conn(f"UPDATE {table} SET {set} WHERE {condition}", 2)

db = DatabaseWrapper()

# Отравка на команду /start главной страницы бота
@e.messages(commands = ['start'])
def handle_start(message):
    sender = message.from_user
    user = db.select_by_id("tg_users", sender.id)
    if not user: db.insert("tg_users", f"id, sex", f"{sender.id}, 0")
    user = db.select_by_id("tg_users", sender.id)
    params = e.get_default_params(sender)
    now = datetime.now()
    weekday = weekdays[now.weekday()]
    params['weekday'] = weekday
    params['datetime'] = f"{now.day} {months[now.month - 1]} {now.year} року"
    markup = [
        [
            {"text": e.get_button("training-programs"), "data": "training-programs"},
            {"text": e.get_button("diets"), "data": "diets"}
        ],
        {"text": e.get_button("sex-male" if user[1] == 0 else "sex-female"), "data": "toggle-sex"}
    ]
    e.send_tag(sender.id, "main-section", markup, params)
    gc.collect()

# Приём нажатий на inline-кнопки в боте
@e.callbacks(func = lambda call: True)
def handle_callbacks(call):
    images = json.load(open(IMAGES_PATH, encoding = 'utf-8-sig'))
    sender = call.from_user
    user = db.select_by_id("tg_users", sender.id)
    if not user: db.insert("tg_users", f"id, sex", f"{sender.id}, 0")
    user = db.select_by_id("tg_users", sender.id)
    params = e.get_default_params(sender)
    now = datetime.now()
    weekday_int = now.weekday()
    weekday = weekdays[weekday_int]
    params['weekday'] = weekday
    params['datetime'] = f"{now.day} {months[now.month - 1]} {now.year} року"
    
    if call.data == 'main-section':
        markup = [
            [
                {"text": e.get_button("training-programs"), "data": "training-programs"},
                {"text": e.get_button("diets"), "data": "diets"}
            ],
            {"text": e.get_button("sex-male" if user[1] == 0 else "sex-female"), "data": "toggle-sex"}
        ]
        e.edit_tag(call.message, "main-section", markup, params)
    
    if call.data == 'training-programs':
        sex = user[1]
        program = list(filter(lambda x: x[0] == sex + 1, db.select_all("training_programs")))[0]
        exercises_today = convert_str_to_list(program[3 + weekday_int])
        icon_path = program[2]
        _sex = "male" if sex == 0 else "female"
        image = None
        if images[_sex]: image = images[_sex]
        else: image = open(os.path.join(os.path.abspath("."), "assets", icon_path), "rb").read()
        params['sex'] = "Чоловіча" if sex == 0 else "Жіноча"
        markup = []
        for exercise in exercises_today:
            _exercise = db.select_by_id("exercises", exercise)
            markup.append({"text": e.get_button("exercise").format(_exercise[1]), "data": f"exercise={exercise}"})
        markup.append({"text": e.get_button("back"), "data": "main-section"})
        params['weekday'] = _weekdays[weekday_int]
        message = e.edit_tag(call.message, "training-programs", markup, params, image)
        try:
            photo = message.photo[0].file_id
            images[_sex] = photo
            json.dump(images, open(IMAGES_PATH, 'w+', encoding = 'utf-8'), indent = 4, ensure_ascii = False)
        except: pass

    if call.data == 'diet-mass-plus':
        
        image = None
        icon_path = "images\\diets\\diet_3.jpg"
        if images['diet-mass-plus']: image = images['diet-mass-plus']
        else: image = open(os.path.join(os.path.abspath("."), "assets", icon_path), "rb").read()
        markup = [
            {"text": e.get_button("breakfast"), "data": "mass-plus-breakfast"},
            {"text": e.get_button("brunch"), "data": "mass-plus-brunch"},
            {"text": e.get_button("dinner"), "data": "mass-plus-dinner"},
            {"text": e.get_button("back"), "data": "diets"},
        ]
        params['diet:type'] = "для набору ваги"
        message = e.edit_tag(call.message, "diet", markup, params, image)
        try:
            photo = message.photo[0].file_id
            images["diet-mass-plus"] = photo
            json.dump(images, open(IMAGES_PATH, 'w+', encoding = 'utf-8'), indent = 4, ensure_ascii = False)
        except: pass

    if call.data == 'diet-mass-minus':
        
        image = None
        icon_path = "images\\diets\\diet_4.jpg"
        if images['diet-mass-minus']: image = images['diet-mass-minus']
        else: image = open(os.path.join(os.path.abspath("."), "assets", icon_path), "rb").read()
        markup = [
            {"text": e.get_button("breakfast"), "data": "mass-minus-breakfast"},
            {"text": e.get_button("brunch"), "data": "mass-minus-brunch"},
            {"text": e.get_button("dinner"), "data": "mass-minus-dinner"},
            {"text": e.get_button("back"), "data": "diets"},
        ]
        params['diet:type'] = "для схуднення"
        message = e.edit_tag(call.message, "diet", markup, params, image)
        try:
            photo = message.photo[0].file_id
            images["diet-mass-minus"] = photo
            json.dump(images, open(IMAGES_PATH, 'w+', encoding = 'utf-8'), indent = 4, ensure_ascii = False)
        except: pass

    if call.data == 'diet-dry':
        
        image = None
        icon_path = "images\\diets\\diet_2.jpg"
        if images['diet-dry']: image = images['diet-dry']
        else: image = open(os.path.join(os.path.abspath("."), "assets", icon_path), "rb").read()
        markup = [
            {"text": e.get_button("breakfast"), "data": "dry-breakfast"},
            {"text": e.get_button("brunch"), "data": "dry-brunch"},
            {"text": e.get_button("dinner"), "data": "dry-dinner"},
            {"text": e.get_button("back"), "data": "diets"},
        ]
        params['diet:type'] = "для сушіння"
        message = e.edit_tag(call.message, "diet", markup, params, image)
        try:
            photo = message.photo[0].file_id
            images["diet-dry"] = photo
            json.dump(images, open(IMAGES_PATH, 'w+', encoding = 'utf-8'), indent = 4, ensure_ascii = False)
        except: pass

    if call.data == 'diets':

        image = None
        icon_path = "images\\diets\\diet_1.jpg"
        if images['diet-main']: image = images['diet-main']
        else: image = open(os.path.join(os.path.abspath("."), "assets", icon_path), "rb").read()
        markup = [
            {"text": e.get_button("diet-mass-plus"), "data": "diet-mass-plus"},
            {"text": e.get_button("diet-mass-minus"), "data": "diet-mass-minus"},
            {"text": e.get_button("diet-dry"), "data": "diet-dry"},
            {"text": e.get_button("back"), "data": "main-section"},
        ]
        message = e.edit_tag(call.message, "diets", markup, params, image)
        try:
            photo = message.photo[0].file_id
            images["diet-main"] = photo
            json.dump(images, open(IMAGES_PATH, 'w+', encoding = 'utf-8'), indent = 4, ensure_ascii = False)
        except: pass

    if call.data.startswith("exercise="):
        exercise_id = call.data.split('=')[1]
        exercise = db.select_by_id("exercises", exercise_id)

        title = exercise[1]
        description = exercise[2][:900]
        repeats = exercise[3]
        icon_path = exercise[4]
        
        image = None
        try: image = images["exercises"][str(exercise_id)]
        except: image = open(os.path.join(os.path.abspath("."), "assets", icon_path), "rb").read()
        params['title'] = title
        params['description'] = description
        params['repeat'] = repeats

        markup = [{"text": e.get_button("back"), "data": "training-programs"}]
        message = e.edit_tag(call.message, "exercise", markup, params, image)
        try:
            photo = message.photo[0].file_id
            images["exercises"][str(exercise_id)] = photo
            json.dump(images, open(IMAGES_PATH, 'w+', encoding = 'utf-8'), indent = 4, ensure_ascii = False)
        except: pass

    if "dinner" in call.data or "breakfast" in call.data or "brunch" in call.data:
        diet = None
        dish_id = None
        dish = None
        splitted = call.data.split('-')
        back_data = ""

        if splitted[0] == 'mass':
            if splitted[1] == 'plus': 
                diet = db.select_by_id("diets", 2)
                params["diet:type"] = "для набору ваги"
            elif splitted[1] == 'minus': 
                diet = db.select_by_id("diets", 3)
                params["diet:type"] = "для схуднення"
            if splitted[2] == 'breakfast': dish_id = diet[2]
            if splitted[2] == 'brunch': dish_id = diet[3]
            if splitted[2] == 'dinner': dish_id = diet[4]
            dish_id = int(dish_id.replace("[", "").replace("]", ""))
            dish = db.select_by_id("dishes", dish_id)
            back_data = f"diet-mass-{splitted[1]}"

        elif splitted[0] == 'dry':
            diet = db.select_by_id("diets", 4) 
            params["diet:type"] = "для сушіння"
            if splitted[1] == 'breakfast': dish_id = diet[2]
            if splitted[1] == 'brunch': dish_id = diet[3]
            if splitted[1] == 'dinner': dish_id = diet[4]
            dish_id = int(dish_id.replace("[", "").replace("]", ""))
            dish = db.select_by_id("dishes", dish_id)
            back_data = "diet-dry"

        if "breakfast" in call.data: params["eattime"] = "🌅 Сніданок"
        if "brunch" in call.data: params["eattime"] = "☀️ Обід"
        if "dinner" in call.data: params["eattime"] = "🌄 Вечеря"
        params["diet:menu"] = dish[2]
        params["diet:details"] = dish[3]
        icon_path = dish[4]
        image = None
        try: image = images['dishes'][str(dish_id)]
        except: image = open(os.path.join(os.path.abspath("."), "assets", icon_path), "rb").read()
        markup = [{"text": e.get_button("back"), "data": back_data}]
        message = e.edit_tag(call.message, "menu", markup, params, image)
        try:
            photo = message.photo[0].file_id
            images["dishes"][str(dish_id)] = photo
            json.dump(images, open(IMAGES_PATH, 'w+', encoding = 'utf-8'), indent = 4, ensure_ascii = False)
        except: pass


    if call.data == 'toggle-sex':
        current_sex = user[1]
        if current_sex == 1: current_sex = 0
        else: current_sex = 1
        db.update("tg_users", f"sex = {current_sex}", f"id = {sender.id}")
        user = db.select_by_id("tg_users", sender.id)
        markup = [
            [
                {"text": e.get_button("training-programs"), "data": "training-programs"},
                {"text": e.get_button("diets"), "data": "diets"}
            ],
            {"text": e.get_button("sex-male" if user[1] == 0 else "sex-female"), "data": "toggle-sex"}
        ]
        e.edit_tag(call.message, "main-section", markup, params)

    gc.collect()

e.start_polling()