import sys
from urllib2 import urlopen
import datetime

baseurl = "ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/"

default_stations = ["kbos", "kmsp", "kdca", "ymml", "cyul"]

def stationurl(stn):
    return "%s%s.TXT" % (baseurl, stn.upper())

def fetchcurrent(stn):
    url = stationurl(stn)
    r = urlopen(url)
    return r.read()

def rawparts(s):
    return s.strip().splitlines()

def dateparse(ds):
    return datetime.datetime.strptime(ds, "%Y/%m/%d %H:%M")

class Parser:

    _parts = ["station", "datetime", ]

    def parse(raw):
        s = raw.strip().strip("=")
        if s.find("METAR") == 0:
            s = s[5:]
        
        s = s.split(" ")


        parsed = s

        return parsed

if __name__ == "__main__":

    def usage():
        print "metar [fetch stn [stn...]]"

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    if sys.argv[1] == "fetch":
        if len(sys.argv) < 3:
            usage()
            sys.exit(1)

        stations = sys.argv[2:]

        for stn in stations:
            try:
                ds, ms = rawparts(fetchcurrent(stn))
                d = dateparse(ds)
                print "%s\t%s" % (d, ms)
            except:
                sys.stderr.write("couldn't fetch: %s\n" % (stn,))
