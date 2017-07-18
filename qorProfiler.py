#!/remote/us01home40/phyan/depot/Python-2.7.11/bin/python
import sys 
import os
import commands
import re
import copy

from collections import defaultdict

import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
from tabulate import tabulate

METRICS_ORDER_1 = ["ELAPSE_TIME", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM"]
METRICS_ORDER_2 = ["ELAPSE_TIME", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM", "LEAKPWR"]
METRICS_ORDER_3 = ["ELAPSE_TIME", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM", "WHNS"]
METRICS_ORDER_4 = ["ELAPSE_TIME", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM",  "LEAKPWR", "WHNS"]
METRICS_ORDER = ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "AREA",  "MEM", "ELAPSE_TIME", "LVTCNT", "LVTPCNT", "LEAKPWR", "WHNS"]
METRICS_ORDER_ROPT = ["RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"]
METRICS_ORDER_GROPT = METRICS_ORDER_ROPT
METRICS_ORDER_NPO = METRICS_ORDER_ROPT
STAGE_LIST = ['initial_place', 'initial_drc','initial_opto','final_place','final_opto']

CALC = [3600, 60, 1]
#core command definition
COPT_PATTERN = "Perform clock synthesis and placement+optimization (clock_opt) flow"
POPT_PATTERN = "Perform placement and circuit optimization (place_opt) on design"
REFINE_PATTERN = "Perform placement and circuit optimization (refine_opt) on design"
#place_opt stage definition
INIT_PLACE = "Running initial placement"
HFSDRC = "Running initial HFS and DRC step"
INIT_OPTO = "Running initial optimization step"
FINAL_PLACE = "Running final (timing-driven) placement step"
FINAL_OPTO = "Running final optimization step"

class QorProfiler():
    def __init__(self, log_list=None, compress=True, pattern="all", script_list=None):
        self._profiler = {"PREROUTE": self.preroute_profiler, "ROPT": self.ropt_profiler, "GROPT":   self.gropt_profiler, "NPO":   self.npo_profiler, "PREROUTE_STG": self.preroute_stg_profiler}
        self._profiler_script = {"PREROUTE": None, "ROPT": None, "GROPT": None, "NPO": None, "PREROUTE_STG": None}
        self.matched_pattern = []
        self.auto_skip_dict = defaultdict(list)
        self.step_match_dict = defaultdict(list)
        self.qor_metrics_dict = defaultdict(list)
        self.step_qor_dict = defaultdict(list)
        self.steps_dict = defaultdict(list)
        self.metrics_order = defaultdict(list)
        self.log_list = log_list
        self.compress = compress
        self.pattern = pattern
        self.script_list = script_list

    def generate_profile(self):
        _profiler = copy.copy(self._profiler)
        _profiler_script = copy.copy(self._profiler_script)
        if self.pattern == "USER":
            i = 1
            for script in self.script_list:
                _profiler['USER'+str(i)] = self.user_profiler
                _profiler_script['USER'+str(i)] = script
                i += 1

        for pattern_name, profiler in _profiler.items():
            script = _profiler_script[pattern_name]
            self.qor_metrics_dict[pattern_name], self.step_qor_dict[pattern_name], \
            self.auto_skip_dict[pattern_name], self.step_match_dict[pattern_name], self.steps_dict[pattern_name], self.metrics_order[pattern_name]  = self._pattern_to_metrics(profiler, script)

        #clear empty pattern    
        for pattern, qor_metrics in self.qor_metrics_dict.items():
            empty_pattern = True
            for metrics in qor_metrics:
                if not pd.DataFrame.from_dict(metrics).empty:
                    empty_pattern = False
            if empty_pattern:
               del(self.qor_metrics_dict[pattern])

    def _pattern_to_metrics(self, profiler, script):
        qor_metrics_list = []
        step_qor_list = []
        steps_list = []
        auto_skip_list = []
        step_length_flag = False

        for log in self.log_list:
            auto_skip = "false"
            step_match = 1
            hb = profiler(log, script)

            #special handling
            hb.fillna("-",inplace=True)
            hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)

            qor_metrics_list.append(hb.T.to_dict(orient='list'))
            step_qor_list.append(hb.T.values.tolist())
            steps_list.append(list(hb.columns))

            if not step_length_flag:
                step_length_flag = True
                step_len = len(hb.columns)
            else:
                if len(hb.columns) != step_len:
                    step_match = 0

            if len(hb.columns) > 80:
                auto_skip = "true"
            auto_skip_list.append(auto_skip)
        
        return qor_metrics_list, step_qor_list, auto_skip_list, step_match, steps_list, list(hb.index)

    def gropt_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_GROPT)
        step_num = 0
        prev_step = ""
        f = open(log).readlines()
        for line in f:
            if not "Global-route-opt optimization" in line or "Global-route-opt optimization summary" in line >= 0: continue
            hb_list = line.split()
            #add wa to skip non-debug ropt log
            if len(hb_list) < 13:
                return hb
            cmd = "R"
            crnt_step = hb_list[2]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-6:]
            else:
                step = "("+str(step_num)+cmd+")"+hb_list[2]               
                hb[step] = hb_list[-10:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step
        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)
        return hb.replace(to_replace="-", value=np.nan)

    def npo_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_NPO)
        step_num = 0
        prev_step = ""
        f = open(log).readlines()
        for line in f:
            if not "npo-clock-opt optimization" in line or "npo-clock-opt optimization summary" in line >= 0: continue
            hb_list = line.split()
            #add wa to skip non-debug ropt log
            if len(hb_list) < 13:
                return hb
            cmd = "R"
            crnt_step = hb_list[2]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-6:]
            else:
                step = "("+str(step_num)+cmd+")"+hb_list[2]               
                hb[step] = hb_list[-10:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step
        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)
        return hb.replace(to_replace="-", value=np.nan)

    def ropt_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_ROPT)
        step_num = 0
        prev_step = ""
        f = open(log).readlines()
        for line in f:
            if not "Route-opt optimization" in line or "Route-opt optimization summary" in line: continue
            hb_list = line.split()
            #add wa to skip non-debug ropt log
            if len(hb_list) < 13:
                return hb
            cmd = "R"
            crnt_step = hb_list[2]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-10:]
            else:
                step = "("+str(step_num)+cmd+")"+hb_list[2]               
                hb[step] = hb_list[-10:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step

        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)
        return hb.replace(to_replace="-", value=np.nan)

    def preroute_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_4)
        first = n = flag = 0
        step_num = 0
        prev_step = ""
        func_name = 'init'
        suffix = "2" #By default, qor calculation start from initial_drc
        cmd = "P" #By default, treat cmd as place_opt

        f = open(log).readlines()
        for line in f:
            #decide core cmd
            
            if COPT_PATTERN in line:
                cmd = "C"
            elif POPT_PATTERN in line:
                cmd = "P"
            elif REFINE_PATTERN in line:
                cmd = "RF"
            #decide stage of place_opt
            if INIT_PLACE in line:
                suffix = "1"
            elif HFSDRC in line:
                suffix = "2"
            elif INIT_OPTO in line:
                suffix = "3"
            elif FINAL_PLACE in line:
                suffix = "4"
            elif FINAL_OPTO in line:
                suffix = "5"

            if "WORST NEG TOTAL" in line:
                n +=1
                flag = 1
                if "LEAKAGE" in line and "MIN DELAY" in line:
                    hb_col = pd.DataFrame(index=METRICS_ORDER_4)
                elif "LEAKAGE" in line:
                    hb_col = pd.DataFrame(index=METRICS_ORDER_2)
                elif "MIN DELAY" in line:
                    hb_col = pd.DataFrame(index=METRICS_ORDER_3)
                else:
                    hb_col = pd.DataFrame(index=METRICS_ORDER_1)
                continue
            
            match = re.search("START_FUNC:\s+(\S+)\s+CPU", line)
            if match:
                func_name = match.group(1)

            if flag:
                n += 1
                if n == 4:
                    n = flag = 0 
                    hb_list = line.split()
                    #hb_col[step] = hb_list[1:]
                    if len(hb_list[1:]) == len(hb_col.index):
                        crnt_step = hb_list[0]
                        if self.compress and crnt_step == prev_step:
                            hb_col[prev_step_hb] = hb_list[1:]
                            hb[prev_step_hb] = hb_col[prev_step_hb]
                        else:                   
                            step = "("+str(step_num)+cmd+suffix+")"+crnt_step
                            hb_col[step] = hb_list[1:]
                            hb = pd.concat([hb, hb_col[step]], axis=1)
                            prev_step = crnt_step
                            prev_step_hb = step
                            step_num += 1                                      
                    elif len(hb_list) == len(hb_col.index):
                        crnt_step = func_name
                        if self.compress and crnt_step == prev_step:
                            hb_col[prev_step_hb] = hb_list
                            hb[prev_step_hb] = hb_col[prev_step_hb]
                        else:                                              
                            step = "("+str(step_num)+cmd+suffix+")"+crnt_step
                            hb_col[step] = hb_list
                            hb = pd.concat([hb, hb_col[step]], axis=1)
                            prev_step = crnt_step
                            prev_step_hb = step
                            step_num += 1
                    else:
                        print "abnormal heartbeat line: %s" %line
                        continue       

        for i in range(len(hb.loc["ELAPSE_TIME"])):          
            hb.loc["ELAPSE_TIME"][i] = sum([int(hb.loc["ELAPSE_TIME"][i].split(":")[index]) * CALC[index] for index in range(3)])             

        if not hb.loc["WHNS"].isnull().all():
            for i in range(len(hb.loc["WHNS"])):
                #print type(hb.loc["WHNS"][i])
                if hb.loc["WHNS"][i] is np.nan:
                    if i == 0:
                        hb.loc["WHNS"][i] = "0.0001"
                    else:
                        hb.loc["WHNS"][i] = hb.loc["WHNS"][i-1]

        return hb.reindex(METRICS_ORDER)

    def preroute_stg_profiler(self, log, script=None):
        hb_stg = pd.DataFrame(index=METRICS_ORDER)
        stg_prev = 0
        hb = self.preroute_profiler(log)
        step_list = list(hb.columns)
        if len(step_list) == 0: return hb_stg
        #print step_list
        hb_stg['initial'] = hb[step_list[0]]
        for step_name in step_list:
            match = re.search(r'\(\d+P(\d)\)', step_name)
            if match:
                stg = match.group(1)
                if stg_prev == 0:
                    stg_prev = stg
                if stg != stg_prev:
                    #print stg
                    hb_stg[STAGE_LIST[int(stg_prev)-1]] = hb[prev_step]
                    #print hb[step_name]
                stg_prev = stg
                prev_step = step_name
        #if len(step_list) > 0:
        hb_stg['final_opto'] = hb[step_list[-1]]
        return hb_stg

    def user_profiler(self, log, script):        
        f = os.popen(script + ' ' + log)
        heart_beat_raw = f.readlines()
        index_list = heart_beat_raw[0].split()
        hb = pd.DataFrame(index=index_list)
        i = 0
        for line in heart_beat_raw[1:]:
            step = line.strip('\n').split()
            if len(step) == len(index_list):
                hb['step'+str(i)] = step
            elif len(step) == len(index_list) + 1:
                step_name = '('+str(i)+')'+step[0]
                hb[step_name] = step[1:]
            else:
                print "abnormal heartbeat line: %s" %line
            i += 1
        return hb 

if __name__ == "__main__":
    import argparse
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-logs', nargs='+', required=True, help='Log files to be profiled.')       
        parser.add_argument('-pattern', required=True, choices=['preroute', 'preroute_stg', 'ropt', 'gropt', 'npo', 'user'], help='Extract log with given pattern.')
        parser.add_argument('-compress', action="store_true", help='Compress consecutive same steps')
        parser.add_argument('-script', help='User script to extract pattern in log.')
        args = parser.parse_args()
        qp = QorProfiler(args.logs, args.compress)

        for log in args.logs:
            if args.pattern == 'preroute':
                output = qp.preroute_profiler(log)
            elif args.pattern == 'preroute_stg':
                output = qp.preroute_stg_profiler(log)
            elif args.pattern == 'ropt':
                output = qp.ropt_profiler(log)
            elif args.pattern == 'gropt':
                output = qp.gropt_profiler(log)
            elif args.pattern == 'npo':
                output = qp.npo_profiler(log)
            elif args.pattern == 'user':
                if args.script is None:
                    print "Please provide csh script using '-script' to extract pattern."
                    exit()

                script = args.script
                if not os.path.exists(script):
                    if not os.path.exists(os.getcwd() + "/" + script):
                        print "Cannot find script: %s." %script
                        exit()
                output = qp.user_profiler(log, script)

            if output.empty:
                print "No pattern found in %s." %log    
            else:
                print tabulate(output.T, headers='keys', tablefmt='psql')                   

    except OSError as e:
        import traceback
        traceback.print_exc()
        print "I/O error({0}): {1} {2}".format(e.errno, e.strerror, e.filename)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print e

