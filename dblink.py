#Collection V3
# now with Thread Safetey!!!
import sys
import time
import json
import os
import base64
import math
import re
import threading
import psycopg2
conn = None
cur = None

# important to prevent the threaded frontend from clobbering the db connection
cursorlock = threading.RLock()

main_table = "gallery_data"

def raw_query(query):
	global cursorlock
	cursorlock.acquire()
	myresponse = []
	try:
		cur.execute(query)
		myresponse = cur.fetchall()
	except:
		pass
	cursorlock.release()
	return myresponse

def dblink_init(cache_host,cache_database,cache_user,cache_password,default_table,port):
	global conn,cur,main_table
	main_table = default_table
	conn = psycopg2.connect(host=cache_host,database=cache_database,user=cache_user,password=cache_password,connect_timeout=5,port=port)
	cur = conn.cursor()
	
	
def fetch_resource(url,):
	global cur,conn,main_table,fetch_locked,cursorlock
	cursorlock.acquire()
	cur.execute("select * from {} where resource_name = '{}' ;".format(main_table,url))
	result = cur.fetchall()
	cursorlock.release()
	if(len(result)!=0):
		return result[0][1].tobytes();
	else: 
		return b'<h1>404 Not Found</h1>'
		

# Converts resource names into url safe b64 strings and vice versa.
def make_resource_url(url):
	return base64.urlsafe_b64encode(url.encode("utf-8")).decode("utf-8")
	
def read_resource_url(url):
	return base64.urlsafe_b64decode(url).decode("utf-8")