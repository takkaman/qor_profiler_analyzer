#!/remote/us01home40/phyan/depot/python/bin/python 
import sys   
import os
import commands
import re
from jinja2 import Environment, PackageLoader, FileSystemLoader

#==========================
# global var init
#==========================
argc = len(sys.argv)
log_num = argc - 2
dir_num = argc - 2
mode = sys.argv[1]
argv_list = []
for i in range(2, argc):
	argv_list.append(sys.argv[i])
argv_list = sorted(argv_list)
#print argv_list
COLOR_LIST = ["#FF6384","#36A2EB","#FFCE56","#CCCC33","#CC9933"]
METRICS_DICT = {"WNS" : [2, 'logarithmic'], "TNS" : [3, 'logarithmic'], "AREA" : [4, 'linear'], "MAXTRAN" : [5, 'logarithmic'], "MAXCAP" : [6, 'logarithmic'], "BUFFCNT" : [7, 'linear'], "INVCNT" : [8, 'linear'], "LVTCNT" : [9, 'linear'], "LVTPCNT" : [10, 'linear'], "MEM" : [11, 'linear']}
METRICS_ORDER = ["WNS", "TNS", "MAXTRAN", 'MAXCAP', "BUFFCNT", "INVCNT", "LVTCNT", "LVTPCNT", "AREA", "MEM"]
auto_skip = "false"
step_match = 1
design_chart_dict = {}
#==========================
# class definition
#==========================
class LogQor:
	metrics = {
		"steps": [], 
		"wns": [], 
		"tns":[], 
		"maxtran": [], 
		"maxcap": [], 
		"buffcnt": [], 
		"invcnt": [], 
		"lvtcnt": [],
		"lvtpcnt": [],
		"area": [],
		"mem": []
		}
	def __init__(self, rows, cols):
		self.metrics["steps"] = [0 for col in range(cols)]
		self.metrics["wns"] = [0 for col in range(cols)]
		self.metrics["tns"] = [0 for col in range(cols)]
		self.metrics["maxtran"] = [0 for col in range(cols)]
		self.metrics["maxcap"] = [0 for col in range(cols)]
		self.metrics["buffcnt"] = [0 for col in range(cols)]
		self.metrics["invcnt"] = [0 for col in range(cols)]
		self.metrics["lvtcnt"] = [0 for col in range(cols)]
		self.metrics["lvtpcnt"] = [0 for col in range(cols)]
		self.metrics["area"] = [0 for col in range(cols)]
		self.metrics["mem"] = [0 for col in range(cols)]

	def info(self):
		print len(self.metrics)


for log in argv_list: #already sorted log name
	print "Extract", log, "..."
	rpt = log + ".qor"	
	os.system("/u/phyan/qor.pl " + log + " > " + rpt)
	#log_rpt[log] = rpt
	cols = int(commands.getoutput("cat " + rpt +" | wc -l")) - 4
	#cols = rpt_cols if rpt_cols > cols else cols

	rows = 13
	log_inst = LogQor(rows, cols)
	print len(log_inst.metrics["steps"])

exit()


#==========================
# function definition
#==========================

# log analysis
def log_qor_analyze(log_list, mode):
	auto_skip = "false"
	step_match = 1
	qor_metrics_list = []
	cols = 0
	log_rpt = {} # log/rpt table
	for log in log_list: #already sorted log name
		print "Extract", log, "..."
		rpt = log + ".qor"	
		os.system("/u/phyan/qor.pl " + log + " > " + rpt)
		log_rpt[log] = rpt
		cols = int(commands.getoutput("cat " + rpt +" | wc -l")) - 4
		#cols = rpt_cols if rpt_cols > cols else cols

		rows = 13
		if cols > 80: auto_skip = "true"
		i = 0

		# logs/qor-metrics/qor-value table
		if mode == "converge":
			qor_metrics = [[0 for col in range(cols)] for row in range(rows)] # reserve 1 more log for converge data
		else:
			qor_metrics = [[0 for col in range(cols)] for row in range(rows)]

		# read logs
		#for (log, rpt) in sorted(log_rpt.iteritems()):
		print "Analyze", log, "..."
		print log, rpt
		f = open(rpt)
		j = 0
		for line in f:
			try:
				match = re.search(r'(\S+)\s+(\d+:\d+:\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
				for k in range(1, rows):
					if k == 2:
						continue

					if (k in [3,4,6,7]) and (int(float(match.group(k))) == 0):
						qor_metrics[k-1][j] = 0.00001
					else:
						qor_metrics[k-1][j] = match.group(k)
				#print qor_metrics_list[i][0][j], qor_metrics_list[i][2][j], qor_metrics_list[i][7][j]
				j += 1
			except:
				pass
		qor_metrics_list.append(qor_metrics)
		f.close()
		print "Done..."
	if len(qor_metrics_list) > 1:
		for i in range(0, len(qor_metrics_list)-1):
			#print len(qor_metrics_list[i][0]), len(qor_metrics_list[i+1][0])	
			if len(qor_metrics_list[i][0]) != len(qor_metrics_list[i+1][0]): step_match = 0
	#print step_match
	if step_match: 
		print "steps between logs match, will show qor metrics in same chart...\n"
	else:
		print "steps between logs not match, will show qor metrics in different charts...\n"
	#print step_match

	return qor_metrics_list, auto_skip, step_match

# qor display
def display_qor_analysis(mode):
	# flow qor display
	print "\n========QoR display========\n"
	info = "QoR Analyzer info: "
	env = Environment(loader = FileSystemLoader('/remote/us01home40/phyan/workspace/python/qor_analyzer/templates'))
	if mode == "log":
		templates = env.get_template('log_mode.html')
		output = templates.render(
			qor_metrics_list=qor_metrics_list, 
			log_list=argv_list, 
			metrics_dict=METRICS_DICT, 
			metrics_order=METRICS_ORDER, 
			color_list=COLOR_LIST, 
			argv_list=argv_list, 
			mode=mode, 
			auto_skip=auto_skip, 
			step_match=step_match
			)
	else:	
		templates = env.get_template('dir_mode.html')
		output = templates.render(
			flow_qor_metrics=flow_qor_metrics, 
			flow_metrics=flow_metrics, 
			metrics_dict=METRICS_DICT, 
			metrics_order=METRICS_ORDER, 
			color_list=COLOR_LIST, 
			argv_list=argv_list, 
			mode=mode, 
			auto_skip=auto_skip, 
			design_chart_dict=design_chart_dict
			)
		#print design_chart_dict
		
	print "Output qor URL:", "http://clearcase"+os.getcwd()+"/qor_analysis-v2.html"

	f = open('qor_analysis-v2.html', 'w')
	f.write(output.encode("utf-8"))
	f.close()

#==============================
# 1. QoR metric extraction
#==============================
#=========================
# 1.1 log mode
#=========================
if mode == "log":
	# log info extraction
	log_list = argv_list
	print "========Detected log mode========"
	qor_metrics_list, auto_skip, step_match = log_qor_analyze(log_list, mode)
	#print len(qor_metrics_list)
    
#=========================
# 1.2 dir/flow mode
#=========================
if mode == "flow":

	dir_list = argv_list
	#print dir_list
	flow_metrics = {} # flow/design table
	flow_qor_metrics = {} #design/qor-per-flow table
	print "#================================"
	print "# Detected dir/flow mode "
	print "#================================\n"
	print "===Scan design candidates===\n"
	#process flows/designs 
	for flow in dir_list:
		search_path = os.getcwd() + "/" + flow
		designs = os.listdir(search_path)
		for design in designs:
			print "Find",design,"..."
			if os.path.isdir(search_path + "/" + design):
				if os.path.exists(search_path + "/" + design + "/" + design + ".nwpopt.out"):
					if flow_metrics.has_key(design):
						flow_metrics[design].append(flow)
					else:
						flow_metrics[design] = []
						flow_metrics[design].append(flow)
				else:
					print search_path + "/" + design + "/" + design + ".nwpopt.out does not exist, skip..."
			else:
				print search_path + "/" + design + " is not dir, skip..."
	#print flow_metrics

	# init flow qor metrics
	print "\n===Extract design qor statistics===\n"
	for design in sorted(flow_metrics.keys()):
		design_chart_dict[design] = {}
		print "Process",design,"..."
		design_log_list = [] # map design name to coresponding log file name
		for flow in flow_metrics[design]:
			log_path = flow + "/" + design + "/" + design + ".nwpopt.out"
			design_log_list.append(log_path)
		print design_log_list

		flow_qor_metrics[design], design_chart_dict[design]['auto_skip'], design_chart_dict[design]['step_match'] = log_qor_analyze(design_log_list, mode)
		#print design_chart_dict[design][step_match]

#=========================
# 1.3 converge mode
#=========================
if mode == "converge":

	dir_list = argv_list
	#print dir_list
	flow_metrics = {} # flow/design table
	flow_qor_metrics = {} #design/qor-per-flow table
	print "#================================"
	print "# Detected converge mode "
	print "#================================\n"

	print "===Scan design candidates===\n"
	#process flows/designs 
	for flow in dir_list:
		search_path = os.getcwd() + "/" + flow
		designs = os.listdir(search_path)
		for design in designs:
			print "Find",design,"..."
			if os.path.isdir(search_path + "/" + design):
				if os.path.exists(search_path + "/" + design + "/" + design + ".nwpopt.out"):
					if flow_metrics.has_key(design):
						flow_metrics[design].append(flow)
					else:
						flow_metrics[design] = []
						flow_metrics[design].append(flow)
				else:
					print search_path + "/" + design + "/" + design + ".nwpopt.out does not exist, skip..."
			else:
				print search_path + "/" + design + " is not dir, skip..."
	#print flow_metrics

	# init flow qor metrics
	print "\n===Extract design qor statistics===\n"
	for design in sorted(flow_metrics.keys()):
		print "Process",design,"..."
		design_log_list = [] # map design name to coresponding log file name
		for flow in flow_metrics[design]:
			log_path = flow + "/" + design + "/" + design + ".nwpopt.out"
			design_log_list.append(log_path)
		print design_log_list

		flow_qor_metrics[design] = log_qor_analyze(design_log_list, mode)
	
	#print step_num, metrics_num
	for metrics_index in METRICS_DICT.values():
		for design in sorted(flow_metrics.keys()):
			step_num = len(flow_qor_metrics[design][0][0])
			print design, metrics_index, step_num
			#for i in range(step_num):
				#print design, flow_qor_metrics[design][0][metrics_index][i]
		#print len(metrics)
		#print len(flow_qor_metrics[design][0])
	exit()
#==============================
# 2. QoR Analysis Display
#==============================
#print auto_skip
display_qor_analysis(mode)





