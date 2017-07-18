#!/remote/us01home40/phyan/depot/Python-2.7.11/bin/python
import sys 
import os
import copy
import commands
import re
import getpass
import datetime
import MySQLdb
from urllib import urlencode
from werkzeug import MultiDict
from collections import defaultdict
#data analysis
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt

from socket import error as SocketError
import errno

from flask import Flask, request, render_template, Response, jsonify
import json
#heartbeat extraction
#from preroute import pr_log_extractor
from qorProfiler import QorProfiler

app = Flask(__name__)

#==========================
# global var init
#==========================
COLOR_LIST = ["#FF6384","#36A2EB","#fdb45c","#46bfbd","#99CC33","#CC9933"]
#COLOR_LIST = ["#FF6384","#36A2EB","#FFCE56","#99CC33","#CC9933"]
METRICS_PROPERTY_DICT = {
	"PREROUTE":
		{"ELAPSE_TIME" : [1, 'linear'], "WNS" : [2, 'logarithmic'], "TNS" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "MAXTRAN" : [5, 'logarithmic'],
		 "MAXCAP" : [6, 'logarithmic'], "BUFFCNT" : [7, 'linear'], "INVCNT" : [8, 'linear'], "LVTCNT" : [9, 'linear'],
		  "LVTPCNT" : [10, 'linear'], "MEM" : [11, 'linear'], "LEAKPWR" : [12, 'linear'], "WHNS" : [13, 'linear']},
	"PREROUTE_STG":
		{"ELAPSE_TIME" : [1, 'linear'], "WNS" : [2, 'logarithmic'], "TNS" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "MAXTRAN" : [5, 'logarithmic'],
		 "MAXCAP" : [6, 'logarithmic'], "BUFFCNT" : [7, 'linear'], "INVCNT" : [8, 'linear'], "LVTCNT" : [9, 'linear'],
		  "LVTPCNT" : [10, 'linear'], "MEM" : [11, 'linear'], "LEAKPWR" : [12, 'linear'], "WHNS" : [13, 'linear']},
	"ROPT":
		{"RSETUP" : [1, 'logarithmic'], "SETUP_COST" : [2, 'logarithmic'], "RHOLD" : [3, 'logarithmic'], "HOLD_COST" : [4, 'linear'], "RLDRC_MT" : [5, 'logarithmic'],
	    "RLDRC_MC" : [6, 'logarithmic'], "LDRC_COST" : [7, 'logarithmic'], "AREA" : [8, 'linear'], "LEAKAGE" : [9, 'linear'], "ELAPSE" : [10, 'linear']},
    "GROPT":
		{"RSETUP" : [1, 'logarithmic'], "SETUP_COST" : [2, 'logarithmic'], "RHOLD" : [3, 'logarithmic'], "HOLD_COST" : [4, 'linear'], "RLDRC_MT" : [5, 'logarithmic'],
	    "RLDRC_MC" : [6, 'logarithmic'], "LDRC_COST" : [7, 'logarithmic'], "AREA" : [8, 'linear'], "LEAKAGE" : [9, 'linear'], "ELAPSE" : [10, 'linear']},
    "NPO":
		{"RSETUP" : [1, 'logarithmic'], "SETUP_COST" : [2, 'logarithmic'], "RHOLD" : [3, 'logarithmic'], "HOLD_COST" : [4, 'linear'], "RLDRC_MT" : [5, 'logarithmic'],
	    "RLDRC_MC" : [6, 'logarithmic'], "LDRC_COST" : [7, 'logarithmic'], "AREA" : [8, 'linear'], "LEAKAGE" : [9, 'linear'], "ELAPSE" : [10, 'linear']}
}

METRICS_ORDER_DICT = {
	"PREROUTE": ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "AREA", "MEM", "ELAPSE_TIME", "LVTCNT", "LVTPCNT", "LEAKPWR", "WHNS"],
	"PREROUTE_STG": ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "AREA", "MEM", "ELAPSE_TIME", "LVTCNT", "LVTPCNT", "LEAKPWR", "WHNS"],
	"ROPT": ["RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"GROPT": ["RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"NPO": ["RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
}

PRS_STAGE = ['icpopt', 'iccopt']
CALC = [3600, 60, 1]
POINT_DICT_DEFAULT = {"prev_d": -1, "prev_p": -1, "crnt_d": -1, "crnt_p": -1}
DUO_METRICS = {
	"cell": ['STEP','EXISTENCE','REF','LOC','PWR','DEF'],
	"path": ['STEP','EXISTENCE','SLACK'],
	"net": ['STEP','TRANS','TRANS_CON','FANOUT'],
	"cong": ['STEP']
}
MAX_INPUT_NUM = 15
LOG_DUMMY = "/u/phyan/workspace/python/qor_analyzer/script/log_dummy"
url_list = []
input_num = 0

@app.route('/')
@app.route('/index')
@app.route('/index/')
def index():
	#username = request.remote_user 
	username = "phyan" #for debug use
	usr_info = os.popen("ph email=" + username)
	f = usr_info.readlines()
	active_duo = True
	for line in f:
		if "cc_name" in line and "GTS" in line:
			active_duo = False

	mode = request.args.get('mode')
	compress = request.args.get('compress')
	input_num = request.args.get('input_num')
	script_num = request.args.get('script_num')

	input_list = []
	script_list = []
	if input_num is not None and input_num is not "None":
		for i in range(1,int(input_num)+1):
			input_list.append(str(request.args.get('input'+str(i))))
	if script_num is not None and input_num is not "None":
		for i in range(1,int(script_num)+1):
			script_list.append(str(request.args.get('script'+str(i))))

	return render_template('index.html', user=request.remote_user, active_duo=active_duo, mode=mode, compress=compress, input_num=input_num, input_list=input_list, script_num=script_num, script_list=script_list)

@app.route('/analysis_tricks')
def qor_analysis_tricks():
	#username = "phyan" #for debug use
	return render_template('analysis_tricks.html', user=request.remote_user)

@app.route('/analysis_sqb', methods=['POST'])
def step_qor_benefit_analysis():
	flow_metrics = {} # flow/design table
	flow_qor_metrics = {} #design/qor-per-flow table
	step_qor_dict = {}
	design_chart_dict = {}
	step_name = request.form['step_name']
	flow_dir = request.form['flow_dir']
	stage = request.form['stage']
	pattern = request.form['pattern']
	cmd = stage[-4:].strip().lower()
	dir_list = [flow_dir]
	mode = "flow"
	compress = True
	step_qor_info = {}
	list_mode = False
	record_usage(mode='sqb')

	if step_name == "":
		list_mode = True

	for dir in dir_list:
		if not os.path.isdir(dir):
			error_msg = "'%s' is not a vaild path!!" % dir
			return jsonify({
				'result': "fail",
				'msg': error_msg,
			})

	if list_mode:
		steps_list_dict = defaultdict(list)
		design_flow_dict = design_flow_extract(dir_list, cmd=cmd)
		for design, log_list in design_flow_dict.items():
			qp = QorProfiler(log_list=log_list, compress=compress)
			qp.generate_profile()

			for pattern in qp.qor_metrics_dict.keys():
				step_list = qp.steps_dict[pattern][0]
				steps_list_dict[pattern].extend(remove_step_prefix(step_list))
			
		for pattern, step_list in steps_list_dict.items():
			steps_list_dict[pattern] = list(set(step_list))
		return jsonify({
			'result': "success",
			'steps_list_dict': json.dumps(steps_list_dict),
		})

	else:
		if pattern == "PREROUTE":
			default_metrics = "WNS"
		else: 
			default_metrics = "RSETUP"
			
		design_flow_dict = design_flow_extract(dir_list, cmd=cmd)
		for design, log_list in design_flow_dict.items():
			qp = QorProfiler(log_list=log_list, compress=compress)
			if pattern == "PREROUTE":
				log_hb = qp.preroute_profiler(log_list[0])
			elif pattern == "GROPT":
				log_hb = qp.gropt_profiler(log_list[0])
			elif pattern == "ROPT":
				log_hb = qp.ropt_profiler(log_list[0])
			elif pattern == "NPO":
				log_hb = qp.npo_profiler(log_list[0])

			step_qor_info[design] = step_qor_analysis(design, log_hb, step_name)

		step_qor_info = pd.DataFrame(step_qor_info)
		step_qor_info = step_qor_info.fillna(value="null").to_dict(orient="index")

		return jsonify({
			'result': "success",
			'step_qor_info': json.dumps(step_qor_info),
			'default_metrics': default_metrics,
			#'step_qor_info': {"Daedalus_TS16FFP": [["(27P)SIZE3", 0.346, "(28P)SIZE4", 0.346, "0.00%"]], "Icarus": [["(27P)SIZE3", 0.051, "(28P)SIZE4", 0.049, "-4.08%"], ["(36P)SIZE3", 0.053, "(37P)SIZE4", 0.053, "0.00%"]]},
	        #'step_qor_result': step_qor_result.to_dict(orient="index")["WNS"]
		})

def step_qor_analysis(design_name, log_hb, base_step):
	step_qor_info = defaultdict(list)
	step_found = False
	log_hb = log_hb.dropna(axis=0, how="all")
	for ele in log_hb.columns:
		m = re.match(r'\(.*\)(\S+)',ele)
		if m:
			col_step = m.group(1)
			if base_step.lower() == col_step.lower():
				step_found = True
				step_index = log_hb.columns.tolist().index(ele)
				compare_qor_array = log_hb.iloc[:,step_index]
				base_qor_array = log_hb.iloc[:,step_index-1]
				step_qor_array = []
				#Leo to refactoring
				for index in compare_qor_array.index:				
					base_val = float(base_qor_array[index])
					comp_val = float(compare_qor_array[index])

					if base_val == 0 and comp_val == 0:
						change_pct = format(0,".2f")
					elif base_val == 0:
						change_pct = format(100,".2f")
					elif comp_val == 0:
						change_pct = format(-100,".2f")
					else:
						change_pct = format((comp_val-base_val)*100/comp_val, ".2f")

					step_qor_info[index].append([base_qor_array.name, base_val, compare_qor_array.name, comp_val, change_pct])
					step_qor_array.append(change_pct)

	return step_qor_info
	
def remove_step_prefix(step_list):
	pure_step_list = []
	for step in step_list:
		m = re.match(r'\(.*\)(\S+)',step)
		if m:
			pure_step = m.group(1)
			pure_step_list.append(pure_step)
	return pure_step_list

@app.route('/analysis_sqc', methods=['POST'])
def step_qor_compare_analysis():
	flow_metrics = {} # flow/design table
	flow_qor_metrics = {} #design/qor-per-flow table
	step_qor_dict = {}
	design_chart_dict = {}
	base_name = request.form['base_name']
	step_name = request.form['step_name']
	flow_dir = request.form['flow_dir']
	stage = request.form['stage']
	pattern = request.form['pattern']
	cmd = stage[-4:].strip().lower()
	dir_list = [flow_dir]
	mode = "flow"
	compress = True
	step_qor_info = {}
	list_mode = False
	record_usage(mode='sqc')

	if base_name == "" and step_name == "":
		list_mode = True
    
	for dir in dir_list:
		if not os.path.isdir(dir):
			error_msg = "'%s' is not a vaild path!!" % dir
			return jsonify({
				'result': "fail",
				'msg': error_msg,
			})

	if list_mode:
		steps_list_dict = defaultdict(list)
		design_flow_dict = design_flow_extract(dir_list, cmd=cmd)
		for design, log_list in design_flow_dict.items():
			qp = QorProfiler(log_list=log_list, compress=compress)
			qp.generate_profile()

			for pattern in qp.qor_metrics_dict.keys():
				step_list = qp.steps_dict[pattern][0]
				steps_list_dict[pattern].extend(remove_step_prefix(step_list))
			
		for pattern, step_list in steps_list_dict.items():
			steps_list_dict[pattern] = list(set(step_list))
		return jsonify({
			'result': "success",
			'steps_list_dict': json.dumps(steps_list_dict),
		})

	else:
		if pattern == "PREROUTE":
			default_metrics = "WNS"
		else: 
			default_metrics = "RSETUP"
		design_flow_dict = design_flow_extract(dir_list, cmd=cmd)
		for design, log_list in design_flow_dict.items():
			qp = QorProfiler(log_list=log_list, compress=compress)
			if pattern == "PREROUTE":
				log_hb = qp.preroute_profiler(log_list[0])
			elif pattern == "GROPT":
				log_hb = qp.gropt_profiler(log_list[0])
			elif pattern == "ROPT":
				log_hb = qp.ropt_profiler(log_list[0])
			elif pattern == "NPO":
				log_hb = qp.npo_profiler(log_list[0])
			step_qor_info[design] = step_qor_compare(design, log_hb, base_name,step_name)

		step_qor_info=pd.DataFrame(step_qor_info)
		step_qor_info=step_qor_info.fillna(value="null").to_dict(orient="index")

		return	jsonify({
		'result':	"success",
		'step_qor_info':	json.dumps(step_qor_info),
		'default_metrics':	default_metrics,
		})

def compare_list(design_name, log_hb, base_name,step_name):
	find_list = []
	s = []
	base_index = 0
	step_index = 0
	log_hb = log_hb.dropna(axis=0, how="all")
	for ele in log_hb.columns:
		m = re.match(r'\(.*\)(\S+)',ele)
		if m:
			col_step = m.group(1)
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
			base_val = float(base_qor_array[index])
			comp_val = float(compare_qor_array[index])

			if base_val == 0 and comp_val == 0:
				change_pct = format(0,".2f")
			elif base_val == 0:
				change_pct = format(100,".2f")
			elif comp_val == 0:
				change_pct = format(-100,".2f")
			else:
				change_pct = format((comp_val-base_val)*100/comp_val, ".2f")

			step_qor_info[index].append([base_qor_array.name, base_val, compare_qor_array.name, comp_val, change_pct])
			step_qor_array.append(change_pct)

	return step_qor_info

@app.route('/analysis_sqt', methods=['POST'])
def step_trajectory_analysis():
	flow_metrics = {} # flow/design table
	flow_qor_metrics = {} #design/qor-per-flow table
	step_qor_dict = {}
	design_chart_dict = {}
	flow_dir = request.form['flow_dir']
	stage = request.form['stage']
	pattern = request.form['pattern']
	bound = request.form['bound']
	cmd = stage[-4:].strip().lower()
	dir_list = [flow_dir]
	mode = "flow"
	compress = True
	step_qor_info = {}
	list_mode = False
	record_usage(mode='sqt')

	if bound == "":
		list_mode = True

	for dir in dir_list:
		if not os.path.isdir(dir):
			error_msg = "'%s' is not a vaild path!!" % dir
			return jsonify({
				'result': "fail",
				'msg': error_msg,
			})

	if list_mode:
		steps_list_dict = defaultdict(list)
		design_flow_dict = design_flow_extract(dir_list, cmd=cmd)
		for design, log_list in design_flow_dict.items():
			qp = QorProfiler(log_list=log_list, compress=compress)
			qp.generate_profile()

			for pattern in qp.qor_metrics_dict.keys():
				step_list = qp.steps_dict[pattern][0]
				steps_list_dict[pattern].extend(remove_step_prefix(step_list))
			
		for pattern, step_list in steps_list_dict.items():
			steps_list_dict[pattern] = list(set(step_list))
		return jsonify({
			'result': "success",
			'steps_list_dict': json.dumps(steps_list_dict),
		})

	else:
		if pattern == "PREROUTE":
			default_metrics = "WNS"
		else: 
			default_metrics = "RSETUP"
			
		design_flow_dict = design_flow_extract(dir_list, cmd=cmd)
		for design, log_list in design_flow_dict.items():
			qp = QorProfiler(log_list=log_list, compress=compress)
			if pattern == "PREROUTE":
				log_hb = qp.preroute_profiler(log_list[0])
			elif pattern == "GROPT":
				log_hb = qp.gropt_profiler(log_list[0])
			elif pattern == "ROPT":
				log_hb = qp.ropt_profiler(log_list[0])
			elif pattern == "NPO":
				log_hb = qp.npo_profiler(log_list[0])

			step_qor_info[design] = step_qor_trajectory(design, log_hb, float(bound))

		step_qor_info = pd.DataFrame(step_qor_info)
		step_qor_info = step_qor_info.fillna(value="null").to_dict(orient="index")

		return jsonify({
			'result': "success",
			'step_qor_info': json.dumps(step_qor_info),
			'default_metrics': default_metrics,
			#'step_qor_info': {"Daedalus_TS16FFP": [["(27P)SIZE3", 0.346, "(28P)SIZE4", 0.346, "0.00%"]], "Icarus": [["(27P)SIZE3", 0.051, "(28P)SIZE4", 0.049, "-4.08%"], ["(36P)SIZE3", 0.053, "(37P)SIZE4", 0.053, "0.00%"]]},
	        #'step_qor_result': step_qor_result.to_dict(orient="index")["WNS"]
		})

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
			# if step_name.lower() == col_step.lower():
			step_index = log_hb.columns.tolist().index(ele)
			base_index = step_index-1
			if(base_index>=0):
				find_list.append([step_index-1,step_index])
	return find_list

def step_qor_trajectory(design_name, log_hb, bound):
	step_qor_info = defaultdict(list)
	step_found = False
	log_hb = log_hb.dropna(axis=0, how="all")
	compare_find_list = trajectory_list(design_name, log_hb)
	for cfl in compare_find_list:
		compare_qor_array = log_hb.iloc[:,cfl[1]]
		base_qor_array = log_hb.iloc[:,cfl[0]]
		step_qor_array = []
		for index in compare_qor_array.index:				
			base_val = float(base_qor_array[index])
			comp_val = float(compare_qor_array[index])

			if base_val == 0 and comp_val == 0:
				change_pct = format(0,".2f")
			elif base_val == 0:
				change_pct = format(100,".2f")
			elif comp_val == 0:
				change_pct = format(-100,".2f")
			else:
				change_pct = format((comp_val-base_val)*100/comp_val, ".2f")

			if float(change_pct)>bound:
				step_qor_info[index].append([base_qor_array.name, base_val, compare_qor_array.name, comp_val, change_pct])
				step_qor_array.append(change_pct)
		
	# print "design name is ",design_name
	# print "step_qor_info is",step_qor_info
	return step_qor_info

@app.route('/analysis_sqa', methods=['POST'])
def stage_based_qor_analysis():
	base_dir = request.form['flowb_dir']
	compare_dir = request.form['flowc_dir']
	dir_list = [base_dir,compare_dir]
	design_flow_dict = design_flow_extract(dir_list)
	mean_qor = calc_qor_mean_by_stage(design_flow_dict)

	return render_template('index.html', user="phyan", active_duo=False)
	return jsonify({
		'mean_qor': mean_qor,
		#'step_qor_info': {"Daedalus_TS16FFP": [["(27P)SIZE3", 0.346, "(28P)SIZE4", 0.346, "0.00%"]], "Icarus": [["(27P)SIZE3", 0.051, "(28P)SIZE4", 0.049, "-4.08%"], ["(36P)SIZE3", 0.053, "(37P)SIZE4", 0.053, "0.00%"]]},
	    'step_qor_result': step_qor_result.to_dict(orient="index")["WNS"]
	})

@app.route('/profile', methods=['POST','GET'])
def qor_profile():
	base_url = request.base_url
	if request.method == 'POST':		
		mode = request.form['selected-mode']
		if mode == "":
			error_msg = "Please select a mode!"
			return error_found(msg=error_msg)

		if mode == "log" or mode == "flow":
			point_dict = copy.copy(POINT_DICT_DEFAULT)
			compress = int(request.form['compress-mode'])
			try:
				input_num = int(request.form['param-num'])
				if input_num > MAX_INPUT_NUM:
					error_msg = "Number of inputs should not larger than %d..." %MAX_INPUT_NUM
					return error_found(msg=error_msg)
			except:
				error_msg = "Please enter number of inputs!"
				return error_found(msg=error_msg)	

			script_num = int(request.form['script-num'])		
			if script_num > 0:
				pattern = "USER"
				script_list = []
				for i in range(1,script_num+1):
					path_orig = request.form['script'+str(i)]
					path = path_translate(path_orig)
					if path_orig == "":
						error_msg = "Script %d should not be empty!" % i
						return error_found(msg=error_msg)	
					if not os.path.exists(path):
						error_msg = "Script%d: '%s' does not exist!! (Maybe on secure disk?? Please use terminal version.)" % (i, path_orig)
						return error_found(msg=error_msg)

					script_list.append(str(path))
			else:
				pattern = "all"
				script_list = []

			input_list = []
			for i in range(1,input_num+1):
				path_orig = request.form['input'+str(i)]
				path = path_translate(path_orig)
				if path_orig == "":
					error_msg = "Input %d should not be empty!" % i
					return error_found(msg=error_msg)	
				if not os.path.exists(path):
					error_msg = "Input%d: '%s' does not exist!! (Maybe on secure disk?? Please use terminal version.)" % (i, path_orig)
					return error_found(msg=error_msg)

				input_list.append(str(path))
			
			#record usage after user provides correct inputs
			record_usage(mode=mode+'_'+str(compress))
			return qor_profile_main(base_url=base_url, mode=mode, compress=compress, input_list=input_list, point_dict=point_dict, pattern=pattern, script_list=script_list)
		elif mode == "checkpoint":
			record_usage(mode=mode)
			dir_path = request.form['param-2']

			return duo_analysis_main(mode=mode, dir_path=dir_path)

	elif request.method == 'GET':
		point_dict = copy.copy(POINT_DICT_DEFAULT)
		mutable_dict = request.args.copy()
		if mutable_dict.__len__():
			mode = mutable_dict.get('mode')
			if mode == "checkpoint":
				dir_path = mutable_dict.get('dir_path')
				active_design = mutable_dict.get('active_design')
				record_usage(mode=mode)

				return duo_analysis_main(mode=mode, dir_path=dir_path, active_duo=active_design)
			else:
				input_list = mutable_dict.getlist('input_list')
				input_list = [str(inp) for inp in input_list]
				script_list = mutable_dict.getlist('script_list')
				script_list = [str(script) for script in script_list]
				compress = int(mutable_dict.get('compress'))
				cmd = mutable_dict.get('cmd')
				active_design = mutable_dict.get('active_design')
				active_metrics = mutable_dict.get('active_metrics')
				active_pattern = mutable_dict.get('active_pattern')

				pattern = str(mutable_dict.get("pattern"))
				point_dict["prev_d"] = mutable_dict.get('prev_d')
				point_dict["prev_p"] = mutable_dict.get('prev_p')
				point_dict["crnt_d"] = mutable_dict.get('crnt_d')
				point_dict["crnt_p"] = mutable_dict.get('crnt_p')
				record_usage(mode=mode+'_'+str(compress))
				return qor_profile_main(base_url=base_url, mode=mode, compress=compress, input_list=input_list, cmd=cmd, active_pattern=active_pattern, active_design=active_design,active_metrics=active_metrics, point_dict=point_dict, pattern=pattern, script_list=script_list)
		else:
			return render_template('index.html')	

@app.route('/jump_profile', methods=['POST'])
def jump_profile():
	first_name = request.form.get('first_name')
	first_dir = request.form.get('first_dir')
	first_pattern = request.form.get('first_pattern')
	first_stage = request.form.get('first_stage')
	second_name = request.form.get('second_name')
	single_name = request.form.get('single_name')
	mode = request.form.get('mode')
	return render_template('analysis_tricks.html', mode = mode, single_name = single_name, step_name = first_name, comp_name=second_name, flow_dir = first_dir, stage = first_stage, pattern = first_pattern)

@app.route('/display_design_chart', methods=['POST'])
def qor_profile_by_design():
	mutable_dict = request.form.copy()
	mode = "flow"
	active_design = mutable_dict.get("active_design")
	pattern = str(mutable_dict.get("pattern"))
	#print pattern
	script_list = mutable_dict.getlist("script_list[]")
	dir_list = mutable_dict.getlist("dir_list[]")
	flow_list = []
	for dir in dir_list:
		if dir.split('/')[-1] != '':
			flow_list.append(dir.split('/')[-1])
		else:
			flow_list.append(dir.split('/')[-2])

	cmd = mutable_dict.get("cmd")
	compress = bool(int(mutable_dict.get("compress")))
	design_flow_dict = design_flow_extract(dir_list=dir_list, cmd=cmd, active_design=active_design)
	log_list = design_flow_dict[active_design]
	log_name_list = [log.split('/')[-1] for log in log_list]

	qp = QorProfiler(log_list=log_list, compress=compress, pattern=pattern, script_list=script_list)
	qp.generate_profile()

	metrics_order_dict = copy.copy(METRICS_ORDER_DICT)
	metrics_property_dict = copy.copy(METRICS_PROPERTY_DICT)

	for pattern in qp.qor_metrics_dict.keys():
		if "USER" in pattern:			
			metrics_order_dict[pattern] = qp.metrics_order[pattern]			
			metrics_property_dict[pattern] = defaultdict(list)
			i = 1
			for metrics in metrics_order_dict[pattern]:
				metrics_property_dict[pattern][metrics] = [i, "linear"]
				i += 1
			metrics_property_dict[pattern] = dict(metrics_property_dict[pattern])
	#print metrics_order_dict, metrics_property_dict

	return jsonify({
		'qor_metrics_dict': qp.qor_metrics_dict, 
		'step_qor_dict': qp.step_qor_dict, 
		'auto_skip_dict': qp.auto_skip_dict, 
		'step_match_dict': qp.step_match_dict, 
		#'log_list': log_list, 
		'metrics_order_dict': metrics_order_dict, 
		'metrics_property_dict': metrics_property_dict,
		#'url': url, 
		#'point_dict': point_dict,
		'steps_dict': qp.steps_dict,
		'log_list': log_list,
		'log_name_list': log_name_list,
		'flow_list': flow_list,
		'color_list': COLOR_LIST,
	})

@app.route('/display_metrics_chart', methods=['POST'])
def qor_profile_by_metrics():
	mutable_dict = request.form.copy()
	mode = "flow"
	active_metrics = mutable_dict.get("active_metrics")
	selected_pattern = str(mutable_dict.get("selected_pattern"))
	pattern = str(mutable_dict.get("pattern"))
	script_list = mutable_dict.getlist("script_list[]")
	dir_list = mutable_dict.getlist("dir_list[]")
	flow_list = []
	for dir in dir_list:
		if dir.split('/')[-1] != '':
			flow_list.append(dir.split('/')[-1])
		else:
			flow_list.append(dir.split('/')[-2])

	cmd = mutable_dict.get("cmd")
	compress = bool(int(mutable_dict.get("compress")))
	design_flow_dict = design_flow_extract(dir_list=dir_list, cmd=cmd)
	design_qor = defaultdict(dict)
	for design in design_flow_dict:
		log_list = design_flow_dict[design]
		log_name_list = [log.split('/')[-1] for log in log_list]

		qp = QorProfiler(log_list=log_list, compress=compress, pattern=pattern, script_list=script_list)
		qp.generate_profile()
		design_qor[design]['qor_metrics_dict'], design_qor[design]['step_qor_dict'], design_qor[design]['auto_skip_dict'], design_qor[design]['step_match_dict'], design_qor[design]['steps_dict'] = \
		qp.qor_metrics_dict, qp.step_qor_dict, qp.auto_skip_dict, qp.step_match_dict, qp.steps_dict
		design_qor[design]['log_list'], design_qor[design]['log_name_list']= log_list, log_name_list
		#print design
		#print qp.qor_metrics_dict.keys()
	metrics_order_dict = copy.copy(METRICS_ORDER_DICT)
	metrics_property_dict = copy.copy(METRICS_PROPERTY_DICT)
	for pattern_name in qp.qor_metrics_dict.keys():
		if "USER" in pattern:
			metrics_order_dict[pattern_name] = qp.metrics_order[pattern_name]
			metrics_property_dict[pattern_name] = defaultdict(list)
			i = 1
			for metrics in metrics_order_dict[pattern_name]:
				metrics_property_dict[pattern_name][metrics] = [i, "linear"]
				i+=1
			metrics_property_dict[pattern_name] = dict(metrics_property_dict[pattern_name])
	#print metrics_order_dict, metrics_property_dict
	return jsonify({
		'design_qor': design_qor,
		'metrics': active_metrics,
		'metrics_order_dict': metrics_order_dict, 
		'metrics_property_dict': metrics_property_dict,
		'flow_list': flow_list,
		'color_list': COLOR_LIST, 
		'selected_pattern': selected_pattern,
	})

@app.route('/profile_popt', methods=['POST','GET'])
def qor_profile_popt():
	base_url = request.base_url
	mode = request.args.get('mode')
	active_design = request.args.get('active_design')
	active_metrics = request.args.get('active_metrics')
	active_pattern = request.args.get('active_pattern')
	pattern = str(request.args.get('pattern'))
	script = str(request.args.get('script'))
	#get point
	mutable_dict = request.args.copy()
	point_dict = copy.copy(POINT_DICT_DEFAULT)
	point_dict["prev_d"] = mutable_dict.get('prev_d')
	point_dict["prev_p"] = mutable_dict.get('prev_p')
	point_dict["crnt_d"] = mutable_dict.get('crnt_d')
	point_dict["crnt_p"] = mutable_dict.get('crnt_p')
	compress = int(request.args.get('compress'))
	input_list = mutable_dict.getlist('input_list')
	input_list = [str(input) for input in input_list]
	script_list = mutable_dict.getlist('script_list')
	script_list = [str(script) for script in script_list]
	return qor_profile_main(base_url=base_url, mode=mode, compress=compress, input_list=input_list, point_dict=point_dict, active_design=active_design, active_pattern=active_pattern, active_metrics=active_metrics, pattern=pattern, script_list=script_list)

@app.route('/profile_copt', methods=['POST','GET'])
def qor_profile_copt():
	base_url = request.base_url
	mode = request.args.get('mode')
	pattern = str(request.args.get('pattern'))
	script = str(request.args.get('script'))
	active_design = request.args.get('active_design')
	active_metrics = request.args.get('active_metrics')
	active_pattern = request.args.get('active_pattern')
	#get point
	mutable_dict = request.args.copy()
	point_dict = copy.copy(POINT_DICT_DEFAULT)
	point_dict["prev_d"] = mutable_dict.get('prev_d')
	point_dict["prev_p"] = mutable_dict.get('prev_p')
	point_dict["crnt_d"] = mutable_dict.get('crnt_d')
	point_dict["crnt_p"] = mutable_dict.get('crnt_p')
	compress = int(request.args.get('compress'))
	input_list = mutable_dict.getlist('input_list')
	input_list = [str(input) for input in input_list]
	script_list = mutable_dict.getlist('script_list')
	script_list = [str(script) for script in script_list]

	return qor_profile_main(base_url=base_url, mode=mode, compress=compress, input_list=input_list,cmd="copt", point_dict=point_dict, active_design=active_design, active_pattern=active_pattern, active_metrics=active_metrics, pattern=pattern, script_list=script_list)

@app.route('/profile_ropt', methods=['POST','GET'])
def qor_profile_ropt():
	base_url = request.base_url
	mode = request.args.get('mode')
	pattern = str(request.args.get('pattern'))
	script = str(request.args.get('script'))
	active_design = request.args.get('active_design')
	active_metrics = request.args.get('active_metrics')
	active_pattern = request.args.get('active_pattern')
	#get point
	mutable_dict = request.args.copy()
	point_dict = copy.copy(POINT_DICT_DEFAULT)
	point_dict["prev_d"] = mutable_dict.get('prev_d')
	point_dict["prev_p"] = mutable_dict.get('prev_p')
	point_dict["crnt_d"] = mutable_dict.get('crnt_d')
	point_dict["crnt_p"] = mutable_dict.get('crnt_p')
	compress = int(request.args.get('compress'))
	input_list = mutable_dict.getlist('input_list')
	input_list = [str(input) for input in input_list]
	script_list = mutable_dict.getlist('script_list')
	script_list = [str(script) for script in script_list]

	return qor_profile_main(base_url=base_url, mode=mode, compress=compress, input_list=input_list,cmd="ropt", point_dict=point_dict, active_design=active_design, active_pattern=active_pattern, active_metrics=active_metrics, pattern=pattern, script_list=script_list)

@app.route('/profile_fopt', methods=['POST','GET'])
def qor_profile_fopt():
	base_url = request.base_url
	mode = request.args.get('mode')
	pattern = str(request.args.get('pattern'))
	script = str(request.args.get('script'))
	active_design = request.args.get('active_design')
	active_metrics = request.args.get('active_metrics')
	active_pattern = request.args.get('active_pattern')
	#get point
	mutable_dict = request.args.copy()
	point_dict = copy.copy(POINT_DICT_DEFAULT)
	point_dict["prev_d"] = mutable_dict.get('prev_d')
	point_dict["prev_p"] = mutable_dict.get('prev_p')
	point_dict["crnt_d"] = mutable_dict.get('crnt_d')
	point_dict["crnt_p"] = mutable_dict.get('crnt_p')
	compress = int(request.args.get('compress'))
	input_list = mutable_dict.getlist('input_list')
	input_list = [str(input) for input in input_list]
	script_list = mutable_dict.getlist('script_list')
	script_list = [str(script) for script in script_list]

	return qor_profile_main(base_url=base_url, mode=mode, compress=compress, input_list=input_list,cmd="fopt", point_dict=point_dict, active_design=active_design, active_pattern=active_pattern, active_metrics=active_metrics, pattern=pattern, script_list=script_list)

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

def record_usage(mode):
	conn = MySQLdb.connect(host="pvicc015",user="user",db="preroute_random")
	cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
	time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	#username = request.remote_user
	username = "phyan"
	if username != "phyan":
		source = "web"
		sql = "insert into qor_analyzer(username,source,mode,date) values(%s,%s,%s,%s)"
		param = (username,source,mode,time,)
		n = cursor.execute(sql,param)

def design_flow_extract(dir_list, cmd="popt", active_design=None):
	design_flow_dict = defaultdict(list) # key:design value:flow/log list table

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
			if os.path.isdir(search_path + "/" + design):
				#fatal precheck
				fatal_path = flow_dir + "/" + design + "/" + design + ".nw" + cmd + ".out.gz.fatal"
				fatal_path_1 = flow_dir + "/" + design + "/" + design + ".nw" + cmd + ".out.fatal"
				if os.path.exists(fatal_path) or os.path.exists(fatal_path_1): continue
				if os.path.exists(search_path + "/" + design + "/" + design + ".nw" + cmd + ".out.gz"):
					log_path = search_path + "/" + design + "/" + design + ".nw" + cmd + ".out.gz"
					design_flow_dict[design].append(log_path)
				elif os.path.exists(search_path + "/" + design + "/" + design + ".nw" + cmd + ".out"):
					log_path = search_path + "/" + design + "/" + design + ".nw" + cmd + ".out"
					design_flow_dict[design].append(log_path)

	return design_flow_dict

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
def duo_analysis_main(mode, dir_path, active_duo=None):
	url_data = []
	url_data.append(('mode', mode))
	url_data.append(('dir_path', dir_path))
	#url = "http://pvicc004:8087/analysis?"+urlencode(url_data)
	url = "http://pv/util/opt/qor_analyzer_web/profile?"+urlencode(url_data)
	#get all duo_work dirs
	duo_work_list = {}
	duo_list = []

	duo_list = os.listdir(dir_path)

	for d in duo_list:
		match = re.match('duo_work', d)
		if match:
			duo_work_list[str(d)] = {}
			f = os.popen('cat ' + dir_path +'/' + str(d) + '/run_option.tmp')
			duo_work_list[str(d)]["option"] = str(f.readline().strip())
			duo_mode = str(d.split('_')[-1])			
			duo_work_list[str(d)]["mode"] = duo_mode
			duo_work_list[str(d)]["step"] = {}
			duo_work_list[str(d)]["seq"] = []
			f1 = open(dir_path+"/"+d+"/checkpoints")
			for line in f1.readlines():
				step_name = line.strip()
				duo_work_list[str(d)]["seq"].append(step_name)
				file_list = os.listdir(dir_path+"/"+d+"/"+step_name+".design")
				match = re.match("(\w+)\.nlib",file_list[0])
				nlib_name = match.group(1)
				f = open(dir_path+"/"+d+"/"+step_name+".design/"+nlib_name+".nlib."+step_name+".design.info")
				design_info = f.readline().split()
				design_img = nlib_name+".nlib."+step_name+".design."+duo_mode+".snapshot.gif"
				duo_work_list[str(d)]["step"][step_name] = {}
				duo_work_list[str(d)]["step"][step_name]["info"] = design_info
				if os.path.exists(dir_path+"/"+d+"/"+step_name+".design/"+design_img):
					duo_work_list[str(d)]["step"][step_name]["img"] = dir_path+"/"+d+"/"+step_name+".design/"+design_img
				else:
					duo_work_list[str(d)]["step"][step_name]["img"] = None

	return display_duo_analysis(cp_list=duo_work_list, url=url, active_design=active_duo)

def qor_profile_main(base_url, mode,compress,input_list,point_dict,pattern="all", script_list=None, active_pattern=None,cmd="popt",active_design=None,active_metrics=None):
	#get url
	url_data = []
	url_data.append(('mode',mode))
	url_data.append(('pattern', pattern))
	url_data.append(('compress',compress))
	for param in input_list:
		url_data.append(('input_list', str(param)))
	if script_list is not None:
		for param in script_list:
			url_data.append(('script_list', str(param)))

	url_data.append(('cmd',cmd))
	url = str(base_url)+"?"+urlencode(url_data)
	#==============================
	# 1. QoR metric extraction
	#==============================
	#=========================
	# 1.1 log mode
	#=========================
	if mode == "log":
		# log info extraction
		log_list = sorted(input_list)
		#log_name_list = [log.split('/')[-1] for log in log_list]

		for log in log_list:
			if not os.path.isfile(log):
				error_msg = "'%s' is not a vaild file!!" % log
				return error_found(msg=error_msg)

		qp = QorProfiler(log_list=log_list, compress=compress, pattern=pattern, script_list=script_list)
		qp.generate_profile()

		for pattern in qp.qor_metrics_dict.keys():
			if "USER" in pattern:
				METRICS_ORDER_DICT[pattern] = qp.metrics_order[pattern]
				METRICS_PROPERTY_DICT[pattern] = defaultdict(list)
				i = 1
				for metrics in METRICS_ORDER_DICT[pattern]:
					METRICS_PROPERTY_DICT[pattern][metrics] = [i, "linear"]
					i+=1

		return display_qor_profile_log(mode=mode,compress=compress,qor_metrics_dict=qp.qor_metrics_dict, step_qor_dict=qp.step_qor_dict, auto_skip_dict=qp.auto_skip_dict, 
			step_match_dict=qp.step_match_dict, log_list=log_list, metrics_order_dict=METRICS_ORDER_DICT, metrics_property_dict=METRICS_PROPERTY_DICT,
			url=url, active_pattern=active_pattern, point_dict=point_dict,steps_dict=qp.steps_dict, script_list=script_list)

	#=========================
	# 1.2 flow mode
	#=========================
	elif mode == "flow":
		dir_list = input_list

		for dir in dir_list:
			if not os.path.isdir(dir):
				error_msg = "'%s' is not a vaild path!!" % dir
				return error_found(msg=error_msg)

		design_flow_dict = design_flow_extract(dir_list=dir_list, cmd=cmd)
		design_list = sorted(design_flow_dict.keys())

		metrics_order_dict = copy.copy(METRICS_ORDER_DICT)
		if pattern == "USER":
			i = 1;
			for script in script_list:
				qp = QorProfiler(compress=compress)
				hb_dummy = qp.user_profiler(LOG_DUMMY, script)
				metrics_order_dict[pattern+str(i)] = list(hb_dummy.index)
				i += 1

		#print METRICS_ORDER_DICT
		return display_qor_profile_flow(mode=mode, design_list=design_list, compress=compress, dir_list=dir_list, url=url, cmd=cmd, active_design=active_design, active_metrics=active_metrics, active_pattern=active_pattern, point_dict=point_dict, pattern=pattern, script_list=script_list, metrics_order_dict=metrics_order_dict)
		#return display_qor_profile_flow1(flow_qor_metrics=flow_qor_metrics, step_qor_dict=step_qor_dict, flow_metrics=flow_metrics, 
			#argv_list=input_list, compress=compress, design_chart_dict=design_chart_dict, mode=mode, cmd=cmd, url=url, active_design=active_design, active_metrics=active_metrics, point_dict=point_dict)

def calc_qor_mean_by_stage(design_flow_dict):
	compress = True
	stages = [("initial_drc", "\(.*P2\)"), ("initial_opto", "\(.*P3\)"), ("final_place", "\(.*P4\)"), ("final_opto", "\(.*P5\)")]
	hb_result = pd.DataFrame(index=METRICS_ORDER_DICT["PREROUTE"]) #final qor change pct between base and compare for each stage
	hb  = {} #qor data by stage for each design
	hb_pct = {} #qor data change pct by stage between base and compare of each design
	for stage, reg in stages:
		hb_pct[stage] = pd.DataFrame(index=METRICS_ORDER_DICT["PREROUTE"])
		hb[stage] = pd.DataFrame(index=METRICS_ORDER_DICT["PREROUTE"])
	#for stage, symbol in stages:
	for design,log_list in design_flow_dict.items():
		if len(log_list) != 2: continue #only compare valid logs in both flows
		qp = QorProfiler(log_list=log_list, compress=compress)

		for log in log_list:
			pr_hb = qp.preroute_profiler(log)
			steps_order = pr_hb.columns.tolist()
			steps_order.reverse()

			for stage, reg in stages:
				for step in steps_order:
					match = re.match(reg, step)
					if match:
						hb[stage][log] = pr_hb[step]
						#if design == "VDP_PU" and stage == "final_opto":
							#print hb[stage][log]
						break

		for stage, reg in stages:
			pct_list = []

			hb[stage][log_list] = hb[stage][log_list].astype(float)

			for index in METRICS_ORDER_DICT["PREROUTE"]:
				base = hb[stage][log_list[0]][index]
				comp = hb[stage][log_list[1]][index]
				if np.isnan(base) and np.isnan(comp):
					pct = np.nan
				elif base == comp:
					pct = format(0,".2f")
				elif base > 0 and base <= 0.3 and comp <= 0.3:
					pct = np.nan
				else:
					if base == 0:
						pct = 100
					else:
						pct = (comp - base)*100/base
						if pct > 100: pct = 100
						pct = format(pct,".2f")
				pct_list.append(pct)
			hb_pct[stage][design] = pct_list
			hb_pct[stage][design] = hb_pct[stage][design].astype(float)		

	for stage, reg in stages:
		hb_result[stage] = hb_pct[stage].mean(axis=1,skipna=True)
		hb_result[stage] = hb_result[stage].map('{:,.2f}%'.format)

	#print hb_result
	#print hb_pct["final_opto"]["VDP_PU"]
	#print hb_pct["final_opto"]
	hb_result.to_csv('/u/phyan/hb_result.csv')
	hb_pct["final_opto"].to_csv('/u/phyan/hb_pct_final_opto.csv')
	#print hb["initial_drc"]
	return hb_result

# duo display
def display_duo_analysis(cp_list, url, active_design):
	return render_template('duo_mode_web.html',
		cp_list = cp_list, 
		mode = "checkpoint",
		url=url,
		active_design=active_design,
		duo_metrics = DUO_METRICS
	)	

# qor display
def display_qor_profile_log(mode, compress, qor_metrics_dict, step_qor_dict, auto_skip_dict, step_match_dict, log_list, metrics_order_dict, metrics_property_dict, url, active_pattern, point_dict, steps_dict, script_list, msg=None):
	log_name_list = [log.split('/')[-1] for log in log_list]
	return render_template('log_mode_web.html',
		qor_metrics_dict = qor_metrics_dict, 
		step_qor_dict = dict(step_qor_dict),
		log_list = log_list, 
		log_name_list=log_name_list,
		metrics_order_dict = metrics_order_dict,
		metrics_property_dict = metrics_property_dict, 
		color_list = COLOR_LIST, 
		mode = mode, 
		compress = compress,
		auto_skip_dict = auto_skip_dict, 
		step_match_dict = step_match_dict,
		url=url,
		active_pattern=active_pattern,
		point_dict=point_dict,
		steps_dict=dict(steps_dict),
		script_list=script_list,
	)

def display_qor_profile_flow(mode, design_list, compress, dir_list, url, active_design, active_pattern, active_metrics, point_dict, pattern, script_list, metrics_order_dict, cmd="popt"):
	return render_template('dir_mode_web.html',
		mode=mode,
		design_list=design_list,
		compress=compress,
		dir_list=dir_list,
		active_design=active_design, 
		active_pattern=active_pattern, 
		active_metrics=active_metrics, 
		point_dict=point_dict,
		color_list=COLOR_LIST,
		cmd=cmd, 
		url=url,
		metrics_order_dict=metrics_order_dict,
		pattern=pattern, 
		script_list=script_list,
	)

def error_found(msg):
	return render_template('error.html', msg=msg)

if __name__ == '__main__':
    app.run(host="pv007", port=8087, debug=True)
