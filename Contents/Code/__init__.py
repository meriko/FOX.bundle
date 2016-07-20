PREFIX = '/video/fox'
TITLE = 'FOX'

SHOWS_URL = 'aHR0cDovL2Fzc2V0cy5mb3guY29tL2FwcHMvRkVBL3YxLjgvYWxsc2hvd3MuanNvbg__'
SERIES_URL = 'aHR0cDovL2ZlZWQudGhlcGxhdGZvcm0uY29tL2YvZm94LmNvbS9tZXRhZGF0YT9jb3VudD10cnVlJmJ5Q3VzdG9tVmFsdWU9e2Z1bGxFcGlzb2RlfXt0cnVlfSZieUNhdGVnb3JpZXM9U2VyaWVzLyVz'
FEATURED_URL = 'aHR0cDovL2ZlZWQudGhlcGxhdGZvcm0uY29tL2YvVEJtbzFCL2FwcGxldHYtZmVhdHVyZWQ/YWRhcHRlclBhcmFtcz1tdnBkJTNEJnJhbmdlPTEtMTAx'

SHOW_IMAGE_URL = 'http://www.fox.com/_ugc/feeds/images/%s/aptveSeries.jpg'
FALLBACK_THUMB = 'http://resources-cdn.plexapp.com/image/source/com.plexapp.plugins.fox.jpg'

VIDEO_TEMPLATE_URL = 'http://www.fox.com/watch/%s'

SMIL_NS = {'a': 'http://www.w3.org/2005/SMIL21/Language'}

##########################################################################################
def Start():

    # Setup the default attributes for the ObjectContainer
    ObjectContainer.title1 = TITLE

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.User_Agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.3.18 (KHTML, like Gecko) Version/8.0.3 Safari/600.3.18'

##########################################################################################
@handler(PREFIX, TITLE)
def MainMenu():
    
    oc = ObjectContainer()

    oc.add(
        DirectoryObject(
            key = Callback(Special, latest = True),
            title = 'Latest'
        )
    )

    oc.add(
        DirectoryObject(
            key = Callback(Special),
            title = 'Featured'
        )
    )
    
    oc.add(
        DirectoryObject(
            key = Callback(Shows),
            title = 'All Shows'
        )
    )

    return oc
    
##########################################################################################
@route(PREFIX + '/special')
def Special(latest = False):
    
    oc = ObjectContainer()

    featured_data = JSON.ObjectFromURL(url = String.Decode(FEATURED_URL))
    shows_data = JSON.ObjectFromURL(url = String.Decode(SHOWS_URL))
    
    episodes = {}
    for featured_episode in featured_data['entries']:
        if not featured_episode['fox$fullEpisode']:
            continue
        
        found_show = None    
        for show in shows_data['shows']:
            if show['stub'] == featured_episode['fox$showcode']:
                found_show = show
                break
                
        if not found_show:
            continue
            
        episodes_data = JSON.ObjectFromURL(url = String.Decode(SERIES_URL) % String.Quote(found_show['title']))

        for episode in episodes_data['results']:
            if (int(episode['episode']) == int(featured_episode['fox$episode'])) and (int(episode['season']) == int(featured_episode['fox$season'])):
                episode_oc = Episodes(title = found_show['title'], stub = found_show['stub'], season = str(episode['season']), forced_episode = int(episode['season']))
                
                for object in episode_oc.objects:
                    if int(episode['season']) >= 10:
                        season_string = str(episode['season'])
                    else:
                        season_string = '0' + str(episode['season'])
                        
                    if int(episode['episode']) >= 10:
                        episode_string = str(episode['episode'])
                    else:
                        episode_string = '0' + str(episode['episode'])
                        
                    object.title = object.title + ', S%sE%s' % (season_string, episode_string)
                    
                    if latest:
                        try:
                            episodes[episode['airdate']] = object
                        except:
                            pass
                    else:
                        oc.add(object)
                
                break

    if latest:
        for key in sorted(episodes, reverse=True):
            oc.add(episodes[key])
  
    return oc

##########################################################################################
@route(PREFIX + '/shows')
def Shows():
    
    oc = ObjectContainer()

    json_data = JSON.ObjectFromURL(url = String.Decode(SHOWS_URL))
    
    for show in json_data['shows']:
        if show['fullepisodes'] == "false":
            continue
            
        if show['external_link']:
            continue
           
        oc.add(
            TVShowObject(
                key = Callback(Seasons, title = show['title'], stub = show['stub']),
                rating_key = show['title'],
                studio = 'FOX',
                title = show['title'],
                thumb = Resource.ContentsOfURLWithFallback(SHOW_IMAGE_URL % show['stub'], FALLBACK_THUMB)
            ) 
        )
 
    return oc

##########################################################################################
@route(PREFIX + '/seasons')
def Seasons(title, stub):

    oc = ObjectContainer(title2 = title)
    
    json_url = String.Decode(SERIES_URL) % String.Quote(title)
    json_data = JSON.ObjectFromURL(url = json_url)

    seasons = {}
    
    for episode in json_data['results']:
        if episode['fullepisode']:
            if episode['season'] and (not episode['season'] in seasons):
                seasons[episode['season']] = 1
            elif episode['season'] and (episode['season'] in seasons):
                seasons[episode['season']] = seasons[episode['season']] + 1   
    
    for season in seasons:
        oc.add(
            SeasonObject(
                key = Callback(Episodes, title = title, stub = stub, season = str(season)),
                rating_key = title + str(season),
                title = "Season " + str(season),
                show = title,
                index = int(season),
                episode_count = seasons[season],
                thumb = Resource.ContentsOfURLWithFallback(SHOW_IMAGE_URL % stub, FALLBACK_THUMB)
            )
        )

    if len(oc) < 1:
        oc.header = "Sorry"
        oc.message = "Couldn't find any full episodes for this show"

    return oc

##########################################################################################
@route(PREFIX + '/episodes', forced_episode = int)
def Episodes(title, stub, season, forced_episode = None):

    oc = ObjectContainer(title2 = title)
    org_thumb = SHOW_IMAGE_URL % stub
    json_url = String.Decode(SERIES_URL) % String.Quote(title)
    json_data = JSON.ObjectFromURL(url = json_url)
    
    for episode in json_data['results']:
        if str(episode['season']) != str(season):
            continue

        url = episode['videoURL']
        id = episode['id']
        title = episode['name']
        summary = episode['shortDescription']
        
        if episode['videoStillURL']:
            thumb = episode['videoStillURL']
        elif episode['thumbnailURL']:
            thumb = episode['thumbnailURL']
        else:
            thumb = org_thumb
        
        duration = int(episode['length']) * 1000
        
        try:
            show = episode['series'].split("/")[1]
        except:
            show = episode['series']

        index = int(episode['episode'])
        season = int(episode['season'])
        originally_available_at = episode['airdate']
        
        forced_episode_found = False
        if forced_episode:
            if forced_episode == index:
                forced_episode_found = True
                
        if (not forced_episode) or (forced_episode_found):
            oc.add(
                DirectoryObject(
                    key = Callback(
                        CreateEpisodeObject,
                        url = url,
                        id = id,
                        title = title,
                        summary = summary,
                        thumb = thumb,
                        duration = duration,
                        show = show,
                        index = index,
                        season = season,
                        originally_available_at = originally_available_at,
                        content_rating = episode['rating'] if 'rating' in episode else None
                    ),
                    title = title,
                    summary = summary,
                    thumb = thumb
                )
            )
            
            if forced_episode:
                break

    if len(oc) < 1:
        oc.header = "Sorry"
        oc.message = "Couldn't find any full episodes for this show"

    return oc

####################################################################################################
@route(PREFIX + '/createepisodeobject', id=int, duration=int, index=int, season=int)
def CreateEpisodeObject(url, id, title, summary, thumb, duration, show, index, season, originally_available_at, content_rating):

    oc = ObjectContainer(title2 = title)
    episode_xml = XML.ObjectFromURL(url)

    needs_auth = 'InvalidAuthToken' in XML.StringFromObject(episode_xml)
    if needs_auth:
        return ObjectContainer(
            header = "Unavailable",
            message = "This episode is currently locked"
        )

    try:
        url = VIDEO_TEMPLATE_URL % episode_xml.xpath("//a:param[@name='brightcoveId']", namespaces=SMIL_NS)[0].get('value')
    except:
        url = VIDEO_TEMPLATE_URL % id

    oc.add(
        EpisodeObject(
            url = url,
            title = title,
            summary = summary,
            thumb = thumb,
            duration = duration,
            show = show,
            index = index,
            season = season,
            originally_available_at = Datetime.ParseDate(originally_available_at),
            content_rating = content_rating,
        )
    )

    return oc
