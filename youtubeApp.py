import pandas
import MySQLdb
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import webbrowser

DEVELOPER_KEY = "AIzaSyB17kQbcQ6fBrNwiVPsLRCKMk79iUaYjPk"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
baseUrl = "https://www.youtube.com/watch?v="

db = MySQLdb.connect(host="localhost",user="root",passwd="",db="youtube_app")

cur = db.cursor()



def get_all_videos(playlistId):
	results = youtube.playlistItems().list(part="snippet",playlistId=playlistId,maxResults=50).execute()
	while "nextPageToken" in results:
		for item in results["items"]:
			videoId = item["snippet"]["resourceId"]["videoId"]
			publishedAt = item["snippet"]["publishedAt"]
			title = item["snippet"]["title"].replace('"','')
			description = item["snippet"]["description"]
			channelTitle = item["snippet"]["channelTitle"]
			channelId = item["snippet"]["channelId"]
			print videoId
			q = 'INSERT INTO videos VALUES ("' + title + '","' + videoId + '","' + publishedAt + '","' + channelTitle + '","' + channelId + '");'
			q = q.encode("ascii","ignore")
			cur.execute(q)
			db.commit()
		results = youtube.playlistItems().list(part="snippet",playlistId=playlistId,maxResults=50,pageToken = results["nextPageToken"]).execute()
	for item in results["items"]:
		videoId = item["snippet"]["resourceId"]["videoId"]
		publishedAt = item["snippet"]["publishedAt"]
		title = item["snippet"]["title"].replace('"','')
		description = item["snippet"]["description"]
		channelTitle = item["snippet"]["channelTitle"]
		channelId = item["snippet"]["channelId"]
		print videoId
		q = 'INSERT INTO videos VALUES ("' + title + '","' + videoId + '","' + publishedAt + '","' + channelTitle + '","' + channelId + '");'
		# print q
		q = q.encode("ascii","ignore")
		cur.execute(q)
		db.commit()

def get_latest_video(channelId):
	results = youtube.channels().list(part="contentDetails",id=channelId).execute()
	playlistId = results["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
	get_all_videos(playlistId)
	# results = youtube.playlistItems().list(part="snippet",playlistId=playlistId).execute()
	# videoId = results["items"][0]["snippet"]["resourceId"]["videoId"]
	# # print results
	# # standard_url = results["items"][0]["snippet"]["thumbnails"]["standard"]["url"]
	# publishedAt = results["items"][0]["snippet"]["publishedAt"]
	# title = results["items"][0]["snippet"]["title"]
	# description = results["items"][0]["snippet"]["description"]
	# channelTitle = results["items"][0]["snippet"]["channelTitle"]
	# channelId = results["items"][0]["snippet"]["channelId"]
	# print videoId
	# q = 'INSERT INTO videos VALUES ("' + title + '","' + videoId + '","' + publishedAt + '","' + channelTitle + '","' + channelId + '");'
	# # print q
	# cur.execute(q)
	# db.commit()


df = pandas.read_sql("SELECT * FROM subscriptions", con = db)

for ch in list(df.channelId)[5:]:
	get_latest_video(ch)

# subscriptions = youtube.subscriptions().list(part="snippet",channelId="UCUbh6T8Nr6ss7JWsq-3xYQg").execute()["items"]

# for channel in subscriptions[:3]:
# 	channelId = channel["snippet"]["resourceId"]["channelId"]
# 	results = youtube.channels().list(part="contentDetails",id=channelId).execute()
# 	playlistId = results["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
# 	webbrowser.open(baseUrl + get_latest_video(playlistId),new=2) 

cur.close()