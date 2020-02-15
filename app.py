import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from load_data import get_dataframe

df = get_dataframe()

# remove fucking spam posts
df.drop(df[df.price > 10000000].index, inplace=True)
tdf = df[['state', 'price']].groupby('state').mean()


def model_brand_df():
    dd = df.groupby(['model', 'manufacturer'], as_index=False).count().sort_values('Unnamed: 0')
    dd.rename(columns={'Unnamed: 0': 'count'}, inplace=True)
    return dd[dd['count'] > 2000]


def count_by_manufacturer(ddf):
    dic = ddf.groupby('manufacturer').count()['Unnamed: 0'].to_dict()
    return {'x': list(dic.keys()), 'y': list(dic.values())}


external_stylesheets = ['static/app.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'داشبرد تحلیلی خودرو'

wk_days = [
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday',
]


def generate_submission_choro(states):
    tdf = df
    if states:
        tdf = tdf[tdf.state.apply(lambda x: x.upper() in states)]

    return {
        'data': [
            {**count_by_manufacturer(tdf), 'type': 'bar', 'name': 'SF'},
        ],
        'layout': {
            'title': 'تعداد آگهی‌های ثبت شده به ازای هر تولید‌کننده'
        }
    }


def generate_submission_time_hm(states):
    hm = []
    ddf = df
    if states:
        ddf = df[df.state.apply(lambda x: x.upper() in states)]

    for i in range(24):
        hm_df = ddf[ddf.hour == i].groupby('day').count()['image_url']
        hm.append(hm_df)

    hm_df = pd.concat(hm, axis=1)

    y = list(wk_days)

    trace = dict(
        type="heatmap",
        z=hm_df.to_numpy(),
        x=list(f"{i}:00" for i in range(24)),
        y=y,
        colorscale=[[0, "#71cde4"], [1, "#ecae50"]],
        reversescale=True,
        showscale=True,
        xgap=2,
        ygap=2,
        colorbar=dict(
            len=0.7,
            ticks="",
            title="Submissions",
            titlefont=dict(family="Gravitas One", color="#515151"),
            thickness=15,
            tickcolor="#515151",
            tickfont=dict(family="Open Sans, sans serif", color="#515151"),
        ),
    )

    title = f'زمان ارسال آگهی در ایالات {states} بر حسب روز و ساعت'

    layout = dict(
        title=dict(
            text=title,
            font=dict(family="Open Sans, sans-serif", size=15, color="#515151"),
        ),
        font=dict(family="Sahel, Open Sans, sans-serif", size=13),
        automargin=True,
        dir='rtl',
    )

    return {"data": [trace], "layout": layout}


def generate_odometer_price_sctr(model):
    return {
        'data': [dict(
            x=df[df.model == model].odometer,
            y=df[df.model == model].price,
            mode='markers+line'
        )],
        'layout': dict(
            title=dict(
                text='قیمت / کارکرد',
                font=dict(family="Open Sans, sans-serif", size=15, color="#515151"),
            ),
            font=dict(family="Sahel, Open Sans, sans-serif", size=13),
            automargin=True,
            dir='rtl',
        )
    }


app.layout = html.Div(className='container', children=[
    html.Div(id='head-row', children=[
        html.H1(children='داشبرد تحلیلی بازار خودرو آمریکا', dir='rtl'),
        html.H4(children='بر اساس داده‌ی منتشر شده از سایت CraigsList', dir='rtl'),
        html.A(dir='rtl', target='_blank', href='/static/blog.html', children=html.H5(children='توضیحات بیشتر در بلاگ')),
    ]),
    dcc.Loading(children=dcc.Graph(id='submission_count')),
    html.Div(
        id="top-row",
        className="row",
        children=[
            html.Div(
                id="map_geo_outer",
                className="six columns",
                # avg arrival/dep delay by destination state
                children=dcc.Loading(children=dcc.Graph(id="choropleth", figure={"data": [go.Choropleth(
                    locations=list(tdf.index.str.upper()),  # Spatial coordinates
                    z=list(tdf['price'].astype(float)),  # Data to be color-coded
                    locationmode='USA-states',  # set of locations match entries in `locations`
                    colorscale='Reds',
                    colorbar_title="USD",
                )], "layout": dict(
                    title=dict(
                        text='میانگین قیمت بر حسب ایالت',
                        font=dict(family="Open Sans, sans-serif", size=15, color="#515151"),
                    ),
                    margin=dict(l=20, r=20, b=20, pad=5),
                    automargin=False,
                    clickmode="event+select",
                    geo=go.layout.Geo(
                        scope="usa", projection=go.layout.geo.Projection(type="albers usa")
                    ),
                )})),
            ),
            html.Div(
                dir='rtl',
                className='six columns',
                id="dropdown-select-outer",
                children=[
                    html.Div(
                        [
                            html.P("نوع خودرو را انتخاب کنید"),
                            dcc.Loading(children=dcc.Dropdown(
                                id="dropdown-select",
                                options=[
                                    {'label': str(model), 'value': str(model)} for model in list(df.model.unique())
                                ],
                                value=list(df.model.unique())[0],
                            )),
                        ],
                        className="selector",
                    ),
                    html.Div(
                        id="bottom-row",
                        className="twelve columns",
                        children=[
                            html.Div(
                                id='sctr_outer',
                                children=dcc.Loading(children=dcc.Graph(id='odometer_price_sctr'))
                            )
                        ]
                    )
                ],
            ),
        ],
    ),
    html.Div(
        id="mid-row",
        className="row",
        children=[
            html.Div(
                id="submissions_by_day_hm_outer",
                className="six columns",
                children=dcc.Loading(children=dcc.Graph(id="submission_time_hm")),
            ),
            html.Div(
                id="models_by_brand_sunburst",
                className="six columns",
                children=[
                    dcc.Loading(children=dcc.Graph(id="model_by_brand", figure=px.sunburst(
                        model_brand_df(),
                        path=['manufacturer', 'model'],
                        values='count',
                    )))],
            ),
        ],
    ),
])


@app.callback(
    Output('odometer_price_sctr', 'figure'),
    [Input("dropdown-select", "value")]
)
def update_sctr(model):
    return generate_odometer_price_sctr(model)


@app.callback(
    Output("submission_time_hm", "figure"),
    [Input("choropleth", "clickData"), Input("choropleth", "figure")],
)
def update_hm(choro_click, choro_figure):
    if choro_click is not None:
        states = []
        for point in choro_click["points"]:
            states.append(point["location"])

        return generate_submission_time_hm(states)
    else:
        return generate_submission_time_hm([])


@app.callback(
    Output("submission_count", "figure"),
    [Input("choropleth", "clickData"), Input("choropleth", "figure")],
)
def update_choro(choro_click, choro_figure):
    if choro_click is not None:
        states = []
        for point in choro_click["points"]:
            states.append(point["location"])
            return generate_submission_choro(states)
    else:
        return generate_submission_choro([])


if __name__ == '__main__':
    app.run_server(debug=True)
