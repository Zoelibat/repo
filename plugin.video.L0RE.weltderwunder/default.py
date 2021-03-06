#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import xbmcvfs
import urllib, urllib2, socket, cookielib, re, os, shutil,json
import time
import base64
import requests
from bs4 import BeautifulSoup
from HTMLParser import HTMLParser

# Setting Variablen Des Plugins
global debuging
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()
# Lade Sprach Variablen
translation = addon.getLocalizedString




xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)


icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')


profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")

if xbmcvfs.exists(temp):
  shutil.rmtree(temp)
xbmcvfs.mkdirs(temp)
cookie=os.path.join( temp, 'cookie.jar')
cj = cookielib.LWPCookieJar();

if xbmcvfs.exists(cookie):
    cj.load(cookie,ignore_discard=True, ignore_expires=True)                  

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    

  
def addDir(name, url, mode, thump, desc="",page=1,serie=""):   
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&serie="+str(serie)
  ok = True
  liz = xbmcgui.ListItem(name)  
  liz.setArt({ 'fanart' : thump })
  liz.setArt({ 'thumb' : thump })
  liz.setArt({ 'banner' : icon })
  liz.setArt({ 'fanart' : icon })
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
	
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok
  
def addLink(name, url, mode, thump, duration="", desc="", genre='',director="",bewertung="",serie=""):
  debug("URL ADDLINK :"+url)
  debug( icon  )
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&serie="+str(serie)
  ok = True
  liz = xbmcgui.ListItem(name,thumbnailImage=thump)
  liz.setArt({ 'fanart' : icon })
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre, "Director":director,"Rating":bewertung,"TVShowTitle":serie})
  liz.setProperty('IsPlayable', 'true')
  liz.addStreamInfo('video', { 'duration' : duration })
	#xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
  return ok
  
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict


def geturl(url,data="x",header="",referer=""):
        global cj
        debug("Get Url: " +url)
        for cook in cj:
          debug(" Cookie :"+ str(cook))
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))        
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
        if header=="":
          opener.addheaders = [('User-Agent', userAgent)]        
        else:
          opener.addheaders = header        
        if not referer=="":
           opener.addheaders = [('Referer', referer)]

        try:
          if data!="x" :
             content=opener.open(url,data=data).read()
          else:
             content=opener.open(url).read()
        except urllib2.HTTPError as e:
             #debug( e.code )  
             cc=e.read()  
             debug("Error : " +cc)
             content=""
       
        opener.close()
        cj.save(cookie,ignore_discard=True, ignore_expires=True)               
        return content


  
def liste():   
    addDir("Alle Sendungen" , "http://www.weltderwunder.de/sendungen", "videoliste","")   
    addDir("Themen" , "http://www.weltderwunder.de/videos", "themen","")   
    addLink("Live", "", 'playlive', "")
    addDir("Search", "", 'search', "")
    addDir("Settings", "", 'Settings', "")
    xbmcplugin.endOfDirectory(addon_handle) 

def playvideo(url):    
    quality=addon.getSetting("quality")  
    content=geturl(url)
    videoliste=re.compile('<iframe class="embed-responsive-item" src="(.+?)"', re.DOTALL).findall(content)[0]
    debug("playvideo videoliste :"+videoliste)
    content=geturl(videoliste)
    videos=re.compile('kalturaIframePackageData = \{(.+?)\};', re.DOTALL).findall(content)[0]    
    videos_json="{"+videos+"}"
    struktur = json.loads(videos_json)  
  #Ziel         http://cloudfront.cdn.vidoo.de/p/102/sp/10200/playManifest/entryId/0_uay1cwio/flavorId/0_ajyzewx3/format/url/protocol/http/a.mp4
  #Quelle       http:\/\/cloudfront.cdn.vidoo.de/p/102/sp/10200/playManifest/entryId/0_oa0rw00d                   /format\/url\/protocol\/http
    videofile=struktur["entryResult"]["meta"]["dataUrl"]
    debug("VFILE :"+videofile)
    max=0
    videofound=""
    for format in struktur["entryResult"]["contextData"]["flavorAssets"]:
        if format["videoCodecId"]=="avc1":                     
            height=int(format["height"])
            debug("height :"+ str(height))
            debug(format)
            idd=format["id"]
            entryId=format["entryId"]
            videourl="http://cloudfront.cdn.vidoo.de/p/102/sp/10200/playManifest/entryId/"+entryId+"/flavorId/"+idd+"/format/url/protocol/http/a.mp4"             
            if height>=max and height<=int(quality):
               max=height
               videofound=videourl            
    listitem = xbmcgui.ListItem(path=videofound)   
    addon_handle = int(sys.argv[1])  
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
def themen(url):
    content=geturl(url)    
    xbmcplugin.setContent(addon_handle, 'tvshows')
    htmlPage = BeautifulSoup(content, 'html.parser')
    themen = htmlPage.find_all("h2",attrs={"class":"h2-videos h2-index-videos"})  
    for thema in themen:
      themenlink = thema.find("a")
      title=thema.text.encode("utf-8").replace("» Alle Anzeigen","")
      debug("--------") 
      debug(title)
      link="http://weltderwunder.de"+themenlink["href"]
      addDir(title,link,"themenseite","")  
    xbmcplugin.endOfDirectory(addon_handle)

def  themenseite(url,page=1):
     xbmcplugin.setContent(addon_handle, 'episodes')
     newurl=url+"_load?page="+str(page)
     content=geturl(newurl)
     htmlPage = BeautifulSoup(content, 'html.parser') 
     Videos = htmlPage.find_all("div",attrs={"class":"col-md-3 col-sm-6 item-video item-video-global"})  
     for video in Videos:
       debug("-----")
       debug(video)
       name = video.find("h4").text.encode("utf-8")
       link = "http://weltderwunder.de"+video.find("a")["href"]
       bild = video.find("img")["src"]
       desc=video.find("p").text.encode("utf-8")
       durationstring=video.find("div",attrs={"class":"item-video-duration-global"}).text.encode("utf-8")
       duration=re.compile('([0-9]+:[0-9]+)', re.DOTALL).findall(durationstring)[0]    
       debug(name)
       debug(bild)
       debug(link)
       addLink(name,link,"playvideo",bild,duration=duration,desc=desc)
     addDir("Next",url,"themenseite","",page=int(page)+1)
     xbmcplugin.endOfDirectory(addon_handle)
    
params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
referer = urllib.unquote_plus(params.get('referer', ''))
page= urllib.unquote_plus(params.get('page', ''))
serie= urllib.unquote_plus(params.get('serie', ''))

def videoliste(url):  
  content=geturl(url)
  xbmcplugin.setContent(addon_handle, 'tvshows')
  htmlPage = BeautifulSoup(content, 'html.parser')
  serien = htmlPage.find_all("div",attrs={"class":"col-md-3 col-sm-3 col-xs-6 program-thumbnail"})  
  for sserie in serien:   
    
    debug("-->")
    debug(serien)     
    img=sserie.find("img")["src"]
    link=sserie.find("a")["href"]
    link="http://weltderwunder.de"+link
    title=re.compile('.+/([^/]+)$', re.DOTALL).findall(link)[0]
    addDir(title,link,"listserie",img,serie=title)  
  xbmcplugin.endOfDirectory(addon_handle)
def   listserie(url,serie=""):
   content=geturl(url)
   xbmcplugin.setContent(addon_handle, 'tvshows')
   htmlPage = BeautifulSoup(content, 'html.parser')
   staffeln_liste = htmlPage.find("select",attrs={"class":"form-control"})  
   staffeln = staffeln_liste.find_all("option") 
   for staffel in staffeln:
     debug("listserie Staffe : ")
     debug(staffel)
     addDir(staffel.text,url+"?staffel="+str(staffel["value"]),"staffelliste","",serie=serie)  
   xbmcplugin.endOfDirectory(addon_handle)
  
def staffelliste(url,serie=""):
  xbmcplugin.setContent(addon_handle, 'episodes')
  content=geturl(url)
  htmlPage = BeautifulSoup(content, 'html.parser')
  folgen = htmlPage.find_all("div",attrs={"class":"col-md-3 col-sm-6 item-video item-video-global"})  
  for folge in folgen:
    debug("-->")
    debug(folge)
    img=folge.find("img")["src"]
    link=folge.find("a")["href"]
    desc=folge.find("p").text.encode("utf-8")
    durationstring=folge.find("div",attrs={"class":"item-video-duration-global"}).text.encode("utf-8")
    duration=re.compile('([0-9]+:[0-9]+)', re.DOTALL).findall(durationstring)[0]    
    link="http://weltderwunder.de"+link
    title=folge.find("h4").text
    addLink(title,link,"playvideo",img,desc=desc,duration=duration,serie=serie)  
  xbmcplugin.endOfDirectory(addon_handle)
def playlive():
 url="http://www.weltderwunder.de/videos/live"
 content=geturl(url)
 htmlPage = BeautifulSoup(content, 'html.parser')
 videoinfo = htmlPage.find("iframe")["src"]
 content=geturl(videoinfo)
 debug(content)
 videoliste=re.compile('"applehttp",url":"(.+?)"', re.DOTALL).findall(content)[0]
 videoliste=videoliste.replace("\\/","/")
 listitem = xbmcgui.ListItem(path=videoliste)   
 addon_handle = int(sys.argv[1])  
 xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
 

def search():   
   dialog = xbmcgui.Dialog()
   d = dialog.input(translation(30010), type=xbmcgui.INPUT_ALPHANUM)
   newurl="http://www.weltderwunder.de/ "
   content=geturl(newurl)
   token=re.compile('name="csrf-token" content="(.+?)"', re.DOTALL).findall(content)[0]   
   url="http://www.weltderwunder.de/search/find"   
   userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"       
   header = [('User-Agent', userAgent),
             ('X-CSRF-Token' , token),
             ('X-Requested-With', 'XMLHttpRequest'),
             ('Accept', '*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript')]           
   values ={'query' : d,
            'utf8':"✓"}
   data = urllib.urlencode(values)
   content=geturl(url,data=data,header=header)
   htmlcode=re.compile(".html\('(.+)'\);", re.DOTALL).findall(content)[0]   
   htmlcode=htmlcode.replace("\/","/").replace('\\"','"')
   debug(htmlcode)
   htmlPage = BeautifulSoup(htmlcode, 'html.parser')
   debug(htmlPage)
   videos = htmlPage.find_all("li",attrs={"class":"row"})  
   for video in videos:
      debug("---->")
      debug(video)
      try:
        img=video.find("img")["src"]
        link="http://weltderwunder.de"+video.find("a")["href"]
        name=video.find("div",attrs={"class":"results-info-global"}).text.encode("utf-8").replace("\\n","").replace("\t","").strip()
        debug("+ "+name)
        debug("+ "+link)
        debug("+ "+img)
        if "VIDEO" in name:
          name=name.replace("VIDEO","")
          addLink(name,link,"playvideo",img)  
      except:
        debug("---->ERROR")
   xbmcplugin.endOfDirectory(addon_handle)
 
# Haupt Menu Anzeigen      
if mode is '':
     liste()   
else:
  # Wenn Settings ausgewählt wurde
  if mode == 'Settings':
          addon.openSettings()
  # Wenn Kategory ausgewählt wurde
  if mode == 'playvideo':
          playvideo(url)
  if mode == 'subrubrik':
          subrubrik(url)
  if mode == 'videoliste':
          videoliste(url)  
  if mode == 'listserie':
          listserie(url,serie)
  if mode == 'staffelliste':
          staffelliste(url,serie)  
  if mode == 'themen':
          themen(url)
  if mode == 'themenseite':
          themenseite(url,page)  
  if mode == 'playlive':
          playlive()
  if mode == 'search':
          search()           