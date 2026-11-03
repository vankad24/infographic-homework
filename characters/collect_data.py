# -*- coding: utf-8 -*-
"""Сбор характеристик персонажей Honkai: Star Rail.
Источник: открытый репозиторий игровых данных Mar-7th/StarRailRes (GitHub),
который содержит данные, извлечённые из клиента игры. Результат: hsr_characters.csv
"""
import requests
import pandas as pd

BASE = 'https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/index_min/'
LEVEL = 80  # максимальный уровень персонажа (6-е повышение)


def get(lang, name):
    r = requests.get(f'{BASE}{lang}/{name}.json', timeout=30)
    r.raise_for_status()
    return r.json()


chars_en = get('en', 'characters')
chars_ru = get('ru', 'characters')
promo = get('en', 'character_promotions')

rows = []
for cid, c in chars_en.items():
    p = promo.get(cid)
    if not p:
        continue
    v = p['values'][6]  # характеристики после 6-го повышения
    row = {
        'id': int(cid),
        'name': c['name'],
        'name_ru': chars_ru.get(cid, {}).get('name', c['name']),
        'rarity': c['rarity'],
        'path': c['path'],
        'element': c['element'],
        'max_energy': c['max_sp'],
    }
    for stat in ('hp', 'atk', 'def', 'spd', 'taunt', 'crit_rate', 'crit_dmg'):
        row[stat] = round(v[stat]['base'] + v[stat]['step'] * (LEVEL - 1), 2)
    rows.append(row)

df = pd.DataFrame(rows).sort_values('id').reset_index(drop=True)
# Путешественник представлен несколькими записями - подпишем их стихией
mask = df.name.str.contains('Trailblazer') | df.name.str.contains('{NICKNAME}')
df.loc[mask, 'name'] = 'Trailblazer (' + df.loc[mask, 'path'] + '/' + df.loc[mask, 'element'] + ')'
df.loc[mask, 'name_ru'] = 'Первопроходец (' + df.loc[mask, 'path'] + '/' + df.loc[mask, 'element'] + ')'
df = df.drop_duplicates('name').reset_index(drop=True)  # мужская/женская версии Путешественника
PATH_RU = {'Warrior': 'Разрушение', 'Rogue': 'Охота', 'Mage': 'Эрудиция', 'Shaman': 'Гармония', 'Warlock': 'Небытие',
           'Knight': 'Сохранение', 'Priest': 'Изобилие', 'Memory': 'Память', 'Elation': 'Ликование'}
EL_RU = {'Physical': 'Физический', 'Fire': 'Огонь', 'Ice': 'Лёд', 'Thunder': 'Молния', 'Wind': 'Ветер',
         'Quantum': 'Квантовый', 'Imaginary': 'Мнимый'}
df['path_ru'] = df.path.map(PATH_RU)
df['element_ru'] = df.element.map(EL_RU)
df.to_csv('hsr_characters.csv', index=False, encoding='utf-8-sig')
df.to_excel('hsr_characters.xlsx', index=False)
print(df.shape); print(df.head(10).to_string())
