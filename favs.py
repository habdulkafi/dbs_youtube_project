import pandas
from sqlalchemy import create_engine
from apiclient.discovery import build
import traceback

execfile("../creds.py")

DEVELOPER_KEY = devkey
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

engine = create_engine("postgresql://ql2257:3368@w4111a.eastus.cloudapp.azure.com/proj1part2")

cur = engine.connect()

df = pandas.read_sql("SELECT * FROM channel",con=engine.raw_connection())

c_id = df["c_id"]

for ch in c_id:
	results = youtube.channels().list(part="contentDetails",id=ch).execute()
	playlists = results["items"][0]["contentDetails"]["relatedPlaylists"].keys()
	if "favorites" in playlists:
		playlistId = results["items"][0]["contentDetails"]["relatedPlaylists"]["favorites"]
		results = youtube.playlistItems().list(part="snippet",playlistId=playlistId).execute()
		all_res = results["items"]
		while (len(all_res) < results["pageInfo"]["totalResults"]) and ("nextPageToken" in results.keys()):
			print len(all_res)
			results = youtube.playlistItems().list(part="snippet",maxResults=50,pageToken=results["nextPageToken"],playlistId=playlistId).execute()
			all_res += results["items"]
		for vid in all_res:
			# insert into video table
			try:
				video_id = vid["snippet"]["resourceId"]["videoId"]
				vresults = youtube.videos().list(part="snippet,contentDetails,player,statistics",id=video_id).execute()
				vresults = vresults["items"][0]
				title = vresults["snippet"]["title"].replace("'","").replace("%","").encode('utf-8')
				description = vresults["snippet"]["description"].replace("'","").replace("%","").encode('utf-8')
				publishedAt = vresults["snippet"]["publishedAt"]
				length = vresults["contentDetails"]["duration"]
				embed_code = vresults["player"]["embedHtml"]
				view_count = vresults["statistics"]["viewCount"]
				like_count = vresults["statistics"]["likeCount"]
				dislike_count = vresults["statistics"]["dislikeCount"]
				upload_channel = vresults["snippet"]["channelId"]
				q = "INSERT INTO Video SELECT '{0}','{1}','{2}','{3}','{4}','{5}','{6}',{7},{8},{9} WHERE NOT EXISTS (SELECT 1 FROM Video WHERE video_id = '{0}')".format(video_id,upload_channel,title,description,publishedAt,length,embed_code,str(view_count),str(like_count),str(dislike_count)) 
				#(video_id,channel_id,title,description,date,length,embed_code,view_count,like_count,dislike_count)
				cur.execute(q)
				q = "INSERT INTO favorites (video_id, c_id) SELECT '{0}','{1}' WHERE NOT EXISTS (SELECT 1 FROM favorites WHERE video_id = '{0}' AND c_id = '{1}')".format(video_id,ch)
				cur.execute(q)
				thumdict = vresults["snippet"]["thumbnails"]
				for size in thumdict:
					thumurl = thumdict[size]['url']
					width = thumdict[size]['height']
					height = thumdict[size]['height']
					q = "INSERT INTO Thumbnail (t_url, t_width, t_height) SELECT '{0}',{1},{2} WHERE NOT EXISTS (SELECT 1 FROM Thumbnail WHERE t_url = '{0}')".format(thumurl,str(width),str(height))
					cur.execute(q)
					q = "INSERT INTO has_thumb_1 (t_url,video_id) SELECT '{0}','{1}' WHERE NOT EXISTS (SELECT 1 FROM has_thumb_1 WHERE t_url = '{0}' AND video_id = '{1}')".format(thumurl,video_id)
					cur.execute(q)
			except:
				print vresults
				traceback.print_exc()

			# insert into comment table
			try:
				cresults = youtube.commentThreads().list(part="snippet",maxResults=10,videoId=video_id).execute()
				for comm in cresults["items"]:
					commentId = comm["snippet"]["topLevelComment"]["id"]
					commentLikes = comm["snippet"]["topLevelComment"]["snippet"]["likeCount"]
					commentorImage = comm["snippet"]["topLevelComment"]["snippet"]["authorProfileImageUrl"]
					commentDate = comm["snippet"]["topLevelComment"]["snippet"]["updatedAt"]
					commentText = comm["snippet"]["topLevelComment"]["snippet"]["textDisplay"].encode("ascii","ignore").replace("'","").replace("%","")
					commentorName = comm["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"].encode("ascii","ignore").replace("'","").replace("%","")
					q = "INSERT INTO comment (com_id,video_id,text,com_date,display_name, profile_img,like_count) SELECT '{0}','{1}','{2}','{3}','{4}','{5}',{6} WHERE NOT EXISTS (SELECT 1 FROM comment WHERE com_id = '{0}')".format(commentId,video_id,commentText,commentDate,commentorName,commentorImage,str(commentLikes))
					cur.execute(q)
			except:
				traceback.print_exc()
