# -*- coding: utf-8 -*-
"""
Дашборд «Леса, пожары и животный мир Байкальской природной территории (БПТ)».
Итоговая работа по предмету «Инфографика и визуализация данных».

Запуск:  pip install -r requirements.txt  ->  python app.py  ->  http://127.0.0.1:8050
Данные лежат в папке data/ (получены скриптом prepare_data.py из архива «Леса и животные»).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, callback, Output, Input, no_update
from plotly.subplots import make_subplots

DATA = Path(__file__).parent / 'data'

# =====================================================================
# 1. ДАННЫЕ
# =====================================================================
forest = pd.read_csv(DATA / 'forestry.csv')
hunt = pd.read_csv(DATA / 'hunting.csv')
wild = pd.read_csv(DATA / 'wildlife.csv')
fish = pd.read_csv(DATA / 'fish.csv')
fish['species'] = fish.species.replace({'Всего': 'Все виды (итого)'})

# Сопоставление лесничеств и охотничьих районов (там, где названия совпадают)
FOREST_TO_DISTRICT = {
    'Казачинско-Ленское': 'Казачинско-Ленский район', 'Качугское': 'Качугский район',
    'Ольхонское': 'Ольхонский район', 'Слюдянское': 'Слюдянский район',
    'Усольское': 'Усольский район', 'Черемховское': 'Черемховский район',
    'Шелеховское': 'Шелеховский район', 'Баяндаевское': 'Баяндаевский район',
    'Осинское': 'Осинский район', 'Иркутское': 'Иркутский район', 'Ангарское': 'Ангарский район',
    'Баргузинское': 'Баргузинский район', 'Бичурское': 'Бичурский район',
    'Джидинское': 'Джидинский район', 'Еравнинское': 'Еравнинский район',
    'Заиграевское': 'Заиграевский район', 'Закаменское': 'Закаменский район',
    'Иволгинское': 'Иволгинский район', 'Кабанское': 'Кабанский район',
    'Кижингинское': 'Кижингинский район', 'Курумканское': 'Курумканский район',
    'Кяхтинское': 'Кяхтинский район', 'Мухоршибирское': 'Мухоршибирский район',
    'Прибайкальское': 'Прибайкальский район', 'Северо-Байкальское': 'Северобайкальский район',
    'Селенгинское': 'Селенгинский район', 'Хилокское': 'Хилокский район',
    'Хоринское': 'Хоринский район', 'Красночикойское': 'Красночикойский район',
    'Петровск-Забайкальское': 'Петровск-Забайкальский район',
    'Усть-Ордынское': 'Эхирит-Булагатский район',
}
forest['district'] = forest.forestry.map(FOREST_TO_DISTRICT)

METRICS = {
    'fire_area_kha': ('Площадь пожаров', 'тыс. га'),
    'fires': ('Число пожаров', 'шт.'),
    'cut_k_m3': ('Объём рубок', 'тыс. м³'),
}
REGION_COLORS = {'Иркутская область': '#1f77b4', 'Республика Бурятия': '#d62728',
                 'Забайкальский край': '#2ca02c'}
REGIONS = list(REGION_COLORS)
YEARS_F = sorted(forest.year.unique())            # 2016–2022
YEARS_H = sorted(hunt.year.unique())              # 2013–2020
YEARS_W = sorted(wild.year.unique())              # 2015–2022
SPECIES = sorted(hunt.animal.unique())
FISH_SPECIES = sorted(fish.species.unique(), key=lambda s: (s != 'Все виды (итого)', s))
KINDS = ['Рыбы', 'Земноводные', 'Пресмыкающиеся', 'Птицы', 'Млекопитающие']

MAP_STYLE = 'open-street-map'


def style(fig, h=None):
    """Единое оформление: белый фон, русские разделители (десятичная запятая, пробел тысяч)."""
    fig.update_layout(template='plotly_white', separators=', ', margin=dict(l=40, r=20, t=60, b=40),
                      legend=dict(title_text=''), font=dict(size=13))
    if h:
        fig.update_layout(height=h)
    return fig


def sg(x, nd=1):
    """Число со знаком, десятичной запятой и typographic-минусом."""
    return f'{x:+.{nd}f}'.replace('.', ',').replace('-', '\u2212')


def fmt(x, nd=0):
    return f'{x:,.{nd}f}'.replace(',', '\u00a0').replace('.', ',')


# =====================================================================
# 2. ВЫВОДЫ (считаются из данных, чтобы цифры не расходились с диаграммами)
# =====================================================================
def fire_vs_animals(fire_year):
    """Изменение численности копытных в районах с наибольшей площадью пожаров и в остальных."""
    tot = hunt.groupby(['district', 'year'])['count'].sum().unstack()
    fa = forest[(forest.year == fire_year) & forest.district.notna()] \
        .groupby('district').fire_area_kha.sum()
    df = pd.DataFrame({'fire': fa, 'n0': tot[fire_year], 'n1': tot[fire_year + 1]}).dropna()
    df = df[df.n0 >= 200]                                   # отбрасываем районы с «нулевым» учётом
    df['chg'] = (df.n1 / df.n0 - 1) * 100
    thr = df.fire.quantile(.75)
    hi, lo = df[df.fire >= thr], df[df.fire < thr]
    return dict(df=df,
                hi=(hi.n1.sum() / hi.n0.sum() - 1) * 100,
                lo=(lo.n1.sum() / lo.n0.sum() - 1) * 100,
                rho=df.fire.corr(df.chg, method='spearman'), n=len(df))


def tourism_table():
    """Индекс экотуристической привлекательности ООПТ по данным 2022 г. (0–100)."""
    w = wild[wild.year == 2022]
    t = pd.DataFrame({
        'species': w[w.indicator == 'Всего'].groupby('area').species.sum(),
        'redbook': w[w.indicator == 'Красная книга РФ'].groupby('area').species.sum(),
        'endemic': w[w.indicator == 'Эндемичные виды'].groupby('area').species.sum(),
    })
    norm = (t - t.min()) / (t.max() - t.min())
    t['index'] = norm.mean(axis=1) * 100
    return t.sort_values('index', ascending=False)


def build_findings():
    tot = forest.groupby('year')[['fires', 'fire_area_kha', 'cut_k_m3']].sum()
    area_all = tot.fire_area_kha.sum()
    peak = tot.fire_area_kha.nlargest(2)
    by_f = forest.groupby('forestry').agg(area=('fire_area_kha', 'sum'), n=('fires', 'sum'),
                                          cut=('cut_k_m3', 'sum'), region=('region', 'first'))
    top2 = by_f.area.nlargest(2)
    most_n = by_f.n.idxmax()
    by_reg = forest.groupby('region').fire_area_kha.sum()
    cut_top = by_f.cut.idxmax()
    cut_share = by_f.cut.max() / by_f.cut.sum() * 100

    hn = hunt.groupby('year')['count'].sum()
    r16, r19, r17 = fire_vs_animals(2016), fire_vs_animals(2019), fire_vs_animals(2017)
    om = fish[(fish.species == 'Омуль')].set_index('year').catch
    al = fish[(fish.species == 'Все виды (итого)')].set_index('year').catch
    tr = tourism_table()
    lead, second = tr.index[0], tr.index[1]

    md = f"""
**1. Пожары.** За 2016–2022 гг. на БПТ пройдено огнём **{fmt(area_all, 0)} тыс. га** леса. Два года-рекордсмена —
{peak.index[0]} ({fmt(peak.iloc[0], 0)} тыс. га) и {peak.index[1]} ({fmt(peak.iloc[1], 0)} тыс. га) — дают
{fmt(peak.sum() / area_all * 100, 0)}% всей площади. Больше всего пострадали лесничества **{top2.index[0]}**
({fmt(top2.iloc[0], 0)} тыс. га) и **{top2.index[1]}** ({fmt(top2.iloc[1], 0)} тыс. га): вместе
{fmt(top2.sum() / area_all * 100, 0)}% всей выгоревшей площади. По региону лидирует {by_reg.idxmax()}
({fmt(by_reg.max(), 0)} тыс. га). Чаще всего пожары возникали в лесничестве **{most_n}** — {fmt(by_f.n.max())} случаев за 7 лет.

**2. Территория, наиболее подверженная природным катаклизмам.** Это **{top2.index[0]} лесничество** (Иркутская область):
по площади пожаров оно первое, при этом на территории ещё и ведётся интенсивная вырубка. По числу возгораний лидирует
{most_n} ({by_f.loc[most_n, 'region']}). Данных о землетрясениях в предоставленном наборе нет, поэтому вывод
сделан только по пожарам.

**3. Рубки.** Объём рубок снизился с {fmt(tot.cut_k_m3.max(), 0)} тыс. м³ ({tot.cut_k_m3.idxmax()} г.)
до {fmt(tot.cut_k_m3.iloc[-1], 0)} тыс. м³ (2022 г.), то есть на {fmt((1 - tot.cut_k_m3.iloc[-1] / tot.cut_k_m3.max()) * 100, 0)}%.
Лесничество **{cut_top}** даёт {fmt(cut_share, 0)}% всех рубок за период.

**4. Влияние пожаров на численность животных (копытные, охотничьи ресурсы).** Общая численность выросла со
{fmt(hn[2013])} (2013) до {fmt(hn[2020])} (2020). Но после пожарного сезона 2019 г. (второго по площади) в 2020 г. численность
впервые снизилась — на {fmt(abs((hn[2020] / hn[2019] - 1) * 100), 1)}%. Сравнение районов:

- после пожаров 2019 г. в районах с самой большой выгоревшей площадью (верхняя четверть) численность изменилась на
  **{sg(r19['hi'])}%**, в остальных — на **{sg(r19['lo'])}%**;
- после пожаров 2016 г.: **{sg(r16['hi'])}%** против **{sg(r16['lo'])}%** (в сильнее пострадавших районах численность упала);
- после пожаров 2017 г. разницы практически нет: {sg(r17['hi'])}% против {sg(r17['lo'])}%.

Коэффициент корреляции Спирмена между площадью пожаров и изменением численности слабый
({sg(r16['rho'], 2)} для 2016, {sg(r17['rho'], 2)} для 2017, {sg(r19['rho'], 2)} для 2019). **Вывод:** в 2016 и 2019 гг.
численность в «горевших» районах росла заметно медленнее (или падала), чем в остальных, но устойчивой статистической связи данные не
показывают — на учёт влияют также охота, методика подсчёта и погода. Утверждать, что пожары *привели* к сокращению числа
животных, по этим данным нельзя; это гипотеза для проверки на более длинных рядах.

**5. Рыбный промысел.** Вылов омуля упал с {fmt(om[2013], 0)} (2013) до {fmt(om[2022], 0)} (2022), то есть на
{fmt((1 - om[2022] / om[2013]) * 100, 0)}%; общий вылов — на {fmt((1 - al[2022] / al[2013]) * 100, 0)}%
(с {fmt(al[2013], 0)} до {fmt(al[2022], 0)}).

**6. Наиболее привлекательная территория для экотуризма** (по индексу биоразнообразия: число видов, виды Красной книги РФ,
эндемики, 2022 г.) — **{lead}** (индекс {tr.loc[lead, 'index']:.0f} из 100): всего видов — {fmt(tr.loc[lead, 'species'])},
из Красной книги РФ — {fmt(tr.loc[lead, 'redbook'])}, эндемичных — {fmt(tr.loc[lead, 'endemic'])}. На втором месте —
{second} ({tr.loc[second, 'index']:.0f}). Транспортная доступность и инфраструктура в данных отсутствуют,
поэтому индекс отражает только природную ценность территории.
"""
    return md


# =====================================================================
# 3. МАКЕТ
# =====================================================================
def ctl(label, comp):
    return html.Div([html.Label(label, className='ctl'), comp])


app = Dash(__name__, title='Байкальская природная территория: дашборд', requests_pathname_prefix="/dataton/",
    routes_pathname_prefix="/dataton/")
server = app.server

app.layout = html.Div(className='page', children=[
    html.H1('Леса, пожары и животный мир Байкальской природной территории'),
    html.P('Интерактивный дашборд: где и когда горели и вырубались леса БПТ, как менялась численность '
           'животных и какие территории наиболее ценны.', className='subtitle'),

    # ---------- Блок 1 ----------
    html.H2('1. Пожары и рубки по лесничествам'),
    html.Div([
        html.Div(ctl('Регион (можно выбрать несколько)', dcc.Checklist(
            REGIONS, REGIONS, id='regions', inputStyle={'marginRight': '6px'},
            labelStyle={'display': 'block'})), className='card col'),
        html.Div(ctl('Показатель на карте и диаграммах', dcc.RadioItems(
            [{'label': f'{n}, {u}', 'value': k} for k, (n, u) in METRICS.items()],
            'fire_area_kha', id='metric', inputStyle={'marginRight': '6px'},
            labelStyle={'display': 'block'})), className='card col'),
        html.Div(ctl('Год (также выбирается кликом по столбцу в диаграмме динамики)', dcc.Slider(
            YEARS_F[0], YEARS_F[-1], 1, value=2019, id='year',
            marks={int(y): str(y) for y in YEARS_F},
            tooltip={'placement': 'bottom', 'always_visible': False})), className='card col-wide'),
    ], className='row'),

    html.Div(id='kpis', className='row'),

    html.Div([
        html.Div([dcc.Graph(id='map-forest'),
                  html.P('Карта. Размер и цвет пузырька — выбранный показатель. Точки поставлены приблизительно '
                         '(по административным центрам), границы лесничеств в данных отсутствуют. '
                         'Кликните по пузырьку — внизу появится динамика этого лесничества.', className='note')],
                 className='card col-wide'),
        html.Div([dcc.Graph(id='top-bar'),
                  html.P('Топ-10 лесничеств по выбранному показателю за выбранный год.', className='note')],
                 className='card col'),
    ], className='row'),

    html.Div([
        html.Div([dcc.Graph(id='trend-region'),
                  html.P('Динамика по регионам. Кликните по столбцу — год переключится во всём блоке.',
                         className='note')], className='card col-wide'),
        html.Div([dcc.Graph(id='trend-forestry')], className='card col'),
    ], className='row'),

    # ---------- Блок 2 ----------
    html.H2('2. Животные и пожары'),
    html.Div([
        html.Div(ctl('Виды животных (охотничьи ресурсы)', dcc.Dropdown(
            SPECIES, SPECIES, multi=True, id='species', clearable=False)), className='card col-wide'),
        html.Div(ctl('Год учёта численности (на карте)', dcc.Slider(
            YEARS_H[0], YEARS_H[-1], 1, value=2020, id='year-h',
            marks={int(y): str(y) for y in YEARS_H})), className='card col'),
        html.Div(ctl('Год пожаров (для сравнения с изменением численности в следующем году)', dcc.Dropdown(
            [2016, 2017, 2018, 2019], 2019, id='fire-year', clearable=False)), className='card col'),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='fire-animals'),
                  html.P('Столбцы (правая ось) — площадь пожаров на всей БПТ, линии (левая ось) — численность '
                         'выбранных видов на 1 января. Данные о пожарах есть с 2016 г., о животных — по 2020 г.; '
                         'скачок 2013→2014 вероятно связан с изменением методики учёта.', className='note')],
                 className='card col-wide'),
        html.Div([dcc.Graph(id='map-animals'),
                  html.P('Карта. Численность выбранных видов по районам; координаты — центры районов.',
                         className='note')], className='card col'),
    ], className='row'),
    html.Div([html.Div([dcc.Graph(id='scatter'),
                        html.P('Каждая точка — район. Ось X — площадь пожаров в выбранном году, ось Y — '
                               'изменение численности животных к 1 января следующего года. Размер точки — '
                               'численность до пожаров. Показаны районы, где учтено не менее 200 животных.',
                               className='note')], className='card')],
             className='row'),

    # ---------- Блок 3 ----------
    html.H2('3. Биоразнообразие особо охраняемых территорий и вылов рыбы'),
    html.Div([
        html.Div(ctl('Показатель видового состава', dcc.Dropdown(
            ['Всего', 'Красная книга РФ', 'Красная книга СРФ', 'Эндемичные виды'], 'Всего',
            id='indicator', clearable=False)), className='card col'),
        html.Div(ctl('Год', dcc.Dropdown(
            [int(y) for y in YEARS_W], 2022, id='year-w', clearable=False)), className='card col'),
        html.Div(ctl('Виды рыб (вылов)', dcc.Dropdown(
            FISH_SPECIES, ['Все виды (итого)', 'Омуль', 'Плотва'], multi=True, id='fish-species')),
            className='card col-wide'),
    ], className='row'),
    html.Div([
        html.Div([dcc.Graph(id='wild-bar'),
                  html.P('Число видов по группам животных в заповедниках и национальных парках. Нули и пропуски '
                         'в исходных таблицах (например, по парку «Чикой» в 2015, 2016 и 2018 гг., по 2021 г.) — '
                         'это отсутствие данных, а не отсутствие видов.', className='note')],
                 className='card col-wide'),
        html.Div([dcc.Graph(id='tourism'),
                  html.P('Индекс = среднее трёх показателей 2022 г. (всего видов, виды Красной книги РФ, эндемики), '
                         'каждый приведён к шкале 0–100 между минимумом и максимумом по ООПТ.',
                         className='note')], className='card col'),
    ], className='row'),
    html.Div([html.Div([dcc.Graph(id='fish-line')], className='card')], className='row'),

    # ---------- Выводы и записка ----------
    html.H2('4. Выводы по результатам анализа'),
    html.Div(dcc.Markdown(build_findings()), className='card findings'),

])


# =====================================================================
# 4. CALLBACKS
# =====================================================================
def sel(regions):
    return forest[forest.region.isin(regions or [])]


@callback(Output('kpis', 'children'), Input('year', 'value'), Input('regions', 'value'))
def kpis(year, regions):
    d = sel(regions)
    cur, prev = d[d.year == year], d[d.year == year - 1]
    cards = []
    for k, (name, unit) in METRICS.items():
        v = cur[k].sum()
        txt = html.Div('нет предыдущего года', className='d')
        if len(prev):
            p = prev[k].sum()
            ch = (v / p - 1) * 100 if p else np.nan
            if not np.isnan(ch):
                txt = html.Div(f'{ch:+.0f}% к {year - 1} г.'.replace('.', ','),
                               className='d ' + ('up' if ch > 0 else 'down'))
        cards.append(html.Div([html.Div(fmt(v, 0 if k != 'fire_area_kha' else 1), className='v'),
                               html.Div(f'{name}, {unit}, {year} г.', className='l'), txt],
                              className='card kpi'))
    return cards


@callback(Output('map-forest', 'figure'), Input('year', 'value'), Input('metric', 'value'),
          Input('regions', 'value'))
def map_forest(year, metric, regions):
    name, unit = METRICS[metric]
    d = sel(regions)
    d = d[d.year == year].copy()
    d['size'] = d[metric].fillna(0).clip(lower=0) + 1e-6
    fig = px.scatter_map(d, lat='lat', lon='lon', size='size', color=metric, hover_name='forestry',
                         custom_data=['forestry'], size_max=45, zoom=4.5, center=dict(lat=53.3, lon=108.5),
                         color_continuous_scale='YlOrRd', map_style=MAP_STYLE,
                         hover_data={'size': False, 'lat': False, 'lon': False, 'region': True,
                                     metric: ':,.2f'},
                         labels={metric: f'{name}, {unit}', 'region': 'Регион'},
                         title=f'{name}, {unit} — {year} г.')
    style(fig, 560)
    fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
    return fig


@callback(Output('top-bar', 'figure'), Input('year', 'value'), Input('metric', 'value'),
          Input('regions', 'value'))
def top_bar(year, metric, regions):
    name, unit = METRICS[metric]
    d = sel(regions)
    d = d[d.year == year].nlargest(10, metric).sort_values(metric)
    fig = px.bar(d, x=metric, y='forestry', color='region', color_discrete_map=REGION_COLORS, orientation='h',
                 labels={metric: f'{name}, {unit}', 'forestry': '', 'region': 'Регион'},
                 title=f'Топ-10 лесничеств, {year} г.')
    return style(fig, 560)


@callback(Output('trend-region', 'figure'), Input('metric', 'value'), Input('regions', 'value'),
          Input('year', 'value'))
def trend_region(metric, regions, year):
    name, unit = METRICS[metric]
    d = sel(regions).groupby(['year', 'region'], as_index=False)[metric].sum()
    fig = px.bar(d, x='year', y=metric, color='region', color_discrete_map=REGION_COLORS,
                 labels={'year': 'Год', metric: f'{name}, {unit}', 'region': 'Регион'},
                 title=f'{name} по регионам БПТ, {unit}')
    fig.update_xaxes(dtick=1)
    fig.add_vline(x=year, line_dash='dot', line_color='gray')
    fig.update_layout(clickmode='event')
    return style(fig, 420)


@callback(Output('year', 'value'), Input('trend-region', 'clickData'), prevent_initial_call=True)
def pick_year(click):
    if not click:
        return no_update
    return int(click['points'][0]['x'])


@callback(Output('trend-forestry', 'figure'), Input('map-forest', 'clickData'))
def trend_forestry(click):
    name = click['points'][0]['customdata'][0] if click else 'Качугское'
    d = forest[forest.forestry == name].sort_values('year')
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=('Площадь пожаров, тыс. га', 'Число пожаров, шт.', 'Объём рубок, тыс. м³'))
    for i, (col, color) in enumerate([('fire_area_kha', '#d62728'), ('fires', '#ff7f0e'),
                                      ('cut_k_m3', '#8c564b')], start=1):
        fig.add_bar(x=d.year, y=d[col], marker_color=color, row=i, col=1, showlegend=False)
    fig.update_xaxes(dtick=1)
    fig.update_layout(title=f'Лесничество «{name}» ({"выбрано кликом" if click else "по умолчанию"})')
    return style(fig, 420)


@callback(Output('fire-animals', 'figure'), Input('species', 'value'))
def fire_animals(species):
    species = species or SPECIES
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fa = forest.groupby('year').fire_area_kha.sum().reset_index()
    fig.add_bar(x=fa.year, y=fa.fire_area_kha, name='Площадь пожаров, тыс. га', marker_color='rgba(214,39,40,.35)',
                secondary_y=True)
    d = hunt[hunt.animal.isin(species)].groupby(['year', 'animal'], as_index=False)['count'].sum()
    for a, g in d.groupby('animal'):
        fig.add_scatter(x=g.year, y=g['count'], mode='lines+markers', name=a, secondary_y=False)
    fig.update_xaxes(dtick=1, title_text='Год')
    fig.update_yaxes(title_text='Численность, особей', secondary_y=False)
    fig.update_yaxes(title_text='Площадь пожаров, тыс. га', secondary_y=True, showgrid=False)
    fig.update_layout(title='Пожары и численность животных на БПТ', hovermode='x unified')
    return style(fig, 480)


@callback(Output('map-animals', 'figure'), Input('species', 'value'), Input('year-h', 'value'))
def map_animals(species, year):
    species = species or SPECIES
    d = hunt[hunt.animal.isin(species) & (hunt.year == year)] \
        .groupby(['district', 'lat', 'lon'], as_index=False)['count'].sum()
    d['size'] = d['count'].clip(lower=0) + 1e-6
    fig = px.scatter_map(d, lat='lat', lon='lon', size='size', color='count', hover_name='district',
                         size_max=40, zoom=3.6, center=dict(lat=53.3, lon=108.5),
                         color_continuous_scale='Greens', map_style=MAP_STYLE,
                         hover_data={'size': False, 'lat': False, 'lon': False, 'count': ':,.0f'},
                         labels={'count': 'Особей'}, title=f'Численность по районам на 1 января {year} г.')
    style(fig, 480)
    fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
    return fig


@callback(Output('scatter', 'figure'), Input('fire-year', 'value'), Input('species', 'value'))
def scatter(fire_year, species):
    species = species or SPECIES
    tot = hunt[hunt.animal.isin(species)].groupby(['district', 'year'])['count'].sum().unstack()
    fa = forest[(forest.year == fire_year) & forest.district.notna()].groupby('district').fire_area_kha.sum()
    df = pd.DataFrame({'fire': fa, 'n0': tot[fire_year], 'n1': tot[fire_year + 1]}).dropna()
    df = df[df.n0 >= 200].copy()
    df['chg'] = (df.n1 / df.n0 - 1) * 100
    df = df.reset_index().rename(columns={'index': 'district'})
    rho = df.fire.corr(df.chg, method='spearman')
    fig = px.scatter(df, x='fire', y='chg', size='n0', hover_name='district', text='district', size_max=40,
                     labels={'fire': f'Площадь пожаров в {fire_year} г., тыс. га',
                             'chg': f'Изменение численности {fire_year}→{fire_year + 1}, %', 'n0': 'Особей до'},
                     title=f'Пожары {fire_year} г. и изменение численности животных (корреляция Спирмена = '
                           f'{sg(rho, 2)}, районов: {len(df)})')
    fig.update_traces(textposition='top center', textfont_size=10)
    fig.add_hline(y=0, line_dash='dot', line_color='gray')
    return style(fig, 520)


@callback(Output('wild-bar', 'figure'), Input('indicator', 'value'), Input('year-w', 'value'))
def wild_bar(indicator, year):
    d = wild[(wild.indicator == indicator) & (wild.year == year)].dropna(subset=['species'])
    if d.species.sum() == 0:
        fig = go.Figure().add_annotation(text='Для этого года и показателя в исходных данных нет значений',
                                         showarrow=False, font_size=15)
        return style(fig, 480)
    fig = px.bar(d, y='area', x='species', color='kind', orientation='h', category_orders={'kind': KINDS},
                 labels={'area': '', 'species': 'Число видов', 'kind': 'Группа'},
                 title=f'{indicator}: число видов по ООПТ, {year} г.')
    fig.update_yaxes(categoryorder='total ascending')
    return style(fig, 480)


@callback(Output('tourism', 'figure'), Input('year-w', 'value'))
def tourism(_):
    t = tourism_table().sort_values('index')
    fig = px.bar(t.reset_index(), x='index', y='area', orientation='h', color='index',
                 color_continuous_scale='Viridis', hover_data={'species': True, 'redbook': True, 'endemic': True},
                 labels={'index': 'Индекс, 0–100', 'area': '', 'species': 'Видов', 'redbook': 'Красная книга РФ',
                         'endemic': 'Эндемики'},
                 title='Индекс привлекательности для экотуризма (2022 г.)')
    fig.update_layout(coloraxis_showscale=False)
    return style(fig, 480)


@callback(Output('fish-line', 'figure'), Input('fish-species', 'value'))
def fish_line(species):
    species = species or ['Все виды (итого)']
    d = fish[fish.species.isin(species)]
    fig = px.line(d, x='year', y='catch', color='species', markers=True,
                  labels={'year': 'Год', 'catch': 'Вылов (единицы в файле не указаны)', 'species': 'Вид'},
                  title='Вылов рыбы в бассейне Байкала, 2013–2022')
    fig.update_xaxes(dtick=1)
    return style(fig, 420)


if __name__ == '__main__':
    app.run(debug=False, port=8051)
