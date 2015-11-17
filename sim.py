#!/usr/bin/python3

import collections  # for named tuple
import re  # for regex

Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

# generate a token list of input text
# adapted from https://docs.python.org/3/library/re.html#writing-a-tokenizer
def tokenize(code):
	token_specification = [
		('NUMBER',        r'\d+'),         # Integer number
		('ASSIGN',        r'='),           # Assignment operator '='
		('END',           r';'),           # Statement terminator ';'
		('ID',            r'\w+'),         # Identifiers
		('L_BRACE',       r'\('),          # Left brace '('
		('R_BRACE',       r'\)'),          # Right brace ')'
		('L_CURLY_BRACE', r'{'),           # Left curly brace '{'
		('R_CURLY_BRACE', r'}'),           # Right curly brace '}'
		('COLUMN',        r','),           # column ','

        #order counts here (the more complex rules go first)
        ('COMMUNICATION', r'<->'),         # Communication rule sign '<->'
		('EVOLUTION',     r'->'),          # Evolution rule sign '->'
        ('SMALLER',       r'<'),           # Smaller sign '<'
		('LARGER',        r'>'),           # Larger sign '>'

		('CHECK_SIGN',    r'/'),           # Checking rule separator '/'
		('NEWLINE',       r'\n'),          # Line endings
		('SKIP',          r'[ \t]+'),      # Skip over spaces and tabs
		('MISMATCH',      r'.'),           # Any other character
	]
	# join all groups into one regex expr; ex:?P<NUMBER>\d+(\.\d*)?) | ...
	tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
	line_num = 1
	line_start = 0
	# iteratively search and return each match (for any of the groups)
	for mo in re.finditer(tok_regex, code):
		kind = mo.lastgroup # last group name matched
		value = mo.group(kind) # the last matched string (for group kind)
		#print("kind = %s, value = %s" % (kind, value))
		if kind == 'NEWLINE':
			line_start = mo.end()
			line_num += 1
		elif kind == 'SKIP':
			pass
		elif kind == 'MISMATCH':
			raise RuntimeError('%r unexpected on line %d' % (value, line_num))
		else:
			column = mo.start() - line_start
			yield Token(kind, value, line_num, column)
#end tokenize

# prints tokens separated by spaces on their original line (with line numbering)
def print_token_by_line(v):
    line_num = 0;
    for token in v:
        if (token.line > line_num):
            line_num = token.line;
            print('\n%d  ' % line_num, end='');

        print(token.value, end=" ");
#end print_token_by_line

##########################################################################
#   MAIN
##########################################################################

with open("input.txt") as file_in:
    lines = "".join(file_in.readlines());

# construct array of tokens for later use
tokens = [token for token in tokenize(lines)];

print_token_by_line(tokens);

print("\n\n");
