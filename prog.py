#!/usr/bin/env python

import os
import re
import argparse
import glob
from datetime import date

# Constants
DEFAULT_TARGET_DIR = os.path.expanduser('~/Pictures/original/')
MAX_DIR_NAME_LEN = 200  # Maximum length of the name for the event directory.
# Magic number, pathconf.NAME_MAX would be the real deal.
FILENAME_DESC = "" \
"The replaced file names follow a schema. Filename replacing is necessary because of:\n" \
"1) Cameras only use 4-digits for the image sequence number. Having unique file names prevents serious problems.\n" \
"2) Recognizable file names are a nice side effect.\n" \
"Let DSC_4321.JPG be the original filename, then the resulting filename is z3d04321.jpg\n" \
"Format: |constant prefix|year-2010|camera identifier|original 4-digits|.|lowercase file suffix|\n" \
"Current camera identifiers: d0 = Nikon D90, f0 = Nikon D600, v0 = Nikon 1 V1, s0 = Canon S95, ... , o0 = other\n" \
"When a camera shots more than 9999 pics in a calendar year, (or better, when the original 4-digits pass 9999)\n" \
"the camera identifier is incremented!"

class Output:
	"""Helper for sysout and logging with history"""
	hist = []

	def out(self, message):
		"""Print the message and saves it to the history"""
		print message
		self.hist.append(message)

o = Output()


class Directory:
	path = None

	def __init__(self, path):
		if not os.path.exists(path):
			raise 'Directory does not exist: <' + path + '>'
		if not os.path.isdir(path):
			raise path + ' is a file, not a directory!'
		self.path = path

	def str(self):
		return self.path


class Prog:

	def main (self):
		picImporter = self.parseInput()
		picImporter.repeatCommand()
		picImporter.buildFileList()
		picImporter.copy()

	def parseInput (self):
		# create parser
		parser = argparse.ArgumentParser(
			description='Import pictures (e.g. from sd card) to new folder in library.')
		parser.add_argument('-n', '--dry-run', required=False, action='store_true', 
			help='Does not copy anything, just a simulation.')
		parser.add_argument('event_name', 
			help='Short, descriptive name for the target subfolder.')
		parser.add_argument('-t target_dir', default=DEFAULT_TARGET_DIR, type=Directory, dest='t', 
			help='Library directory. Here a subdir is created for the renamed pictures. <default=' + DEFAULT_TARGET_DIR + '>')
		parser.add_argument('file', default='.',  
			#help='Files to be imported, or folder containing files to be imported. <default=.>', nargs='*',) TODO LATER
			help='Folder containing files to be imported. <default=.>', nargs='?')
		args = parser.parse_args()

		# interpret command
		return PicImporter(simulation = args.dry_run, eventName = args.event_name, libDir = args.t, origin = args.file)

class PicImporter:

	# Globals
	simulation = False
	eventName = '<No event name specified>'
	libDir = Directory(DEFAULT_TARGET_DIR)
	origin = '.'

	fourDigits = re.compile('.{0,20}(\d{4}).{0,20}') # match the first 4 digits, where before and after can be at max any 20 chars
	day = date.today().strftime("%y-%m-%d")
	files = []

	def __init__ (self, simulation, eventName, libDir, origin):
		self.simulation = simulation
		self.eventName = eventName
		self.libDir = libDir
		self.origin = origin

	def repeatCommand (self):
		if (self.simulation):
			o.out('dry-run ' * 10)
		else:
			o.out('real!   ' * 10)
		o.out('Event name = ' + self.eventName + ' target=' + self.libDir.str())

	def copy (self):
		"""Copy the files"""
		files = self.files
		targetDir = self.buildFolderName(self.eventName)
		o.out('Copy {0} files from {1} to {2}.'.format(len(files), self.libDir.str(), targetDir))
		for f in files:
			camIdentifier = self.decideWhichCamera(f)
			origDigits = self.extract4originalDigits(f)
			suffix = self.extractFileSuffixToLowercase(f)
			o.out('Copy {0} to {1}'.format(f, 'z3' + camIdentifier + origDigits + suffix)) # TODO year is static now

	def decideWhichCamera (self, picname):
		name = picname
		if (name.find("ZP0_") == 0):
			return "d0"
		if (name.find("DSC_xx")):
			return "TODO" # TODO
		camera = input("Known Cameras:\n d0 = Nikon D90\n f0 = Nikon D600\n v0 = Nikon 1 V1\n "
		               "s0 = Canon S95\n o0 = other\n e0 = extra\n u0 = unknown\n"
		               "Only these camera identifiers are valid.\n "
		               "\nPlease enter camera identifier:")

		if (len(camera) == 2) and (camera[1] == "0") and (camera[0] in "dfvsoeu"):
			return camera
		else:
			return self.decideWhichCamera(pic)

	def extract4originalDigits(self, filename):
		m = self.fourDigits.match(filename)
		if m:
			return m.group(1)
		else:
			raise NameError('Cannot convert filename, 4-digits not found: ' + filename)

	def extractFileSuffixToLowercase(self, filename):
		return filename[filename.rfind('.'):].lower()

	def buildFolderName (self, eventName):
		# TODO remove double slash /
		res = self.libDir.str() + '/' + self.day + '-' + self.prepareEventName(eventName)
		# TODO os.path.exists
		return res

	def buildFileList (self):
		self.files = [ f for f in os.listdir(self.origin) if os.path.isfile(os.path.join(self.origin,f)) ]

	@staticmethod
	def prepareEventName (inEventName):
		""" For practical reasons the eventName should not contain special characters
		    nor whitespaces, and be of 'limited' size. """
		eventName = inEventName
		assert 0 < len(eventName) < MAX_DIR_NAME_LEN

		eventName = re.sub('[\s]+', '_', eventName) # replace whitespaces greedy with _
		eventName = re.sub('[\W]+', 'x', eventName) # replace all non-ASCII-word chars greedy with x
		if (inEventName != eventName):
			o.out('Replaced Event Name to ' + eventName)

		return eventName



Prog().main()