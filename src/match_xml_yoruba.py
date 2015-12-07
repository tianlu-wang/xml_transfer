__author__ = 'koala'
#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import sys
import os
import subprocess
from bs4 import BeautifulSoup


def xml2lxf(xml, ltf_split, ltf_match, laf_split, laf_match):
    soup = BeautifulSoup(open(xml).read(), 'html.parser')
    for segment in soup.find_all("parallel"):
        name = segment.segment_source['id']
        cmd = ['cp', ltf_split
               +name+'.ltf.xml', ltf_match]
        subprocess.call(cmd)
        cmd = ['cp', laf_split
               +name+'.laf.xml', laf_match]
        subprocess.call(cmd)


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print 'USAGE:python match_xml_yoruba.py <input file><ltf_split dir><ltf_match dir><laf_split dir><laf_match dir>'
        print 'this script will match all files in elisa file & LDC file and put result in match dir'
    else:
        in_file = sys.argv[1]
        ltf_split = sys.argv[2]
        ltf_match = sys.argv[3]
        laf_split = sys.argv[4]
        laf_match = sys.argv[5]
        xml2lxf(in_file, ltf_split, ltf_match, laf_split, laf_match)




