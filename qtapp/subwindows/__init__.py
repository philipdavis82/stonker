# import importlib,os,glob

# import __global__

# WIDGETS = []

# def import_widgets():
#     global FILTERS
#     print(__global__.HOME_DIR)
#     searchPath = os.path.join(__global__.HOME_DIR,"qtapp",'subwindows',"*")
#     files = [ os.path.split(file)[1] for file in glob.glob(searchPath) if file.count("__")==0 ]
#     for file in files:
#         file = "qtapp.subwindows."+file.replace(".py","")
#         tmp = importlib.import_module(file)

# if __name__ != "__main__":
#     import_widgets()

from .companySearch import SearchWidget
