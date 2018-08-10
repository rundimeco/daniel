#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import sys
import os
import re
import glob
sys.path.append('./rstr_max')
from tools_karkkainen_sanders import *
from rstr_max import *
import os
from tools import *

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
    if has_inter or weak_struct: 
      NE_ids=[x-len(set_id_text) for x in s_occur.difference(set_id_text)]
      if len(inter)>1:
        l_dist = [min(d, len(set_id_text)-d-1) for d in inter]
      else:
        l_dist = get_normalized_pos(ss, rstr.global_suffix)
      desc.append([ss, NE_ids, sorted(l_dist)])
  return desc

def get_score(ratio, dist):
  score = pow(ratio, 1+dist[0]*dist[1])
  return score

def filter_desc(desc, l_rsc, loc=False):
  out = []
  for ss, dis_list, distances in desc:
    for id_dis in dis_list:
      disease_name = l_rsc[id_dis]
      ratio = float(len(ss))/len(disease_name)
      if ss[0]!=disease_name[0]:
        if loc==True:
          continue#for country names the first character should not change
        else:
          ratio = ratio-0.1#penalty
      score = get_score(ratio, distances)
      out.append([score, disease_name, ss, distances])
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

def zoning(string):
  z = re.split("<p>", string)
  if len(z)==1:
    z = re.split("\n", string)
  z = [x for x in z if x!=""]
  if len(z)<3:#insufficient structure
    sentences = re.split("\. ", string)
    if len(sentences)<5:
      return z
    z = [sentences[:2],sentences[2:-3],sentences[-3:]]
    z = [" ".join(x) for x in z]
  return z

def analyze(string, ressource, options): 
  zones = zoning(string)
  dis_infos = get_desc(zones, ressource["diseases"])
  events = []
  loc_infos = []
  if len(dis_infos)>0:
    loc_infos = get_desc(zones, ressource["locations"], True)
    if len(loc_infos)==0:
      loc = [ressource["locations"]["default_value"]]
    else:
      loc = [loc_infos[0][1]]
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

def get_ressource(lg):
  dic = {}
  for rsc_type in ["diseases", "locations"]:
    path = "ressources/%s_%s.json"%(rsc_type, lg)
    if os.path.exists(path)==True:
      try:
        dic[rsc_type] = eval(open_utf8(path))
      except Exception as e:
        print "\n  Problem with ressource %s :"%path
        print e
        exit()
    else:
      print "  Ressource '%s' not found\n ->exiting"%path
      exit()
  try:
    path_towns= "ressources/towns_%s.json"%lg
    dic["towns"] = get_towns(path_towns)
  except:
#    print "  Non mandatory ressource '%s' not found"%path_towns
    dic["towns"]={}
  return dic

def open_utf8(path):
  f = codecs.open(path,"r", "utf-8")
  string = f.read()
  f.close()
  return string

def translate_justext():
  dic= eval(open_utf8("ressources/language_codes.json"))
  return dic

def get_lg_JT(lg_iso):
  dic_lg = translate_justext()
  lg = "unknown"
  if lg_iso in dic_lg:
    lg = dic_lg[lg_iso]
  return lg

def get_clean_html(o, lg_JT):
  print "toto"
  if o.is_clean == True:
    return open_utf8(o.document_path)
  try:
    import justext
    text = open_utf8(o.document_path)
    paragraphs = justext.justext(text, justext.get_stoplist(language))
    out = ""
    for paragraph in paragraphs:
      if not paragraph.is_boilerplate:
        out+="<p>%s</p>\n"%paragraph.text
    if o.verbose==True:
      print "-> Document cleaned"
  except:#to improve
    if o.verbose==True:
      print "Justext is missing, to install it: pip install justext"
    out = open_utf8(o.document_path)
  return out
  
def process(o, ressource = False, filtered=True):
  try:
    lg_iso = o.language
  except:
    lg_iso="unknown"
  lg_JT = get_lg_JT(lg_iso)
  string = get_clean_html(o, lg_JT)
  if ressource ==False:
    ressource = get_ressource(o.language)
  results = analyze(string, ressource, o)
  if filtered==True:
    if results["dis_infos"][0][0]<o.ratio:
      return {"events":[["N", "N", "N"]]}
  return results

if __name__=="__main__":
  options = get_args()
  try: os.makedirs("tmp")
  except: pass
  results = process(options, ressource = False, filtered = False)
  ratio = float(options.ratio)
  descriptions = eval(open_utf8("ressources/descriptions.json"))
  for key, val in results.iteritems():
    if val[0][0]<ratio:break
    print descriptions[key]
    for v in val:
      if v[0]<ratio:break
      print "  %s"%v
