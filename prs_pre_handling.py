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
from multiprocessing import Pool, Process
import threading
import sys 
import os
import commands
import stat
from qorProfiler import QorProfiler

RUN_LOG_LIST = ['dcopt','nwpopt','nwcopt','nwropt','nwfopt']
RPT_LOG_LIST = ['dcrpt','nwprpt','nwcrpt','nwrrpt','nwrpt']

def extract_flow(flow, compress, overwrite):
    print "Flow dir: %s" %flow
    print "Start log extraction!"
    designs = os.listdir(flow)
    
    for design in designs:
        design_dir = flow+'/'+design
        extract_design(design, design_dir, compress, overwrite)

def extract_design(design, design_dir, compress, overwrite):
    global threads
    global threads_full_flow

    if not os.path.isdir(design_dir): return

    print "handling design dir %s" %design        
    cwd = os.getcwd()
    os.chdir(design_dir)
    
    for log in RUN_LOG_LIST:
        if os.path.exists(design+'.'+log+'.out'):                
            p = Process(target=extract_xopt, args=(design, log, compress, design_dir, overwrite))
            threads.append(p)
        else:
            print "    Not found %s log, skip extraction" %log
    
    for log in RPT_LOG_LIST:
        if os.path.exists(design+'.'+log+'.out'):                
            p = Process(target=extract_xrpt, args=(design, log, compress, design_dir, overwrite))
            threads.append(p)
        elif os.path.exists(design+'.'+log+'.out.gz'):           
            p = Process(target=zextract_xrpt, args=(design, log, compress, design_dir, overwrite))
            threads.append(p)
        else:
            print "    Not found %s log, skip extraction" %log
    
    os.chdir(cwd)
    p = Process(target=extract_full_flow, args=(design_dir, compress, design_dir, overwrite))
    threads_full_flow.append(p)
        # p.start()

def extract_full_flow(design, compress, design_dir, overwrite):
    cwd = os.getcwd()
    os.chdir(design_dir)
    print "    Extract %s full flow pattern" %design
    try:
        qp = QorProfiler(input_list=[design], pattern="FULL_FLOW", compress=compress, dump_csv=True)
        qp.generate_profile()
    except Exception as e:
        print e

    os.chdir(cwd)
    return

def extract_xopt(design, log, compress, design_dir, overwrite):
    print "    Found %s %s log, do default pattern extraction" %(design,log)
    """
    if os.path.exists(design+'.'+log+'.qp'):
        print "    Found extracted file %s.%s.qp, skip extraction" %(design,log)
        return
    """
    # print "%s %s xopt dir is %s" %(design, log, os.getcwd())
    cwd = os.getcwd()
    os.chdir(design_dir)

    log_file = design+'.'+log+'.out'
    # output_file = design+'.'+log+'.qp'
    try:
        qp = QorProfiler(input_list=[log_file], compress=compress, dump_csv=True)
        qp.generate_profile()

    except Exception as e:
        # import traceback
        # traceback.print_exc()
        print "oops", cwd, design, log, design_dir, e
    os.chdir(cwd)
    return

def extract_xrpt(design, log, compress, design_dir, overwrite):
    print "    Found %s %s log, do rpt extraction" %(design,log)
    cwd = os.getcwd()
    os.chdir(design_dir)
    output_file = './qor_profile/'+design+'.'+log+'.qp'    
    if os.path.exists(output_file) and not overwrite:
        print "    Found extracted file %s.%s.qp, skip extraction" %(design,log)
        os.chdir(cwd)
        return

    try:                   
        os.makedirs("qor_profile") 
        os.system('chmod -R 777 qor_profile')                
    except:
        pass

    log_file = design+'.'+log+'.out'
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

    os.chdir(cwd)
    return

def zextract_xrpt(design, log, compress, design_dir, overwrite):
    print "    Found %s zipped log, do rpt extraction" %log
    cwd = os.getcwd()
    os.chdir(design_dir)
    output_file = './qor_profile/'+design+'.'+log+'.qp'
    if os.path.exists(output_file) and not overwrite:
        print "Found extracted file %s.%s.qp, skip extraction" %(design,log)
        os.chdir(cwd)
        return

    log_file = design+'.'+log+'.out.gz'
    
    try:                   
        os.makedirs("qor_profile") 
        os.system('chmod -R 777 qor_profile')                
    except:
        pass

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

    os.chdir(cwd)
    return

# handling *.nw*rpt.out(.gz)
if __name__ == "__main__":
    import argparse
    threads = []
    threads_full_flow = []
    try:
        print os.getcwd()
        parser = argparse.ArgumentParser()
        parser.add_argument('-flows', nargs='+', help='Extract designs qor info under specified flows.')
        parser.add_argument('-name', nargs=1, help='Extract qor info for current design.')      
        parser.add_argument('-designs', nargs='+', help='Extract qor info for specified designs.')    
        parser.add_argument('-compress', action="store_true", help='Compress hb.')  
        parser.add_argument('-overwrite', action="store_true", help='Overwrite existing qp cache.') 
        args = parser.parse_args()
        if not args.flows and not args.designs and not args.name:
            print "Please select '-flows' or '-designs' option!"
            exit()

        if args.flows:
            for flow in args.flows:
                if os.path.exists(flow):
                    extract_flow(os.path.abspath(flow), args.compress, args.overwrite)
                else:
                    print "%s is not a valid path!" %flow
        elif args.designs:
            for design in args.designs:
                if os.path.exists(design):
                    if design == '.':
                        design_dir = os.getcwd()
                        design_name = design_dir.split('/')[-1]
                    else:
                        design_name = design.split('/')[-1]
                        if not design_name:
                            design_name = design.split('/')[-2]
                        design_dir = os.path.abspath(design)
                    extract_design(design_name, design_dir, args.compress, args.overwrite)
        elif args.name:

            design_name = args.name[0]
            design_dir = os.getcwd()
            
            extract_design(design_name, design_dir, args.compress, args.overwrite)

        nloops = range(len(threads))
        for i in nloops:
            threads[i].start()
        for i in nloops:
            threads[i].join()
        
        # extract full flow ppa after simplified rpt qp cache generated
        nloops = range(len(threads_full_flow))
        for i in nloops:
            threads_full_flow[i].start()
        for i in nloops:
            threads_full_flow[i].join()
        print "All done!"

    except OSError as e:
        import traceback
        traceback.print_exc()
        print "I/O error({0}): {1} {2}".format(e.errno, e.strerror, e.filename)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print e

