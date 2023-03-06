import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.preprocessing import StandardScaler

from statistics import mode
import gower 

from spotify_utils import get_playlist_df
from spotify_utils import get_track_features
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from etl_utils import get_unique_map_from_df_col, clean_date

num_features = ['popularity', 'danceability', 'energy', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']

# distance recs based on Euclidean distance
def get_distance_recs_song(features,data,data_labels):
    # Get the index of the track with the given ID
    data_new = data.copy()
    features = np.array(features)
    
    distances = []
    for j in range(len(data_new)):
        dist = np.linalg.norm(features - np.array(data_new.iloc[j]))
        if dist==0:
            distances.append(1000000)
        else:
            distances.append(dist)
    
    data_new['Distance'] = distances
    data_new = data_new.join(data_labels)
    data_new = data_new.sort_values(by=['Distance'])
    return data_new,distances
    
def get_distance_recs_song_gower(features,data,data_labels):
    # Get the index of the track with the given ID
    data_new = data.copy()
    #features = np.array(features)
    

    gower_closest = gower.gower_topn(features, data, n = 5)
    
    top_5 = list(gower_closest['index'])
    top_5_df = data.iloc[top_5]
    top_5_df = top_5_df.join(data_labels.iloc[top_5])
    
    return top_5_df

# Gets n number of recs from each song then finds recs based on the closests songs to the centroid of all inputted songs
def get_distance_recs_playlist_1(uri,data,data_labels,scaler,sp):
    # Get the index of the track with the given ID
    df_original = get_playlist_df('spotify', uri, sp, song_limit=8)
    ids = list(df_original['track_id'])
    #genre = df_original['track_genre']

    df_num = df_original[num_features]

    df_combined = pd.DataFrame(df_num.mean(axis=0)).T
    df_combined.columns=num_features

    df_combined = pd.DataFrame(scaler.transform(df_combined),columns=num_features)
    df = pd.DataFrame(scaler.transform(df_num),columns=num_features)
    
    recs = []
    
    for i in range(len(df)):
        song_recs,distance = get_distance_recs_song(df.iloc[i],data,data_labels)
        recs.extend([list(song_recs.iloc[i,:]) for i in range(3)])

    song_recs,distance = get_distance_recs_song(df_combined.iloc[0],data,data_labels)
    recs.extend([list(song_recs.iloc[i,:]) for i in range(5)])
    
    data_cols = list(data.columns)
    data_cols.append('Distance') 
    cols = data_cols + list(data_labels.columns)
    
    final_recs = pd.DataFrame(recs,columns=cols)

    return final_recs[~final_recs['track_id'].isin(ids)]



# Gets n number of recs from each song then finds the distance from each inputted song to all songs in the corpus. Finds the average distance from
# all songs to each inputed songs and finds the closest songs to all inputte songs.
def get_distance_recs_playlist_2(uri,data,data_labels,scaler,sp):
    # Get the index of the track with the given ID
    df_original = get_playlist_df('spotify', uri, sp, song_limit=8)
    ids = list(df_original['track_id'])
    #genre = df_original['track_genre']

    df_num = df_original[num_features]
    df = pd.DataFrame(scaler.transform(df_num),columns=num_features)
    
    recs = []
    distances = []
    
    for i in range(len(df)):
        song_recs,distance = get_distance_recs_song(df.iloc[i],data,data_labels)
        recs.extend([list(song_recs.iloc[i,:]) for i in range(3)])
        distances.append(distance)

    all_distances = np.array(distances)
    avg_dist = np.sum(all_distances, 0) / len(all_distances)

    data['Distance'] = avg_dist.tolist()

    data_new = data.join(data_labels)
    data_new = data_new.sort_values(by=['Distance'])

    #print(data_new[['track_name','artists']].head(10))
    recs.extend([list(data_new.iloc[i,:]) for i in range(5)])
    
    data_cols = list(data.columns)
    cols = data_cols + list(data_labels.columns)
    final_recs = pd.DataFrame(recs,columns=cols)
    final_recs = final_recs[~final_recs['track_id'].isin(ids)]

    return final_recs.drop_duplicates(subset=['track_id'])

# calculate reccomendations using the gower distance
# IMPORTANT: Remember to add genre column to labels to data and drop it from data_labels before running this function
# data_numerical['Genre'] = data.track_genre
# data_labels.drop(columns=['track_genre'],inplace=True)
def get_distance_recs_playlist_gower(uri,data,data_labels,scaler,sp):
    # Get the index of the track with the given ID
    df_original = get_playlist_df('spotify', uri, sp, song_limit=8)
    ids = list(df_original['track_id'])
    genres = list(df_original['track_genre'])
    playlist_genre = [mode(genres)]
    #genre = df_original['track_genre']

    df_num = df_original[num_features]

    df_combined = pd.DataFrame(df_num.mean(axis=0)).T
    df_combined.columns=num_features

    df_combined = pd.DataFrame(scaler.transform(df_combined),columns=num_features)
    df = pd.DataFrame(scaler.transform(df_num),columns=num_features)
    
    df_combined['Genre'] = playlist_genre
    df['Genre'] = df_original.track_genre

    recs = []
    
    for i in range(len(df)):
        song_recs = get_distance_recs_song_gower(df.iloc[i:i+1,:],data,data_labels)
        recs.extend([list(song_recs.iloc[i,:]) for i in range(3)])

    song_recs = get_distance_recs_song_gower(df_combined.iloc[0:1,:],data,data_labels)
    recs.extend([list(song_recs.iloc[i,:]) for i in range(5)])
     
    cols = list(data.columns) + list(data_labels.columns)
    
    final_recs = pd.DataFrame(recs,columns=cols)

    return final_recs[~final_recs['track_id'].isin(ids)]



# https://community.spotify.com/t5/Spotify-for-Developers/Redirect-URI-needed/td-p/5067419
def create_playlist(recs,playlist_name,id,id_secret,Public=False):
    uris = list(recs.track_id)
    uris = ["spotify:track:" + str(x) for x in uris]
    
    auth_man = SpotifyOAuth(client_id=id, client_secret=id_secret, redirect_uri = 'http://localhost/',scope='playlist-modify-private playlist-modify-public')
    sp = spotipy.Spotify(auth_manager=auth_man)

    # Create a new playlist
    playlist_name = playlist_name + " Playlist Recs"
    playlist_description = "Playlist Consisting of Songs Recommended by Data Mining Team 4's Program"
    user_id = sp.me()["id"]
    new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=Public, description=playlist_description)

    sp.playlist_add_items(playlist_id=new_playlist["id"], items=uris)

    return new_playlist['external_urls']['spotify']