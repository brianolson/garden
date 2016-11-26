#!/usr/bin/env python

import serial
import sys
import time


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage:\n\treader.py /dev/cu.{port}\n")
        sys.exit(1)
    #fin = open(sys.argv[1], 'r')
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
