import sys
from urllib2 import urlopen
import datetime
import re

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

    _parts = ["station", "datetime", "wind", "visibility", 
        "runway_visual_range", "current_weather", "cloud_cover", 
        "temperature", "atmospheric_pressure"]

    def parse(self, raw):
        s = raw.strip().strip("=")
        if s.find("METAR") == 0:
            s = s[5:]
        
        s = s.split(" ")


        parsed = []

        i = 0

        for pt in self._parts:
            if i > len(s):
                continue
            spt = s[i]
            cb = getattr(self, "parse_"+pt, False)
            if not cb:
                continue
            pd = cb(spt)
            if pd is False:
                parsed.append(None)
                continue
            elif pt == 'cloud_cover':
                j = 1
                while pd:
                    spt = s[i+j]
                    pd = cb(spt)
                    if pd is not False:
                        parsed.append(pd)
                    j = j + 1
                i = i + j - 1
                continue
            i = i + 1
            parsed.append(pd)

        return parsed

    def parse_station(self, stn):
        return stn

    def parse_datetime(self, dtraw):
        dom = int(dtraw[0:2])
        h = int(dtraw[2:4])
        m = int(dtraw[4:6])
        tz = dtraw[6:]
        return (dom, h, m, tz)

    def parse_wind(self, wraw):
        if wraw[0:3] == "VRB":
            dirxn = -1
        else:
            dirxn = int(wraw[0:3])
        vel = int(wraw[3:5])
        units = wraw[5:]
        return (dirxn, vel, units)

    def parse_visibility(self, vraw):
        p = re.compile(r'(?P<distance>\d+)(?P<units>\w+)?')
        m = p.search(vraw).groupdict()
        m["distance"] = int(m["distance"])
        return m

    def parse_current_weather(self, praw):
        p = re.compile(r'(?P<intensity>[\-\+ ])?(?P<descriptor>MI|PR|BC|DR|BL|SH|TS|FZ)?(?P<phenomena>(?P<precipitation>DZ|RA|SN|SG|IC|PL|GR|GS|UP)|'+
            r'(?P<obscuration>BR|FG|FU|VA|DU|SA|HZ|PY)|(?P<other>PO|SQ|FC|SS))')
        m = p.match(praw)
        if m:
            m = p.search(praw)
            m = m.groupdict()
        else:
            m = False
        return m

    def parse_cloud_cover(self, craw):
        p = re.compile(r'(?P<amount>FEW|CLR|SKC|SCT|BKN|OVC)(?P<height>\d{3})')
        m = p.match(craw)
        if m:
            m = p.search(craw)
            m = m.groupdict()
            m["height"] = int(m["height"])*100
        else:
            m = False
        return m

    def parse_temperature(self, traw):
        p = re.compile(r'(?P<negative_temp>M)?(?P<temperature>\d{2})/(?P<negative_dewpoint>M)?(?P<dewpoint>\d{2})?')
        m = p.match(traw)
        if m:
            m = p.search(traw)
            m = m.groupdict()
            m['temperature'] = int(m['temperature'])
            if m.get("negative_temp", False) == 'M':
                m['temperature'] = -m['temperature']
            del m['negative_temp']
            if m.get('dewpoint', False) is not False:
                m['dewpoint'] = int(m['dewpoint'])
            if m.get("negative_dewpoint", False) == 'M':
                m['dewpoint'] = -m['dewpoint']
            del m['negative_dewpoint']
        else:
            m = False
        return m

    def parse_atmospheric_pressure(self, praw):
        p = re.compile(r'(?P<unit>A|Q)(?P<pressure>\d{4})')
        m = p.match(praw)
        if m:
            m = p.search(praw)
            m = m.groupdict()
            if m['unit'] == 'Q':
                m['unit'] = 'mb'
            else:
                m['unit'] = 'inHg'
                m['pressure'] = float(m['pressure']) / 100.0
        else:
            m = False
        return m
            

if __name__ == "__main__":

    def usage():
        sys.stderr.write("metar [[fetch stn [stn...]] | [parse]]\n")

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
            except Exception as e:
                print e
                sys.stderr.write("couldn't fetch: %s (%s)\n" % (stn,e))
    elif sys.argv[1] == "parse":
        p = Parser()
        m = sys.stdin.read()
        print p.parse(m)
    else:
        usage()
        sys.exit(1)
