#!/usr/bin/python3
#

import datetime
import logging
import os
import re
import shutil
import sys
import time

logger = logging.getLogger(__name__)


class TimelapseShuffler(object):
    def __init__(self, timelapseRootPath='/mnt/usb128/timelapse'):
        self.timelapseRootPath = timelapseRootPath
        self.pathParseRe = re.compile(r'i(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)\.jpg')
        self.now = None
        self.lt = None

    def setNow(self):
        self.now = time.time()
        self.lt = time.localtime(self.now)

    def filenameToDate(self, filename):
        # Parse immddHHMMSS.jpg made by raspistill
        # Return (timestamp seconds, time tuple from time.localtime)
        m = self.pathParseRe.match(filename)
        if not m:
            logger.error('could not parse filename: %r', filename)
            return None, None
        month = int(m.group(1))
        day = int(m.group(2))
        hour = int(m.group(3))
        minute = int(m.group(4))
        second = int(m.group(5))
        if lt.tm_mon == 1 and month == 12:
            year = lt.tm_year - 1
        else:
            year = lt.tm_year
        tt = (year, month, day, hour, minute, second, 0, 0, 0)
        then = time.mktime(tt)
        return then, time.localtime(then)

    def shuffle(self):
        self.setNow()
        lt = self.lt
        # day 1 (yesterday), keep everything
        # day 2 (before that), keep ..:..:00 (throw away :30 images)
        # day 3, keep ..:.0:00, one image per 10 minutes
        # day Inf, keep ..:00:00 one image per hour
        today = datetime.date.fromtimestamp(self.now)
        day1 = previousDate(today)
        day2 = previousDate(day1)
        day3 = previousDate(day2)

        day3path = os.path.join(self.timelapseRootPath, daystr(day3))
        if os.path.exists(day3path):
            archiveDir = os.path.join(self.timelapseRootPath, day3.strftime('%Y%m'))
            if not os.path.exists(archiveDir):
                os.makedirs(archiveDir)
            # move hourly into archive
            nextlt = (day3.year, day3.month, day3.day, 0,0,0, 0,0,0)
            nextt = time.mktime(nextlt)
            nextlt = time.localtime(nextt)
            they = sorted(filter lambda x: x.endswith('.jpg'), os.listdir(day3path))
            for imagename in they:
                filetime, filelt = self.filenameToDate(imagename)
                if filetime is not None:
                    if filetime < nextt:
                        continue
                    shutil.move(os.path.join(day3path, imagename), archiveDir)
                    nextt, nextlt = nextHour(nextlt)
                    if nextlt.tm_mday != day3.day:
                        break


def previousDate(somedate):
    return datetime.date.fromordinal(somedate.toordinal() - 1)

def nextHour(lt):
    nextlt = (lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour + 1, 0, 0, 0,0,0)
    nextt = time.mktime(nextlt)
    return nextt, time.localtime(nextt)

def daystr(somedate):
    return somedate.strftime('%Y%m%d')

