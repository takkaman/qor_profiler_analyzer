#!/remote/us01home40/phyan/depot/Python-2.7.11/bin/python
import sys, os, commands
import copy, re, getpass, datetime
import threading
from multiprocessing import Pool, Process
from multiprocessing.managers import BaseManager, DictProxy
#import MySQLdb
#from urllib import urlencode
#from werkzeug import MultiDict
from collections import defaultdict

import numpy as np
import pandas as pd

from socket import error as SocketError
import errno

#from flask import Flask, request, render_template, Response, jsonify
#from flask_util_js import FlaskUtilJs
#import json

from qorProfiler import QorProfiler

class MyManager(BaseManager):
    pass

MyManager.register('defaultdict', defaultdict, DictProxy)  
#==========================
# function definition
#==========================
def path_translate(path):
    path_split = path.split('/')
    if len(path_split) == 1: # empty input
        return path
    if path_split[0] == "~": # ~/xxx/xxx
        #username = request.remote_user
        username = "phyan"
    elif "~" in path_split[0]: # ~phyan/xxx/xxx
        username = path_split[0][1:]
    else: # normal path
        return path

    path_split.remove(path_split[0])
    path_split.insert(0, username)
    path_split.insert(0,'u')
    path_split.insert(0,'')

    return '/'.join(path_split)

def remove_step_prefix(step_list):
    pure_step_list = []
    for step in step_list:
        m = re.match(r'\(.*\)(\S+)',step)
        if m:
            pure_step = m.group(1)
            pure_step_list.append(pure_step)
        else:
            pure_step_list.append(step)
    return pure_step_list

def design_flow_extract(dir_list, cmd="popt", active_design=None, tech_nodes=[], customers=[]):
    design_flow_dict = defaultdict(list) # key:design value:flow/log list table
    design_flow_dict1 = defaultdict(list)
    tech_node_dict = defaultdict(list)
    customer_dict = defaultdict(list)
    design_list = []
    designs_by_tech_nodes = []
    designs_by_customers = []

    for flow_dir in dir_list:       
        try:
            #absolute path mode
            search_path = flow_dir
            designs = os.listdir(search_path)
        except:
            #relative path mode
            search_path = os.getcwd() + "/" + flow_dir
            designs = os.listdir(search_path)
        if active_design is not None:
            designs = [active_design]

        for design in designs:
            if cmd == 'full_flow':
                if os.path.isdir(os.path.join(search_path,design)):
                    design_list.append(design)
                    design_tech_node, design_customer = extract_design_info(os.path.join(search_path,design))
                    tech_node_dict[design_tech_node].append(design)
                    customer_dict[design_customer].append(design)
            else:
                if os.path.isdir(os.path.join(search_path,design)):
                    #fatal precheck
                    fatal_path = flow_dir + "/" + design + "/" + design + ".nw" + cmd + ".out.gz.fatal"
                    fatal_path_1 = flow_dir + "/" + design + "/" + design + ".nw" + cmd + ".out.fatal"
                    if os.path.exists(fatal_path) or os.path.exists(fatal_path_1): continue
                    design_tech_node, design_customer = extract_design_info(os.path.join(search_path,design))
                    tech_node_dict[design_tech_node].append(design)
                    customer_dict[design_customer].append(design)
                    if os.path.exists(search_path + "/" + design + "/" + design + ".nw" + cmd + ".out.gz"):
                        log_path = search_path + "/" + design + "/" + design + ".nw" + cmd + ".out.gz"
                        design_flow_dict[design].append(log_path)
                    elif os.path.exists(search_path + "/" + design + "/" + design + ".nw" + cmd + ".out"):
                        log_path = search_path + "/" + design + "/" + design + ".nw" + cmd + ".out"
                        design_flow_dict[design].append(log_path)

    if cmd == 'full_flow':
        return list(set(design_list)), tech_node_dict, customer_dict

    if len(tech_nodes):
        for tech_node in tech_nodes: designs_by_tech_nodes.extend(tech_node_dict[tech_node]) 
    else: 
        designs_by_tech_nodes = design_flow_dict.keys()

    if len(customers):
        for customer in customers: designs_by_customers.extend(customer_dict[customer])
    else: 
        designs_by_customers = design_flow_dict.keys()   

    design_list = list(set(designs_by_tech_nodes).intersection(set(designs_by_customers)))

    for design in design_list:
        design_flow_dict1[design] = design_flow_dict[design]

    return design_flow_dict1, tech_node_dict, customer_dict

def extract_design_info(design_path):
    tech_node = "others"
    customer = "others"

    design_info = os.path.join(design_path,'design_info')
    if os.path.exists(design_info):
        with open(design_info, 'r') as f:
            for line in f:
                if "tech_node" in line:
                    tech_node = line.split()[1]
                elif "customer" in line:
                    customer = line.split()[1]
            #print tech_node, customer

    return tech_node, customer
"""
def flow_design_extract(flow_dir):
    cmd = "popt"

    if not os.path.isdir(flow_dir):
        error_msg = "'%s' is not a path!!" % flow_dir
        return error_found(msg=error_msg)

    flow_design_dict = {}

    try:
        #relative path mode
        search_path = os.getcwd() + "/" + flow_dir
        designs = os.listdir(search_path)
    except:
        #absolute path mode
        search_path = flow_dir
        designs = os.listdir(search_path)

    for design in designs:
        if os.path.isdir(search_path + "/" + design):
            if os.path.exists(search_path + "/" + design + "/" + design + ".nw" + cmd + ".out.gz"):
                log_path = search_path + "/" + design + "/" + design + ".nw" + cmd + ".out.gz"
                flow_design_dict[design].append(log_path)
            elif os.path.exists(search_path + "/" + design + "/" + design + ".nw" + cmd + ".out"):
                log_path = search_path + "/" + design + "/" + design + ".nw" + cmd + ".out"
                flow_design_dict[design].append(log_path)

    return flow_design_dict
"""

def compare_list(design_name, log_hb, base_name,step_name):
    find_list = []
    s = []
    base_index = 0
    step_index = 0
    log_hb = log_hb.dropna(axis=0, how="all")
    for ele in log_hb.columns:
        m = re.match(r'\(.*\)(\S+)',ele)
        if m: # step is like (2)DRC
            col_step = m.group(1)
        else: # step with no step prefix
            col_step = ele
        if base_name.lower() == col_step.lower():
            if(len(s)==0):
                s.append(base_name)
            else:
                s.pop()
            base_index = log_hb.columns.tolist().index(ele)
        if step_name.lower() == col_step.lower():
            step_index = log_hb.columns.tolist().index(ele)
            if(len(s)!=0):
                find_list.append([base_index,step_index])
                s.pop()
    return find_list

def step_qor_compare(design_name, log_hb, base_name,step_name):
    step_qor_info = defaultdict(list)
    step_found = False
    log_hb = log_hb.dropna(axis=0, how="all")
    compare_find_list = compare_list(design_name, log_hb, base_name,step_name)
    for cfl in compare_find_list:
        compare_qor_array = log_hb.iloc[:,cfl[1]]
        base_qor_array = log_hb.iloc[:,cfl[0]]
        step_qor_array = []
        for index in compare_qor_array.index:               
            try:
                base_val = float(base_qor_array[index])
                comp_val = float(compare_qor_array[index])
            except ValueError: #skip N/A value compare
                continue

            if base_val == 0 and comp_val == 0:
                change_pct = format(0,".2f")
            elif base_val == 0:
                change_pct = format(100,".2f")
            elif comp_val == 0:
                change_pct = format(-100,".2f")
            else:
                factor = 1
                if index == "FREQUENCY_GHz":
                    factor = -1
                change_pct = format((comp_val-base_val)*100*factor/base_val, ".2f")

            step_qor_info[index].append([base_qor_array.name, base_val, compare_qor_array.name, comp_val, change_pct])
            step_qor_array.append(change_pct)

    return step_qor_info

def step_qor_analysis(design_name, log_hb, base_step):
    step_qor_info = defaultdict(list)
    step_found = False
    log_hb = log_hb.dropna(axis=0, how="all")
    for ele in log_hb.columns:
        m = re.match(r'\(.*\)(\S+)',ele)
        if m: # step is like (2)DRC
            col_step = m.group(1)
        else: # step with no step prefix
            col_step = ele

        if base_step.lower() == col_step.lower():
            step_found = True
            step_index = log_hb.columns.tolist().index(ele)
            compare_qor_array = log_hb.iloc[:,step_index]
            base_qor_array = log_hb.iloc[:,step_index-1]
            step_qor_array = []
            #Leo to refactoring
            for index in compare_qor_array.index:
                try:
                    base_val = float(base_qor_array[index])
                    comp_val = float(compare_qor_array[index])
                except ValueError: #skip N/A value compare
                    continue

                if base_val == 0 and comp_val == 0:
                    change_pct = format(0,".2f")
                elif base_val == 0:
                    change_pct = format(100,".2f")
                elif comp_val == 0:
                    change_pct = format(-100,".2f")
                else:
                    factor = 1
                    if index == "FREQUENCY_GHz":
                        factor = -1
                    change_pct = format((comp_val-base_val)*100*factor/base_val, ".2f")

                step_qor_info[index].append([base_qor_array.name, base_val, compare_qor_array.name, comp_val, change_pct])
                step_qor_array.append(change_pct)

    return step_qor_info

def step_qor_analysis2(design_name, log_hb, log_hb2, base_step):
    step_qor_info = defaultdict(list)
    step_found = False
    log_hb = log_hb.dropna(axis=0, how="all")
    log_hb2 = log_hb2.dropna(axis=0, how="all")
    for ele,ele2 in zip(log_hb.columns,log_hb2.columns):
        m = re.match(r'\(.*\)(\S+)',ele)
        if m: # step is like (2)DRC
            col_step = m.group(1)
        else: # step with no step prefix
            col_step = ele

        if base_step.lower() == col_step.lower():
            step_found = True
            step_index = log_hb.columns.tolist().index(ele)
            compare_qor_array = log_hb2.iloc[:,step_index]
            base_qor_array = log_hb.iloc[:,step_index]
            step_qor_array = []
            #Leo to refactoring
            for index in compare_qor_array.index:   
                try:            
                    base_val = float(base_qor_array[index])
                    comp_val = float(compare_qor_array[index])
                except ValueError: #skip N/A value compare
                    continue

                if base_val == 0 and comp_val == 0:
                    change_pct = format(0,".2f")
                elif base_val == 0:
                    change_pct = format(100,".2f")
                elif comp_val == 0:
                    change_pct = format(-100,".2f")
                else:
                    factor = 1
                    if index == "FREQUENCY_GHz":
                        factor = -1
                    change_pct = format((comp_val-base_val)*100*factor/base_val, ".2f")

                step_qor_info[index].append([base_qor_array.name, base_val, compare_qor_array.name, comp_val, change_pct])
                step_qor_array.append(change_pct)

    return step_qor_info


def trajectory_list(design_name, log_hb):
    find_list = []
    s = []
    base_index = 0
    step_index = 0
    log_hb = log_hb.dropna(axis=0, how="all")
    for ele in log_hb.columns:
        m = re.match(r'\(.*\)(\S+)',ele)
        if m:
            col_step = m.group(1)
        else:
            col_step = ele
        if col_step:
            # col_step = m.group(1)
            # if step_name.lower() == col_step.lower():
            step_index = log_hb.columns.tolist().index(ele)
            # print "step_index is",step_index
            base_index = step_index-1
            if(base_index>=0):
                find_list.append([step_index-1,step_index])
    return find_list

def step_qor_trajectory(design_name, log_hb, bound):
    step_qor_info = defaultdict(list)
    step_found = False
    log_hb = log_hb.dropna(axis=0, how="all")
    compare_find_list = trajectory_list(design_name, log_hb)
    # print "compare_list is",compare_find_list
    for cfl in compare_find_list:
        compare_qor_array = log_hb.iloc[:,cfl[1]]
        base_qor_array = log_hb.iloc[:,cfl[0]]
        step_qor_array = []
        for index in compare_qor_array.index:               
            try:
                base_val = float(base_qor_array[index])
                comp_val = float(compare_qor_array[index])
            except ValueError: #skip N/A value compare
                continue

            if base_val == 0 and comp_val == 0:
                change_pct = format(0,".2f")
            elif base_val == 0:
                change_pct = format(100,".2f")
            elif comp_val == 0:
                change_pct = format(-100,".2f")
            else:
                change_pct = format((comp_val-base_val)*100/base_val, ".2f")

            if float(change_pct)>bound:
                step_qor_info[index].append([base_qor_array.name, base_val, compare_qor_array.name, comp_val, change_pct])
                step_qor_array.append(change_pct)
        
    # print "design name is ",design_name
    # print "step_qor_info is",step_qor_info
    return step_qor_info

def generate_step_dict(pattern, dir_list, cmd, compress, tech_nodes=[], customers=[]):
    mgr = MyManager()
    mgr.start()
    steps_list_dict = mgr.defaultdict(list)
    threads = []

    if pattern == "FULL_FLOW_PPA":
        # print design
        design_list = []
        for dir in dir_list:
            design_list.extend(os.listdir(dir))
        design_list = list(set(design_list))
        for design in design_list:
            # print design
            input_list = [dir_list[0] +'/'+design]
            # log_list = input_list
            p = Process(target=generate_step_list, args=(input_list, pattern, compress, steps_list_dict))
            threads.append(p)
    else:
        design_flow_dict, tech_node_dict, customer_dict = design_flow_extract(dir_list=dir_list, cmd=cmd, tech_nodes=tech_nodes, customers=customers)
        for design, log_list in design_flow_dict.items():
            p = Process(target=generate_step_list, args=(log_list, 'all', compress, steps_list_dict))
            threads.append(p)   

    nloops = range(len(threads))
    for i in nloops:
        threads[i].start()
    for i in nloops:
        threads[i].join()
        
    steps_list_dict = dict(steps_list_dict)
    try:
        del(steps_list_dict['ELAPSE_MEM'])
        del(steps_list_dict['FUNC_DIST'])
    except KeyError:
        pass

    for pattern, step_list in steps_list_dict.items():
        tmp = list(set(step_list))
        steps_list_dict[pattern] = tmp

    return steps_list_dict

def generate_step_list(log_list, pattern, compress, steps_list_dict):
    qp = QorProfiler(input_list=log_list, pattern=pattern, compress=compress)
    qp.generate_profile()

    for pattern in qp.qor_metrics_dict.keys():
        step_list = qp.steps_dict[pattern][0]
        # print type(steps_list_dict[pattern])
        tmp = list(steps_list_dict[pattern])
        tmp.extend(remove_step_prefix(step_list))
        # print tmp
        steps_list_dict[pattern] = tmp
    # print steps_list_dict

def generate_sqb_step_pair(design, log_list, pattern, cmd, compress, dir_list, dir_list2, step_name, step_qor_info):
    qp = QorProfiler(input_list=log_list, compress=compress)
    if pattern == "PREROUTE":
        log_hb = qp.preroute_profiler(log_list[0])
    elif pattern == "GROPT":
        log_hb = qp.gropt_profiler(log_list[0])
    elif pattern == "ROPT":
        log_hb = qp.ropt_profiler(log_list[0])
    elif pattern == "NPO":
        log_hb = qp.npo_profiler(log_list[0])
    elif pattern == "PREROUTE_STG":
        log_hb = qp.preroute_stg_profiler(log_list[0])

    if dir_list!=dir_list2:
        design_flow_dict2, _ , _= design_flow_extract(dir_list2, cmd=cmd)
        log_list2 = design_flow_dict2[design]
        if(len(log_list2)==1):
            # print log_list2
            qp2 = QorProfiler(input_list=log_list2, compress=compress)
            if pattern =="PREROUTE_STG":
                log_hb2 = qp2.preroute_stg_profiler(log_list2[0])
                step_qor_info[design] = step_qor_analysis2(design, log_hb, log_hb2, step_name)
            else:
                step_qor_info[design] = step_qor_analysis(design, log_hb, step_name)

    else:
        # print len(second_dir)
        step_qor_info[design] = step_qor_analysis(design, log_hb, step_name)    

def generate_sqb_step_pair1(design, input_list, pattern, dir_list, dir_list2, step_name, step_qor_info):
    qp = QorProfiler(input_list=input_list, pattern=pattern)
    log_hb = qp.full_flow_ppa_profiler(input_list[0])

    if dir_list!=dir_list2:
        input_list2 = [dir+'/'+design for dir in dir_list2]
        log_list2 = input_list2
        qp2 = QorProfiler(input_list=input_list2, pattern=pattern)
        log_hb2 = qp.full_flow_ppa_profiler(input_list2[0])
        step_qor_info[design] = step_qor_analysis2(design, log_hb, log_hb2, step_name)
    else:
        # print len(second_dir)
        step_qor_info[design] = step_qor_analysis(design, log_hb, step_name)

def generate_sqc_step_pair(design, log_list, pattern, compress, base_name, step_name, step_qor_info):
    qp = QorProfiler(input_list=log_list, compress=compress)
    if pattern == "PREROUTE":
        log_hb = qp.preroute_profiler(log_list[0])
    elif pattern == "GROPT":
        log_hb = qp.gropt_profiler(log_list[0])
    elif pattern == "ROPT":
        log_hb = qp.ropt_profiler(log_list[0])
    elif pattern == "NPO":
        log_hb = qp.npo_profiler(log_list[0])
    elif pattern == "PREROUTE_STG":
        log_hb = qp.preroute_stg_profiler(log_list[0])
    elif pattern == "FULL_FLOW_PPA":
        log_hb = qp.full_flow_ppa_profiler(input_list[0])

    step_qor_info[design] = step_qor_compare(design, log_hb,base_name,step_name)    

def generate_sqt_step_pair(design, log_list, pattern, compress, bound, step_qor_info):
    qp = QorProfiler(input_list=log_list, compress=compress)
    if pattern == "PREROUTE":
        log_hb = qp.preroute_profiler(log_list[0])
    elif pattern == "GROPT":
        log_hb = qp.gropt_profiler(log_list[0])
    elif pattern == "ROPT":
        log_hb = qp.ropt_profiler(log_list[0])
    elif pattern == "NPO":
        log_hb = qp.npo_profiler(log_list[0])
    elif pattern == "PREROUTE_STG":
        log_hb = qp.preroute_stg_profiler(log_list[0])
    elif pattern == "FULL_FLOW_PPA":
        log_hb = qp.full_flow_ppa_profiler(log_list[0])

    step_qor_info[design] = step_qor_trajectory(design, log_hb,float(bound))


def sub_qp_process(design, log_list, compress, pattern, script_list, log_name_list, design_qor):
    qp = QorProfiler(input_list=log_list, compress=compress, pattern=pattern, script_list=script_list)
    qp.generate_profile()
    # wrong dict assignment method under multiprocess
    """
    design_qor[design]['qor_metrics_dict'], design_qor[design]['step_qor_dict'], design_qor[design]['auto_skip_dict'], design_qor[design]['step_match_dict'], design_qor[design]['steps_dict'] = \
    qp.qor_metrics_dict, qp.step_qor_dict, qp.auto_skip_dict, qp.step_match_dict, qp.steps_dict
    design_qor[design]['log_list'], design_qor[design]['log_name_list']= log_list, log_name_list
    """
    # correct assignment method
    design_qor[design] = {
        'qor_metrics_dict':qp.qor_metrics_dict,
        'step_qor_dict': qp.step_qor_dict,
        'auto_skip_dict': qp.auto_skip_dict,
        'step_match_dict': qp.step_match_dict,
        'steps_dict': qp.steps_dict,
        'log_list': log_list,
        'log_name_list': log_name_list,
    }
