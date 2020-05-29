import time 
import threading

prog_cache_lock = threading.RLock()
prog_caches= {}
 
def flush_cached(cacheset=None):
	global prog_caches
	if(cacheset==None):
		prog_caches= {}
	else:
		prog_caches[cacheset] = []
 
def get_cached(cacheset,targetkey):
		prog_cache_lock.acquire()
		if(cacheset in prog_caches):
			cacheset = prog_caches[cacheset]
		else:
			prog_cache_lock.release()
			return None
		for data in cacheset:
			if(data["key"]==targetkey):
				data["used"] = time.time()
				prog_cache_lock.release()
				return data["data"]
		prog_cache_lock.release()
		return None
		
def add_cached(cacheset,targetkey,val,maxentries=10):
		prog_cache_lock.acquire()
		if(cacheset in prog_caches):
			cacheset = prog_caches[cacheset]
		else:
			prog_caches[cacheset] = []
			cacheset = prog_caches[cacheset]
			
		minset = 0;
		minused = time.time()
		i=0;
		for data in cacheset:
			if(data["key"]==targetkey):
				data["used"] = time.time()
				data["data"] = val
				prog_cache_lock.release()
				return
			if(minused>data["used"]):
				minset = i
				minused = data["used"]
			i = i + 1
		if(len(cacheset)<maxentries):
			cacheset.append({"key":targetkey,"data":val,"used":time.time()})
		else:
			if(i>=len(cacheset)):
				i = minset
			cacheset[i] = {"key":targetkey,"data":val,"used":time.time()}
		prog_cache_lock.release()