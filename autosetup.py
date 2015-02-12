#!/usr/bin/env python
import subprocess,re, os.path, os, shutil
import sys

from urllib2 import Request, urlopen
from urllib import unquote_plus
from urlparse import urlparse
from contextlib import closing
import zipfile, StringIO
from lxml import etree

arg_sub_expr = re.compile("\$(\d+)")

def repodir(repo_url):
	return os.path.splitext(os.path.basename(urlparse(repo_url).path))[0]

def fetch(url,save_data=True,save_name=None,expected_ext=".jar"):
	req = Request(url)
	with closing(urlopen(req)) as response:
		print "Fetching",url,"...\t",
		sys.stdout.flush()
		data = response.read()
		print "done."
		if save_data:
			if save_name:
				fname = save_name
			else:
				urlparts = urlparse(url)
				urlpath = urlparts.path
				if expected_ext and os.path.splitext(urlpath)[1] == expected_ext:
					fname = os.path.basename(urlpath)
				else: # guess what we should call it by looking at the rest of the url
					for param in urlparts.query.split("&"):
						kvp = param.split("=")
						urlpath = kvp[-1]
						if expected_ext and os.path.splitext(urlpath)[1] == expected_ext:
							fname = os.path.basename(urlpath)
							break
					else:
						raise RuntimeError("Unable to name file downloaded from %s according to specification." % url)
			print "Saving as",fname
			with open(fname, 'wb') as f:
				f.write(data)
		else: return data

def arg_sub(args,*subs):
	return [a if not arg_sub_expr.match(a) else subs[int(arg_sub_expr.match(a).group(1))] for a in args]

GIT_PATH = "git"
SVN_PATH = "svn"
SKIP_PLUGINS = True
SKIP_SHARED = True

MVN_PROJECT			= "pom.xml"
MVN_XMLNS_URL		= "http://maven.apache.org/POM/4.0.0"
MVN_NSMAP			= {'pom' : MVN_XMLNS_URL}

SCALA_ECLIPSE_PATH = "/Applications/scala-eclipse/Eclipse.app/Contents/MacOS/eclipse"
ECLIPSE_JAVA_HOME = "/Library/Java/JavaVirtualMachines/jdk1.7.0_71.jdk/Contents/Home/jre"
ECLIPSE_WORKSPACE = "/Users/thomas/Documents/scala-workspace-temp"
#KEYTOOL_PATH = "keytool"
#PY_DEV_CERT_URL = "http://pydev.org/pydev_certificate.cer"
ANTLR4_URL 		= "http://www.antlr.org/download/antlr-4.4-complete.jar"
JSYNTAXPANE_URL	= "https://jsyntaxpane.googlecode.com/files/jsyntaxpane-0.9.4.jar"
JYTHON_URL		= "http://search.maven.org/remotecontent?filepath=org/python/jython-standalone/2.7-b3/jython-standalone-2.7-b3.jar"
JNA_URL			= "https://maven.java.net/content/repositories/releases/net/java/dev/jna/jna/4.1.0/jna-4.1.0.jar"
VALIDATOR_NU_URL= "http://about.validator.nu/htmlparser/htmlparser-1.4.zip"
VALIDATOR_NU_BIN= "htmlparser-1.4/htmlparser-1.4.jar"
LWJGL_URL		= "http://downloads.sourceforge.net/project/java-game-lib/Official%20Releases/LWJGL%202.9.3/lwjgl-2.9.3.zip"
SLICK_URL		= "http://slick.ninjacave.com/slick-util.jar"

PRIMARY_REPO	= "https://github.com/elfprince13/FreeBuild.git"
PARSER_REPO		= "https://github.com/elfprince13/LDrawParser.git"
SHADER_REPO		= "https://github.com/elfprince13/GLSL-Shader-Editor.git"
CRANE_REPO		= "https://github.com/elfprince13/libcrane.git"
CSS_REPO_1		= "https://github.com/radkovo/jStyleParser.git"
CSS_REPO_2		= "https://github.com/radkovo/CSSBox.git"

JSYNTAXPANE_REPO	= "http://jsyntaxpane.googlecode.com/svn/branches/r095/"
JSYNTAXPANE_DIR		= "jSyntaxPane"

INSTALL_ARGS	= ["$0","-nosplash","-data","$1","-application","org.eclipse.equinox.p2.director","-repository","$2","-installIU","$3"]
#KEYTOOL_ARGS	= ["sudo","$0","-import","-file","$1","-alias","PyDevBrainwy","-keystore","$2"]

def suppress_args(src,to_suppress):
	return [arg for arg in src if arg not in to_suppress]

GIT_ARGS		= ["$0","$1","$2"]
GIT_CHECKOUT_COMMAND	= "clone"
GIT_UPDATE_COMMAND		= "pull"
GIT_COMMAND_FOR_EXISTS	= {True : GIT_UPDATE_COMMAND, False : GIT_CHECKOUT_COMMAND}
GIT_SUPPRESS_FOR_EXISTS = {True : {}, False : {}}
SVN_ARGS				= GIT_ARGS + ["$3"]
SVN_CHECKOUT_COMMAND	= "checkout"
SVN_UPDATE_COMMAND		= "update"
SVN_COMMAND_FOR_EXISTS	= {True : SVN_UPDATE_COMMAND, False : SVN_CHECKOUT_COMMAND}
SVN_SUPPRESS_FOR_EXISTS	= {True : {"$2"}, False : {}}

PROJECT_IMPORT_ARGS	= ["$0","-nosplash","-data","$1","-application", "org.eclipse.cdt.managedbuilder.core.headlessbuild","-import","$2"]

PLUGINS_TO_INSTALL = [
	("http://pydev.org/updates",
	 "org.python.pydev.feature.feature.group"),
	("http://download.eclipse.org/tools/gef/updates/releases/",
	 "org.eclipse.draw2d.feature.group"),
	("http://download.eclipse.org/modeling/tmf/xtext/updates/composite/releases/",
	 "org.eclipse.xtext.sdk.feature.group"),
	("http://dl.bintray.com/jknack/antlr4ide/",
	 "antlr4ide.sdk.feature.group"),
	("http://repo1.maven.org/maven2/.m2e/connectors/m2eclipse-antlr/0.15.0/N/0.15.0.201405281449/",
	 "org.sonatype.m2e.antlr.feature.feature.group")
	# add JDT + Jflex sites for jSyntaxPane
]

HELPER_DIR	= os.getcwd()

PROJECTS_TO_IMPORT = [os.path.join(ECLIPSE_WORKSPACE,repodir(repo)) for repo in [PRIMARY_REPO, PARSER_REPO, CSS_REPO_1, CSS_REPO_2, SHADER_REPO]]

#req = Request(PY_DEV_CERT_URL)
#with closing(urlopen(req)) as response:
#	fname = os.path.basename(urlparse(PY_DEV_CERT_URL).path)
#	
#	cert = response.read()
#	
#	with open(fname,'wb') as f:
#		f.write(cert)
#code = subprocess.call(arg_sub(KEYTOOL_ARGS, KEYTOOL_PATH,
#							   fname, os.path.join(ECLIPSE_JAVA_HOME,"lib/security/cacerts")))
#if code:
#	print "Warning: Couldn't import key."
#	print "Y/N? ",
#	inp = raw_input()
#	if not inp or inp.lower()[0] != 'y':
#		sys.exit(1)
#os.remove(fname)

if __name__ == '__main__':
	if not SKIP_PLUGINS:
		print " ".join(arg_sub(INSTALL_ARGS,SCALA_ECLIPSE_PATH,ECLIPSE_WORKSPACE,*[",".join(l) for l in zip(*PLUGINS_TO_INSTALL)]))
		code = subprocess.call(arg_sub(INSTALL_ARGS,SCALA_ECLIPSE_PATH,ECLIPSE_WORKSPACE,*[",".join(l) for l in zip(*PLUGINS_TO_INSTALL)]))
		#code = 0
		if code:
			print "eclipse exited with code",code
			raise RuntimeError("Couldn't install a plugin(s)!")
	print('time for dependencies and stuff')
		
	os.chdir(ECLIPSE_WORKSPACE)
	if not os.path.isdir("shared-libs"):
		os.mkdir("shared-libs")
	os.chdir("shared-libs")
	if not SKIP_SHARED:
		fetch(ANTLR4_URL)
		fetch(JSYNTAXPANE_URL)
		fetch(JYTHON_URL)
		fetch(JNA_URL)
		with zipfile.ZipFile(StringIO.StringIO(fetch(VALIDATOR_NU_URL,False)),'r') as parser_zip:
			if VALIDATOR_NU_BIN in parser_zip.namelist():
				print "Extracting...\t",
				sys.stdout.flush()
				with parser_zip.open(VALIDATOR_NU_BIN,'r') as vn_src:
					with open(os.path.basename(VALIDATOR_NU_BIN),'wb') as vn_dst:
						vn_dst.write(vn_src.read())
				print "done."
			else:
				print "Can't find JAR (%s) in archive:" % VALIDATOR_NU_BIN
				print "\n".join("\t%s" % f for f in sorted(parser_zip.namelist()))
				
		with zipfile.ZipFile(StringIO.StringIO(fetch(LWJGL_URL,False,expected_ext=".zip")),'r') as lwjgl_zip:
			print "Extracting all...\t",
			sys.stdout.flush()
			lwjgl_zip.extractall()
			print "done."
		
		fetch(SLICK_URL)
		
	print("Checking out REPOs")
	os.chdir(ECLIPSE_WORKSPACE)
	for protocol,(cmd_path, cmd_args, cmd_for_exists, to_suppress, repo_set) in {"git" : (GIT_PATH, GIT_ARGS, GIT_COMMAND_FOR_EXISTS, GIT_SUPPRESS_FOR_EXISTS, [(r,) for r in [PRIMARY_REPO, PARSER_REPO, SHADER_REPO, CRANE_REPO, CSS_REPO_1, CSS_REPO_2]]),
		"svn" :  (SVN_PATH, SVN_ARGS, SVN_COMMAND_FOR_EXISTS, SVN_SUPPRESS_FOR_EXISTS, [(JSYNTAXPANE_REPO,JSYNTAXPANE_DIR)])}.iteritems():
		for repo in repo_set:
			rdir = repodir(*repo) if protocol == "git" else repo[1]
			exists = os.path.isdir(rdir)
			if exists:
				os.chdir(rdir)
			print " ".join(arg_sub(suppress_args(cmd_args,to_suppress[exists]),cmd_path,cmd_for_exists[exists],*repo))
			code = subprocess.call(arg_sub(suppress_args(cmd_args,to_suppress[exists]),cmd_path,cmd_for_exists[exists],*repo))
			if code: raise RuntimeError("Couldn't fetch repo")
			if exists:
				os.chdir(ECLIPSE_WORKSPACE)
	
	os.chdir(ECLIPSE_WORKSPACE) # just for fun
	
	os.chdir(repodir(CRANE_REPO))
	code = subprocess.call(["make"])
	if code: raise RuntimeError("Couldn't make libcrane")
	
	os.chdir(ECLIPSE_WORKSPACE)
	os.chdir(repodir(CSS_REPO_1))
	with open(MVN_PROJECT,'r') as pom_h:
		pom = etree.fromstring(pom_h.read())
		version_path = etree.XPath("/pom:project/pom:version",namespaces=MVN_NSMAP)
		version = version_path(pom)[0].text
		
	os.chdir(ECLIPSE_WORKSPACE)
	os.chdir(repodir(CSS_REPO_2))
	with open(MVN_PROJECT,'r') as pom_h:
		pom = etree.fromstring(pom_h.read())
		dep_version_path = etree.XPath('/pom:project/pom:dependencies/pom:dependency/pom:version[../pom:artifactId/text() = "jstyleparser"]',namespaces=MVN_NSMAP)
		req_version_tag = dep_version_path(pom)[0]
		if req_version_tag.text != version:
			print "Warning, CSSBox requested a different version of jStyleParser than was checked out"
			print "This is probably just an oversight on the part of the repo maintainers"
			print "We will attempt to correct the",MVN_PROJECT
			req_version_tag.text = version
	with open(MVN_PROJECT,'w') as pom_h:
		pom_h.write(etree.tostring(pom))
		
	os.chdir(ECLIPSE_WORKSPACE)
	
	#for project_dir in PROJECTS_TO_IMPORT:
	#	print " ".join(arg_sub(PROJECT_IMPORT_ARGS,SCALA_ECLIPSE_PATH,ECLIPSE_WORKSPACE,project_dir))
	#	code = subprocess.call(arg_sub(PROJECT_IMPORT_ARGS,SCALA_ECLIPSE_PATH,ECLIPSE_WORKSPACE,project_dir))
	#	if code:
	#			print "eclipse exited with code",code
	#			raise RuntimeError("Couldn't import project %s!" % project_dir)
			
	# need to patch in Jython version and User Libraries
	

