# *-* coding: utf-8 *-*

import urllib, urllib2, base64, re 
from xml.dom import minidom
import dom_parser
import urlparse

class NapiProjektKatalog:
    def __init__(self):
        self.download_url = "http://napiprojekt.pl/api/api-napiprojekt3.php"
        self.base_url = "http://www.napiprojekt.pl"
        self.search_url = "/ajax/search_catalog.php"

    def try_get_org_title(self, title):
        start_index = title.find("(")
        end_index = title.find(")")
        if start_index != -1 and end_index != -1:
            return title[start_index + 1:end_index]
        return None
    
    def find_subtitle_page(self, item):
        try:
            if not any((True for x in item["3let_language"] if x in ["pl", "pol"])):
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
                    result = urlparse.urljoin(self.base_url, row.attrs['href'])
                    if item['tvshow']:
                        season = item['season']
                        episode = item['episode']
                        result += '-s' + season.zfill(2) + 'e' + episode.zfill(2)
                    result = result.replace('napisy-', 'napisy1,1,1-dla-', 1).encode('utf-8')
                    return result        
        except:
            pass

    def search(self, item):        
        subtitle_list = []
        try:
            url = self.find_subtitle_page(item)
            page = urllib2.urlopen(url).read()
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
            print e 
            pass
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
        title = re.sub('\n|([[].+?[]])|([(].+?[)])|\s(vs|v[.])\s|(:|;|-|–|"|,|\'|\_|\.|\?)|\s', '', title).lower()
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

        except:
            pass
            

        return False
