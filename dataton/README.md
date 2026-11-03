# Дашборд: леса, пожары и животный мир БПТ

## Запуск
    pip install -r requirements.txt
    python app.py        # откройте http://127.0.0.1:8050

Данные уже подготовлены в папке data/. Чтобы пересобрать их из архива:
    python prepare_data.py "<папка Леса и животные>"

## Состав
- app.py — дашборд (Dash + Plotly): 2 карты, 8 диаграмм, 9 элементов управления, выводы и пояснительная записка
- prepare_data.py — преобразование исходных таблиц в CSV и координаты точек
- data/ — forestry.csv, hunting.csv, wildlife.csv, fish.csv
- assets/style.css — оформление


.\venv\Scripts\python -m pip install -r requirements.txt
python -m venv venv



