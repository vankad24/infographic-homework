# -*- coding: utf-8 -*-
"""Дашборд Honkai: Star Rail на Dash - сравнение характеристик персонажей.
Запуск: python app_hsr.py  (данные: hsr_characters.csv из collect_data.py)"""
from dash import Dash, html, dcc, callback, Output, Input, State, ctx
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

df = pd.read_csv('hsr_characters.csv')
STATS = {'hp': 'Здоровье (HP)', 'atk': 'Атака', 'def': 'Защита', 'spd': 'Скорость',
         'taunt': 'Провокация', 'max_energy': 'Энергия ульты'}
RADAR = ['hp', 'atk', 'def', 'spd', 'taunt']
# цвета стихий: ярко-узнаваемые, читаются на тёмном фоне
EL_COL = {'Физический': '#C9C9C9', 'Огонь': '#FF6B4A', 'Лёд': '#4FC3F7', 'Молния': '#C77DFF',
          'Ветер': '#2EE6A8', 'Квантовый': '#7B7FFF', 'Мнимый': '#F7E05A'}
BG, PANEL, TXT = '#12141C', '#1C1F2B', '#E8E8F0'
stat_opts = [{'label': v, 'value': k} for k, v in STATS.items()]
char_opts = [{'label': f'{r.name_ru} ({r.rarity}★)', 'value': r['name']} for _, r in df.iterrows()]
name_ru = dict(zip(df.name, df.name_ru))

def style(fig, h=420):
    fig.update_layout(template='plotly_dark', paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                      font_color=TXT, height=h, margin=dict(t=60, l=50, r=20, b=40))
    return fig

app = Dash(__name__)
server = app.server
box = {'background': PANEL, 'padding': '12px', 'borderRadius': '10px', 'margin': '8px'}
dd = {'color': '#111'}
app.layout = html.Div([
    html.H1('Honkai: Star Rail — сравнение персонажей', style={'textAlign': 'center'}),
    html.Div([
        html.Div([html.Label('1. Персонажи для сравнения (до 6)'),
                  dcc.Dropdown(char_opts, ['Kafka', 'Silver Wolf', 'Acheron', 'Firefly'],
                               multi=True, id='chars', style=dd)], style={**box, 'flex': 3}),
        html.Div([html.Label('2. Характеристика (столбцы и тепловая карта)'),
                  dcc.Dropdown(stat_opts, 'atk', clearable=False, id='stat', style=dd)],
                 style={**box, 'flex': 1}),
        html.Div([html.Label('3. Радар'),
                  dcc.RadioItems([{'label': ' % от максимума', 'value': 'pct'},
                                  {'label': ' абсолютные', 'value': 'abs'}], 'pct', id='norm')],
                 style={**box, 'flex': 1}),
    ], style={'display': 'flex'}),
    html.Div([
        html.Div([dcc.Graph(id='radar')], style={**box, 'flex': 1}),
        html.Div([dcc.Graph(id='bar')], style={**box, 'flex': 1}),
    ], style={'display': 'flex'}),
    html.Div([
        html.Div([html.Label('4. Ось X'), dcc.Dropdown(stat_opts, 'spd', clearable=False, id='sx', style=dd)],
                 style={'flex': 1, 'padding': '4px'}),
        html.Div([html.Label('5. Ось Y'), dcc.Dropdown(stat_opts, 'hp', clearable=False, id='sy', style=dd)],
                 style={'flex': 1, 'padding': '4px'}),
        html.Div([html.Label('6. Стихии'), dcc.Dropdown(list(EL_COL), list(EL_COL), multi=True,
                                                         id='els', style=dd)], style={'flex': 2, 'padding': '4px'}),
        html.Div([html.Label('7. Редкость'), dcc.Checklist([4, 5], [4, 5], inline=True, id='rar')],
                 style={'flex': 1, 'padding': '4px'}),
    ], style={**box, 'display': 'flex'}),
    html.Div([
        html.Div([dcc.Graph(id='scatter')], style={**box, 'flex': 3}),
        html.Div([dcc.Graph(id='heat')], style={**box, 'flex': 2}),
    ], style={'display': 'flex'}),
    html.P('Клик по точке на диаграмме рассеяния добавляет персонажа в сравнение', style={'textAlign': 'center', 'color': '#888'}),
], style={'background': BG, 'color': TXT, '--Dash-Text-Strong': TXT,
          'fontFamily': 'Segoe UI, Arial', 'padding': '10px'})


@callback(Output('chars', 'value'), Input('scatter', 'clickData'), State('chars', 'value'),
          prevent_initial_call=True)
def add_char(click, cur):
    cur = list(cur or [])
    name = click['points'][0]['customdata'][0] if click else None
    if name and name not in cur and len(cur) < 6:
        cur.append(name)
    return cur


@callback(Output('radar', 'figure'), Input('chars', 'value'), Input('norm', 'value'))
def update_radar(chars, norm):
    d = df[df.name.isin((chars or [])[:6])]
    fig = go.Figure()
    for _, r in d.iterrows():
        vals = [r[s] / df[s].max() * 100 if norm == 'pct' else r[s] for s in RADAR]
        fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=[STATS[s] for s in RADAR] + [STATS[RADAR[0]]],
                                      name=r.name_ru, fill='toself', opacity=0.45,
                                      line_color=EL_COL[r.element_ru]))
    fig.update_layout(title='Профиль характеристик (радар)', polar=dict(bgcolor=PANEL))
    return style(fig)


@callback(Output('bar', 'figure'), Input('chars', 'value'), Input('stat', 'value'))
def update_bar(chars, stat):
    d = df[df.name.isin(chars or [])].sort_values(stat, ascending=False)
    fig = px.bar(d, x='name_ru', y=stat, color='element_ru', color_discrete_map=EL_COL, text_auto='.0f',
                 title=f'{STATS[stat]}: выбранные персонажи',
                 labels={'name_ru': '', stat: STATS[stat], 'element_ru': 'Стихия'})
    fig.add_hline(y=df[stat].mean(), line_dash='dot', annotation_text='среднее по всем')
    return style(fig)


@callback(Output('scatter', 'figure'), Input('sx', 'value'), Input('sy', 'value'),
          Input('els', 'value'), Input('rar', 'value'), Input('chars', 'value'))
def update_scatter(x, y, els, rar, chars):
    d = df[df.element_ru.isin(els or []) & df.rarity.isin(rar or [])].copy()
    d['sel'] = d.name.isin(chars or [])
    fig = px.scatter(d, x=x, y=y, color='element_ru', color_discrete_map=EL_COL, symbol='path_ru',
                     hover_name='name_ru', custom_data=['name'], opacity=0.85,
                     hover_data={'path_ru': True, 'rarity': True},
                     title=f'{STATS[y]} и {STATS[x]}: все персонажи',
                     labels={x: STATS[x], y: STATS[y], 'element_ru': 'Стихия', 'path_ru': 'Путь'})
    fig.update_traces(marker=dict(size=11, line=dict(width=0)))
    s = d[d.sel]  # выбранные - белая обводка и подпись
    fig.add_trace(go.Scatter(x=s[x], y=s[y], mode='markers+text', text=s.name_ru, textposition='top center',
                             marker=dict(size=18, color='rgba(0,0,0,0)', line=dict(color='white', width=2)),
                             showlegend=False, hoverinfo='skip'))
    return style(fig, 480)


@callback(Output('heat', 'figure'), Input('stat', 'value'))
def update_heat(stat):
    p = df.pivot_table(index='path_ru', columns='element_ru', values=stat, aggfunc='mean')
    fig = px.imshow(p, color_continuous_scale='Viridis', aspect='auto', text_auto='.0f',
                    title=f'Среднее: {STATS[stat]} по Пути и Стихии',
                    labels={'color': STATS[stat], 'x': 'Стихия', 'y': 'Путь'})
    return style(fig, 480)


if __name__ == '__main__':
    app.run(debug=True, port=8052)
