from db_scripts.db import *
from os import listdir
from os.path import isfile, join


def temp(name):
    with open(name, 'rb') as file:
        array = file.read()
    add_challenge(name, 'описание ' + name, 0, '20/02/2024', array, False, 'image', coins_prize=10)


onlyfiles = [f for f in listdir('.') if isfile(join('.', f)) and (f.endswith('png') or f.endswith('jpg'))]
for file in onlyfiles:
    temp(file)
