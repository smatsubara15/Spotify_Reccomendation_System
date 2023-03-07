import numpy as np
import pandas as pd

from spotify_utils import get_playlist_df
from spotify_utils import get_track_features
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from sklearn.preprocessing import StandardScaler

from spotify_recs import get_distance_recs_playlist_1
from spotify_recs import get_distance_recs_playlist_gower
from spotify_utils import get_track_features
import json

# find distance from all songs in the playlist to all songs in corpus. Then get the average of all these distances to 
# find the songs with the closest average distance to all songs in the playlist
def get_distance_recs_playlist(uri, data, data_labels,scaler,sp, OH = False):
    # Get the index of the track with the given ID
    
    df_original = get_playlist_df('spotify', uri, sp, song_limit=8)
    genre = df_original['track_genre']
    df = df_original[num_features]
    df = pd.DataFrame(scaler.transform(df),columns=num_features)
    # if(OH):
    #     for col in dummies_cols:
    #         df[col] = 0
    #     for i in range(len_df):
    #         df.loc[i,lower(genre)] = 1
        
    
    data_new = data.copy()
    all_distances = []
    
    for i in range(len(df)):
        features = np.array(df.iloc[i])
        distances = []
        for j in range(len(data_new)):
            dist = np.linalg.norm(features - np.array(data_new.iloc[j]))
            if dist==0:
                distances.append(1000000)
            else:
                distances.append(dist)
        all_distances.append(distances)

    all_distances = np.array(all_distances)
    avg_dist = np.sum(all_distances, 0) / len(all_distances)
    
    data_new['Distance'] = avg_dist.tolist()

    data_new = data_new.join(data_labels)
    return data_new.sort_values(by=['Distance']),df_original

# use this function within the get_distance_recs_3
def get_distance_recs_playlist_new(df, data, data_labels,scaler,sp, OH = False):
    # Get the index of the track with the given ID

    data_new = data.copy()
    all_distances = []
    
    for i in range(len(df)):
        features = np.array(df.iloc[i])
        distances = []
        for j in range(len(data_new)):
            dist = np.linalg.norm(features - np.array(data_new.iloc[j]))
            if dist==0:
                distances.append(1000000)
            else:
                distances.append(dist)
        all_distances.append(distances)

    all_distances = np.array(all_distances)
    avg_dist = np.sum(all_distances, 0) / len(all_distances)
    
    data_new['Distance'] = avg_dist.tolist()

    data_new = data_new.join(data_labels)
    return data_new.sort_values(by=['Distance'])

from statistics import mode
# data = pd.read_csv('spoty_new_w_langflag.csv')
# print(data)
num_features = ['popularity', 'danceability', 'energy', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']

file = open('credentials.json')
credentials = json.load(file)
file.close()

id_client = credentials["client_id"]
id_client_secret = credentials["client_secret"]
auth_manager = SpotifyClientCredentials(client_id = id_client, 
                                        client_secret = id_client_secret)

sp = spotipy.Spotify(auth_manager=auth_manager)

data = pd.read_csv('spotify_new2.csv').drop(columns =['Unnamed: 0','level_0'])
data = data[data.track_genre!='children'].reset_index()

data_num = data[num_features]

scaler = StandardScaler()
scale_fit = scaler.fit(data_num)

final_numerical = data[num_features]
final_labels = data.drop(columns=num_features)

# song features are getting different scaled values
final_numerical = pd.DataFrame(scale_fit.transform(final_numerical),columns=num_features)

final_numerical['Genre'] = final_labels['track_genre']
final_numerical['mode'] = final_labels['mode']
final_numerical['key'] = final_labels['key']
final_labels.drop(columns=['track_genre','mode','key'],inplace=True)

input_uri = 'spotify:playlist:3Ins6u27JrxxYbQaQ0SmDY'
recs = get_distance_recs_playlist_gower(input_uri,final_numerical,final_labels,scale_fit,sp)
print(recs)
#28501