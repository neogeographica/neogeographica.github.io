"""
DESCRIPTION
Elements is a powerful tool for experienced web developers to build sites using templates, 
simple replacements and scripts.

Elements won't help write the code, but it will make changing, updating and maintaining 
the code as simple and reliable as possible.

Elements eliminates the need to do site-wide search and replace.

Elements scripts have access to information about the file name and file path to 
programatically generate the bits of template code that change from page to page.
"""

import os, sys, string, shutil, copy, time, types, webbrowser, exceptions, re
ElementsVersion = "1.1.1"

__true__ = ('true', 'yes', '1') #true is not a keyword in Python

def parseFile (obj, f):
	"Return a dictionary containing the elements of a single element or content file."
	fd = open(f, 'r') # XXX if this was urllib.open(), we could open from anywhere
	lines = fd.read()
	fd.close
	lines = lines.replace (LineSep.sep['unix'], '\n')
	lines = lines.replace (LineSep.sep['mac'], '\n')
	lines = lines.replace (LineSep.sep['win'], '\n')
	lines = lines.split ('\n')
	
	fileElements = {}
	multiLine = 0 # not a multi line element
	previousBlank = 0 # the previous line was not ''
	beginContent = 0
	for this in range(len(lines)):
		if (lines[this][:1] == obj.elements["elementMarker"]): # is it an element?
			previousBlank = 0 # says we're still in the elements section
			if multiLine: # end of previous multiline, get ready to begin new element
				multiLine = 0
				if (value[0] == '') and (len(value) > 1): del(value[0]) # multilines don't start with a blank line
				fileElements[element] = value
			try:
				element, value = lines[this][1:].split (" ", 1)
			except ValueError:
				try:
					element, value = lines[this][1:].split (obj.elements["elementMarker"], 1)
					multiLine = 1
					value = [value] # cast to list for efficient string building
				except ValueError:
					element, value = lines[this][1:], ''
			if element.find('#') > -1: # e.g "#asdf# asdf"
				element, value = lines[this][1:].split (obj.elements["elementMarker"], 1)
				multiLine = 1
				value = [value.lstrip()] # strip, to list
			if element == '': continue # skip if no element name
			elif element == 'file:': # XXX unfortunatley, the value of dir: & file: is not allowed to be processed by eval
				try: fileElements.update(parseFile(obj, value))
				except: error('A problem occurred reading file: '+ value)
			elif element == 'dir:':
				try: Directory.dirElements (obj, value, elemDir=1) # XXX this errors if #dir: is in the content file/or perhaps when in content file and its the first content file
				except: error('A problem occurred reading dir: '+ value)
			else: # not mulit-line
				fileElements[element] = value
		elif multiLine: # in the middle of collecting lines of a multiline # note that lines beginning with "#" are not allowed in multiline
			value.append(lines[this])
		elif (lines[this] == '') and (not previousBlank): #(sys.platform == 'mac' ) and  # it may be a Windows file where each line is "\n\n" to other platforms
			# allowing Windows element files on Mac & Unix requires that elements may be separated by one blank line on any platform
			previousBlank = 1
		else: # begin body content
			beginContent = 1
			break
	
	if beginContent:
		lines = lines[this - previousBlank:] # drop the element lines, keep that initial blank line if it exists
	else: # the last line was an element, content for this file is empty
		lines = ['']

	# all done with elements, lines now == the file content
	
	fileName, fileExt = os.path.splitext(os.path.basename(f))
	
	# XXX the following does not account for elementFolder files!
	if (fileName[0] == obj.elements["elementFilePrefix"]): # it's an element file
		fileName = fileName[1:]
	
	fileElements[fileName] = lines
	
	# element files set their values here, but the page is last, and overwrites the values
	fileElements['fileName'] = fileName
	fileElements['fileExt'] = fileExt
	fileElements['filePath'] = f
	return fileElements

def copyOneAsset (obj, src):
	if isSysFile(src): return
	shutil.copyfile(src, getOutputPath(obj, src))

def appendElements(obj, f):
	"A wrapper around parseFile(), allows us to call parseFile on other files from scripts."
	obj.elements.update(parseFile (obj, f))

def getOutputPath(obj, srcPath):
	"Replace the siteSrc part of a file path with the siteDest."
	return buildPath(obj.elements['siteDest'], srcPath[obj.elements['siteSrcLen']:])
	#return os.path.join(obj.elements['siteDest'], srcPath[obj.elements['siteSrcLen']+1:])
	
def buildPath(root, fragment):
	"os.path.join workaround for platform differences."
	# PC: PRESENCE OF leading pathSep in the 2nd part will look like an absolute path and cause the dropping of the 1st part
	# MAC: LACK OF leading pathSep in the 2nd part will look like an absolute path and cause the dropping of the 1st part
	if not fragment: return root
	if sys.platform == "mac":
		if fragment[0] != os.sep:
			fragment = os.sep + fragment
	else:
		if fragment[0] == os.sep:
			fragment = fragment[1:]
	return os.path.join(root, fragment)
	
	
class LineSep:
	sep = {}
	if sys.platform == 'mac': # mac has the symbols swapped
		sep['mac'] = "\n"
		sep['unix'] = "\r"
		sep['win'] = "\n\r"
	else:
		sep['mac'] = "\r"
		sep['unix'] = "\n"
		sep['win'] = "\r\n"

class Site:
	"The base container for all processing."
	def __init__(self, siteSrc, siteDest, settingsFile, processSubDir=''):
		self.elements = {}
		self.elements['elementMarker'] = "#" # defined here only for appendElements(settingsFile)
		self.elements['elementFilePrefix'] = "`" # defined here only for appendElements(settingsFile)
		self.getSettings(settingsFile)
		self.siteSrc = self.elements['siteSrc'] = siteSrc
		self.siteDest = self.elements['siteDest'] = siteDest
		self.siteSrcLen = self.elements['siteSrcLen'] = len(self.siteSrc) # used in getOutputPath()
		self.processSubDir = processSubDir

	def getSettings(self, settingsFile):
		"Get defaults to begin the Elements process."
		try: appendElements (self, settingsFile)
		except IOError: error("Problem reading 'ElementsSettings.txt' file at: "+ settingsFile +'.')
		self.elements["ElementsVersion"] = ElementsVersion
		self.elements['pathNames'] = []
		self.elements['pathToTop'] = ''
		self.elements['currentDepth'] = -1
		
	def processSite(self):
		self.startSecs = time.time()
		msg("Begin processing "+ self.siteSrc +" at "+ time.strftime('%I:%M:%S'))
		self.processSrc = self.siteSrc
		if self.processSubDir: # only process a sub-section of self.siteSrc
			dirs = self.processSubDir.split('/')
			for subDir in dirs:
				dir = Directory(self, self.processSrc)
				try: dir.dirElements(self.processSrc)
				except OSError: error("processSubDir: can't find directory: "+ self.processSrc)
				dir.elements['copyAssets'] = 0
				self.elements.update(dir.elements)
				dir.dirDestPath()
				self.processSrc = os.path.join(self.processSrc, subDir)
		if os.path.isfile(self.processSrc):
			try: Page(self, self.processSrc)
			except OSError: error("processSubDir can't find file: "+ self.processSrc)
		else:
			dir = Directory(self, self.processSrc)
			dir.processDir()
		msg("Finished processing at "+ time.strftime('%I:%M:%S') +' after '+ str(round(time.time() - self.startSecs, 2)) +' seconds.')

class Directory:
	"Consolidate all the self.elements into one Directory.elements dictionary."
	def __init__(self, parent, srcDir):
		self.elements = copy.deepcopy(parent.elements)
		self.srcDir = self.elements['srcDir'] = srcDir
		self.destDir = self.elements['destDir'] = getOutputPath(self, self.srcDir)
		
		self.elements['currentDepth'] = self.elements['currentDepth'] +1
		if self.elements['currentDepth'] > 0:
			self.elements['pathToTop'] = self.elements['pathToTop'] + "../"
			self.elements['pathNames'].append(os.path.basename(srcDir))

	def processDir(self):
		msg("Process Directory " + self.srcDir)
		self.dirElements(self.srcDir)
		self.dirDestPath()
		self.dirContent()

	def dirElements (self, dir, elemDir=0): # dir!=self.srcDir if elemDir==1
		"Get all the elements of one directory into one dictionary and append it to self.elements."
		for name in os.listdir(dir):
			if isSysFile(name): continue
			if (name[0]==self.elements["elementFilePrefix"]) or (elemDir==1): # elemDir==1 means we're in an element directory
				f = os.path.join(dir, name)
				if os.path.isdir(f): self.dirElements(f, elemDir=1)
				else: appendElements (self, f)

	def dirDestPath(self):
		"Create the destDir if necessary."
		if os.path.exists(self.destDir):
			if self.elements['copyAssets'] in __true__:
				try:
					shutil.rmtree(self.destDir)
					os.mkdir(self.destDir, 0775)
				except:
					error('Unable to delete/create directory '+ self.destDir)
		else: 
			try:
				os.mkdir(self.destDir, 0775)
			except:
				error('Unable to create directory '+ self.destDir)
	
	def dirContent (self):
		"Process all the content and, if copyAssets is true, copy the assets."
		names = os.listdir(self.srcDir)
		for name in names:
			if isSysFile(name): continue
			f = os.path.join(self.srcDir, name)
			if name[0] != self.elements["elementFilePrefix"]:
				if os.path.isdir(f):
					dir = Directory(self, f)
					dir.processDir()
				else:
					if self.elements["contentExtensions"].find(os.path.splitext(f)[1]) > -1:
						Page (self, f)
					elif self.elements['copyAssets'] in __true__:
						copyOneAsset(self, f)

class Page:
	"Process one page of content."
	def __init__(self, parent, srcFile):
		self.elements = copy.deepcopy(parent.elements)
		appendElements (self, srcFile)
		self.elements.update(globals()) # deepcopy breaks when this is the first thing put in Site.elements
		self.srcFile = self.elements['srcFile'] = srcFile
		
		self.elements['page'] = self
		self.destFile = self.elements['destFile'] = getOutputPath(self, self.srcFile)
		self.elements['pathNames'].append(self.elements['fileName'])
		self.elements['pathNameStr'] = string.join(self.elements['pathNames'], '.')
		self.processPage()
	
	def pageInfo(self):
		"Print the page elements dictionary to the terminal window."
		s = ['','*** Results of pageInfo()', '']
		keys = self.elements.keys()
		keys.sort()
		for key in keys:
			s.append(key +': '+ str(self.elements[key]))
			s.append('')
		msg(string.join(s, '\n'))
		
	def processPage(self):
		msg("Process "+ self.srcFile)
		#compile all scripts
		for phrase in self.elements.keys():
			if phrase.find(self.elements["codeBlockMarker"]) == 0: # it is Python code
				try:
					phraseContent = string.join (self.elements[phrase], '\n') + '\n'
					exec compile(phraseContent, '<compiled code>', 'exec') in self.elements
				except SyntaxError, (errno, strerror):
					warning('SyntaxError in '+ phrase +': '+ strerror[3].rstrip())
					del(self.elements[phrase]) # does this help or hurt anything?
	
		# process elements in element names, scripts work too!
		for key in self.elements.keys(): #we allow {element} in the element name: "#[fileName]On On"
			start = 0
			if ((key.find(self.elements["markerStart"]) > -1) and (key.find(self.elements["markerEnd"]) > -1)):
				s = key
				while 1:
					start = string.find(s, self.elements["markerStart"], start)
					end = string.find(s, self.elements["markerEnd"], start)
					if start < 0 or end < 0:
						break
					phrase = s[start +1:end]
					try:
						s = s.replace(self.elements["markerStart"] + phrase + self.elements["markerEnd"], str(eval(phrase, self.elements))) #the replace value must be a string
						start = 0
					except:
						start += 1
						continue
				if self.elements.has_key(s): #evaluated element names cannot overwrite static names
					warning('element name "'+ str(key) +'" evaluating to: "'+ str(s) +'" cannot overwrite existing value '+ str(s) +' == '+ str(self.elements[s]))
				else:
					self.elements[s] = self.elements[key]
				
		# get the template & content
		if type(self.elements['firstElement']) == types.StringType:
			self.elements['pageString'] = [self.elements['firstElement']]
			lineCt = 1
		else:
			self.elements['pageString'] = self.elements['firstElement'][:]
			lineCt = len(self.elements['pageString'])
			
		if self.elements['pageString'] == ['']: # this is always a user error?
			warning("The firstElement was set to '' (empty string).")
			lineCt = 1
		
		# do the replacements
		end = line = foundOne = 0
		while 1:
			# find a phrase
			end = string.find(self.elements['pageString'][line], self.elements["markerEnd"], end)
			start = string.rfind(self.elements['pageString'][line], self.elements["markerStart"], 0, end)
			if start < 0 or end < 0:
				end = 0
				line += 1
				if line == lineCt:
					if foundOne == 0: break
					else: end = line = foundOne = 0
				continue
			if start > 0 and self.elements['pageString'][line][start-1: start] == '\\': # skip escaped items
				end += 1
				continue
			phrase = self.elements['pageString'][line][start +1: end]
			
			# get the phrase value
			if self.elements.has_key(phrase):
				newLines = self.elements[phrase] # illegal variable names are OK as element[key]
			else:
				try:
					newLines = eval(phrase, self.elements) # call functions, etc.
				except StandardError, e:
					if (self.elements['debugOn'] in __true__) and foundOne == 0:
						warning(str(e) +'. calling: '+ phrase +' in "'+ self.elements['pageString'][line] +'"')
					end += 1
					continue

			# insert the value
			if type(newLines) == types.ListType:
				newLines = newLines[:] # make a copy so we don't mess with the self.elements value
				newLines[0] = self.elements['pageString'][line][0: start] + newLines[0]
				newLines[len(newLines)-1] = newLines[len(newLines)-1] + self.elements['pageString'][line][end +1:]
				lineCt = lineCt + len(newLines) -1
			else:
				if type(newLines) != types.StringType:
					newLines = str(newLines)
				newLines = [self.elements['pageString'][line][0: start] + newLines + self.elements['pageString'][line][end +1:]]
			self.elements['pageString'][line: line +1] = newLines
			end = start
			foundOne = 1
	
		self.elements['pageString'] = string.join(self.elements['pageString'], LineSep.sep[self.elements['lineSep']])
		self.elements['pageString'] = self.elements['pageString'].replace ('\\' + self.elements["markerStart"], self.elements["markerStart"])
		writeFile(self.elements['pageString'], self.destFile)

class ElementsError(exceptions.Exception):
	def __init__(self, args = None):
		self.args = args

def error(s):
	"Raise an ElementsError."
	raise ElementsError, s

def warning(s):
	"Warning."
	print '*** Warning: '+ s

def msg(s):
	"Just print the string. The function is here in case some day we want to do something different."
	print s
	
def help ():
	print __doc__
	
def isSysFile(f):
	"Avoid pesky system files by file name."
	name = os.path.basename(f)
	if name == "Icon\r": return 1 # skip invisible Mac Icon files
	if name[0] == '.': return 1 #skip invisible Unix files
	return 0 # don't skip
	
def writeFile (s, f):
	"Write to file."
	fd = open(f, 'w')
	fd.write(s)
	msg("  Write "+ f)
	fd.close()

def process (srcDir, destDirIn, processSubDir='', displayTarget=None):
	"Figure out the key directories, begin the process."
	# figure the src
	srcDir = os.path.abspath(srcDir)
	if not os.path.exists(srcDir):
		error("Aborting process. Source directory is missing: "+ srcDir)
	if not (os.path.isdir(srcDir)):
		error("Aborting process. Source directory is not a directory: "+ srcDir)
	#figure the dest location
	if os.path.isabs(destDirIn):
		destDir = destDirIn
	else:
		destDir = os.path.join(os.path.split(srcDir)[0], destDirIn)
	if destDir == srcDir:
		error("Aborting process. Destination directory is the same as the source. Can't overwrite source.")
	
	#figure the settings location
	settingsFile = os.path.split(__file__) # ElementsSettings.txt must be in the same directory as this Elements.pyc file
	settingsFile = os.path.join(settingsFile[0], "ElementsSettings.txt")
	
	# do it
	if processSubDir:
		if processSubDir[0] =='/': processSubDir = processSubDir[1:] # strip leading '/'
		if processSubDir[-1] =='/': processSubDir = processSubDir[0:-1] # strip trailing '/'
	site = Site(srcDir, destDir, settingsFile, processSubDir)
	site.processSite()
	msg('')
	
	# open the resultPage
	if not displayTarget:
		displayTarget = buildPath (destDir, processSubDir.replace('/', os.sep))
	
	if displayTarget[0:7] == 'http://':
		webbrowser.open(displayTarget)
		return
	elif os.path.isfile(displayTarget):
		webbrowser.open("file:///"+ displayTarget.replace(os.sep, '/'))
		return
	elif not os.path.isdir(displayTarget):
		displayTarget = buildPath (destDir, displayTarget.replace('/', os.sep))

	if os.path.isfile(displayTarget):
		webbrowser.open("file:///"+ displayTarget.replace(os.sep, '/'))
		return

	for displayPage in map(string.strip, site.elements["displayPage"].split(',')):
		f = os.path.join(displayTarget, displayPage)
		if os.path.isfile(f):
			webbrowser.open("file:///"+ f.replace(os.sep, '/'))
			return		
	webbrowser.open("file:///"+ displayTarget.replace(os.sep, '/'))
	
	