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


results = youtube.subscriptions().list(part="snippet", maxResults=10, channelId="UCUbh6T8Nr6ss7JWsq-3xYQg").execute()

# for ch in list(df.channelId):
# 	results = youtube.channels().list(part="contentDetails",id=ch).execute()
# 	playlistId = results["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
# 	results = youtube.playlistItems().list(part="snippet",playlistId=playlistId).execute()
# 	for item in results["items"]:
# 		videoId = item["snippet"]["resourceId"]["videoId"]
# 		publishedAt = item["snippet"]["publishedAt"]
# 		title = item["snippet"]["title"].replace('"','')
# 		description = item["snippet"]["description"]
# 		channelTitle = item["snippet"]["channelTitle"]
# 		channelId = item["snippet"]["channelId"]
# 		# print videoId
# 		q = 'INSERT INTO videos (title, videoId, publishedAt, channelTitle, channelId)  SELECT "' + title + '","' + videoId + '","' + publishedAt + '","' + channelTitle + '","' + channelId + '" FROM dual WHERE NOT EXISTS (SELECT * FROM videos WHERE videoId = "' + videoId + '" );' 
# 		# print q
# 		q = q.encode("ascii","ignore")
# 		cur.execute(q)
# 		db.commit()

for channel in results["items"]:
	channelId = channel["snippet"]["resourceId"]["channelId"]
	chresults = youtube.channels().list(part="snippet,contentDetails,statistics",id=channelId).execute()
	channeltitle = chresults["items"][0]["snippet"]["title"]
	channelsubcount = chresults["items"][0]["statistics"]["subscriberCount"]
	channeldesc = chresults["items"][0]["snippet"]["description"]
	channelviewcount = chresults["items"][0]["statistics"]["viewCount"]
	q = "INSERT INTO channel VALUES ('" + channelId + "','" + channeltitle + "','" + channeldesc + "'," + str(channelviewcount) + "," + str(channelsubcount) + ")" 
	cur.execute(q)



# df = pandas.read_sql("SELECT * FROM video",con=engine)


