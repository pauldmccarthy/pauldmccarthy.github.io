#!/usr/bin/env python
#
# s3_photo_upload.py - Upload photos to an Amazon s3 bucket.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Upload a collection of photos, and resized versions of them, to a s3
bucket, naming the photos according to a standard convention.  Also upload a
json file containing a list of the photos that were uploaded.


For example, given a directory containing the following:

  1.jpg
  2.jpg
  3.jpg

This command:

  s3_photo_upload.py bucket-name photos/ album-name \
    -s 1600 -s 1200 -s 800

Will add the following content to the s3 bucket:

  s3://bucket-name/album-name.json
  s3://bucket-name/album-name/1_X0_Y0.jpg
  s3://bucket-name/album-name/2_X0_Y0.jpg
  s3://bucket-name/album-name/3_X0_Y0.jpg
  s3://bucket-name/album-name/1_X1_Y1.jpg
  s3://bucket-name/album-name/2_X1_Y1.jpg
  s3://bucket-name/album-name/3_X1_Y1.jpg
  s3://bucket-name/album-name/1_X2_Y2.jpg
  s3://bucket-name/album-name/2_X2_Y2.jpg
  s3://bucket-name/album-name/3_X2_Y2.jpg
  s3://bucket-name/album-name/1_X3_Y3.jpg
  s3://bucket-name/album-name/2_X3_Y3.jpg
  s3://bucket-name/album-name/3_X3_Y3.jpg

Where:

 - XN/YN give the width/height of each re-sized image.
 - Files named *-X0_Y0.jpg are the original images.
 - Files named *-X1_Y1.jpg have a maximum width/height of 1600 pixels.
 - Files named *-X2_Y2.jpg have a maximum width/height of 1200 pixels.
 - Files named *-X3_Y3.jpg have a maximum width/height of 800 pixels.
 - album-name.json contains the following:

   jsonp({
     "1.jpg" : [[X0, Y0],
                [X1, Y1],
                [X2, Y2],
                [X3, Y3]],
     "2.jpg" : [[X0, Y0],
                [X1, Y1],
                [X2, Y2],
                [X3, Y3]],
     "3.jpg" : [[X0, Y0],
                [X1, Y1],
                [X2, Y2],
                [X3, Y3]], 
    })

The resized images are sized so that their dimensions do not exceed the
requested width/height.


Requires:
  awscli
  Pillow
"""


from __future__ import print_function

import               os
import os.path    as op
import               sys
import               glob
import               json
import               shutil
import               tempfile
import               argparse
import               textwrap
import               collections
import subprocess as sp
import itertools  as it

from PIL import Image, ExifTags


FILE_TYPES = ['.jpg', '.png']
FILE_TYPES = FILE_TYPES + [ft.upper() for ft in FILE_TYPES]


def main(argv=None):

    namespace                  = parseArgs(argv)
    workspace, albumDir, index = prepareAlbum(namespace)
    index                      = prepareFileIndex(index)

    if namespace.local is not None: copyLocal(namespace, albumDir, index)
    else:                           copyToS3( namespace, albumDir, index)
    
    shutil.rmtree(workspace)
    os.remove(    index)


def prepareAlbum(namespace):

    workspace = tempfile.mkdtemp(prefix='s3_photo_upload_py')
    albumDir  = op.join(workspace, namespace.album_name)

    os.makedirs(albumDir)

    images = [op.join(namespace.album, '*{}'.format(ft)) for ft in FILE_TYPES]
    images = list(it.chain(*[glob.glob(i) for i in images]))

    # Assuming images are numerically named
    try:
        images.sort(lambda i1, i2: cmp(int(op.splitext(op.basename(i1))[0]),
                                       int(op.splitext(op.basename(i2))[0])))
    except:
        pass

    print('Preparing album in {} [{} images]...'.format(
        albumDir, len(images)))

    imageIndex = collections.OrderedDict()

    for image in images:
        allSizes, allImageFiles = prepareImage(
            namespace, albumDir, image)

        imageIndex[op.basename(image)] = allSizes

    return workspace, albumDir, imageIndex


def prepareImage(namespace, albumDir, imageFile):

    image = Image.open(imageFile)

    # Thanks http://stackoverflow.com/a/6218425
    try:
        for okey in ExifTags.TAGS.keys(): 
            if ExifTags.TAGS[okey] == 'Orientation':
                break

        orient = image._getexif()[okey]
    except:
        orient = -1


    if   orient == 3: image = image.rotate(180, expand=True)
    elif orient == 6: image = image.rotate(270, expand=True)
    elif orient == 8: image = image.rotate(90,  expand=True)
 
    ow, oh    = image.size
    allImages = []
    allSizes  = []

    for size in namespace.photo_size:

        if ow < size and oh < size:
            continue

        if ow == oh:
            rw = size
            rh = size
            
        elif ow > oh:
            rw = min(ow, size)
            rh = rw * (oh / float(ow))
            
        elif ow < oh:
            rh = min(ow, size)
            rw = rh * (ow / float(oh))

        rw      = int(round(rw))
        rh      = int(round(rh))
        resized = image.resize((rw, rh))

        allSizes .append([rw, rh])
        allImages.append(resized)

    allImages.append(image)
    allSizes .append([ow, oh])
        
    prefix, suffix = op.splitext(op.basename(imageFile))

    print('  {} ...'.format(imageFile), end='')

    allImageFiles = []
    
    for image in allImages:
        
        w, h     = image.size
        fileName = '{}_{}_{}{}'.format(prefix, w, h, suffix)
        fileName = op.join(albumDir, fileName)

        print('  {}x{}'.format(w, h), end='')

        allImageFiles.append(fileName)

        image.save(fileName)
        
    print()

    return allSizes, allImageFiles


def prepareFileIndex(index):

    fd, indexFile = tempfile.mkstemp(prefix='s3_photo_upload_py')

    print(json.dumps(index))

    with open(indexFile, 'wt') as f:
        f.write('jsonp({})'.format(json.dumps(index)))

    os.close(fd)

    return indexFile


def copyToS3(namespace, albumDir, fileIndex):

    cmd1 = 'aws s3 cp {} s3://{}/{}.json {}'.format(
        fileIndex,
        namespace.bucket_name,
        namespace.album_name,
        namespace.s3args)

    cmd2 = 'aws s3 cp {} s3://{}/{} --recursive {}'.format(
        albumDir,
        namespace.bucket_name,
        namespace.album_name,
        namespace.s3args)

    if sp.call(cmd1.split(), stdin=sys.stdin, stdout=sys.stdout) != 0:
        raise RuntimeError('Command failed: {}'.format(cmd1))
    
    if sp.call(cmd2.split(), stdin=sys.stdin, stdout=sys.stdout) != 0:
        raise RuntimeError('Command failed: {}'.format(cmd2))


def copyLocal(namespace, albumDir, fileIndex):
    cmd1 = 'cp {} {}'.format(
        fileIndex,
        op.join(namespace.local, '{}.json'.format(namespace.album_name)))

    cmd2 = 'cp -r {} {}'.format(
        albumDir,
        op.join(namespace.local, namespace.album_name))

    if sp.call(cmd1.split(), stdin=sys.stdin, stdout=sys.stdout) != 0:
        raise RuntimeError('Command failed: {}'.format(cmd1))
    
    if sp.call(cmd2.split(), stdin=sys.stdin, stdout=sys.stdout) != 0:
        raise RuntimeError('Command failed: {}'.format(cmd2)) 


def parseArgs(argv=None):
    
    if argv is None:
        argv = sys.argv[1:]

    description = 'Upload photos to a s3 bucket'
    epilog      = textwrap.dedent("""
    Supported file types: {}
    
    s3_photo_upload.py assumes that aws cli has been installed and correctly
    configured.
    """.format(', '.join(FILE_TYPES)))

    parser = argparse.ArgumentParser(
        's3_photo_upload.py',
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('bucket_name',
                        help='s3 bucket name')
    parser.add_argument('album',
                        help='Directory containing photos')
    parser.add_argument('-n', '--album_name',
                        help='Name to give album (defaults to directory name)')

    parser.add_argument('-l', '--local',
                        help='Copy pics to local dir instead of to s3')

    parser.add_argument('-a', '--s3args',
                        help='Arguments passed through to aws s3 cp command '
                             '(e.g. --dryrun, --storage-class '
                             'REDUCED_REDUNDANCY)')

    sizes = parser.add_mutually_exclusive_group()
    
    sizes.add_argument('-s', '--photo_size', type=int, action='append',
                        help='Resize resolution')
    sizes.add_argument('-d', '--default_sizes', action='store_true',
                       help='Use a default set of sizes (140, 400, '
                            '600, 800, 1000, 1200, 1400, 1600)')

    namespace = parser.parse_args()

    if not op.exists(namespace.album) or \
       not op.isdir( namespace.album):
        raise RuntimeError('{} is not a directory'.format(namespace.album))

    if namespace.album_name is None:
        namespace.album_name = op.basename(namespace.album.strip(op.sep))

    if namespace.default_sizes:
        namespace.photo_size =  [94,   110,  128, 200, 220, 288, 320,  400,
                                 512,  576,  640, 720, 800, 912, 1024, 1152,
                                 1280, 1440, 1600]

    # Only the original size image will be uploaded
    elif namespace.photo_size is None:
        namespace.photo_size = []

    if namespace.local is not None:
        namespace.local = op.abspath(namespace.local)
        if not op.exists(namespace.local):
            raise RuntimeError('Destination directory {} does not '
                               'exist'.format(namespace.local))

    return namespace
    

if __name__ == '__main__':
    main()
