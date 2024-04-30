from db_scripts.sql import *


def create_users_table():
    sql = f""" CREATE TABLE IF NOT EXISTS {USERS_DB} (
                                                            id integer PRIMARY KEY,
                                                            name text NOT NULL,
                                                            coins int,
                                                            prizes text,
                                                            telegram_id text
                                                );"""
    execute(sql)


# is_hard: if prize is actual thing in real life this value is True, otherwise its False
# date: day/month/year 02/13/2024
def create_challenges_table():
    sql = f""" CREATE TABLE IF NOT EXISTS {CHALLENGES_DB} (
                                                            id integer PRIMARY KEY,
                                                            name text NOT NULL,
                                                            desc text,
                                                            image blob,
                                                            price int,
                                                            coins_prize int,
                                                            prize_id int,
                                                            date_to text,
                                                            work_type text,
                                                            is_hard bool
                                                    ); """
    execute(sql)


def create_works_table():
    sql = f""" CREATE TABLE IF NOT EXISTS {USERWORKS_DB} (
                                                            id integer PRIMARY KEY,
                                                            user_id int,
                                                            data blob,
                                                            challenge_id int,
                                                            date text,
                                                            type text,
                                                            like_count int,
                                                            is_approved bool
                                                    ); """
    execute(sql)


def create_prizes_table():
    sql = f""" CREATE TABLE IF NOT EXISTS {PRIZES_DB} (
                                                            id integer PRIMARY KEY,
                                                            name text
                                                    ); """
    execute(sql)


def crate_brands_table():
    sql = f""" CREATE TABLE IF NOT EXISTS {PRIZES_DB} (
                                                                id integer PRIMARY KEY,
                                                                name text
                                                        ); """
    execute(sql)


def create_tables():
    create_users_table()
    create_challenges_table()
    create_works_table()
    create_prizes_table()