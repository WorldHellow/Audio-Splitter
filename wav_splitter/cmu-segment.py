#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os, os.path, shutil, sys, tempfile
from ioLib import uwrite, uclose
from xmlWriterLib import openXml, closeXml

SOX_TOOL = '/usr/bin/sox'
CMU_TOOLS = '/home/atahir/work/from_rcms/shakeeb_cmu/CMUseg_0.5/bin/linux'

##### options for wave2mfcc
# FILTER PARAMETERS
# -----------------
# "-alpha"        This is a simple IIR preemphasis filter of the form y[n] = y[n] - alpha*y[n-1]
# "-srate"        Sets the sampling rate of the input file in Hz
# "-frate"        Sets the output frame rate (number of vectors) in Hz
# "-wlen"         Is the size of the hamming window for calculating the FFT
# "-dft"          Is the number of points used in computing the DFT (1/2 the FFT size)
# "-nfilt"        Is the number of triangular filters to use
# "-nlog"         Is the portion of traingular filters that will be logarithmically spaced in freq
# "-logsp"        Is the ratio to be used in spacing the logarithmically spaced filters
# "-linsp"        Is the separation to be used in spacing the linearly spaced filters
# "-lowerf"       Is the lower edge of the lowest frequency filter
# "-upperf"       Is the higher edge of the highest frequency filter
# "-ncep"         Is the number of features to generate (13 for cep, 40 for logspec)

# INPUT PROCESSING
# ----------------
# "-DC"           Will perform causual DC offset removal.
# "-dither"       Will add 1/2-bit noise to the signal which is necessary if the data
#                 contains lots of zeros (such as mu-law data) since the log will otherwise
#                 be undefined.
MFCC_OPT = '-srate 16000 -frate 100 -wlen 0.025'

##### options for UTT_Kseg
# [-w <value>] width of comparison windows (in # frames) def=250
# [-s <value>] scanning length for peaks (in # frames) def=500
# [-h <value>] length of smoothing window (Hamming, in # frames) def=100
# [-m <value>] minimum Kseg threshold def=0.020
# [-f <value>] variance floor def=0.000
# KSEG_OPT = ''
# CMU Hub 4 1996 Evaluation Settings
KSEG_OPT = '-h 100 -w 250 -s 500 -v -m 0.05 -f 0.1'

##### options of UTT_findsil
# Silence Detection Algorithm
# ---------------------------
# 1. Define an "inner" and "outer" window.  Centerpoints for these windows are the same.
#         Size of inner and outer window defined by "-sw <value>" and "-sW <value>"
# 2. Slide the window pair along a region of interest, when the following criterion are
#    met, and they are also maximized, a silence is detected:
#         Region of interest (guided mode) defined by "-sn <value>"
#         Region of interest (free running) defined by "-sf <value>"
#         Dynamic range of the inner window < "-sd <value>"
#         Mean Power in inner window < Maximum Power in outer window - "-st <value>"
#         Maximum segment length = "-m <value>"
#         Minimum segment length = "-n <value>"
# 3. If neither criterion is met, no silence is detected.
#
# [-D] output silence details (depth,DNR)
# [-st <value>] silence threshold (dB) def=20.00
# [-sd <value>] silence DN (dB) def=10.00
# [-sn <value>] width of silence search region (in # frames) def=200
# [-sf <value>] width of silence search region (in # frames) for fakes def=500
# [-sw <value>] width of silence inner window (in # frames) def=10
# [-sW <value>] width of silence outer window (in # frames) def=200
# [-m <value>] maximum length restriction (0=unlimited) def=0
# [-n <value>] minimum length restriction (0=unlimited) def=0
# FINDSIL_OPT = '-st 10'
# CMU Hub 4 1996 Evaluation Settings
FINDSIL_OPT = '-sw 7 -sW 200 -sn 200 -st 8 -sd 10 -n 30'

class TempDir:
	def __init__(self, tmpDir = None, cleanUp = True):
		if tmpDir is None:
			self.tmpDir = tempfile.mkdtemp()
		else:
			self.tmpDir = tmpDir
			if not os.path.isdir(self.tmpDir):
				os.system('mkdir -p %s' % self.tmpDir)
		self.cleanUp = cleanUp
		assert os.path.isdir(self.tmpDir)

	def __del__(self):
		assert self.tmpDir is not None
		if self.cleanUp:
			import shutil
			shutil.rmtree(self.tmpDir)
		self.tmpDir = None
	
	def dir(self):
		assert self.tmpDir
		return self.tmpDir

	def path(self, filename):
		assert self.tmpDir
		return os.path.join(self.tmpDir, filename)

	def rm(self, filename):
		assert self.tmpDir
		os.unlink(os.path.join(self.tmpDir, filename))



class Segmenter:
	def __init__(self, name, corpusDir, audioDir, tmpDir, cleanUp):
		self.name = name
		self.corpusDir = corpusDir
		self.audioDir = audioDir
		self.tmpDir = TempDir(tmpDir, cleanUp)
		self.corpusFile = os.path.join(self.corpusDir, self.name + '.corpus.gz')
		self.segFile = os.path.join(self.corpusDir, self.name + '.segments')
		print 'Corpus file     : %s' % self.corpusFile
		print 'Segments file   : %s' % self.segFile
		print 'Temporary files : %s' % self.tmpDir.dir()

	def run(self, cmd):
		print '\nExecute: "%s" ...' % cmd
		os.system(cmd)

	def extractMfccs(self, name, wavFile):
                if(not os.path.exists(wavFile)):
                  print "error: wav file does not exist", wavFile
		assert os.path.exists(wavFile)
		rawFile = self.tmpDir.path(name + '.raw')
		self.run('%s %s -t raw -s -r 16000 -c 1 %s' % \
			(SOX_TOOL, wavFile, rawFile))
		mfccFile = self.tmpDir.path(name + '.mfcc')
		mfccLogFile = mfccFile + '.log'
		self.run('%s/wave2mfcc %s -raw L -i %s -sphinx -o %s -verbose &> %s' % \
				 (CMU_TOOLS, MFCC_OPT, rawFile, mfccFile, mfccLogFile))
		nFrames = None
		for l in iterLines(mfccLogFile):
			if l.startswith('total of'):
				cols = l.split()
				assert cols[6] == 'frames'
				nFrames = int(cols[5])
		assert nFrames is not None
		return (mfccFile, nFrames)

	def extractSegments(self, name, mfccFile, secList):
		print 'inside extractSegments'
		ctrFile = self.tmpDir.path(name + '.ctr')
		fd = uwrite(ctrFile)
		for i, r in enumerate(secList):
			print >> fd, '%s %d %d %d' % (mfccFile, r[0], r[1], (i+1))
		uclose(fd)
		bpFile = self.tmpDir.path(name + '.bp')
		ksegLogFile = self.tmpDir.path(name + '.kseg.log')
		self.run('%s/UTT_Kseg %s -c %s -r %s -v 2>&1 &> %s' % \
				 (CMU_TOOLS, KSEG_OPT, ctrFile, bpFile, ksegLogFile))
		segFile = self.tmpDir.path(name + '.seg')
		findSilLogFile = self.tmpDir.path(name + '.findsil.log')
		self.run('%s/UTT_findsil %s -c %s -r %s -v 2>&1 &> %s' % \
				 (CMU_TOOLS, FINDSIL_OPT, bpFile, segFile, findSilLogFile))
		return (bpFile, segFile)

	def openCorpus(self):
		self.xml = openXml(self.corpusFile)
		self.xml.open('corpus', name=self.name)
		# speaker
		# condition
		self.segFd = uwrite(self.segFile)

	def closeCorpus(self):
		self.xml.close()
		closeXml(self.xml)
		self.xml = None
		uclose(self.segFd)
		self.segFd = None

	def printRecording(self, wavFile, recName, secList, segFile):
		segList = []
		for l in iterLines(segFile):
			segList.append( [ int(c) for c in l.split()[1:] ] )
		assert len(secList) == len(segList)
		self.xml.open('recording', name=recName, audio=os.path.abspath(wavFile))
		for section, segments in zip(secList, segList):
			if section[0] + 30 < segments[0]:
				segments.insert(0, section[0])
			else:
				segments[0] = section[0]
			if segments[-1] + 30 < section[-1]:
				segments.append(section[-1])
			else:
				segments[-1] = section[-1]
			nextStart = segments[0] - 1
			for end in segments[1:]:
				end -= 1
				startTime, endTime = float(nextStart) / 100.0, float(end) / 100.0
				segName = '%s_%s_%s' % (
					recName, \
					str(int(round(startTime * 1000.0))).zfill(10), \
					str(int(round(endTime * 1000.0))).zfill(10))
				nextStart = end
				self.xml.open('segment', name=segName, start='%.3f' % startTime, end='%.3f' % endTime)
				self.xml.empty('orth')
				self.xml.close()
				print >> self.segFd, segName
		self.xml.close()

	def wav2seg(self, wavFiles):
		self.openCorpus()
		for wavFile in wavFiles:
			recName = os.path.basename(wavFile)
			if recName.endswith('.wav'):
				recName = recName[:-4]
			wavFile = os.path.join(self.audioDir, wavFile)
			mfccFile, nFrames = self.extractMfccs(recName, wavFile)
			secList = [ (1, nFrames - 1) ]
			bpFile, segFile = self.extractSegments(recName, mfccFile, secList)
			self.printRecording(wavFile, recName, secList, segFile)
		self.closeCorpus()

	def uem2seg(self, uemFiles):
		self.openCorpus()
		recNames = []
		secLists = {}
		for uemFile in uemFiles:
			for l in iterLines(uemFile):
				cols = l.split()
				recName, start, end = cols[0], int(float(cols[2]) * 100.0) + 1, int(float(cols[3]) * 100.0) + 1
				segList = secLists.get(recName, None)
				if recName in secLists:
					secLists[recName].append( (start, end) )
				else:
					recNames.append(recName)
					secLists[recName] = [ (start, end) ]
		for recName in recNames:
			wavFile = os.path.join(self.audioDir, recName + '.wav')
			mfccFile, nFrames = self.extractMfccs(recName, wavFile)
			secList = secLists[recName]
			extractSecList = []
			for section in secList:
				extractSecList.append( (min(section[0], nFrames - 1), min(section[-1], nFrames - 1) ) )
			bpFile, segFile = self.extractSegments(recName, mfccFile, extractSecList)
			self.printRecording(wavFile, recName, secList, segFile)
		self.closeCorpus()



if __name__ == '__main__':	
	from optparse import OptionParser
	from ioLib import iterLines
	optparser = OptionParser( \
	usage= \
	'usage:\n %prog [OPTION] <wav-file> [<wav-file> [...]] | <uem-file> [<uem-file> [...]]\n')
	optparser.add_option("-t", "--temp-dir", dest="tmpDir", default=None,
						 help="temporary directory", metavar="DIR")
	optparser.add_option("", "--no-clean-up", dest="noCleanUp", action="store_true", default=False,
						 help="don't delete temporary directory", metavar="BOOL")
	optparser.add_option("-a", "--audio-dir", dest="audioDir", default='.',
						 help="audio directory", metavar="DIR")
	optparser.add_option("-o", "--output-dir", dest="outputDir", default='.',
						 help="output directory", metavar="DIR")
	optparser.add_option("-n", "--name", dest="name", default=None,
						 help="corpus name", metavar="STRING")
	optparser.add_option("-u", "--uem", dest="isUem", action="store_true", default=False,
						 help="uem file; default is wav file", metavar="BOOL")
	optparser.add_option("-w", "--wav", dest="isWav", action="store_true", default=False,
						 help="wav file; default is wav file", metavar="BOOL")
	opts, args = optparser.parse_args()
	assert len(args) > 0
	inType = 0
	if opts.isWav:
		inType = 1
	elif opts.isUem:
		inType = 2
	else:
		suffix = args[0][-4:].lower()
		if suffix == '.wav':
			inType = 1
		elif suffix == '.uem':
			inType = 2
		else:
			print 'Unknown file type'
			sys.exit(1)
	if inType == 1:
		if opts.name is None:
			name = os.path.basename(args[0])
			if name.endswith('.wav'):
				name = name[:-4]
		else:
			name = opts.name
		segmenter = Segmenter(name, "tp", opts.audioDir, opts.tmpDir, not opts.noCleanUp)
		segmenter.wav2seg(args)
	elif inType == 2:
		if opts.name is None:
			name = os.path.basename(args[0])
			if name.endswith('.uem'):
				name = name[:-4]
		else:
			name = opts.name
		segmenter = Segmenter(name, opts.outputDir, opts.audioDir, opts.tmpDir, not opts.noCleanUp)
		segmenter.uem2seg(args)
	else:
		assert False
