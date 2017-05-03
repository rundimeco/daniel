from daniel import process
import glob
import sys
import json
import os
import time

def get_args():
  from optparse import OptionParser
  parser = OptionParser()
  parser.add_option("-c", "--corpus", dest="corpus",
                  help="JSON file for the corpus to process", metavar="CORPUS")
  parser.add_option("-l", "--language", dest="language", default ="fr",
                  help="Language to process")
  parser.add_option("-b", "--boilerplate", dest="boilerplate", 
                  default =False, action ="store_true", 
                  help="if set, boilerplate removal will be performed")
  parser.add_option("-e", "--evaluate", dest="evaluate", 
                  default=False, action="store_true",      
                  help = "Perform Evaluation")
  (options, args) = parser.parse_args()
  return options

def translate_justext():
#TODO: add json ressource
  dic= {"id": "Indonesian"}
  return dic

def  write_output(output_dic, options):
  output_path = "%s.results"%options.corpus
  output_json = json.dumps(output_dic, sort_keys=True, indent=2)
  wfi = open(output_path, "w")
  wfi.write(output_json)
  wfi.close()
  return output_path

def get_lg(infos):
  dic_lg = translate_justext()
  lg = "unknown"
  if "language" in infos:
    lg_iso = infos["language"]
    if lg_iso in dic_lg:
      lg = dic_lg[lg_iso]
  return lg

def  start_detection(options):
  corpus_to_process = json.load(open(options.corpus))
  cpt = 0
  output_dic = {}
  for id_file, infos in corpus_to_process.iteritems():
    output_dic[id_file] = infos
    cpt+=1
    lg = get_lg(infos)
    results = process(lg, infos["path"], options.boilerplate)
    if len(results["events"])>0:
      print id_file, results["events"]
      output_dic[id_file]["annotations"] = results["events"]
  output_path = write_output(output_dic, options)
  return cpt, output_path

if __name__=="__main__":
  start = time.clock()
  options = get_args()
  print options
  if options.corpus==None:
    print "Please specify a Json file (-c option), see README.txt for more informations about the format"
    exit()
  try:
    os.makedirs("tmp")
  except:
    pass
  cpt_doc, output_path = start_detection(options)
  end = time.clock()
  print "%s documents processed in %s seconds"%(str(cpt_doc), str(end-start))
  print "  Results written in %s"%output_path
  if options.evaluate==True:
    print "\nEvaluation\n"
    os.system("python evaluate.py %s %s"%(options.corpus, output_path))
