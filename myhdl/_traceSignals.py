#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003 Jan Decaluwe
#
#  The myhdl library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 2.1 of the
#  License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" myhdl traceSignals module.

"""

__author__ = "Jan Decaluwe <jan@jandecaluwe.com>"
__revision__ = "$Revision$"
__date__ = "$Date$"

from inspect import currentframe, getouterframes
import time
import os
path = os.path
import shutil
from sets import Set

from myhdl import _simulator, Signal, __version__
from myhdl._util import _isGenSeq, _isGenFunc
from myhdl._extractHierarchy import _findInstanceName, _HierExtr

_tracing = 0
_profileFunc = None

class Error(Exception):
    """ traceSignals Error"""
    def __init__(self, arg=""):
        self.arg = arg
    def __str__(self):
        msg = self.__doc__
        if self.arg:
            msg = msg + ": " + str(self.arg)
        return msg

class TopLevelNameError(Error):
    """result of traceSignals call should be assigned to a top level name"""

class ArgTypeError(Error):
    """traceSignals first argument should be a classic function"""
    
class MultipleTracesError(Error):
    """Cannot trace multiple instances simultaneously"""


def traceSignals(dut, *args, **kwargs):
    global _tracing
    if _tracing:
        return dut(*args, **kwargs) # skip
    if not callable(dut):
        raise ArgTypeError("got %s" % type(dut))
    if _simulator._tracing:
        raise MultipleTracesError()
    _tracing = 1
    try:
        outer = getouterframes(currentframe())[1]
        name = _findInstanceName(outer)
        if name is None:
            raise TopLevelNameError
        h = _HierExtr(name, dut, *args, **kwargs)
        vcdpath = name + ".vcd"
        if path.exists(vcdpath):
            backup = vcdpath + '.' + str(path.getmtime(vcdpath))
            shutil.copyfile(vcdpath, backup)
            os.remove(vcdpath)
        vcdfile = open(vcdpath, 'w')
        _simulator._tracing = 1
        _simulator._tf = vcdfile
        _writeVcdHeader(vcdfile)
        _writeVcdSigs(vcdfile, h.hierarchy)
    finally:
        _tracing = 0
    return h.top


_codechars = ""
for i in range(33, 127):
    _codechars += chr(i)
_mod = len(_codechars)

def _genNameCode():
    n = 0
    while 1:
        yield _namecode(n)
        n += 1
        
def _namecode(n):
    q, r = divmod(n, _mod)
    code = _codechars[r]
    while q > 0:
        q, r = divmod(q, _mod)
        code = _codechars[r] + code
    return code

def _writeVcdHeader(f):
    print >> f, "$date"
    print >> f, "    %s" % time.asctime()
    print >> f, "$end"
    print >> f, "$version"
    print >> f, "    MyHDL %s" % __version__
    print >> f, "$end"
    print >> f, "$timesscale"
    print >> f, "    1ns"
    print >> f, "$end"
    print >> f

def _writeVcdSigs(f, hierarchy):
    curlevel = 0
    namegen = _genNameCode()
    siglist = []
    for level, name, sigdict in hierarchy:
        delta = curlevel - level
        curlevel = level
        assert(delta >= -1)
        if delta >= 0:
            for i in range(delta + 1):
                print >> f, "$upscope $end"
        print >> f, "$scope module %s $end" % name
        for n, s in sigdict.items():
            if not s._tracing:
                s._tracing = 1
                s._code = namegen.next()
                siglist.append(s)
            w = s._nrbits
            if w:
                if w == 1:
                    print >> f, "$var reg 1 %s %s $end" % (s._code, n)
                else:
                    print >> f, "$var reg %s %s %s $end" % (w, s._code, n)
            else:
                print >> f, "$var real 1 %s %s $end" % (s._code, n)
    for i in range(curlevel):
        print >> f, "$upscope $end"
    print >> f
    print >> f, "$enddefinitions $end"
    print >> f, "$dumpvars"
    for s in siglist:
        s._printVcd() # initial value
    print >> f, "$end"
            
            
        
        


    
    

            
        
    
    
