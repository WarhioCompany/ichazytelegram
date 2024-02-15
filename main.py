from db_scripts.db import *

with open('cat.jpg', 'rb') as file:
    array = file.read()
add_challenge('Шаурмяу', 'заверни кота в шаурму', 0, '20/02/2024', array, False, coins_prize=10)
with open('ichazy.png', 'rb') as file:
    array = file.read()
add_challenge('Chazy', "chazy's cool", 0, '20/02/2024', array, False, coins_prize=25)
with open('gigachad.jpg', 'rb') as file:
    array = file.read()
add_challenge('Gigachad', 'стань сигмой', 0, '20/02/2024', array, False, coins_prize=25)