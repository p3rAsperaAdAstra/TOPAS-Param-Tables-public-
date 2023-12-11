import re
from glob import glob
from bs4 import BeautifulSoup
from bs4.element import Tag as Bs4Tag
from decimal import Decimal, getcontext
import copy
import argparse


def html_parser(path):

	'''Opens the template.htm and returns it as a bs4 Object'''

	with open(path,'rb') as inf:
		soup = BeautifulSoup(inf,'html.parser')
	
	return soup



def make_space2cryst_dict(soup):

	'''Creates the space2cryst dict from a bs4 soup object.'''
	space2cryst = {}

	for tr in soup.findAll('tr')[1:]:
		tds = tr.findAll('td')
		keys = tds[0].text.strip().split(';')
		formatted = tds[1].p.contents
		system = tds[2].text.strip()

		for key in keys:
			space2cryst[key.lower()] = (formatted,system)

	return space2cryst




def cryst_round(parm,mean_err):
	'''
	DESCRIPTION: This function preforms crystallographic rounding on a string that contains two floats 
	separated by the substring "`_".
	'''
	
	# set precision ridiculously high
	getcontext().prec = 32

	if '_' not in mean_err:
		if re.search(r'\d+\.\d+',mean_err) and parm in ['chi','rwp','rexp']: 
			return '{:.2f}'.format(Decimal(mean_err))
		else:
			return mean_err

	if 'LIMIT_MAX' in mean_err or 'LIMIT_MIN' in mean_err:
		return 
	elif '`_' in mean_err:
		mean, error = mean_err.split('`_')
	elif '_' in mean_err:
		mean, error = mean_err.split('_')
	
	mean  = Decimal(mean)
	error = Decimal(error)
	
	# print('0. Initial values: {}, {}'.format(mean,error))
	# transform mean and err into scientific
	mean  = '{:.16e}'.format(mean)
	error = '{:.16e}'.format(error)
	
	# get exponents of mean and error
	ex_m = int(re.search(r'(?<=e)[+-]*\d*',mean).group()) 
	ex_e = int(re.search(r'(?<=e)[+-]*\d*',error).group())
	dex  = 1+ex_m-ex_e
	
	# cut off mean
	mean_cut = '{:.{}}'.format(Decimal(mean),str(dex)+'e')
	# print('1. Cut mean and round: {}'.format(Decimal(mean_cut)))
	
	# initial round of error
	bracket = re.sub(r'e[+-]*\d*','',error)
	bracket = '{:.1f}'.format(Decimal(bracket))
	bracket = bracket.replace('.','')
	# print('2. Initial cut and round of error: {}'.format(bracket))
	
	# set mean_round
	mean_round = Decimal(mean_cut)
	
	# second round for digits higher 20
	if int(bracket) > 20:
		bracket = '0.'+bracket
		bracket = '{:.1f}'.format(Decimal(bracket))
		bracket = bracket[-1]
		# print('3. Optional second cut and round of error: {}'.format(bracket))
		
		mean_round = str(Decimal(mean_cut))
		mean_round = '{:.{}}'.format(Decimal(mean_round),dex)
		# print('4. Second cut and round of mean, if 3. occurs: {}'.format(mean_round))
	
	# print('5. Final result put into html table: {}({})'.format(mean_round,bracket))
	# print('\n')
	return '%s(%s)'%(mean_round,bracket)




def find_space_group(raw,data):

	'''Finds the space group in outfile (str). If not found, add "Not found" to data dict.'''

	rexes = [r'space_group\s+"*([\w\d/-]+)"*'] # Error index 3 in backs.log

	for rex in rexes:
		match = re.search(rex,raw)
		if match:
			data['space_group'] = match.group(1)
			break
		else:
			pass

	try:
		data['space_group']
	except KeyError:
		data['space_group'] = 'Not found'
		print('The space group could not be found in the .out file!!!: %s'%data['filename'])

	return data





def find_volume(raw,data):

	'''Finds the volume in the .out file (str) If none found, adds "Not found".'''

	rexes = [r'volume\s+(\d+\.\d+`_\d+\.\d+)',
			 r'volume\s+(\d+\.\d+)`*',
			 r'cell_volume\s+(\d+\.\d+`_\d+\.\d+)',
			 r'cell_volume\s+(\d+\.\d+)`*'] # Error index 3 in backs.log

	for rex in rexes: # iterate over patterns and break at first match
		match = re.search(rex,raw)
		if match:
			data['volume'] = match.group(1)
			break
		else:
			pass # move on to next pattern

	try:
		data['volume']
	except KeyError:
		data['volume'] = 'Not found'
		# print('The volume could not be found in the .out file!!!')
		# print('In rare cases, this is because there simply is no volume.')
		# print('More likely, however, none of the regexes (rex) in the list of regexes (rexes), can match the pattern of the volume inside the .out file.')

	return data


def complete_lengths(raw,data,crystal_system,found):

	'''Completes the lengths based on the crystal system, if possible.
	If the number of lengths is still smaller than 3, print out error and add "Not found" to data for those lengths.'''

	equal_lengths = {'triclinic':{'a':0,'b':0,'c':0},
					 'monoclinic':{'a':0,'b':0,'c':0},
					 'orthorhombic':{'a':1,'b':1,'c':0},
					 'tetragonal':{'a':1,'b':1,'c':0},
					 'hexagonal':{'a':1,'b':1,'c':0},
					 'cubic':{'a':1,'b':1,'c':1},
					 'rhombohedral':{'a':1,'b':1,'c':1}}

	equals = equal_lengths[crystal_system]
	a = data['a']

	for length in equals.keys():
		if equals[length] == 1:
			data[length] = a
			if length not in found:
				found.append(length)

	if len(found) == 3:
		pass
	else:
		for length in ['a','b','c']:
			if length not in found:
				data[length] = 'Not found'
		print('Not alt notation, yet not all parameters found. This is weird.')
		print('Make a bug report at: "https://github.com/p3rAsperaAdAstra/TOPAS-Param-Tables-public-"')


	return data
	



def complete_angles(raw,data,crystal_system,found):

	'''Completes the lengths based on the crystal system, if possible.
	If the number of lengths is still smaller than 3, print out error and add "Not found" to data for those lengths.'''

	fix_angles = {'triclinic':{},
				  'monoclinic':{'al':'90','ga':'90'},
				  'orthorhombic':{'al':'90','be':'90','ga':'90'},
				  'tetragonal':{'al':'90','be':'90','ga':'90'},
				  'hexagonal':{'al':'90','be':'90','ga':'120'},
				  'cubic':{'al':'90','be':'90','ga':'90'},
				  'rhombohedral':{'al':'90','be':'90'}}

	givens = fix_angles[crystal_system]

	for angle in givens.keys():
		data[angle] = givens[angle]
		if angle not in found:
			found.append(angle)

	if len(found) == 3:
		pass
	else:
		for angle in ['al','be','ga']:
			if angle not in found:
				data[angle] = 'Not found'

	return data





def find_alt_parms(raw,data):

	'''If the number of lengths found by find_lengths() is equal to zero, a search for the alternative notation
	of TOPAS .out files is executed. If the number of lengths is still zero after this, print out error and add 
	"Not found" to data for those lengths.'''


	rexes = [r'([a-zA-Z]+)\(\s*@*\s*(\d+\.\d+`*_\d+.\d+)[a-zA-Z_]*\d*\.*\d*,\s*@*\s*(\d+\.\d+`*_\d+\.\d+)[a-zA-Z_]*\d*\.*\d*',
			 r'([a-zA-Z]+)\(\s*@*\s*(\d+\.\d+`*_\d+\.\d+)[a-zA-Z_]*\d*\.*\d*,\s*@*\s*(\d+\.\d+)[a-zA-Z_]*\d*\.*\d*`*',
			 r'([a-zA-Z]+)\(\s*@*\s*(\d+\.\d+`*_\d+\.\d+)[a-zA-Z_]*\d*\.*\d*,\s*@*\s*(\d+\.\d+)[a-zA-Z_]*\d*\.*\d*`*',
			 r'([a-zA-Z]+)\(\s*@*\s*(\d+\.\d+)[a-zA-Z_]*\d*\.*\d*`*,\s*@*\s*(\d+\.\d+)[a-zA-Z_]*\d*\.*\d*`*',
			 r'([a-zA-Z]+)\(\s*@*\s*(\d+.\d+`*_\d+.\d+)[a-zA-Z_]*\d*\.*\d*',
			 r'([a-zA-Z]+)\(\s*@*\s*(\d+.\d+)[a-zA-Z_]*\d*\.*\d*`*\s*']

	for rex in rexes:
		match = match = re.search(rex,raw)
		if match:
			sys = match.group(1)
			break

	if sys:
		if sys == 'Cubic':
			a = match.group(2) 
			data['a'] = a; data['b'] = a; data['c'] = a; data['al'] = '90'; data['be'] = '90'; data['ga'] = '90'
			data['crystal_system'] = 'cubic'
		elif sys == 'Hexagonal':
			a,c = match.group(2,3)
			data['a'] = a; data['b'] = a; data['c'] = c; data['al'] = '90'; data['be'] = '90'; data['ga'] = '120'
			data['crystal_system'] = 'hexagonal'
		elif sys == 'Rhombohedral':
			a,ga = match.group(2,3)
			data['a'] = a; data['b'] = a; data['c'] = a; data['al'] = '90'; data['be'] = '90'; data['ga'] = ga
			data['crystal_system'] = 'rhombohedral'
		elif sys == 'Tetragonal':
			a,c = match.group(2,3)
			data['a'] = a; data['b'] = a; data['c'] = c; data['al'] = '90'; data['be'] = '90'; data['ga'] = '90'
			data['crystal_system'] = 'tetragonal'
		elif sys == 'Monoclinic':
			print('%s alt notation not implemented. format first encountered'%sys)
		elif sys == 'Triclinic':
			print('%s alt notation not implemented. format first encountered'%sys)
		elif sys == 'Trigonal':
			a,c = match.group(2,3)
			data['a'] = a; data['b'] = a; data['c'] = c; data['al'] = '90'; data['be'] = '90'; data['ga'] = '120'
			data['crystal_system'] = 'trigonal'
				
	else:
		print('No alt notation found.')


	parms = ['a','b','c','al','be','ga']

	for par in parms:
		if par not in data.keys():
			data[par] = 'Not found'
			print('Could not find %s in find_alt_parms(). FILE: %s'%(par,data['filename']))

	return data




def find_lengths(raw,data,crystal_system):

	'''Finds the lengths a,b,c in outfile (str). If not found, add "Not found" to data dict.
	Calls complete_lengths() to check if can be derived from crystal system.'''

	rexes = [r'%s\s+@*\s*(\d+\.\d+`*_\d+\.\d+)[a-zA-Z_]*\d*\.*\d*',
			 r'%s\s+@*\s*(\d+\.\d+)`*_[a-zA-Z_]*\d*\.*\d*',
			 r'%s\s+@*\s*(\d+\.\d+)`',
			 r'%s\s+@*\s*(\d+\.\d+)`*'] # might need to be modified later.

	lengths = ['a','b','c'] # lengths to be searched for
	found = [] # append found lengths so that they can be skipped

	for rex in rexes: # iterate over patterns and break at first match
		for length in lengths:
			if length in found:
				pass
			else:
				match = re.search(rex%length,raw)
				if match:
					data[length] = match.group(1)
					found.append(length)
				else:
					pass


	if len(found) == 3: # all lengths found
		pass
	elif 1 < len(found) < 3: # call complete_lengths()
		data = complete_lengths(raw,data,crystal_system,found)
	elif len(found) == 0: # call find_alt_lengths()
		data = find_alt_parms(raw,data)
	
	return data


def find_angles(raw,data,crystal_system):

	'''Finds the lengths a,b,c in outfile (str). If not found, add "Not found" to data dict.
	Calls complete_lengths() to check if can be derived from crystal system.'''

	rexes = [r'\s+%s\s*@*\s*(\d+.\d+`*_\d+.\d+)',
			 r'\s+%s\s*@*\s*(\d+.\d+)`*',
			 r'\s+%s\s*@*\s*(\d+)[^:]',] # might need to be modified later.

	angles = ['al','be','ga'] # lengths to be searched for
	found = [] # append found lengths so that they can be skipped

	for rex in rexes: # iterate over patterns and break at first match
		for angle in angles:
			if angle in found:
				pass
			else:
				match = re.search(rex%angle,raw)
				if match:
					data[angle] = match.group(1)
					found.append(angle)
				else:
					pass


	if len(found) == 3: # all lengths found
		pass
	elif 1 < len(found) < 3: # call complete_angles()
		data = complete_angles(raw,data,crystal_system,found)
	elif len(found) == 0: # call find_alt_angles()
		data = find_alt_parms(raw,data)
	
	return data


############ new code 
def get_data(path,data):

	'''Finds all the available data in a TOPAS output file.'''

	with open(path,'r',encoding='utf8',errors='ignore') as inf:
		raw = inf.read()

	data = find_space_group(raw,data) # find space group first
	try:
		data['crystal_system'] = space2cryst[data['space_group'].lower()][1] # now based on new and improved space2cryst
	except KeyError:
		data['crystal_system'] = space2cryst[data['space_group'].lower()][1] # now based on new and improved space2cryst
	data = find_volume(raw,data) # find volume of ??unit cell??

	data = find_lengths(raw,data,data['crystal_system']) # find lengths
	data = find_angles(raw,data,data['crystal_system']) # find angles
	
	# find rwp, rexp and gof (these should be easy)
	rwp = re.search(r'r_wp\s+(\d+\.*\d*)',raw).group(1)
	rexp = re.search(r'r_exp\s+(\d+\.*\d*)',raw).group(1)
	chi = re.search(r'gof\s+(\d+\.*\d*)',raw).group(1)

	data['rwp'] = rwp
	data['rexp'] = rexp
	data['chi'] = chi

	parms = ['a','b','c','al','be','ga','space_group','crystal_system','chi','rwp','rexp','volume']
	for par in parms:
		if par not in data.keys():
			data[par] = 'Not found'

	return data
	


def write_soup(soup,path='check.htm'):

	'''Write a temporary soup so it can be displayed in the browser and checked.'''

	with open(path,'w',encoding='utf-8') as outf:
		outf.write(str(soup))


def make_new_column(template,outsoup,params):

	'''Takes the data from get_data and adds a new data column to the template.htm soup.'''

	template2data = {'Compound':'filename',
					 'crystalsystem':'crystal_system',
					 'spacegroup':'space_group',
					 'a/Å':'a',
					 'b/Å':'b',
					 'c/Å':'c',
					 'α/°':'al',
					 'β/°':'be',
					 'γ/°':'ga',
					 'V/Å3':'volume',
					 'Rwp/%':'rwp',
					 'Rexp/%':'rexp',
					 'χ':'chi'}

	trs_template = template.findAll('tr')
	trs_outsoup = outsoup.findAll('tr')

	for i in range(len(trs_template)):
		tr_template = trs_template[i]
		tr_outsoup = trs_outsoup[i]

		td_rowname = tr_template.findAll('td')[0]
		td_template = tr_template.findAll('td')[-1]

		row_name = re.sub(r'\s+', '', td_rowname.text)
		key = template2data[row_name]
		val = params[key]

		if key in ['a','b','c','al','be','ga','volume','rwp','rexp','chi'] and key != 'Not found':
			val = cryst_round(key,val)

		new_td = copy.copy(td_template)

		if key == 'space_group' and val != 'Not found': # get formatted space group from "space groups.htm"
			formatted = space2cryst[data['space_group'].lower()][0]
			formatted_str = ''.join([str(ele) for ele in formatted]) # doing this the hard way.
			new_td_str = str(new_td)
			new_td_str = new_td_str.replace('Blank',formatted_str)
			new_td = BeautifulSoup(new_td_str, 'html.parser')
		else:
			new_td.span.string = val

		tr_outsoup.append(new_td)
		

	return outsoup



# Main Loop
input_files = glob('*.out')

resource = html_parser('resource.htm')
template = copy.copy(resource)
template.findAll('table')[-1].decompose() # remove space2cryst from template copy
for p in template.findAll('p')[-2:]: p.decompose() # remove two weird p tags that somehow appear when writing to file
outsoup = copy.copy(template)
for tr in outsoup.findAll('tr'): tr.findAll('td')[-1].decompose() # remove blank column. Change later if useful. 
space2cryst = resource.findAll('table')[-1]

# create space2cryst dict from soup
space2cryst = make_space2cryst_dict(space2cryst)

for i,file in enumerate(input_files):
	data = {}
	data['filename'] = file
	print('%s: (%s/%s)'%(file,i+1,len(input_files)))
	data = get_data(file,data)
	outsoup = make_new_column(template,outsoup,data)
	
write_soup(outsoup,'done.htm')
