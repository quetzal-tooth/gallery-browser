from flask import Flask
import dblink
import os
import sys
import base64
import prog_cache
app = Flask(__name__)

@app.route('/')
def app_root():
	global myroot
	return myroot()

def hello_world(*args):
    return 'Hello, World!'
	
@app.route('/local/<path:resource>') # route for resources stored on local storage. Used for static resources such as css and js files, as well as icons etc.
def app_local(resource):
	resourcepath = "local/"+resource
	mydata = prog_cache.get_cached("flaskWrap_local",resourcepath)
	if(mydata==None):
		if(not os.path.isfile(resourcepath)):
			prog_cache.add_cached('flaskWrap_local',resourcepath,"<h1>404 Not Found</h1>")
			return "<h1>404 Not Found</h1>"
		myres = open(resourcepath,"rb")
		mydata = myres.read()
		myres.close()
		prog_cache.add_cached('flaskWrap_local',resourcepath,mydata,32)
	return mydata

resCacheSize = 100
	
@app.route('/res/<path:resource>') # route for resources fetched from primary database
def app_res(resource):
	myurl = dblink.read_resource_url(resource) # base64 encode resource names so that characters in file paths dont break the url
	respdata = prog_cache.get_cached("flaskWrap_res",myurl)
	if(respdata==None):
		print(myurl)
		respdata =  dblink.fetch_resource(myurl) 
		prog_cache.add_cached("flaskWrap_res",myurl,respdata,resCacheSize)
	return respdata
	

	
@app.route('/proc/<path:resource>') # route for procedurally handled urls
def app_proc(resource):
	global myhandler
	return myhandler(resource)
	
myhandler = hello_world	
myroot = hello_world

def set_handler(new_handler):
	global myhandler
	myhandler = new_handler
	
def set_root(new_handler):
	global myroot
	myroot = new_handler

def start(**args):
	global app
	app.run(**args)
	
if __name__ == '__main__':
    start()
	
	
