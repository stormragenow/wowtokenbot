from datetime import datetime
from dbClasses import *

global token_price_history
global users_history


def database_start():
    try:
        psql_db.connect()
        print(f"{datetime.now():}connect database")
    except IndexError:
        psql_db.connect()
        _create_tables()
        print(f"{datetime.now():}connect database and create table")
        return


def _create_tables():
    print(f"{datetime.now():}create tables")
    Users.create_table()
    Token_price_history.create_table()


def add_user(id_usr, region=None):
    database_start()
    print(f"{datetime.now():}add user on database")
    if region:
        row = Users(
            id=id_usr,
            region=region
        )
        try:
            row.save(force_insert=True)
        except IndexError:
            row.save(only=[Users.region])

    psql_db.close()


def update_region_users(id_usr, region):
    database_start()
    row = Users.update(region=region).where(Users.id == id_usr)
    row.execute()

    psql_db.close()


def add_token_price_history(id_prc, region, price):
    database_start()

    row = Users(
        id=id_prc,
        region=region.lower().strip(),
        price=price
    )
    row.save()
    psql_db.close()


def get_user_info(id_usr):
    database_start()
    print(f"{datetime.now():} get user info of database")
    global users_history
    users_history = (Users.select(Users).where(Users.id == id_usr))
    users_history_all = []
    for usr in users_history:
        users_history_all += [usr.region, usr.id]
    psql_db.close()
    return users_history_all


def get_token_price_history(region, id_prc=None):
    database_start()
    global token_price_history
    token_price_history = Token_price_history.select().where(Users.id == id_prc.strip()).where(
        Users.region == region.strip()).get()
    psql_db.close()
    return token_price_history



