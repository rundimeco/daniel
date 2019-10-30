#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs, sys, os
import re
import glob
import math
sys.path.append('./rstr_max')
from tools_karkkainen_sanders import *
from rstr_max import *
import os
from tools import *
import json

def get_normalized_pos(ss, text):
  s = re.escape(ss)
  l_dist = [m.start() for m in re.finditer(s, text)]
  l_dist = [min(x, len(text)-x) for x in l_dist]
  return [float(x)/len(text) for x in l_dist]

def exploit_rstr(r,rstr, set_id_text):
  desc = []
  weak_struct = len(set_id_text)==1#if paragraph structuration is weak
  for (offset_end, nb), (l, start_plage) in r.iteritems():
    ss = rstr.global_suffix[offset_end-l:offset_end]
    s_occur = set()
    for o in xrange(start_plage, start_plage+nb) :
      id_str = rstr.idxString[rstr.res[o]]
      s_occur.add(id_str)
    inter = s_occur.intersection(set_id_text)
    has_inter = len(inter)>1 and len(s_occur)>len(inter)
    weak_and_repeat=(weak_struct and 0 in s_occur)#needs to be in 1st paragraph
    if has_inter or weak_and_repeat: 
      NE_ids=[x-len(set_id_text) for x in s_occur.difference(set_id_text)]
      if len(inter)>1:
        l_dist = [min(pos, len(set_id_text)-pos-1) for pos in inter]
      else:
        l_dist = get_normalized_pos(ss, rstr.global_suffix)
      l_dist = [round(x, 5) for x in l_dist]
      desc.append([ss, NE_ids, sorted(l_dist)])
  return desc

def get_score(ratio, dist):
  if ratio ==1:
    ratio = 0.99
  if dist[0]==1:
    return ratio
  elif dist[1]<=1:
    score = pow(ratio, 1+dist[0]*dist[1])
  else:
    score = pow(ratio, 1+dist[0]*math.log(dist[1]))
  if len(set(dist).intersection(set([0, 1])))==0:#not in headline:penalty
    score-=0.1
  return score

def filter_desc(desc, l_rsc, loc=False):
  out = []
  for ss, dis_list, distances in desc:
    for id_dis in dis_list:
      entity_name = l_rsc[id_dis].decode("utf-8")
      ratio = float(len(ss))/len(entity_name)
      if ss[0].lower()!=entity_name[0].lower():
        if loc==True:
          #for country names the first character should not change
          ratio = max(0, ratio-0.2)#penalty
        else:
          ratio = max(0, ratio-0.1)#penalty
      score = get_score(ratio, distances)
#      if score>0.75 and loc==False:
#        print([ss,ratio,score,distances])
      out.append([score, entity_name, ss, distances])
  return sorted(out,reverse=True)

def get_desc(string, rsc, loc = False):
  set_id_text = set()
  rstr = Rstr_max()
  cpt = 0
  l_rsc = rsc.keys()
  for s in string:
    rstr.add_str(s)
    set_id_text.add(cpt)
    cpt+=1
  for r in l_rsc:
    rstr.add_str(r.decode("utf-8"))
  r = rstr.go()
  desc = exploit_rstr(r,rstr, set_id_text)
  res = filter_desc(desc, l_rsc, loc)
  return res 

def zoning(string, options):
  zones = re.split("<p>", string)
  if len(zones)==1:
    zones = re.split("\n", string)
  zones = [x for x in zones if x!=""]
  sentences = re.split("\. |\</p>", string)
  sentences = [x for x in sentences if len(x)>2]
  if len(zones)<3:#insufficient paragraph/linebreaks structure
    if len(sentences)<5:#very short article
      zones = [string]
    elif len(zones)==2:#Title may have been extracted
      part = int(len(zones[1])/2)
      zones = [zones[0], zones[1][:part], zones[1][part:]]
    else:#No usable structure
      part = int(len(string)/3)
      zones = [string[:part], string[part:part*2], string[part*2:]]
#  elif len(sentences)<1*len(zones):
#    zones = [zones[0:3], zones[3:-2],zones[-2:]]
  if options.debug ==True:
    for zone in zones:
      print re.sub("\n", "--",zone[:70])
      print("")
    d = raw_input("Zoning ended, proceed to next step ?")
  return zones

def get_implicit_location(ressource, options):
  loc = ressource["locations"]["default_value"]
  try:
    source = options.source
    if source in ressource["sources"]:
      loc = ressource["sources"][source]
  except:
    pass
  return loc

def analyze(string, ressource, options): 
  zones = zoning(string, options)
  dis_infos = get_desc(zones, ressource["diseases"])
  if options.debug==True:
    for res in dis_infos[:10]:
      print "  ",round(res[0], 2)," \t", res[1], "\t", res[2]
    d = raw_input(" first 10 entities displayed, proceed to next step ?")
  events = []
  loc_infos = []
  if len(dis_infos)>0:
    loc_infos = get_desc(zones, ressource["locations"], True)
    if options.debug==True:
      print loc_infos[:10]
    if len(loc_infos)==0 or loc_infos[0][0]<0.5:
      loc =  get_implicit_location(ressource, options)
    else:
      loc = loc_infos[0][1]
    town_infos = get_desc(zones, ressource["towns"], True)
    if len(town_infos)>0:
      for t in town_infos:
        if t[0]<options.ratio:break
        loc.append((t[1], t[0]))
    for dis in dis_infos[:1]:
      events.append([dis[1], loc])
  dic_out = {"events":events, "dis_infos":dis_infos, "loc_infos":loc_infos}
  return dic_out

def get_towns(path):
  liste = eval(open_utf8(path))
  dic = {}
  for town, pop, region in liste:
    dic[town] = [pop, region]
  return dic

def get_ressource(lg, o):
  dic = {}
  mandatory_rsc = ["diseases", "locations"]
  for rsc_type in ["diseases", "locations", "sources"]:
    path = "ressources/%s_%s.json"%(rsc_type, lg)
    if os.path.exists(path)==True:
      try:
        dic[rsc_type] = eval(open_utf8(path))
      except Exception as e:
        if rsc_type in mandatory_rsc:
          print "\n  Problem with ressource %s :"%path
          print e
          exit()
        else:
          dic[rsc_type] = {}
    else:
      if rsc_type in mandatory_rsc:
        print "  Ressource '%s' not found\n ->exiting"%path
        exit()
  try:
    path_towns= "ressources/towns_%s.json"%lg
    dic["towns"] = get_towns(path_towns)
  except:
    if o.debug==True:
      print "  Non mandatory ressource '%s' not found"%path_towns
    dic["towns"]={}
  return dic

def open_utf8(path):
  f = codecs.open(path,"r", "utf-8")
  string = f.read()
  f.close()
  return string

def translate_justext():#TODO: with big corpus, getting it only once
  dic= eval(open_utf8("ressources/language_codes.json"))
  return dic

def get_lg_JT(lg_iso):
  dic_lg = translate_justext()
  lg = "unknown"
  if lg_iso in dic_lg:
    lg = dic_lg[lg_iso]
  return lg

def get_clean_html(o, lg_JT):
  if o.is_clean == True:
    return open_utf8(o.document_path)
  try:
    import justext
    text = open_utf8(o.document_path)
    paragraphs = justext.justext(text, justext.get_stoplist(lg_JT))
    out = ""
    for paragraph in paragraphs:
      if not paragraph.is_boilerplate:
        out+="<p>%s</p>\n"%paragraph.text
    if o.verbose==True:
      print "-> Document cleaned"
  except Exception as e:
    if o.verbose==True:
      print e
      print "** Probably Justext is missing, do 'pip install justext'"
    out = open_utf8(o.document_path)
  return out
  
def process(o, ressource = False, filtered=True, process_res = True, string = False):
  try:
    lg_iso = o.language
  except:
    lg_iso="unknown"
  lg_JT = get_lg_JT(lg_iso)
  if string == False:
    string = get_clean_html(o, lg_JT)
  if ressource ==False:
    ressource = get_ressource(lg_iso, o)
  results = analyze(string, ressource, o)
  if filtered==True:
    results["dis_infos"] = [x for x in results["dis_infos"] if x[0]>=o.ratio]
    results["loc_infos"] = [x for x in results["loc_infos"] if x[0]>=o.ratio]
    if len(results["dis_infos"])==0:
      return {"events":[["N", "N", "N"]]}
    return results
  if process_res == True:
    process_results(results, options)
  return results

def  process_results(results, options):
  ratio = float(options.ratio)
  descriptions = eval(open_utf8("ressources/descriptions.json"))
  if options.debug==True:
    print "-"*10, "RESULTS", "-"*10
    print(descriptions["events"])
    for event in results["events"]:
      print("  "+" ".join(event))
  if "dis_infos" not in results:
    return
  res_filtered = {}
  if len(results["dis_infos"])>0:
    if results["dis_infos"][0][0]>=options.ratio:
      for info in ["dis_infos", "loc_infos"]:
        res_filtered[info] = []
        for elems in results[info]:
          if elems[0]<options.ratio:
           break
          res_filtered[info].append(elems)
          if options.verbose==True or options.showrelevant==True:
            print options.document_path
            print(descriptions[info])
            print(eval(str(elems)))
            print("")
      print("-"*10)
  w = codecs.open(options.name_out, "w", "utf-8")
  w.write(json.dumps(res_filtered))
  w.close()

#  if options.verbose==True:
#    print "-"*30

if __name__=="__main__":
  options = get_args()
  print("For processing a json file, use 'process_corpus.py'")
  try: os.makedirs("tmp")
  except: pass
  results = process(options, ressource = False, filtered = False, process_res=True)
