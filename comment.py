from sqlalchemy import create_engine
import pandas
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

execfile("../creds.py")

engine = create_engine("postgresql://ql2257:3368@w4111a.eastus.cloudapp.azure.com/proj1part2")

cur = engine.connect()

DEVELOPER_KEY = devkey
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

videoId = '_26z0xvClxA'

results = youtube.commentThreads().list(part="snippet",maxResults=10,videoId=videoId).execute()
for comm in results["items"]:
	commentId = comm["snippet"]["topLevelComment"]["id"]
	commentLikes = comm["snippet"]["topLevelComment"]["snippet"]["likeCount"]
	commentorImage = comm["snippet"]["topLevelComment"]["snippet"]["authorProfileImageUrl"]
	commentDate = comm["snippet"]["topLevelComment"]["snippet"]["updatedAt"]
	commentText = comm["snippet"]["topLevelComment"]["snippet"]["textDisplay"].encode("ascii","ignore").replace("'","")
	commentorName = comm["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"].encode("ascii","ignore").replace("'","")
	q = "INSERT INTO comment (com_id,video_id,text,com_date,display_name, profile_img,like_count) SELECT '{0}','{1}','{2}','{3}','{4}','{5}',{6} WHERE NOT EXISTS (SELECT 1 FROM comment WHERE com_id = '{0}')".format(commentId,videoId,commentText,commentDate,commentorName,commentorImage,commentLikes)
	cur.execute(q)


