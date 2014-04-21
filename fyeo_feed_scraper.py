#!/usr/bin/env python
import time
import StringIO

import feedparser
import requests
from internetarchive import get_item


# iter_entries()
#_________________________________________________________________________________________
def iter_entries(url):
    f = feedparser.parse(u)
    for e in f.entries:
        parsed_date = e.get('published_parsed')
        date = time.strftime('%Y-%m-%d', parsed_date)
        md = dict(
            collection='test_collection',
            mediatype='audio',

            identifier='test' + e.get('link', '').split('/')[-1].split('.')[0],
            title=e.get('title'),
            description=e.get('summary'),
            date=date,
            source=e.get('link'),
        )
        yield md

# get_audio_fh()
#_________________________________________________________________________________________
def get_audio_fh(url):
    r = requests.get(url)
    r.raise_for_status()
    fh = StringIO.StringIO()
    fh.write(r.content)
    return fh
    
# main()
#_________________________________________________________________________________________
if __name__ == '__main__':
    u = 'http://feeds.feedburner.com/foryourearsonlyonair'
    for md in iter_entries(u):
        item = get_item(md['identifier'])
        audio_fname = '{0}.mp3'.format(md['identifier'])
        # Skip if file already exists on IA.
        # TODO: Should we verify checksums before skipping?;
        if audio_fname in [f.name for f in item.iter_files()]:
            log.info('{0}/{1} already exists, skipping.'.format(item.identifier,
                                                                audio_fname)
            continue
        audio_fh = get_audio_fh(md['source'])
        sys.stdout.write('{0}:\n'.format(item.identifier))
        resps = item.upload({audio_fname: audio_fh}, metadata=md, verbose=True)
        for r in resps:
            r.raise_for_status()

#summary_detail
#subtitle
#published_parsed
#links
#title
#media_content
#author
#itunes_explicit
#subtitle_detail
#content
#guidislink
#feedburner_origenclosurelink
#title_detail
#link
#itunes_keywords
#authors
#author_detail
#summary
#id
#tags
#published
