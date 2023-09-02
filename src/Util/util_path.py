# Copyright Allve, Inc. All Rights Reserved.

import os
import glob
from pathlib import Path

def make_absoultepath(directory_path, filename) -> str:
    return directory_path + '/' + filename

def make_directorypath(path) -> str:
    if not path.endsWith('\\') and not path.endsWith('/'):
        path += '\\'
    return path

def get_current_work_directorypath() -> str:
    return os.getcwd()
    
def get_allfiles_from_directorypath(directorypath) -> list[str]:
    files = []
    path = Path(directorypath)
    if path.exists():
        [[files.append(f.replace('\\', '/'))] for f in glob.glob(directorypath + '/**/*.*', recursive=True)]
    return files

def get_file_extension(filename):
    name, extension = os.path.splitext(filename)
    return extension

def is_headerfile(filepath):
    ext = get_file_extension(filepath)
    return ext == '.h' or ext == '.hpp'

def is_cppfile(filepath):
    ext = get_file_extension(filepath)
    return ext == '.cpp' or ext == '.cc'