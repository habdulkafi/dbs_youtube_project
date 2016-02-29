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

results1 = youtube.subscriptions().list(part="snippet,contentDetails,statistics", maxResults=50, channelId="UCUbh6T8Nr6ss7JWsq-3xYQg").execute()
results2 = youtube.subscriptions().list(part="snippet", maxResults=50, channelId="UCUbh6T8Nr6ss7JWsq-3xYQg",pageToken=results1["nextPageToken"]).execute()
results3 = youtube.subscriptions().list(part="snippet", maxResults=50, channelId="UCUbh6T8Nr6ss7JWsq-3xYQg",pageToken=results2["nextPageToken"]).execute()
subscriptions = results1["items"] + results2["items"] + results3["items"]

cur = db.cursor()

for channel in subscriptions:
	title = channel["snippet"]["title"]
	channelId = channel["snippet"]["resourceId"]["channelId"]
	thumbnail = channel["snippet"]["thumbnails"]["high"]["url"]
	q = 'INSERT INTO subscriptions VALUES ("' + title + '","' + channelId + '","' + thumbnail + '");'
	# print q
	cur.execute(q)
	db.commit()


cur.close()
