#!/remote/us01home40/phyan/depot/Python-2.7.11/bin/python
import sys 
import os
import commands
import re
import copy
import stat
import getpass
import gzip

from collections import defaultdict
from record_usage import *

import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
from tabulate import tabulate

METRICS_ORDER_1 = ["Line", "ELAPSE_TIME", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM"]
METRICS_ORDER_2 = ["Line", "ELAPSE_TIME", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM", "LEAKPWR"]
METRICS_ORDER_3 = ["Line", "ELAPSE_TIME", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM", "WHNS"]
METRICS_ORDER_4 = ["Line", "ELAPSE_TIME", "WNS", "TNS", "AREA", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "MEM",  "LEAKPWR", "WHNS"]
METRICS_ORDER = ["Line", "WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "AREA",  "MEM", "ELAPSE_TIME", "LVTCNT", "LVTPCNT", "LEAKPWR", "WHNS"]
METRICS_ORDER_QOR = ["Line", "TNS", "LDRC", "AREA", "LEAKAGE", "ELAPSE"]
METRICS_ORDER_ROPT = ["Line", "RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"]
METRICS_ORDER_DF_ROPT = ["Line", "SETUP_COST","HOLD_COST","LDRC_COST","AREA","LEAKAGE","ELAPSE"]
METRICS_ORDER_GROPT = METRICS_ORDER_ROPT
METRICS_ORDER_DF_GROPT = METRICS_ORDER_DF_ROPT
METRICS_ORDER_NPO = METRICS_ORDER_ROPT
METRICS_ORDER_DF_NPO = METRICS_ORDER_DF_ROPT
METRICS_ORDER_FULL_FLOW_PPA = ["FREQUENCY_GHz", "WNS", "AREA", "LEAKAGE", "DYNAMIC", "ELAPSE", "MEM"]
METRICS_ORDER_FUNC_DIST = ['ELAPSE', 'MEM_PEAK']
METRICS_ORDER_ELAPSE_MEM = METRICS_ORDER_FUNC_DIST

FULL_FLOW_PPA_RPT_LIST = ['dcrpt','nwprpt','nwcrpt','nwrrpt','nwrpt']
FULL_FLOW_PPA_LOG_LIST = ['dcopt','nwpopt','nwcopt','nwropt','nwfopt']
FULL_FLOW_PPA_NAME_MAP = {'dcrpt':'DC/DCRT','nwprpt':'place_opt','nwcrpt':'clock_opt','nwrrpt':'route','nwrpt':'route_opt'}

POPT_STAGE_LIST = ['initial_place', 'initial_drc','initial_opto','final_place','final_opto']
RFOPT_STAGE_LIST = ['initial_path_opt', 'incr_opto', 'incr_place', 'final_path_opt']
COPT_STAGE_LIST = ['cts','cto','final_opto']
ROPT_STAGE_LIST = ['ropt']
GRFO_STAGE_LIST = ['grfo']

CALC = [3600, 60, 1]
# core command definition
COPT_PATTERN = "Perform clock synthesis and placement+optimization (clock_opt) flow"
POPT_PATTERN = "Perform placement and circuit optimization (place_opt) on design"
REFINE_PATTERN = "Perform placement and circuit optimization (refine_opt) on design"
# place_opt stage definition
INIT_PLACE = "Running initial placement"
HFSDRC = "Running initial HFS and DRC step"
INIT_OPTO = "Running initial optimization step"
FINAL_PLACE = "Running final (timing-driven) placement step"
FINAL_OPTO = "Running final optimization step"

SKIP_INIT_PLACE = "Skipping initial placement"
SKIP_HFSDRC = "Skipping initial HFS and DRC step"
SKIP_INIT_OPTO = "Skipping initial optimization step"
SKIP_FINAL_PLACE = "Skipping final (timing-driven) placement step"
SKIP_FINAL_OPTO = "Skipping final optimization step"
# refine_opt stahe definition
INIT_PATH_OPT = "Running initial path_opt step"
INC_PLACE = "Running incremental (timing-driven) placement step"
INC_OPTO = "Running incremental optimization step"
FINAL_PATH_OPT = "Running final path_opt step"

SKIP_INIT_PATH_OPT = "Skipping initial path_opt step"
SKIP_INC_PLACE = "Skipping incremental (timing-driven) placement step"
SKIP_INC_OPTO = "Skipping incremental optimization step"
SKIP_FINAL_PATH_OPT = "Skipping final path_opt step"
# clock_opt stage definition
CTO = "Running post-clock optimization step"
CTS = "Running clock synthesis step"

class QorProfiler():
    def __init__(self, input_list=None, compress=True, pattern="all", script_list=None, dump_csv=False):
        self._profiler = {
                            "APS": self.aps_profiler, "QOR_STG": self.qor_stg_profiler, "QOR": self.qor_profiler,
                            "ROPT": self.ropt_profiler, "DF_ROPT": self.df_ropt_profiler, "GROPT":   self.gropt_profiler, "DF_GROPT":   self.df_gropt_profiler, 
                            "NPO_POPT":   self.npo_popt_profiler, "DF_NPO_POPT":   self.df_npo_popt_profiler, "NPO_COPT":   self.npo_copt_profiler, "DF_NPO_COPT":   self.df_npo_copt_profiler,  
                            "FULL_FLOW_PPA": self.full_flow_ppa_profiler,
                            "FUNC_DIST": self.func_dist_profiler, 
                            # "ELAPSE_MEM": self.elapse_mem_profiler,
                        }
        self._profiler_clear = ['APS', 'ROPT', 'DF_ROPT', 'GROPT', 'DF_GROPT', 'NPO_POPT', 'NPO_COPT', 'DF_NPO_POPT', 'DF_NPO_COPT']
        self._profiler_script = {}
        for p in self._profiler.keys():
            self._profiler_script[p] = None

        self.matched_pattern = []
        self.auto_skip_dict = defaultdict(list)
        self.step_match_dict = defaultdict(list)
        self.qor_metrics_dict = defaultdict(list)
        self.step_qor_dict = defaultdict(list)
        self.steps_dict = defaultdict(list)
        self.metrics_order = defaultdict(list)
        self.input_list = input_list
        self.compress = compress
        self.pattern = pattern
        self.script_list = script_list
        self.dump_csv = dump_csv
        self.qor_hb = {}
        self.qor_stg_hb = {}
        self.qor_generated = []
        self.empty_profile = []
        for log in input_list:
            self.qor_hb[log] = pd.DataFrame(index=METRICS_ORDER_QOR)
            self.qor_stg_hb[log] = pd.DataFrame(index=METRICS_ORDER_QOR)

    def generate_profile(self): #hb to json metrics
        _profiler = copy.copy(self._profiler)
        _profiler_script = copy.copy(self._profiler_script)
        # print self.pattern
        if self.pattern == "FULL_FLOW":
            _profiler = {"FULL_FLOW_PPA": self._profiler["FULL_FLOW_PPA"], "FUNC_DIST": self._profiler["FUNC_DIST"]}
            _profiler_script = {"FULL_FLOW_PPA": self._profiler_script["FULL_FLOW_PPA"],"FUNC_DIST": self._profiler_script["FUNC_DIST"]}
        elif self.pattern != 'all' and self.pattern != 'USER': #specific pattern
            _profiler = {self.pattern: self._profiler[self.pattern]}
            _profiler_script = {self.pattern: self._profiler_script[self.pattern]}
        elif self.pattern == "USER": #user pattern
            i = 1
            for script in self.script_list:
                _profiler['USER'+str(i)] = self.user_profiler
                _profiler_script['USER'+str(i)] = script
                i += 1
        else: #all
            del(_profiler["FULL_FLOW_PPA"])
            del(_profiler_script["FULL_FLOW_PPA"])
            del(_profiler["FUNC_DIST"])
            del(_profiler_script["FUNC_DIST"])


        # prepare dataframe for each pattern
        for pattern_name, profiler in _profiler.items():
            if pattern_name == "QOR" or pattern_name == "QOR_STG": continue
            script = _profiler_script[pattern_name]
            self.qor_metrics_dict[pattern_name], self.step_qor_dict[pattern_name], \
            self.auto_skip_dict[pattern_name], self.step_match_dict[pattern_name], self.steps_dict[pattern_name], self.metrics_order[pattern_name]  = self._pattern_to_metrics(profiler, script)

        # handle qor, qor_stg pattern at last
        if _profiler.has_key("QOR"):
            pattern_name = "QOR"
            profiler = _profiler["QOR"]
            script = _profiler_script[pattern_name]
            self.qor_metrics_dict[pattern_name], self.step_qor_dict[pattern_name], \
            self.auto_skip_dict[pattern_name], self.step_match_dict[pattern_name], self.steps_dict[pattern_name], self.metrics_order[pattern_name]  = self._pattern_to_metrics(profiler, script)   

        if _profiler.has_key("QOR_STG"):
            pattern_name = "QOR_STG"
            profiler = _profiler["QOR_STG"]
            script = _profiler_script[pattern_name]
            self.qor_metrics_dict[pattern_name], self.step_qor_dict[pattern_name], \
            self.auto_skip_dict[pattern_name], self.step_match_dict[pattern_name], self.steps_dict[pattern_name], self.metrics_order[pattern_name]  = self._pattern_to_metrics(profiler, script) 

        # drop empty pattern    
        for pattern, qor_metrics in self.qor_metrics_dict.items():
            empty_pattern = True
            for metrics in qor_metrics:
                if not pd.DataFrame.from_dict(metrics).empty:
                    empty_pattern = False
            if empty_pattern:
               del(self.qor_metrics_dict[pattern])

        # simplify final patterns to show
        for pattern in self._profiler_clear:
            if self.qor_metrics_dict.has_key(pattern):
                del(self.qor_metrics_dict[pattern])

    def _pattern_to_metrics(self, profiler, script):
        qor_metrics_list = []
        step_qor_list = []
        steps_list = []
        auto_skip_list = []
        step_length_flag = False

        for input in self.input_list:
            auto_skip = "false"
            step_match = 1
            pattern_name = profiler.__name__[:-9]

            if self.compress:
                qp_suffix = '.compress.qp'
            else: 
                qp_suffix = '.non_compress.qp'

            if os.path.isdir(input):
                dir_path = input
                log_name = dir_path.split('/')[-1]
            else:
                dir_path = os.path.dirname(os.path.abspath(input))
                log_name = os.path.basename(os.path.abspath(input))
            #pattern_name = str(sys._getframe().f_code.co_name)[:-9]
            #print input, pattern_name
            qp_file = dir_path+'/qor_profile/'+log_name+'.'+pattern_name+qp_suffix           

            if os.path.exists(qp_file):
                # print "Found existing qp file %s, load it" %qp_file               
                try:
                    hb = pd.read_csv(qp_file,index_col=0,parse_dates=True,dtype=str)
                except Exception as e:
                    hb = pd.DataFrame()
            else:
                # print "Not found existing %s qp file under %s, do extraction" %(input, dir_path)
                if self.dump_csv:
                    dir_tmp = os.getcwd()
                    # print "Dump %s file now to %s" %(log_name, dir_tmp)
                    if os.access(dir_path,os.W_OK):
                        os.chdir(dir_path)
                        if not os.path.exists('qor_profile'):
                            try:             
                                os.makedirs("qor_profile") 
                                os.system('chmod -R 777 qor_profile')
                            except Exception as e:
                                if e.errno == 17:
                                    pass

                        hb = profiler(input, script)                               
                        hb.to_csv(qp_file,float_format='%g')      
                        os.chmod("%s" %qp_file, stat.S_IRWXU+stat.S_IRWXG+stat.S_IRWXO)               
                    else: # no permission skip extraction
                        hb = profiler('/u/phyan/workspace/python/qor_analyzer/script/log_dummy', script)                
                else:
                    hb = profiler(input, script)    


            if hb.empty:
                continue

            if pattern_name != "qor":
                #special handling
                hb.fillna("-",inplace=True)
                # hb.fillna("~",inplace=True)
                hb = hb.replace(to_replace='0', value="0.0001").replace(to_replace=0, value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
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
            else:
                self.qor_hb[input] = hb

        if pattern_name == "qor":
            for log in self.input_list:
                hb = self.qor_hb[log]
                # print hb
                if hb.empty:
                    del(self.qor_hb[log])
                    self.empty_profile.append(log)
                    continue

                hb = hb.reindex(METRICS_ORDER_QOR)
                #special handling
                hb.fillna("0.0001",inplace=True)
                # hb.fillna("~",inplace=True)
                hb = hb.replace(to_replace='0', value="0.0001").replace(to_replace=0, value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
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
        line_num = 0
        suffix = 1 #By default, qor calculation start from initial_drc
        cmd = "PL" #By default, treat cmd as place_opt
        f = open(log).readlines()
        for line in f:
            #decide core cmd
            if COPT_PATTERN in line:
                cmd = "CL"
                suffix = 1
            elif POPT_PATTERN in line:
                cmd = "PL"
                suffix = 1
            elif REFINE_PATTERN in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: place_opt" in line:
                cmd = "PL"
                suffix = 1
            elif "START_CMD: refine_opt" in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: clock_opt" in line:
                cmd = "CL"
                suffix = 1                
            ## decide stages
            #  find stage
            if INIT_PLACE in line:
                suffix = 1
            elif HFSDRC in line:
                suffix = 2
            elif INIT_OPTO in line:
                suffix = 3
            elif FINAL_PLACE in line:
                suffix = 4
            elif FINAL_OPTO in line:
                if cmd == "PL":
                    suffix = 5
                elif cmd == "CL":
                    suffix = 3
            elif INIT_PATH_OPT in line:
                suffix = 1
            elif INC_PLACE in line:
                suffix = 2
            elif INC_OPTO in line:
                suffix = 3
            elif FINAL_PATH_OPT in line:
                suffix = 4
            elif CTO in line:
                suffix = 2
            elif CTS in line:
                cmd = "CL"
                suffix = 1

            # skip stage
            if "Skipping initial placement" in line:
                suffix = 0 # 0 stands for pending status
            elif "Skipping initial" in line or "Skipping final" in line:
                suffix += 1

            if not "Global-route-opt optimization" in line or "Global-route-opt optimization summary" in line >= 0: continue
            hb_list = line.split()
            hb_list.insert(-10, line_num)
            #add wa to skip non-debug ropt log
            if len(hb_list) < 14:
                return hb
            cmd = "RT"
            crnt_step = hb_list[2]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-11:]
            else:
                # step = "("+str(step_num)+cmd+")"+hb_list[2]    
                step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step            
                hb[step] = hb_list[-11:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step
        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)

        hb = hb.replace(to_replace="-", value=np.nan)
        hb_tmp = hb.T[['Line', 'SETUP_COST', 'LDRC_COST', 'AREA', 'LEAKAGE', 'ELAPSE']].T
        hb_tmp.index = ['Line', 'TNS', 'LDRC', 'AREA', 'LEAKAGE', 'ELAPSE']
        self.qor_hb[log] = pd.concat([self.qor_hb[log], hb_tmp], axis=1)
        return hb

    def df_gropt_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_DF_GROPT)
        step_num = 0
        prev_step = ""
        line_num = 0
        suffix = 1 #By default, qor calculation start from initial_drc
        cmd = "PL" #By default, treat cmd as place_opt
        f = open(log).readlines()
        for line in f:
            line_num += 1
            #decide core cmd
            if COPT_PATTERN in line:
                cmd = "CL"
                suffix = 1
            elif POPT_PATTERN in line:
                cmd = "PL"
                suffix = 1
            elif REFINE_PATTERN in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: place_opt" in line:
                cmd = "PL"
                suffix = 1
            elif "START_CMD: refine_opt" in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: clock_opt" in line:
                cmd = "CL"
                suffix = 1                
            ## decide stages
            #  find stage
            if INIT_PLACE in line:
                suffix = 1
            elif HFSDRC in line:
                suffix = 2
            elif INIT_OPTO in line:
                suffix = 3
            elif FINAL_PLACE in line:
                suffix = 4
            elif FINAL_OPTO in line:
                if cmd == "PL":
                    suffix = 5
                elif cmd == "CL":
                    suffix = 3
            elif INIT_PATH_OPT in line:
                suffix = 1
            elif INC_PLACE in line:
                suffix = 2
            elif INC_OPTO in line:
                suffix = 3
            elif FINAL_PATH_OPT in line:
                suffix = 4
            elif CTO in line:
                suffix = 2
            elif CTS in line:
                cmd = "CL"
                suffix = 1

            # skip stage
            if "Skipping initial placement" in line:
                suffix = 0 # 0 stands for pending status
            elif "Skipping initial" in line or "Skipping final" in line:
                suffix += 1

            if not "Global-route-opt optimization" in line or "Global-route-opt optimization summary" in line >= 0: continue
            hb_list = line.split()
            hb_list.insert(-6, line_num)
            #add wa to skip non-debug ropt log
            if len(hb_list) >= 14:
                return hb
            cmd = "GF"
            suffix = 1
            if hb_list[2] == 'complete':
                crnt_step = hb_list[2]
            else:
                crnt_step = hb_list[2] + hb_list[3] + hb_list[4] + hb_list[5]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-7:]
            else:
                # step = "("+str(step_num)+cmd+")"+crnt_step  
                step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step            
                hb[step] = hb_list[-7:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step

        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)
        hb = hb.replace(to_replace="-", value=np.nan)
        hb_tmp = hb.T[['Line', 'SETUP_COST', 'LDRC_COST', 'AREA', 'LEAKAGE', 'ELAPSE']].T
        hb_tmp.index = ['Line', 'TNS', 'LDRC', 'AREA', 'LEAKAGE', 'ELAPSE']
        self.qor_hb[log] = pd.concat([self.qor_hb[log], hb_tmp], axis=1)
        return hb    

    def npo_popt_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_NPO)
        step_num = 0
        prev_step = ""
        line_num = 0
        suffix = 1 #By default, qor calculation start from initial_drc
        cmd = "PL" #By default, treat cmd as place_opt
        f = open(log).readlines()
        for line in f:
            line_num += 1
            #decide core cmd
            if COPT_PATTERN in line:
                cmd = "CL"
                suffix = 1
            elif POPT_PATTERN in line:
                cmd = "PL"
                suffix = 1
            elif REFINE_PATTERN in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: place_opt" in line:
                cmd = "PL"
                suffix = 1
            elif "START_CMD: refine_opt" in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: clock_opt" in line:
                cmd = "CL"
                suffix = 1                
            ## decide stages
            #  find stage
            if INIT_PLACE in line:
                suffix = 1
            elif HFSDRC in line:
                suffix = 2
            elif INIT_OPTO in line:
                suffix = 3
            elif FINAL_PLACE in line:
                suffix = 4
            elif FINAL_OPTO in line:
                if cmd == "PL":
                    suffix = 5
                elif cmd == "CL":
                    suffix = 3
            elif INIT_PATH_OPT in line:
                suffix = 1
            elif INC_PLACE in line:
                suffix = 2
            elif INC_OPTO in line:
                suffix = 3
            elif FINAL_PATH_OPT in line:
                suffix = 4
            elif CTO in line:
                suffix = 1

            # skip stage
            if "Skipping initial placement" in line:
                suffix = 0 # 0 stands for pending status
            elif "Skipping initial" in line or "Skipping final" in line:
                suffix += 1

            if not "npo-place-opt optimization" in line or "npo-place-opt optimization summary" in line >= 0: continue
            hb_list = line.split()
            hb_list.insert(-10, line_num)
            #add wa to skip non-debug ropt log
            if len(hb_list) < 14:
                return hb
            cmd = "PL"
            crnt_step = hb_list[2]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-11:]
            else:
                # step = "("+str(step_num)+cmd+")"+hb_list[2]  
                step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step              
                hb[step] = hb_list[-11:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step
                 
        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)

        hb = hb.replace(to_replace="-", value=np.nan)
        hb_tmp = hb.T[['Line', 'SETUP_COST', 'LDRC_COST', 'AREA', 'LEAKAGE', 'ELAPSE']].T
        hb_tmp.index = ['Line', 'TNS', 'LDRC', 'AREA', 'LEAKAGE', 'ELAPSE']
        self.qor_hb[log] = pd.concat([self.qor_hb[log], hb_tmp], axis=1)
        return hb

    def df_npo_popt_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_DF_NPO)
        step_num = 0
        prev_step = ""
        line_num = 0
        suffix = 1 #By default, qor calculation start from initial_drc
        cmd = "PL" #By default, treat cmd as place_opt
        f = open(log).readlines()
        for line in f:
            line_num += 1
            #decide core cmd
            if COPT_PATTERN in line:
                cmd = "CL"
                suffix = 1
            elif POPT_PATTERN in line:
                cmd = "PL"
                suffix = 1
            elif REFINE_PATTERN in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: place_opt" in line:
                cmd = "PL"
                suffix = 1
            elif "START_CMD: refine_opt" in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: clock_opt" in line:
                cmd = "CL"
                suffix = 1                
            ## decide stages
            #  find stage
            if INIT_PLACE in line:
                suffix = 1
            elif HFSDRC in line:
                suffix = 2
            elif INIT_OPTO in line:
                suffix = 3
            elif FINAL_PLACE in line:
                suffix = 4
            elif FINAL_OPTO in line:
                if cmd == "PL":
                    suffix = 5
                elif cmd == "CL":
                    suffix = 3
            elif INIT_PATH_OPT in line:
                suffix = 1
            elif INC_PLACE in line:
                suffix = 2
            elif INC_OPTO in line:
                suffix = 3
            elif FINAL_PATH_OPT in line:
                suffix = 4
            elif CTO in line:
                suffix = 1

            # skip stage
            if "Skipping initial placement" in line:
                suffix = 0 # 0 stands for pending status
            elif "Skipping initial" in line or "Skipping final" in line:
                suffix += 1

            if not "npo-place-opt optimization" in line or "npo-place-opt optimization summary" in line >= 0: continue
            hb_list = line.split()
            hb_list.insert(-6, line_num)
            #add wa to skip non-debug ropt log
            if len(hb_list) >= 14:
                return hb
            cmd = "PL"
            if hb_list[2] == 'complete':
                crnt_step = hb_list[2]
            else:
                crnt_step = hb_list[2] + hb_list[3] + hb_list[4] + hb_list[5]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-7:]
            else:
                # step = "("+str(step_num)+cmd+")"+crnt_step      
                step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step       
                hb[step] = hb_list[-7:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step

        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)
        hb = hb.replace(to_replace="-", value=np.nan)
        hb_tmp = hb.T[['Line', 'SETUP_COST', 'LDRC_COST', 'AREA', 'LEAKAGE', 'ELAPSE']].T
        hb_tmp.index = ['Line', 'TNS', 'LDRC', 'AREA', 'LEAKAGE', 'ELAPSE']
        self.qor_hb[log] = pd.concat([self.qor_hb[log], hb_tmp], axis=1)
        return hb

    def npo_copt_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_NPO)
        step_num = 0
        prev_step = ""
        line_num = 0
        suffix = 1 #By default, qor calculation start from initial_drc
        cmd = "PL" #By default, treat cmd as place_opt
        f = open(log).readlines()
        for line in f:
            line_num += 1
            #decide core cmd
            if COPT_PATTERN in line:
                cmd = "CL"
                suffix = 1
            elif POPT_PATTERN in line:
                cmd = "PL"
                suffix = 1
            elif REFINE_PATTERN in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: place_opt" in line:
                cmd = "PL"
                suffix = 1
            elif "START_CMD: refine_opt" in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: clock_opt" in line:
                cmd = "CL"
                suffix = 1                
            ## decide stages
            #  find stage
            if INIT_PLACE in line:
                suffix = 1
            elif HFSDRC in line:
                suffix = 2
            elif INIT_OPTO in line:
                suffix = 3
            elif FINAL_PLACE in line:
                suffix = 4
            elif FINAL_OPTO in line:
                if cmd == "PL":
                    suffix = 5
                elif cmd == "CL":
                    suffix = 3
            elif INIT_PATH_OPT in line:
                suffix = 1
            elif INC_PLACE in line:
                suffix = 2
            elif INC_OPTO in line:
                suffix = 3
            elif FINAL_PATH_OPT in line:
                suffix = 4
            elif CTO in line:
                suffix = 2
            elif CTS in line:
                cmd = "CL"
                suffix = 1

            # skip stage
            if "Skipping initial placement" in line:
                suffix = 0 # 0 stands for pending status
            elif "Skipping initial" in line or "Skipping final" in line:
                suffix += 1

            if not "npo-clock-opt optimization" in line or "npo-clock-opt optimization summary" in line >= 0: continue
            hb_list = line.split()
            hb_list.insert(-10, line_num)
            #add wa to skip non-debug ropt log
            if len(hb_list) < 14:
                return hb
            cmd = "CL"
            crnt_step = hb_list[2]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-11:]
            else:
                # step = "("+str(step_num)+cmd+")"+hb_list[2]    
                step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step            
                hb[step] = hb_list[-11:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step

        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)

        hb = hb.replace(to_replace="-", value=np.nan)
        hb_tmp = hb.T[['Line', 'SETUP_COST', 'LDRC_COST', 'AREA', 'LEAKAGE', 'ELAPSE']].T
        hb_tmp.index = ['Line', 'TNS', 'LDRC', 'AREA', 'LEAKAGE', 'ELAPSE']
        self.qor_hb[log] = pd.concat([self.qor_hb[log], hb_tmp], axis=1)
        return hb

    def df_npo_copt_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_DF_NPO)
        step_num = 0
        prev_step = ""
        line_num = 0
        suffix = 1 #By default, qor calculation start from initial_drc
        cmd = "PL" #By default, treat cmd as place_opt
        f = open(log).readlines()
        for line in f:
            line_num += 1
            #decide core cmd
            if COPT_PATTERN in line:
                cmd = "CL"
                suffix = 1
            elif POPT_PATTERN in line:
                cmd = "PL"
                suffix = 1
            elif REFINE_PATTERN in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: place_opt" in line:
                cmd = "PL"
                suffix = 1
            elif "START_CMD: refine_opt" in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: clock_opt" in line:
                cmd = "CL"
                suffix = 1                
            ## decide stages
            #  find stage
            if INIT_PLACE in line:
                suffix = 1
            elif HFSDRC in line:
                suffix = 2
            elif INIT_OPTO in line:
                suffix = 3
            elif FINAL_PLACE in line:
                suffix = 4
            elif FINAL_OPTO in line:
                if cmd == "PL":
                    suffix = 5
                elif cmd == "CL":
                    suffix = 3
            elif INIT_PATH_OPT in line:
                suffix = 1
            elif INC_PLACE in line:
                suffix = 2
            elif INC_OPTO in line:
                suffix = 3
            elif FINAL_PATH_OPT in line:
                suffix = 4
            elif CTO in line:
                suffix = 2
            elif CTS in line:
                cmd = "CL"
                suffix = 1

            # skip stage
            if "Skipping initial placement" in line:
                suffix = 0 # 0 stands for pending status
            elif "Skipping initial" in line or "Skipping final" in line:
                suffix += 1

            if not "npo-clock-opt optimization" in line or "npo-clock-opt optimization summary" in line >= 0: continue
            hb_list = line.split()
            hb_list.insert(-6, line_num)
            #add wa to skip non-debug ropt log
            if len(hb_list) >= 14:
                return hb
            cmd = "CL"
            if hb_list[2] == 'complete':
                crnt_step = hb_list[2]
            else:
                crnt_step = hb_list[2] + hb_list[3] + hb_list[4] + hb_list[5]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-7:]
            else:
                # step = "("+str(step_num)+cmd+")"+crnt_step  
                step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step            
                hb[step] = hb_list[-7:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step

        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)
        hb = hb.replace(to_replace="-", value=np.nan)
        hb_tmp = hb.T[['Line', 'SETUP_COST', 'LDRC_COST', 'AREA', 'LEAKAGE', 'ELAPSE']].T
        hb_tmp.index = ['Line', 'TNS', 'LDRC', 'AREA', 'LEAKAGE', 'ELAPSE']
        self.qor_hb[log] = pd.concat([self.qor_hb[log], hb_tmp], axis=1)
        return hb   

    def ropt_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_ROPT)
        step_num = 0
        prev_step = ""
        line_num = 0
        suffix = 1 #By default, qor calculation start from initial_drc
        cmd = "RT" #By default, treat cmd as place_opt
        f = open(log).readlines()
        for line in f:
            line_num += 1
                        #decide core cmd
            if COPT_PATTERN in line:
                cmd = "CL"
                suffix = 1
            elif POPT_PATTERN in line:
                cmd = "PL"
                suffix = 1
            elif REFINE_PATTERN in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: place_opt" in line:
                cmd = "PL"
                suffix = 1
            elif "START_CMD: refine_opt" in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: clock_opt" in line:
                cmd = "CL"
                suffix = 1                
            ## decide stages
            #  find stage
            if INIT_PLACE in line:
                suffix = 1
            elif HFSDRC in line:
                suffix = 2
            elif INIT_OPTO in line:
                suffix = 3
            elif FINAL_PLACE in line:
                suffix = 4
            elif FINAL_OPTO in line:
                if cmd == "PL":
                    suffix = 5
                elif cmd == "CL":
                    suffix = 3
            elif INIT_PATH_OPT in line:
                suffix = 1
            elif INC_PLACE in line:
                suffix = 2
            elif INC_OPTO in line:
                suffix = 3
            elif FINAL_PATH_OPT in line:
                suffix = 4
            elif CTO in line:
                suffix = 2
            elif CTS in line:
                cmd = "CL"
                suffix = 1

            # skip stage
            if "Skipping initial placement" in line:
                suffix = 0 # 0 stands for pending status
            elif "Skipping initial" in line or "Skipping final" in line:
                suffix += 1

            if not "Route-opt optimization" in line or "Route-opt optimization summary" in line: continue
            hb_list = line.split()
            hb_list.insert(-10, line_num)
            #add wa to skip non-debug ropt log
            if len(hb_list) < 14:
                return hb
            cmd = "RT"
            suffix = 1
            crnt_step = hb_list[2]
            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-11:]
            else:
                # step = "("+str(step_num)+cmd+")"+hb_list[2]    
                step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step             
                hb[step] = hb_list[-11:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step

        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)

        hb = hb.replace(to_replace="-", value=np.nan)
        hb_tmp = hb.T[['Line', 'SETUP_COST', 'LDRC_COST', 'AREA', 'LEAKAGE', 'ELAPSE']].T
        hb_tmp.index = ['Line', 'TNS', 'LDRC', 'AREA', 'LEAKAGE', 'ELAPSE']
        self.qor_hb[log] = pd.concat([self.qor_hb[log], hb_tmp], axis=1)
        return hb

    def df_ropt_profiler(self, log, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_DF_ROPT)
        step_num = 0
        prev_step = ""
        line_num = 0
        suffix = 1 #By default, qor calculation start from initial_drc
        cmd = "RT" #By default, treat cmd as place_opt
        f = open(log).readlines()
        for line in f:
            line_num += 1
                                    #decide core cmd
            if COPT_PATTERN in line:
                cmd = "CL"
                suffix = 1
            elif POPT_PATTERN in line:
                cmd = "PL"
                suffix = 1
            elif REFINE_PATTERN in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: place_opt" in line:
                cmd = "PL"
                suffix = 1
            elif "START_CMD: refine_opt" in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: clock_opt" in line:
                cmd = "CL"
                suffix = 1                
            ## decide stages
            #  find stage
            if INIT_PLACE in line:
                suffix = 1
            elif HFSDRC in line:
                suffix = 2
            elif INIT_OPTO in line:
                suffix = 3
            elif FINAL_PLACE in line:
                suffix = 4
            elif FINAL_OPTO in line:
                if cmd == "PL":
                    suffix = 5
                elif cmd == "CL":
                    suffix = 3
            elif INIT_PATH_OPT in line:
                suffix = 1
            elif INC_PLACE in line:
                suffix = 2
            elif INC_OPTO in line:
                suffix = 3
            elif FINAL_PATH_OPT in line:
                suffix = 4
            elif CTO in line:
                suffix = 2
            elif CTS in line:
                cmd = "CL"
                suffix = 1

            # skip stage
            if "Skipping initial placement" in line:
                suffix = 0 # 0 stands for pending status
            elif "Skipping initial" in line or "Skipping final" in line:
                suffix += 1

            if not "Route-opt optimization" in line or "Route-opt optimization summary" in line: continue
            hb_list = line.split()
            hb_list.insert(-6, line_num)
            #add wa to skip non-debug ropt log
            if len(hb_list) >= 14:
                return hb
            cmd = "RT"
            suffix = 1
            if hb_list[2] == 'complete':
                crnt_step = hb_list[2]
            else:
                crnt_step = hb_list[2] + hb_list[3] + hb_list[4] + hb_list[5]

            if self.compress and prev_step == crnt_step:
                hb[prev_step_hb] = hb_list[-7:]
            else:
                # step = "("+str(step_num)+cmd+")"+crnt_step   
                step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step             
                hb[step] = hb_list[-7:]
                step_num += 1
                prev_step_hb = step
                prev_step = crnt_step

        #hb = hb.replace(to_replace="0", value="0.0001").replace(to_replace="0\.0+$", value="0.0001", regex=True)
        for i in range(len(hb.loc["ELAPSE"])):
            hb.loc["ELAPSE"][i] = '{:.2f}'.format(float(hb.loc["ELAPSE"][i]) * 3600)
        hb = hb.replace(to_replace="-", value=np.nan)
        hb_tmp = hb.T[['Line', 'SETUP_COST', 'LDRC_COST', 'AREA', 'LEAKAGE', 'ELAPSE']].T
        hb_tmp.index = ['Line', 'TNS', 'LDRC', 'AREA', 'LEAKAGE', 'ELAPSE']
        self.qor_hb[log] = pd.concat([self.qor_hb[log], hb_tmp], axis=1)
        return hb   

    def aps_profiler(self, log, script=None):
        """
        pattern_name = str(sys._getframe().f_code.co_name)[:-9]
        # print pattern_name
        if self.compress:
            qp_file = './qor_profile/'+log+'.'+pattern_name+'.compress.qp'
        else:
            qp_file = './qor_profile/'+log+'.'+pattern_name+'.non_compress.qp'
        if os.path.exists(qp_file):
            # print "Found existing hb file, load it"
            hb = pd.read_csv(qp_file,index_col=0,parse_dates=True, dtype=str)
            # print hb
            return hb
        """
        hb = pd.DataFrame(index=METRICS_ORDER_4)
        first = n = flag = 0
        step_num = 0
        prev_step = ""
        func_name = 'init'
        suffix = 1 #By default, qor calculation start from initial_drc
        suffix_pre = 1
        line_num = 0
        cmd = "PL" #By default, treat cmd as place_opt

        f = open(log).readlines()
        for line in f:
            line_num += 1
            #decide core cmd
            if COPT_PATTERN in line:
                cmd = "CL"
                suffix = 1
            elif POPT_PATTERN in line:
                cmd = "PL"
                suffix = 1
            elif REFINE_PATTERN in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: place_opt" in line:
                cmd = "PL"
                suffix = 1
            elif "START_CMD: refine_opt" in line:
                cmd = "RF"
                suffix = 1
            elif "START_CMD: clock_opt" in line:
                cmd = "CL"
                suffix = 1                
            ## decide stages
            #  find stage
            if INIT_PLACE in line:
                suffix = 1
            elif HFSDRC in line:
                suffix = 2
            elif INIT_OPTO in line:
                suffix = 3
            elif FINAL_PLACE in line:
                suffix = 4
            elif FINAL_OPTO in line:
                if cmd == "PL":
                    suffix = 5
                elif cmd == "CL":
                    suffix = 3
            elif INIT_PATH_OPT in line:
                suffix = 1
            elif INC_PLACE in line:
                suffix = 2
            elif INC_OPTO in line:
                suffix = 3
            elif FINAL_PATH_OPT in line:
                suffix = 4
            elif CTO in line:
                suffix = 2
            elif CTS in line:
                cmd = "CL"
                suffix = 1

            # skip stage
            if "Skipping initial placement" in line:
                suffix = 0 # 0 stands for pending status
            elif "Skipping initial" in line or "Skipping final" in line:
                suffix += 1

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
            
            match = re.search("START_FUNC:\s+(.*)\s+CPU", line)
            if match:
                func_name = match.group(1)

            if flag:
                n += 1
                if n == 4:
                    n = flag = 0 
                    hb_list = line.split()
                    if len(hb_list[1:]) == len(hb_col.index) - 1:
                        hb_list.insert(1, line_num)
                        crnt_step = hb_list[0]
                        if self.compress and crnt_step == prev_step:
                            hb_col[prev_step_hb] = hb_list[1:]
                            hb[prev_step_hb] = hb_col[prev_step_hb]
                        else:
                            step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step
                            hb_col[step] = hb_list[1:]
                            hb = pd.concat([hb, hb_col[step]], axis=1)
                            if prev_step == "START":
                                hb.rename(columns={prev_step_hb: "("+str(step_num-1)+cmd+str(suffix)+")"+prev_step}, inplace=True)
                            prev_step = crnt_step
                            prev_step_hb = step
                            step_num += 1                                      
                    elif len(hb_list) == len(hb_col.index) - 1:
                        hb_list.insert(0, line_num)
                        crnt_step = func_name
                        if self.compress and crnt_step == prev_step and suffix == suffix_pre:
                            hb_col[prev_step_hb] = hb_list
                            hb[prev_step_hb] = hb_col[prev_step_hb]
                        else:                                          
                            if suffix_pre == 0:
                                hb.rename(columns={prev_step_hb: "("+str(step_num-1)+cmd+str(suffix)+")"+prev_step}, inplace=True)    
                            step = "("+str(step_num)+cmd+str(suffix)+")"+crnt_step
                            hb_col[step] = hb_list
                            hb = pd.concat([hb, hb_col[step]], axis=1)
                            prev_step = crnt_step
                            prev_step_hb = step
                            step_num += 1
                    else:
                        # print "abnormal heartbeat line: %s" %line
                        continue   

                    suffix_pre = suffix

        for i in range(len(hb.loc["ELAPSE_TIME"])):          
            hb.loc["ELAPSE_TIME"][i] = sum([int(hb.loc["ELAPSE_TIME"][i].split(":")[index]) * CALC[index] for index in range(3)])             

        if not hb.loc["WHNS"].isnull().all():
            for i in range(len(hb.loc["WHNS"])):
                if hb.loc["WHNS"][i] is np.nan:
                    if i == 0:
                        hb.loc["WHNS"][i] = "0.0001"
                    else:
                        hb.loc["WHNS"][i] = hb.loc["WHNS"][i-1]

        hb = hb.reindex(METRICS_ORDER)
        hb_tmp = hb.T[['Line', 'TNS', 'AREA', "MAXTRAN", 'MAXCAP', 'LEAKPWR', 'ELAPSE_TIME']]
        hb_tmp['LDRC'] = pd.to_numeric(hb_tmp['MAXTRAN']) + pd.to_numeric(hb_tmp['MAXCAP'])
        hb_tmp['LDRC'] = hb_tmp['LDRC'].apply('{:.3f}'.format)
        hb_tmp = hb_tmp[['Line', 'TNS', 'LDRC', 'AREA', 'LEAKPWR', 'ELAPSE_TIME']].T
        hb_tmp.index = ['Line', 'TNS', 'LDRC', 'AREA', 'LEAKAGE', 'ELAPSE']
        self.qor_hb[log] = pd.concat([self.qor_hb[log], hb_tmp], axis=1)
        """
        if self.dump_csv:
            try:
                os.makedirs("qor_profiler")
            except:
                pass
            hb.to_csv('./qor_profiler/'+qp_file,float_format='%g')
        """
        return hb

    def qor_stg_profiler(self, log, script=None):

        if not log in self.qor_generated and not log in self.empty_profile:
            self.qor_profiler(log, script)

        return self.qor_stg_hb[log]

    # def qor_stg_profiler_bk(self, log, script=None):

    #     index = 0
    #     hb_stg = pd.DataFrame(index=METRICS_ORDER)
    #     stg_prev = 0
    #     hb = self.aps_profiler(log)
    #     step_list = list(hb.columns)
    #     if len(step_list) == 0: return hb_stg
    #     hb_stg['('+str(index)+')initial'] = hb[step_list[0]]
    #     index += 1
    #     for step_name in step_list:
    #         match = re.search(r'\(\d+(P|C|RF)(\d)\)', step_name)
    #         if match:               
    #             cmd = match.group(1)
    #             if cmd == 'PL':
    #                 stage_list = POPT_STAGE_LIST
    #             elif cmd == 'CL':
    #                 stage_list = COPT_STAGE_LIST
    #             elif cmd == 'RF':
    #                 stage_list = RFOPT_STAGE_LIST

    #             if stg_prev == 0:
    #                 prev_stage_list = stage_list

    #             stg = match.group(2)
    #             if stg_prev == 0:
    #                 stg_prev = stg
    #             if stg != stg_prev:
    #                 hb_stg['('+str(index)+')'+prev_stage_list[int(stg_prev)-1]] = hb[prev_step]
    #                 index += 1
    #             stg_prev = stg
    #             prev_stage_list = stage_list
    #             prev_step = step_name
                
    #     #if len(step_list) > 0:
    #     hb_stg['('+str(index)+')'+stage_list[int(stg)-1]] = hb[step_list[-1]]

    #     return hb_stg

    def qor_profiler(self, log, script=None):
        self.qor_hb[log] = self.qor_hb[log].T.sort_values('Line').T
        index = 0
        stg_index = 0
        stage_prev = ""
        stage_list = []
        for col in self.qor_hb[log].columns.values:
            match = re.search('(\(\w+\))(.*)\s?', col)
            if match:
                new_step = '('+str(index)+match.group(1)[-4:]+match.group(2)
                stage = match.group(1)[-4:-1]
                cmd = match.group(1)[-4:-2]
                phase = match.group(1)[-2]
                if cmd == 'PL':
                    stage_list = POPT_STAGE_LIST
                elif cmd == 'CL':
                    stage_list = COPT_STAGE_LIST
                elif cmd == 'RF':
                    stage_list = RFOPT_STAGE_LIST
                elif cmd == 'RT':
                    stage_list = ROPT_STAGE_LIST
                elif cmd == "GF":
                    stage_list = GRFO_STAGE_LIST
                
            self.qor_hb[log].columns.values[index] = new_step
            # if new_step == "(79GF1)Phase1Iter1":
            # print self.qor_hb[log].columns.values
            # print self.qor_hb[log][new_step] this will raise issue, dont know why, use iloc instead...
            # print self.qor_hb[log].iloc[:,index]
            if stage_prev != stage:
                if stage_prev == "":
                    prev_stage_list = stage_list
                    self.qor_stg_hb[log]['(0)init'] = self.qor_hb[log].iloc[:,index]
                else:
                    self.qor_stg_hb[log]['('+str(stg_index)+')'+prev_stage_list[int(phase_prev)-1]] = self.qor_hb[log].iloc[:,index-1]
                stg_index += 1
            prev_stage_list = stage_list
            new_step_prev = new_step
            stage_prev = stage 
            phase_prev = phase
            index += 1
            
        # handle last step
        prev_stage_list = stage_list
        
        if not self.qor_stg_hb[log].empty:
            self.qor_stg_hb[log]['('+str(stg_index)+')'+prev_stage_list[int(phase)-1]] = self.qor_hb[log].iloc[:,index-1]
            self.qor_generated.append(log)
            self.generate_lcs()

        return self.qor_hb[log]

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
                # print "abnormal heartbeat line: %s" %line
                continue
            i += 1
        return hb 

    def elapse_mem_profiler(self, input, script=None):
        hb = pd.DataFrame(index=METRICS_ORDER_ELAPSE_MEM)
        f = open(input).readlines()
        func_stack = []
        ttl_elapse = 0
        ttl_mem = 0
        step_num = 0

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
                        hb['('+str(step_num)+')'+func_name] = [ttl_elapse, ttl_mem]
                        func_stack.pop()
                        step_num += 1
        return hb

    def func_dist_profiler(self, input, script=None):
        ttl_plc_elapse = 0
        ttl_lgl_elapse = 0
        ttl_dlyo_elapse = 0
        ttl_grt_elapse = 0
        ttl_plc_mem = 0
        ttl_lgl_mem = 0
        ttl_dlyo_mem = 0
        ttl_grt_mem = 0
        ttl_elapse = 0
        ttl_mem = 0
        hb = pd.DataFrame(index=METRICS_ORDER_FUNC_DIST)

        if os.path.isdir(input):
            #full flow func dist extract
            for log in FULL_FLOW_PPA_LOG_LIST:
                design_name = input.split('/')[-1]
                log_file = input+'/'+design_name+'.'+log+'.out'
                if os.path.exists(log_file):
                    if hb.empty:
                        hb = self.func_dist_profiler(log_file) 
                    else:
                        hb += self.func_dist_profiler(log_file)
            return hb
        else:
            #single stage func dist  
            try:        
                f = open(input).readlines()
                for line in f:
                    match = re.search("END_FUNC:\s+.*\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
                    if match:
                        ttl_elapse = match.group(1)
                        ttl_mem = match.group(2)

                    match = re.search("START_FUNC:\s+nplcoarse::run\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
                    if match:
                        plc_elapse_s = match.group(1)
                        plc_mem_s = match.group(2)
                    match = re.search("END_FUNC:\s+nplcoarse::run\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
                    if match:
                        plc_elapse_e = match.group(1)
                        plc_mem_e = match.group(2)
                        ttl_plc_elapse += int(plc_elapse_e) - int(plc_elapse_s)
                        ttl_plc_mem += int(plc_mem_e) - int(plc_mem_s)

                    match = re.search("START_FUNC:\s+psynopt_delay_opto\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
                    if match:
                        dlyo_elapse_s = match.group(1)
                        dlyo_mem_s = match.group(2)
                    match = re.search("END_FUNC:\s+psynopt_delay_opto\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
                    if match:
                        dlyo_elapse_e = match.group(1)
                        dlyo_mem_e = match.group(2)
                        ttl_dlyo_elapse += int(dlyo_elapse_e) - int(dlyo_elapse_s)
                        ttl_dlyo_mem += int(dlyo_mem_e) - int(dlyo_mem_s)

                    match = re.search("START_FUNC:\s+legalize_placement\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
                    if match:
                        lgl_elapse_s = match.group(1)
                        lgl_mem_s = match.group(2)
                    match = re.search("END_FUNC:\s+legalize_placement\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
                    if match:
                        lgl_elapse_e = match.group(1)
                        lgl_mem_e = match.group(2)
                        ttl_lgl_elapse += int(lgl_elapse_e) - int(lgl_elapse_s)
                        ttl_lgl_mem += int(lgl_mem_e) - int(lgl_mem_s)

                    match = re.search("START_CMD:\s+route_global\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
                    if match:
                        grt_elapse_s = match.group(1)
                        grt_mem_s = match.group(2)
                    match = re.search("END_CMD:\s+route_global\s+CPU:\s+\d+\s+.*ELAPSE:\s+(\d+)\s+.*MEM-PEAK:\s+(\d+)\s+Mb", line)
                    if match:
                        grt_elapse_e = match.group(1)
                        grt_mem_e = match.group(2)
                        ttl_grt_elapse += int(grt_elapse_e) - int(grt_elapse_s)
                        ttl_grt_mem += int(grt_mem_e) - int(grt_mem_s)

                ttl_others_elapse = int(ttl_elapse) - ttl_plc_elapse - ttl_lgl_elapse - ttl_dlyo_elapse - ttl_grt_elapse
                ttl_others_mem = int(ttl_mem) - ttl_plc_mem - ttl_lgl_mem - ttl_dlyo_mem - ttl_grt_mem

                hb['PLC'] = [ttl_plc_elapse, ttl_plc_mem]
                hb['LGL'] = [ttl_lgl_elapse, ttl_lgl_mem]
                hb['DLYO'] = [ttl_dlyo_elapse, ttl_dlyo_mem]
                hb['GRT'] = [ttl_grt_elapse, ttl_grt_mem]
                hb['OTHERS'] = [ttl_others_elapse, ttl_others_mem]
            except:
                # no permission
                pass

            return hb


    def full_flow_ppa_profiler(self, dir,script=None):        
        design_name = dir.split('/')[-1]
        hb = pd.DataFrame(index=METRICS_ORDER_FULL_FLOW_PPA)
        for tool in FULL_FLOW_PPA_RPT_LIST:
            log_qp = dir+'/qor_profile/'+design_name+'.'+tool+'.qp'
            log = dir+'/'+design_name+'.'+tool+'.out'
            log_gz = dir+'/'+design_name+'.'+tool+'.out.gz'
            if os.path.exists(log_qp):    
                hb[FULL_FLOW_PPA_NAME_MAP[tool]] = self.extract_qor(log_qp)
            elif os.path.exists(log):
                hb[FULL_FLOW_PPA_NAME_MAP[tool]] = self.extract_qor(log)
            elif os.path.exists(log_gz):
                hb[FULL_FLOW_PPA_NAME_MAP[tool]] = self.zextract_qor(log_gz)

        return hb.dropna(axis=1, how='all')

    def zextract_qor(self, log):
        f = os.popen("zcat "+log+" | awk '/Design[[:space:]]+\(Setup\)[[:space:]]+[-+]?([0-9]*\.[0-9]+|[0-9]+)[[:space:]]+/ {print $3}' ").readlines()
        if not len(f): return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]

        wns = f[0].strip('\n')
        f = os.popen("zcat "+log+" | awk '/Time Unit.*:/ {print $4}' ").readlines()
        if len(f):
            unit = f[0].strip('\n')
        else:
            unit = '1ns'
        area = os.popen("zcat "+log+" |awk '/Cell Area \(netlist\):/ {print $4}' ").readlines()[0].strip()
        lkg = os.popen("zcat "+log+" |awk '/Cell Leakage Power\W+=/ {print $5}' ").readlines()
        if len(lkg):
            lkg = lkg[0].strip()
        else:
            lkg = 0

        dyn = os.popen("zcat "+log+" |awk '/Total Dynamic Power\W+=/ {print $5}' ").readlines()
        if len(dyn):
            dyn = dyn[0].strip()
        else:
            dyn = 0

        try:
            elapse = os.popen("zcat "+log+" |awk '/Elapsed time for this session:/ {print $6}' ").readlines()[0].strip()
            mem = os.popen("zcat "+log+" |awk '/Maximum memory usage for this session:/ {print $7}' ").readlines()[0].strip()
        except:
            elapse = np.nan
            mem = np.nan

        clk_sets = defaultdict(float)
        report_timing = os.popen("zcat "+log+" |awk '/clock .* \(.* edge\)\W+\w+\W+\w+/ {print $2, $5}' ").readlines()
        for rpt in report_timing:
            clk_name = rpt.strip().split()[0]
            clk_period = rpt.strip().split()[1]
            if float(clk_period) != 0:
                if not clk_sets.has_key(clk_name):
                    clk_sets[clk_name] = clk_period
                elif clk_sets[clk_name] > clk_period:
                    clk_sets[clk_name] = clk_period
        try:
            worst_clk_name = report_timing[1].strip().split()[0]
        except:
            worst_clk_name = 'abnormal'

        if 'ns' in unit:
            freq = 1/(float(clk_sets[worst_clk_name])-float(wns))
        elif 'ps' in unit:
            freq = 1000/(float(clk_sets[worst_clk_name])-float(wns))
        return [format(freq,".3f"), format(float(wns), '.3f'), format(float(area), '.3f'), lkg, dyn, elapse, mem]

    def extract_qor(self, log):
        f = os.popen("awk '/Design[[:space:]]+\(Setup\)[[:space:]]+[-+]?([0-9]*\.[0-9]+|[0-9]+)[[:space:]]+/ {print $3}' " + log).readlines()
        if not len(f): return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]

        wns = f[0].strip('\n')
        f = os.popen("awk '/Time Unit.*:/ {print $4}' " + log).readlines()
        if len(f):
            unit = f[0].strip('\n')
        else:
            unit = '1ns'

        area = os.popen("awk '/Cell Area \(netlist\):/ {print $4}' " + log).readlines()[0].strip()

        lkg = os.popen("awk '/Cell Leakage Power\W+=/ {print $5}' " + log).readlines()
        if len(lkg):
            lkg = lkg[0].strip()
        else:
            lkg = 0

        dyn = os.popen("awk '/Total Dynamic Power\W+=/ {print $5}' " + log).readlines()
        if len(dyn):
            dyn = dyn[0].strip()
        else:
            dyn = 0

        try:
            elapse = os.popen("awk '/Elapsed time for this session:/ {print $6}' " + log).readlines()[0].strip()
            mem = os.popen("awk '/Maximum memory usage for this session:/ {print $7}' " + log).readlines()[0].strip()
        except:
            elapse = np.nan
            mem = np.nan

        clk_sets = defaultdict(float)
        report_timing = os.popen("awk '/clock .* \(.* edge\)\W+\w+\W+\w+/ {print $2, $5}' " + log).readlines()

        for rpt in report_timing:
            clk_name = rpt.strip().split()[0]
            clk_period = rpt.strip().split()[1]
            if float(clk_period) != 0:
                if not clk_sets.has_key(clk_name):
                    clk_sets[clk_name] = clk_period
                elif clk_sets[clk_name] > clk_period:
                    clk_sets[clk_name] = clk_period
        try:
            worst_clk_name = report_timing[1].strip().split()[0]
        except:
            worst_clk_name = 'abnormal'

        if 'ns' in unit:
            freq = 1/(float(clk_sets[worst_clk_name])-float(wns))
        elif 'ps' in unit:
            freq = 1000/(float(clk_sets[worst_clk_name])-float(wns))
        return [format(freq,".3f"), format(float(wns), '.3f'), format(float(area), '.3f'), lkg, dyn, elapse, mem]

    def extract_step(self, step):
        match = re.search('(\(\w+\))(.*)\s?', step)
        new_step  = match.group(1)[-4:-1]+'-'+match.group(2)
        return new_step

    def generate_lcs(self):
        if len(self.qor_generated) <= 1: return

        # lcs algorithm to get longest subsequence steps
        log1 = self.qor_generated[0]
        log2 = self.qor_generated[-1]
        step_list1 = self.qor_hb[log1].columns.values
        step_list2 = self.qor_hb[log2].columns.values
        step_index1 = []
        step_index2 = []
        lcs = [[0 for i in range(len(step_list2)+1)] for i in range(len(step_list1)+1)]
        for i in range(len(step_list1)-1, -1, -1):
            for j in range(len(step_list2)-1, -1, -1):
                if self.extract_step(step_list1[i]) == self.extract_step(step_list2[j]):
                    lcs[i][j] = lcs[i+1][j+1]+1
                else:
                    lcs[i][j] = max(lcs[i+1][j], lcs[i][j+1])
        i = 0
        j = 0
        index = 0
        new_columns = []
        while i < len(step_list1) and j < len(step_list2):
            stepi = self.extract_step(step_list1[i])
            stepj = self.extract_step(step_list2[j])
            if  stepi == stepj:
                step_index1.append(i)
                step_index2.append(j)
                i += 1
                j += 1
                match = re.search('(\w\w\d)-(.*)', stepi)
                stg = match.group(1)
                step = match.group(2)
                common_step = '('+str(index)+stg+')'+step
                index += 1
                new_columns.append(common_step)
            elif lcs[i + 1][j] >= lcs[i][j + 1]:
                i += 1
            else:
                j += 1

        # re-extract steps from original hb and re-index
        for i in range(len(self.qor_generated)):
            log = self.qor_generated[i]
            hb_update = pd.DataFrame(index=METRICS_ORDER_QOR)
            if i < len(self.qor_generated) - 1:
                step_index = step_index1
            else:
                step_index = step_index2
            for j in step_index:
                hb_update = pd.concat([hb_update, self.qor_hb[log].iloc[:,j]], axis=1)
            self.qor_hb[log] = hb_update
            self.qor_hb[log].columns = new_columns


if __name__ == "__main__":
    import argparse
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-logs', nargs='+', required=True, help='Log files to be profiled.')       
        parser.add_argument('-pattern', required=True, choices=['aps', 'qor', 'qor_stg', 'df_ropt', 'ropt', 'gropt', 'df_gropt', 'npo_popt', 'df_npo_popt', 'npo_copt', 'df_npo_copt','user'], help='Extract log with given pattern.')
        parser.add_argument('-compress', action="store_true", help='Compress consecutive same steps')
        parser.add_argument('-script', help='User script to extract pattern in log.')
        parser.add_argument('-dump_csv', action="store_true", help='Output dataframe to csv.')
        record_usage("terminal",getpass.getuser())
        args = parser.parse_args()
        qp = QorProfiler(input_list=args.logs, compress=args.compress, dump_csv=args.dump_csv)

        for log in args.logs:
            if args.pattern == 'aps':
                output = qp.aps_profiler(log)
            elif args.pattern == 'qor':
                qp.generate_profile()
                output = qp.qor_hb[log]                
            elif args.pattern == 'qor_stg':
                qp.generate_profile()
                output = qp.qor_stg_hb[log]
            elif args.pattern == 'ropt':
                output = qp.ropt_profiler(log)
            elif args.pattern == 'df_ropt':
                output = qp.df_ropt_profiler(log)
            elif args.pattern == 'npo_popt':
                output = qp.npo_popt_profiler(log)
            elif args.pattern == 'df_npo_popt':
                output = qp.df_npo_popt_profiler(log)  
            elif args.pattern == 'npo_copt':
                output = qp.npo_copt_profiler(log)
            elif args.pattern == 'df_npo_copt':
                output = qp.df_npo_copt_profiler(log)                 
            elif args.pattern == 'gropt':
                output = qp.gropt_profiler(log)
            elif args.pattern == 'df_gropt':
                output = qp.df_gropt_profiler(log)
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
                if args.dump_csv:
                    print "Output hb to %s.%s.csv" %(log, args.pattern)
                    output.T.to_csv(log+'.'+args.pattern+'.csv', float_format='%g')                
                print tabulate(output.T, headers='keys', tablefmt='psql')                   

    except OSError as e:
        import traceback
        traceback.print_exc()
        print "I/O error({0}): {1} {2}".format(e.errno, e.strerror, e.filename)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print e

