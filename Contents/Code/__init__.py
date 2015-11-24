PREFIX = '/video/fox'
TITLE = 'FOX'

SHOWS_URL = 'aHR0cDovL2Fzc2V0cy5mb3guY29tL2FwcHMvRkVBL3YxLjgvYWxsc2hvd3MuanNvbg__'
SERIES_URL = 'aHR0cDovL2ZlZWQudGhlcGxhdGZvcm0uY29tL2YvZm94LmNvbS9tZXRhZGF0YT9jb3VudD10cnVlJmJ5Q3VzdG9tVmFsdWU9e2Z1bGxFcGlzb2RlfXt0cnVlfSZieUNhdGVnb3JpZXM9U2VyaWVzLyVz'

SHOW_IMAGE_URL = 'http://www.fox.com/_ugc/feeds/images/%s/aptveSeries.jpg'
FALLBACK_THUMB = 'http://resources-cdn.plexapp.com/image/source/com.plexapp.plugins.fox.jpg'

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
    full_episode_found = False
    
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
@route(PREFIX + '/episodes')
def Episodes(title, stub, season):

    oc = ObjectContainer(title2 = title)
    org_thumb = SHOW_IMAGE_URL % stub
    json_url = String.Decode(SERIES_URL) % String.Quote(title)
    json_data = JSON.ObjectFromURL(url = json_url)
    
    for episode in json_data['results']:
        if str(episode['season']) != str(season):
            continue

        url = 'http://www.fox.com/watch/%s' % episode['id']
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
        originally_available_at = Datetime.ParseDate(episode['airdate'])
        
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
                originally_available_at = originally_available_at,
                content_rating = episode['rating'] if 'rating' in episode else None
            )
        )

    if len(oc) < 1:
        oc.header = "Sorry"
        oc.message = "Couldn't find any full episodes for this show"

    return oc
