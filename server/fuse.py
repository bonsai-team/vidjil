#!/usr/bin/env python
# -*- coding: utf-8 -*-

### fuse.py - Vidjil utility to parse and regroup list of clones of different timepoints or origins

#  This file is part of "Vidjil" <http://bioinfo.lifl.fr/vidjil>
#  Copyright (C) 2011, 2012, 2013, 2014 by Bonsai bioinformatics at LIFL (UMR CNRS 8022, Université Lille) and Inria Lille
#
#  "Vidjil" is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  "Vidjil" is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with "Vidjil". If not, see <http://www.gnu.org/licenses/>

import collections
import json
import argparse
import sys
import time
import copy
import os.path
from operator import itemgetter


VIDJIL_JSON_VERSION = "2014.02"

####

class Window:
    '''storage class for sequence informations
    with some function to group sequence informations
    
    >>> str(w1)
    '<window : [5] 3 aaa>'
    
    >>> str(w3)
    '<window : [8] 4 aaa>'
    
    >>> str(w1 + w3)
    '<window : [5, 8] 3 aaa>'
    
    
    check if other information are conserved
    
    >>> (w2 + w4).d["test"]
    [0, 'plop']
    
    '''
    
    ### init Window with the minimum data required
    def __init__(self, size):
        self.d={}
        self.d["window"] = ""
        self.d["top"] = sys.maxint
        self.d["size"] = []
        for i in range(size):
            self.d["size"].append(0)
        
        
    ### 
    def __iadd__(self, other):
        ### Not used now
        """Add other.size to self.size in-place, without extending lists"""

        assert(len(self.d['size']) == len(other.d['size']))
        self.d['size'] = [my + her for (my, her) in zip(self.d['size'], other.d['size'])]

        return self
        
    def __add__(self, other):
        """Concat two windows, extending lists such as 'size'"""
        #data we don't need to duplicate
        myList = [ "V", "D", "J", "Vend", "Dend", "Jstart", "Dstart", "top", "window", "Nlength", "sequence", "name", "id", "status"]
        obj = Window(1)
        
        t1 = []
        t2 = []
        
        for i in range(len(self.d["size"])):
            t1.append(0)
        for i in range(len(other.d["size"])):
            t2.append(0)
            
        #concat data, if there is some missing data we use an empty buffer t1/t2 
        #with the same size as the number of misssing data
        for key in self.d :
            if key not in myList :
                obj.d[key] = self.d[key]
                if key not in other.d :
                    obj.d[key] += t2
        
        for key in other.d :
            if key not in myList :
                if key not in obj.d :
                    obj.d[key] = t1 + other.d[key]
                else :
                    obj.d[key] += other.d[key]
                    
        #keep other data who don't need to be concat
        if other.d["top"] < self.d["top"] :
            for key in other.d :
                if key in myList :
                    obj.d[key] = other.d[key]
        else :
            for key in self.d :
                if key in myList :
                    obj.d[key] = self.d[key]
        
        return obj
        
    ### print essential info about Window
    def __str__(self):
        return "<window : %s %s %s>" % ( self.d["size"], '*' if self.d["top"] == sys.maxint else self.d["top"], self.d["window"])
        


class OtherWindows:
    
    """Aggregate counts of windows that are discarded (due to too small 'top') for each point into several 'others-' windows."""

    def __init__(self, length, ranges = [1000, 100, 10, 1]):
        self.ranges = ranges
        self.length = length
        self.sizes = {}

        for r in self.ranges:
            self.sizes[r] = [0 for i in range(self.length)]


    def __iadd__(self, window):
        """Add to self a window. The different points may land into different 'others-' windows."""

        for i, s in enumerate(window.d["size"]):
            for r in self.ranges:
                if s >= r:
                     break
            self.sizes[r][i] += s
            ## TODO: add seg_stat
            
        # print window, '-->', self.sizes
        return self

    def __iter__(self):
        """Yield the 'others-' windows"""

        for r in self.ranges:
            w = Window(self.length)
            w.d['size'] = self.sizes[r]
            w.d['window'] = 'others-%d' % r
            w.d['top'] = 0

            print '  --[others]-->', w
            yield w
        
class ListWindows:
    '''storage class for sequences informations 
    
    >>> lw1.info()
    <ListWindows : [[25]] 2 >
    <window : [5] 3 aaa>
    <window : [12] 2 bbb>
    
    >>> lw2.info()
    <ListWindows : [[34]] 2 >
    <window : [8] 4 aaa>
    <window : [2] 8 ccc>
    
    >>> lw3 = lw1 + lw2 
    >>> lw3.info()
    <ListWindows : [[25], [34]] 3 >
    <window : [12, 0] 2 bbb>
    <window : [5, 8] 3 aaa>
    <window : [0, 2] 8 ccc>
    
    '''
    
    def __init__(self):
        '''init ListWindows with the minimum data required'''
        self.d={}
        self.d["windows"] = []
        self.d["clones"] = []
        self.d["reads_segmented"] = [[0]]
        self.d["germline"] = [""]
        
    def __str__(self):
        return "<ListWindows : %s %d >" % ( self.d["reads_segmented"], len(self.d["windows"]) )

    ### print info about each Windows stored 
    def info(self):
        print self
        for i in range(len(self.d["windows"])):
            print self.d["windows"][i]

    ### check vidjil_json_version
    def check_version(self, filepath):
        if "vidjil_json_version" in self.d:
            if self.d["vidjil_json_version"][0] >= VIDJIL_JSON_VERSION:
                return
        raise IOError ("File '%s' is too old -- please regenerate it with a newer version of Vidjil" % filepath)
        
    ### save / load to .json

    def save_json(self, output):
        '''save ListWindows in .json format''' 
        print "==>", output
        with open(output, "w") as file:
            json.dump(self, file, indent=2, default=self.toJson)
            
    def load(self, file_path, pipeline):
        '''init listWindows with data file
        Detects and selects the parser according to the file extension.'''

        # name = file_path.split("/")[-1]
        extension = file_path.split('.')[-1]
        
        print "<==", file_path, "\t",
        
        
        if (extension=="data" or extension=="vidjil"): 
            with open(file_path, "r") as file:
                tmp = json.load(file, object_hook=self.toPython)       
                self.d=tmp.d
                self.check_version(file_path)
                
        elif (extension=="clntab"):
            self.load_clntab(file_path)
                
        else:
            raise IOError ("Invalid file extension .%s" % extension)

        
        if pipeline: 
            # renaming, private pipeline
            f = '/'.join(file_path.split('/')[2:-1])
            print "[%s]" % f

        else:
            f = file_path
            print
        
        self.d['point'] = [f]
        
        if not 'point' in self.d.keys():
            self.d['point'] = [file_path]

    ### 
    def __add__(self, other): 
        '''Combine two ListWindows into a unique ListWindows'''
        obj = ListWindows()
        t1=[]
        t2=[]

        for i in range(len(self.d["reads_segmented"])):
            t1.append(0)
    
        for i in range(len(other.d["reads_segmented"])):
            t2.append(0)
    
        #concat data, if there is some missing data we use an empty buffer t1/t2 
        #with the same size as the number of missing data
        for key in self.d :
            if key != "windows" and key != "links":
                obj.d[key] = self.d[key]
                if key not in other.d :
                    obj.d[key] += t2

        for key in other.d :
            if key != "windows" and key != "links":
                if key not in obj.d :
                    obj.d[key] = t1 + other.d[key]
                else :
                    obj.d[key] += other.d[key]
        
        obj.d["windows"]=self.fuseWindows(self.d["windows"], other.d["windows"], t1, t2)
        obj.d["vidjil_json_version"] = [VIDJIL_JSON_VERSION]

        return obj
        
    ###
    def __mul__(self, other):
        
        for i in range(len(self.d["reads_segmented"])):
            self.d["reads_segmented"][i] += other.d["reads_segmented"][i] 
        
        self.d["windows"] += other.d["windows"]
        self.d["vidjil_json_version"] = [VIDJIL_JSON_VERSION]
        
        self.d["system_segmented"].update(other.d["system_segmented"])
        
        return self
        
    ###
    def add_system_info(self):
        
        w = self.d["windows"]
        germline = self.d["germline"][0]
        system = germline[-3:]
        
        
        for i in range(len(w)):
            w[i].d["system"] = system
        
        self.d["system_segmented"] = {system : list(self.d["reads_segmented"]) }
    
        
    ### 
    def fuseWindows(self, w1, w2, t1, t2) :
        #store data in dict with "window" as key
        dico1 = {}
        for i in range(len(w1)) :
            dico1[ w1[i].d["window"] ] = w1[i]

        dico2 = {}
        for i in range(len(w2)) :
            dico2[ w2[i].d["window"] ] = w2[i]

        #concat data with the same key ("window")
        #if some data are missing we concat with an empty Windows()
        dico3 = {}
        for key in dico1 :
            if key in dico2 :
                dico3[key] = dico1[key] + dico2[key]
            else :
                w=Window(len(t2))
                dico3[key] = dico1[key] + w

        for key in dico2 :
            if key not in dico1 :
                w=Window(len(t1))
                dico3[key] = w + dico2[key]
        
        
        #sort by top
        tab = []
        for key in dico3 :
            tab.append((dico3[key], dico3[key].d["top"]))
        tab = sorted(tab, key=itemgetter(1))
        
        #store back in a List
        result=[]
        for i in range(len(tab)) :
            result.append(tab[i][0])
        
        return result
        
    
    def cut(self, limit, nb_points):
        '''Remove information from sequence/windows who never enter in the most represented sequences. Put this information in 'other' windows.'''

        length = len(self.d["windows"])
        w=[]

        others = OtherWindows(nb_points)

        for index in range(length): 
            win = self.d["windows"][index]
            if (int(win.d["top"]) < limit or limit == 0) :
                w.append(win)
            else:
                others += win

        self.d["windows"] = w + list(others) 
        self.d["germline"]=self.d["germline"][0]

        print "### Cut merged file, keeping window in the top %d for at least one point" % limit
        return self
        
    def load_clntab(self, file_path):
        '''Parser for .clntab file'''

        self.d["vidjil_json_version"] = [VIDJIL_JSON_VERSION]
        self.d["timestamp"] = "1970-01-01 00:00:00" ## todo: timestamp of file_path
        self.d["normalization_factor"] = [1]
        
        listw = []
        listc = []
        total_size = 0
        
        fichier = open(file_path,"r")
        for ligne in fichier:
            if "clonotype" in ligne:
                header_map = ligne.replace('\n', '').split('\t')
            else :
                tab = AccessedDict()
                for index, data in enumerate(ligne.split('\t')):
                    tab[header_map[index]] = data
                        
                w=Window(1)
                #w.window=tab["sequence.seq id"] #use sequence id as window for .clntab data
                w.d["window"]=tab["sequence.raw nt seq"] #use sequence as window for .clntab data
                s = int(tab["sequence.size"])
                total_size += s
                w.d["size"]=[ s ]

                w.d["sequence"] = tab["sequence.raw nt seq"]
                w.d["V"]=tab["sequence.V-GENE and allele"].split('=')
                if (tab["sequence.D-GENE and allele"] != "") :
                    w.d["D"]=tab["sequence.D-GENE and allele"].split('=')
                w.d["J"]=tab["sequence.J-GENE and allele"].split('=')

                # use sequence.JUNCTION to colorize output (this is not exactly V/J !)
                junction = tab.get("sequence.JUNCTION.raw nt seq")
                position = w.d["sequence"].find(junction)
                if position >= 0:
                    w.d["Jstart"] = position + len(junction)
                    w.d["Vend"] = position 
                    w.d["Nlength"] = len(junction)
                else:
                    w.d["Jstart"] = 0
                    w.d["Vend"] = len(w.d["sequence"])
                    w.d["Nlength"] = 0
                w.d["name"]=w.d["V"][0] + " -x/y/-z " + w.d["J"][0]
                w.d["Dend"]=0
                w.d["Dstart"]=0
                    
                listw.append((w , w.d["size"][0]))

                raw_clonotype = tab.get("clonotype")
                clonotype = raw_clonotype.split(' ')
                if (len(clonotype) > 1) :
                    listc.append((w, raw_clonotype))
                
                #keep data that has not already been stored
                for header in tab.not_accessed_keys():
                    w.d["_"+header] = [tab[header]]

        #sort by sequence_size
        listw = sorted(listw, key=itemgetter(1), reverse=True)
        #sort by clonotype
        listc = sorted(listc, key=itemgetter(1))
        
        #generate data "top"
        for index in range(len(listw)):
            listw[index][0].d["top"]=index+1
            self.d["windows"].append(listw[index][0])
        
        self.d["reads_segmented"] = [total_size]

        
    def toJson(self, obj):
        '''Serializer for json module'''
        if isinstance(obj, ListWindows):
            result = {}
            for key in obj.d :
                result[key]= obj.d[key]
                
            return result
            raise TypeError(repr(obj) + " fail !") 
        
        if isinstance(obj, Window):
            result = {}
            for key in obj.d :
                result[key]= obj.d[key]
            
            return result
            raise TypeError(repr(obj) + " fail !") 
        
        if isinstance(obj, dict):
            result = {}
            for key in obj :
                result[key]= obj[key]
            
            return result
            raise TypeError(repr(obj) + " fail !") 

    def toPython(self, obj_dict):
        '''Reverse serializer for json module'''
        if "reads_segmented" in obj_dict:
            obj = ListWindows()
            for key in obj_dict :
                if key != "links" :
                    if isinstance(obj_dict[key], list):
                        obj.d[key]=obj_dict[key]
                    else :
                        obj.d[key]=[obj_dict[key]]
            return obj

        if "window" in obj_dict:
            obj = Window(1)
            for key in obj_dict :
                #hack for data file with seg_stat (first version)
                if key == "seg_stat" and isinstance(obj_dict[key], dict) : 
                    obj.d[key]=[obj_dict[key]]
                else :
                    obj.d[key]=obj_dict[key]
            return obj
            
        if not "window" in obj_dict and not "reads_segmented" in obj_dict:
            res = {}
            for key in obj_dict :
                res[key]=obj_dict[key]
            return res
        


######
def common_substring(l):
    '''Return the longest common substring among the strings in the list
    >>> common_substring(['abcdfffff', 'ghhhhhhhhhbcd'])
    'bcd'
    >>> common_substring(['abcdfffff', 'ghhhhhhhhh'])
    ''
    >>> common_substring(['b-abc-123', 'tuvwxyz-abc-321', 'tuvwxyz-abc-456', 'd-abc-789'])
    '-abc-'
    '''

    table = []
    for s in l:
        # adds in table all substrings of s - duplicate substrings in s are added only once
        table += set(s[j:k] for j in range(len(s)) for k in range(j+1, len(s)+1))

    # sort substrings by length (descending)
    table = sorted(table, cmp=lambda x,y: cmp(len(y), len(x)))
    # get the position of duplicates and get the first one (longest)
    duplicates=[i for i, x in enumerate(table) if table.count(x) == len(l)]
    if len(duplicates) > 0:
        return table[duplicates[0]]
    else:
        return ""

def interesting_substrings(l, target_length=6, substring_replacement='-'):
    '''Return a list with intersting substrings.
    Now it removes common prefixes and suffixes, and then the longest 
    common substring. 
    But it stops removing once all lengths are at most 'target_length'.

    >>> interesting_substrings(['ec-3--bla', 'ec-512-bla', 'ec-47-bla'], target_length=0)
    ['3-', '512', '47']
    >>> interesting_substrings(['ec-A-seq-1-bla', 'ec-B-seq-512-bla', 'ec-C-seq-21-bla'], target_length=0, substring_replacement='')
    ['A1', 'B512', 'C21']
    >>> interesting_substrings(['ec-A-seq-1-bla', 'ec-B-seq-512-bla', 'ec-C-seq-21-bla'], target_length=0)
    ['A-1', 'B-512', 'C-21']
    >>> interesting_substrings(['ec-A-seq-1-bla', 'ec-B-seq-512-bla', 'ec-C-seq-21-bla'], target_length=9)
    ['A-seq-1', 'B-seq-512', 'C-seq-21']
    '''

    if not l:
        return {}

    if max(map (len, l)) <= target_length:
        return l

    min_length = min(map (len, l))

    ### Remove prefixes

    common_prefix = 0
    for i in range(min_length):
        if all(map(lambda x: x[i] == l[0][i], l)):
            common_prefix = i+1
        else:
            break

    substrings = [x[common_prefix:] for x in l]

    if max(map (len, substrings)) <= target_length:
        return substrings

    ### Remove suffixes

    common_suffix = 0
    for i in range(min_length - common_prefix):
        if all(map(lambda x: x[-(i+1)] == l[0][-(i+1)], l)):
            common_suffix = i
        else:
            break

    substrings = [x[common_prefix:-(common_suffix+1)] for x in l]            

    if max(map (len, substrings)) <= target_length:
        return substrings

    ### Remove the longest common substring
    
    #Have to replace '' by '_' if the removal have place between 2 substrings 

    common = common_substring(substrings)
    if common:
        substrings = [s.replace(common, substring_replacement) for s in substrings]

    return substrings
    
    # ### Build dict
    # substrings = {}
    # for x in l:
    #     substrings[x] = x[common_prefix:-(common_suffix+1)]
    # return substrings

 
class AccessedDict(dict):
    '''Dictionary providing a .not_accessed_keys() method
    Note that access with .get(key) are not tracked.

    >>> d = AccessedDict({1:11, 2:22, 3: 33, 4: 44})

    >>> d[1], d[3]
    (11, 33)

    >>> list(d.not_accessed_keys())
    [2, 4]
    '''

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.accessed_keys = []

    def __getitem__(self, key):
        self.accessed_keys.append(key)
        return dict.__getitem__(self, key)

    def not_accessed_keys(self):
        for key in self.keys():
            if key in self.accessed_keys:
                continue
            yield key





### some data used for test
w1 = Window(1)
w1.d ={"window" : "aaa", "size" : [5], "top" : 3 }
w2 = Window(1)
w2.d ={"window" : "bbb", "size" : [12], "top" : 2 }
w3 = Window(1)
w3.d ={"window" : "aaa", "size" : [8], "top" : 4 }
w4 = Window(1)
w4.d ={"window" : "ccc", "size" : [2], "top" : 8, "test" : ["plop"] }


w5 = Window(1)
w5.d ={"window" : "aaa", "size" : [5], "top" : 3 }
w6 = Window(1)
w6.d ={"window" : "bbb", "size" : [12], "top" : 2 }

lw1 = ListWindows()
lw1.d["reads_segmented"]=[[25]]
lw1.d["windows"].append(w5)
lw1.d["windows"].append(w6)

w7 = Window(1)
w7.d ={"window" : "aaa", "size" : [8], "top" : 4 }
w8 = Window(1)
w8.d ={"window" : "ccc", "size" : [2], "top" : 8, "test" : ["plop"] }

lw2 = ListWindows()
lw2.d["reads_segmented"]=[[34]]
lw2.d["windows"].append(w7)
lw2.d["windows"].append(w8)

    
    

 
def main():
    print "#", ' '.join(sys.argv)

    DESCRIPTION = 'Vidjil utility to parse and regroup list of clones of different timepoints or origins'
    
    #### Argument parser (argparse)

    parser = argparse.ArgumentParser(description= DESCRIPTION,
                                    epilog='''Example:
                                    python2 %(prog)s --germline IGH ../out/vidjil.data''',
                                    formatter_class=argparse.RawTextHelpFormatter)


    group_options = parser.add_argument_group() # title='Options and parameters')

    group_options.add_argument('--test', action='store_true', help='run self-tests')
    group_options.add_argument('--merge', action='store_true', help='merge multiple system')
    
    group_options.add_argument('--compress', '-c', action='store_true', help='compress point names, removing common substrings')
    group_options.add_argument('--pipeline', '-p', action='store_true', help='compress point names (internal Bonsai pipeline)')

    group_options.add_argument('--output', '-o', type=str, default='fused.data', help='output file (%(default)s)')
    group_options.add_argument('--top', '-t', type=int, default=50, help='keep only clones in the top TOP of some point (%(default)s)')
    group_options.add_argument('--germline', '-g', type=str, default='TRG', help='germline used (%(default)s): TRG, IGH, TRB, ...')

    parser.add_argument('file', nargs='+', help='''input files (.vidjil/.cnltab)''')
  
    args = parser.parse_args()
    # print args

    if args.test:
        import doctest
        doctest.testmod(verbose = True)
        sys.exit(0)

    jlist_fused = None

    print "### fuse.py -- " + DESCRIPTION
    print

    if args.merge:
        for path_name in args.file:
            jlist = ListWindows()
            jlist.load(path_name, args.pipeline)
            jlist.add_system_info()
            
            print "\t", jlist,

            if jlist_fused is None:
                jlist_fused = jlist
            else:
                jlist_fused = jlist_fused * jlist
                
            print '\t==> merge to', jlist_fused
        jlist_fused.d['germline'][0] = "multi"
        
    else:
        print "### Read and merge input files"
        for path_name in args.file:
            jlist = ListWindows()
            jlist.load(path_name, args.pipeline)
            
            w1 = Window(1)
            w2 = Window(2)
            w3 = w1+w2
            
            print "\t", jlist,
            # Merge lists
            if jlist_fused is None:
                jlist_fused = jlist
            else:
                jlist_fused = jlist_fused + jlist
            
            print '\t==> merge to', jlist_fused
        jlist_fused.d['germline'][0] = args.germline
        
        print
        print "### Select point names"
        l = jlist_fused.d["point"]
        ll = interesting_substrings(l)
        print "  <==", l
        print "  ==>", ll
        jlist_fused.d["point"] = ll

    if args.compress:
        print
        print "### Compress point names"
        l = jlist_fused.d["point"]
        ll = interesting_substrings(l)
        print "  <==", l
        print "  ==>", ll
        jlist_fused.d["point"] = ll
    
    print
    jlist_fused.cut(args.top, len(l))
    print "\t", jlist_fused 
    print

    print "### Save merged file"
    jlist_fused.save_json(args.output)

    
    
if  __name__ =='__main__':
    main()
