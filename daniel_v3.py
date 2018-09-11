import re
import json
import sys
from daniel import process

#This is a third way to run daniel
#Unlike process_corpus, you do not need a JSON woth daniel format
#Unlike daniel.py it does not work through command line
# Please note that it will run much faster with pypy2

class Struct:
  def __init__(self, **entries):
    self.__dict__.update(entries)

text = "J'ai la dengue, \n c'est dengue"

infos = {
    "language": "fr",
    "is_clean":True,
    "ratio":0.8,
    "verbose":False,
    "debug":False
  }

o = Struct(**infos)

results = process(o, string = text)
print(results)
