#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text
from flask import Flask, request, render_template, g, redirect, Response, send_from_directory
from datetime import datetime
import time
import string
import random

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir,static_url_path='',static_folder='static')
app.debug = True
# PROPAGATE_EXCEPTIONS = True

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111a.eastus.cloudapp.azure.com/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@w4111a.eastus.cloudapp.azure.com/proj1part2"
#
DATABASEURI = "postgresql://ql2257:3368@w4111a.eastus.cloudapp.azure.com/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


# Front page of the webpage.  Gets all the users from the db and displays them
@app.route('/')
def index():
  s = text("SELECT * FROM users")
  cursor = g.conn.execute(s)
  users = list(cursor)
  allusers = []
  for user in users:
    userdict = dict(name=user[1],userid=user[0])
    allusers.append(userdict)
  context = dict(allusers = allusers)

  return render_template("index.html", **context)


# routing for static files like the bootstrap css file we use
@app.route('/static/css/<path:filename>')
def send_css(filename):
  return send_from_directory('static/css/',filename)



# Route for the video page.  Give userId and videoId, multiple things happen:
#   * gets the video from the db
#   * gets the comments for that video
#   * trys to get the name of the channel from the db if we're tracking it
#   * updates the watched table for the user recording when the user watched the video
#   * sends all the user info to the browser
@app.route('/<userId>/video/<videoId>/')
def video(userId, videoId):
  s = text("SELECT * FROM video WHERE video_id = :x")
  cursor = g.conn.execute(s,x=videoId)
  vidobj = list(cursor)[0]
  vidtitle = vidobj['title']
  embed = vidobj['embed_code']
  numlikes = vidobj['like_count']
  numdislikes = vidobj['dislike_count']
  views = vidobj["view_count"]
  desc = vidobj["description"]
  date = vidobj["date"]
  cid = vidobj["channel_id"]
  cursor.close()
  s2 = text("SELECT * FROM comment WHERE video_id = :x")
  cursor = g.conn.execute(s2,x=videoId)
  allcomms = []
  for comment in cursor:
    comdict = dict(text=comment['text'],name=comment['display_name'],
      date =comment["com_date"],likes = comment['like_count'])
    allcomms.append(comdict)
  cursor.close()
  try:
    s4 = text("SELECT * FROM channel WHERE c_id = :x")
    cursor = g.conn.execute(s4,x=cid)
    cha = list(cursor)[0]
    cname = cha['c_title']
  except IndexError:
    cname = cid

  curtime = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
  # s3 = text("UPDATE watched SET watch_time=:z WHERE user_id=:x AND video_id=:y; \
  #   INSERT INTO watched (user_id, video_id, watch_time) \
  #   SELECT :x, :y, :z \
  #   WHERE NOT EXISTS (SELECT 1 FROM watched WHERE user_id = :x AND video_id = :y)")
  s3 = text("UPDATE watched SET watch_time=:z WHERE user_id=:x AND video_id=:y; \
    INSERT INTO watched (user_id, video_id, watch_time) \
    SELECT :x, :y, :z \
    WHERE NOT EXISTS (SELECT 1 FROM watched WHERE user_id = :x AND video_id = :y)")

  cursor = g.conn.execute(s3,x=userId,y=videoId,z='{' + curtime + '}')

  s5 = text("(SELECT v1.video_id, v1.title, v1.dislike_count, v1.like_count, v1.view_count, v1.like_count/(1 + v1.dislike_count) AS ratio \
  FROM uploaded_by ub1, video v1 \
  WHERE v1.video_id = ub1.video_id AND ub1.c_id IN (SELECT st1.c_id \
  FROM subscribes_to st1 \
  WHERE st1.user_id = :x) AND v1.video_id NOT IN \
  (select watched.video_id from watched where watched.watch_time[array_length(watch_time,1)] > (SELECT CURRENT_TIMESTAMP - INTERVAL '1 day') AND watched.user_id = :x)\
  AND v1.video_id NOT IN (SELECT skips.video_id FROM skips WHERE skips.user_id = :x)) \
UNION \
(SELECT v.video_id, v.title, v.dislike_count, v.like_count, v.view_count, v.like_count/(1 + v.dislike_count) AS ratio \
  FROM likes_2 ub, video v \
  WHERE v.video_id = ub.video_id AND ub.c_id IN (SELECT st.c_id \
  FROM subscribes_to st \
  WHERE st.user_id = :x) AND v.video_id NOT IN \
  (select watched.video_id from watched where watched.watch_time[array_length(watch_time,1)] > (SELECT CURRENT_TIMESTAMP - INTERVAL '1 day') AND watched.user_id = :x)\
  AND v.video_id NOT IN (SELECT skips.video_id FROM skips WHERE skips.user_id = :x)) \
ORDER BY ratio DESC \
LIMIT 5;")
  cursor = g.conn.execute(s5,x=userId)
  suggested = []
  # a = list(cursor)
  # print a
  for sugvid in cursor:
    s6 = text("SELECT t.t_url FROM has_thumb_1 ht1, thumbnail t WHERE t.t_url = ht1.t_url AND ht1.video_id=:x ORDER BY t.t_width DESC")
    c2 = g.conn.execute(s6,x=str(sugvid["video_id"]))
    # print list(c2)
    vidth = dict(title = '"' + sugvid["title"] + '"', vid = '../' + sugvid["video_id"], thumb = list(c2)[0][0])
    # print vidth
    suggested.append(vidth)


  s6 = text("UPDATE video SET view_count = :y where video_id = :x")
  cursor = g.conn.execute(s6,x=videoId,y=views+1)



  context = dict(title=vidtitle,embhtml=embed,likes=numlikes,
    dislikes = numdislikes,comments = allcomms,views = views,
    desc = desc, date = date, cid = "../../channel/" + cid, cname = cname, suggested = suggested)
  
  return render_template("video.html", **context)



@app.route('/<userId>/video/<videoId>/add_comment', methods=['POST'])
def add_comment(userId, videoId):
    # print videoId
    s = text("INSERT INTO comment (com_id,video_id,text,com_date,display_name,profile_img,like_count) VALUES (:a,:b,:c,:d,:e,:f,:g)")
    comid = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(34))
    comment = request.form['comment']
    comdate = datetime.strftime(datetime.now().date(),"%Y-%m-%d")
    
    s2 = text("SELECT * FROM users WHERE user_id = :x")
    cursor = g.conn.execute(s2, x=userId)
    displayname = list(cursor)[0]['username']
    cursor.close()
    
    s3 = text("SELECT * FROM prof_pic WHERE user_id = :x")
    cursor = g.conn.execute(s3, x=userId)
    profimg = list(cursor)[0]['t_url']
    cursor.close()

    likecount = '0'

    cursor = g.conn.execute(s,a=comid,b=videoId,c=comment,d=comdate,e=displayname,f=profimg,g=likecount)
    # g.db.execute('INSERT INTO comment (com_id,video_id,text,com_date,display_name,profile_img,like_count) values (?,?,?,?,?,?,?)',
    #              [request.form['title'], request.form['text']])
    return redirect('/' + userId + '/video/' + videoId)



# This route is for when a user presses the "like" button on a video.
# It inserts into the likes table the userId and video
# This page is never rendered in the browser, it happens using jquery (I think)
@app.route('/<userId>/video/<videoId>/like',methods=['POST'])
def likevid(userId,videoId):
  s = text("INSERT INTO likes_1 (user_id, video_id) SELECT :x, :y WHERE NOT EXISTS (SELECT 1 FROM likes_1 WHERE user_id = :x AND video_id = :y)")
  cursor = g.conn.execute(s,x=userId,y=videoId)
  s1 = text("SELECT v.like_count FROM video v WHERE v.video_id = :x")
  cursor = g.conn.execute(s1,x=videoId)
  likes = list(cursor)[0][0] + 1
  # print type(likes)
  s2 = text("UPDATE video SET like_count = :y where video_id = :x")
  cursor = g.conn.execute(s2,x=videoId,y=likes)
  return "", 200, {'Content-Type': 'text/plain'}


# This is route for when the user presses the "skip" button on a video
# It inserts into the skips table the userId and video
# Then it goes on the interesting query
# Basically it does the following steps:
#   * Gets all the channels the user subscribes to
#   * From each of those channels, it gets the videos uploaded by the channel and liked by the channel
#   * Then, it removes the videos that were watched by the user in the past day
#   * Then, it removes the videos skipped previously by the user
#   * Then, it orders all these videos by the ratio of likes to dislikes 
#   * Finally, it limits it to just one video
# At the end of this route, it redirects the browser to this top video that the query got
@app.route('/<userId>/video/<videoId>/skip',methods=['POST'])
def skipvid(userId,videoId):
  s = text("INSERT INTO skips (user_id, video_id) SELECT :x, :y WHERE NOT EXISTS (SELECT 1 FROM skips WHERE user_id = :x AND video_id = :y)")
  cursor = g.conn.execute(s,x=userId,y=videoId)

  s2 = text("(SELECT v1.video_id, v1.title, v1.dislike_count, v1.like_count, v1.view_count, v1.like_count/(1 + v1.dislike_count) AS ratio \
  FROM uploaded_by ub1, video v1 \
  WHERE v1.video_id = ub1.video_id AND ub1.c_id IN (SELECT st1.c_id \
  FROM subscribes_to st1 \
  WHERE st1.user_id = :x) AND v1.video_id NOT IN \
  (select watched.video_id from watched where watched.watch_time[array_length(watch_time,1)] > (SELECT CURRENT_TIMESTAMP - INTERVAL '1 day') AND watched.user_id = :x)\
  AND v1.video_id NOT IN (SELECT skips.video_id FROM skips WHERE skips.user_id = :x)) \
UNION \
(SELECT v.video_id, v.title, v.dislike_count, v.like_count, v.view_count, v.like_count/(1 + v.dislike_count) AS ratio \
  FROM likes_2 ub, video v \
  WHERE v.video_id = ub.video_id AND ub.c_id IN (SELECT st.c_id \
  FROM subscribes_to st \
  WHERE st.user_id = :x) AND v.video_id NOT IN \
  (select watched.video_id from watched where watched.watch_time[array_length(watch_time,1)] > (SELECT CURRENT_TIMESTAMP - INTERVAL '1 day') AND watched.user_id = :x)\
  AND v.video_id NOT IN (SELECT skips.video_id FROM skips WHERE skips.user_id = :x)) \
ORDER BY ratio DESC \
LIMIT 1;")
  cursor = g.conn.execute(s2,x=userId)
  vidobj = list(cursor)[0]
  newvidid = vidobj["video_id"]
  s3 = text("SELECT v.dislike_count FROM video v WHERE v.video_id = :x")
  cursor = g.conn.execute(s3,x=videoId)
  dislikes = list(cursor)[0][0] + 1
  # print type(likes)
  s4 = text("UPDATE video SET dislike_count = :y where video_id = :x")
  cursor = g.conn.execute(s4,x=videoId,y=dislikes)

  return redirect('/' + userId + '/video/' + newvidid)




# This is a route for listing the channels a user subscribes to.
@app.route('/<userId>/channel/')
def channels(userId):
  s = text("SELECT * FROM channel c, subscribes_to st WHERE c.c_id = st.c_id and st.user_id = :x")
  cursor = g.conn.execute(s,x=userId)
  allch = []
  for ch in cursor:
    allch.append(dict(cid =  ch["c_id"],ctitle = ch["c_title"],
      cdesc = ch["c_description"],cviews = ch["c_view_count"],
      subs = ch["c_sub_count"]))
  cursor.close()
  for ch in allch:
    s = text("SELECT * FROM thumbnail t where t.t_url in (select ht2.t_url from has_thumb_2 ht2 where c_id = :x)")
    cursor = g.conn.execute(s,x=ch['cid'])
    thumbnail = list(cursor)[0]
    ch['thumb'] = thumbnail['t_url']
    cursor.close()

  s = text("SELECT * FROM users WHERE user_id = :x")
  cursor = g.conn.execute(s,x=userId)
  userobj = list(cursor)[0]
  username = userobj['username']
  cursor.close()

  context = dict(username = username, allch = allch)
  return render_template("channels.html", **context)




# This route is to render a specific channel's information
# If we're not tracking this channel, it just returns "Not Implemented"
@app.route('/<userId>/channel/<channelId>')
def channel(userId, channelId):

  s = text("SELECT * FROM channel WHERE c_id = :x")
  cursor = g.conn.execute(s,x=channelId)
  try:
    chobj = list(cursor)[0]

    chtitle = chobj['c_title']
    desc = chobj['c_description']
    views = chobj['c_view_count']
    subs = chobj['c_sub_count']
    cursor.close()

    s2 = text("select * from thumbnail t where t.t_url in (select ht2.t_url from has_thumb_2 ht2 where c_id = :x)" )
    cursor = g.conn.execute(s2,x=channelId)
    thumbs = []
    for thumb in cursor:
      thumbs.append(thumb['t_url'])
    cursor.close()

    s3 = text("SELECT SUM(like_count) AS total_likes FROM video v, uploaded_by ub WHERE v.video_id = ub.video_id AND ub.c_id = :x GROUP BY ub.c_id")
    cursor = g.conn.execute(s3,x=channelId)
    likes = list(cursor)[0][0]
    cursor.close()

    s4 = text("select v.video_id, v.title from uploaded_by ub, video v where ub.video_id = v.video_id and ub.c_id = :x order by v.view_count desc limit 5")
    cursor = g.conn.execute(s4,x=channelId)
    # top_vids = [i[0] for i in list(cursor)]
    top_vids = []
    for vid in cursor:
      top_vids.append(dict(vid = "../video/" + vid["video_id"],title = vid["title"]))
    cursor.close()
    context = dict(title=chtitle,views=views,subs = subs,desc = desc,thumbs = thumbs,likes = likes,top = top_vids )
  except:
    context = dict(title='Not Implemented',views=0,subs = 0,desc = '',thumbs = [],likes = 0,top = [] )

  return render_template("channel.html", **context)



# This route renders the user's homepage
# It gets the profile pic of the user
# It gets the videos liked by the user
# It gets the videos skipped by the user
# It gets the videos watched by the user
# Then it sends that info to the template
@app.route('/<int:userId>/')
def users(userId):
  s = text("SELECT * FROM users WHERE user_id = :x")
  cursor = g.conn.execute(s,x=userId)
  userobj = list(cursor)[0]
  username = userobj['username']
  cursor.close()

  prof_pic = text("SELECT * FROM prof_pic WHERE user_id = :x")
  cursor = g.conn.execute(prof_pic, x=userId)
  prof_obj = list(cursor)[0]
  prof_url = prof_obj['t_url']
  cursor.close()

  likes_1 = text("SELECT * FROM likes_1 WHERE user_id = :x")
  cursor = g.conn.execute(likes_1, x=userId)
  likevidobjs = list(cursor)
  likevid = []
  for likevidobj in likevidobjs:
    likevid.append(likevidobj['video_id'])
  cursor.close()

  likevideos = []
  for vid in likevid:
    like_vtab = text("SELECT * FROM video WHERE video_id = :x")
    cursor = g.conn.execute(like_vtab, x=vid)
    like_vtabobj = list(cursor)[0]
    likevideos.append(dict(vid = "video/" + vid, title = like_vtabobj['title']))
    cursor.close()

  skips = text("SELECT * FROM skips WHERE user_id = :x")
  cursor = g.conn.execute(skips, x=userId)
  skipvidobjs = list(cursor)
  skipvid = []
  for skipvidobj in skipvidobjs:
    skipvid.append(skipvidobj['video_id'])
  cursor.close()

  skipvideos = []
  for vid in skipvid:
    skip_vtab = text("SELECT * FROM video WHERE video_id = :x")
    cursor = g.conn.execute(skip_vtab, x=vid)
    skip_vtabobj = list(cursor)[0]
    skipvideos.append(dict(vid = "video/" + vid, title = skip_vtabobj['title']))
    cursor.close()

  watched = text("SELECT * FROM watched WHERE user_id = :x")
  cursor = g.conn.execute(watched, x=userId)
  watvidobjs = list(cursor)
  watvid = []
  for watvidobj in watvidobjs:
    watvid.append(watvidobj['video_id'])
  cursor.close()

  watvideos = []
  for vid in watvid:
    wat_vtab = text("SELECT * FROM video WHERE video_id = :x")
    cursor = g.conn.execute(wat_vtab, x=vid)
    wat_vtabobj = list(cursor)[0]
    watvideos.append(dict(vid = "video/" + vid, title = wat_vtabobj['title']))
    cursor.close()

  context = dict(username=username, profurl=prof_url, userid=userId, likevideos=likevideos, skipvideos=skipvideos, watvideos=watvideos, cid= "../"+str(userId)+"/channel/")
  return render_template("user.html", **context)


@app.route('/<int:userId>/search/<searchtext>')
def search(userId,searchtext):
  # alllower = searchtext.lower()
  alllower = " ".join(searchtext.split()).replace(' ',' & ')
  # s = text("SELECT * FROM video WHERE LOWER(video.title) LIKE :x \
  #   OR LOWER(video.description) LIKE :x")
  s = text("SELECT * FROM video where to_tsvector(description) @@ to_tsquery(:x) \
            OR to_tsvector(title) @@ to_tsquery(:x)")
  cursor = g.conn.execute(s,x='%' + alllower + '%')
  searchresults = []
  for vidobj in cursor:
    vidtitle = vidobj['title']
    vidid = '/' + str(userId) + '/video/' + vidobj['video_id']
    searchresults.append(dict(title=vidtitle,vidid = vidid))
  context = dict(results=searchresults)
  return render_template("search.html", **context)









if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=5001, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.debug=True
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
