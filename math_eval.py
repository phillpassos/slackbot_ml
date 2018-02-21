import re
from py_expression_eval import Parser
parser = Parser()

def has_expression(txt):
	value = "".join(re.findall(r'[\d\(\)\^\%\+\-\*\/\.]', txt))
	value = "".join(re.findall(r'[\+\-\^\%\*\/]', value))
	return len(value) > 0

def extract_expression(txt):
	return "".join(re.findall(r'[\d\(\)\^\%\+\-\*\/\.]', txt))
	
def exec_expression(exp_txt):
	try:
		#result = eval(extract_expression(exp_txt))
		result = parser.parse(extract_expression(exp_txt)).evaluate({})
	except Exception as e:
		result = ""
	return result
