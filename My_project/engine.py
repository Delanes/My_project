import json
import telebot
from datetime import datetime
import calendar
import math
from time import sleep
from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMedia

BUTTONS_PATH = "config/buttons.json"
TEXTS_PATH = "config/texts.json"
CONFIG_PATH = "config/config.json"
LOGS_PATH = "logs/"

class ChatUtil():
    def __init__(self, id): self.id = id

class MessageUtil():
    def __init__(self, chatid, messageid):
        self.chat = ChatUtil(chatid)
        self.message_id = messageid

class Engine():

    def __init__(self): 
        config = json.load(open(CONFIG_PATH, encoding = 'utf-8'))
        self.bot = telebot.TeleBot(config['bot']['token'])
        self.messages = self.bot.message_handler
        self.callbacks = self.bot.callback_query_handler

    def start_polling(self, sleep = 30): BotThread(self, self.bot, sleep).start()
    def get_default_params(self, sender):
        return {
            "id": sender.id, 
            "firstname": sender.first_name if sender.first_name else self.get_text("anonimous"),
            "lastname": sender.last_name if sender.last_name else "", 
            "username": "@" + sender.username if sender.username else ""
        }       

    def b(self, t, d): return InlineKeyboardButton(text = t, callback_data = d)
    def bu(self, t, u): return InlineKeyboardButton(text = t, url = u)             

    def build(self, buttons = [], params = {}):
        markup = InlineKeyboardMarkup()
        for row in buttons:
            if type(row) == type([]):
                _row = []
                for button in row:
                    if type(button) == type({}):
                        if "text" in button.keys():
                            text = self.format(button['text'], params)
                            if "data" in button.keys(): 
                                data = self.format(button['data'], params)
                                _row.append(self.b(text, data))
                            elif "url" in button.keys(): 
                                url = self.format(button['url'], params)
                                _row.append(self.bu(text, url))
                markup.row(*_row)
            elif type(row) == type({}):
                if "text" in row.keys():
                    text = self.format(row['text'], params)
                    if "data" in row.keys(): 
                        data = self.format(row['data'], params)
                        markup.row(self.b(text, data))
                    elif "url" in row.keys(): 
                        url = self.format(row['url'], params)
                        markup.row(self.bu(text, url))  
        return markup                         
    
    def get_message(self, chatid, messageid): 
        message = MessageUtil(chatid, messageid)
        return message

    def format(self, text, params = {}):
        if text:
            for key, value in params.items(): text = text.replace(f"${key}", str(value))
            return text

    def get_text(self, tag, locale = "ua"):
        texts = json.load(open(TEXTS_PATH, encoding = 'utf-8'))
        try: return texts[locale][tag] if type(tag) == type("_") else texts[locale][list(texts[locale].keys())[tag]]
        except: pass 

    def get_button(self, tag, locale = "ua"):
        buttons = json.load(open(BUTTONS_PATH, encoding = 'utf-8'))
        try: return buttons[locale][tag] if type(tag) == type("_") else buttons[locale][list(buttons[locale].keys())[tag]]
        except: pass 

    def send(self, id, text, markup = None, params = {}, photo = None):
        if markup:
            if type(markup) == type([]): markup = self.build(markup, params)
        if photo: return self.send_photo(id, photo, text, markup, params)
        else:
            try: return self.bot.send_message(id, self.format(text, params), parse_mode = 'html', reply_markup = markup, disable_web_page_preview = True)
            except Exception as e: print(e)

    def send_photo(self, id, photo, caption = None, markup = None, params = {}):
        if markup:
            if type(markup) == type([]): markup = self.build(markup, params)
        try: return self.bot.send_photo(id, photo, caption = self.format(caption, params), parse_mode = 'html', reply_markup = markup)
        except: pass

    def edit(self, message, text, markup = None, params = {}, photo = None):
        if markup:
            if type(markup) == type([]): markup = self.build(markup, params)
        if photo:
            media = InputMedia("photo", photo, self.format(text, params), "html")
            try: return self.bot.edit_message_media(media, message.chat.id, message.message_id, reply_markup = markup)
            except:
                self.delete(message)
                return self.send_photo(message.chat.id, photo, text, markup, params)
        else:
            try: return self.bot.edit_message_text(self.format(text, params), message.chat.id, message.message_id, parse_mode = 'html', reply_markup = markup, disable_web_page_preview = True)
            except: 
                try:
                    self.delete(message)
                    return self.send(message.chat.id, text, markup, params)
                except: pass

    def edit_markup(self, message, markup, params = {}):
        if markup:
            if type(markup) == type([]): markup = self.build(markup, params)
        try: return self.bot.edit_message_reply_markup(message.chat.id, message.message_id, reply_markup = markup)
        except Exception as e: print(e)                    

    def delete(self, message):
        try: self.bot.delete_message(message.chat.id, message.message_id)
        except: pass

    def send_tag(self, id, tag, markup = None, params = {}, photo = None):
        text = self.get_text(tag)
        return self.send(id, text, markup, params, photo)

    def edit_tag(self, message, tag, markup = None, params = {}, photo = None):
        text = self.get_text(tag)
        return self.edit(message, text, markup, params, photo)

class BotThread(Thread):
    def __init__(self, engine, bot, time = 30): 
        self.bot = bot
        self.engine = engine
        self.time = time
        Thread.__init__(self)
    def run(self): 
        while True:
            try: self.bot.polling()
            except Exception as e:
                self.engine.log(e)
            sleep(self.time)    