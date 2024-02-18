# -*- coding: utf-8 -*-
# Copyright (c) CDU

"""Model Docstrings

"""
import datetime
import random
import sqlite3
import textwrap
from typing import TypeVar

T = TypeVar("T")


class Field:
    __mapping__ = {
        int: "INTEGER",
        str: "TEXT",
        float: "REAL",
        bytes: "BLOB",
        None: "NULL",
        datetime.datetime: "DATATIME"
    }

    def __init__(self, __type=None,
                 primary_key=False,
                 default=None,
                 unique=False,
                 ddl="",
                 enable_null=False,
                 *args, **kwargs):
        self._type = __type

        self._primary_key = primary_key
        self._enable_null = enable_null
        self._name = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if self._name is not None:
            raise AttributeError("name has been set")
        self._name = value

    def __repr__(self):
        _type = repr(self._type)[8:-2] if self._type is not None else "None"
        return f"{self.__class__.__name__}({_type})"

    def create_table(self):
        return " ".join(filter(None, [
            self._name,
            self.__mapping__[self._type],
            "PRIMARY KEY AUTOINCREMENT" if self._primary_key else None,
            "NOT NULL" if not self._enable_null else None
        ]))


class ModelType(type):
    def __new__(cls, name, base, attrs):
        # print(cls, name, base, attrs)
        if name == "Model":
            return type.__new__(cls, name, base, attrs)
        mappings = {}
        for k, v in attrs.items():
            if isinstance(v, Field):
                v.name = k
                mappings[k] = v
        for k in mappings.keys():
            attrs.pop(k)
        if "__table_name__" not in attrs or not attrs["__table_name__"]:
            attrs["__table_name__"] = name.lower()
        attrs['__mappings__'] = mappings
        return type.__new__(cls, name, base, attrs)

    def __repr__(self):
        self: "Model"
        return f"{self.__name__}(Model):\n" + "\n".join(
            f"  {k} = {v}" for k, v in self.__mappings__.items()
        )


class Model(metaclass=ModelType):
    __table_name__: str
    __mappings__: dict[str, Field]
    __temp__: bool = False

    __database__: "Database" = None

    def __init__(self, insert=True, **kwargs):
        self.columns = self.__mappings__.keys()
        self.sql = self.insert()
        self.__row__ = kwargs
        if insert:
            print(self.sql, kwargs)
            self.__database__.cursor.execute(self.sql, kwargs)

    def __getattribute__(self, item):
        if item in super().__getattribute__("__mappings__"):
            return self.__row__[item]
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if key in super().__getattribute__("__mappings__"):
            self.__database__.execute(
                f"UPDATE {self.__table_name__} SET {key} = {value} WHERE id = {self.__row__['id']}")
            self.__row__[key] = value
        super().__setattr__(key, value)

    def __repr__(self):
        return f"<{self.__class__.__name__}({', '.join(self.columns)})>"

    @classmethod
    def connect_db(cls, db: "Database"):
        cls.__database__ = db

    @classmethod
    def disconnect_db(cls):
        cls.__database__ = None

    @classmethod
    def insert(cls, *args, **kwargs):
        values = ", ".join([f":{k}" for k in cls.__mappings__.keys()])
        return f"INSERT INTO {cls.__table_name__} VALUES ({values})"

    @classmethod
    def delete(cls, *args, **kwargs):
        cls.__database__.cursor.execute(
            f"DELETE FROM {cls.__table_name__} WHERE id=:id;", kwargs
        )

    @classmethod
    def delete_all(cls):
        return f"DELETE FROM {cls.__table_name__};"

    @classmethod
    def create_table(cls):
        cols = ",\n".join(map(lambda x: x.create_table(), cls.__mappings__.values()))
        cols = textwrap.indent(cols, "  ")
        if cls.__temp__:
            return f"CREATE TEMPORARY TABLE IF NOT EXISTS {cls.__table_name__} (\n{cols}\n);"
        return f"CREATE TABLE IF NOT EXISTS {cls.__table_name__} (\n{cols}\n);"


class Database:
    def __init__(self, database=":memory:"):
        self.db = sqlite3.connect(database)
        self.cursor = self.db.cursor()

    def connect(self, *args):
        for model in args:
            print(model.create_table())
            self.cursor.execute(model.create_table())
            model.connect_db(self)

    def select(self, model: T) -> list[T]:
        self.cursor.execute(f"SELECT * FROM {model.__table_name__};")
        return [model(insert=False, **dict(zip(model.__mappings__.keys(), row))) for row in self.cursor.fetchall()]

    def execute(self, sql: str):
        print("EXEC", sql)


class Example(Model):
    __table_name__ = ""

    id = Field(int, primary_key=True)
    content = Field(str)
    length = Field(int)
    dt = Field(datetime.datetime)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.id}, {self.content}, {self.length}), {self.dt}>"


if __name__ == "__main__":
    db = Database("dev.db")
    db.connect(Example)
    for _ in range(10):
        Example(content="Hello, World!", length=13, id=None,
                dt=datetime.datetime.now())

    for i in db.select(Example):
        if random.random() > 0.5:
            ent = "abc"
        if random.random() > 0.5:
            i.delete(id=i.id)
        print(i)

    print("-----------------------")
    for i in db.select(Example):
        print(i)
    db.db.commit()
