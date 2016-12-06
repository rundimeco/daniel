from daniel import process
import glob
import sys
import json
import os

def translate_justext():
#TODO: add json ressource
  dic= {"id": "Indonesian"}
  return dic

if len(sys.argv)!=2:
  print "="*20
  print "USAGE : python process_corpus.py MYjson_file.json"
  print "for information about the format for daniel, see README.txt"
  print "="*20
else:
  try:
    os.makedirs("tmp")
  except:
    pass
  path_json = sys.argv[1]
  try:
    json = json.load(open(path_json))
  except:
    print "!"*20
    print "%s is not a valid json, see README.txt for more details"%path_json
    print "!"*20
    exit()
  dic_lg = translate_justext()
  for id_file, infos in json.iteritems():
    lg = "unknown"
    if "language" in infos:
      lg_iso = infos["language"]
      if lg_iso in dic_lg:
        lg = dic_lg[lg_iso]
    results = process(lg, infos["path"])
    print id_file, results["events"]
