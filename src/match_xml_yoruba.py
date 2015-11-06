__author__ = 'koala'
#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import sys
import os
import subprocess

from bs4 import BeautifulSoup

def xml2lxf(xml):
    soup = BeautifulSoup(open(xml).read(), 'html.parser')
    for segment in soup.find_all("parallel"):
        name = segment.segment_source['id']
        cmd = ['cp', './data/Yoruba_data/annotation/entity_annotation/simple/with_tone/ltf_split/'
               +name+'.ltf.xml', './data/Yoruba_data/annotation/entity_annotation/simple/with_tone/match_ltf']
        subprocess.call(cmd)
        cmd = ['cp', './data/Yoruba_data/annotation/entity_annotation/simple/with_tone/laf_split/'
               +name+'.laf.xml', './data/Yoruba_data/annotation/entity_annotation/simple/with_tone/match_laf']
        subprocess.call(cmd)




xml2lxf('/Users/koala/Documents/lab/Blender/LORELEI/active_learning/elisa.yor.package.y1r1.v1/elisa.yor-eng.train.y1r1.v1.xml')




