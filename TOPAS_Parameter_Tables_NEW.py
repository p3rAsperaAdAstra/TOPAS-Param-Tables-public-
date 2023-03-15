import re
from glob import glob
from bs4 import BeautifulSoup
from bs4.element import Tag as Bs4Tag
from decimal import Decimal, getcontext
import copy


space2cryst = {"triclinic":{"P1", "P-1"},
			   "monoclinic":{"Cc", "C2/c", "C2", "Cm", "C2/m", 
							 "P21/c", "Pc", "P2/c", "P21", "P21/m", 
							 "P2", "Pm", "P2/m"},
			   "orthorhombic":{"Fddd", "Fdd2", "F222", "Fmm2", "Fmmm", 
							   "Ccca", "Ibca", "Ccc2", "Cccm", "Iba2", 
							   "Ibam", "Aba2", "Cmca", "Ima2", "Imma", 
							   "Cmc21", "Ama2", "Cmcm", "Abm2", "Cmma", 
							   "C2221", "I222", "I212121", "Imm2", "Immm", 
							   "C222", "Cmm2", "Amm2", "Cmmm", "Pnna", 
							   "Pccn", "Pbcn", "Pbca", "Pnnn", "Pcca", 
							   "Pban", "Pna21", "Pnma", "Pnn2", "Pnnm", 
							   "Pba2", "Pbam", "Pnc2", "Pmna", "Pca21", 
							   "Pbcm", "Pcc2", "Pccm", "Pmn21", "Pmmn", 
							   "Pmc21", "Pma2", "Pmma", "P212121", "P21212", 
							   "P2221", "P222", "Pmm2", "Pmmm"},
			   "tetragonal":{"I41/acd", "I41cd", "I41/amd", "I41md", "I-42d", 
							 "I4cm", "I-4c2", "I4/mcm", "I41/a", "I41", "I4122", 
							 "I4", "I-4", "I4/m", "I422", "I4mm", "I-4m2", 
							 "I-42m", "I4/mmm", "P4/ncc", "P4/nnc", "P42/nbc", 
							 "P4cc", "P 4/mcc", "P4nc", "P 4/mnc", "P42bc",
							 "P 42/mbc", "P42/nmc", "P42/ncm", "P42/nnm", 
							 "P4/nbm", "P-421c", "P42mc", "P-42c", "P42/mmc", 
							 "P42nm", "P-4n2", "P42/mnm", "P42cm", "P-4c2", 
							 "P42/mcm", "P4bm", "P-4b2", "P4/mbm", "P42/n", 
							 "P4/n", "P4/nmm", "P41212", "P43212", "P42212", 
							 "P41", "P43", "P4122", "P4322", "P42", "P 42/m", 
							 "P4222", "P4212", "P-421m", "P4", "P-4", "P4/m", 
							 "P422", "P4mm", "P-42m", "P-4m2", "P4/mmm"},
			   "hexagonal":{"P6cc", "P6/mcc", "P63mc", "P-62c", "P63/mmc",
							"P63cm", "P-6c2", "P63/mcm", "P61", "P65", "P6122",
							"P6522", "P62", "P64", "P6222", "P6422", "P63", 
							"P63/m", "P6322", "P6", "P-6", "P6/m", "P622", 
							"P6mm", "P-6m2", "P-62m", "P6/mmm",
							"P31c", "P-31c", "P3c1", "P-3c1", "P31", "P32", 
							"P3112", "P3121", "P3212", "P3221", "P3", "P-3", 
							"P312", "P321", "P3m1", "P31m", "P-31m", "P-3m1"},
			   "cubic":{"Fd-3c", "F-43c", "Fm-3c", "Fd-3", "Fd-3m", 
						"F4132", "F23", "Fm-3", "F432", "F-43m", 
						"Fm-3m", "Ia-3d", "I-43d", "Ia-3", "I4132", 
						"I23", "I213", "Im-3", "I432", "I-43m", 
						"Im-3m", "Pn-3n", "P-43n", "Pm-3n", "Pn-3", 
						"Pn-3m", "Pa-3", "P4332", "P4132", "P213", 
						"P4232", "P23", "Pm-3", "P432", "P-43m", "Pm-3m"},
			   "rhombohedral":{"R3c", "R-3c", "R3", "R-3", "R32", "R3m", "R-3m"}}



def html_parser(path,parser='html.parser'):

	'''Opens the template.htm and returns it as a bs4 Object'''

	with open(path,'r') as inf:
		soup = BeautifulSoup(inf,features=parser)
	
	return soup


def get_formatted_space_group(spacegroup,soup):

	'''Finds the formatted space group inside space groups.htm and replaces the 
	unformatted one in the found data.'''

	for tr in soup.findAll('tr'):
		tds = tr.findAll('td')
		if tds[0].text.strip() == spacegroup:
			# inner_html = ''.join([str(ele) for ele in tds[1].p.contents])
			# formatted = BeautifulSoup(inner_html,'html.parser') 
			formatted = tds[1].p.contents
			return formatted

	print('NO FORMATTED SPACE GROUP COULD BE FOUND IN "space groups.htm".')





def cryst_round(mean_err):
	'''
	DESCRIPTION: This function preforms crystallographic rounding on a string that contains two floats 
	separated by the substring "`_".
	'''
	
	# set precision ridiculously high
	getcontext().prec = 32

	if '`_' not in mean_err:
		if re.search(r'\d+\.\d+',mean_err): 
			return '{:.2f}'.format(Decimal(mean_err))
		else:
			return mean_err

	mean, error = mean_err.split('`_')
	
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


def handle_alt_notations(data,raw):

	'''Sometimes the parameters are written in an alternative notation which uses the name of the
	bravais lattice without letters to identify different parameters.'''

	# THIS MIGHT NEED IMPROVEMENT IF VALUES WITHOUT ERRORS OCCUR!!!
	V = re.search(r'volume\s+(\d+.\d+`_\d+.\d+)',raw).group(1)
	data['volume'] = V

	if re.search(r'Cubic\(@\s+(\d+.\d+`_\d+.\d+)\)',raw):
		a = re.search(r'Cubic\(@\s+(\d+.\d+`_\d+.\d+)\)',raw).group(1)
		data['a'] = a; data['b'] = a; data['c'] = a; data['al'] = '90'; data['be'] = '90'; data['ga'] = '90'
	elif re.search(r'Hexagonal\(@\s+(\d+.\d+`_\d+.\d+),\s+@\s+(\d+.\d+`_\d+.\d+)\)',raw):
		a,c = re.search(r'Hexagonal\(@\s+(\d+.\d+`_\d+.\d+),\s+@\s+(\d+.\d+`_\d+.\d+)\)',raw).group(1,2)
		data['a'] = a; data['b'] = a; data['c'] = c; data['al'] = '90'; data['be'] = '90'; data['ga'] = '120'
	elif re.search(r'Rhombohedral\(@\s+(\d+.\d+`_\d+.\d+),@\s+(\d+.\d+`_\d+.\d+)\)',raw):
		a,ga = re.search(r'Rhombohedral\(@\s+(\d+.\d+`_\d+.\d+),@\s+(\d+.\d+`_\d+.\d+)\)',raw).group(1,2)
		data['a'] = a; data['b'] = a; data['c'] = a; data['al'] = '90'; data['be'] = '90'; data['ga'] = ga
	elif re.search(r'Tetragonal\(@\s+(\d+.\d+`_\d+.\d+),@\s+(\d+.\d+`_\d+.\d+)\)',raw):
		a,c = re.search(r'Tetragonal\(@\s+(\d+.\d+`_\d+.\d+),@\s+(\d+.\d+`_\d+.\d+)\)',raw).group(1,2)
		data['a'] = a; data['b'] = a; data['c'] = c; data['al'] = '90'; data['be'] = '90'; data['ga'] = '90'

	return data
	# others to be implemented if testing shows that it's necessary.



############ new code 
def get_data(path):

	'''Finds all the available data in a TOPAS output file.'''

	fix_angles = {'triclinic':{},
				  'monoclinic':{'al':'90','ga':'90'},
				  'orthorhombic':{'al':'90','be':'90','ga':'90'},
				  'tetragonal':{'al':'90','be':'90','ga':'90'},
				  'hexagonal':{'al':'90','be':'90','ga':'120'},
				  'cubic':{'al':'90','be':'90','ga':'90'},
				  'rhombohedral':{'al':'90','be':'90'}}

	equal_lengths = {'triclinic':{'a':0,'b':0,'c':0},
					 'monoclinic':{'a':0,'b':0,'c':0},
					 'orthorhombic':{'a':1,'b':1,'c':0},
					 'tetragonal':{'a':1,'b':1,'c':0},
					 'hexagonal':{'a':1,'b':1,'c':0},
					 'cubic':{'a':1,'b':1,'c':1},
					 'rhombohedral':{'a':1,'b':1,'c':1}}

	angles = ['al','be','ga']
	lengths = ['a','b','c']

	param_rexes = [r'%s\s+@*\s+(\d+.\d+`_\d+.\d+)',r'%s\s+@*\s+(\d+.\d+)`',r'%s\s+@*\s+(\d+.\d+)',r'%s\s+@*\s*(\d+.*)']

	with open(path,'r',encoding='utf8') as inf:
		raw = inf.read()

	data = {}

	space_group = re.search(r'space_group\s+"*([\w\d/-]+)"*',raw).group(1) # find space group first 
	crystal = [key for key in space2cryst if space_group in space2cryst[key]][0] # determine crystal system from it using inverse space2cryst

	data['space_group'] = space_group
	data['crystal_system'] = crystal

	# find rwp, rexp and gof
	rwp = re.search(r'r_wp\s+(\d+[.]\d+)',raw).group(1)
	rexp = re.search(r'r_exp\s+(\d+[.]\d+)',raw).group(1)
	chi = re.search(r'gof\s+(\d+[.]\d+)',raw).group(1)

	# find cell volume
	for rex in param_rexes:
		rex = rex%'cell_volume'
		match = re.search(rex,raw)
		if match:
			data['volume'] = match.group(1)
			break

	volume = re.search(r'gof\s+(\d+[.]\d+)',raw).group(1)

	data['rwp'] = rwp
	data['rexp'] = rexp
	data['chi'] = chi

	# find angles
	given_angles = fix_angles[crystal]
	equiv_lengths = equal_lengths[crystal]

	for angle in angles:
		if angle in given_angles.keys():
			data[angle] = given_angles[angle]
		else:
			for rex in param_rexes:
				rex = rex%angle
				match = re.search(rex,raw)
				if match:
					data[angle] = match.group(1)
					break

	skip = []
	for length in lengths:
		if length in skip:
			pass
		else:
			for rex in param_rexes:
				rex = rex%length
				match = re.search(rex,raw)
				if match:
					data[length] = match.group(1)
					if equiv_lengths[length] == 1:
						equals = [key for key in equiv_lengths if equiv_lengths[key] == 1]
						skip += equals
						for key in equals: data[key] = match.group(1)
					break
	
	if len(data.keys()) == 12:
		return data
	else:
		# Implement edge cases for different types of crystal systems like Cubic(@ 15.517450`_0.003075)
		params = handle_alt_notations(data,raw)
		for par in params.keys():
			if par not in data.keys():
				data[par] = params[par]

		if len(data.keys()) == 12:
			return data
		else:
			print('Still not finding all values.')
	

def write_soup(soup,path='check.htm'):

	'''Write a temporary soup so it can be displayed in the browser and checked.'''

	with open(path,'w',encoding='utf8') as outf:
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

		if key in ['a','b','c','al','be','ga','volume','rwp','rexp','chi']:
			val = cryst_round(val)

		new_td = copy.copy(td_template)

		if key == 'space_group': # get formatted space group from "space groups.htm"
			formatted = get_formatted_space_group(val,formatted_spacegroups)
			new_td.span.contents = formatted
		else:
			new_td.span.string = val

		tr_outsoup.append(new_td)
		

	return outsoup



# Main Loop
input_files = glob('*.out')

template = html_parser('template.htm')
outsoup = copy.copy(template)
formatted_spacegroups = html_parser('space groups.htm')


for tr in outsoup.findAll('tr'):
	tr.findAll('td')[-1].decompose()


# write_soup(outsoup,'outsoup.htm')
for file in input_files:
	params = get_data(file) # this should work now. add more rex to param_rexes if doesn't work.
	params['filename'] = file
	outsoup = make_new_column(template,outsoup,params)
	

write_soup(outsoup,'done.htm')
