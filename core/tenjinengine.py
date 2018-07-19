import tenjin
#tenjin.set_template_encoding('utf-8')  # optional (defualt 'utf-8')
from tenjin.helpers import *
from tenjin.html import *
from tenjin import MemoryCacheStorage  
#import tenjin.gae; tenjin.gae.init()   # for Google App Engine

class TenjinEngine():
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(TenjinEngine, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.engine = tenjin.Engine(cache=MemoryCacheStorage())
        #self.engine = tenjin.Engine()
    
    def renderFunction(self,dobyfile):
        context= {}
        return lambda : self.engine.render(dobyfile, context).strip()

def saveStrTemaplate(str):
    '''save str to tenjin formate template file'''
    import tempfile
    tmpfd, tempfilename = tempfile.mkstemp(suffix='.pyhtml', prefix='pylot_')
    #print tmpfd,tempfilename
    #os.close(tmpfd)
    with open(tempfilename,"w") as f:
        f.write(str)
    return tempfilename