import os.path
import urllib.request

this_dir = os.path.dirname(__file__)

urls_to_files = {
    "https://dl.dropboxusercontent.com/scl/fi/jphaqhoci2fae0tmy0gna/best_model.h5?rlkey=w7tbd1woo8yafzq1m1djlf2um&dl=1": "best_model.h5"
}

for url, file in urls_to_files.items():
    print(f"Downloading {file}")
    urllib.request.urlretrieve(url, f"{this_dir}/{file}")
