import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

songs = pd.read_csv("songs.csv", index_col =0)

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

similarity_matrix = cosine_similarity(song_data.iloc[:,5:])

similarity_matrix = pd.DataFrame(similarity_matrix,
                                index = songs.iloc[:,:5],
                                columns = songs.iloc[:,:5])

similarity_matrix.to_csv("score.csv")
