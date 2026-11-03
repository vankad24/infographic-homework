import pandas as pd, json
df = pd.read_csv('hsr_characters.csv')
data = df[['name','name_ru','rarity','path_ru','element_ru','hp','atk','def','spd','taunt','max_energy']].to_dict('records')
html = open('template.html', encoding='utf-8').read().replace('__DATA__', json.dumps(data, ensure_ascii=False))
open('hsr_dashboard.html', 'w', encoding='utf-8').write(html)
