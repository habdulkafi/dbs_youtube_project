import pandas
import MySQLdb
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

execfile("../creds.py")

DEVELOPER_KEY = devkey
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)


db = MySQLdb.connect(host="localhost",user="root",passwd="",db="youtube_app")

cur = db.cursor()

df = pandas.read_sql("SELECT * FROM subscriptions", con = db)

for ch in list(df.channelId):
	results = youtube.channels().list(part="contentDetails",id=ch).execute()
	playlistId = results["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
	results = youtube.playlistItems().list(part="snippet",playlistId=playlistId).execute()
	for item in results["items"]:
		videoId = item["snippet"]["resourceId"]["videoId"]
		publishedAt = item["snippet"]["publishedAt"]
		title = item["snippet"]["title"].replace('"','')
		description = item["snippet"]["description"]
		channelTitle = item["snippet"]["channelTitle"]
		channelId = item["snippet"]["channelId"]
		# print videoId
		q = 'INSERT INTO videos (title, videoId, publishedAt, channelTitle, channelId)  SELECT "' + title + '","' + videoId + '","' + publishedAt + '","' + channelTitle + '","' + channelId + '" FROM dual WHERE NOT EXISTS (SELECT * FROM videos WHERE videoId = "' + videoId + '" );' 
		# print q
		q = q.encode("ascii","ignore")
		cur.execute(q)
		db.commit()