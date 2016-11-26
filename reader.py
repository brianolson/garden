#!/usr/bin/env python

import logging
import serial
import sys
import threading
import time


logger = logging.getLogger(__name__)


class TimeTempHumidity(object):
    def __init__(self, when, tempHumids):
        # timestamp float seconds
        self.when = when
        # [temp C, % humid, ...]
        self.tempHumids = tempHumids

    def degC(self):
        sumC = 0.0
        count = 0
        for i in range(0, len(self.tempHumids), 2):
            sumC += self.tempHumids[i]
            count += 1
        return sumC / count

    def degF(self):
        return degCtoF(self.degC())

    def pctHumid(self):
        sumH = 0.0
        count = 0
        for i in range(0, len(self.tempHumids), 2):
            sumH += self.tempHumids[i + 1]
            count += 1
        return sumH / count

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

        self.lock = threading.Lock()

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
                with self.lock:
                    self.recentData.append(newRecord)
                    if len(self.recentData) > self.recentLimit:
                        self.recentData = self.recentData[-self.recentLimit:]
                    self._notifyListeners(newRecord)
            except Exception as e:
                logger.error('err reading and parsing: %s', e, exc_info=True)
                #sys.stdout.write('{}\t\t\t\t\tbad read\n'.format(timestr))
                pass

    def addListener(self, lister):
        with self.lock:
            self.listeners.append(lister)

    def getLatest(self):
        with self.lock:
            if not self.recentData:
                return None
            return self.recentData[0]

    def _notifyListeners(self, record):
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
    reader.addListener(printListener)
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
