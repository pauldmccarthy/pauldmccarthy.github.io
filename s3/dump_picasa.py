#!/usr/bin/env python
#
# dump_picasa.py - Download your albums from picasa.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""dump_picasa.py is a script which allows you to list and download albums
from your Picasa account. Because dump Picasa, that's why!

Requires (all can be installed via pip):

   - gdata
   - oauth2client

Type "dump_picasa.py --help" for help.

In order to use this script, you must:

1. Go to https://console.developers.google.com

2. Click on 'Credentials' in the left-hand menu

3. Create a dummy project

4. Create an Oauth2 client ID

5. Download the authentication shit as a JSON file.

6. Pass that JSON file to dump_picasa.py

7. The first time you run dump_picasa.py, a web page will open,
   asking you to give dump_picasa.py permission to do shit.
   dump_picasa.py will save the permission shit to a credentials
   file, which you then need to pass in on subsequent runs.

These instructions are valid as of August 2016.

The OAuth2 authentication procedure was gratefully pilfered from:

https://github.com/MicOestergaard/picasawebuploader
"""


from __future__ import print_function

import os
import os.path as op
import re
import sys
import argparse
import urllib
import httplib2
import webbrowser
import datetime

import gdata.gauth 
import gdata.photos.service
import oauth2client.client as oauth2client
import oauth2client.file   as oauth2file


def main(argv=None):

    namespace = parseArgs(argv)

    if (not namespace.list):
        if op.exists(namespace.dest):
            print('Destination directory already exists: {}'.format(
                namespace.dest))
            sys.exit(1)
            
        os.makedirs(namespace.dest) 
    
    client      = login(namespace)
    albums, ids = getAlbums(namespace, client)
 
    if namespace.list:
        printAlbums(namespace, client, albums, ids)
        sys.exit(0)

    for album, id in zip(albums, ids):
        downloadAlbum(namespace, client, album, id)


def printAlbums(namespace, client, albums, ids):
    
    for album, id in zip(albums, ids):
        
        print('{}'.format(album))

        if namespace.files:
            photos, urls = getAlbumPhotos(namespace, client, id)

            for p, u in zip(photos, urls):
                print('  {}: {}'.format(p, u))

            print()


def getAlbums(namespace, client):

    albums = client.GetUserFeed()

    names = [a.title.text     for a in albums.entry]
    ids   = [a.gphoto_id.text for a in albums.entry] 

    if namespace.include_albums is not None:

        keep = []

        for i, (name, id) in enumerate(zip(names, ids)):
            for pat in namespace.include_albums:
                if re.search(pat, name) is not None:
                    keep.append(i)
                    break

            if namespace.print_exclude and (len(keep) == 0 or keep[-1] != i):
                print('Excluding {}'.format(name))
                

        names = [names[i] for i in keep]
        ids   = [ids[  i] for i in keep] 

    return names, ids


def downloadAlbum(namespace, client, album, id):

    destDir = op.join(namespace.dest, album)

    print('Downloading {}...'.format(album))

    if not op.exists(destDir):
        os.makedirs(destDir)

    names, urls = getAlbumPhotos(namespace, client, id)

    for name, url in zip(names, urls):
        destFile = op.join(destDir, name)

        print('  Saving {} to {} ...'.format(name, destFile))
        urllib.urlretrieve(url, destFile)


def getAlbumPhotos(namespace, client, id):
    
    photos = client.GetFeed(
        '/data/feed/api/user/{}/albumid/{}?kind=photo&imgmax=d'.format(
            namespace.email, id))

    names = [p.title.text  for p in photos.entry]
    urls  = [p.content.src for p in photos.entry]

    return names, urls

    
# Thanks https://github.com/MicOestergaard/picasawebuploader/
def login(namespace):
    
    scope = 'https://picasaweb.google.com/data/'
    agent = 'dump_picasa'

    storage     = oauth2file.Storage(namespace.credfile)
    credentials = storage.get()
    
    if credentials is None or credentials.invalid:
        flow = oauth2client.flow_from_clientsecrets(
            namespace.keyfile,
            scope=scope,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        uri = flow.step1_get_authorize_url()
        webbrowser.open(uri)
        code = raw_input('Enter the authentication code: ').strip()
        credentials = flow.step2_exchange(code)

    if (credentials.token_expiry - datetime.datetime.utcnow()) < datetime.timedelta(minutes=5):
        http = httplib2.Http()
        http = credentials.authorize(http)
        credentials.refresh(http)

    storage.put(credentials)

    client = gdata.photos.service.PhotosService(
        source=agent,
        email=namespace.email,
        additional_headers={
            'Authorization' : 'Bearer {}'.format(credentials.access_token)})

    return client


def parseArgs(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser('dump_picasa.py')

    parser.add_argument('keyfile',
                        help='Google API access OAuth2 JSON file - '
                             'generate one at '
                             'https://console.developers.google.com') 
    parser.add_argument('credfile',
                        help='Place to store oauth2 credentials - this '
                             'will be generated the first time you run '
                             'dump_picassa.py. On subsequent runs, you '
                             'will still need to pass in the file path.')
    parser.add_argument('email', help='gmail address')
    parser.add_argument('dest',
                        help='Download all albums to this location')

    parser.add_argument('-l', '--list', action='store_true',
                        help='List albums (applying include_albums '
                             'pattern), then exit')
    parser.add_argument('-f', '--files', action='store_true',
                        help='If -l, list files as well')

    parser.add_argument('-e', '--print_exclude', action='store_true',
                        help='Print albums that will be excluded '
                             'by include_albums patterns')

    parser.add_argument('-ia', '--include_albums',
                        action='append',
                        help='Only download Picasa albums which '
                             'match this regex (default: all '
                             'albums are downloaded). This argument '
                             'can be used multiple times.')

    return parser.parse_args()


if __name__ == '__main__':
    main()
