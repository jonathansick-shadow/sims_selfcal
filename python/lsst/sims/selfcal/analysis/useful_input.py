#####
#  Lynne Jones, ljones@astro.washington.edu.
#  svn version info : $Id$
#
# This module has some input / output methods for python which are useful for
# general analysis. Suitable for flexible, quick input/output, but if you need a
# large data volume or faster read/write, you probably want something more efficient.
#
# This basically, gives you a set of functions to connect to, then query, then
# close a database - either mysql or postgres - or read from a data file,
# and place the data read from those sources into a python dictionary of
# numpy arrays (keys for the dictionary are user-defined).
#   (the readDatafile method could be better done using recarrays from numpy I think, but
#    this is a to-do. )
#
# Requires numpy, MySQLdb, and pgdb (or psycopg2) modules for python.
#
# * sqlConnect(hostname='localhost', username='lsst', passwdname='lsst', dbname='opsimdev',
#             type="mysql", verbose=True):
#   This sets up your connection to the database. Returns the connection and cursor objects.
# * sqlEndConnect(conn, cursor, verbose=True):
#   This ends your connection to the database. Execute when done with all queries.
# * sqlQuery(cursor, query, verbose=True):
#   This executes your query.
# * sqlQueryLimited(cursor, query, verbose=True, offset=0, drows=1000):
#   This executes your query, for a subset of the data (drows). Might not work for postgres?
# * assignResults(sqlresults, keys):
#   This puts your database results into the python dictionary of numpy arrays.
# * readDatafile(infilename, keys, keytypes=None,
#   This reads your data file and puts the results into numpy arrays. If the
#    file includes non-numeric data, include the keytypes.
# * writeDatafile(outfilename, data, keys, printheader=True, newfile=True):
#   Take your python dictionary and write it out to disk.
#
#####

# general python modules
import numpy as n
# import MySQLdb as mysql  #not in latest stack
#import pgdb as pgsql
#import psycopg2 as pgsql

# for opsim
minexpmjd = 49353.
maxexpmjd = 53003.
midnight = 0.66

deg2rad = n.pi/180.0
rad2deg = 180.0/n.pi


def readDatafile(infilename, keys, keytypes=None,
                 startcol=0, cols=None, sample=1, skiprows=0, delimiter=None):
    """Read values from infilename, in columns keys, and return dictionary of numpy arrays.

    Limitation - while startcol can be >0, cannot skip columns beyond that point."""
    # open file
    import sys
    try:
        f = open(infilename, 'r')
    except IOError:
        print >>sys.stderr, "Couldn't open file %s" % (infilename)
        print >>sys.stderr, "Returning None values"
        value = {}
        for i in keys:
            value[i] = None
        return value
    print >>sys.stderr, "Reading file %s" % (infilename)
    # Read data from file.
    value = {}
    for key in keys:
        value[key] = []
    sampleskip = 0
    i = 0
    for line in f:
        i = i + 1
        if line.startswith("!"):
            continue
        if line.startswith("#"):
            continue
        sampleskip = sampleskip + 1
        # Assign values
        if sampleskip == sample:
            linevalues = line.split()
            j = startcol
            if len(linevalues) >= (len(keys)-j):
                for key in keys:
                    try:
                        value[key].append(linevalues[j])
                    except IndexError:
                        print "readDataFile failed at line %d, column %d, key=%s" \
                              % (i, j+1, key)
                        print "Data values: %s" % (linevalues)
                        raise IndexError
                    j = j+1
            sampleskip = 0
    # End of loop over lines.
    # Convert to numpy arrays.
    for key in keys:
        if keytypes != None:
            value[key] = n.array(value[key], dtype=keytypes[keys.index(key)])
        else:
            value[key] = n.array(value[key], dtype='float')
    f.close()
    return value


def writeDatafile(outfilename, data, keys, printheader=True, newfile=True):
    """Write dictionary of numpy arrays to file, potentially appending to existing file."""
    import sys
    if newfile:
        try:
            fout = open(outfilename, 'w')
        except IOError:
            print >>sys.stderr, "Couldn't open file %s" % (outfilename)
            return
    else:
        try:
            fout = open(outfilename, 'a')
        except IOError:
            print >>sys.stderr, "Couldn't open file %s" % (outfilename)
            return
    # Print header information if desired.
    if printheader:
        writestring = "# "
        for key in keys:
            writestring = writestring + " " + key
        print >>fout, writestring
    # Print data information.
    datatype = {}
    for key in keys:
        if isinstance(data[key][0], float):
            datatype[key] = 'float'
        elif isinstance(data[key][0], int):
            datatype[key] = 'int'
        elif isinstance(data[key][0], str):
            datatype[key] = 'str'
        else:
            datatype[key] = 'unknown'
            print >>sys.stderr, "Couldn't determine data type of values with %s key; will skip in output" % (
                key)
    for i in range(len(data[keys[0]])):
        writestring = ""
        for key in keys:
            if datatype[key] == 'str':
                writestring = writestring + " " + data[key][i]
            elif datatype[key] == 'float':
                writestring = writestring + " %f" % (data[key][i])
            elif datatype[key] == 'int':
                writestring = writestring + " %d" % (data[key][i])
        # Done constructing write line.
        print >>fout, writestring
    # Done writing data.
    fout.close()
