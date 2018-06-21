#!/remote/us01home40/phyan/depot/Python-2.7.11/bin/python
import sys
import os
import commands
import re
from jinja2 import Environment, PackageLoader, FileSystemLoader
import getpass
import MySQLdb
import datetime
from collections import defaultdict
#data analysis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import logging

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
    filename='app.log',
    filemode='a')
#==========================
# global var init
#==========================
argc = len(sys.argv)
if argc > 7:
    print "Error: No more than 5 inputs to be compared... Do you really need to compare that many inputs?"
    exit()

mode = sys.argv[1]

def get_argv():
    argv_list = []
    for i in range(2, argc):
        if not os.path.exists(sys.argv[i]):
            print "Error: \"%s\" does not exist, please double check..." % sys.argv[i]
            exit()
        argv_list.append(sys.argv[i])
    return sorted(argv_list)

#==========================
# 1. global var init
#==========================
PATTERN_DICT = {
    "PREROUTE": "/u/phyan/qor.pl",
    "ROPT": "/u/phyan/ropt_grep.csh",
    "GROPT": "/u/phyan/gropt_grep.csh"
}
PATTERN_FUNC = {
    "PREROUTE": "preroute_pattern_to_metrics",
    "ROPT": "ropt_pattern_to_metrics",
    "GROPT": "gropt_pattern_to_metrics"
}
COLOR_LIST = ["#FF6384","#36A2EB","#FFCE56","#99CC33","#CC9933"]
#==========================
# 1.1 pre-route heartbeat
#==========================
METRICS_PROPERTY = {"CPU" : [1, 'linear'], "WNS" : [2, 'logarithmic'], "TNS" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "MAXTRAN" : [5, 'logarithmic'],
 "MAXCAP" : [6, 'logarithmic'], "BUFFCNT" : [7, 'linear'], "INVCNT" : [8, 'linear'], "LVTCNT" : [9, 'linear'],
  "LVTPCNT" : [10, 'linear'], "MEM" : [11, 'linear'], "LEAKPWR" : [12, 'linear'], "WHNS" : [12, 'linear']}
METRICS_PROPERTY1 = {"CPU" : [1, 'linear'], "WNS" : [2, 'logarithmic'], "TNS" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "MAXTRAN" : [5, 'logarithmic'],
 "MAXCAP" : [6, 'logarithmic'], "BUFFCNT" : [7, 'linear'], "INVCNT" : [8, 'linear'], "LVTCNT" : [9, 'linear'],
  "LVTPCNT" : [10, 'linear'], "MEM" : [11, 'linear'], "LEAKPWR" : [12, 'linear'], "WHNS" : [13, 'linear']}
METRICS_ORDER = ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "AREA","MEM", "CPU"]
METRICS_ORDER_INDEX = [0,2,3,5,6,7,8,9,10,4,11,1]
METRICS_ORDER_1 = ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "AREA", "MEM", "CPU", "LEAKPWR"]
METRICS_ORDER_INDEX_1 = [0,2,3,5,6,7,8,9,10,4,11,1,12]
METRICS_ORDER_2 = ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "AREA", "MEM", "CPU", "WHNS"]
METRICS_ORDER_INDEX_2 = [0,2,3,5,6,7,8,9,10,4,11,1,12]
METRICS_ORDER_3 = ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "AREA", "MEM", "CPU", "LEAKPWR", "WHNS"]
METRICS_ORDER_INDEX_3 = [0,2,3,5,6,7,8,9,10,4,11,1,12,13]
OPT_CMD = ['popt', 'copt']
CALC = [3600, 60, 1]

#==========================
# 1.2 Route-opt optimization
#==========================
METRICS_PROPERTY_ROPT = {"RSETUP" : [1, 'linear'], "SETUP_COST" : [2, 'logarithmic'], "RHOLD" : [3, 'logarithmic'], "HOLD_COST" : [4, 'linear'], "RLDRC_MT" : [5, 'logarithmic'],
    "RLDRC_MC" : [6, 'logarithmic'], "LDRC_COST" : [7, 'logarithmic'], "AREA" : [8, 'linear'], "LEAKAGE" : [9, 'linear'], "ELAPSE" : [10, 'linear']}
METRICS_ORDER_ROPT = ["RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"]
#==========================
# 1.3 Global Route-opt optimization
#==========================
METRICS_PROPERTY_GROPT = {"SETUP_COST" : [1, 'logarithmic'], "HOLD_COST" : [2, 'linear'], "LDRC_COST" : [3, 'logarithmic'], 
    "AREA" : [4, 'linear'], "LEAKAGE" : [5, 'linear'], "ELAPSE" : [6, 'linear']}
METRICS_ORDER_GROPT = ["SETUP_COST","HOLD_COST","LDRC_COST","AREA","LEAKAGE","ELAPSE"]

url_list = []
#==========================
# 2. function definition
#==========================
def record_usage(mode):
    conn = MySQLdb.connect(host="pvicc015",user="user",db="preroute_random")
    cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print time

    username = getpass.getuser()
    if username != "phyan":
        source = "terminal"
        sql = "insert into qor_analyzer(username,source,mode,date) values(%s,%s,%s,%s)"
        param = (username,source,mode,time,)
        n = cursor.execute(sql,param)

#==============================
# 3. Main
#==============================
def main():
#==============================
# 3.1 QoR metric extraction
#==============================
#=========================
# 3.1.1 log mode
#=========================
    if mode == "log" or mode == "log_compress":
        # log info extraction
        log_list = argv_list = get_argv()

        print "#================================"
        print "# Detected log mode "
        print "#================================\n"
        for log in log_list:
            if not os.path.isfile(log):
                print "Error: '%s' file does not exist..." % log
                exit()
        qor_metrics_dict, step_qor_dict, auto_skip_dict, step_match_dict, metrics_order_dict, metrics_order_index_dict, metrics_property_dict = log_qor_analyze(log_list, mode)

        #print len(step_qor_list[0])
        display_qor_analysis_log(qor_metrics_dict=qor_metrics_dict, step_qor_dict=step_qor_dict, log_list=argv_list, 
            auto_skip_dict=auto_skip_dict, step_match_dict=step_match_dict,
            metrics_order_dict=metrics_order_dict, metrics_order_index_dict=metrics_order_index_dict, metrics_property_dict=metrics_property_dict)
        record_usage(mode=mode)
        print "======URLs for QoR Analyzer======"
        for url in url_list:
            print url

#=========================
# 3.1.2 dir/flow mode
#=========================
    if mode == "flow" or mode == "flow_compress":
        print "#================================"
        print "# Detected dir/flow mode "
        print "#================================\n"
        argv_list = get_argv()
        for argv in argv_list:
            if not os.path.isdir(argv):
                print "Error: '%s' path does not exist..." % argv
                exit()
        for cmd in OPT_CMD:
            print "======Handling nw" + cmd + " files======\n"
            dir_list = argv_list
            #print dir_list
            flow_metrics = {} # flow/design table
            flow_qor_metrics = {} #design/qor-per-flow table
            step_qor_dict = {}
            design_chart_dict = {}

            print "===Scan design candidates===\n"
            #process flows/designs
            for flow in dir_list:
                try:
                    #relative path mode
                    search_path = os.getcwd() + "/" + flow
                    designs = os.listdir(search_path)
                except:
                    #absolute path mode
                    search_path = flow
                    designs = os.listdir(search_path)

                for design in designs:
                    print "Find",design,"..."
                    if os.path.isdir(search_path + "/" + design):
                        if os.path.exists(search_path + "/" + design + "/" + design + ".nw" + cmd + ".out.gz") or os.path.exists(search_path + "/" + design + "/" + design + ".nw" + cmd + ".out"):
                            if flow_metrics.has_key(design):
                                flow_metrics[design].append(flow)
                            else:
                                flow_metrics[design] = []
                                flow_metrics[design].append(flow)
                        else:
                            print search_path + "/" + design + "/" + design + ".nw" + cmd + ".out or .out.gz does not exist, skip..."
                    else:
                        print search_path + "/" + design + " is not dir, skip..."
            #print flow_metrics

            # init flow qor metrics
            print "\n===Extract design qor statistics===\n"
            for design in sorted(flow_metrics.keys()):
                design_chart_dict[design] = {}
                #print "Process",design,"..."
                design_log_list = [] # map design name to coresponding log file name
                design_chart_dict[design]['fatal_flow'] = []
                for flow in flow_metrics[design]:
                    log_path = flow + "/" + design + "/" + design + ".nw" + cmd + ".out.gz"
                    if not os.path.exists(log_path):
                        log_path = flow + "/" + design + "/" + design + ".nw" + cmd + ".out"
                    fatal_path = flow + "/" + design + "/" + design + ".nw" + cmd + ".out.gz.fatal"
                    fatal_path_1 = flow + "/" + design + "/" + design + ".nw" + cmd + ".out.fatal"
                    if os.path.exists(fatal_path) or os.path.exists(fatal_path_1):
                        design_chart_dict[design]['fatal_flow'].append(str(flow))
                    design_log_list.append(log_path)
                print design_log_list

                flow_qor_metrics[design], step_qor_dict[design], design_chart_dict[design]['auto_skip'], design_chart_dict[design]['step_match'],\
                design_chart_dict[design]['metrics_order'], design_chart_dict[design]['metrics_order_index'], design_chart_dict[design]['metrics_property'] = log_qor_analyze(design_log_list, mode)
                #print design_chart_dict[design][step_match]
            display_qor_analysis_flow(flow_qor_metrics=flow_qor_metrics, step_qor_dict=step_qor_dict, flow_metrics=flow_metrics,
                argv_list=argv_list, design_chart_dict=design_chart_dict, cmd=cmd)
        record_usage(mode=mode)
        print "======URLs for QoR Analyzer======"
        for url in url_list:
            print url

    if mode == "trend":
        prs_path, baseline, compare, rpt_script = sys.argv[2:6]
        prs_trend_analyze(prs_path=prs_path, baseline=baseline, compare=compare, rpt_script=rpt_script)
        print "======URLs for QoR Analyzer======"
        for url in url_list:
            print url

#========================
#trend analysis
#========================
def get_rpt_qor_metrics(rpt_script):
    DEFAULT_METRICS_LIST = ['GROver', 'TNSPF', 'WNS', 'NMxCapPM', 'SDynPow', 'SLeakPow', 'STotPow', 'NMxTranPM']
    RPT_ANC_RE = re.compile("#report_line#")
    WORD_RE = re.compile("\S+")
    #IC_RE = re.compile("IC.(\w+)")
    metrics_count = {}
    rpt_line = False
    fp = open(rpt_script)
    f = fp.readlines()
    for line in f:
        if rpt_line:
            for match in WORD_RE.finditer(line):
                qor_metrics = match.group()
                match1 = re.match("IC.(\w+)", qor_metrics)
                match2 = re.search("Mem|CLKcmd", qor_metrics)
                if match1 and not match2:
                    qor_metrics = match1.group(1)
                    metrics_count.setdefault(qor_metrics, 0)
                    metrics_count[qor_metrics] += 1
            break
        if len(RPT_ANC_RE.findall(line)):
            rpt_line = True
    if rpt_line:
        metrics_list = [k for k,v in metrics_count.items() if v == 4]
    else:
        metrics_list = DEFAULT_METRICS_LIST
    return metrics_list

def prs_trend_analyze(prs_path, baseline, compare, rpt_script):
    QOR_ORDER = ['ICP','ICC','ICR','ICF']
    metrics_list = get_rpt_qor_metrics(rpt_script=rpt_script)
    fp = open(prs_path+'/report/allbase/'+baseline+'/drep.html')
    f = fp.readlines()
    index = {}
    for line in f:
        for metrics in metrics_list:
            index.setdefault(metrics, {})
            QOR_RE = re.compile(compare+'_(\S+)_(IC.'+metrics+')_top"\>\s+(\S+)% \<')
            for match in QOR_RE.finditer(line):
                design, column, value = match.group(1), match.group(2), match.group(3)
                if value == '--':
                    value = '+0.00%'
                qor_pair = (column, value)
                index[metrics].setdefault(design, []).append(qor_pair)
    #print index
    qor_metrics = {}
    for metrics in index:
        if not index[metrics]:
            print "IC*%s column content is empty, drop from trend analysis table..." %metrics
            continue
        qor_metrics[metrics] = {}
        for design, qor_tuple in index[metrics].items():
            qor_metrics[metrics][design] = [float(t[1]) for t in sorted(qor_tuple, key=lambda x: QOR_ORDER.index(x[0][:3])) ]
    #print qor_metrics
    display_trend_analysis(qor_metrics=qor_metrics)

#==============================
# pattern handling
#==============================
def pattern_match(log):
    f = open(log)
    first_line = f.readlines()[0].strip()
    is_heartb = re.search("Heartbeat", first_line)
    rpt_dict = {}

    for pattern_name, script in PATTERN_DICT.items():
        rpt_dict[pattern_name] = os.popen(script + " " + log)
        #pattern_to_metrics(pattern_name, rpt[pattern_name])

    return rpt_dict

def pattern_to_metrics(rpt_dict):
    pattern_metrics_dict = {}
    metrics_property= {}
    auto_skip = {}
    metrics_order = {}
    metrics_order_index = {}

    for pattern_name, pattern_func_name in PATTERN_FUNC.items():
        #print "Handling pattern: %s" %pattern_name
        pattern_func = eval(pattern_func_name)
        pattern_metrics_dict[pattern_name],\
        metrics_property[pattern_name], metrics_order[pattern_name], metrics_order_index[pattern_name],\
        auto_skip[pattern_name] = pattern_func(rpt_dict[pattern_name])

    #print metrics_order_index
    return pattern_metrics_dict, auto_skip, metrics_property, metrics_order, metrics_order_index

def ropt_pattern_to_metrics(rpt):
    f = rpt.readlines()
    auto_skip = "false"
    metrics_property = METRICS_PROPERTY_ROPT
    metrics_order = METRICS_ORDER_ROPT
    metrics_order_index = range(11)

    regexp = re.compile('(\S+)\s+Iter\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)')
    qor_metrics = []
    if mode.find("compress") >= 0:
        pass
    else:
        for line in f:
            match = regexp.search(line)
            if match:
                #print match.groups()
                qor_metrics.append(list(match.groups()))
    qor_metrics = np.array(qor_metrics)
    qor_metrics = qor_metrics.T
    
    return qor_metrics, metrics_property, metrics_order, metrics_order_index, auto_skip

def gropt_pattern_to_metrics(rpt):
    f = rpt.readlines()
    auto_skip = "false"
    metrics_property = METRICS_PROPERTY_GROPT
    metrics_order = METRICS_ORDER_GROPT
    metrics_order_index = range(7)

    regexp = re.compile('(\S+)\s+Iter\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)')
    qor_metrics = []
    if mode.find("compress") >= 0:
        pass
    else:
        for line in f:
            match = regexp.search(line)
            if match:
                #print match.groups()
                qor_metrics.append(list(match.groups()))
    qor_metrics = np.array(qor_metrics)
    qor_metrics = qor_metrics.T
    #print qor_metrics
    return qor_metrics, metrics_property, metrics_order, metrics_order_index, auto_skip

def preroute_pattern_to_metrics(rpt):
    f = rpt.readlines()
    auto_skip = "false"

    if (len(f) > 4):
        anchor1 = len(f[1].split())
        metrics_property = METRICS_PROPERTY
        if anchor1 == 14 or anchor1 == 13:
            rows = 13
        elif anchor1 == 15:
            metrics_property = METRICS_PROPERTY1
            rows = 14
        elif anchor1 == 12:
            rows = 12
        else:
            rows = 12

        anchor2 = f[1].split()[-1]
        anchor3 = f[1].split()[-3]
        #print anchor2

        metrics_order = METRICS_ORDER
        metrics_order_index = METRICS_ORDER_INDEX
        if anchor2 == "PEAK":
            metrics_order = METRICS_ORDER
            metrics_order_index = METRICS_ORDER_INDEX
        elif anchor2 == "LEAKAGE":
            metrics_order = METRICS_ORDER_1
            metrics_order_index = METRICS_ORDER_INDEX_1
        elif anchor2 == "DELAY" and anchor3 == "PEAK":
            metrics_order = METRICS_ORDER_2
            metrics_order_index = METRICS_ORDER_INDEX_2
        elif anchor2 == "DELAY" and anchor3 == "LEAKAGE":
            metrics_order = METRICS_ORDER_3
            metrics_order_index = METRICS_ORDER_INDEX_3

        cols = len(f) - 4
    else:
        metrics_property = METRICS_PROPERTY
        metrics_order = METRICS_ORDER
        metrics_order_index = METRICS_ORDER_INDEX
        rows = 12
        cols = 1

    #print rows
    #log_rpt[log] = rpt
    #cols = int(commands.getoutput("cat " + rpt +" | wc -l")) - 4
    #cols = rpt_cols if rpt_cols > cols else cols
    #if cols > 80: auto_skip = "true"
    i = 0

    # logs/qor-metrics/qor-value table
    qor_metrics = [[]  for row in range(14)]

    # read logs
    #for (log, rpt) in sorted(log_rpt.iteritems()):
    #print "Analyze", log, "..."
    #print log, rpt
    #f = open(rpt)

    j = 0
    cmd_prefix = ""
    if mode.find("compress") >= 0:
        for line in f:
            match = re.search(r'place_opt',line)
            if match:
                cmd_prefix = "P"
                continue
            match = re.search(r'clock_opt',line)
            if match:
                cmd_prefix = "C"
                continue
            match = re.search(r'refine_opt',line)
            if match:
                cmd_prefix = "RE"
                continue

            try:
                #debug mode used in log file
                match = re.search(r'(\S+)\s+(\d+:\d+:\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
                if not match: # LEAK and MIN detected
                    #print "Debug mode detected in log file..."
                    match = re.search(r'(\S+)\s+(\d+:\d+:\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
                    if not match:
                        match = re.search(r'(\S+)\s+(\d+:\d+:\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
                        if not match:
                            continue

                for k in range(1, rows+1):
                    if k == 1:
                        step_label = str(match.group(k))
                        if ((j > 0) and (str(qor_metrics[k-1][j-1])[(str(qor_metrics[k-1][j-1]).find(")")+1):] == step_label)):
                            j -= 1
                            same_step = True
                        else:
                            qor_metrics[k-1].append("("+str(j)+cmd_prefix+")"+step_label)
                            same_step = False
                    elif k == 2:
                        seconds = sum([int(match.group(k).split(":")[index]) * CALC[index] for index in range(3)])
                        if not same_step:
                            qor_metrics[k-1].append(seconds)
                        else:
                            qor_metrics[k-1][j] = seconds
                    elif (k in [3,4,6,7]): #need translate 0 to 0.00001
                        if match.group(k) == "~":
                            if not same_step:
                                qor_metrics[k-1].append(0.00001)
                            else:
                                qor_metrics[k-1][j] = 0.00001
                        elif float(match.group(k)) == 0.0:
                            if not same_step:
                                qor_metrics[k-1].append(0.00001)
                            else:
                                qor_metrics[k-1][j] = 0.00001
                        else:
                            if not same_step:
                                qor_metrics[k-1].append(match.group(k))
                            else:
                                qor_metrics[k-1][j] = match.group(k)
                    else:
                        try:
                            if not same_step:
                                qor_metrics[k-1].append(match.group(k))
                            else:
                                qor_metrics[k-1][j] = match.group(k)
                        except:
                            if j == 0:
                                if not same_step:
                                    qor_metrics[k-1].append(0)
                                else:
                                    qor_metrics[k-1][j] = 0
                            else:
                                if not same_step:
                                    qor_metrics[k-1].append(qor_metrics[k-1][j-1])
                                else:
                                    qor_metrics[k-1][j] = qor_metrics[k-1][j-1]

                j += 1
                continue
            except Exception, e:
                #print e
                #print "No match"
                pass
    else:
        for line in f:
            match = re.search(r'place_opt',line)
            if match:
                cmd_prefix = "P"
                continue
            match = re.search(r'clock_opt',line)
            if match:
                cmd_prefix = "C"
                continue
            match = re.search(r'refine_opt',line)
            if match:
                cmd_prefix = "RE"
                continue

            try:
                #debug mode used in log file
                match = re.search(r'(\S+)\s+(\d+:\d+:\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
                if not match:
                    match = re.search(r'(\S+)\s+(\d+:\d+:\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
                    if not match:
                        match = re.search(r'(\S+)\s+(\d+:\d+:\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
                        if not match:
                            continue

                for k in range(1, rows+1):
                    if k == 1:
                        step_label = str(match.group(k))
                        qor_metrics[k-1].append("("+str(j)+cmd_prefix+")"+step_label)
                    elif k == 2:
                        seconds = sum([int(match.group(k).split(":")[index]) * CALC[index] for index in range(3)])
                        qor_metrics[k-1].append(seconds)
                    elif (k in [3,4,6,7]): #need translate 0 to 0.00001
                        if match.group(k) == "~":
                            qor_metrics[k-1].append(0.00001)
                        elif float(match.group(k)) == 0.0:
                            qor_metrics[k-1].append(0.00001)
                        else:
                            qor_metrics[k-1].append(match.group(k))
                    else:
                        try:
                            qor_metrics[k-1].append(match.group(k))
                        except:
                            if j == 0:
                                qor_metrics[k-1].append(0)
                            else:
                                qor_metrics[k-1].append(qor_metrics[k-1][j-1])
                    #print qor_metrics_list[i][0][j], qor_metrics_lis
                #print qor_metrics_list[i][0][j], qor_metrics_list[i][2][j], qor_metrics_list[i][7][j]
                j += 1
                continue

            except Exception, e:
                #print e
                #print "No match"
                pass

    #print qor_metrics[0]
    if len(qor_metrics[0]) > 80:
        auto_skip = "true"

    qor_metrics = np.array(qor_metrics)
    qor_metrics = np.array([y for y in qor_metrics if len(y) > 0])

    return qor_metrics, metrics_property, metrics_order, metrics_order_index, auto_skip

# log analysis
def log_qor_analyze(log_list, mode):
    auto_skip_dict = defaultdict(list)
    step_match_dict = defaultdict(list)
    qor_metrics_dict = defaultdict(list)
    step_qor_dict = defaultdict(list)
    metrics_property_dict = defaultdict(list)
    metrics_order_dict = defaultdict(list)
    metrics_order_index_dict = defaultdict(list)

    #log_rpt = {} # log/rpt table
    for log in log_list: #already sorted log name
        print "Extracting and analyzing", log, "..."
        #rpt = log + ".qor"
        rpt_dict = pattern_match(log)
        pattern_metrics_dict, auto_skip, metrics_property, metrics_order, metrics_order_index = pattern_to_metrics(rpt_dict)

        for pattern, script in PATTERN_DICT.items():
            qor_metrics = pattern_metrics_dict[pattern]
            step_qor = qor_metrics.T
            qor_metrics_dict[pattern].append(qor_metrics.tolist())
            step_qor_dict[pattern].append(step_qor.tolist())
            auto_skip_dict[pattern].append(auto_skip[pattern])
            metrics_property_dict[pattern].append(metrics_property[pattern])
            metrics_order_dict[pattern].append(metrics_order[pattern])
            metrics_order_index_dict[pattern].append(metrics_order_index[pattern])

    for pattern, script in PATTERN_DICT.items():
        empty_pattern = True
        for i in range(0, len(qor_metrics_dict[pattern])-1):
            if len(qor_metrics_dict[pattern][i]) > 0:
                empty_pattern = False
                break
        if empty_pattern:
            print "No info extracted for pattern: %s" %pattern
            del qor_metrics_dict[pattern]
            continue

        step_match_dict[pattern] = 1
        if len(qor_metrics_dict[pattern]) > 1:
            for i in range(0, len(qor_metrics_dict[pattern])-1):
                #print len(qor_metrics_list[i][0]), len(qor_metrics_list[i+1][0])
                if len(qor_metrics_dict[pattern][i][0]) != len(qor_metrics_dict[pattern][i+1][0]): step_match_dict[pattern] = 0
        #print step_match
        if step_match_dict[pattern]:
            print "steps of pattern: %s between logs match, will show qor metrics in same chart...\n" %pattern
        else:
            print "steps of pattern: %s between logs not match, will show qor metrics in different charts...\n" %pattern
    
    #print qor_metrics_dict
    #print auto_skip_dict
    #print metrics_order_dict
    #print step_match_dict
    #print metrics_property_dict
    return dict(qor_metrics_dict), dict(step_qor_dict), dict(auto_skip_dict), dict(step_match_dict), dict(metrics_order_dict), dict(metrics_order_index_dict), dict(metrics_property_dict)

# qor display
def display_trend_analysis(qor_metrics):
    # flow qor display
    global url_list
    print "Recording QoR URL ...\n"
    #info = "QoR Analyzer info: "
    #print qor_metrics_list
    env = Environment(loader = FileSystemLoader('/remote/us01home40/phyan/workspace/python/qor_analyzer/templates'))
    templates = env.get_template('trend_mode.html')
    output = templates.render(
        qor_metrics = qor_metrics,
    )
    msg = "Output qor URL: " + " http://clearcase"+os.getcwd()+"/qor_analysis.html"
    url_list.append(msg)
    file_name = 'qor_analysis.html'
    f = open(file_name, 'w')
    f.write(output.encode("utf-8"))
    f.close()

def display_qor_analysis_log(qor_metrics_dict, step_qor_dict, log_list, auto_skip_dict, step_match_dict, metrics_order_dict, metrics_order_index_dict, metrics_property_dict):
    # flow qor display
    global url_list
    print "Recording QoR URL ...\n"
    #info = "QoR Analyzer info: "
    env = Environment(loader = FileSystemLoader('/remote/us01home40/phyan/workspace/python/qor_analyzer/templates'))
    templates = env.get_template('log_mode_dev.html')
    output = templates.render(
        qor_metrics_dict = qor_metrics_dict,
        step_qor_dict = step_qor_dict,
        log_list = log_list,
        metrics_property_dict = metrics_property_dict,
        metrics_order_dict = metrics_order_dict,
        metrics_order_index_dict = metrics_order_index_dict,
        color_list = COLOR_LIST,
        mode = "log",
        auto_skip_dict = auto_skip_dict,
        step_match_dict = step_match_dict
    )
    msg = "Output qor URL: " + " http://clearcase"+os.getcwd()+"/qor_analysis.html"
    url_list.append(msg)
    file_name = 'qor_analysis.html'
    f = open(file_name, 'w')
    f.write(output.encode("utf-8"))
    f.close()

def display_qor_analysis_flow(flow_qor_metrics, step_qor_dict, flow_metrics, argv_list, design_chart_dict, cmd):
    # flow qor display
    global url_list
    print "Recording QoR URL ...\n"
    #info = "QoR Analyzer info: "
    env = Environment(loader = FileSystemLoader('/remote/us01home40/phyan/workspace/python/qor_analyzer/templates'))

    templates = env.get_template('dir_mode_dev.html')
    output = templates.render(
        flow_qor_metrics=flow_qor_metrics,
        step_qor_dict = step_qor_dict,
        flow_metrics=flow_metrics,
        metrics_property=METRICS_PROPERTY,
        metrics_order=METRICS_ORDER_1,
        color_list=COLOR_LIST,
        argv_list=argv_list,
        mode="flow",
        design_chart_dict=design_chart_dict,
        cmd = cmd
    )
    #print design_chart_dict

    msg = "Output qor URL: " + " http://clearcase"+os.getcwd()+"/qor_analysis_"+cmd+".html"
    url_list.append(msg)
    file_name = 'qor_analysis_'+cmd+'.html'
    f = open(file_name, 'w')
    f.write(output.encode("utf-8"))
    f.close()

if __name__ == "__main__":
    main()