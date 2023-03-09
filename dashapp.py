import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import dash_extensions as de
from jupyter_dash import JupyterDash
from datetime import datetime, date
import requests

# set the style

load_figure_template("bootstrap")
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
header_font = "https://fonts.googleapis.com/css2?family=Lato:wght@900&display=swap"

# load necessary files
stations = pd.read_csv("./data/idstations.csv", index_col=0)
# observations_url = (
#     "https://api.ipma.pt/open-data/observation/meteorology/stations/observations.json"
# )
# obs_r = requests.get(observations_url)
# obs_json = obs_r.json()
# obs_df = pd.DataFrame()
# obs_df = pd.concat({k: pd.DataFrame(v).T for k, v in obs_json.items()}, axis=0)
# obs_df.reset_index(inplace=True)
# obs_df["level_1"] = obs_df["level_1"].astype("int64")
# obs_df.rename(columns={"level_0": "date", "level_1": "id"}, inplace=True)
# obs_df["humidade"] = obs_df["humidade"].astype("float")
# obs_df = obs_df.merge(stations, on='id')
# metrics = ['intensidadeVentoKM', 'temperatura', 'radiacao', 'idDireccVento',
#            'precAcumulada',	'intensidadeVento',	'humidade',	'pressao']
# obs_df.dropna(subset=metrics)

obs_df = pd.read_csv("./data/obs_outdated.csv")


# images
termo_hot = "https://assets2.lottiefiles.com/packages/lf20_qkvneqme.json"
termo_cold = "https://assets5.lottiefiles.com/packages/lf20_vaxtjvo1.json"
options = dict(
    loop=True,
    autoplay=True,
    rendererSettings=dict(preserveAspectRatio="xMidYMid slice"),
)

# card with temperature info
card = dbc.Card(
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
                    children="24 grados",
                    style=dict(textSize="18rem", textAlign="center"),
                ),
            ]
        ),
    ],
)

# barplot with temperatures
temp_df = obs_df[obs_df["id"] == 1210881]
# figure = px.bar(temp_df, "date", "temperatura", color="humidade")

# dropdown selector
dropdown = dcc.Dropdown(
    id="dropdown",
    options=stations["local"],
    value="Lisboa, Amoreiras (LFCL)",
    className="mb-5",
)


# Initialize the dash app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc_css, header_font],
    meta_tags=[
        dict(
            name="viewport",
            content="width=device-width, initial-scale=1.0",
        ),
    ],
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                html.H1(
                    id="header",
                    children="PORTUGAL WEATHER",
                    style=dict(
                        textAlign="center",
                        fontFamily="Lato, sans-serif",
                        backgroundColor="#FFA552",
                    ),
                    className="mb-5 pt-2 pb-2",
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col([dropdown, card], width=dict(size=4, offset=2)),
                dbc.Col(dcc.Graph(id="temp-bar"), width=5),
            ],
            align="center",
        ),
    ],
    fluid=True,
)


@app.callback(Output("temp-bar", "figure"), [Input("dropdown", "value")])
def location(value):
    df = obs_df[obs_df["local"] == value]
    fig = px.bar(df, "date", "temperatura", color="humidade")
    return fig


@app.callback(Output("themometer-text", "children"), [Input("dropdown", "value")])
def update_temperature(value):
    df = obs_df[obs_df["local"] == value]
    temperature = df[df["date"] == df["date"].max()]["temperatura"].values[0]
    if temperature == np.nan:
        return "There is not data available"
    return f"{temperature}°C"


@app.callback(Output("themometer", "url"), [Input("dropdown", "value")])
def update_temperature(value):
    df = obs_df[obs_df["local"] == value]
    temperature = df[df["date"] == df["date"].max()]["temperatura"].values[0]
    if temperature > 17:
        return termo_hot
    else:
        return termo_cold


if __name__ == "__main__":
    app.run_server(debug=True)
