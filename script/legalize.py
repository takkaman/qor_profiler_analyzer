import re
import sys

print "RMS MAX AVG TTL_MV LG_DISP"
log = sys.argv[1]
f = open(log).readlines()
legalize_list = []

for line in f:
    match = re.search("rms cell displacement:.*um\s+\(\s*(\S+)\s+row height\)", line)
    if match:
        legalize_list.append(match.group(1))

    match = re.search("max cell displacement:.*um\s+\(\s*(\S+)\s+row height\)", line)
    if match:
        legalize_list.append(match.group(1))

    match = re.search("avg cell displacement:.*um\s+\(\s*(\S+)\s+row height\)", line)
    if match:
        legalize_list.append(match.group(1))

    match = re.search("number of cells moved:\s*(\d+)$", line)
    if match:
        legalize_list.append(match.group(1))

    match = re.search("number of large displacements:\s*(\d+)$", line)
    if match:
        legalize_list.append(match.group(1))
        print (" ").join(legalize_list)
        legalize_list = []              