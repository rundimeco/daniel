import re
import sys
import json

def get_dic(path):
  print(path)
  f = open(path)
  dic = json.load(f)
  f.close()
  return dic

def get_verdict(GT, EV):
  if GT[0][0]!="N":
    if EV[0][0]!="N":
      verdict = "TP"
    else:
      verdict = "FN"
  else:
    if EV[0][0]!="N":
      verdict = "FP"
    else:
      verdict = "TN"
  return verdict

def get_measures(dic, beta=1):
  TP, FP, FN = dic["TP"], dic["FP"] , dic["FN"]
  if TP==0:
    return {"Recall":0, "Precision":0, "F%s-measure"%str(beta):0}
  R = float(TP)/(TP+FN)
  P = float(TP)/(TP+FP)
  B = beta*beta
  F = (1+B)*P*R/(B*P+R)
  return {"Recall":R, "Precision":P, "F%s-measure"%str(beta):F}

def get_results(dic_GT, dic_eval):
  dic_results = {x:0 for x in ["TP","FP","FN","TN"]}
  dic_results["Missing_GT"] = []
  for id_doc, infos in dic_eval.items():
    annot_eval = infos["annotations"]
    if id_doc in dic_GT:
      annot_GT = dic_GT[id_doc]["annotations"]  
      verdict = get_verdict(annot_GT, annot_eval)#TODO: add events
      dic_results[verdict]+=1
    else:
      dic_results["Missing_GT"].append(id_doc)
    if verdict=="FN":
      print(annot_GT, annot_eval)
      print(infos["document_path"])
      print("")
  if dic_results["TP"]+dic_results["FN"]==0:
    print("  No relevant documents in this Ground Truth")
  print(dic_results)
  print(get_measures(dic_results))
  print("  %s annotations missing"%str(len(dic_results["Missing_GT"])))

if len(sys.argv)!=3:
  print("USAGE : arg1=groundtruth file arg2 = result file")
  exit()

groundtruth_path = sys.argv[1]
eval_path = sys.argv[2]

dic_GT = get_dic(groundtruth_path)
dic_eval = get_dic(eval_path)

get_results(dic_GT, dic_eval)
