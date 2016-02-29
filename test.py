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

for channel in results["items"]:
	channelId = channel["snippet"]["resourceId"]["channelId"]
	chresults = youtube.channels().list(part="snippet,contentDetails,statistics",id=channelId).execute()
	channeltitle = chresults["items"][0]["snippet"]["title"]
	channelsubcount = chresults["items"][0]["statistics"]["subscriberCount"]
	channeldesc = chresults["items"][0]["snippet"]["description"].replace("'","")
	channelviewcount = chresults["items"][0]["statistics"]["viewCount"]
	# q = "INSERT INTO channel (c_id, c_title, c_description, c_view_count, c_sub_count) VALUES ('" + channelId + "','" + channeltitle + "','" + channeldesc + "'," + str(channelviewcount) + "," + str(channelsubcount) + ")" 
	q = "INSERT INTO channel (c_id, c_title, c_description, c_view_count, c_sub_count) SELECT '{0}' ,'{1}','{2}',{3},{4} WHERE NOT EXISTS (SELECT 1 FROM channel WHERE c_id = '{0}')".format(channelId,channeltitle,channeldesc,str(channelviewcount),str(channelsubcount)) 
	cur.execute(q)
	thumdict = chresults["items"][0]["snippet"]["thumbnails"]
	for size in thumdict:
		thumurl = thumdict[size]['url']
		q = "INSERT INTO Thumbnail (t_url, t_width, t_height) SELECT '{0}',{1},{2} WHERE NOT EXISTS (SELECT 1 FROM Thumbnail WHERE t_url = '{0}')".format(thumurl,str(1),str(1))
		cur.execute(q)
		q = "INSERT INTO has_thumb_2 (t_url,c_id) SELECT '{0}','{1}' WHERE NOT EXISTS (SELECT 1 FROM has_thumb_2 WHERE t_url = '{0}')".format(thumurl,channelId)
		cur.execute(q)
		# print size, channelId


# df = pandas.read_sql("SELECT * FROM video",con=engine)


