import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import requests
import base64

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

#------------------------------------------------------------------------------
'''
# Replace with your own Client ID and Client Secret
CLIENT_ID = '52f7cfd2ef2c41f89685df88e3772f55'
CLIENT_SECRET = 'de8f11bd0e51450cbff4ea897009eb14'
SPOTIFY_REDIRECT_URI = 'http://example.com'

# Base64 encode the client ID and client secret
client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
client_credentials_base64 = base64.b64encode(client_credentials.encode())

# Request the access token
token_url = 'https://accounts.spotify.com/api/token'
headers = {
    'Authorization': f'Basic {client_credentials_base64.decode()}'
}
data = {
    'grant_type': 'client_credentials'
}
response = requests.post(token_url, data=data, headers=headers)

if response.status_code == 200:
    access_token = response.json()['access_token']
    print("Access token obtained successfully.")
else:
    print("Error obtaining access token.")
    exit()
'''
#print(access_token)
access_token = "BQABErf3gEg5IwQNMhSZ602phNXQEjfWZQ0ch7Li3OW1P1QCdfmLko3nFzcS2xcApLSZj7adn43q2phSCCLNvPvwaftCOuZHY8_6TmnlBwohYXwCQuE"    
#------------------------------------------------------------------------------

#Get song data from a playlist and turn it into a useable dataframe

def playlist_song_data(playlist_id, access_token):
    # Set up Spotipy with the access token
    #Authentication - without user
    #client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID,
    #                                                      client_secret=CLIENT_SECRET)
    #sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)
    sp = spotipy.Spotify(auth=access_token)

    # Get the tracks from the playlist
    playlist_tracks = sp.playlist_tracks(playlist_id,
                        fields='items(track(id, name, artists, album(id, name)))')

    # Extract relevant information and store in a list of dictionaries
    music_data = []
    for track_info in playlist_tracks['items']:
        track = track_info['track']
        track_name = track['name']
        artists = ', '.join([artist['name'] for artist in track['artists']])
        album_name = track['album']['name']
        album_id = track['album']['id']
        track_id = track['id']

        # Get audio features for the track
        audio_features = sp.audio_features(track_id)[0] if track_id != 'Not available' else None
        
        # Get release date of the album
        try:
            album_info = sp.album(album_id) if album_id != 'Not available' else None
            release_date = album_info['release_date'] if album_info else None
        except:
            release_date = None
        
        # Get popularity of the track
        try:
            track_info = sp.track(track_id) if track_id != 'Not available' else None
            popularity = track_info['popularity'] if track_info else None
        except:
            popularity = None

        # Add additional track information to the track data
        track_data = {
            'Track Name': track_name,
            'Artists': artists,
            'Album Name': album_name,
            'Album ID': album_id,
            'Track ID': track_id,
            'Popularity': popularity,
            'Release Date': release_date,
            'Duration (ms)': audio_features['duration_ms'] if audio_features else None,
            'Explicit': track_info.get('explicit', None),
            'External URLs': track_info.get('external_urls', {}).get('spotify', None),
            'Danceability': audio_features['danceability'] if audio_features else None,
            'Energy': audio_features['energy'] if audio_features else None,
            'Key': audio_features['key'] if audio_features else None,
            'Loudness': audio_features['loudness'] if audio_features else None,
            'Mode': audio_features['mode'] if audio_features else None,
            'Speechiness': audio_features['speechiness'] if audio_features else None,
            'Acousticness': audio_features['acousticness'] if audio_features else None,
            'Instrumentalness': audio_features['instrumentalness'] if audio_features else None,
            'Liveness': audio_features['liveness'] if audio_features else None,
            'Valence': audio_features['valence'] if audio_features else None,
            'Tempo': audio_features['tempo'] if audio_features else None,
        }

        music_data.append(track_data)

    # Create a pandas DataFrame from the list of dictionaries
    df = pd.DataFrame(music_data)

    return df

#------------------------------------------------------------------------------

def prepare_songs(songs):
    '''
    input:
    songs: dataframe

    output:
    song_data: dataframe
    '''

    #"Normalize" each variable to roughly 0-1 to reduce the effect of any one column
    songs["Popularity"] = songs["Popularity"]/100 #Ranges from 0-100
    songs["Duration (norm)"] = songs["Duration (ms)"]/300000 #No theoretical limit but mean time is 3.8 min
    songs["Explicit"].replace({True : 0, False : 0}, inplace = True) #"Explicit" bool -> bianary numerical
    songs["Key"] = songs["Key"]/11 #There are 12 keys (0-11)
    songs["Loudness"] = songs["Loudness"]/(-60) #No theoretical min, but typically from 0 to -60
    songs["Tempo"] = songs["Tempo"]/200 #No theoretical limit but most songs are 60-200 bpm

    #Split up date and "normalize"
    songs["Release Date"] = pd.to_datetime(songs["Release Date"])
    #songs["day"] = songs["Release Date"].dt.day/31
    #songs["month"] = songs["Release Date"].dt.month/12
    songs["year"] = (songs["Release Date"].dt.year-1950)/70 #most songs are from 1950-2020

    return songs

#--------------------------------------------------------------------------------

def get_playlist_id(link):

    link = link.split("/")[-1]
    playlist_id = link.split("?")[0]

    return playlist_id

#--------------------------------------------------------------------------------

link = "https://open.spotify.com/playlist/1KW8SkrdDSSYzihEPZuMFJ?si=3c37bc70240842dd"    

playlist_id = get_playlist_id(link)
print(playlist_id)
#Get the music data from the dataset and new playlist & preprocess them
#song_data_df = pd.read_csv("song_data.zip", compression = "zip", index_col =0)
song_data_df = pd.read_csv("song_data.csv", index_col =0)
song_data = song_data_df.copy()
song_data = prepare_songs(song_data_df)
song_data = song_data.drop(columns = ["Release Date", "Duration (ms)"])

new_music_df = playlist_song_data(playlist_id, access_token)
new_music_df = new_music_df.drop(columns = ["Album Name", "Album ID", "External URLs"])
new_music = new_music_df.copy()
new_music = prepare_songs(new_music_df)
new_music = new_music.drop(columns = ["Release Date", "Duration (ms)"])


#Get the average value for the playlist to get the best representation of the whole
average_new_music = new_music.median(numeric_only = True)
average_new_music['Key'] = new_music["Key"].mode() #Key is categorical not continuous

#--------------------------------------------------------------------------------

#Add parameters for recommendeding songs

# Don't recommend songs already in the playlist
new_song_list = new_music['Track ID'].tolist() #get IDs for songs on playlist
song_data = song_data[song_data["Track ID"].isin(new_song_list) == False]

# Don't recommend incredibly obscure songs
squal = 0.70 # squal >=0.7 reduces the recommendable songs to just over 4500 songs
song_data = song_data[song_data["Popularity"] >= squal]

# Don't include "White Noise" tracks
song_data = song_data[song_data["Track Name"].str.contains("White Noise|Black Noise|Grey Noise|Gray Noise",
                                                             regex=False) == False]

#--------------------------------------------------------------------------------

#compute the cosine similarity on the numerical values
similarity_matrix = cosine_similarity(np.array(average_new_music).reshape(1,-1),
                                        song_data.iloc[:,3:])

#Get the worst or least similar song
worst_i = np.argmin(similarity_matrix)
worst_rec = song_data.iloc[worst_i,:]["Track Name"]
worst_rec_art = song_data.iloc[worst_i,:]["Artists"]
worst_rec_id = song_data.iloc[worst_i,:]["Track ID"]
print(f"The worst recommendation for this playlist is: {worst_rec} by {worst_rec_art}",
 "\n",
f"Track Link: https://open.spotify.com/track/{worst_rec_id}")

#Get the best or most similar song
best_i = np.argmax(similarity_matrix)
best_rec = song_data.iloc[best_i,:]["Track Name"]
best_rec_art = song_data.iloc[best_i,:]["Artists"]
best_rec_id = song_data.iloc[best_i,:]["Track ID"]
print(f"The best recommendation for this playlist is: {best_rec} by {best_rec_art}",
 "\n",
f"Track Link: https://open.spotify.com/track/{best_rec_id}")

#----------------------------------------------------------------------------------

#Add new songs to dataset
before = song_data_df.shape[0] #number of songs before new playlist is added

dataset_IDs = song_data_df['Track ID'].tolist()

new_music_df = new_music_df[new_music_df["Track ID"].isin(dataset_IDs) == False]
total_song_data = pd.concat([song_data_df, new_music_df], ignore_index = True, axis = 0)
total_song_data.dropna(axis = 0, inplace = True)
print(total_song_data.columns)
print(total_song_data.head())
#save dataset with new songs to zip file
filename = 'song_data'
compression_options = dict(method='zip', archive_name=f'{filename}.csv')
total_song_data.to_csv(f'{filename}.zip', compression=compression_options)

#Thank them for the new songs
after = total_song_data.shape[0] #number of songs before new playlist is added
added = after-before

print(f"Thank you for adding {added} new songs to the dataset!")
print(total_song_data.columns)
print(total_song_data.head())
#new_music = new_music[new_music["Track ID"].isin(dataset_IDs) == False]
#norm_song_data = pd.concat([song_data, new_music], ignore_index = True, axis = 0)
#norm_song_data.dropna(axis = 0, inplace = True, ignore_index = True)

#norm_song_data.to_csv("norm_song_data.csv")
