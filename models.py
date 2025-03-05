import sqlalchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String, Column, Integer, VARCHAR, ForeignKey, Boolean, BIGINT



class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    chat_id = Column(BIGINT, unique=True)

    def __str__(self):
        return f'{self.id}'



class Words(Base):
    __tablename__ = "words"

   
    id = Column(Integer, primary_key=True)
    ru = Column(String(length=40), unique=True)
    en = Column(String(length=40), unique=True)
    common = Column(Boolean)

    def __str__(self):
        return f'{self.id} |  {self.ru}  | {self.en}'
    


class UsersWords(Base):
    __tablename__ = "users_words"

    id = Column(Integer, primary_key=True)
    id_user = Column(Integer, ForeignKey('users.id', ondelete= 'CASCADE'), nullable=False)
    id_word = Column(Integer, ForeignKey('words.id', ondelete= 'CASCADE'), nullable=False)

    def __str__(self):
        return f'{self.id} |  {self.id_user} | {self.id_word}'




