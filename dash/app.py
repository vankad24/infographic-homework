# -*- coding: utf-8 -*-
"""Дашборд Gapminder на Dash: 4 диаграммы, 6 элементов управления."""
from dash import Dash, html, dcc, callback, Output, Input, no_update
import plotly.express as px
import pandas as pd

# ---------- Данные ----------
URL = 'https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv'
df = pd.read_csv(URL)

# Числовые меры (русские подписи для интерфейса)
MEASURES = {
    'pop': 'Население',
    'lifeExp': 'Продолжительность жизни',
    'gdpPercap': 'ВВП на душу населения',
}
measure_options = [{'label': v, 'value': k} for k, v in MEASURES.items()]
LOG_MEASURES = {'pop', 'gdpPercap'}  # для них удобна логарифмическая шкала

countries = sorted(df.country.unique())
years = sorted(df.year.unique())
YEAR_MIN, YEAR_MAX = int(years[0]), int(years[-1])

# ---------- Приложение ----------
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server  # нужен для gunicorn (Render / PythonAnywhere)

card = {'padding': '10px'}

app.layout = html.Div([
    html.H1('Gapminder: дашборд', style={'textAlign': 'center'}),

    # ---- Блок 1: линейный график ----
    html.Div([
        html.Div([
            html.Label('1. Страны (можно выбрать несколько)'),
            dcc.Dropdown(countries, ['Canada', 'Russia'], multi=True,
                         id='country-dropdown'),
        ], className='six columns'),
        html.Div([
            html.Label('2. Мера по оси Y (линейный график)'),
            dcc.Dropdown(measure_options, 'pop', clearable=False,
                         id='line-y'),
        ], className='six columns'),
    ], className='row', style=card),
    dcc.Graph(id='line-chart'),
    html.P('Кликните по точке на линейном графике — выберется год '
           'для остальных диаграмм (кросс-фильтр).',
           style={'textAlign': 'center', 'color': 'gray'}),

    # ---- 6-й элемент управления: год ----
    html.Div([
        html.Label('6. Год (меняется кликом по линейному графику или ползунком)'),
        dcc.Slider(YEAR_MIN, YEAR_MAX, step=1, value=2007, id='year-slider',
                   marks={y: str(y) for y in range(YEAR_MIN, YEAR_MAX + 1, 5)},
                   tooltip={'placement': 'bottom', 'always_visible': True}),
    ], style={'padding': '10px 10px 30px 10px'}),

    # ---- Блок 2: пузырьковая диаграмма ----
    html.Div([
        html.Div([
            html.Label('3. Ось X'),
            dcc.Dropdown(measure_options, 'gdpPercap', clearable=False,
                         id='bubble-x'),
        ], className='four columns'),
        html.Div([
            html.Label('4. Ось Y'),
            dcc.Dropdown(measure_options, 'lifeExp', clearable=False,
                         id='bubble-y'),
        ], className='four columns'),
        html.Div([
            html.Label('5. Радиус пузырька'),
            dcc.Dropdown(measure_options, 'pop', clearable=False,
                         id='bubble-size'),
        ], className='four columns'),
    ], className='row', style=card),
    dcc.Graph(id='bubble-chart'),

    # ---- Блок 3: топ-15 и круговая ----
    html.Div([
        html.Div(dcc.Graph(id='top15-chart'), className='six columns'),
        html.Div(dcc.Graph(id='pie-chart'), className='six columns'),
    ], className='row'),
], style={'maxWidth': '1400px', 'margin': '0 auto'})


# ---------- Callbacks ----------
@callback(
    Output('line-chart', 'figure'),
    Input('country-dropdown', 'value'),
    Input('line-y', 'value'),
)
def update_line(selected, measure):
    dff = df[df.country.isin(selected or [])].sort_values('year')
    fig = px.line(dff, x='year', y=measure, color='country', markers=True,
                  labels={'year': 'Год', measure: MEASURES[measure],
                          'country': 'Страна'})
    fig.update_layout(clickmode='event', hovermode='closest')
    return fig


# Кросс-фильтр: клик по линейному графику -> год в ползунке
@callback(
    Output('year-slider', 'value'),
    Input('line-chart', 'clickData'),
    prevent_initial_call=True,
)
def pick_year(click):
    if not click:
        return no_update
    return int(click['points'][0]['x'])


@callback(
    Output('bubble-chart', 'figure'),
    Input('year-slider', 'value'),
    Input('bubble-x', 'value'),
    Input('bubble-y', 'value'),
    Input('bubble-size', 'value'),
)
def update_bubble(year, x, y, size):
    dff = df[df.year == year].dropna(subset=[x, y, size])
    fig = px.scatter(
        dff, x=x, y=y, size=size, color='continent', hover_name='country',
        size_max=60, log_x=x in LOG_MEASURES, log_y=y in LOG_MEASURES,
        title=f'Пузырьковая диаграмма, {year} г.',
        labels={x: MEASURES[x], y: MEASURES[y], size: MEASURES[size],
                'continent': 'Континент'})
    return fig


@callback(
    Output('top15-chart', 'figure'),
    Input('year-slider', 'value'),
)
def update_top15(year):
    dff = df[df.year == year].nlargest(15, 'pop')
    fig = px.bar(dff, x='country', y='pop', color='continent',
                 title=f'Топ-15 стран по населению, {year} г.',
                 labels={'country': 'Страна', 'pop': 'Население',
                         'continent': 'Континент'})
    fig.update_xaxes(categoryorder='total descending')
    return fig


@callback(
    Output('pie-chart', 'figure'),
    Input('year-slider', 'value'),
)
def update_pie(year):
    dff = df[df.year == year].groupby('continent', as_index=False)['pop'].sum()
    return px.pie(dff, names='continent', values='pop',
                  title=f'Население по континентам, {year} г.')


if __name__ == '__main__':
    app.run(debug=True)
