#!/usr/bin/python3

import collections  # for named tuple && Counter (multisets)
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

ruleNames = {
        RuleType.evolution : '->',
        RuleType.communication : '<->',
        RuleType.conditional : '/',
}

# tuple used to describe parsed data
Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

class Pcolony:

    """Pcolony class that holds all the components of a P colony."""

    # constructor (members are defined inside in order to avoid alteration caused by other objects of this type)
    def __init__(self):
        self.A = []  # alphabet (list of objects)
        self.e = '' # elementary object
        self.f = '' # final object
        self.n = 0   # capacity
        self.env = collections.Counter() # store objects found in the environement
        self.B = []  # agents (list of Agent type objects)
        self.agents = {} # agent dictionary (agent_name : Agent_object)
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
        # all *type members take values from RuleType
        self.main_type = 0 # used to distinguish a conditional (composed) rule from simple rules
        
        self.type = 0 
        self.lhs = '' # Left Hand Side operand
        self.rhs = '' # Right Hand Side operand
        
        # used only for conditional rules
        self.alt_type = 0
        self.alt_lhs = '' # Left Hand Side operand for alternative rule
        self.alt_rhs = '' # Right Hand Side operand for alternative rule
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

def print_colony_components(colony):
    """Prints the given Pcolony as a tree, to aid in inspecting the internal structure of the parsed colony

    :colony: Pcolony type object used as input

    """

    print("Pcolony = {")
    print("    A = %s" % colony.A)
    print("    e = %s" % colony.e)
    print("    f = %s" % colony.f)
    print("    n = %s" % colony.n)
    # print out only a:3 b:5 (None is used for printing all objects, not just the most common n)
    print("    env = %s" % colony.env.most_common(None))
    print("    B = %s" % colony.B)
    for ag_name in colony.B:
        print("        %s = (" % ag_name);
        # print out only a:3 b:5 (None is used for printing all objects, not just the most common n)
        print("             obj = %s" % colony.agents[ag_name].obj.most_common(None))
        print("             programs = (")
        for i, program in enumerate(colony.agents[ag_name].programs):
            print("                 P%d = <" % i)
            for rule in program:
                if (rule.main_type != RuleType.conditional):
                    print("                     %s %s %s" % (rule.lhs, ruleNames[rule.main_type], rule.rhs))
                else:
                    print("                     (%s %s %s) / (%s %s %s)" % (
                        rule.lhs, ruleNames[rule.type], rule.rhs,
                        rule.alt_lhs, ruleNames[rule.alt_type], rule.alt_rhs,))
            print("                 >")

        print("             )")

        print("        )")
    print("}")

#end print_colony_components()

def process_tokens(tokens, parent, index):
    """Process tokens recurently and return a P colony structure (or a subcomponent of the same type as parent)

    :tokens: the list of tokens to be processed
    :parent: an object that represents the type of the result
    :index: the start index in the list of tokens
    :returns: index - the current index in the token list (after finishing this component)
    :returns: result - an object that is the result of processing the input parent and tokens
    
    """
    
    logging.warning("process_tokens (parent_type = %s, index = %d)" % (type(parent), index))
    result = parent # construct the result of specified type
    prev_token = tokens[index]
    rule = Rule() # dirty workaround to parsing rules recursively
    
    while (index < len(tokens)):
        token = tokens[index]
        logging.debug("token = '%s'" % token.value)
        
        if (type(parent) == Pcolony):
            # process the following tokens as members of a Pcolony class
            logging.warning("processing as Pcolony")
            if (token.type == 'ASSIGN'):
                if (prev_token.value == 'A'):
                    logging.info("building list");
                    index, result.A = process_tokens(tokens, result.A, index + 1);
                
                elif (prev_token.value == 'e'):
                    logging.info("setting value");
                    index, result.e = process_tokens(tokens, result.e, index + 1);
                
                elif (prev_token.value == 'f'):
                    logging.info("setting value");
                    index, result.f = process_tokens(tokens, result.f, index + 1);
                
                elif (prev_token.value == 'n'):
                    logging.info("setting value");
                    index, result.n = process_tokens(tokens, result.n, index + 1);
                
                elif (prev_token.value == 'env'):
                    logging.info("building list");
                    index, objects = process_tokens(tokens, list(), index + 1);
                    result.env = collections.Counter(objects)
                
                elif (prev_token.value == 'B'):
                    logging.info("building list");
                    index, result.B = process_tokens(tokens, result.B, index + 1);
                
                # if the previout token was an agent name found in B
                elif (prev_token.value in result.B):
                    logging.info("constructing agent");
                    index, agent = process_tokens(tokens, Agent(), index + 1);
                    result.agents[prev_token.value] = agent # store newly parsed agent indexed by name

        elif (type(parent) == Agent):
            logging.warning("processing as Agent")
            # process the following tokens as members of an Agent class
            
            # agent object lists are separated with curly braces
            if (token.type == 'L_CURLY_BRACE'):
                logging.info("building object counter from object list");
                index, objects = process_tokens(tokens, list(), index + 1);
                result.obj = collections.Counter(objects)
            
            # agent programs start with '<'
            if (token.type == 'SMALLER'):
                logging.info("building program");
                index, program = process_tokens(tokens, Program(), index + 1);
                result.programs.append(program)
        
        elif (type(parent) == Program):
            logging.warning("processing as Program")
            # process the following tokens as members of an Program class 
            
            # if i reached the end of a rule definition
            if (token.type == 'COLUMN'):
                logging.info("Added new rule")
                # if the main type of the rule is not set (i.e it was not declared as a conditional rule)
                if (rule.main_type == 0):
                    rule.main_type = rule.type
                # append the new rule to the program
                result.append(rule);
                rule = Rule() # re-initialize the rule object used for rule building
            
            elif (token.type == 'LARGER'):
                logging.info("finishing Program")
                # if the main type of the rule is not set (i.e it was not declared as a conditional rule)
                if (rule.main_type == 0):
                    rule.main_type = rule.type
                # append the new rule to the program
                result.append(rule);
                logging.info("finished this program with result = %s" % result)
                return index, result;
            
            else:
                # if this is not a conditional rule
                if (rule.main_type != RuleType.conditional):
                    if (token.type == 'ID'):
                            #if the left hand side of the rule is unfilled
                            if (rule.lhs == ''):
                                rule.lhs = token.value
                            else:
                                rule.rhs = token.value
                    elif (token.type == 'EVOLUTION'):
                        rule.type = RuleType.evolution
                    elif (token.type == 'COMMUNICATION'):
                        rule.type = RuleType.communication
                    elif (token.type == 'CHECK_SIGN'):
                        rule.main_type = RuleType.conditional
                
                # if this is a conditional rule then use the alternate fields
                else:
                    if (token.type == 'ID'):
                        #if the left hand side of the rule is unfilled
                        if (rule.alt_lhs == ''):
                            rule.alt_lhs = token.value
                        else:
                            rule.alt_rhs = token.value
                    elif (token.type == 'EVOLUTION'):
                        rule.alt_type = RuleType.evolution
                    elif (token.type == 'COMMUNICATION'):
                        rule.alt_type = RuleType.communication
                    elif (token.type == 'CHECK_SIGN'):
                        rule.main_type = RuleType.conditional
        
        elif (type(parent) == list):
            logging.warning("processing as List")
            if (token.type == 'ID'):
                result.append(token.value);

        elif (type(parent) == str):
            logging.warning("processing as Str")
            if (token.type == 'ID'):
                result = token.value;

        elif (type(parent) == int):
            logging.warning("processing as Int")
            if (token.type == 'NUMBER'):
                result = int(token.value);

        else:
            logging.warning("processing as GENERAL")
            # process the token generally
            if (token.type == 'ASSIGN' and prev_token.value == 'pi'): 
                index, result = process_tokens(tokens, Pcolony(), index + 1);

        if (token.type == 'END'):
            logging.info("finished this block with result = %s" % result)
            return index, result;

        #if (token.type == 'L_CURLY_BRACE'):
            #index, result = process_tokens(tokens, new_descendant, index + 1);
        
        prev_token = token;
        index += 1
    return index, result
#end process_tokens


##########################################################################
#   MAIN
formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s %(message)s %(reset)s",
        datefmt=None,
        reset=True,
        log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
)
colorlog.basicConfig(level = logging.DEBUG)
stream = colorlog.root.handlers[0]
stream.setFormatter(formatter);

logging.info("Reading input file")

with open("input.txt") as file_in:
    lines = "".join(file_in.readlines());

# construct array of tokens for later use
tokens = [token for token in tokenize(lines)];

print_token_by_line(tokens);

print("\n\n");
index, end_result = process_tokens(tokens, None, 0)

print("\n\n");
