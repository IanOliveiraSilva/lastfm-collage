import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

import plotly.graph_objs as go
import requests
import os
from dotenv import load_dotenv
from PIL import Image
import numpy as np
import base64
import urllib.request

import matplotlib
matplotlib.use('Agg')
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects

import textwrap


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',
                        'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css',
                        'https://use.fontawesome.com/releases/v5.8.1/css/all.css']


class LastFmDashboard:
    def __init__(self, api_key):
        self.api_key = api_key
        self.app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
        self.app.layout = html.Div([
            html.H1(
                'Last.fm Collage', 
                style={
                    'textAlign': 'center', 
                    'padding': '20px', 
                    'fontWeight':'bold',
                    'color': 'black',
                    'borderRadius': '15px', 
                }
            ),

            html.Div(
    children=[
        dcc.Input(
            id='username-input', 
            type='text', 
            placeholder='Enter your Last.fm username', 
            style={
                'width': '50%', 
                'height': '50px',
                'fontSize': '20px',
                'padding': '10px',
                'borderRadius': '15px',
                'border': '1px solid #7a4bd8',
                'outline': 'none',
                'boxShadow': '0px 0px 5px 1px #5229b1'
            }),
        html.Br(),
        html.Br(),
        dcc.Dropdown(
            id='period-input',
            options=[
                {'label': '7 days', 'value': '7day'},
                {'label': '1 month', 'value': '1month'},
                {'label': '3 months', 'value': '3month'},
                {'label': '6 months', 'value': '6month'},
                {'label': '12 months', 'value': '12month'}
            ],
            placeholder='Period: ',
            style={
                'width': '50%', 
                'fontSize': '20px',
                'borderRadius': '15px',
            }
        ),
        html.Br(),
        html.Button(
            'Generate Collage', 
            id='generate-button',
            n_clicks=0,
            style={
                'width': '50%', 
                'backgroundColor': '#a16dfe', 
                'fontSize': '20px', 
                'color': 'white', 
                'border': 'none', 
                'padding': '1px', 
                'textDecoration': 'none', 
                'margin': '4px 2px', 
                'cursor': 'pointer', 
                'borderRadius': '12px', 
                'boxShadow': '0 2px #999'
            }),
            html.Br(),
            html.Img(
                            id='collage-image',
                            style={
                                'Width': '874px',
                                'Height': '874px',
                            }
                        ),
            html.A(
            html.Button(
                children=[
                    html.I(className="fas fa-download")
                ],
                id='download-button',
                className="btn btn-primary mt-3"
            ),
            href='collage.png',
            download="collage.png",
        ),
    ],
    style={
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center'
    }
),

                html.Div(
                    children=[
                        
                    ],
                    id='top-albums-graph', 
                    style={
                        'padding': '20px', 
                        'margin': '20px', 
                        'fontSize': '15px',
                        'borderRadius': '15px',
                        'display': 'flex',
                        'justifyContent': 'center',
                        'alignItems': 'center',
                        'height': '874px',
                        'width': '874px'
                    }
                ),
        ])
        self.app.callback(
            Output('collage-image', 'src'),
            [Input('generate-button', 'n_clicks')],
            [Input('username-input', 'value')],
            [Input('period-input', 'value')]
        )(self.update_output)

    def get_json_data(self, method, user, period):
        url = f"http://ws.audioscrobbler.com/2.0/?method={method}&user={user}&api_key={self.api_key}&period={period}&format=json"
        response = requests.get(url)
        return response.json()

    def update_output(self, n_clicks, username, period):
        if n_clicks > 0:
            self.create_collage(username, period, '3x3')
            encoded_image = base64.b64encode(open('collage.png', 'rb').read()).decode('ascii')
            return 'data:image/png;base64,{}'.format(encoded_image)

    def create_collage(self, user, period, size='3x3'):
        method = "user.gettopalbums"
        data = self.get_json_data(method, user, period)
        placeholder_img_url = "https://lastfm.freetls.fastly.net/i/u/174s/2a96cbd8b46e442fc41c2b86b821562f.png"

        size_dict = {'3x3': (3, 3), '4x4': (4, 4), '5x5': (5, 5), '6x6': (6, 6)}
        n_rows, n_cols = size_dict.get(size, (3, 3))

        fig, axs = plt.subplots(n_rows, n_cols, figsize=(5*n_rows, 5*n_cols), facecolor='#000000')

        plt.suptitle(f'Top albums from {user} ({period})', color='white', fontsize=20, fontweight='bold', 
                    path_effects=[path_effects.Stroke(linewidth=3, foreground='black'), path_effects.Normal()], y=0.87)

        for i, ax in enumerate(axs.flat):
            if i < len(data['topalbums']['album']):
                artist = data['topalbums']['album'][i]
                img_url = artist['image'][-1]['#text'] if artist['image'][-1]['#text'] else placeholder_img_url

                with urllib.request.urlopen(img_url) as url:
                    img = np.array(Image.open(url))
                
                ax.imshow(img)
                ax.axis('off')

                fancybox = patches.FancyBboxPatch((0,0),1,1, boxstyle="round,pad=0.02", linewidth=2, edgecolor="white", facecolor='none', transform=ax.transAxes)
                ax.add_patch(fancybox)

                # Wrap the album name to fit within the image
                album_name = textwrap.fill(artist['name'], width=20)  # Adjust the width as needed

                ax.text(0.5, 0.05, album_name, color='white', fontsize=14, fontweight='bold', 
                        path_effects=[path_effects.withSimplePatchShadow(offset=(2, -2), shadow_rgbFace='black', alpha=0.7)],
                        transform=ax.transAxes, ha='center')

                ax.text(0.05, 0.85, artist['playcount'], color='white', fontsize=14 ,fontweight='bold', 
                        path_effects=[path_effects.withSimplePatchShadow(offset=(2, -2), shadow_rgbFace='black', alpha=0.7)],
                        transform=ax.transAxes, va='top')

            else:
                ax.axis('off') 

        plt.subplots_adjust(wspace=0, hspace=0)
        plt.savefig('collage.png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("API_KEY")
    dashboard = LastFmDashboard(api_key)
    dashboard.app.run_server(debug=True, host='0.0.0.0', port=os.getenv('PORT', 8050))
