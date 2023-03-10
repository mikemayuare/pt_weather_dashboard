import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import dash_extensions as de
from datetime import datetime, date
import requests

# set the style

load_figure_template("darkly")
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
obs_r = requests.get(observations_url)
obs_json = obs_r.json()
global obs_df
obs_df = pd.DataFrame()
obs_df = pd.concat({k: pd.DataFrame(v).T for k, v in obs_json.items()}, axis=0)
obs_df.reset_index(inplace=True)
obs_df["level_1"] = obs_df["level_1"].astype("int64")
obs_df.rename(columns={"level_0": "date", "level_1": "id"}, inplace=True)
obs_df["humidade"] = obs_df["humidade"].astype("float")
obs_df = obs_df.merge(stations, on="id")


def check_nodata(X):
    return [0 if x == -99 else x for x in X]


obs_df[metrics] = obs_df[metrics].apply(check_nodata)

# images
termo_hot = "https://assets2.lottiefiles.com/packages/lf20_qkvneqme.json"
termo_cold = "https://assets5.lottiefiles.com/packages/lf20_vaxtjvo1.json"
wind = "https://assets7.lottiefiles.com/packages/lf20_qdgvz2hn.json"
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
hidden = html.Div(hidden="hidden", id="hidden")

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

########## place holder for the card below temperature
card_sensors = dbc.Card(
    [
        dbc.CardBody(
            [
                html.Ul(
                    [
                        html.Li("item 1"),
                        html.Li("item 2"),
                        html.Li("item 3"),
                        html.Li("item 4"),
                    ]
                )
            ]
        ),
    ],
)

# Initialize the dash app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY, dbc_css, header_font],  # CSS
    meta_tags=[  # for responsiveness
        dict(
            name="viewport",
            content="width=device-width, initial-scale=1.0",
        ),
    ],
)


########## APP LAYOUT ###########
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                html.H1(
                    id="header",
                    children="PORTUGAL WEATHER",
                    style=dict(
                        textAlign="center",
                        fontFamily="Bebas Neue, sans-serif",
                        backgroundColor="#3D4142",
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
                            interval=3600 * 500,
                            n_intervals=0,
                        ),
                        hidden,
                    ],
                    width=dict(size=5),
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    card_sensors,
                    width=dict(size=3, offset=2),
                ),
                dbc.Col(dcc.Graph(id="map-figure"), width=dict(size=5)),
            ]
        ),
    ],
    fluid=True,
    class_name="dbc",
)

############# CALLBACKS #############


# update dataframe
@app.callback(Output("hidden", "children"), [Input("weather_update", "n_intervals")])
def bar_plot_update(n):
    observations_url = "https://api.ipma.pt/open-data/observation/meteorology/stations/observations.json"
    obs_r = requests.get(observations_url)
    obs_json = obs_r.json()
    global obs_df
    obs_df = pd.DataFrame()
    obs_df = pd.concat({k: pd.DataFrame(v).T for k, v in obs_json.items()}, axis=0)
    obs_df.reset_index(inplace=True)
    obs_df["level_1"] = obs_df["level_1"].astype("int64")
    obs_df.rename(columns={"level_0": "date", "level_1": "id"}, inplace=True)
    obs_df["humidade"] = obs_df["humidade"].astype("float")
    obs_df = obs_df.merge(stations, on="id")
    obs_df[metrics] = obs_df[metrics].apply(check_nodata)
    return None


# change barplot location info
@app.callback(Output("temp-bar", "figure"), [Input("dropdown", "value")])
def location(value):
    df = obs_df[obs_df["local"] == value]
    df["temperatura"] = df["temperatura"].apply(lambda x: round(x, 0))
    fig = px.bar(
        df,
        "date",
        "temperatura",
        color="humidade",
        text_auto=True,
        color_continuous_scale=["#682D00", "#256AFF"],
    )
    return fig


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
# @app.callback(Output("map-figure", "figure"), [Input("dropdown", "value")])


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
