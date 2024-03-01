import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

import plotly.graph_objs as go
import requests
import os
import concurrent.futures
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

import aiohttp
import asyncio
import joblib

import textwrap


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',
                        'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css',
                        'https://use.fontawesome.com/releases/v5.8.1/css/all.css']


class LastFmDashboard:
    def __init__(self, api_key):
        self.api_key = api_key
        self.image_cache = {}
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
        dcc.Dropdown(
            id='size-input',
            options=[
                {'label': '3x3', 'value': '3x3'},
                {'label': '4x4', 'value': '4x4'},
                {'label': '5x5', 'value': '5x5'}
            ],
            placeholder='Size: ',
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
            html.A(
                
            ),
            html.Img(
                            id='collage-image',
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
            [Input('period-input', 'value')],
            [Input('size-input', 'value')]
        )(self.update_output)

    def get_json_data(self, method, user, period, limit):
        url = f"http://ws.audioscrobbler.com/2.0/?method={method}&user={user}&api_key={self.api_key}&period={period}&limit={limit}&format=json"
        response = requests.get(url)
        print(response.elapsed)
        return response.json()

    def update_output(self, n_clicks, username, period, size):
        if n_clicks > 0:
            self.create_collage(username, period, size)
            encoded_image = base64.b64encode(open('collage.png', 'rb').read()).decode('ascii')
            return 'data:image/png;base64,{}'.format(encoded_image)

    def get_image(self, img_url):
        if img_url in self.image_cache:
            return self.image_cache[img_url]

        with urllib.request.urlopen(img_url) as url:
            img = np.array(Image.open(url))
        self.image_cache[img_url] = img
        return img

    def create_collage(self, user, period, size):
        method = "user.gettopalbums"
        size_dict = {'3x3': (9, 9), '4x4': (16, 16), '5x5': (25, 25), '6x6': (36, 36)}
        limit, _ = size_dict.get(size, (9, 9))
        data = self.get_json_data(method, user, period, limit)
        albums = data['topalbums']['album']
        placeholder_img_url = "https://lastfm.freetls.fastly.net/i/u/174s/2a96cbd8b46e442fc41c2b86b821562f.png"

        size_dict = {'3x3': (3, 3), '4x4': (4, 4), '5x5': (5, 5), '6x6': (6, 6)}
        n_rows, n_cols = size_dict.get(size, (3, 3))

        fig = plt.figure(figsize=(4*n_rows, 4*n_cols), facecolor='#000000')

        plt.suptitle(f'Top albums from {user} ({period})', color='white', fontsize=20, fontweight='bold', 
                    path_effects=[path_effects.Stroke(linewidth=3, foreground='black'), path_effects.Normal()], y=0.87)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            album_images = list(executor.map(self.get_image, [album['image'][-1]['#text'] if album['image'][-1]['#text'] else placeholder_img_url for album in albums]))

        for i in range(n_rows * n_cols):
            ax = fig.add_subplot(n_rows, n_cols, i+1)
            if i < len(albums):
                artist = albums[i]
                img = album_images[i]
                
                ax.imshow(img)
                ax.axis('off')

                fancybox = patches.FancyBboxPatch((0,0),1,1, boxstyle="round,pad=0.02", linewidth=2, edgecolor="white", facecolor='none', transform=ax.transAxes)
                ax.add_patch(fancybox)
                
                album_name = textwrap.fill(artist['name'], width=20)

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

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("API_KEY")
    dashboard = LastFmDashboard(api_key)
    dashboard.app.run_server(debug=True, host='0.0.0.0', port=os.getenv('PORT', 8050))
