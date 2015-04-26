#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import urllib
import urllib2
import socket
import sys
import re
import json
import xbmcplugin
import xbmcaddon
import xbmcgui

# addon = xbmcaddon.Addon()
# addonID = addon.getAddonInfo('id')
addonID = "plugin.video.arte_tv"
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
forceViewMode = addon.getSetting("forceView") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewMode = str(addon.getSetting("viewIDNew"))
addonDir = xbmc.translatePath(addon.getAddonInfo('path'))
defaultFanart = os.path.join(addonDir ,'fanart.png')
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
baseUrl = "http://www.arte.tv"
baseUrlConcert = "http://concert.arte.tv"
language = addon.getSetting("language")
language = ["de", "fr"][int(language)]
maxVideoQuality = addon.getSetting("maxVideoQuality")
maxVideoQuality = ["480p", "720p"][int(maxVideoQuality)]
streamingType = addon.getSetting("streamingType")
streamingType = ["HTTP", "RTMP"][int(streamingType)]

guide = '%s/guide/%s' % (baseUrl, language)
new_json = 'plus7.json'
selection_json = 'plus7/selection.json'
lastchance_json = 'plus7/derniere_chance.json'
mostviewed_json = 'plus7/plus_vues.json'


def jsonUrl(jsonfile, regions=''):
    url = '%s/%s' % (guide, jsonfile)
    if regions:
        url = '%s?regions=%s' % (url, regions)
    return url


def index():
    content = getUrl(baseUrl+"/artews/js/geolocation.js")
    match = re.compile('arte_geoip_zone_codes.+?return new Array\\((.+?)\\)',
                       re.DOTALL).findall(content)
    regionFilters = match[0].split(",")
    regionFilter = ""
    for filter in regionFilters:
        regionFilter += filter.replace("'", "").strip()+"%2C"
    regionFilter = regionFilter[:-3]
    addDir(translation(30001), jsonUrl(new_json),
           "listVideosNew", "")
    addDir(translation(30002), jsonUrl(selection_json, regionFilter),
           "listVideosNew", "")
    addDir(translation(30003), jsonUrl(lastchance_json, regionFilter),
           "listVideosNew", "")
    addDir(translation(30004), jsonUrl(mostviewed_json, regionFilter),
           "listVideosNew", "")
    addDir(translation(30005), "by_channel", "listCats", "", regionFilter)
    addDir(translation(30006), "by_cluster", "listCats", "", regionFilter)
    addDir(translation(30007), "by_date", "listCats", "", regionFilter)
    addDir(translation(30008), "", "search", "")
    addDir(translation(30012), "", "listConcertsMain", "")
    if regionFilter != "ALL":
        addLink(translation(30009), "", "playLiveStream", icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def str_item(item):
    '''Convert item to utf-8 encoded string object'''
    if not item:
        item = ''
    if not isinstance(item, basestring):
        try:
            item = str(item)
        except:
            item = ''
    return item.encode('utf-8', 'replace')


def listVideosNew(url):
    xbmcplugin.setContent(pluginhandle, "episodes")
    content = getUrl(url)
    content = json.loads(content)
    for item in content["videos"]:
        title = str_item(item.get("title", "No Title"))
        desc = str_item(item.get("desc", ""))
        duration = str_item(item.get("duration", ""))
        date = str_item(item.get("airdate_long", ""))
        url = str_item(item.get("url", ""))
        thumb = str_item(item.get("image_url", ""))
        channels = str_item(item.get("video_channels", ""))
        views = str_item(item.get("video_views", ""))
        until = str_item(item.get("video_rights_until", ""))
        rank = str_item(item.get("video_rank", ""))

        desc = views+"   |   "+date+"\n"+channels+"\n"+desc
        addLink(title,
                baseUrl+url,
                'playVideoNew',
                thumb,
                desc,
                duration,
                )
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listSearchVideos(urlMain):
    xbmcplugin.setContent(pluginhandle, "episodes")
    try:
        content = getUrl(urlMain)
        spl = content.split('<div class="video-block has-play"')
        for i in range(1, len(spl), 1):
            entry = spl[i]
            match = re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
            title = match[0]
            match = re.compile('data-description="(.+?)"', re.DOTALL).findall(entry)
            desc = ""
            if match:
                desc = match[0]
            match = re.compile('<p class="time-row">.+?<span class=".+?">.+?</span>(.+?)</p>.+?<p class=".+?">.+?<span class=".+?">.+?</span>(.+?)</p>', re.DOTALL).findall(entry)
            if match:
                date = match[0][0].strip()
                desc = date+"\n"+desc
                duration = match[0][1].strip()
                duration = duration.split(" ")[0]
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = match[0]
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            addLink(title, url, 'playVideoNew', thumb, desc, duration)
        currentPage = urlMain[urlMain.find("page=")+5:]
        nextPage = str(int(currentPage)+1)
        addDir(translation(30010), urlMain.replace("page="+currentPage,"page="+nextPage), "listSearchVideos", "")
    except:
        pass
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listCats(type, regionFilter):
    content = getUrl(baseUrl+"/guide/"+language+"/plus7")
    content = content[content.find('<ul class="span12" data-filter="'+type+'">'):]
    content = content[:content.find('</ul>')]
    match = re.compile('<a href="(.+?)" data-controller="catchup" data-action="refresh" >(.+?)</a>', re.DOTALL).findall(content)
    for url, title in match:
        title = title
        url = baseUrl+url.replace("?", ".json?").replace("&amp;", "&")+"&regions="+regionFilter
        addDir(title, url, 'listVideosNew', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def search():
    keyboard = xbmc.Keyboard('', translation(30008))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        if language == "de":
            url = "http://www.arte.tv/guide/de/suchergebnisse?keyword="+search_string+"&page=1"
        elif language == "fr":
            url = "http://www.arte.tv/guide/fr/resultats-de-recherche?keyword="+search_string+"&page=1"
        listSearchVideos(url)


def listConcertsMain():
    addDir(translation(30002), "", "listConcerts", "")
    addDir("Collections", "", "listCollections", "")
    addDir(translation(30011), baseUrlConcert+"/"+language+"/videos/all", "listConcerts", "")
    addDir(translation(30013), baseUrlConcert+"/"+language+"/videos/rockpop", "listConcerts", "")
    if language=="de":
        addDir(translation(30014), baseUrlConcert+"/de/videos/klassische-musik", "listConcerts", "")
    else:
        addDir(translation(30014), baseUrlConcert+"/fr/videos/musique-classique", "listConcerts", "")
    addDir(translation(30015), baseUrlConcert+"/"+language+"/videos/jazz", "listConcerts", "")
    if language=="de":
        addDir(translation(30016), baseUrlConcert+"/de/videos/weltmusik", "listConcerts", "")
    else:
        addDir(translation(30016), baseUrlConcert+"/fr/videos/musique-du-monde", "listConcerts", "")
    if language=="de":
        addDir(translation(30017), baseUrlConcert+"/de/videos/tanz", "listConcerts", "")
    else:
        addDir(translation(30017), baseUrlConcert+"/fr/videos/danse", "listConcerts", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listConcerts(url=""):
    if not url:
        url = baseUrlConcert+"/"+language
    content = getUrl(url)
    content = content[:content.find('<div class="video_box_tab_1')]
    spl = content.split('<article')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = baseUrlConcert+match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("/alw_rectangle_376/","/alw_rectangle_690/").replace("/alw_highlight_480/","/alw_rectangle_690/")
        if "node-eventp" in entry:
            addDir(title, url, "listConcerts", thumb)
        elif "node-videop" in entry:
            addLink(title, url, 'playVideoNew', thumb, "")
    match = re.compile('<li class="pager-next">.+?href="(.+?)"', re.DOTALL).findall(content)
    if match:
        addDir(translation(30010), baseUrlConcert+match[0], "listConcerts", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listCollections():
    content = getUrl("http://concert.arte.tv/"+language+"/collections.xml")
    spl = content.split('<item>')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<title>(.+?)</title>', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile('field-name-eventp-videos-count.*?&gt;(.+?)&lt;', re.DOTALL).findall(entry)
        if match:
            count = match[0].strip()
            if language=="de":
                count = count.replace("vidéos","Videos")
            title += " ("+count+")"
        match = re.compile('<link>(.+?)</link>', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('data-src=&quot;(.+?)&quot;', re.DOTALL).findall(entry)
        thumb = match[0].replace("/alw_rectangle_376/","/alw_rectangle_690/").replace("/alw_highlight_480/","/alw_rectangle_690/")
        addDir(title, url, "listConcerts", thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideoNew(url):
    listitem = xbmcgui.ListItem(path=getStreamUrlNew(url))
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def getStreamUrlNew(url):
    content = getUrl(url)
    match = re.compile('arte_vp_url=[\'"](.+?)[\'"]', re.DOTALL).findall(content)
    if "concert.arte.tv" in url:
        url = match[0]
        content = getUrl(url)
        match1 = re.compile('"HTTP_SQ_1":.+?"url":"(.+?)"', re.DOTALL).findall(content)
        match2 = re.compile('"HTTP_EQ_1":.+?"url":"(.+?)"', re.DOTALL).findall(content)
        match3 = re.compile('"RMTP_HQ":.*?"streamer":"(.+?)","url":"(.+?)"', re.DOTALL).findall(content)
        if match1 and maxVideoQuality == "720p":
            return match1[0].replace("\\","")
        elif match2:
            return match2[0].replace("\\","")
        elif match3:
            return match3[0][0].replace("\\","")+match3[0][1].replace("\\","")+" swfUrl=http://www.arte.tv/flash/mediaplayer/mediaplayer.swf live=1 swfVfy=1"
    elif streamingType=="HTTP":
        url = match[0].replace("/player/","/")
        content = getUrl(url)
        match1 = re.compile('"HBBTV","VQU":"SQ","VMT":"mp4","VUR":"(.+?)"', re.DOTALL).findall(content)
        match2 = re.compile('"HBBTV","VQU":"EQ","VMT":"mp4","VUR":"(.+?)"', re.DOTALL).findall(content)
        if match1 and maxVideoQuality == "720p":
            return match1[0]
        elif match2:
            return match2[0]
    elif streamingType=="RTMP":
        url = match[0]
        content = getUrl(url)
        match1 = re.compile('"RTMP_SQ_1":.+?"streamer":"(.+?)","url":"(.+?)"', re.DOTALL).findall(content)
        match2 = re.compile('"RTMP_MQ_1":.+?"streamer":"(.+?)","url":"(.+?)"', re.DOTALL).findall(content)
        if match1 and maxVideoQuality == "720p":
            base = match1[0][0]
            playpath = match1[0][1]
        elif match2:
            base = match2[0][0]
            playpath = match2[0][1]
        return base+" playpath=mp4:"+playpath


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def playLiveStream():
    if language == "de":
        url = "http://org-www.arte.tv/papi/tvguide/videos/livestream/player/D/"
    elif language == "fr":
        url = "http://org-www.arte.tv/papi/tvguide/videos/livestream/player/F/"
    content = getUrl(url)
    match = re.compile('"RMTP_HQ":\\{"quality":"SD - 400p","width":.+?,"height":.+?,"mediaType":"rtmp","mimeType":"application/x-fcs","bitrate":.+?,"streamer":"(.+?)","url":"(.+?)"', re.DOTALL).findall(content)
    listitem = xbmcgui.ListItem(path=match[0][0] + match[0][1] + " swfUrl=http://www.arte.tv/flash/mediaplayer/mediaplayer.swf live=1 swfVfy=1")
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#39;", "'").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.replace('\\"', '"').strip()
    return title


def getUrl(url, cookie=None):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')
    if cookie != None:
        req.add_header('Cookie', cookie)
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, desc="", duration=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart and iconimage!=icon:
        liz.setProperty("fanart_image", iconimage)
    else:
        liz.setProperty("fanart_image", defaultFanart)
    liz.addContextMenuItems([(translation(30020), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, regionFilter=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&regionFilter="+urllib.quote_plus(regionFilter)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if useThumbAsFanart and iconimage and iconimage!=icon:
        liz.setProperty("fanart_image", iconimage)
    else:
        liz.setProperty("fanart_image", defaultFanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
regionFilter = urllib.unquote_plus(params.get('regionFilter', ''))

if mode == 'listVideosNew':
    listVideosNew(url)
elif mode == 'listSearchVideos':
    listSearchVideos(url)
elif mode == 'listCats':
    listCats(url, regionFilter)
elif mode == 'queueVideo':
    queueVideo(url, name)
elif mode == 'playVideoNew':
    playVideoNew(url)
elif mode == 'playLiveEvent':
    playLiveEvent(url)
elif mode == 'playLiveStream':
    playLiveStream()
elif mode == 'listConcerts':
    listConcerts(url)
elif mode == 'listCollections':
    listCollections()
elif mode == 'listConcertsMain':
    listConcertsMain()
elif mode == 'search':
    search()
else:
    index()
