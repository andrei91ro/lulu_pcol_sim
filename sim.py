#!/usr/bin/python3

import collections  # for named tuple
import re  # for regex
from enum import Enum # for enumerations (enum from C)
import logging # for logging functions
import colorlog # colors log output

##########################################################################
# type definitions

class RuleType(Enum):

    """Enumeration of rule types """

    evolution = 1
    communication = 2
    conditional = 3

#end class RuleType

# tuple used to describe parsed data
Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

class Pcolony:

    """Pcolony class that holds all the components of a P colony."""

    # constructor (members are defined inside in order to avoid alteration caused by other objects of this type)
    def __init__(self):
        self.A = []  # alphabet (list of objects)
        self.e = 'e' # elementary object
        self.f = 'f' # final object
        self.n = 2   # capacity
        self.B = []  # agents (list of Agent type objects)
    #end __init__

    # TODO add specialized functions
#end class Pcolony

class Agent:

    """Agent class used to represent a P colony agent."""

    # constructor (members are defined inside in order to avoid alteration caused by other objects of this type)
    def __init__(self):
        self.obj = collections.Counter() # objects stored by the agent (stored as a multiset thanks to Counter) 
        self.programs = [] # programs (list of programs (each program is a list of n  Rule objects))
    #end __init__()

    def ChoseProgram(self):
        pass #TODO chose an executable program (or chose stochastically from a list of executable programs)
    #end ChoseProgram()
#end class Agent

class Program(list):

    """Program class used to encapsulate a list o rules."""

    def __init__(self):
        """Initialize the underling list used to store rules"""
        list.__init__(self)
#end class Program

class Rule():

    """Rule class used to represent rules that compose a program."""

    # constructor (members are defined inside in order to avoid alteration caused by other objects of this type)
    def __init__(self):
        self.rule_type = 0 
        self.lhs = '' # Left Hand Side operand
        self.rhs = '' # Right Hand Side operand
#end class Rule

##########################################################################

def tokenize(code):
    """ generate a token list of input text
        adapted from https://docs.python.org/3/library/re.html#writing-a-tokenizer"""
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

def print_token_by_line(v):
    """Prints tokens separated by spaces on their original line (with line numbering)"""
    line_num = 0;
    for token in v:
        if (token.line > line_num):
            line_num = token.line;
            print('\n%d  ' % line_num, end='');

        print(token.value, end=" ");
#end print_token_by_line

##########################################################################
#   MAIN

colorlog.basicConfig(level=logging.DEBUG)
logging.info("Reading input file")

with open("input.txt") as file_in:
    lines = "".join(file_in.readlines());

# construct array of tokens for later use
tokens = [token for token in tokenize(lines)];

print_token_by_line(tokens);

print("\n\n");
