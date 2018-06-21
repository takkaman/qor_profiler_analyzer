#!/remote/us01home40/phyan/depot/Python-2.7.11/bin/python

#=============================================================================
#
# PRS output file *.nw*opt.out, *.nw*rpt.out(.gz) pre handling
# Purpose:
#   reduce later qor analyzer extraction runtime
#
# Output:
#   *.nw*opt.out      -> *.nw*opt.qp
#   *.nw*rpt.out(.gz) -> *.nw*rpt.qp
#
#=============================================================================

import sys 
import os
import commands
import stat
from qorProfiler import QorProfiler

RUN_LOG_LIST = ['dcopt','nwpopt','nwcopt','nwropt','nwfopt']
RPT_LOG_LIST = ['dcrpt','nwprpt','nwcrpt','nwrrpt','nwrpt']

def extract_flow(flow, compress):
    print "Flow dir: %s" %flow
    print "Start log extraction!"
    designs = os.listdir(flow)
    cwd = os.getcwd()
    for design in designs:
        if not os.path.isdir(flow+'/'+design): continue
        print "handling design dir %s" %design        

        os.chdir(flow+'/'+design)
        for log in RUN_LOG_LIST:
            if os.path.exists(design+'.'+log+'.out'):
                print "    Found %s log, do default pattern extraction" %log
                extract_xopt(design, log, compress)
            else:
                print "    Not found %s log, skip extraction" %log

        for log in RPT_LOG_LIST:
            if os.path.exists(design+'.'+log+'.out'):
                print "    Found %s log, do rpt extraction" %log
                extract_xrpt(design, log, compress)
            elif os.path.exists(design+'.'+log+'.out.gz'):
                print "    Found %s zipped log, do rpt extraction" %log
                zextract_xrpt(design, log, compress)
            else:
                print "    Not found %s log, skip extraction" %log

        os.chdir(cwd)
        extract_full_flow(flow+'/'+design, compress)

def extract_full_flow(design, compress):
    print "    Extract full flow pattern"
    try:
        qp = QorProfiler(input_list=[design], pattern="FULL_FLOW", compress=compress, dump_csv=True)
        qp.generate_profile()
    except Exception as e:
        print e

    return

def extract_xopt(design, log, compress):
    """
    if os.path.exists(design+'.'+log+'.qp'):
        print "    Found extracted file %s.%s.qp, skip extraction" %(design,log)
        return
    """
    log_file = design+'.'+log+'.out'
    # output_file = design+'.'+log+'.qp'
    try:
        qp = QorProfiler(input_list=[log_file], compress=compress, dump_csv=True)
        qp.generate_profile()

    except Exception as e:
        # import traceback
        # traceback.print_exc()
        print e

    return

def extract_xrpt(design, log, compress):
    if os.path.exists(design+'.'+log+'.qp'):
        print "    Found extracted file %s.%s.qp, skip extraction" %(design,log)
        return

    log_file = design+'.'+log+'.out'
    output_file = './qor_profile/'+design+'.'+log+'.qp'
    try:
        with open(output_file, 'w') as fp:
            # extract frequency/wns
            slack = os.popen("awk '/Design.*\(Setup\)/ {print $0}' " + log_file).readlines()
            if len(slack):
                for l in slack:
                    fp.write(l)
            clk = os.popen("awk '/clock .* \(.* edge\)\W+\w+\W+\w+/ {print $0}' " + log_file).readlines()
            if len(clk): 
                for l in clk:
                    fp.write(l)
            unit = os.popen("awk '/Time Unit.*:/ {print $0}' " + log_file).readlines()
            if len(unit): 
                for l in unit:
                    fp.write(l)
            # extract area
            area = os.popen("awk '/Cell Area \(netlist\):/ {print $0}' " + log_file).readlines()
            if len(area): 
                for l in area:
                    fp.write(l)
            # extract leakage
            lkg = os.popen("awk '/Cell Leakage Power\W+=/ {print $0}' " + log_file).readlines()
            if len(lkg): 
                for l in lkg:
                    fp.write(l)
            # extract for dynamic
            dyn = os.popen("awk '/Total Dynamic Power\W+=/ {print $0}' " + log_file).readlines()
            if len(dyn): 
                for l in dyn:
                    fp.write(l)                    
            # extract peak mem
            mem = os.popen("awk '/Maximum memory usage for this session:/ {print $0}' " + log_file).readlines()
            if len(mem):
                for l in mem:
                    fp.write(l)
            # extract elapse
            elapse = os.popen("awk '/Elapsed time for this session:/ {print $0}' " + log_file).readlines()
            if len(elapse):
                for l in elapse:
                    fp.write(l)
            fp.close()
        os.chmod("%s" %output_file, stat.S_IRWXU+stat.S_IRWXG+stat.S_IRWXO)
    except Exception as e:
        # import traceback
        # traceback.print_exc()
        print e

    return

def zextract_xrpt(design, log, compress):
    if os.path.exists(design+'.'+log+'qp'):
        print "Found extracted file %s.%s.qp, skip extraction" %(design,log)
        return

    log_file = design+'.'+log+'.out.gz'
    output_file = './qor_profile/'+design+'.'+log+'.qp'
    try:
        with open(output_file, 'w') as fp:
        #extract frequency/wns
            slack = os.popen("zcat "+log_file+" | awk '/Design.*\(Setup\)/ {print $0}' ").readlines()
            if len(slack):
                for l in slack:
                    fp.write(l)
            clk = os.popen("zcat "+log_file+" | awk '/clock .* \(rise edge\)/ {print $0}' ").readlines()
            if len(clk): 
                for l in clk:
                    fp.write(l)
            unit = os.popen("zcat "+log_file+" | awk '/Time Unit.*:/ {print $0}' ").readlines()
            if len(unit): 
                for l in unit:
                    fp.write(l)
            #extract area
            area = os.popen("zcat "+log_file+" | awk '/Cell Area \(netlist\):/ {print $0}' ").readlines()
            if len(area): 
                for l in area:
                    fp.write(l)
            #extract leakage
            lkg = os.popen("zcat "+log_file+" | awk '/Cell Leakage Power\W+=/ {print $0}' ").readlines()
            if len(lkg): 
                for l in lkg:
                    fp.write(l)
            # extract for dynamic
            dyn = os.popen("zcat "+log_file+" | awk '/Total Dynamic Power\W+=/ {print $0}' ").readlines()
            if len(dyn): 
                for l in dyn:
                    fp.write(l)
            # extract peak mem
            mem = os.popen("zcat "+log_file+" | awk '/Maximum memory usage for this session:/ {print $0}' ").readlines()
            if len(mem):
                for l in mem:
                    fp.write(l)
            # extract elapse
            elapse = os.popen("zcat "+log_file+" | awk '/Elapsed time for this session:/ {print $0}' ").readlines()
            if len(elapse):
                for l in elapse:
                    fp.write(l)                

            fp.close()
        os.chmod("%s" %output_file, stat.S_IRWXU+stat.S_IRWXG+stat.S_IRWXO)
    except Exception as e:
        # import traceback
        # traceback.print_exc()
        print e

    return

# handling *.nw*rpt.out(.gz)
if __name__ == "__main__":
    import argparse
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-flows', nargs='+', required=True, help='Flow files to be extract.')       
        parser.add_argument('-compress', action="store_true", help='Compress hb.')  

        args = parser.parse_args()
        for flow in args.flows:
            if os.path.exists(flow):
                extract_flow(flow, args.compress)
            else:
                print "%s is not a valid path!" %flow
         

    except OSError as e:
        import traceback
        traceback.print_exc()
        print "I/O error({0}): {1} {2}".format(e.errno, e.strerror, e.filename)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print e

