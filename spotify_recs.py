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

        # if the distance is clost to 0, the songs being compared are likely the same
        if dist<0.001:
            distances.append(1000000)
        else:
            distances.append(dist)
    
    data_new['Distance'] = distances
    data_new = data_new.join(data_labels)
    data_new = data_new.sort_values(by=['Distance'])

    return data_new,distances

# get 5 most similar songs to a song using Gower distance  
def get_distance_recs_song_gower(features,data,data_labels):
    data_new = data.copy()
    
    gower_closest = gower.gower_topn(features, data, n = 5)
    
    top_5 = list(gower_closest['index'])
    top_5_df = data.iloc[top_5]
    top_5_df = top_5_df.join(data_labels.iloc[top_5])
    
    return top_5_df

# Gets n number of recs from each song then finds the distance from each inputted song to all songs in the corpus. Finds the average distance from
# all songs to each inputed songs and finds the closest songs to all inputte songs.
def get_distance_recs_playlist_2(uri,data,data_labels,scaler,sp):

    # get dataframe consisting of songs from the playlist
    df_original = get_playlist_df('spotify', uri, sp, song_limit=8)
    ids = list(df_original['track_id'])
    song_names = list(df_original['track_name'])

    # drop songs from the dataset with the same track_id and track_name
    # so that we dont recommend same songs from the playlist
    data = data[~data_labels['track_id'].isin(ids)]
    data_labels = data_labels[~data_labels['track_id'].isin(ids)]
    
    data = data[~data_labels['track_name'].isin(song_names)]
    data_labels = data_labels[~data_labels['track_name'].isin(song_names)]

    # get numerical features and scale them with the scaler used to scale whole dataset
    df_num = df_original[num_features]
    df = pd.DataFrame(scaler.transform(df_num),columns=num_features)
    
    recs = []
    distances = []
    
    # compare each inputted song to each song in the dataset and add the three most similar to the recs
    print('\n')
    for i in range(len(df)):
        print("Gettings Recs for Song "+ str(i+1))
        song_recs,distance = get_distance_recs_song(df.iloc[i],data,data_labels)
        recs.extend([list(song_recs.iloc[i,:]) for i in range(3)])
        distances.append(distance)

    all_distances = np.array(distances)
    avg_dist = np.sum(all_distances, 0) / len(all_distances)

    data['Distance'] = avg_dist.tolist()

    data_new = data.join(data_labels)
    data_new = data_new.sort_values(by=['Distance'])

    recs.extend([list(data_new.iloc[i,:]) for i in range(5)])
    
    data_cols = list(data.columns)
    cols = data_cols + list(data_labels.columns)
    final_recs = pd.DataFrame(recs,columns=cols)

    return final_recs.drop_duplicates(subset=['track_id'])

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
        print("Gettings Recs for Song "+ str(i+1))
        song_recs,distance = get_distance_recs_song(df.iloc[i],data,data_labels)
        recs.extend([list(song_recs.iloc[i,:]) for i in range(3)])

    song_recs,distance = get_distance_recs_song(df_combined.iloc[0],data,data_labels)
    recs.extend([list(song_recs.iloc[i,:]) for i in range(5)])
    
    data_cols = list(data.columns)
    data_cols.append('Distance') 
    cols = data_cols + list(data_labels.columns)
    
    final_recs = pd.DataFrame(recs,columns=cols)

    final_recs = final_recs[~final_recs['track_id'].isin(ids)]

    return final_recs.drop_duplicates(subset=['track_id'])

# calculate reccomendations using the gower distance
# IMPORTANT: Remember to add genre column to labels to data and drop it from data_labels before running this function
# data_numerical['Genre'] = data.track_genre
# data_labels.drop(columns=['track_genre'],inplace=True)
def get_distance_recs_playlist_gower(uri,data,data_labels,scaler,sp):

    # get dataframe consisting of songs from the playlist
    df_original = get_playlist_df('spotify', uri, sp, song_limit=8)
    ids = list(df_original['track_id'])
    song_names = list(df_original['track_name'])

    # drop songs from the dataset with the same track_id and track_name
    # so that we dont recommend same songs from the playlist
    data = data[~data_labels['track_id'].isin(ids)]
    data_labels = data_labels[~data_labels['track_id'].isin(ids)]

    data = data[~data_labels['track_name'].isin(song_names)]
    data_labels = data_labels[~data_labels['track_name'].isin(song_names)]

    # get the most common genre in the playlist. This is used when creating the 
    # combined song from all songs in the playlist
    genres = list(df_original['track_genre'])
    playlist_genre = [mode(genres)]

    # get only the numeric features that we will scale
    df_num = df_original[num_features]

    # create songs that consists of the mean values of all numeric columbns
    df_combined = pd.DataFrame(df_num.mean(axis=0)).T
    df_combined.columns=num_features

    # scale these numeric variables
    df_combined = pd.DataFrame(scaler.transform(df_combined),columns=num_features)
    df = pd.DataFrame(scaler.transform(df_num),columns=num_features)
    
    # add genre to inputted data. Now we can use Gower distance to compare songs
    df_combined['Genre'] = playlist_genre
    df['Genre'] = df_original.track_genre

    recs = []
    
    # compare each inputted song to each song in the dataset and add the three most similar to the recs
    for i in range(len(df)):
        print("Gettings Recs for Song "+ str(i+1))
        song_recs = get_distance_recs_song_gower(df.iloc[i:i+1,:],data,data_labels)
        recs.extend([list(song_recs.iloc[i,:]) for i in range(3)])

    # find 5 most similar songs to the combined song
    song_recs = get_distance_recs_song_gower(df_combined.iloc[0:1,:],data,data_labels)
    recs.extend([list(song_recs.iloc[i,:]) for i in range(5)])

    cols = list(data.columns) + list(data_labels.columns)
    
    final_recs = pd.DataFrame(recs,columns=cols)

    # drop any potential duplicate songs in the playlist
    return final_recs.drop_duplicates(subset=['track_id'])



# https://community.spotify.com/t5/Spotify-for-Developers/Redirect-URI-needed/td-p/5067419
def create_playlist(recs,playlist_name,id,id_secret,Public=False):

    # create list of uris from inputted playlist dataframe
    uris = list(recs.track_id)
    uris = ["spotify:track:" + str(x) for x in uris]
    
    # create authorization token to create playlist
    auth_man = SpotifyOAuth(client_id=id, client_secret=id_secret, redirect_uri = 'http://localhost/',scope='playlist-modify-private playlist-modify-public')
    sp = spotipy.Spotify(auth_manager=auth_man)

    # Create a new playlist
    playlist_name = playlist_name + " Playlist Recs"
    playlist_description = "Playlist Consisting of Songs Recommended by Data Mining Team 2's Program"
    user_id = sp.me()["id"]
    new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=Public, description=playlist_description)

    # add songs to the playlist by URI
    sp.playlist_add_items(playlist_id=new_playlist["id"], items=uris)

    return new_playlist['external_urls']['spotify']