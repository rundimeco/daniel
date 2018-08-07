from daniel import process
import glob
import sys
import json
import os
import time
import codecs
from tools import *
from daniel import get_ressource

class Struct:
  def __init__(self, **entries):
    self.__dict__.update(entries)

def open_utf8(path):
  f = codecs.open(path,"r", "utf-8")
  chaine = f.read()
  f.close()
  return chaine

def translate_justext():
  dic= eval(open_utf8("ressources/language_codes.json"))
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
  cpt_proc, cpt_rel = 0, 0
  output_dic, ressources = {}, {}
  not_found = []
  for id_file, infos in corpus_to_process.iteritems():
    if os.path.exists(infos["document_path"])==False:
      not_found.append(infos["document_path"])
      continue
    if "Elmoudjahid" not in infos["document_path"]:
      continue
    cpt_proc+=1
    output_dic[id_file] = infos
    infos["is_clean"] = options.is_clean
    lg = get_lg(infos)
    infos["language"] = lg
    ressources.setdefault(lg, get_ressource(lg))
    infos["ratio"] = options.ratio
    o = Struct(**infos)
    results = process(o, ressources[lg])
    if len(results["events"])>0:
      cpt_rel +=1
    output_dic[id_file]["annotations"] = results["events"]
    output_dic[id_file]["is_clean"] = str(output_dic[id_file]["is_clean"])
    if cpt_proc%100==0:
      print "%s documents proc, %s rel"%(str(cpt_proc), str(cpt_rel))
  output_path = write_output(output_dic, options)
  if len(not_found)>0:
    path_not_found = "tmp/files_not_found"
    print "--\n %s files not found\n"%str(len(not_found))
    print " list here : %s\n--"%(path_not_found)
    write_utf8(path_not_found, "\n".join(not_found))
  return cpt_proc, cpt_rel, output_path

if __name__=="__main__":
  start = time.clock()
  options = get_args()
  print options
  if options.corpus==None:
    print "Please specify a Json file (-c option), see README.txt for more informations about the format. To use the default example :"
    print "-c docs/Indonesian_GL.json"
    exit()
  try:
    os.makedirs("tmp")
  except:
    pass
  cpt_doc, cpt_rel, output_path = start_detection(options)
  end = time.clock()
  print "%s documents processed in %s seconds"%(str(cpt_doc), str(round(end-start, 4)))
  print "  %s relevant documents"%(str(cpt_rel))
  print "  Results written in %s"%output_path
  if options.evaluate==True:
    print "\nEvaluation\n :"
    cmd = "python evaluate.py %s %s"%(options.corpus, output_path)
    print "-->",cmd
    os.system(cmd)
