#!/usr/bin/env python

import logging
import serial
import sys
import time


logger = logging.getLogger(__name__)


class TimeTempHumidity(object):
    def __init__(self, when, tempHumids):
        # timestamp float seconds
        self.when = when
        # [temp C, % humid, ...]
        self.tempHumids = tempHumids

def degCtoF(degC):
    return (degC * 1.8) + 32

class Reader(object):
    def __init__(self, dev=None):
        self.devPath = dev
        self.ser = None
        # Callable that receives (this Reader, newest TimeTempHumidity).
        # Runs in the thread that reads data from the serial port.
        self.listeners = []
        # each entry is TimeTempHumidity
        self.recentData = []
        self.recentLimit = 100

    def run(self):
        ser = serial.Serial(sys.argv[1], 115200, timeout=0.5)
        while True:
            line = ser.readline()
            if not line:
                continue
            line = line.strip()
            if not line:
                continue
            if line[0] == '#':
                continue
            now = time.time()
            try:
                parts = list(map(lambda x: x.strip(), line.split(b'\t')))
                tempHumids = []
                while len(parts) >= 2:
                    tempHumids.append(float(parts.pop(0))) # degC
                    tempHumids.append(float(parts.pop(0))) # % humid
                newRecord = TimeTempHumidity(now, tempHumids)
                self.recentData.append(newRecord)
                if len(self.recentData) > self.recentLimit:
                    self.recentData = self.recentData[-self.recentLimit:]
                self.notifyListeners(newRecord)
            except Exception as e:
                logger.error('err reading and parsing: %s', e, exc_info=True)
                #sys.stdout.write('{}\t\t\t\t\tbad read\n'.format(timestr))
                pass

    def notifyListeners(self, record):
        for lister in self.listeners:
            lister(self, record)

def printListener(reader, newRecord):
    timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(newRecord.when))
    parts = [timestr, str(newRecord.when)]
    for i in range(0, len(newRecord.tempHumids), 2):
        degC = newRecord.tempHumids[i]
        degF = degCtoF(degC)
        pctHumid = newRecord.tempHumids[i+1]
        parts.append('{:0.1f}\t{:0.1f}\t{}'.format(degC, degF, pctHumid))
    sys.stdout.write('\t'.join(parts) + '\n')

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage:\n\treader.py /dev/cu.{port}\n")
        sys.exit(1)
    reader = Reader(sys.argv[1])
    reader.listeners.append(printListener)
    reader.run()

def _old_main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage:\n\treader.py /dev/cu.{port}\n")
        sys.exit(1)
    ser = serial.Serial(sys.argv[1], 115200, timeout=0.5)
    while True:
        line = ser.readline()
        if not line:
            continue
        line = line.strip()
        if not line:
            continue
        if line[0] == '#':
            continue
        now = time.time()
        timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        try:
            parts = map(lambda x: x.strip(), line.split('\t'))
            degC = float(parts[0])
            degF = (degC * 1.8) + 32
            percentHumidity = float(parts[1])
            sys.stdout.write('{}\t{}\t{}\t{:0.1f}\t{}\t\n'.format(timestr, now, parts[0], degF, percentHumidity))
        except Exception as e:
            sys.stdout.write('{}\t\t\t\t\tbad read\n'.format(timestr))


if __name__ == '__main__':
    main()
