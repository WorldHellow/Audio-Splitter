# -*- coding: utf-8 -*-

f = open('data/demo.seg','r')
f2 = open('wav-splitting-script.sh','w')

linenum=0
for line in f.readlines():
	#print line
	l2 = line.split()
	#print l2
	n=0
	prev=""
	for x in l2:
		#print x
		n=n+1
		s=str(n-2)
		if(len(s)==1):
			s="000"+s
		if(len(s)==2):
			s="00"+s
		if(len(s)==3):
			s="0"+s
		u1=u"دو"
		#print prev, x
		if (prev != "") and (prev != x):
			str1 = "sox data/demo.wav " + s + ".wav trim " + str(float(prev)/100) + " " + str((float(x)-float(prev))/100) + "\n"
			f2.write(str1)
		prev=x

