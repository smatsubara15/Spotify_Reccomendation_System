# Credit Akshat Palnitkar

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
import pandas as pd

def get_track_ids(username, playlist_id, sp):

    """Get the unique spotify id of each song in a spotify playlist"""

    results = sp.user_playlist_tracks(username, playlist_id)
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    track_ids = []
    for track in tracks:
        track_id = track['track']['id']
        track_ids.append(track_id)
    return track_ids

def get_track_features(id, sp):

    """Given a track_id and spotify object, return a list of 
    fields associated with that track"""

    track_info = sp.track(id)
    features_info = sp.audio_features(id)
    
    # Track info
    name = track_info['name']
    album = track_info['album']['name']
    artist = track_info['album']['artists'][0]['name']
    
    artist_info = sp.artist(track_info['album']['artists'][0]["external_urls"]["spotify"])
    
    # Get the genre of the artist
    if artist_info["genres"]:
        top_genre = artist_info["genres"][0]
    # Some artists in spotify don't have genres
    else:
        top_genre = ''
    
    release_date = track_info['album']['release_date']
    length = track_info['duration_ms']
    popularity = track_info['popularity']
        
    # Track features
    acousticness = features_info[0]['acousticness']
    danceability = features_info[0]['danceability']
    energy = features_info[0]['energy']
    instrumentalness = features_info[0]['instrumentalness']
    liveness = features_info[0]['liveness']
    loudness = features_info[0]['loudness']
    speechiness = features_info[0]['speechiness']
    tempo = features_info[0]['tempo']
    time_signature = features_info[0]['time_signature']
    valence = features_info[0]['valence']
    
    track_data = [name, album, artist, top_genre, release_date, length, popularity, acousticness, danceability, energy, 
                  instrumentalness, liveness, loudness, speechiness, tempo, valence, time_signature]
    
    return track_data    

def get_playlist_df(username, playlist_id, sp, song_limit=None):

    """Return a dataframe of information about songs in a spotify playlist
        Set a song limit to only fetch a certain number of songs from a playlist"""
    
    track_ids = get_track_ids(username, playlist_id, sp)
    
    track_list = []
    total_tracks = len(track_ids)

    for i in range(total_tracks):
        time.sleep(.3)
        track_data = get_track_features(track_ids[i], sp)
        track_list.append(track_data)
        print("Got track "+ str(i+1)+" out of "+str(len(track_ids)))
        if song_limit is not None:
            if i>song_limit:
                break
    playlist_df = pd.DataFrame(track_list, columns=['track_name', 'album_name', 'artists', 
                                                    'track_genre', 'Release_date', 
                                                    'Length', 'popularity', 
                                                    'acousticness', 'danceability', 
                                                    'energy', 'instrumentalness', 
                                                    'liveness', 
                                                    'loudness', 'speechiness', 
                                                    'tempo', 'valence', 'Time Signature'])     

    if ((song_limit is None) or (song_limit>total_tracks)):
        track_nums = total_tracks
    else:
        track_nums = song_limit+2

    #playlist_df['track_id'] = track_ids[:10]
    playlist_df['track_id'] = track_ids[:track_nums]
    return playlist_df

