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
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
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
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


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


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
  return redirect('/')


@app.route('/video/<videoId>')
def video(videoId):
  s = text("SELECT * FROM video WHERE video_id = :x")
  cursor = g.conn.execute(s,x=videoId)
  vidobj = list(cursor)[0]
  vidtitle = vidobj['title']
  embed = vidobj['embed_code']
  numlikes = vidobj['like_count']
  numdislikes = vidobj['dislike_count']
  cursor.close()
  s2 = text("SELECT * FROM comment WHERE video_id = :x")
  cursor = g.conn.execute(s2,x=videoId)
  allcomms = []
  for comment in cursor:
    comdict = dict(text=comment['text'],name=comment['display_name'],
      date =comment["com_date"],likes = comment['like_count'])
    allcomms.append(comdict)
  cursor.close()




  context = dict(title=vidtitle,embhtml=embed,likes=numlikes,
    dislikes = numdislikes,comments = allcomms)
  return render_template("video.html", **context)


@app.route('/user/<int:userId>')
def users(userId):
  print request.args
  print userId
  print type(userId)
  #
  # example of a database query
  #
  # cursor = g.conn.execute("SELECT name FROM test")
  # try:  
  # cursor = g.conn.execute("SELECT * FROM video WHERE video_id = '3dhKRWB1_IA'")
  # cursor = g.conn.execute("SELECT * FROM video WHERE video_id = '{0}'".format(videoId))
  # print "SELECT * FROM video WHERE video_id = '{0}'".format(videoId)
  # cursor = g.conn.execute("SELECT * FROM video limit 5")
  s = text("SELECT * FROM users WHERE user_id = :x")
  cursor = g.conn.execute(s,x=userId)
  userobj = list(cursor)[0]
  # print "197"
  # for result in cursor:
  #   names.append(result['video_id'])  # can also be accessed using result[0]
  username = userobj['username']
  cursor.close()
  #print username

  prof_pic = text("SELECT * FROM prof_pic WHERE user_id = :x")
  cursor = g.conn.execute(prof_pic, x=userId)
  prof_obj = list(cursor)[0]
  prof_url = prof_obj['t_url']
  cursor.close()

  likes_1 = text("SELECT * FROM likes_1 WHERE user_id = :x")
  cursor = g.conn.execute(likes_1, x=userId)
  likevidobj = list(cursor)[0]
  likevid = []
  likevid.append(likevidobj['video_id'])
  cursor.close()
  #print likevid

  likevideos = []
  for vid in likevid:
    like_vtab = text("SELECT * FROM video WHERE video_id = :x")
    cursor = g.conn.execute(like_vtab, x=vid)
    like_vtabobj = list(cursor)[0]
    likevideos.append(dict(vid = "../video/" + vid, title = like_vtabobj['title']))
    cursor.close()

  skips = text("SELECT * FROM skips WHERE user_id = :x")
  cursor = g.conn.execute(skips, x=userId)
  skipvidobj = list(cursor)[0]
  skipvid = []
  skipvid.append(skipvidobj['video_id'])
  cursor.close()
  #print skipvid

  skipvideos = []
  for vid in skipvid:
    skip_vtab = text("SELECT * FROM video WHERE video_id = :x")
    cursor = g.conn.execute(skip_vtab, x=vid)
    skip_vtabobj = list(cursor)[0]
    skipvideos.append(dict(vid = "../video/" + vid, title = skip_vtabobj['title']))
    cursor.close()

  watched = text("SELECT * FROM watched WHERE user_id = :x")
  cursor = g.conn.execute(watched, x=userId)
  watvidobj = list(cursor)[0]
  watvid = []
  watvid.append(watvidobj['video_id'])
  cursor.close()
  #print watvid

  watvideos = []
  for vid in watvid:
    wat_vtab = text("SELECT * FROM video WHERE video_id = :x")
    cursor = g.conn.execute(wat_vtab, x=vid)
    wat_vtabobj = list(cursor)[0]
    watvideos.append(dict(vid = "../video/" + vid, title = wat_vtabobj['title']))
    cursor.close()

  #context = dict(username=username, userid=userId, likevid=likevid, skipvid=skipvid, watvid=watvid)
  context = dict(username=username, profurl=prof_url, userid=userId, likevideos=likevideos, skipvideos=skipvideos, watvideos=watvideos)
  return render_template("user.html", **context)



@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


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
    app.debug = True
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()