#!/usr/bin/env python
import logging
import argparse
import time
import StringIO
import re
import sys

import feedparser
from bs4 import BeautifulSoup
from internetarchive import get_item
import requests


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
fh = logging.FileHandler('fyeo_feed_scraper.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
log.addHandler(fh)
log.addHandler(ch)


# iter_entries()
# ________________________________________________________________________________________
def iter_entries(url):
    f = feedparser.parse(u)
    for e in f.entries:
        parsed_date = e.get('published_parsed')
        date = time.strftime('%Y-%m-%d', parsed_date)
        id = 'fyeo-{0}'.format(e.get('link', '').split('/')[-1].split('.')[0])
        lineup = get_lineup(id)
        if not lineup:
            log.warning('{0} has no lineup.'.format(id))
        description = '{0}\n{1}'.format(e.get('summary', '').replace('http://', '//'), lineup)
        md = dict(
            collection='foryourearsonly',
            mediatype='audio',
            creator='David Alpern',
            rights='These items are provided for non-commercial use only.',
            language='eng',

            identifier=id,
            title=e.get('title'),
            description=description,
            date=date,
            source=e.get('link'),
            subject=e.get('itunes_keywords', '').split(','),
        )
        yield dict((k, v) for (k, v) in md.items() if v)


# get_lineup()
# ________________________________________________________________________________________
def get_lineup(identifier):
    match = re.search(r'\d{6}', identifier)
    if not match:
        return
    else:
        lineup_id = match.group()
    u = 'http://gatewave.org/fyeo/lineup/{0}'.format(lineup_id)
    r = requests.get(u)
    s = BeautifulSoup(r.content)
    lineup = ['<h2>Lineup:</h2>']
    for i, div in enumerate(s.select('.content')):
        if i != 6:
            continue
        for p in div.find_all('p'):
            if 'You are missing some Flash' in p.get_text():
                continue
            else:
                lineup.append(str(p))
        return '\n'.join(lineup)


# get_audio_fh()
# ________________________________________________________________________________________
def get_audio_fh(url):
    r = requests.get(url)
    r.raise_for_status()
    fh = StringIO.StringIO()
    fh.write(r.content)
    return fh


# main()
# ________________________________________________________________________________________
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Archive FYEO RSS feed.')
    parser.add_argument('--skip', metavar='N', type=int, nargs='?',
                        help='Exit after N skips.')
    args = parser.parse_args()

    u = 'http://feeds.feedburner.com/foryourearsonlyonair'
    skips = 0
    for md in iter_entries(u):
        item = get_item(md['identifier'])
        audio_fname = '{0}.mp3'.format(md['identifier'].replace('fyeo-', ''))
        if audio_fname in [f.name for f in item.iter_files()]:
            log.info('{0}/{1} already exists, skipping.'.format(item.identifier,
                                                                audio_fname))
            skips += 1
            if (args.skip) and (skips >= args.skip):
                log.info(
                    'skipped {0} items, we must be up to date... exiting.'.format(skips))
                sys.exit(0)
            continue
        audio_fh = get_audio_fh(md['source'])
        sys.stdout.write('{0}:\n'.format(item.identifier))
        resps = item.upload({audio_fname: audio_fh}, metadata=md, verbose=True)
        for r in resps:
            r.raise_for_status()
        log.info('{0}/{1} successfully uploaded.'.format(item.identifier, audio_fname))
