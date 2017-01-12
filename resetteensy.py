#!/usr/bin/env python3

import fcntl
import re
import subprocess
import sys

USBDEVFS_RESET = 0x00005514 # from <linux/usbdevice_fs.h>

def main():
    proc = subprocess.Popen(['lsusb'], stdout=subprocess.PIPE)
    # Bus 001 Device 004: ID 16c0:0483 Van Ooijen Technische Informatica Teensyduino Serial
    stdoutdata, stderrdata = proc.communicate()
    pat = re.compile(r'Bus\s+(\d+)\s+Device\s+(\d+).*Teensyduino Serial')
    bus = None
    device = None
    for line in stdoutdata.splitlines():
        m = pat.match(line)
        if m:
            bus = m.group(1)
            device = m.group(2)
            break
    if (bus is None) or (device is None):
        sys.stderr.write("teensyduino not found in lsusb\n")
        sys.exit(1)
        return
    pf = open('/dev/bus/usb/{}/{}'.format(bus, device), 'wb')
    pfd = pf.fileno()
    fcntl.ioctl(pfd, USBDEVFS_RESET, 0)
    pf.close()
    return


if __name__ == '__main__':
    main()
