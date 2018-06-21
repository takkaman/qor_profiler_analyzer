#!/remote/us01home40/phyan/depot/Python-2.7.11/bin/python
import sys, os, commands
import copy, re, getpass, datetime
import threading
from multiprocessing import Pool, Process
from multiprocessing.managers import BaseManager, DictProxy
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
from flask_util_js import FlaskUtilJs
import json
#heartbeat extraction
#from preroute import pr_log_extractor
from qorProfiler import QorProfiler
from record_usage import *
from utility import *

app = Flask(__name__)
fujs = FlaskUtilJs(app)

class MyManager(BaseManager):
    pass

MyManager.register('defaultdict', defaultdict, DictProxy)    
#==========================
# global var init
#==========================
COLOR_LIST = ["#FF6384","#36A2EB","#fdb45c","#46bfbd","#996699","#99CC33"]
COLOR_LIST1 = [["#f5486c","#3399cc","#e49d46","#009999","#8c548c","#99cc66"], ["#FF6384","#36A2EB","#fdb45c","#46bfbd","#996699","#99CC33"]]
#COLOR_LIST = ["#FF6384","#36A2EB","#FFCE56","#99CC33","#CC9933"]
METRICS_PROPERTY_DICT = {
	"APS":
		{"Line": [0, 'linear'], "ELAPSE_TIME" : [1, 'linear'], "WNS" : [2, 'logarithmic'], "TNS" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "MAXTRAN" : [5, 'logarithmic'],
		 "MAXCAP" : [6, 'logarithmic'], "BUFFCNT" : [7, 'linear'], "INVCNT" : [8, 'linear'], "LVTCNT" : [9, 'linear'],
		  "LVTPCNT" : [10, 'linear'], "MEM" : [11, 'linear'], "LEAKPWR" : [12, 'linear'], "WHNS" : [13, 'linear']},
	"QOR":
		{"Line": [0, 'linear'], "TNS" : [1, 'logarithmic'], "LDRC" : [2, 'logarithmic'], "AREA" : [3, 'linear'], "LEAKAGE" : [4, 'linear'], "ELAPSE" : [5, 'linear']},		
	"QOR_STG":
		{"Line": [0, 'linear'], "TNS" : [1, 'logarithmic'], "LDRC" : [2, 'logarithmic'], "AREA" : [3, 'linear'], "LEAKAGE" : [4, 'linear'], "ELAPSE" : [5, 'linear']},	
	# "QOR_STG":
	# 	{"ELAPSE_TIME" : [1, 'linear'], "WNS" : [2, 'logarithmic'], "TNS" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "MAXTRAN" : [5, 'logarithmic'],
	# 	 "MAXCAP" : [6, 'logarithmic'], "BUFFCNT" : [7, 'linear'], "INVCNT" : [8, 'linear'], "LVTCNT" : [9, 'linear'],
	# 	  "LVTPCNT" : [10, 'linear'], "MEM" : [11, 'linear'], "LEAKPWR" : [12, 'linear'], "WHNS" : [13, 'linear']},
	"ROPT":
		{"Line": [0, 'linear'], "RSETUP" : [1, 'logarithmic'], "SETUP_COST" : [2, 'logarithmic'], "RHOLD" : [3, 'logarithmic'], "HOLD_COST" : [4, 'linear'], "RLDRC_MT" : [5, 'logarithmic'],
	    "RLDRC_MC" : [6, 'logarithmic'], "LDRC_COST" : [7, 'logarithmic'], "AREA" : [8, 'linear'], "LEAKAGE" : [9, 'linear'], "ELAPSE" : [10, 'linear']},
	"DF_ROPT":
		{"Line": [0, 'linear'], "SETUP_COST" : [1, 'logarithmic'],"HOLD_COST" : [2, 'linear'],"LDRC_COST" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "LEAKAGE" : [5, 'linear'], "ELAPSE" : [6, 'linear']},	    
    "GROPT":
		{"Line": [0, 'linear'], "RSETUP" : [1, 'logarithmic'], "SETUP_COST" : [2, 'logarithmic'], "RHOLD" : [3, 'logarithmic'], "HOLD_COST" : [4, 'linear'], "RLDRC_MT" : [5, 'logarithmic'],
	    "RLDRC_MC" : [6, 'logarithmic'], "LDRC_COST" : [7, 'logarithmic'], "AREA" : [8, 'linear'], "LEAKAGE" : [9, 'linear'], "ELAPSE" : [10, 'linear']},
	"DF_GROPT":
		{"Line": [0, 'linear'], "SETUP_COST" : [1, 'logarithmic'],"HOLD_COST" : [2, 'linear'],"LDRC_COST" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "LEAKAGE" : [5, 'linear'], "ELAPSE" : [6, 'linear']},	    	    
    "NPO_COPT":
		{"Line": [0, 'linear'], "RSETUP" : [1, 'logarithmic'], "SETUP_COST" : [2, 'logarithmic'], "RHOLD" : [3, 'logarithmic'], "HOLD_COST" : [4, 'linear'], "RLDRC_MT" : [5, 'logarithmic'],
	    "RLDRC_MC" : [6, 'logarithmic'], "LDRC_COST" : [7, 'logarithmic'], "AREA" : [8, 'linear'], "LEAKAGE" : [9, 'linear'], "ELAPSE" : [10, 'linear']},
	"DF_NPO_COPT":
		{"Line": [0, 'linear'], "SETUP_COST" : [1, 'logarithmic'],"HOLD_COST" : [2, 'linear'],"LDRC_COST" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "LEAKAGE" : [5, 'linear'], "ELAPSE" : [6, 'linear']},	
    "NPO_POPT":
		{"Line": [0, 'linear'], "RSETUP" : [1, 'logarithmic'], "SETUP_COST" : [2, 'logarithmic'], "RHOLD" : [3, 'logarithmic'], "HOLD_COST" : [4, 'linear'], "RLDRC_MT" : [5, 'logarithmic'],
	    "RLDRC_MC" : [6, 'logarithmic'], "LDRC_COST" : [7, 'logarithmic'], "AREA" : [8, 'linear'], "LEAKAGE" : [9, 'linear'], "ELAPSE" : [10, 'linear']},
	"DF_NPO_POPT":
		{"Line": [0, 'linear'], "SETUP_COST" : [1, 'logarithmic'],"HOLD_COST" : [2, 'linear'],"LDRC_COST" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "LEAKAGE" : [5, 'linear'], "ELAPSE" : [6, 'linear']},	
	"FULL_FLOW_PPA":
		{"FREQUENCY_GHz": [1, 'linear'], "WNS": [2, 'linear'], "AREA": [2, 'linear'], "LEAKAGE": [2, 'linear'], "DYNAMIC": [3, 'linear'], "ELAPSE": [4, 'linear'], "MEM": [5, 'linear']},
	"FUNC_DIST":
		{"ELAPSE": [1, 'linear'], "MEM_PEAK": [2, 'linear']},
	"ELAPSE_MEM":
		{"ELAPSE": [1, 'linear'], "MEM_PEAK": [2, 'linear']},
}

METRICS_ORDER_DICT = {
	"APS": ["Line", "WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "AREA", "MEM", "ELAPSE_TIME", "LVTCNT", "LVTPCNT", "LEAKPWR", "WHNS"],
	"QOR": ["Line", "TNS", "LDRC", "AREA", "LEAKAGE", "ELAPSE"],
	"QOR_STG": ["Line", "TNS", "LDRC", "AREA", "LEAKAGE", "ELAPSE"],
	# "QOR_STG": ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "AREA", "MEM", "ELAPSE_TIME", "LVTCNT", "LVTPCNT", "LEAKPWR", "WHNS"],
	"ROPT": ["RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"DF_ROPT":["SETUP_COST","HOLD_COST","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"GROPT": ["RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"DF_GROPT":["SETUP_COST","HOLD_COST","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"NPO_POPT": ["Line", "RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"DF_NPO_POPT":["SETUP_COST","HOLD_COST","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"NPO_COPT": ["Line", "RSETUP","SETUP_COST","RHOLD","HOLD_COST","RLDRC_MT","RLDRC_MC","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"DF_NPO_COPT":["SETUP_COST","HOLD_COST","LDRC_COST","AREA","LEAKAGE","ELAPSE"],
	"FULL_FLOW_PPA": ["FREQUENCY_GHz", "WNS", "AREA", "LEAKAGE", "DYNAMIC", "ELAPSE", "MEM"],
	"FUNC_DIST": ['ELAPSE', 'MEM_PEAK'],
	"ELAPSE_MEM": ['ELAPSE', 'MEM_PEAK'],
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
	username = "phyan"
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

@app.route('/about')
@app.route('/about/')
def about():
	record_usage(mode='about', username=request.remote_user)
	return render_template('about.html', user=request.remote_user)

@app.route('/analysis_tricks')
def qor_analysis_tricks():
	return render_template('analysis_tricks.html', user=request.remote_user)

@app.route('/analysis_sqb', methods=['POST'])
def step_qor_benefit_analysis():
	flow_metrics = {} # flow/design table
	flow_qor_metrics = {} #design/qor-per-flow table
	step_qor_dict = {}
	design_chart_dict = {}
	step_name = request.form['step_name']
	flow_dir = request.form['flow_dir']
	second_dir = request.form['second_dir']
	stage = request.form['stage']
	pattern = request.form['pattern']
	""" for design filter """
	tech_nodes = json.loads(request.form['tech_nodes'])
	customers = json.loads(request.form['customers'])
	# print "sqb ",tech_nodes, customers
	cmd = stage[-4:].strip().lower()
	dir_list = [flow_dir]
	dir_list2 = [second_dir]
	mode = "flow"
	compress = True
	# step_qor_info = {}
	list_mode = False
	record_usage(mode='sqb', username=request.remote_user)

	if step_name == "":
		list_mode = True

	for dir in dir_list+dir_list2:
		if not os.path.isdir(dir):
			error_msg = "'%s' is not a vaild path!!" % dir
			return jsonify({
				'result': "fail",
				'msg': error_msg,
			})

	if list_mode:
		steps_list_dict = generate_step_dict(pattern, dir_list, cmd, compress, tech_nodes, customers)

		return jsonify({
			'result': "success",
			'steps_list_dict': json.dumps(steps_list_dict),
		})

	else:
		mgr = MyManager()
		mgr.start()
		step_qor_info = mgr.defaultdict(list)
		threads = []
		# print "display mode"
		if pattern == "APS" or pattern == "QOR_STG":
			default_metrics = "WNS"
		elif pattern == "FULL_FLOW_PPA":
			default_metrics = "FREQUENCY_GHz"
		else: 
			default_metrics = "RSETUP"
			
		if pattern == "FULL_FLOW_PPA":
			design_list, tech_node_dict, customer_dict = design_flow_extract(dir_list=dir_list, cmd='full_flow', tech_nodes=tech_nodes, customers=customers)
			for design in design_list:
				# print "Process ", design
				input_list = [dir+'/'+design for dir in dir_list]
				log_list = input_list
				p = Process(target=generate_sqb_step_pair1, args=(design, log_list, pattern, dir_list, dir_list2, step_name, step_qor_info))
				threads.append(p)

		else:
			design_flow_dict, tech_node_dict, customer_dict = design_flow_extract(dir_list=dir_list, cmd=cmd, tech_nodes=tech_nodes, customers=customers)
			for design, log_list in design_flow_dict.items():
				p = Process(target=generate_sqb_step_pair, args=(design, log_list, pattern, cmd, compress, dir_list, dir_list2, step_name, step_qor_info))
				threads.append(p)

		nloops = range(len(threads))
		for i in nloops:
			threads[i].start()
		for i in nloops:
			threads[i].join()

		step_qor_info = dict(step_qor_info)
		step_qor_info = pd.DataFrame(step_qor_info)
		step_qor_info = step_qor_info.fillna(value="null").to_dict(orient="index")

		return jsonify({
			'result': "success",
			'step_qor_info': json.dumps(step_qor_info),
			'default_metrics': default_metrics,
			#'step_qor_info': {"Daedalus_TS16FFP": [["(27P)SIZE3", 0.346, "(28P)SIZE4", 0.346, "0.00%"]], "Icarus": [["(27P)SIZE3", 0.051, "(28P)SIZE4", 0.049, "-4.08%"], ["(36P)SIZE3", 0.053, "(37P)SIZE4", 0.053, "0.00%"]]},
	        #'step_qor_result': step_qor_result.to_dict(orient="index")["WNS"]
		})

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
	""" for design filter """
	tech_nodes = json.loads(request.form['tech_nodes'])
	customers = json.loads(request.form['customers'])
	cmd = stage[-4:].strip().lower()
	dir_list = [flow_dir]
	mode = "flow"
	compress = True
	step_qor_info = {}
	list_mode = False
	record_usage(mode='sqc', username=request.remote_user)

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
		steps_list_dict = generate_step_dict(pattern, dir_list, cmd, compress)

		return jsonify({
			'result': "success",
			'steps_list_dict': json.dumps(steps_list_dict),
		})

	else:
		mgr = MyManager()
		mgr.start()
		step_qor_info = mgr.defaultdict(list)
		threads = []

		if pattern == "APS"  or pattern == "QOR_STG":
			default_metrics = "WNS"
		elif pattern == "FULL_FLOW_PPA":
			default_metrics = "FREQUENCY_GHz"
		else: 
			default_metrics = "RSETUP"

		if pattern == "FULL_FLOW_PPA":
			design_list, tech_node_dict, customer_dict = design_flow_extract(dir_list=dir_list, cmd='full_flow', tech_nodes=tech_nodes, customers=customers)
			for design in design_list:
				# print design
				input_list = [dir_list[0] +'/'+design]
				log_list = input_list
				p = Process(target=generate_sqc_step_pair, args=(design, log_list, pattern, compress, base_name, step_name, step_qor_info))
				threads.append(p)
				# print step_qor_info[design]
		else:
			design_flow_dict, tech_node_dict, customer_dict = design_flow_extract(dir_list=dir_list, cmd=cmd, tech_nodes=tech_nodes, customers=customers)
			for design, log_list in design_flow_dict.items():
				# print "Process ", design
				p = Process(target=generate_sqc_step_pair, args=(design, log_list, pattern, compress, base_name, step_name, step_qor_info))
				threads.append(p)

		nloops = range(len(threads))
		for i in nloops:
			threads[i].start()
		for i in nloops:
			threads[i].join()

		step_qor_info = dict(step_qor_info)
		step_qor_info = pd.DataFrame(step_qor_info)
		step_qor_info = step_qor_info.fillna(value="null").to_dict(orient="index")

		return	jsonify({
			'result':	"success",
			'step_qor_info':	json.dumps(step_qor_info),
			'default_metrics':	default_metrics,
		})

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
	record_usage(mode='sqt', username=request.remote_user)
    
	if bound == "":
		list_mode = True

	for dir in dir_list:
		if not os.path.isdir(dir):
			error_msg = "'%s' is not a vaild path!!" % dir
			return jsonify({
				'result': "fail",
				'msg': error_msg,
			})
	# print "list mode is",list_mode
	if list_mode:
		steps_list_dict = generate_step_dict(pattern, dir_list, cmd, compress)

		# print steps_list_dict
		return jsonify({
			'result': "success",
			'steps_list_dict': json.dumps(steps_list_dict),
		})

	else:
		mgr = MyManager()
		mgr.start()
		step_qor_info = mgr.defaultdict(list)
		threads = []

		if pattern == "APS" or pattern == "QOR_STG":
			default_metrics = "WNS"
		elif pattern == "FULL_FLOW_PPA":
			default_metrics = "FREQUENCY_GHz"
		else: 
			default_metrics = "RSETUP"
			
		if pattern == "FULL_FLOW_PPA":
			# design_list = []
			# for dir in dir_list:
			# 	design_list.extend(os.listdir(dir))
			# print cmd
			design_list, tech_node_dict, customer_dict = design_flow_extract(dir_list, cmd='full_flow')
			for design in design_list:
				# print design
				input_list = [dir_list[0] +'/'+design]
				log_list = input_list
				p = Process(target=generate_sqt_step_pair, args=(design, log_list, pattern, compress, bound, step_qor_info))
				threads.append(p)
				# print step_qor_info[design]
		else:
			design_flow_dict, tech_node_dict, customer_dict = design_flow_extract(dir_list, cmd=cmd)
			for design, log_list in design_flow_dict.items():
				p = Process(target=generate_sqt_step_pair, args=(design, log_list, pattern, compress, bound, step_qor_info))
				threads.append(p)

		nloops = range(len(threads))
		for i in nloops:
			threads[i].start()
		for i in nloops:
			threads[i].join()

		step_qor_info = dict(step_qor_info)
		step_qor_info = pd.DataFrame(step_qor_info)
		step_qor_info = step_qor_info.fillna(value="null").to_dict(orient="index")

		return jsonify({
			'result': "success",
			'step_qor_info': json.dumps(step_qor_info),
			'default_metrics': default_metrics,
			#'step_qor_info': {"Daedalus_TS16FFP": [["(27P)SIZE3", 0.346, "(28P)SIZE4", 0.346, "0.00%"]], "Icarus": [["(27P)SIZE3", 0.051, "(28P)SIZE4", 0.049, "-4.08%"], ["(36P)SIZE3", 0.053, "(37P)SIZE4", 0.053, "0.00%"]]},
	        #'step_qor_result': step_qor_result.to_dict(orient="index")["WNS"]
		})

@app.route('/analysis_sqa', methods=['POST'])
def stage_based_qor_analysis():
	base_dir = request.form['flowb_dir']
	compare_dir = request.form['flowc_dir']
	dir_list = [base_dir,compare_dir]
	design_flow_dict, tech_node_dict, customer_dict = design_flow_extract(dir_list)
	mean_qor = calc_qor_mean_by_stage(design_flow_dict)

	return render_template('index.html', user="phyan", active_duo=False)
	return jsonify({
		'mean_qor': mean_qor,
		#'step_qor_info': {"Daedalus_TS16FFP": [["(27P)SIZE3", 0.346, "(28P)SIZE4", 0.346, "0.00%"]], "Icarus": [["(27P)SIZE3", 0.051, "(28P)SIZE4", 0.049, "-4.08%"], ["(36P)SIZE3", 0.053, "(37P)SIZE4", 0.053, "0.00%"]]},
	    'step_qor_result': step_qor_result.to_dict(orient="index")["WNS"]
	})

@app.route('/qor_profile', methods=['POST','GET'])
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
			record_usage(mode=mode+'_'+str(compress), username=request.remote_user)
			return qor_profile_main(base_url=base_url, mode=mode, compress=compress, input_list=input_list, point_dict=point_dict, pattern=pattern, script_list=script_list)
		elif mode == "checkpoint":
			record_usage(mode=mode, username=request.remote_user)
			dir_path = request.form['param-2']

			return duo_analysis_main(base_url=base_url, mode=mode, dir_path=dir_path)

	elif request.method == 'GET':
		point_dict = copy.copy(POINT_DICT_DEFAULT)
		mutable_dict = request.args.copy()
		if mutable_dict.__len__():
			mode = mutable_dict.get('mode')
			if mode == "checkpoint":
				dir_path = mutable_dict.get('dir_path')
				active_design = mutable_dict.get('active_design')
				record_usage(mode=mode, username=request.remote_user)

				return duo_analysis_main(base_url=base_url, mode=mode, dir_path=dir_path, active_duo=active_design)
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
				record_usage(mode=mode+'_'+str(compress), username=request.remote_user)
				return qor_profile_main(base_url=base_url, mode=mode, compress=compress, input_list=input_list, cmd=cmd, active_pattern=active_pattern, active_design=active_design,active_metrics=active_metrics, point_dict=point_dict, pattern=pattern, script_list=script_list)
		else:
			return render_template('index.html')	

@app.route('/jump_profile', methods=['POST'])
def jump_profile():
	first_name = request.form.get('first_name')
	first_dir = request.form.get('first_dir')
	second_dir = request.form.get('second_dir')
	first_pattern = request.form.get('first_pattern')
	first_stage = request.form.get('first_stage')
	second_name = request.form.get('second_name')
	single_name = request.form.get('single_name')
	number = request.form.get('number')
	mode = request.form.get('mode')
	tech_nodes = str(request.form.get('tech_nodes'))
	customers = str(request.form.get('customers'))
	# print "jump ", tech_nodes, customers

	if tech_nodes == "":
		tech_nodes = []
	else:
		tech_nodes = tech_nodes.split(',')

	if customers == "":
		customers = []
	else:	
		customers = customers.split(',')

	return render_template('analysis_tricks.html', second_dir=second_dir, number = number, mode = mode, single_name = single_name, step_name = first_name, comp_name=second_name, flow_dir = first_dir, stage = first_stage, pattern = first_pattern, tech_nodes=tech_nodes, customers=customers)

@app.route('/display_design_chart', methods=['POST'])
def qor_profile_by_design():
	mutable_dict = request.form.copy()
	mode = "flow"
	active_design = mutable_dict.get("active_design")
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
	if cmd == "full_flow":
		design_list = [dir+'/'+active_design for dir in dir_list]
		log_list = design_list
		qp = QorProfiler(input_list=design_list, pattern=cmd.upper())

	else:
		compress = bool(int(mutable_dict.get("compress")))
		design_flow_dict, tech_node_dict, customer_dict = design_flow_extract(dir_list=dir_list, cmd=cmd, active_design=active_design)
		log_list = design_flow_dict[active_design]
		qp = QorProfiler(input_list=log_list, compress=compress, pattern=pattern, script_list=script_list)

	qp.generate_profile()

	for log in qp.empty_profile:
		log_list.remove(log)
		flow = log.split('/')[-3]
		flow_list.remove(flow)
	log_name_list = [log.split('/')[-1] for log in log_list]

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
		'metrics_order_dict': metrics_order_dict, 
		'metrics_property_dict': metrics_property_dict,
		#'url': url, 
		#'point_dict': point_dict,
		'steps_dict': qp.steps_dict,
		'log_list': log_list,
		'log_name_list': log_name_list,
		'flow_list': flow_list,
		'color_list': COLOR_LIST,
		'color_list1': COLOR_LIST1,
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
	mgr = MyManager()
	mgr.start()
	design_qor = mgr.defaultdict(dict)

	threads = []
	if selected_pattern == "FULL_FLOW_PPA":
		# print cmd
		design_list, tech_node_dict, customer_dict = design_flow_extract(dir_list, cmd=cmd)
		for design in design_list:
			# print "Process ", design
			input_list = [dir+'/'+design for dir in dir_list]
			log_list = input_list
			log_name_list = [log.split('/')[-1] for log in log_list]
			pattern = selected_pattern.upper()
			compress = True
			p = Process(target=sub_qp_process, args=(design, log_list, compress, pattern, script_list, log_name_list, design_qor))
			threads.append(p)

	else:
		compress = bool(int(mutable_dict.get("compress")))
		design_flow_dict, tech_node_dict, customer_dict = design_flow_extract(dir_list=dir_list, cmd=cmd)		
		for design in design_flow_dict:
			# print "Process ", design
			log_list = design_flow_dict[design]
			log_name_list = [log.split('/')[-1] for log in log_list]
			p = Process(target=sub_qp_process, args=(design, log_list, compress, pattern, script_list, log_name_list, design_qor))
			threads.append(p)

	nloops = range(len(threads))
	for i in nloops:
		threads[i].start()
	for i in nloops:
		threads[i].join()
        # print "All done!"
		#print qp.qor_metrics_dict.keys()
	# redundant generate aiming to get patterns
	qp = QorProfiler(input_list=log_list, compress=compress, pattern=pattern, script_list=script_list)
	qp.generate_profile()
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
		'design_qor': dict(design_qor),
		'metrics': active_metrics,
		'metrics_order_dict': metrics_order_dict, 
		'metrics_property_dict': metrics_property_dict,
		'flow_list': flow_list,
		'color_list': COLOR_LIST, 
		'selected_pattern': selected_pattern,
	})

@app.route('/profile_flow', methods=['POST','GET'])
def profile_flow():
	# print request.method
	cmd = request.args.get('cmd')
	# print cmd
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
	tech_nodes = [str(tech_node) for tech_node in mutable_dict.getlist('tech_nodes')]
	customers = [str(customer) for customer in mutable_dict.getlist('customers')]
	# print tech_nodes, customers
	# input list from url get 
	input_list = mutable_dict.getlist('input_list')
	# input list from flaskURL get
	input_list2 = mutable_dict.getlist('input_list')[0].split(',')
	if len(input_list2) > len(input_list): input_list = input_list2
	#print input_list
	input_list = [str(input) for input in input_list]
	script_list = mutable_dict.getlist('script_list')
	script_list = [str(script) for script in script_list]
	return qor_profile_main(base_url=base_url, mode=mode, compress=compress, input_list=input_list, cmd=cmd, point_dict=point_dict, active_design=active_design, active_pattern=active_pattern, active_metrics=active_metrics, pattern=pattern, script_list=script_list,tech_nodes=tech_nodes, customers=customers)

def duo_analysis_main(base_url, mode, dir_path, active_duo=None):
	url_data = []
	url_data.append(('mode', mode))
	url_data.append(('dir_path', dir_path))
	#url = "http://pvicc004:8087/analysis?"+urlencode(url_data)
	# url = "http://pv/util/opt/qor_analyzer_web/profile?"+urlencode(url_data)
	url = str(base_url)+"?"+urlencode(url_data)
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
				if not len(file_list): 
					duo_work_list[str(d)]["step"][step_name] = {}
					duo_work_list[str(d)]["step"][step_name]["info"] = ""
					continue
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

def qor_profile_main(base_url, mode,compress,input_list,point_dict,pattern="all", script_list=None, active_pattern=None,cmd="full_flow",active_design=None,active_metrics=None, tech_nodes=[], customers=[]):
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

		qp = QorProfiler(input_list=log_list, compress=compress, pattern=pattern, script_list=script_list)
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
			# print dir
			if not os.path.isdir(dir):			
				error_msg = "'%s' is not a vaild path!!" % dir
				return error_found(msg=error_msg)

		if cmd == "full_flow":
			design_list, tech_node_dict, customer_dict = design_flow_extract(dir_list=dir_list, cmd=cmd)
			# print design_list
		else:
			design_flow_dict, tech_node_dict, customer_dict = design_flow_extract(dir_list=dir_list, cmd=cmd)
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
		return display_qor_profile_flow(mode=mode, design_list=design_list, compress=compress, dir_list=dir_list, url=url, cmd=cmd, active_design=active_design, active_metrics=active_metrics, active_pattern=active_pattern, point_dict=point_dict, pattern=pattern, script_list=script_list, metrics_order_dict=metrics_order_dict, tech_node_dict=tech_node_dict, customer_dict=customer_dict, tech_nodes=tech_nodes, customers=customers)
		#return display_qor_profile_flow1(flow_qor_metrics=flow_qor_metrics, step_qor_dict=step_qor_dict, flow_metrics=flow_metrics, 
			#argv_list=input_list, compress=compress, design_chart_dict=design_chart_dict, mode=mode, cmd=cmd, url=url, active_design=active_design, active_metrics=active_metrics, point_dict=point_dict)

def calc_qor_mean_by_stage(design_flow_dict):
	compress = True
	stages = [("initial_drc", "\(.*P2\)"), ("initial_opto", "\(.*P3\)"), ("final_place", "\(.*P4\)"), ("final_opto", "\(.*P5\)")]
	hb_result = pd.DataFrame(index=METRICS_ORDER_DICT["APS"]) #final qor change pct between base and compare for each stage
	hb  = {} #qor data by stage for each design
	hb_pct = {} #qor data change pct by stage between base and compare of each design
	for stage, reg in stages:
		hb_pct[stage] = pd.DataFrame(index=METRICS_ORDER_DICT["APS"])
		hb[stage] = pd.DataFrame(index=METRICS_ORDER_DICT["APS"])
	#for stage, symbol in stages:
	for design,log_list in design_flow_dict.items():
		if len(log_list) != 2: continue #only compare valid logs in both flows
		qp = QorProfiler(input_list=log_list, compress=compress)

		for log in log_list:
			pr_hb = qp.aps_profiler(log)
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

			for index in METRICS_ORDER_DICT["APS"]:
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
		color_list1 = COLOR_LIST1,
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

def display_qor_profile_flow(mode, design_list, compress, dir_list, url, active_design, active_pattern, active_metrics, point_dict, pattern, script_list, metrics_order_dict, tech_node_dict, customer_dict, tech_nodes, customers, cmd="popt"):
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
		tech_node_dict=dict(tech_node_dict), 
		customer_dict=dict(customer_dict),
		tech_nodes=tech_nodes,
		customers=customers,
	)

def error_found(msg):
	return render_template('error.html', msg=msg)

if __name__ == '__main__':
    app.run(host="pv007", port=8087, debug=True)