import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from random import shuffle
import time

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from crud import create_tables, create_data, get_4_words, add_word, register_user, del_my_words, check_lang, get_users_chats, answer
from settings import TOKEN
from models import Users

user_states = {}  # Хранение состояний пользователей (ожидание ввода)
user_last_word = 'f' # Хранение последнего слова



bot = telebot.TeleBot(TOKEN)
print('Start bot')

# Класс генерации случайных слов
class Words():
    def __init__(self, chat_id):
        self.word_true, self.words_false = get_4_words(chat_id=chat_id)
        print(self.word_true, self.words_false)




# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    start_message = f"Привет! Я бот для изучения английского\nТы можешь отгадывать слова, пролистывать, добавлять свои и \nудалять их. Давай учиться?"
    Word = Words(message.chat.id)
    
    bot.send_message(message.chat.id, start_message, reply_markup=ReplyKeyboardRemove())
    register_user(chat_id=message.chat.id)  # создаем пользователя
    send_start_menu(message)
    


# Меню
def send_start_menu(message):
    global Word
    global user_last_word

    # Если слово было в пред итерации то комплект слов изменяется
    Word = Words(message.chat.id)
    while True:
        if user_last_word == Word.word_true[1]:
            Word = Words(message.chat.id)
        else:
            user_last_word = Word.word_true[1]
            break

    # Создаем клавиатуру 
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_true = KeyboardButton(Word.word_true[1])
    btns = [KeyboardButton(f'{word[1]}') for word in Word.words_false] + [btn_true]
    # перемешиваем слова
    shuffle(btns)
    btn_next = KeyboardButton("Пропустить")
    btn_add = KeyboardButton("Добавить слово")
    btn_del = KeyboardButton("Удалить слово")
    # Добавляем кнопки в клавиатуру
    markup.add(*btns, btn_next, btn_add, btn_del)

    # Отправляем сообщение с прикрепленной клавиатурой
    bot.send_message(message.chat.id, f'Напиши перевод слова: {Word.word_true[0]}', reply_markup=markup)



# Обработчик пропска слова, возврат к start_menu
@bot.message_handler(func=lambda message: message.text == "Пропустить")
def skip_user(message):
    bot.send_message(message.chat.id, "пропускаем")
    send_start_menu(message)


# Обработчик добавления нового слова
@bot.message_handler(func=lambda message: message.text == "Добавить слово")
def add_word_step1(message):
    user_states[message.chat.id] = "waiting_for_russian"            # сохраняем состояние
    bot.send_message(message.chat.id, "Введите слово на русском:", reply_markup=ReplyKeyboardRemove())

# обработчик состояния, ввод слова на русском
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_russian") # проверка состояния
def add_word_step2(message):
    
    # проверка языковой при надлежности слова
    if check_lang(message.text) != 'ru':
        bot.send_message(message.chat.id, f'Слово {message.text} содержит латинские буквы или спецсимволы')
        return
    
    # сохраняем состояние
    user_states[message.chat.id] = {"russian": message.text, "state": "waiting_for_english"}
    bot.send_message(message.chat.id, "Теперь введите перевод на английский:")

# обработчик состояния, ввод на английском
@bot.message_handler(func=lambda message: isinstance(user_states.get(message.chat.id), dict) and user_states[message.chat.id].get("state") == "waiting_for_english")
def add_word_step3(message):

    # проверка на языковую принадлежность и ошибки
    if check_lang(message.text) != 'en':
        bot.send_message(message.chat.id, f'Слово {message.text} содержит русские буквы или спецсимволы')
        return
    
    russian_word = user_states[message.chat.id]["russian"]
    english_word = message.text

    # Добавление слова в базу, если его там еще нет, возврат в start_menu
    if add_word(chat_id= message.chat.id, russian_word = russian_word, english_word=english_word):
        bot.send_message(message.chat.id, f"Слово '{russian_word}' – '{english_word}' добавлено в базу!")
    else:
        bot.send_message(message.chat.id, f"Слово '{russian_word}' – '{english_word}' уже существует!")

    del user_states[message.chat.id]  # Очистка состояния
    send_start_menu(message)



# обработчик удаления своего слова
@bot.message_handler(func=lambda message: message.text == "Удалить слово")
def del_word_user(message):
    user_states[message.chat.id] = "delete"    # сохраняем состояние
    bot.send_message(message.chat.id, "Введите слово для удаления:", reply_markup=ReplyKeyboardRemove())

# продолжение обработчика...
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'delete')
def del_word_step(message):

    # проверка на яыковую принадлежность и ошибки
    word = message.text
    if not check_lang(word):
        bot.send_message(message.chat.id, f'Слово {word} содержит оба языка или спецсимволы')
        return

    # проверка на принадлежность слова пользователю и удаление, в случае успеной проверки
    if del_my_words(message.chat.id, word):
        bot.send_message(message.chat.id, f'Слово {word} удалено из вашего списка')
        send_start_menu(message)
    else:
        bot.send_message(message.chat.id, f'Вы не добавляли слово {word}')
        send_start_menu(message)
   

# обработчик ответов
@bot.message_handler(func=lambda message: True)
def greet_user(message):
    # при перезапуске бота может возникнуть ошиька, так как меню остается
    try:
        Word.word_true[1]
    except:
        send_start_menu(message)

    # проверка слова
    if message.text == Word.word_true[1]:
        bot.send_message(message.chat.id, answer('right'))
        send_start_menu(message)
    else:
        bot.send_message(message.chat.id, f"{answer('wrong')}")
        time.sleep(0.2)
        bot.send_message(message.chat.id, f"Слово : {Word.word_true[0]}")



def send_start_to_self():
    time.sleep(1) 
    chats = get_users_chats() 
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  
    btn_start = KeyboardButton("/start")
    markup.add(btn_start)
    if chats:
        for chat in chats:
            bot.send_message(chat, 'pres start', reply_markup=markup)  # Отправляем команду самому себе



# Запуск бота
if __name__ == '__main__':
    send_start_to_self()
    bot.polling(none_stop=True)
    
    
   