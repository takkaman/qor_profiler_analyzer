import re
import sys

print "FUNC_ELAPSE MEM_PEAK"
log = sys.argv[1]
f = open(log).readlines()
func_stack = []
ttl_elapse = 0
ttl_mem = 0

for line in f:
    match = re.search("START_FUNC:\s+(.*)\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
    if match:
        func_name = match.group(1).strip().split()  
        func_name =  "_".join(func_name).replace('-','_')
        elapse_start = match.group(2)
        mem_start = match.group(3)
        func_cand = [func_name, elapse_start, mem_start]

        if len(func_stack):
            func_stack.pop()
        func_stack.append(func_cand)

    match = re.search("END_FUNC:\s+(.*)\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
    if match:
        if len(func_stack):
            func_name = match.group(1).strip().split()  
            func_name =  "_".join(func_name).replace('-','_')
            elapse_end = match.group(2)
            mem_end = match.group(3)

            if func_name == func_stack[0][0]:
                ttl_elapse += int(elapse_end)-int(func_stack[0][1])
                ttl_mem += int(mem_end)-int(func_stack[0][2])
                print func_name, ttl_elapse, ttl_mem
                func_stack.pop()