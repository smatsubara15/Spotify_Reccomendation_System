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

def get_distance_recs_playlist_gower(uri,data,data_labels,scaler,sp):
    # Get the index of the track with the given ID
    df_original = get_playlist_df('spotify', uri, sp, song_limit=8)
    ids = list(df_original['track_id'])
    genres = list(df_original['track_genre'])
    playlist_genre = list(mode(genres))
    #genre = df_original['track_genre']

    df_num = df_original[num_features]

    df_combined = pd.DataFrame(df_num.mean(axis=0)).T
    df_combined.columns=num_features

    df_combined = pd.DataFrame(scaler.transform(df_combined),columns=num_features)
    df = pd.DataFrame(scaler.transform(df_num),columns=num_features)
    
    df_combined['Genre'] = playlist_genre
    df['Genre'] = df_original.track_genre
    
    labels = data_labels.drop(columns=['track_genre'],inplace=True)

    recs = []
    
    for i in range(len(df)):
        song_recs,distance = get_distance_recs_song_gower(df.iloc[i],data,labels)
        recs.extend([list(song_recs.iloc[i,:]) for i in range(3)])

    song_recs,distance = get_distance_recs_song_gower(df_combined.iloc[0],data,labels)
    recs.extend([list(song_recs.iloc[i,:]) for i in range(5)])
    
    data_cols = list(data.columns)
    data_cols.append('Distance') 
    cols = data_cols + list(data_labels.columns)
    
    final_recs = pd.DataFrame(recs,columns=cols)

    return final_recs[~final_recs['track_id'].isin(ids)]
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

data = pd.read_csv("spotify_no_children.csv")

data_num = data[num_features]
data_labels = data.drop(columns=num_features)

data_eng = pd.read_csv('spoty_new_w_langflag.csv').drop(columns =['Unnamed: 0','level_0'])
data_eng = data_eng[data_eng.eng_flag==1]
data_eng = data_eng.reset_index()

data_num_eng = data_eng[num_features]
data_labels_eng = data_eng.drop(columns=num_features)

scaler = StandardScaler()
scale_fit = scaler.fit(data_num)

# song features are getting different scaled values
data_numerical = pd.DataFrame(scale_fit.transform(data_num),columns=num_features)
data_numerical_eng = pd.DataFrame(scale_fit.transform(data_num_eng),columns=num_features)

print(data_labels.track_genre)
print(data_labels_eng.track_genre)

data_numerical_eng['Genre'] = data_labels.track_genre

print(data_numerical_eng['Genre'])
#get_track_features('spotify:track:7I7Dk8FOkZqhqZp9N2RKiP',sp)

#input_uri = input("Please input a Spotify Playlist URI: ")
# recs = get_distance_recs_playlist_4(input_uri,data_numerical_eng,data_labels_eng,scale_fit,sp)
#print(recs[['track_name','artists']].head(10))
#28501