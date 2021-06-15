
import importlib,os,glob

import __global__

FILTERS = []

def import_filters():
    global FILTERS
    print(__global__.HOME_DIR)
    searchPath = os.path.join(__global__.HOME_DIR,"filters","*.py")
    files = [ os.path.split(file)[1] for file in glob.glob(searchPath) if file.count("__")==0 ]
    for file in files:
        file = "filters."+file.replace(".py","")
        tmp = importlib.import_module(file)

if __name__ != "__main__":
    import_filters()