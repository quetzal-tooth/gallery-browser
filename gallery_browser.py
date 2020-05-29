import dblink
import flaskWrap
from requests_html import HTML
import traceback
from flask import request
import sys
import json
import gallery_search
from html import escape,unescape
import urllib
import prog_cache
import random

def pullpage(url,forcerefresh=False):
	result = dblink.fetch_resource(url,forcerefresh)
	return HTML(html=result.decode("utf-8"))
	

mydetails = open("credentials.json")
mycredentials = json.loads(mydetails.read())
mydetails.close()



''' 
Index table schema:
 gallery_id text primary key
 pages bigint
 title text
 index_block text
 thumbnail text
 images text[]
'''

'''
Data table schema:
 resource_name text primary key
 data_block bytea
'''

''' sample index entry
[
	'gal_1', 
	3, 
	'some_galelry_title', 
	'{"id": "gal_1", "title": "some_galelry_title", "title_jpn": "", "parody": ["pokemon"], "character": ["misty"], "tag": ["schoolgirl uniform", "uncensored"], "artist": ["some dude"], "group": [], "language": ["translated", "english"], "category": ["doujinshi"], "pages": 3, "thumbnail": "/mnt/collection/gallery1/1.jpg"}, 
	'/mnt/temp/gallery1/1.jpg',
	['/mnt/temp/gallery1/1.jpg',/mnt/temp/gallery1/2.jpg,/mnt/temp/gallery1/3.jpg]
]

Most of the data is stored in the json block, because the system originally used a local json file as its index. The index was moved to the db as the collection was migrated, but I haven't gotten around to duplicating the search functionality in sql yet.
'''





dblink.dblink_init(cache_host=mycredentials["host"],cache_database=mycredentials["database"],cache_user=mycredentials["user"],cache_password=mycredentials["password"],default_table=mycredentials["data_table"],port=mycredentials["port"])

def refreshData():
	global my_galleries,myindexedindex,myimage_pages,myindex
	dblink.cursorlock.acquire()
	dblink.cur.execute("select * from gallery_index order by gallery_id desc;")
	my_galleries = {}
	myindexedindex = {}
	myimage_pages = {}
	myindex = []
	myresp = dblink.cur.fetchall()
	for data in myresp:
		myindex.append(json.loads(data[3]))
		myindexedindex[data[0]] = myindex[-1]
		myimage_pages[data[0]] = data[5]
		my_galleries[data[0]] = data
	dblink.cursorlock.release()
	
refreshData()
	
def my_root():
	global my_galleries,myindex
	rootfile = open("local/gallery_main.html","r")
	mypageroot = rootfile.read()
	rootfile.close()
	mypagenum = 1
	try:
		mypagenum = request.args.get('page')
		if(not mypagenum):
			mypagenum = 1
	except:
		pass
	results = myindex[25*(int(mypagenum)-1):25*(int(mypagenum))]
	mypagecontent = makeTileContainer(results) + makePageBar(mypagenum,int((len(myindex)-1)/25)+1,"/?page=")
	mypage = mypageroot.replace('<title></title>','<title>Gallery-Archive</title>',1).replace('<div id="content"></div>','<div id="content">'+mypagecontent+'</div>')
	
	
	return mypage
	
flaskWrap.set_root(my_root)
	
	
def makeCoverThumbnail(gallery_id,page):
	myimg = getimg(gallery_id,page)
	return '''<img class="lozad" data-src="'''+myimg+'''" alt="" width="250" height="353">
		<noscript>
			<img src="'''+myimg+'''" width="250" height="353" alt="" />
		</noscript>'''
		
def makePageThumbnail(gallery_id,page):
	myimg = getimg(gallery_id,page)
	return '''<div class="thumb-container">
				<a class="gallerythumb" href="/proc/g/'''+str(gallery_id)+'''/'''+str(page)+'''/" rel="nofollow">
					<img class="lozad" data-src="'''+myimg+'''" alt="" width="200" height="282">
		<noscript>
			<img src="'''+myimg+'''" width="200" height="282" alt="" />
		</noscript>
		</a>
	</div>'''
		
def makePageTile(gallery_id):
	#data-tags 6346 jpn 12227 eng
	#as per nh css
	try:
		target_galleries = my_galleries[gallery_id]
		targetindex = myindexedindex[gallery_id]
		datatags = ''
		for data in targetindex["language"]:
			if(data=='english'):
				datatags = datatags + '12227'
			if(data=='japanese'):
				datatags = datatags + '6346'
		return '''<div class="gallery" data-tags="'''+datatags+'''">
	<a href="/proc/g/'''+str(gallery_id)+'''/" class="cover" style="padding:0 0 141.2% 0">
		'''+ makeCoverThumbnail(gallery_id,1)+'''
		<div class="caption">'''+escape(target_galleries[2])+'''</div>
	</a>
</div>'''
	except:
		traceback.print_exc()
		return '''<div class="gallery" data-tags="1234">Error</div>'''
		
def getimg(gallery,page):
	target_galleries = my_galleries[gallery]
	return "/res/"+dblink.make_resource_url(myimage_pages[gallery][int(page)-1])

def makePageBar(curpage,totpages,prefix,suffix='',setkeybinds=True,beforefirst=None,afterlast=None):
	i = max(int(curpage)-5,1)
	mypagebar = '''<section class="pagination">'''
	if(curpage!=1):
		mypagebar = mypagebar + '''<a href="'''+prefix+'''1'''+suffix+'''" class="first"><i class="fa fa-chevron-left"></i><i class="fa fa-chevron-left"></i></a>
	<a href="'''+prefix+str(int(curpage)-1)+suffix+'''" class="previous"><i class="fa fa-chevron-left"></i></a>'''
	elif(beforefirst):
		mypagebar = mypagebar + '''<a href="'''+beforefirst+'''" class="previous"><i class="fa fa-chevron-left"></i></a>'''
	while(i<=(int(curpage)+5) and i<=int(totpages)):
		mypagebar = mypagebar + '''<a href="'''+prefix+str(i)+suffix+'''" class="page '''+("current" if i==int(curpage) else "")+'''">'''+str(i)+'''</a>'''
		i = i + 1;
	if(int(curpage)!=int(totpages)):
		mypagebar = mypagebar + '''<a href="'''+prefix+str(int(curpage)+1)+suffix+'''" class="next"><i class="fa fa-chevron-right"></i></a>
	<a href="'''+prefix+str(totpages)+suffix+'''" class="last"><i class="fa fa-chevron-right"></i><i class="fa fa-chevron-right"></i></a>'''
	elif(afterlast):
		mypagebar = mypagebar + '''<a href="'''+afterlast+'''" class="last"><i class="fa fa-chevron-right"></i></a>'''
	mypagebar = mypagebar + '''</section>'''
	myscript = ''
	if(setkeybinds):
		myscript = '''<script> '''
		myscript = myscript + '''current_page='''+str(curpage)+''';page_count='''+str(totpages)+''';prev_chap="'''+str(beforefirst)+'''";next_chap="'''+str(afterlast)+'''";'''
		if(int(curpage)>1):
			myscript = myscript + '''onarrow_prev_page="'''+prefix+str(int(curpage)-1)+suffix+'''";'''
		elif(beforefirst):
			myscript = myscript + '''onarrow_prev_page="'''+beforefirst+'''";'''
		if(int(curpage)<int(totpages)):
			myscript = myscript + '''onarrow_next_page="'''+prefix+str(int(curpage)+1)+suffix+'''";'''
		elif(afterlast):
			myscript = myscript + '''onarrow_next_page="'''+afterlast+'''";'''
		
		myscript = myscript + '''</script>'''
	
	return mypagebar+myscript
	
def makeTileContainer(galleries):
	myblock = '<div class="container index-container">\n'
	for data in galleries:
		myblock = myblock + makePageTile(data["id"])
	myblock = myblock+'<div class="container index-container">'
	return myblock
		
def makeTagList(tagtype,taglabel,tags):
	myset = '''<div class="tag-container field-name '''+("hidden" if len(tags)==0 else "")+'''">'''
	myset = myset + escape(taglabel) + '''\n<span class="tags">'''
	for data in tags:
		myset = myset + '''<a href="/proc/search/?q='''+urllib.parse.quote_plus(tagtype+':=="'+data+'"')+'''" class="tag">
								'''+escape(data)+''' 
								<span class="count"></span>
							</a>\n'''
	myset = myset + '''</span>\n</div>\n'''
	return myset
	
def makeGalleryHeader(galleryindex):
	gallery_id  = galleryindex["id"]
	
	myheader = '''<div class="container" id="bigcontainer">
		<div id="cover">
			<a href="/proc/g/'''+gallery_id+'''/1/">
				<img class="lozad" data-src="'''+getimg(gallery_id,1)+'''" alt="" width="350" height="494"><noscript><img src="'''+getimg(gallery_id,1)+'''" width="350" height="494" alt="" /></noscript>
			</a>
		</div>
		<div id="info-block">
			<div id="info">
				<h1>''' +escape(galleryindex["title"])+'''</h1>
				<h2>''' +escape(galleryindex["title_jpn"])+'''</h2>'''
				
	myheader = myheader + makeTagBlock(galleryindex)
	myheader = myheader + '''			<div>'''+str(galleryindex["pages"])+''' page'''+("" if galleryindex["pages"]==1 else "s")+'''</div>'''
	myheader = myheader + '''		</div>
		</div>
	</div>'''
	return myheader
	
def makeGalleryPage(gallery,forceurl=False):
	rootfile = open("local/gallery_main.html","r")
	mypageroot = rootfile.read()
	rootfile.close()
	galleryindex = myindexedindex[gallery[0]]
	mypagecontent = makeGalleryHeader(galleryindex) + '\n' + makeGalleryTileSet(gallery)
	if(forceurl):
		mypagecontent = mypagecontent + '<script>page_url_override="/proc/g/'+str(gallery[0])+'/";</script>'
	mypage = mypageroot.replace('<title></title>','<title>'+escape(galleryindex["title"])+'</title>',1).replace('<div id="content"></div>','<div id="content">'+mypagecontent+'</div>',1)
	return mypage
	
def makeGalleryTileSet(gallery):
	mytiles = '''<div class="container" id="thumbnail-container">\n'''
	i = 1
	while(i<=gallery[1]):
		mytiles = mytiles + makePageThumbnail(gallery[0],i)+'\n'
		i = i + 1
	mytiles = mytiles + '''</div>'''
	return mytiles
	
	
def makeTagBlock(galleryindex):
	myset = '''<section id="tags">\n'''
	myset = myset + makeTagList("parody","Parodies:",galleryindex["parody"])
	myset = myset + makeTagList("character","Characters:",galleryindex["character"])
	myset = myset + makeTagList("tag","Tags:",galleryindex["tag"])
	myset = myset + makeTagList("artist","Artists:",galleryindex["artist"])
	myset = myset + makeTagList("group","Groups:",galleryindex["group"])
	myset = myset + makeTagList("language","Languages:",galleryindex["language"])
	myset = myset + makeTagList("category","Categories:",galleryindex["category"])
	myset = myset + '''</section>\n'''
	return myset
	
def doSearch(myrequest):
	myfilter = {}
	myquery = request.args.get('q')
	results = prog_cache.get_cached("queries",myquery)
	if(results==None):
		gallery_search.parseExtraFilter(myquery,myfilter)
		results = gallery_search.filterElements(myindex,myfilter)
		prog_cache.add_cached("queries",myquery,results)
	resultcount = len(results)
	mypagenum = 1
	try:
		mypagenum = request.args.get('page')
		if(not mypagenum):
			mypagenum = 1
	except:
		pass
	if(mypagenum!=0):
		results = results[25*(int(mypagenum)-1):25*(int(mypagenum))]
	
	if(len(myrequest)==1):
		return json.dumps(results)
	if(myrequest[1]=="debug"):
		mypage = "<span>Query: "+escape(myquery)+"</span><br/>\n"
		mypage = mypage + "<span>"+escape(str(len(results))+" Results Found")+"</span><br/><br/>\n"
	else:
		rootfile = open("local/gallery_main.html","r")
		mypageroot = rootfile.read()
		rootfile.close()
		mypageroot = mypageroot.replace('''name="q" value=""''','''name="q" value="'''+myquery.replace("&","&amp;").replace('"',"&quot;")+'''"''')
		mypagecontent  = '''<h2>'''+str(resultcount)+''' Results</h2>'''
		mypagecontent = mypagecontent + makeTileContainer(results) + makePageBar(mypagenum,int((resultcount-1)/25)+1,"/proc/search/?q="+urllib.parse.quote_plus(myquery)+"&page=")
		mypage = mypageroot.replace('<title></title>','<title>Search: '+escape(myquery+" >> NH-Archive")+'</title>',1).replace('<div id="content"></div>','<div id="content">'+mypagecontent+'</div>')
	return mypage
		
		
def makeImagePageBar(target_galleries,curpage,myid,pageselection=True):
	i = max(int(curpage)-5,1)
	mypagebar = '''<section class="pagination" id="'''+myid+'''">'''
	if(curpage!=1):
		mypagebar = mypagebar + '''<a href="/proc/g/'''+str(target_galleries[0])+'''/1/" class="first"><i class="fa fa-chevron-left"></i><i class="fa fa-chevron-left"></i></a>
	<a href="/proc/g/'''+str(target_galleries[0])+'''/'''+str(int(curpage)-1)+'''/" class="previous"><i class="fa fa-chevron-left"></i></a>'''
	
	if(pageselection):
		while(i<=(int(curpage)+5) and i<=int(target_galleries[2])):
			mypagebar = mypagebar + '''<a href="/proc/g/'''+str(target_galleries[0])+'''/'''+str(i)+'''/" class="page '''+("current" if i==int(curpage) else "")+'''">'''+str(i)+'''</a>'''
			i = i + 1;
	else:
		mypagebar = mypagebar + '''<button class="page-number btn btn-unstyled"><span class="current">'''+str(curpage)+'''</span> <span class="divider">of</span> <span class="num-pages">'''+str(target_galleries[1])+'''</span></button>'''
	if(int(curpage)!=int(target_galleries[1])):
		mypagebar = mypagebar + '''<a href="/proc/g/'''+str(target_galleries[0])+'''/'''+str(int(curpage)+1)+'''/" class="next"><i class="fa fa-chevron-right"></i></a>
	<a href="/proc/g/'''+str(target_galleries[0])+'''/'''+str(target_galleries[1])+'''/" class="last"><i class="fa fa-chevron-right"></i><i class="fa fa-chevron-right"></i></a>'''
	mypagebar = mypagebar + '''</section>'''
	return mypagebar
	
def makeImagePage(target_galleries,page):
	
	rootfile = open("local/gallery_main.html","r")
	mypageroot = rootfile.read()
	rootfile.close()
	galleryindex = myindexedindex[target_galleries[0]]
	mypagecontent = '''<div class="container" id="page-container">'''
	mypagecontent = mypagecontent + makeImagePageBar(target_galleries,page,"pagination-page-top",False)
	
	nextpage = "/proc/g/"+str(target_galleries[0])+"/"+str(int(page)+1)+"/"
	if(int(page)==target_galleries[1]):
		nextpage = "/proc/g/"+str(target_galleries[0])+"/"
	mypagecontent = mypagecontent + '''<section id="image-container" class="fit-horizontal full-height">
				<a href="'''+nextpage+'''">
			<img src="'''+getimg(target_galleries[0],page)+'''" width="1280">
			</a>
		</section>'''
	
	mypagecontent = mypagecontent+ makeImagePageBar(target_galleries,page,"pagination-page-bottom",False)
	mypagecontent = mypagecontent+  '''<div class="back-to-gallery"><a href="/proc/g/'''+str(target_galleries[0])+'''/">Back to gallery</a></div>'''
	mypagecontent = mypagecontent+ '''</div>'''
	
	prevpage = "/proc/g/"+str(target_galleries[0])+"/"+str(max(int(page)-1,1))+"/"
	
	i = 1
	myimages = []
	while(i<=int(target_galleries[1])):
		myimages.append(getimg(target_galleries[0],i))
		i = i + 1
		
	
	
	myscript = '''<script>'''
	
	if(int(page)>1):
		myscript = myscript + '''onarrow_prev_page="'''+prevpage+'''";'''
	if(int(page)<target_galleries[1]):
		myscript = myscript + '''onarrow_next_page="'''+nextpage+'''";'''
		
	myscript = myscript + '''</script>'''

		
	mypage = mypageroot.replace('<title></title>','<title>'+escape(galleryindex["title"])+'</title>',1).replace('<div id="content"></div>','<div id="content">'+mypagecontent+'\n'+myscript+'</div>')
	return mypage
	

	
def my_handler(resource):
	global my_galleries,myindex
	myrequest = resource.split("/")
	mypage = "<h2>Sorry, We cant find what you're looking for.</h2>"
	print(myrequest)
	if(myrequest[0]=="g"):
		target_galleries = my_galleries[(myrequest[1])]
		if(len(myrequest)>=3 and myrequest[2]!=""):
			return makeImagePage(target_galleries,myrequest[2])
		return makeGalleryPage(target_galleries)
			
	if(myrequest[0]=="search"):
		return doSearch(myrequest)
			
	if(myrequest[0]=="refresh"):
		refreshData()
		prog_cache.flush_cached()
		return '<script>window.location="/"</script>'
			
	return mypage
	
flaskWrap.set_handler(my_handler)

flaskWrap.start(port=5003)