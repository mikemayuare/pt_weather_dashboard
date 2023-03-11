import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, ctx
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import dash_extensions as de
from datetime import datetime
import requests

# set the style

load_figure_template("solar")
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
header_font = "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Cabin:wght@700&family=Lato:wght@900&display=swap"

# load necessary files
stations = pd.read_csv("./data/idstations.csv", index_col=0)
# obs_df = pd.read_csv('./data/obs_outdated.csv') # fallback dataset
metrics = [
    "intensidadeVentoKM",
    "temperatura",
    "radiacao",
    "idDireccVento",
    "humidade",
    "pressao",
]
observations_url = (
    "https://api.ipma.pt/open-data/observation/meteorology/stations/observations.json"
)


# check if there are missing values (-99) means no data
def check_nodata(X):
    return [0 if x == -99 else x for x in X]


# Set wind directions as recognizable strings
def get_direction(id):
    direction_map = {
        None: "",
        0: "without direction",
        1: "N",
        2: "NE",
        3: "E",
        4: "SE",
        5: "S",
        6: "SW",
        7: "W",
        9: "N",
    }
    return direction_map.get(id)


# build the dataframe from IPMA API
def get_stations_metrics():
    obs_r = requests.get(observations_url)
    obs_json = obs_r.json()
    obs_df = pd.DataFrame()
    obs_df = pd.concat({k: pd.DataFrame(v).T for k, v in obs_json.items()}, axis=0)
    obs_df.reset_index(inplace=True)
    obs_df["level_1"] = obs_df["level_1"].astype("int64")
    obs_df.rename(columns={"level_0": "date", "level_1": "id"}, inplace=True)
    obs_df["humidade"] = obs_df["humidade"].astype("float")
    obs_df = obs_df.merge(stations, on="id")
    obs_df[metrics] = obs_df[metrics].apply(check_nodata)
    obs_df["idDireccVento"] = obs_df["idDireccVento"].apply(get_direction)
    obs_df["temperatura"] = obs_df["temperatura"].apply(lambda x: round(x, 0))
    return obs_df


# creates barplot
def draw_barplot(local, data):
    df = data[data["local"] == local]
    fig = px.bar(
        df,
        "date",
        "temperatura",
        color="humidade",
        text_auto=True,
        # color_continuous_scale=["#682D00", "#256AFF"],
        color_continuous_scale=[
            (0, "gray"),
            (0.3, "gray"),
            (0.3, "green"),
            (0.6, "green"),
            (0.6, "#279AF1"),
            (1, "#279AF1"),
        ],
        range_color=[0, 100],
    )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Temperature (C)",
        coloraxis_colorbar_title="%Rel. Humidity",
    )
    return fig


obs_df = get_stations_metrics()


# images
termo_hot = "https://assets2.lottiefiles.com/packages/lf20_qkvneqme.json"
termo_cold = "https://assets5.lottiefiles.com/packages/lf20_vaxtjvo1.json"
wind = "https://assets7.lottiefiles.com/packages/lf20_khrclx93.json"
pressure = "https://assets9.lottiefiles.com/packages/lf20_4pku29fg.json"
options = dict(
    loop=True,
    autoplay=True,
    rendererSettings=dict(preserveAspectRatio="xMidYMid slice"),
)

# dropdown selector
dropdown = dcc.Dropdown(
    id="dropdown",
    options=stations["local"],
    value="Lisboa (Geofísico)",
    className="mb-5",
)

# text above dropdown
dropdown_header = html.P("Choose or type the weather station:")

# card with temperature info
card_temp = dbc.Card(
    [
        dbc.CardBody(
            [
                html.Div(
                    de.Lottie(
                        options=options,
                        width="50%",
                        height="50%",
                        url="",
                        id="themometer",
                    ),
                ),
                html.H1(
                    id="themometer-text",
                    children="",
                    style=dict(textSize="18rem", textAlign="center"),
                ),
            ]
        ),
    ],
)


# Initialize the dash app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.SOLAR, dbc_css, header_font],  # CSS
    meta_tags=[  # for responsiveness
        dict(
            name="viewport",
            content="width=device-width, initial-scale=1.0",
        ),
    ],
    suppress_callback_exceptions=True,
    update_title=None,
)
app.title = "Portugal weather - 24H history"

########## APP LAYOUT ###########
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                html.H1(
                    id="header",
                    children="PORTUGAL WEATHER 24H HISTORY",
                    style=dict(
                        textAlign="center",
                        fontFamily="Bebas Neue, sans-serif",
                        backgroundColor="#1E434A",
                    ),
                    className="mb-5 pt-2 pb-2",
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [dropdown_header, dropdown, card_temp], width=dict(size=3, offset=2)
                ),
                dbc.Col(
                    [
                        dcc.Graph(id="temp-bar"),
                        dcc.Interval(
                            id="weather_update",
                            interval=600 * 1000,
                            n_intervals=0,
                        ),
                    ],
                    width=dict(size=5),
                ),
            ],
            align="end",
        ),
        dbc.Row(
            [
                dbc.Col(
                    id="card-sensors",
                    width=dict(size=3, offset=2),
                ),
                dbc.Col(dcc.Graph(id="map-figure"), width=dict(size=5)),
            ],
            class_name="mt-3",
        ),
        dbc.Row(
            html.Footer(
                [
                    "Data extracted from     ",
                    html.A(
                        html.Img(
                            src="https://api.ipma.pt/img/www/ipma.17-vertical-logo.png",
                            width="60",
                            height="60",
                        ),
                        href="https://api.ipma.pt/",
                    ),
                ],
                style=dict(
                    backgroundColor="#1E434A",
                ),
                className="pt-2 pb-2 ps-5 mt-3",
            )
        ),
    ],
    fluid=True,
    class_name="dbc",
)


############# CALLBACKS #############


# change barplot location info
@app.callback(
    Output("temp-bar", "figure"),
    [Input("dropdown", "value"), Input("weather_update", "n_intervals")],
)
def update_barplot(value, n):
    trigger = ctx.triggered_id
    if trigger == "weather_update":
        global obs_df
        obs_df = get_stations_metrics()
        fig = draw_barplot(value, obs_df)

    else:
        fig = draw_barplot(value, obs_df)

    return fig


# # update dataframe
# @app.callback(Output("temp-bar", "figure"), [Input("weather_update", "n_intervals")])
# def bar_plot_update(n):
#     global obs_df
#     obs_df = get_stations_metrics()
#     fig = location(dropdown.__getattribute__("value"))
#     return fig


# updates temperature in the dbc card
@app.callback(Output("themometer-text", "children"), [Input("dropdown", "value")])
def update_temperature(value):
    df = obs_df[obs_df["local"] == value]
    temperature = df[df["date"] == df["date"].max()]["temperatura"].values[0]
    if temperature == None:
        return "No data at the moment"
    return f"{temperature}°C"


# change thermometer image depending of the temperature
@app.callback(Output("themometer", "url"), [Input("dropdown", "value")])
def update_temperature(value):
    df = obs_df[obs_df["local"] == value]
    temperature = df[df["date"] == df["date"].max()]["temperatura"].values[0]
    if temperature is None:
        return termo_hot
    elif temperature > 17:
        return termo_hot
    else:
        return termo_cold


# sensors callback
@app.callback(Output("card-sensors", "children"), [Input("dropdown", "value")])
def update_sensors(value):
    df = obs_df[obs_df["local"] == value]
    df_max_date = df[df["date"] == df["date"].max()]
    card_sensors = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            de.Lottie(
                                options=options,
                                width="50%",
                                height="50%",
                                url=wind,
                                id="wind",
                            )
                        ),
                        dbc.Col(
                            f"{df_max_date['intensidadeVentoKM'].values[0]} km/h {df_max_date['idDireccVento'].values[0]}",
                            style=dict(fontSize="2rem"),
                        ),
                    ],
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            de.Lottie(
                                options=options,
                                width="50%",
                                height="50%",
                                url=pressure,
                                id="pressure",
                            )
                        ),
                        dbc.Col(
                            f"{df_max_date['pressao'].values[0]} hPa",
                            style=dict(fontSize="2rem"),
                        ),
                    ],
                    align="center",
                    class_name="g-0",
                ),
                dbc.Row(id="clock", style=dict(fontSize="4rem"), justify="center"),
                dcc.Interval(id="clock-update", interval=1000, n_intervals=0),
            ]
        )
    )
    return card_sensors


@app.callback(Output("clock", "children"), [Input("clock-update", "n_intervals")])
def clock_update(n):
    now = datetime.now()
    return now.strftime("%H:%M:%S")


# map figure update
@app.callback(Output("map-figure", "figure"), [Input("dropdown", "value")])
def update_mapbox(value):
    df = stations[stations["local"] == value]
    map = px.scatter_mapbox(
        stations,
        lon="lon",
        lat="lat",
        center=dict(lon=float(df["lon"]), lat=float(df["lat"])),
        zoom=11,
        mapbox_style="carto-positron",
    )
    map.update_traces(marker_color="red", marker_size=8)
    return map


if __name__ == "__main__":
    app.run_server(debug=True)
