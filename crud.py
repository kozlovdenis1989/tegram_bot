import sqlalchemy
from sqlalchemy.orm import sessionmaker
from models import Base, Users, Words, UsersWords

import json
import os

from random import sample
from settings import DSN


# создаем сессию
engine = sqlalchemy.create_engine(DSN)
Session = sessionmaker(bind=engine)
db = Session()


   
def search_in_db(model, **filters):
    """
    Функция для поиска записей.

    :param model: модель 
    :param filters: поля и их значения для добавляемой записи
    :return: объект добавленной записи
    """
    try:
        records = db.query(model).filter_by(**filters).all()  
        return records  
    except Exception as e:
        return False
        

def add_to_db(model, **kwargs):
    """
    Функция для добавления записи в базу данных.

    :param model: модель 
    :param kwargs: поля и их значения для добавляемой записи
    :return: объект добавленной записи
    """
    try:
        record = model(**kwargs)  
        db.add(record)  
        db.commit()  
        return record 
    except Exception as e:
        db.rollback()  
        raise e


def delete_from_db(model, **filters):
    """
    Функция для удаления записи из базы данных по фильтрам.

    :param model: модель 
    :param filters: фильтры для поиска записи
    :return: количество удаленных записей
    """
    try:
        record = db.query(model).filter_by(**filters).first() 
        if record:
            db.delete(record) 
            db.commit()  
            return 1 
        return 0  
    except Exception as e:
        db.rollback()  
        raise e



def register_user(chat_id):
    """
    Функция для регистрации нового пользователя.

    :param chat_id: идентификатор чата
    """
    user = db.query(Users).filter_by(chat_id=chat_id).first()
    if not user:
        new_user = Users(chat_id=chat_id)
        db.add(new_user)
        db.commit()


def create_tables():
    '''
    Функция создания и удаления таблиц в бд
    '''
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    


def create_data():
    '''
    Функция заполнения начальными данными из json
    '''
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "data.json")

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        for field in data['fields']:
            print(f'Добавлено: {add_to_db(Words, **field)}')
            

def my_words_id(chat_id):
    """
    Функция для регистрации нового пользователя.

    :param chat_id: идентификатор чата
    :return: список идентификаторов пользовательских слов
    """
    user = search_in_db(Users, chat_id=chat_id)

    if not user:
        return False
    
    return [word.id_word for word in search_in_db(UsersWords, id_user=user[0].id)]
   

def check_lang(word):
    """
    Функция для регистрации нового пользователя.

    :param word:  слово
    :return: ru если слово русское
             en если английское
             False если смешаноое или со спецсимволами
    """
    lan = []
    for sumb in word:
        code = ord(sumb.lower())
        if code >= 1072 and code <= 1103:
            lan.append('ru')
        elif code >= 97 and code <= 122:
            lan.append('en')
        else:
            return False
    if 'ru' in lan and 'en' in lan:
        return False
    elif 'ru' in lan:
        return 'ru'
    else:
        return 'en'        
            


def del_my_words(chat_id, word):
    """
    Функция для удаления пользовательских слов.

    :param chat_id: идентификатор чата
    :param word:  слово
    :return: список список удаленных  пользовател слов
             False если язык не определен или слов нет у пользователя
    """
    word = word.lower()
    lan = check_lang(word)

    if lan == "ru":
        word = search_in_db(Words, ru=word)
    elif lan == 'en':
        word = search_in_db(Words, en=word)
    else:
        return False

    if word:
        if word[0].id in my_words_id(chat_id):
            return delete_from_db(Words, id = word[0].id)
    else:
        
        return False



def get_4_words(chat_id):
    """
    Функция для генерации случайных слов из общих и пользовательских.

    :param chat_id: идентификатор чата
    :return: слово из бд и список из 3 слов из бд
    """
    my_words = []
    words = my_words_id(chat_id)

    try:
        data = search_in_db(Words, common=True)
    except Exception as e:
        print(e)

    if words:  
        for id_word in words:
            word = search_in_db(Words, id=id_word )
            my_words.append(*word)

        data = data + my_words

    print(f'всего {len(data)}. моих {len(my_words)}')    
    words_all = sample(data, 4)
    wor = [[word.ru, word.en] for word in words_all]

    return wor[0], wor[1:]


def add_word(chat_id, russian_word, english_word):
    """
    Функция для добавления пользовательских слов.

    :param chat_id: идентификатор чата
    :russian_word:  слово на русском
    :english_word:  слово на английском
    :return: добавленый обЪект в случае успеха
             False в случае ошибки
    """
    words = {'ru': russian_word.lower(), 'en': english_word.lower(), 'common': False}

    try: 
        word = add_to_db(Words, **words)
        user = search_in_db(Users, chat_id = chat_id)
        if not user:
            print('перезапусти бота и введи /start')
        user_word = {'id_user': user[0].id, 'id_word': word.id}

        return add_to_db(UsersWords, **user_word)
         

    except Exception as e:
        print(e)
        return False
    
    
    



if __name__ == '__main__':

   
    # user_id = search_in_db(db, Users, chat_id = 5175957601)
    # print(user_id[0])
    # my_words_id(5175957601)
    # get_4_words(5175957601)
    # del_my_words(5175957601, 'qwerty', 'ru')
    print(check_lang('фы '))