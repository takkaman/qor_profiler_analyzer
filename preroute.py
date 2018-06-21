#!/remote/us01home40/phyan/depot/Python-2.7.11/bin/python
import sys 
import os
import commands
import re

from collections import defaultdict

import numpy as np
import pandas as pd

METRICS_ORDER_1 = ["CPU", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM"]
METRICS_ORDER_2 = ["CPU", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM", "LEAKPWR"]
METRICS_ORDER_3 = ["CPU", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM", "WHNS"]
METRICS_ORDER_4   = ["CPU", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM",  "LEAKPWR", "WHNS"]
METRICS_ORDER   = ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "AREA",  "MEM", "CPU", "LVTCNT", "LVTPCNT", "LEAKPWR", "WHNS"]

CALC = [3600, 60, 1]

COPT_PATTERN = "Perform clock synthesis and placement+optimization (clock_opt) flow"
POPT_PATTERN = "Perform placement and circuit optimization (place_opt) on design"
REFINE_PATTERN = "Perform placement and circuit optimization (refine_opt) on design"
INIT_PLACE = "Running initial placement"
HFSDRC = "Running initial HFS and DRC step"
INIT_OPTO = "Running initial optimization step"
FINAL_PLACE = "Running final (timing-driven) placement step"
FINAL_OPTO = "Running final optimization step"

def pr_log_extractor(log, compress=False):
    hb = pd.DataFrame(index=METRICS_ORDER_4)
    first = n = flag = num = 0
    step_num = 0
    f = open(log).readlines()
    for line in f:
        #decide core cmd
        if line.find(COPT_PATTERN) >= 0:
            cmd = "C"
        elif line.find(POPT_PATTERN) >= 0:
            cmd = "P"
        elif line.find(REFINE_PATTERN) >= 0:
            cmd = "RF"

        #decide stage of place_opt
        if line.find(INIT_PLACE) >= 0:
            suffix = "1"
        elif line.find(HFSDRC) >= 0:
            suffix = "2"
        elif line.find(INIT_OPTO) >= 0:
            suffix = "3"
        elif line.find(FINAL_PLACE) >= 0:
            suffix = "4"
        elif line.find(FINAL_OPTO) >= 0:
            suffix = "5"

        if line.find("WORST NEG TOTAL") >= 0:
            n +=1
            flag = 1
            if line.find("LEAKAGE") >= 0 and line.find("MIN DELAY") >= 0:
                hb_col = pd.DataFrame(index=METRICS_ORDER_4)
            elif line.find("LEAKAGE") >= 0:
                hb_col = pd.DataFrame(index=METRICS_ORDER_2)
            elif line.find("MIN DELAY") >= 0:
                hb_col = pd.DataFrame(index=METRICS_ORDER_3)
            else:
                hb_col = pd.DataFrame(index=METRICS_ORDER_1)

            continue
        

        if flag:
            n += 1
            if n == 4:
                step_num += 1
                num += 1
                n = flag = 0 
                hb_list = line.split()
                step = "("+str(step_num)+cmd+suffix+")"+hb_list[0]
                #hb_col[step] = hb_list[1:]
                if len(hb_list[1:]) == len(hb_col.index):
                    hb_col[step] = hb_list[1:]
                else:
                    print "abnormal beartbeat line: %s" %line
                hb = pd.concat([hb, hb_col], axis=1)

    for i in range(len(hb.loc["CPU"])):          
        hb.loc["CPU"][i] = sum([int(hb.loc["CPU"][i].split(":")[index]) * CALC[index] for index in range(3)])

    if not hb.loc["WHNS"].isnull().all():
        for i in range(len(hb.loc["WHNS"])):
            #print type(hb.loc["WHNS"][i])
            if hb.loc["WHNS"][i] is np.nan:
                if i == 0:
                    hb.loc["WHNS"][i] = "0.0001"
                else:
                    hb.loc["WHNS"][i] = hb.loc["WHNS"][i-1]
    else:
        hb.loc["WHNS"].fillna("-",inplace=True)

    hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)

    return hb.reindex(METRICS_ORDER)

def main():
    log_name = sys.argv[1]
    compress = sys.argv[2]
    hb = pr_log_extractor(log_name, compress)

if __name__ == "__main__":
    main()

