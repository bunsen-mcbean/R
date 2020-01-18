

import os
import sys
from subprocess import check_output
from subprocess import call
import shutil

def locate_libs(path):

	locations = set()
	
	if path.endswith(".dSYM"):
		
		shutil.rmtree(path)
		print("removing : " + path)

	elif os.path.isfile(path):
	
		if path.endswith(".so") or path.endswith(".dylib"):
	
			locations.add(path)
			
			output = check_output(["otool", "-L", path])
	
			lines = output.split("\n")
			lines.pop(0)
	
			for line in lines:
	
				line = line.strip()

				if line.startswith("/Library/Frameworks/R.framework/Versions/3.6/Resources/") or line.startswith("/opt/") or line.startswith("/usr/local/"):
		
					file = line.split()[0]
					if os.path.isfile(file):
						locations.add(file)
						
					if (file != path):
						#print("recursing into " + file)
						locations.update(locate_libs(file))
		
	elif os.path.isdir(path):
			
		if path.endswith("/html") or path.endswith("/help") or path.endswith("/demo") or path.endswith("/tests"):
			shutil.rmtree(path)
			print("removing : " + path)

		else:

			for sub in os.listdir(path):
		
				sub_path = os.path.join(path, sub)
				locations.update(locate_libs(sub_path))
			
	asArray = [ ]
	asArray.extend(locations)
			
	return asArray

def extract_lib_dependencies(libs):

	dependencies = set()
	
	for lib in libs:
	
		print(lib)

		output = check_output(["otool", "-L", lib])
	
		lines = output.split("\n")
		lines.pop(0)
	
		for line in lines:
	
			line = line.strip()

			if (line.startswith("/Library/Frameworks/R.framework/")
					or line.startswith("/opt/")
					or line.startswith("/usr/local/")):
		
				file = line.split()[0]
				dependencies.add(file)
				
	asArray = []
	asArray.extend(dependencies)
			
	return asArray
	
def change_dep_paths(lib, changes):

	for change in changes:
	
		call(["install_name_tool", "-change", change["old"], change["new"], lib])


wd = os.getcwd()

path = os.path.join(wd, "R.framework")
out_lib_dir = os.path.join(wd, "R.framework/Versions/3.6/Resources/lib")

if os.path.exists(out_lib_dir) is False:
	os.makedirs(out_lib_dir)

libs = locate_libs(path)
libs.append(os.path.join(wd, "R.framework/Versions/3.6/Resources/bin/exec/R"))

dependencies = extract_lib_dependencies(libs)

new_libs = [ ]
changes = [ ]

for dependency in dependencies:

	dep_base   = os.path.basename(dependency)
	dep_target = os.path.join(out_lib_dir, dep_base)

	if os.path.isfile(dependency):
	
		if dependency != "/opt/X11/lib/libfreetype.6.dylib":
			try:
				shutil.copyfile(dependency, dep_target)
			except Exception as e:
				print(e)
			
		new_libs.append(dep_target)
		
		change = { "old" : dependency, "new" : "@executable_path/../Frameworks/R.framework/Versions/3.6/Resources/lib/" + dep_base }
		changes.append(change)

		change = { "old" : dep_base, "new" : "@executable_path/../Frameworks/R.framework/Versions/3.6/Resources/lib/" + dep_base }
		changes.append(change)
		
	else:
	
		print(dependency + " not found!")
		# sys.exit(1)

print(dependencies)
print(changes)
		
for new_lib in new_libs:

	lib_base = os.path.basename(new_lib)
	new_path = "@executable_path/../Frameworks/R.framework/Versions/3.6/Resources/lib/" + lib_base
	call(["install_name_tool", "-id", new_path, new_lib])

	change_dep_paths(new_lib, changes)
	
for lib in libs:

	lib_base = os.path.basename(lib)
	new_path = os.path.relpath(lib, path)
	
	new_path = new_path.replace("R.framework/Resources/", "R.framework/Versions/3.6/Resources/")
	new_path = new_path.replace("R.framework/Versions/Current/", "R.framework/Versions/3.6/")
	new_path = new_path.replace("R.framework/Libraries/", "R.framework/Versions/3.6/lib/")

	if new_path.startswith(".."):
		new_path = "@executable_path/../Frameworks/R.framework/Versions/3.6/Resources/lib/" + lib_base
	else:
	
		if new_path.startswith("Resources/"):
			new_path = new_path.replace("Resources/", "Versions/3.6/Resources/")
		if new_path.startswith("Versions/Current/"):
			new_path = new_path.replace("Versions/Current/", "Versions/3.6/")
		if new_path.startswith("Libraries/"):
			new_path = new_path.replace("Libraries/", "Versions/3.6/Resources/")
	
		new_path = "@executable_path/../Frameworks/R.framework/" + new_path

	print(new_path)

	call(["install_name_tool", "-id", new_path, lib])

	change_dep_paths(lib, changes)
	
os.remove(os.path.join(wd, "R.framework/Headers"))
os.remove(os.path.join(wd, "R.framework/Libraries"))
os.remove(os.path.join(wd, "R.framework/PrivateHeaders"))
os.remove(os.path.join(wd, "R.framework/R"))
os.remove(os.path.join(wd, "R.framework/Resources"))
os.remove(os.path.join(wd, "R.framework/Versions/3.6/Headers"))
os.remove(os.path.join(wd, "R.framework/Versions/3.6/R"))
os.remove(os.path.join(wd, "R.framework/Versions/3.6/Resources/R"))
os.remove(os.path.join(wd, "R.framework/Versions/3.6/Resources/SVN-REVISION"))
os.remove(os.path.join(wd, "R.framework/Versions/3.6/Resources/COPYING"))
shutil.rmtree(os.path.join(wd, "R.framework/Versions/3.6/PrivateHeaders"))
shutil.rmtree(os.path.join(wd, "R.framework/Versions/3.6/Resources/man1"))
shutil.rmtree(os.path.join(wd, "R.framework/Versions/3.6/Resources/doc"))

call(['install_name_tool', '-id', '@executable_path/../Frameworks/R.framework/Versions/3.6/Resources/lib/libR.dylib', 'R.framework/Versions/3.6/Resources/lib/libR.dylib'])

call(['ln', '-s', 'Versions/3.6/Resources', 'R.framework/Resources'])
