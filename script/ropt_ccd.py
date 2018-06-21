import re
import sys
import copy

print "WNS WGS TNS NVP WNHS TNHS NHVP"
log = sys.argv[1]
f = open(log).readlines()

DEFAULT_DICT = {
    'setup': ['-','-','-','-'],
    'hold': ['-','-','-'],
}

ccd_start = False
just_start = True
wns = wnhs = 0

for line in f:
    if "START_FUNC: Concurrent Clock Data Optimization Engine" in line or "CCD initialization runtime:" in line:
        ccd_start = True
        continue
    if "END_FUNC: Concurrent Clock Data Optimization Engine" in line or "CCD flow runtime:" in line:
        print step_name, (" ").join(ccd_qor_list['setup']), (" ").join(ccd_qor_list['hold'])
        ccd_start = False
        continue

    if ccd_start:
        match = re.search("^CCD:\s+(.*):", line)
        if match:
            if not just_start:
                print step_name, (" ").join(ccd_qor_list['setup']), (" ").join(ccd_qor_list['hold'])
            just_start = False
            ccd_qor_list = copy.copy(DEFAULT_DICT)
            step_name = match.group(1).strip().split()
            step_name = "_".join(step_name)   
            wns = wnhs = 0       
            continue

        match = re.search("Scenario\s+.*\s+WNS\s+=\s+(\S+),\s+WEIGHTED_GROUP_SLACK\s+=\s+(\S+),\s+TNS\s+=\s+(\S+),\s+NVP\s+=\s+(\S+)", line)
        if match:
            if match.group(1) == 'invalid':
                continue

            wns_tmp = float(match.group(1))
            #print match.group(1), match.group(2), match.group(3), match.group(4)
            if wns_tmp >= wns:
                wns = wns_tmp
                ccd_qor_list['setup'] = [match.group(1), match.group(2), match.group(3), match.group(4)]

        match = re.search("Scenario .*\s+WNHS\s+=\s+(\S+),\s+TNHS\s+=\s+(\S+),\s+NHVP\s+=\s+(\S+)", line)
        if match:
            if match.group(1) == 'invalid':
                continue

            wnhs_tmp = float(match.group(1))
            #print wnhs_tmp
            if wnhs_tmp >= wnhs:
                wnhs = wnhs_tmp
                ccd_qor_list['hold'] = [match.group(1), match.group(2), match.group(3)]