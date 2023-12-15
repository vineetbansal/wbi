import pooch

"""
Large files that are downloaded/cached automagically using the pooch library.

  How to add new entries to this list:

  Get expected hash by running md5sum or md5 on the file
  For Dropbox links, use "Copy Link" to get the URL,
    replace "www.dropbox.com" with "dl.dropboxusercontent.com",
    replace "dl=0" with "dl=1"
"""

files = {
    "best_model": {
        "url": "https://dl.dropboxusercontent.com/scl/fi/jphaqhoci2fae0tmy0gna/best_model.h5?rlkey=w7tbd1woo8yafzq1m1djlf2um&dl=1",
        "hash": "md5:4feda1bad12dccfd1ab333bda7bf19dc",
    }
}


def get_file(which):
    assert which in files, f"Unknown file {which}"
    file = files[which]
    return pooch.retrieve(url=file["url"], known_hash=file["hash"])
