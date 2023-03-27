from bs4 import BeautifulSoup


def html_parser(path):

	'''Opens the template.htm and returns it as a bs4 Object'''

	with open(path,'r') as inf:
		soup = BeautifulSoup(inf,'html.parser')
	
	return soup


resource = html_parser('broken.htm')
print(resource)
table = template.findAll('table')[-1]
print(table)