# An excessively over-reverse-engineered search system designed to immitate the search bar on a certain 6 digit website.
# It generally will produce the same results for a given query, and supports a significant number of features to allow for significantly more targeted searches.

# i.e you could search 
# tag:centaur pages:>>40
# to give you all the centaur tagged galleries with more than 40 pages.

operators = ["==",">=","<=",">>","<<","<>","=_","_=","!=",'@>','@<'];
# [eq,gte,lte,lt,gt,contains,startswith,endswith,neq,alph-gt,alph-lt]
classifications = ['|','&']
# [Existential, Universal]
datatypes = ['!','$']
# [Explicit, Variable]
numericopers = ["*","/","-"]
# [multiply,divide,subtract]

aliases = {}
 
def parsealiases(field):
    if(field in aliases.keys()):
        return aliases[field]
    return field

def appendmerge(mydest,mysource):
    for data in mysource:
        if(data not in mydest):
            mydest[data] = mysource[data]
        else:
            mydest[data] = mydest[data] + mysource[data]

def stripsubexpressions(myfilters):
    running = True
    while(running):
        running=False
        i = 0
        while(i<len(myfilters['extra']['subfilters'])):
            #print('Checking subexpr '+str(i))
            if(len(myfilters['extra']['subfilters'][i])==1 and len(myfilters['extra']['subfilters'][i][0]['variables'])==0):
                #print('Stripping...')
                #print('S.E. = '+str(myfilters['extra']['subfilters'][i][0]))
                appendmerge(myfilters['extra'],myfilters['extra']['subfilters'][i][0]['extra'])
                appendmerge(myfilters['nextra'],myfilters['extra']['subfilters'][i][0]['nextra']) 
                running = True
                del (myfilters['extra']['subfilters'])[i]
                i = i - 1
            i = i + 1
        
def getsubexpression(filtertext,mypos,mydest):
    i = mypos
    i = i + 1
    endpos = grabsubquery(filtertext,mypos) 
    mytype = filtertext[endpos:endpos+1]
    if(mytype=="?"):#we have a conditional
        mydest["type"] = "conditional"
        if(filtertext[endpos+1:endpos+2]!="("):
            return endpos+1
        mydest["condition"] ={}
        parseExtraFilter(filtertext[i :endpos-1],mydest["condition"])
        i = getequation(filtertext,"trueval",endpos+2,mydest,False)
        if('trueval' not in mydest.keys()):
            mydest["trueval"] = []
        if(filtertext[i]==":"):
            i = i + 1
        i = getequation(filtertext,"falseval",i+1,mydest,False)
        if('falseval' not in mydest.keys()):
            mydest["falseval"] = []
    if(mytype=="#"):# we have a numeric expression
        i = getequation(filtertext,"expression",i,mydest,True)
        mydest["type"] = "numeric"
        if(filtertext[endpos+1]!="("):
            mydest["numtype"] = "int"
            return endpos+1
        endpos = grabsubquery(filtertext,i+1)
        numtype = filtertext[i+2,endpos-1].lower().strip()
        mydest["numtype"] = numtype
        i = endpos
    if(mytype=="!"):# we are a text equation
        mydest["type"] = "text"
        i = getequation(filtertext,"expression",i,mydest,False)
        i = i + 1
    return i

def getequation(filtertext,myvariable,mypos,mydest,numeric):
    tempfilter = ""
    i = mypos
    explitslice = 0
    myterms = []
    while(filtertext[i]!=" " and filtertext[i]!=")" and i<len(filtertext)):
        if(filtertext[i]=="\""):
            if(tempfilter==""):
                tempfilter = datatypes[0]
            endpos = findendofescape(filtertext,i)
            tempfilter = tempfilter + parseescape(filtertext,i)
            i = endpos
            continue
        elif (filtertext[i]=="("):#sub expression
            tempobject  = {}
            i = getsubexpression(filtertext,i,tempobject)
            tempop = "+"
            if (numericopers.index(filtertext[i])>=0 and numeric):
                tempop = filtertext[i]
            myterms.append([tempobject,tempop])
            if(filtertext[i]=="+" or tempop!="+"):
                i = i + 1
            tempfilter = ""
            explitslice = 0
            continue
        elif (filtertext[i]=="+"):#concatination
            if(tempfilter!=""):
                if(tempfilter[0]==datatypes[1] and explitslice==0):#variable fields must have a slice
                    tempfilter = tempfilter + "[:]"
                myterms.append([tempfilter,"+"])
            tempfilter = ""
            explitslice = 0
        elif (numericopers.index(filtertext[i])>=0 and numeric):#we have an operator that is only supported by numeric equations
            if(tempfilter!=""):
                if(tempfilter[0]==datatypes[1] and explitslice==0):#variable fields must have a slice
                    tempfilter = tempfilter + "[:]"
                myterms.append([tempfilter,filtertext[i]])
            tempfilter = ""
            explitslice = 0
        elif (filtertext[i]=="["):#we have a slice
            endslice = grabslice(filtertext,i,1)
            tempfilter = tempfilter+filtertext[i:endslice]
            i = endslice
            explitslice=1
            continue
        else:
            if(tempfilter==""):#this is the beginning of a term, prepend the type designator if not given
                if(filtertext[i] not in datatypes):
                    tempfilter = tempfilter+ datatypes[0] # default to literal
            tempfilter = tempfilter + filtertext[i]
        i = i + 1
    if(tempfilter!=""):
        if(tempfilter[0]==datatypes[1] and explitslice==0):
            tempfilter = tempfilter + "[:]"
        myterms.append([tempfilter,""])
    mydest[myvariable] = myterms
    return i+1

def grabsubquery(mytext,mypos):
    deapth =0
    i = mypos
    while(i<len(mytext) and (deapth>0 or mypos==i)):
        if(mytext[i]=="\""):
            i = i + 1
            while(i<len(mytext) and mytext[i]!="\""):
                if(mytext[i:i+2]=="\\\""):
                    i = i + 1
                i = i + 1
            i = i + 1
            continue
        if(mytext[i]=="("):
            deapth = deapth + 1
        if(mytext[i]==")"):
            deapth = deapth - 1
        i = i + 1
    return i

def grabslice(mytext,mypos,dir):
    i = mypos
    while((i<len(mytext) and dir==1 and (mytext[i]!="]")) or (i>=0 and dir==-1 and (mytext[i]!="["))):
        i = i + dir
    if(dir==1):
        i = i + 1
    else:
        if(i<0):
            i=0
    return i

def findendofescape(filtertext,mypos):
    i = mypos
    if(filtertext[i]=="\""):
        i = i + 1
        while(i<len(filtertext) and filtertext[i]!="\""):
            if(filtertext[i:i+2]=="\\\""):
                i = i + 2
                continue
            if(filtertext[i:i+2]=="\\n"):
                i = i + 2
                continue
            i = i + 1
        i = i + 1
    return i

def parseescape(filtertext,mypos):
    i = mypos
    tempfilter = ""
    if(filtertext[i]=="\""):
        i = i + 1
        while(i<len(filtertext) and filtertext[i]!="\""):
            if(filtertext[i:i+2]=="\\\""):
                tempfilter = tempfilter + "\""
                i = i + 2
                continue
            if(filtertext[i:i+2]=="\\n"):
                tempfilter = tempfilter + "\n"
                i = i + 2
                continue
            tempfilter = tempfilter + filtertext[i]
            i = i + 1
    return tempfilter

def parseExtraFilter(filtertext,myfilters):
    filtertext = filtertext.strip()+" "
    i = 0
    anonset = []
    explitslice = 0
    tempfield = ""
    tempfilter = ""
    tempneg = False
    myfilters['extratext'] = filtertext.strip()
    myfilters['variables'] = {}
    myfilters['extra'] =({
        'subfilters': [],
        'anonymous': [] #the filters which dont have a specified field to apply to
    })
    myfilters['nextra'] =({
        'subfilters': [],
        'anonymous': []
    })
    while(i<len(filtertext)):
        if(filtertext[i]=="("):# we are now in the subquery parser, this is special...
            tempfilterset = []
            while(filtertext[i]!=" " and i<len(filtertext)):
                tempfilter = {}
                endindex = grabsubquery(filtertext,i)
                parseExtraFilter(filtertext[i+1:endindex-1],tempfilter)
                if((endindex-i)-2>0):
                    tempfilterset.append(tempfilter)
                i = endindex
                while(filtertext[i]!=" " and filtertext[i]!="(" and i<len(filtertext)):
                    i = i + 1
            if(len(tempfilterset)>0):
                if(tempneg):
                    myfilters['nextra']['subfilters'].append(tempfilterset)
                else:
                    myfilters['extra']['subfilters'].append(tempfilterset)         
            tempneg = False
            tempfilter = ""
            tempfield = ""
            anonset = []
            i = i + 1
            continue
        if(filtertext[i]=="\""):
            if(tempfilter==""):
                tempfilter = classifications[0] + operators[5]
            if(len(tempfilter)==3):
                tempfilter = tempfilter + datatypes[0]
            endpos = findendofescape(filtertext,i)
            tempfilter = tempfilter + parseescape(filtertext,i)
            i = endpos
            continue
        elif(filtertext[i]==":"):
            tempfield = tempfilter.lower()
            if(len(tempfield)>4):
                tempfield = tempfield[4:]# trim classification, operator and type designator from our field name
            tempfield=parsealiases(tempfield)
            tempfilter = ""
            explitslice=0
        elif(filtertext[i]==","):
            if(tempfilter!=""):
                if(explitslice==0 and tempfilter[3]==datatypes[1]):#we have a field, and no slice... so we add a [:], non operative slice.
                    tempfilter = tempfilter + "[:]"
                anonset.append(tempfilter)
            explitslice = 0
            tempfilter = ""
        elif(filtertext[i]=="=" and tempfilter!=""):#we have an equation
            if(len(tempfilter)<5):# we dont have a valid variable name, so ignore it.
                while(filtertext[i]!=" " and i<len(filtertext)):
                    i=i+1
                i=i+1
                continue
            tempfilter = tempfilter[4:]
            i = getequation(filtertext,tempfilter,i+1,myfilters['variables'])
            tempneg = False
            tempfilter = ""
            tempfield = ""
            anonset = []
            continue
        elif(filtertext[i]=="["):#we have a slice
            endslice = grabslice(filtertext,i,1)
            tempfilter = tempfilter+filtertext[i:endslice]
            i = endslice
            explitslice=1
            continue
        elif(filtertext[i]=="-"):
            tempneg = True
        elif(filtertext[i]==" "):#we are pushing this element out now.
            if(tempfield!=""):# We are an explicitly mapped element
                #print (tempfilter)
                if(explitslice==0 and tempfilter[3]==datatypes[1]):#we have a field, and no slice... so we add a [:], non operative slice.
                    tempfilter = tempfilter + "[:]"
                if(not tempneg):#this element is positive
                    if(tempfilter!=""):
                        anonset.append(tempfilter)
                    if(len(anonset)>0):
                        if(tempfield not in myfilters['extra'].keys()):
                            myfilters['extra'][tempfield] = []
                        myfilters['extra'][tempfield].append(anonset)

                else:#this element is negative
                    if(tempfilter!=""):
                        anonset.append(tempfilter)
                    if(len(anonset)>0):
                        if(tempfield not in myfilters['nextra'].keys()):
                            myfilters['nextra'][tempfield] = []
                        myfilters['nextra'][tempfield].append(anonset)      
            else:
                if(tempfilter!=""):
                    anonset.append(tempfilter)
                if(len(anonset)>0):
                    if(tempneg):
                        myfilters['nextra']['anonymous'].append(anonset)
                    else:
                        myfilters['extra']['anonymous'].append(anonset)     
            anonset = []
            tempfield = ""
            tempfilter = ""
            explitslice = 0
            tempneg = False
        else: #generic characters are added to our current token (tempfilter)
            #print ('adding generic character')
            if(tempfilter==""):# we need a clasification. Currently: | -Existential, & -Universal
                #print('  adding classification')
                if filtertext[i] not in classifications:
                    tempfilter = classifications[0]
                    #print('    none given, infering: '+classifications[0])
                else:
                    tempfilter = filtertext[i]
                    #print('    classification: '+tempfilter)
                    i = i + 1
                    continue
            if(len(tempfilter)==1):#we need an operator to prefix text
                #print('  adding operator')
                if(filtertext[i:i+2] not in operators):
                    tempfilter = tempfilter + operators[5]
                    #print('    none given, infering: '+operators[5])
                else:
                    tempfilter = tempfilter + filtertext[i:i+2]
                    #print('    operator: '+tempfilter[-2:])
                    i = i + 2
                    continue
            if(len(tempfilter)==3):#we need a type, either ! for literal, or $ for field
                #print('  adding type')
                if(filtertext[i] not in datatypes):
                    #print('    none given, infering: '+ datatypes[0])
                    tempfilter = tempfilter+ datatypes[0] # default to literal
                else:
                    tempfilter = tempfilter + filtertext[i]
                    i = i + 1
                    #print('    type: '+tempfilter[-1:])
                    continue
            tempfilter = tempfilter + filtertext[i]
        i=i+1
    stripsubexpressions(myfilters)

def parseSorter(filtertext,myfilters):
    filtertext = filtertext.lower().strip()+" "
    i = 0
    anonset = []
    explitslice = 0
    tempfield = ""
    tempfilter = ""
    myfilters['extratext'] = filtertext.strip()
    myfilters['variables'] = {}
    while(i<len(filtertext)):
        if(filtertext[i]==":"):
            if(explitslice==0):#we have a field, and no slice... so we add a [:], non operative slice.
                tempfilter = tempfilter + "[:]"
            tempfield = tempfilter
            tempfield=parsealiases(tempfield)
            tempfilter = ""
            explitslice=0
        elif(filtertext[i]=="["):#we have a slice
            endslice = grabslice(filtertext,i,1)
            tempfilter = tempfilter+filtertext[i:endslice]
            i = endslice
            explitslice=1
            continue
        elif(filtertext[i]=="=" and tempfilter!=""):#we have an equation
            if(len(tempfilter)<3):# we dont have a valid variable name, so ignore it.
                while(filtertext[i]!=" " and i<len(filtertext)):
                    i=i+1
                i=i+1
                continue
            tempfilter = tempfilter[3:]
            i = getequation(filtertext,tempfilter,i+1,myfilters['variables'])
            tempneg = False
            tempfilter = ""
            tempfield = ""
            explitslice =0
            continue
        elif(filtertext[i]==" "):#we are pushing this element out now.
            if(tempfield!=""):# We are an explicitly mapped element
                if(tempfilter!=""):
                    anonset.append(tempfield)
                    anonset.append(tempfilter)
            explitslice =0
            tempfield = ""
            tempfilter = ""
        else:#generic characters are added to our current token (tempfilter)
            tempfilter = tempfilter + filtertext[i]
        i=i+1
    myfilters['sortorders'] = anonset

def compareElements(myobj1,myobj2,mysort):
    myvariables1 = {}
    myvariables2 = {}
    assemblevariables(mysort,myvariables1,myobj1)#Make variables for both elements
    assemblevariables(mysort,myvariables2,myobj2)
    i = 0
    while(i<len(mysort['sortorders'])):        
        string1 = evalstring(datatypes[1]+mysort['sortorders'][i],myvariables1,myobj1).lower()
        string2 = evalstring(datatypes[1]+mysort['sortorders'][i],myvariables2,myobj2).lower()
        if('.' not in string1):
            string1 = string1 + '.'
        if('.' not in string2):
            string2 = string2 + '.'
        if(string1num.index('.')>string2num.index('.')):
            string2num = padstringL('0',string2num,string1num.index('.')-string2num.index('.'))
        if(string1num.index('.')<string2num.index('.')):
            string1num = padstringL('0',string1num,string2num.index('.')-string1num.index('.'))

        myvariablename = mysort.sortorders[i][0:grabslice(mysort.sortorders[i],len(mysort.sortorders[i])-1,-1)];
        if(isreference(myvariablename,myobj1) and (type(getreference(myvariablename,myobj1)) in [int,float])):
            string1 = string1num
            string2 = string2num
        
            
        if(mysort['sortorders'][i+1]=='<'):
            if (string1 < string2):
                return -1
            if (string1 > string2):
                return 1
        if(mysort['sortorders'][i+1]=='>'):
            if (string1 > string2):
                return -1
            if (string1 < string2):
                return 1
        if(mysort['sortorders'][i+1]=='#<'):
            if (string1 < string2):
                return -1
            if (string1 > string2):
                return 1
        if(mysort['sortorders'][i+1]=='#>'):
            if (string1 > string2):
                return -1
            if (string1 < string2):
                return 1

            
        i = i + 2
    return 0

def evalsubexpr(myexpr,myvariables,myobject):
    retval = ""
    if("conditional" == myexpr['type']):
        if(compareSubFilter(myobject,myexpr['condition'],myvariables.copy())):
            retval =  evalequation(myexpr['trueval'],myvariables,myobject)
        else:
            retval =  evalequation(myexpr['falseval'],myvariables,myobject)
        return retval
    if("numeric" == myexpr['type']):
        return evalnumequation(myexpr['expression'],myvariables,myobject,myexpr['numtype'])
    if("text" == myexpr['type']):
        return evalequation(myexpr['expression'],myvariables,myobject)
    return ""

def evalnum(mystring,mytype):
    if(mytype == "int"):
        return Math.floor(parseFloat(trimleadingzeroes(mystring)))
    if(mytype == "float"):
        return parseFloat(trimleadingzeroes(mystring))
    return 0

def isreference(mypath,myobject):
    i = 0
    mypath = mypath.split('.')
    while(i<len(mypath)):
        if(mypath[i] not in myobject.keys() or (not isinstance(myobject[mypath[i]],dict) and (i!=len(mypath)-1))):
            return False
        myobject = myobject[mypath[i]]
        i = i + 1
    return True

def getreference(mypath,myobject):
    i = 0
    mypath = mypath.split('.')
    while(i<len(mypath)):
        myobject = myobject[mypath[i]]
        i = i + 1
    return myobject

def evalstring(mystring,myvariables,myobject):# handles field referencing, and slicing
    if(mystring==""):
        return ""
    if(mystring[0:1]==datatypes[0]):
        return mystring[1:].lower()
    i = grabslice(mystring,len(mystring)-1,-1)
    myslice = mystring[i:]
    myvariablename = mystring[1:i]
    
    if(isreference(myvariablename,myobject)):
        mystring = getreference(myvariablename,myobject)#fetch from data object
    elif(myvariablename in myvariables.keys()):
        mystring = myvariables[myvariablename]# if the object doesnt have it, check our variables
    else:
        mystring = str(mystring).lower()#trim and lowercase the data field
    myslice = myslice[1,-1]
    myslice = myslice.split(":")
    if(len(myslice)!=2):
        return mystring# something is wrong with our slice, ignore it.
    startindex = 0
    if(myslice[0]!=""):
        startindex = parseInt(myslice[0])
        if(startindex<0):
            startindex = startindex+len(mystring)
    endindex = len(mystring)
    if(myslice[1]!=""):
        endindex = parseInt(myslice[1])
        if(endindex<0):
            endindex = endindex+len(mystring)
    return mystring[startindex:endindex]

def trimleadingzeroes(mystring):
    tempstring = mystring.strip()
    i = 0
    while(i<len(tempstring) and tempstring[i]=="0"):
        i=i+1
    return tempstring[i:]

def evalequation(myequation,myvariables,myobject):
    tempstring = ""
    i=0
    while(i<len(myequation)):
        if(isinstance(myequation[i][0], str)):
            tempstring = tempstring + evalstring(myequation[i][0],myvariables,myobject)
        else:
            tempstring = tempstring + evalsubexpr(myequation[i][0],myvariables,myobject)
        i=i+1
    return tempstring

def evalnumequation(myequation,myvariables,myobject,mytype):
    lastop = "+"
    tempstring = ""
    tempres = 0
    tempval = 0
    i=0
    while(i<len(myequation)):
        if(isinstance(myequation[i][0], str)):
            tempstring = evalstring(myequation[i][0],myvariables,myobject)
        else:
            tempstring = evalsubexpr(myequation[i][0],myvariables,myobject)
        tempval = evalnum(tempstring,mytype)
        if(lastop=="+"):
            tempres = tempres + tempval
        elif(lastop=="-"):
            tempres = tempres - tempval
        elif(lastop=="*"):
            tempres = tempres * tempval
        elif(lastop=="/"):
            tempres = tempres / tempval
        lastop = myequation[i][1]
        if(mytype=="int"):
            tempres = math.floor(tempres)
        i=i+1
    return str(tempres)

def assemblevariables(myfilters,myvariables,myobject):
    i = 0
    for varname in myfilters['variables']:
        myvariables[varname] = evalequation(myfilters['variables'][varname],myvariables,myobject)
        

def  compareFilter(testelement,myfilters):
    #myfilters is an object populated by the setExtraFilters() def.
    #testelement is the object to be filtered.
    #returns TRUE if the object passes the filter, FALSE if it fails.
    return compareSubFilter(testelement,myfilters, {})

def  compareSubFilter(testelement,myfilters,myvariables): #compare an element to our set of custom filters
    assemblevariables(myfilters,myvariables,testelement)
    i = 0
    j = 0
    curstate = ({
        'passfail': True, # a running state of the explicit passes
        'anonmatch': [], # an array of the anonymous filter satisfaction results, used to calculate wether an objects fields collectively satisfy every anonymous filter
        'anonfail': []
    })
    if('anonymous'  in myfilters['extra'].keys()):
        i = 0
        while(i<len(myfilters['extra']['anonymous'])): #fill the anon state holders with initial values.
            curstate['anonmatch'].append(False)
            curstate['anonfail'].append(False)
            i = i + 1
    for varname in myvariables:# iterate over all variables (but dont run anon filters)
        compareFilterElement(myvariables[varname].lower(),varname,curstate,myfilters,myvariables,testelement)
        compareNegFilterElement(myvariables[varname].lower(),varname,curstate,myfilters,myvariables,testelement)
   
    for alertfield in testelement:# iterate over all fields in the testelement
        #if(typeof(testelement[alertfield])=="string")    # if there is a mix of data types in the object, then add this to ensure that it only attmpts to filter on the strings
        #          (or add something to turn the non string objects into strings.)
        companon(testelement[alertfield],curstate,myfilters,myvariables,testelement)
        compareFilterElement(testelement[alertfield],alertfield.lower(),curstate,myfilters,myvariables,testelement)
        
        compNanon(testelement[alertfield],curstate,myfilters,myvariables,testelement)
        compareNegFilterElement(testelement[alertfield],alertfield.lower(),curstate,myfilters,myvariables,testelement)
    i = 0
    while(i<len(myfilters['extra']['subfilters'])): #run all of our subqueries    
        hit = False
        j=0
        while(j<len(myfilters['extra']['subfilters'][i])): #run all of our subquery elements
            hit = hit  or  compareSubFilter(testelement,myfilters['extra']['subfilters'][i][j],myvariables.copy())
            j = j + 1
        curstate['passfail'] = (curstate['passfail']  and  (hit or j==0))
        i=i+1
    i=0
    while(i<len(myfilters['nextra']['subfilters'])): #run all of our negative subqueries
        hit = True
        j=0
        while(j<len(myfilters['nextra']['subfilters'][i])): #run all of our negative subquery elements
            hit = hit and compareSubFilter(testelement,myfilters['nextra']['subfilters'][i][j],myvariables.copy())
            j=j+1
        curstate['passfail'] = (curstate['passfail']  and  (not hit or j==0))
        i = i + 1
    curstate['passfail'] = (curstate['passfail']  and  matchimplies(curstate['anonfail'],curstate['anonmatch']))# ensure that if we failed an anon check, then we made at least one anon match
    return curstate['passfail']

def matchimplies(a,b):# returns true iff Ax => Bx for all x, used to verify that all of the anonymous filters were satisfied.
    i = 0
    impval = True
    while(i<len(a)):    
        impval = impval  and  ((not a[i]) or (b[i]))
        i=i+1
    return impval

#compares the testelement string to the operator prefaced criterion.
# "DOG" , ">>!CAT" returns weather "DOG">"CAT"
def padstringL(padding,target,count):
    i = 0
    while(i<count):
        target = padding + target
        i = i + 1
    return target

def comparenumbers(myoper,string1,string2):
    if('.' not in string1):
        string1 = string1 + '.'
    if('.' not in string2):
        string2 = string2 + '.'
    if(string1.index('.')>string2.index('.')):
        string2 = padstringL('0',string2,string1.index('.')-string2.index('.'))
    if(string1.index('.')<string2.index('.')):
        string1 = padstringL('0',string1,string2.index('.')-string1.index('.'))
    
    if(myoper==1): # >=
        return   (string1>=string2)
    if(myoper==2): # <=
        return   (string1<=string2)
    if(myoper==3): # >>
        return   (string1>string2)
    if(myoper==4): # <<
        return   (string1<string2)
    
def compareField(testelement,criterion,myvariables,myobject):
    cdata = ""
    myclass = criterion[0]
    myoper = operators.index(criterion[1:3])
    if(myoper>=0):
        cdata = evalstring(criterion[3:],myvariables,myobject)
    if(isinstance(testelement,str)):
        return compareStrings(testelement.lower(),myoper,cdata,myvariables,myobject)
    if(isinstance(testelement,list)):
        if(myclass==classifications[0]):#existential
            temp = False
            for data in testelement:
                temp = temp or compareStrings(str(data).lower(),myoper,cdata,myvariables,myobject)
            return temp
        if(myclass==classifications[1]):#universal
            temp = True
            for data in testelement:
                temp = temp and compareStrings(str(data).lower(),myoper,cdata,myvariables,myobject)
            return temp
    return compareStrings(str(testelement).lower(),myoper,cdata,myvariables,myobject)
    return True

def compareStrings(testelement,myoper,cdata,myvariables,myobject):
    if(myoper==0): # ==
        return  (testelement==cdata)
    if(myoper in [1,2,3,4]): # >= <= >> <<
        return   comparenumbers(myoper,testelement,cdata)
    if(myoper==5): # <>
        return   (cdata in testelement)
    if(myoper==6): # =_
        return  testelement.startswith(cdata)
    if(myoper==7): # _=
        return   testelement.endswith(cdata)
    if(myoper==8): # !=
        return  (testelement!=cdata)
    if(myoper==9): # @>
        return  (testelement>cdata)
    if(myoper==10): # @<
        return  (testelement<cdata)
    return  True#We somehow didnt get a valid operator, so we gracefully defer. (perhaps it is an empty sting)
   
def compareFilterElement(testelementfield,filter,curstate,myfilters,myvariables,myobject):#compares a single field of our element to the appropriate filters
    if(isinstance(testelementfield,dict)):
        for data in testelementfield:
            compareFilterElement(testelementfield[data],filter+'.'+data.lower(),curstate,myfilters,myvariables,myobject)
        return

    j = 0
    total = True
    hits = False
    if(filter in myfilters['extra'].keys()):
        while(j< len(myfilters['extra'][filter])):
            hits = False
            i=0
            while(i<len(myfilters['extra'][filter][j])): #iterate over all of the options for this field's filter
                hits = hits  or  compareField(testelementfield,myfilters['extra'][filter][j][i],myvariables,myobject)
                i=i+1
            total = total  and  (hits or i==0)
            j=j+1
        if(total):
            return
        curstate['passfail'] = False# if we had a explicit rule we wanted to match and it didnt fit

def compareNegFilterElement(testelementfield,filter,curstate,myfilters,myvariables,myobject):#compares a single field of our element to the appropriate exclusion filters
    if(isinstance(testelementfield,dict)):
        for data in testelementfield:
            compareNegFilterElement(testelementfield[data],filter+'.'+data.lower(),curstate,myfilters,myvariables,myobject)
        return
    i = 0
    j = 0
    if(filter in myfilters['nextra'].keys()):
        while(j< len(myfilters['nextra'][filter])):
            hits = True
            i=0
            while(i<len(myfilters['nextra'][filter][j])): #iterate over all of the options for this field's filter
                hits = hits  and  compareField(testelementfield,myfilters['nextra'][filter][j][i],myvariables,myobject)# we must match all of the elements in this exclusion field to be excluded.
                i = i + 1
            curstate['passfail'] = curstate['passfail']  and  ((not hits) or i==0)
            j = j + 1
        
def compNanon(testelementfield,curstate,myfilters,myvariables,myobject):# compares the object field to the anonymous exclusion filters
    i = 0
    j = 0
    if(isinstance(testelementfield,dict)):
        for data in testelementfield:
            compNanon(testelementfield[data],curstate,myfilters,myvariables,myobject)
        return
    while(i<len(myfilters['nextra']['anonymous'])):
        hits = True
        j=0
        while(j<len(myfilters['nextra']['anonymous'][i])):
            hits = hits  and  compareField(testelementfield,myfilters['nextra']['anonymous'][i][j],myvariables,myobject)
            j =  j + 1
        curstate['passfail'] = curstate['passfail']  and  (not hits)
        i = i + 1

def companon(testelementfield,curstate,myfilters,myvariables,myobject):# compares the object field to the anonymous filters
    i = 0
    j = 0
    if(len(myfilters['extra']['anonymous'])==0):#if we have no anonymous filters, then we pass.
        curstate['anonmatch'].append(True)
        curstate['anonfail'].append(False)
        return
    if(isinstance(testelementfield,dict)):
        for data in testelementfield:
            companon(testelementfield[data],curstate,myfilters,myvariables,myobject)
        return
    while(i<len(myfilters['extra']['anonymous'])):
        j=0
        while(j<len(myfilters['extra']['anonymous'][i])):
            if(compareField(testelementfield,myfilters['extra']['anonymous'][i][j],myvariables,myobject)):
                curstate['anonmatch'][i] = True
                break
            j = j + 1
        curstate['anonfail'][i] = True
        i = i + 1

def filterElements(mydata,myfilter):
    newdata = []
    for data in mydata:
        if(compareFilter(data,myfilter)):
            newdata.append(data)
    return newdata
