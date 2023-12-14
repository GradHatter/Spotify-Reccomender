import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import requests
import base64

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

# Replace with your own Client ID and Client Secret
CLIENT_ID = ''
CLIENT_SECRET = ''
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
    
#------------------------------------------------------------------------------

#Get song data from a playlist and turn it into a useable dataframe

def playlist_song_data(playlist_id, access_token):
    # Set up Spotipy with the access token
    #Authentication - without user
    client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID,
                                                          client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)
    #sp = spotipy.Spotify(auth=access_token)

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

def get_playlist_id(link):

    link = link.split("/")[-1]
    playlist_id = link.split("?")[0]

    return playlist_id

#--------------------------------------------------------------------------------

def prepare_songs(songs):
    '''
    input:
    songs: dataframe

    output:
    song_data: dataframe
    '''
    #"Normalize" values for columns
    songs["Popularity"] = songs["Popularity"]/100 #Ranges from 0-100
    songs["Duration (norm)"] = songs["Duration (ms)"]/300000 #No theoretical limit
    songs.replace({True : 0, False : 0}, inplace = True) #Replaces True/False in whole df but mainly for "Explicit"
    songs["Key"] = songs["Key"]/11 #There are 12 keys (0-11)
    songs["Loudness"] = songs["Loudness"]/(-60) #No theoretical min or max, but typically from 0 to -60
    songs["Tempo"] = songs["Tempo"]/200 #No theoretical limit

    #Split up date and "normalize"
    songs["Release Date"] = pd.to_datetime(songs["Release Date"])
    songs["day"] = songs["Release Date"].dt.day/31
    songs["month"] = songs["Release Date"].dt.month/12
    songs["year"] = (songs["Release Date"].dt.year-1950)/70 #most songs will be from 0-1

    song_data = songs.drop(columns = ["Release Date", "Duration (ms)", "External URLs",])

    return song_data

#--------------------------------------------------------------------------------------

link = "https://open.spotify.com/playlist/3q5nKZCz7B6ih8ApUr9yo2?si=00c65d5a8c9c45bb"    

playlist_id = get_playlist_id(link)

# Call the function to get the music data from the playlist and store it in a DataFrame
new_music_df = playlist_song_data(playlist_id, access_token)

new_music_df = prepare_songs(new_music_df)

average_new_music = new_music_df.median(numeric_only = True)

songs = pd.read_csv("songs.csv", index_col =0)

song_data = prepare_songs(songs)

similarity_matrix = cosine_similarity(np.array(average_new_music).reshape(1,-1),
                                        song_data.iloc[:,5:])

'''
similarity_matrix = pd.DataFrame(similarity_matrix,
                                index = songs.iloc[:,:5],
                                columns = songs.iloc[:,:5])
'''
#similarity_matrix.to_csv("score.csv")

i = np.argmin(similarity_matrix)

print(f"Worst song recommendation for this playlist: {songs.iloc[i,:]["Track Name"]}")

j = np.argmax(similarity_matrix)
print(f"Best song recommendation for this playlist: {songs.iloc[j,:]["Track Name"]}")
