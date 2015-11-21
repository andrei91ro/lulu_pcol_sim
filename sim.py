#!/usr/bin/python3

import collections  # for named tuple && Counter (multisets)
import re  # for regex
from enum import Enum # for enumerations (enum from C)
import logging # for logging functions
import colorlog # colors log output
import random # for stochastic chosing of programs
import time # for time.time()
##########################################################################
# type definitions

class RuleType(Enum):

    """Enumeration of rule types """

    evolution = 1
    communication = 2
    conditional = 3

#end class RuleType

class RuleExecOption(Enum):

    """Enumeration of rule selection options (used mainly for marking the executable rule from a conditional rule)"""
    
    none = 1
    first = 2
    second = 3
#end class RuleExecOption

class SimStepResult(Enum):

    """Enumeration of possible results of running a simulation step"""

    finished = 1
    no_more_executables = 2
    error = 3
#end class SimStepResult

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
    # TODO describe_colony
    
    def print_colony_components(self):
        """Prints the given Pcolony as a tree, to aid in inspecting the internal structure of the parsed colony

        :colony: Pcolony type object used as input

        """

        print("Pcolony = {")
        print("    A = %s" % self.A)
        print("    e = %s" % self.e)
        print("    f = %s" % self.f)
        print("    n = %s" % self.n)
        # print out only a:3 b:5 (None is used for printing all objects, not just the most common n)
        print("    env = %s" % self.env.most_common(None))
        print("    B = %s" % self.B)
        for ag_name in self.B:
            print("        %s = (" % ag_name);
            # print out only a:3 b:5 (None is used for printing all objects, not just the most common n)
            print("             obj = %s" % self.agents[ag_name].obj.most_common(None))
            print("             programs = (")
            for i, program in enumerate(self.agents[ag_name].programs):
                print("                 P%d = <" % i)
                for rule in program:
                    rule.print(indentSpaces = 21)
                print("                 >")

            print("             )")

            print("        )")
        print("}")

    #end print_colony_components()

    def runSimulationStep(self):
        """Runs 1 simulation step consisting of chosing (if available) and executing a program for each agent in the colony
        
        :returns: SimStepResult values depending on the succes of the current run """
        
        runnableAgents = [] # the list of agents that have an executable program

        for agent_name, agent in self.agents.items():
            # if the agent choses 1 program to execute
            if (agent.choseProgram()):
                logging.debug("Agent %s is runnable" % agent_name)
                runnableAgents.append(agent_name)
        
        logging.info("%d runnable agents" % len(runnableAgents))
        
        # if there are no runnable agents
        if (len(runnableAgents) == 0):
            return SimStepResult.no_more_executables # simulation cannot continue

        for agent_name in runnableAgents:
            logging.debug("Running %s agent program nr %d" % (agent_name, self.agents[agent_name].chosenProgramNr))
            # if there were errors encountered during program execution
            if (self.agents[agent_name].executeProgram() == False):
                logging.error("Execution failed for agent %s, stopping simulation" % agent_name)
                return SimStepResult.error

        logging.info("Simulation step finished succesfully")
        return SimStepResult.finished
    # end runSimulationStep()

    def simulate(self, stepByStepConfirm = False, printEachColonyState = True, maxSteps = -1, maxTime = -1):
        """Simulates the Pcolony until there are no more programs to execute or one of the imposed limits is reached

        :stepByStepConfirm: True / False - whether or not to wait for confirmation before starting the next simulation step
        :maxSteps: The maximmum number of simulation steps to run
        :maxTime: The maximum time span that the entire simulation can last
        :returns: True / False depending on the succesfull finish of the simulation before reaching any of the limits"""

        currentStep = 0;
        startTime = currentTime = time.time();
         # time.time() == time in seconds since the Epoch
        finalTime = currentTime + maxTime
        
        while (True):
            logging.info("Starting simulation step %d", currentStep)
            
            simResult = self.runSimulationStep()
            currentTime = time.time()

            if (printEachColonyState):
                self.print_colony_components()

            if (stepByStepConfirm):
                input("Press ENTER to continue")

            # if the simulation stopped because there are no more executable programs
            if (simResult == SimStepResult.no_more_executables):
                break; # exit the loop

            # if there was an error encountered during this simulation step
            if (simResult == SimStepResult.error):
                logging.error("Error encountered")
                return False # stop the simulation and mark it as failed
            
            # if there is a maximum time limit set and it was exceded
            if ((currentTime >= finalTime) and (maxTime > 0)):
                logging.warning("Maximum time limit exceeded; Simulation stopped")
                return False # stop the simulation and mark it as failed
            
            # if there is a maximum step limit set and it was exceded
            if ((currentStep >= maxSteps) and (maxSteps > 0)):
                logging.warning("Maximum number of simulation steps exceeded; Simulation stopped")
                return False # stop the simulation and mark it as failed

            currentStep += 1
        #end while loop

        logging.info("Simulation finished succesfully after %d steps and %f seconds; End state below:" % (currentStep, currentTime - startTime))
        self.print_colony_components()
        
        # if the simulation reaches this step it means that the it finished succesfully
        return True
    # end simulate()
#end class Pcolony

class Agent:

    """Agent class used to represent a P colony agent."""

    # constructor (members are defined inside in order to avoid alteration caused by other objects of this type)
    def __init__(self, parent_colony):
        self.obj = collections.Counter() # objects stored by the agent (stored as a multiset thanks to Counter) 
        self.programs = [] # programs (list of programs (each program is a list of n  Rule objects))
        self.chosenProgramNr = -1 # the program that was chosen for execution
    #end __init__()
        self.colony = parent_colony # reference to my parent colony (for acces to env, e, ...)

    def choseProgram(self):
        """Chose an executable program (or chose stochastically from a list of executable programs)
        : env - the objects from the environement
        : returns True / False depending on the availability of an executable program"""
       
        possiblePrograms = [] # used to store executable programs
        for nr, program in enumerate(self.programs):
           
            logging.debug("checking program %d of %d" % (nr, len(self.programs)))
            executable = True
            for rule in program:
                
                # if rule is a simple, non-conditional rule
                if (rule.main_type != RuleType.conditional):
                    
                    # all types of rules require the left hand side obj to be available in the agent
                    if (rule.lhs not in self.obj):
                        executable = False;
                        break; # stop checking
                    
                    # communication rules require the right hand side obj to be available in the environement
                    if (rule.main_type == RuleType.communication and rule.rhs not in self.colony.env):
                        executable = False;
                        break;

                    rule.exec_rule_nr = RuleExecOption.first # the only option available
                
                # if this is a conditional rule
                else:
                    # all types of rules require the left hand side obj to be available in the agent
                    # if not in the prioritary rule then at least in the alternative rule
                    if ((rule.lhs not in self.obj) and (rule.alt_lhs not in self.obj)):
                        executable = False;
                        break; # stop checking
                    #if the first rule is of communication type and the right hand side object is not in the environement
                    if (rule.type == RuleType.communication and rule.rhs not in self.colony.env):
                        # the first rule cannot be executed so we check the second rule

                        # if the second rule is of communication type then the right hand side object has to be in the environement
                        if (rule.alt_type == RuleType.communication and rule.alt_rhs not in self.colony.env):
                            executable = False;
                            break;

                       # the second rule can be executed (and the first cannot)
                        else:
                           rule.exec_rule_nr = RuleExecOption.second # mark the second rule as executable
                             
                    # the first rule can be executed
                    else:
                        rule.exec_rule_nr = RuleExecOption.first # mark the first rule as executable
                
            #end for rule

            if (executable):
                possiblePrograms.append(nr)
        #end for program
        
        logging.debug("possiblePrograms = %s" % possiblePrograms)
        # if there is only 1 executable program
        if (len(possiblePrograms) == 1):
            self.chosenProgramNr = possiblePrograms[0];
            logging.info("chosen_program =  %d" % self.chosenProgramNr)
            return True; # this agent has an executable program
        
        # there is more than 1 executable program
        elif (len(possiblePrograms) > 1):
            rand_value = random.randint(0, len(possiblePrograms) - 1) 
            self.chosenProgramNr = possiblePrograms[rand_value];
            logging.info("stochastically_chosen_program =  %d" % self.chosenProgramNr)
            return True; # this agent has an executable program

        self.chosenProgramNr = -1 # no program can be executed
        logging.info("no executable program")
        return False 
            
    #end choseProgram()
    
    def executeProgram(self):
        """Execute the selected program and modify the agent and the environement according to the rules
        :returns: True / False depending on the succesfull execution the program"""

        if (self.chosenProgramNr < 0):
            return False;

        program = self.programs[self.chosenProgramNr]
        for rule in program:
            # if this is a non-conditional or the first rule of a conditional rule was chosen
            if (rule.exec_rule_nr == RuleExecOption.first):
                
                # remove one instance of rule.lhs from obj
                # both evolution and communication need this part
                self.obj[rule.lhs] -= 1;
                # 0 counts are allowed so if this is the case
                if (self.obj[rule.lhs] == 0):
                    # remove the entry from the obj counter
                    del self.obj[rule.lhs]
                
                if (rule.type == RuleType.evolution):
                    # add the rule.rhs object to obj
                    self.obj[rule.rhs] += 1
                
                # if this is a communication rule
                else:
                    # if the rule.rhs object is not in the environement any more
                    if (self.colony.env[rule.rhs] <= 0):
                        # this is an error, some other agent modified the environement
                        logging.error("Object %s was required in the environement by rule %s but was not found" % (rule.rhs, rule.print(toString = True)))
                        logging.error("Please check your rules and try again")
                        return False
                    
                    # remove one instance of rule.rhs from env only if it not 'e'
                    # 'e' object should remain constant in the environment
                    if (rule.rhs != self.colony.e):
                        # remove one instance of rule.rhs from env
                        self.colony.env[rule.rhs] -= 1;
                        # 0 counts are allowed so if this is the case
                        if (self.colony.env[rule.rhs] == 0):
                            # remove the entry from the env counter
                            del self.colony.env[rule.rhs]

                    # transfer object from environment to agent.obj
                    self.obj[rule.rhs] += 1
                   
                    # only modify the environment if the lhs object is not e
                    if (rule.lhs != self.colony.e): 
                        # transfer object from agent.obj to environment
                        self.colony.env[rule.lhs] += 1
            
            # if this is a conditional rule and the second rule was chosen for execution
            elif (rule.exec_rule_nr == RuleExecOption.second):

                # remove one instance of rule.alt_lhs from obj
                # both evolution and communication need this part
                self.obj[rule.alt_lhs] -= 1;
                # 0 counts are allowed so if this is the case
                if (self.obj[rule.alt_lhs] == 0):
                    # remove the entry from the obj counter
                    del self.obj[rule.alt_lhs]
                
                if (rule.alt_type == RuleType.evolution):
                    # add the rule.alt_rhs object to obj
                    self.obj[rule.alt_rhs] += 1
                
                # if this is a communication rule
                else:
                    # if the rule.alt_rhs object is not in the environement any more
                    if (self.colony.env[rule.alt_rhs] <= 0):
                        # this is an error, some other agent modified the environement
                        logging.error("Object %s was required in the environement by rule %s but was not found" % (rule.alt_rhs, rule.print(toString = True)))
                        logging.error("Please check your rules and try again")
                        return False
                    
                    # remove one instance of rule.alt_rhs from env only if it not 'e'
                    # 'e' object should remain constant in the environment
                    if (rule.alt_rhs != self.colony.e):
                        # remove one instance of rule.alt_rhs from env
                        self.colony.env[rule.alt_rhs] -= 1;
                        # 0 counts are allowed so if this is the case
                        if (self.colony.env[rule.alt_rhs] == 0):
                            # remove the entry from the env counter
                            del self.colony.env[rule.alt_rhs]

                    # transfer object from environment to agent.obj
                    self.obj[rule.alt_rhs] += 1
                    
                    # only modify the environment if the alt_lhs object is not e
                    if (rule.alt_lhs != self.colony.e): 
                        # transfer object from agent.obj to environment
                        self.colony.env[rule.alt_lhs] += 1
            # end elif exec_rule_nr == second
        
        # rule execution finished succesfully
        return True
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
        self.exec_rule_nr = RuleExecOption.none

        self.type = 0 
        self.lhs = '' # Left Hand Side operand
        self.rhs = '' # Right Hand Side operand
        
        # used only for conditional rules
        self.alt_type = 0
        self.alt_lhs = '' # Left Hand Side operand for alternative rule
        self.alt_rhs = '' # Right Hand Side operand for alternative rule

    def print(self, indentSpaces = 2, onlyExecutable = False, toString = False) :
        """Print a rule with a given indentation level

        :indentSpaces: number of spaces used for indentation
        :onlyExecutable: print the rule only if it is marked as executable"""
        
        result = ""

        if (self.main_type != RuleType.conditional):
            # print only if the onlyExecutable filter is not applied, or if applied and the rule is marked as executable
            if ( (not onlyExecutable) or (self.exec_rule_nr == RuleExecOption.first)):
                if (toString):
                    result = "%s %s %s" % (self.lhs, ruleNames[self.main_type], self.rhs)
                else:
                    print(" " * indentSpaces + "%s %s %s" % (self.lhs, ruleNames[self.main_type], self.rhs))
        else:
            # if the onlyExecutable filter is not applied, print the entire conditional rule
            if (not onlyExecutable):
                if (toString):
                    result = "(%s %s %s) / (%s %s %s)" % (
                        self.lhs, ruleNames[self.type], self.rhs,
                        self.alt_lhs, ruleNames[self.alt_type], self.alt_rhs)
                else:
                    print(" " * indentSpaces + "(%s %s %s) / (%s %s %s)" % (
                        self.lhs, ruleNames[self.type], self.rhs,
                        self.alt_lhs, ruleNames[self.alt_type], self.alt_rhs))
            else:
                # print only the executable component of the conditional rule
                if (self.exec_rule_nr == RuleExecOption.first):
                    if (toString):
                        result = "%s %s %s" % (self.lhs, ruleNames[self.type], self.rhs)
                    else:
                        print(" " * indentSpaces + "%s %s %s" % (self.lhs, ruleNames[self.type], self.rhs))
                else:
                    if (toString):
                        result = "%s %s %s" % (self.rhs, ruleNames[self.alt_type], self.rhs)
                    else:
                        print(" " * indentSpaces + "%s %s %s" % (self.rhs, ruleNames[self.alt_type], self.rhs))
        
        return result
    # end print()
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
                    # make sure that 1 simbolic e object is in env
                    if (result.e not in objects):
                        objects.append(result.e)
                    result.env = collections.Counter(objects)
                
                elif (prev_token.value == 'B'):
                    logging.info("building list");
                    index, result.B = process_tokens(tokens, result.B, index + 1);
                
                # if the previout token was an agent name found in B
                elif (prev_token.value in result.B):
                    logging.info("constructing agent");
                    index, agent = process_tokens(tokens, Agent(result), index + 1);
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
end_result.print_colony_components()

print("\n\n");
