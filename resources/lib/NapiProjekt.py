# *-* coding: utf-8 *-*

import urllib, urllib2, base64, re 
from xml.dom import minidom
import dom_parser
import urlparse
import xbmcaddon
import xbmc
import traceback

__addon__ = xbmcaddon.Addon()
__scriptname__ = __addon__.getAddonInfo('name')

class NapiProjektKatalog:
    def __init__(self):
        self.download_url = "http://napiprojekt.pl/api/api-napiprojekt3.php"
        self.base_url = "http://www.napiprojekt.pl"
        self.search_url = "/ajax/search_catalog.php"

    def log(self, msg=None, ex = None):
        if ex : 
            level = xbmc.LOGERROR
            msg = traceback.format_exc()
        else:
            level = xbmc.LOGINFO
        
        xbmc.log((u"### [%s] - %s" % (__scriptname__, msg)).encode('utf-8'), level=level)


    def notify(self, msg):
        xbmc.executebuiltin((u'Notification(%s,%s)' % (__scriptname__, msg)).encode('utf-8'))

    def try_get_org_title(self, title):
        start_index = title.find("(")
        end_index = title.find(")")
        if start_index != -1 and end_index != -1:
            return title[start_index + 1:end_index]
        return None
    
    def find_subtitle_page(self, item):    
        if not any((True for x in item["3let_language"] if x in ["pl", "pol"])):
            self.log('Only polish supported')
            self.notify('Only Polish supported')
            return None
        
        if item['tvshow']:
            title_to_find = item['tvshow']
            query_kind = 1
            query_year = ''
        else:            
            title_to_find = item['title']
            query_kind = 2
            query_year = item['year']
            
        post = {'queryKind':query_kind,
            'queryString':self.getsearch(title_to_find),
            'queryYear':query_year,
            'associate':''}
        self.log('searching for movie: ' + str(post))
        post = urllib.urlencode(post, doseq=True)

        url = self.base_url + self.search_url
        subs = urllib2.urlopen(url, data=post).read()
        rows = self.parseDOM_base(subs, 'a', attrs={'class':'movieTitleCat'}) 
        
        clean_title = self.get_clean(title_to_find)
        for row in rows:
            title = self.parseDOM(row.content, 'h3')[0]
            title = self.try_get_org_title(title)
            if not title:
                title = row.attrs['tytul']
            if self.get_clean(title) == clean_title:
                self.log('Found: ' + title)
                result = urlparse.urljoin(self.base_url, row.attrs['href'])
                if item['tvshow']:
                    season = item['season']
                    episode = item['episode']
                    result += '-s' + season.zfill(2) + 'e' + episode.zfill(2)
                result = result.replace('napisy-', 'napisy1,1,1-dla-', 1).encode('utf-8')
                return result        


    def search(self, item):        
        subtitle_list = []
        try:
            url = self.find_subtitle_page(item)
            if not url:
                self.notify('Movie not found')
                return subtitle_list
            self.log('trying to get subtitles list')
            page = urllib.urlopen(url).read()
            page = self.parseDOM(page, 'tbody')[0]
            rows = self.parseDOM(page, 'tr')
            for row in rows:
                link_hash = self.parseDOM(row, 'a', ret='href')[0]
                link_hash = link_hash.replace('napiprojekt:', '')
                cols = self.parseDOM(row, 'p')
                cols.pop(0)
                cols.pop()
                label = ' | '.join(cols)
                subtitle_list.append({'language':'pol', 'label':label, 'link_hash':link_hash})            
        except Exception as e:
            self.notify('Search error, check log')
            self.log(ex=e)
        
        return subtitle_list
    
    def get_clean(self, title):
        if title is None: return
        try:
            title = title.encode('utf-8')
        except:
            pass
        title = re.sub('&#(\d+);', '', title)
        title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
        title = title.replace('&quot;', '\"').replace('&amp;', '&')
        title = title.replace('&','and')
        title = re.sub('\n|([[].+?[]])|([(].+?[)])|\s(vs|v[.])\s|(:|;|-|–|"|,|\'|\_|\.|\?)|\s', '', title).lower()
        if title.startswith('the'):
            title = title[3:]
        return title
    

    def parseDOM_base(self, html, name, attrs):
        if attrs:
            attrs = dict((key, re.compile(value + ('$' if value else ''))) for (key, value) in attrs.iteritems())
        results = dom_parser.parse_dom(html, name, attrs)
        return results

    def parseDOM(self, html, name='', attrs=None, ret=False):
        results = self.parseDOM_base(html, name, attrs)
        if ret:
            results = [result.attrs[ret.lower()] for result in results]
        else:
            results = [result.content for result in results]
        return results

    def getsearch(self, title):
        if title is None: return
        title = title.lower()
        title = re.sub('&#(\d+);', '', title)
        title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
        title = title.replace('&quot;', '\"').replace('&amp;', '&')
        title = re.sub('\\\|/|-|–|:|;|\*|\?|"|\'|<|>|\|', '', title).lower()
        return title
    
    def download(self, md5hash, filename, language="PL"):
        try:
            values = {
                "mode": "1",
                "client": "NapiProjektPython",
                "client_ver": "0.1",
                "downloaded_subtitles_id": md5hash,
                "downloaded_subtitles_txt": "1",
                "downloaded_subtitles_lang": language
            }
            
            self.log('Downloading subs: ' + str(values))
    
            data = urllib.urlencode(values)

            response = urllib.urlopen(self.download_url, data)

            DOMTree = minidom.parseString(response.read())

            cNodes = DOMTree.childNodes
            if (cNodes[0].getElementsByTagName("status") != []):
                text = base64.b64decode(
                    cNodes[0].getElementsByTagName("subtitles")[0].getElementsByTagName("content")[0].childNodes[
                        0].data)
                filename = filename[:filename.rfind(".")] + ".txt"
                open(filename, "w").write(text)
                return filename

        except Exception as e:
            self.notify('Download error, check log')
            self.log(ex=e)
            pass
            

        return None
