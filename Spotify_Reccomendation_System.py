import numpy as np
import pandas as pd

from spotify_utils import get_playlist_df
from spotify_utils import get_track_features
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from sklearn.preprocessing import StandardScaler

from spotify_recs import get_distance_recs_playlist_3
from spotify_recs import create_playlist
import json

# would Ideally like to add a language flag
def main():
    file = open('credentials.json')
    credentials = json.load(file)
    file.close()

    id_client = credentials["client_id"]
    id_client_secret = credentials["client_secret"]
    auth_manager = SpotifyClientCredentials(client_id = id_client, 
                                            client_secret = id_client_secret)

    sp = spotipy.Spotify(auth_manager=auth_manager)

    num_features = ['popularity', 'danceability', 'energy', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']

    #data = pd.read_csv("spotify_scaled.csv")

    data = pd.read_csv("spotify_new.csv")

    data_num = data[num_features]
    data_labels = data.drop(columns=num_features)

    scaler = StandardScaler()
    scale_fit = scaler.fit(data_num)

    data_numerical = pd.DataFrame(scale_fit.transform(data_num),columns=num_features)

    while True:
        try: 
            print("This Program will Generate a Playlist of Reccomendations Based on a Playlist that you Enter\n")
            print("To Get the Playlist URI:")
            print("1. Go into the desired playlist and make sure the playlist is public")
            print("2. Click on the 3 horizontal dots for more options")
            print("3. Scroll down to the share option, hover over Share, press option, and click the option: Copy Spotify URI\n")
            print('Note: this program will only generate recommendations based on the first 10 songs of the playlist\n')
            input_uri = input("Please input a Spotify Playlist URI: ")
            recs = get_distance_recs_playlist_3(input_uri,data_numerical,data_labels,scale_fit,sp)
            if(input_uri=="q"):
                return 0
        except: 
            print("URI is not valid")
        else:
            break
    
    results = sp.user_playlist(user=None, playlist_id=input_uri, fields="name")
    playlist_name = results['name']

    # while True:
    #     try: 
    #         num_songs = int(input("How many songs would you like in this playist (max 50): "))
    #     except: 
    #         print("Please Input a Valid Number")
    #     else:
    #         if(num_songs<=50):
    #             break
    #         print("Please input a number less than 50")
                
    print("\nOnce You Input Your User information, the screen will show an Error. This is supposed to happen, simply copy the url and paste it back here. ")
    playlist_url = create_playlist(recs,playlist_name,id_client,id_client_secret,True)
    print("\nYour Playlist is Ready!")
    print("Here is the playlist URL: " + playlist_url)
    

main()