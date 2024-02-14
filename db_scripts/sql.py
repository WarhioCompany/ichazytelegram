import sqlite3


DATABASE_NAME = 'database'
USERS_DB = 'users'
CHALLENGES_DB = 'challenges'
USERWORKS_DB = 'userworks'
PRIZES_DB = 'prizes'


def connect():
    conn = sqlite3.connect('database.db')
    return conn.cursor()


def execute(sql):
    cur = connect()
    cur.execute(sql)
    cur.close()


def add(table_name, data):
    cur = connect()

    sql = f"INSERT INTO {table_name} ({', '.join(data.keys())}) VALUES ({', '.join(['?'] * len(data))})"

    data = cur.execute(sql, tuple(data.values()))

    cur.connection.commit()
    cur.close()
    return data


def get(table_name, select=None, where=None):
    cur = connect()

    select_query = ', '.join(select) if select else '*'
    where_query = ' AND '.join(f"{key} = '{where[key]}'" for key in where) if where else '1'
    sql = f"SELECT {select_query} FROM {table_name} WHERE {where_query}"

    result = cur.execute(sql)
    data = []
    for elem in result.fetchall():
        element = {}
        for i in range(len(result.description)):
            element[result.description[i][0]] = elem[i]
        data.append(element)

    cur.close()
    return data
