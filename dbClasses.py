from peewee import *
from config import DB_name_postgre, USER_postgres, PASSWORD_postgres, Server_host_postgres


psql_db = PostgresqlDatabase(
    DB_name_postgre, user=USER_postgres,
    password=PASSWORD_postgres,
    host=Server_host_postgres, port=5432)


class BaseModel(Model):
    class Meta:
        database = psql_db


class Users(BaseModel):
    id = PrimaryKeyField(null=False)
    region = CharField(null=True)


class Token_price_history(BaseModel):
    id = PrimaryKeyField(null=False)
    region = CharField(max_length=25)
    price = IntegerField()
