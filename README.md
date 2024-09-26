# Small adventures (Paul's irregularly updated blog)

Uses the Jekyll-boostrap static site generator.

Instructions for adding a new post:

1. Add a new file in `_posts/<my-new-post>.md`

2. Organise the images in a directory.

3. (from this point refer to s3/s3_notes.txt) Activate/create a Python environment with Pillow and awscli

4. Run `s3/s3_photo_upload.py`, e.g.:
   ```
   python s3_photo_upload.py   \
     pauldmccarthy-github-io   \
     ./pictures/               \
     -d                        \
     -n <my-new-post>
   ```
   `<my-new-post>` must match the `s3-album` ID you have in the `.md` file.
