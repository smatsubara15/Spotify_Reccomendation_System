import numpy as np
import pandas as pd

from spotify_utils import get_playlist_df
from spotify_utils import get_track_features
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from sklearn.preprocessing import StandardScaler

from spotify_recs import get_distance_recs_playlist_1
from spotify_recs import get_distance_recs_playlist_2
from spotify_recs import get_distance_recs_playlist_gower
from spotify_recs import create_playlist
import json

import warnings
warnings.filterwarnings("ignore")

# would ideally like to add a language flag

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

    #data = pd.read_csv("spotify_new.csv")
    #data = pd.read_csv("spotify_no_children.csv")
    data = pd.read_csv('spoty_new_w_langflag.csv').drop(columns =['Unnamed: 0','level_0'])
    data = data[data.track_genre!='children'].reset_index()

    data_num = data[num_features]

    scaler = StandardScaler()
    scale_fit = scaler.fit(data_num)

    print("This Program will Generate a Playlist of Reccomendations Based on a Playlist that you Enter\n")


    while True: 
        english = input("Would you like most songs to be in English? (Y/N) ")
        
        if(english.lower()=='y'):
            data = data[data.eng_flag==1]
            data.drop(columns=['level_0'],inplace=True)
            data = data.reset_index()
            break

        elif(english.lower()=='n'):
            break

        else:
            print("Invalid Input")
    
    data.drop(columns=['eng_flag'],inplace=True)

    final_numerical = data[num_features]
    final_labels = data.drop(columns=num_features)

    # song features are getting different scaled values
    final_numerical = pd.DataFrame(scale_fit.transform(final_numerical),columns=num_features)
    
    while True: 
        genre_based = input("\nWould you like the playlist to be based on Genre? (Y/N) ")
        if(genre_based.lower()=='n'):
            break
        
        elif(genre_based.lower()=='y'):
            final_numerical['Genre'] = final_labels.track_genre
            final_labels.drop(columns=['track_genre'],inplace=True)
            break

        else:
            print("Invalid Input")

    # run this line if we are doing the Gower distance
    #final_labels.drop(columns=['track_genre'],inplace=True)

    while True:
        try: 
            print("\nTo Get the Playlist URI:")
            print("1. Go into the desired playlist and make sure the playlist is public")
            print("2. Click on the 3 horizontal dots for more options")
            print("3. Scroll down to the share option, hover over Share, press option, and click the option: Copy Spotify URI\n")
            print('Note: this program will only generate recommendations based on the first 10 songs of the playlist.')
            print('Because of this, you may get songs that are already in your playlist that are after the first 10.\n')
            input_uri = input("Please input a Spotify Playlist URI: ")
            if(genre_based.lower()=='y'):
                recs = get_distance_recs_playlist_gower(input_uri,final_numerical,final_labels,scale_fit,sp)
            else:
                recs = get_distance_recs_playlist_2(input_uri,final_numerical,final_labels,scale_fit,sp)
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
                
    #print("\nOnce You Input Your User information, the screen will show an Error. This is supposed to happen, simply copy the url and paste it back here. ")

    # Drop songs that are either remastered, adding a feature, or a different verson than the original
    # This keeps the most similar song and drops the second instance of the song
    recs['title_stripped'] = recs['track_name'].str.split('(').str[0]
    recs['title_stripped'] = recs['title_stripped'].str.split('-').str[0] 
    recs['title_stripped'] = recs['title_stripped'].str.strip()
    recs = recs.drop_duplicates(subset=['title_stripped'])

    playlist_url = create_playlist(recs,playlist_name,id_client,id_client_secret,True)
    print("\nYour Playlist is Ready!")
    print("Here is the playlist URL: "+playlist_url)
    

main()