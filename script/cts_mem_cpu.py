import re
import sys

print "CPU ELAPSE MEM"
log = sys.argv[1]
f = open(log).readlines()

for line in f:
    match = re.search("START_FUNC:\s+(.*)\s+CPU:\s+(\d+)\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
    if match:
        group_1 = match.group(1).strip().split()
        group_1 =  "_".join(group_1).replace('-','_')
        print group_1, ' ', match.group(2), ' ', match.group(3), ' ', match.group(4)

