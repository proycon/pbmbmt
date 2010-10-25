#!/usr/bin/python
# PBMBMT: PHRASE-BASED MEMORY-BASED MACHINE TRANSLATOR
# by Maarten van Gompel (proycon)
#   proycon AT anaproy DOT NL
#   http://proylt.anaproy.nl
# Licensed under the GNU Public License v3
import sys
import bz2

class PhraseList:
	def __init__(self,filename, quiet=False, freq_column = 1, phrase_column=3):
		"""Load a phrase list from file into memory (memory intensive!)"""
		self.phraselist = {}
		if filename.split(".")[-1] == "bz2":
			f = bz2.BZ2File(filename,'r')		
		else:
			f = open(filename,'r')
		linenum = 0
		while True:
			if not quiet:
				linenum += 1
				if (linenum % 100000) == 0:
					print >> sys.stderr, "Loading phrase-list: @%d" % linenum
			line = f.readline()
			if not line: 
				break
			
		 	#split into (trimmed) segments
			segments = [ segment.strip() for segment in line.split("\t") ]

			phrase = segments[phrase_column - 1]
			self.add(phrase, int(segments[freq_column - 1]))
		f.close()

	def add(self, phrase, score):
		self.phraselist[phrase] = score

	def exists(self, phrase):
		return (phrase in self.phraselist)

	def __contains__(self, phrase):
		return (phrase in self.phraselist)

	def __getitem__(self, phrase):
		try:
			score = self.phraselist[phrase]
		except:
			raise
		return score


