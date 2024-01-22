import os.path
import glob


class File:
    path: str = ""

    def __new__(cls, file_or_folder_path, *args, **kwargs):
        if path := getattr(cls, "PATH"):
            files = glob.glob(os.path.join(file_or_folder_path, path))
            if len(files) != 1:
                return None
            else:
                instance = super().__new__(cls)
                instance.path = files[0]
                return instance
        else:
            return None
