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
    "best_model.h5": {
        "url": "https://dl.dropboxusercontent.com/scl/fi/jphaqhoci2fae0tmy0gna/best_model.h5?rlkey=w7tbd1woo8yafzq1m1djlf2um&dl=1",
        "hash": "md5:4feda1bad12dccfd1ab333bda7bf19dc",
    },
    "sCMOS_Frames_U16_1024x512.dat": {
        "url": "https://www.dropbox.com/scl/fi/j18s8hfj30ou26hg82g45/sCMOS_Frames_U16_1024x512.dat?rlkey=eqivmm1o8wd4m34wjml64rc52&dl=1",
        "hash": "md5:e5d9d9437a77f5d28b90fc03b2f43d9a",
    },
    "framesDetails.txt": {
        "url": "https://www.dropbox.com/scl/fi/y4yj624x96r1bcqinoged/framesDetails.txt?rlkey=8m8kdp4tozeiwdyxpm8z4you1&dl=1",
        "hash": "md5:e65422d0ca888c3fcee6ecbff3cb62a8",
    },
    "other-frameSynchronous.txt": {
        "url": "https://www.dropbox.com/scl/fi/anusvpiiyrrhemr1bscod/other-frameSynchronous.txt?rlkey=qqa3e9n3g1fp1lm8568v022hz&dl=1",
        "hash": "md5:d39e74b65e2b3907a3182b52012dfc42",
    },
    "other-volumeMetadataUtilities.txt": {
        "url": "https://www.dropbox.com/scl/fi/c7clmlqqcxsy8wasdlmi8/other-volumeMetadataUtilities.txt?rlkey=lseq3jjm61qtjol1glk8mxwwq&dl=1",
        "hash": "md5:ce1ef0aea3bb8af25499d74241c941c8",
    },
    "LowMagBrain20231024_153442": {
        "url": "https://www.dropbox.com/scl/fo/oqgj6jhaz4wixhxi1riec/h?rlkey=7bgjwlx496oxi00chq4144tfs&dl=1",
        "hash": None,
    },
}


def get_file(which):
    assert which in files, f"Unknown file {which}"
    file = files[which]
    return pooch.retrieve(url=file["url"], known_hash=file["hash"], fname=which)
