import collections
import types


def box_value(v):                                                               
    if v:                                                                       
        if isinstance(v, types.StringTypes):                                    
            return [v]                                                          
        elif isinstance(v, types.DictType):                                     
            return [v]                                                          
        else:                                                                   
            return v                                                            
    else:                                                                       
        return []

def box(data):                                                                  
    return dict((k, box_value(v)) for k, v in data.iteritems())                 

    
def flatten(l):
    for i in l:
        if isinstance(i, collections.Iterable):
            for o in flatten(i):
                yield o
        else:
            yield i


