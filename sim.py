#!/usr/bin/python3

import collections  # for named tuple && Counter (multisets)
import re  # for regex
from enum import Enum # for enumerations (enum from C)
import logging # for logging functions
import colorlog # colors log output
import random # for stochastic chosing of programs
import time # for time.time()
from copy import copy # for shallow copy (value not reference as = does for objects)
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

class Pswarm():

    """Pswarm class that holds all the components of an Pswarm (colony of colonies)"""

    def __init__(self):
       self.C = [] # list of colony names
       self.colonies = {} # colony dictionary (colony_name : Pcolony_object)
       self.simResult = {} # simulation step result dictionary (colony_name : SimStepResult object)
    # end __init__()

    def _print_contents(self):
        """prints the contents of this Pswarm (protected method)"""
        print("    C = %s" % self.C)
        for colony_name in self.C:
            print() # add a line betwen colonies
            self.colonies[colony_name].print_colony_components(colony_name, indentSpacesNr = 8)
    # end __print_contents()
    
    def print_colonies(self):
        """Print the contents of this Pswarm"""
        print("Pswarm = {")
        self._print_contents()
        print("}")
    # end print_colonies()

    def runSimulationStep(self, printEachColonyState = False):
        """Runs one simulation step for all colonies that form this Pswarm
        :returns: SimStepResult values depending on the succes of the current run """

        finished = True

        for colony_name in self.C:
            # if this colony has ran all it's simulation steps (no more executables)
            if (self.simResult[colony_name] == SimStepResult.no_more_executables):
                # skip this colony
                continue

            logging.info("Running simulation step from %s Pcolony" % colony_name)
            self.simResult[colony_name] = self.colonies[colony_name].runSimulationStep()

            if (printEachColonyState):
                self.colonies[colony_name].print_colony_components(name = colony_name)

            # if the simulation stopped because there are no more executable programs
            if (self.simResult[colony_name] == SimStepResult.no_more_executables):
                logging.warning("%s Pcolony finished" % colony_name)
                continue; # go to next colony

            # if there was an error encountered during this simulation step
            elif (self.simResult[colony_name] == SimStepResult.error):
                logging.error("Error encountered")
                return SimStepResult.error # stop the simulation and mark it as failed

            # simResult = SimStepResult.finished (this step, but not over yet)
            else:
                finished = False
        #end for colony_name

        if (finished):
            return SimStepResult.no_more_executables

        # if the function reaches this step then the simulation step finished succesfully
        # but there still are colonies with executable programs
        return SimStepResult.finished
    # end runSimulationStep()

    def simulate(self, stepByStepConfirm = False, printEachColonyState = True, maxSteps = -1, maxTime = -1):
        """Simulates the Pswarm until there are no more programs (in any of the Pcolonies) to execute or one of the imposed limits is reached
        The function closely resembles the Pcolony.simulate() only that this function runs simulates all of the colonies synchronously.

        :stepByStepConfirm: True / False - whether or not to wait for confirmation before starting the next simulation step
        :maxSteps: The maximmum number of simulation steps to run
        :maxTime: The maximum time span that the entire simulation can last
        :returns: True / False depending on the succesfull finish of the simulation before reaching any of the limits"""

        # store the simulation result for each colony in the swarm (initially -1)
        self.simResult = {colony_name: -1 for colony_name in self.C}
        currentStep = 0;
        startTime = currentTime = time.time();
         # time.time() == time in seconds since the Epoch
        finalTime = currentTime + maxTime
        # becomes true when all colonies return simStepResult.no_more_executables
        finished = False

        while (not finished):
            logging.info("Starting simulation step %d", currentStep)

            # run the simulation step
            stepResult = self.runSimulationStep(printEachColonyState)
            if (stepResult == SimStepResult.error):
                return False # mark this simulation as failed because there was an error in this simulation step
            elif (stepResult == SimStepResult.no_more_executables):
                finished = True
            else:
                finished = False

            # store current time at simulation step end
            currentTime = time.time()
            if (stepByStepConfirm):
                input("Press ENTER to continue")
            
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
        self.print_colonies()
        
        # if the simulation reaches this step it means that the it finished succesfully
        return True
    # end simulate()
# end class Pswarm

class XPcolony(Pswarm):

    """XPcolony class, built upon the Pswarm (colony of colonies)"""

    def __init__(self, swarm = None):
        Pswarm.__init__(self)
        self.global_env = collections.Counter() # store objects found in the global environment
        # if we inherit an existing Pswarm
        if (swarm):
            self.C = copy(swarm.C)
            self.colonies = copy(swarm.colonies)
    # end __init__()
    
    def _print_contents(self):
        """Prints the contents of this XPcolony (protected method)"""
        print("    global_env = %s" % self.global_env.most_common(None))
        super()._print_contents()
    # end __print_contents()
    
    def print_colonies(self):
        """Print the contents of this XPcolony"""
        print("XPcolony = {")
        self._print_contents()
        print("}")
    # end print_colonies()
# end class XPcolony

class Pcolony:

    """Pcolony class that holds all the components of a P colony."""

    # constructor (members are defined inside in order to avoid alteration caused by other objects of this type)
    def __init__(self):
        self.A = []  # alphabet (list of objects)
        self.e = '' # elementary object
        self.f = '' # final object
        self.n = 0   # capacity
        self.env = collections.Counter() # store objects found in the environement
        self.B = []  # list of agent names
        self.agents = {} # agent dictionary (agent_name : Agent_object)
    #end __init__

    # TODO add specialized functions
    # TODO describe_colony
    
    def print_colony_components(self, name = "Pcolony", indentSpacesNr = 0):
        """Prints the given Pcolony as a tree, to aid in inspecting the internal structure of the parsed colony

        :colony: Pcolony type object used as input

        """

        print(" " * indentSpacesNr + "%s = {" % name)
        print(" " * (indentSpacesNr + 4) + "A = %s" % self.A)
        print(" " * (indentSpacesNr + 4) + "e = %s" % self.e)
        print(" " * (indentSpacesNr + 4) + "f = %s" % self.f)
        print(" " * (indentSpacesNr + 4) + "n = %s" % self.n)
        # print out only a:3 b:5 (None is used for printing all objects, not just the most common n)
        print(" " * (indentSpacesNr + 4) + "env = %s" % self.env.most_common(None))
        print(" " * (indentSpacesNr + 4) + "B = %s" % self.B)
        for ag_name in self.B:
            print(" " * (indentSpacesNr + 8) + "%s = (" % ag_name);
            # print out only a:3 b:5 (None is used for printing all objects, not just the most common n)
            print(" " * (indentSpacesNr + 12) + "obj = %s" % self.agents[ag_name].obj.most_common(None))
            print(" " * (indentSpacesNr + 12) + "programs = (")
            for i, program in enumerate(self.agents[ag_name].programs):
                print(" " * (indentSpacesNr + 16) + "P%d = <" % i)
                for rule in program:
                    rule.print(indentSpaces = 21 + indentSpacesNr)
                print(" " * (indentSpacesNr + 16) + ">")

            print(" " * (indentSpacesNr + 12) + ")")

            print(" " * (indentSpacesNr + 8) + ")")
        print(" " * indentSpacesNr + "}")

    #end print_colony_components()

    def runSimulationStep(self):
        """Runs 1 simulation step consisting of chosing (if available) and executing a program for each agent in the colony
        
        :returns: SimStepResult values depending on the succes of the current run """
        
        runnableAgents = [] # the list of agents that have an executable program

        for agent_name, agent in self.agents.items():
            logging.debug("Checking agent %s" % agent_name)
            # if the agent choses 1 program to execute
            if (agent.choseProgram()):
                logging.info("Agent %s is runnable" % agent_name)
                runnableAgents.append(agent_name)
        
        logging.info("%d runnable agents" % len(runnableAgents))
        
        # if there are no runnable agents
        if (len(runnableAgents) == 0):
            return SimStepResult.no_more_executables # simulation cannot continue

        for agent_name in runnableAgents:
            logging.info("Running Agent %s  Program %d" % (agent_name, self.agents[agent_name].chosenProgramNr))
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
            logging.debug("chosen_program =  %d" % self.chosenProgramNr)
            return True; # this agent has an executable program
        
        # there is more than 1 executable program
        elif (len(possiblePrograms) > 1):
            rand_value = random.randint(0, len(possiblePrograms) - 1) 
            self.chosenProgramNr = possiblePrograms[rand_value];
            logging.debug("stochastically_chosen_program =  %d" % self.chosenProgramNr)
            return True; # this agent has an executable program

        self.chosenProgramNr = -1 # no program can be executed
        logging.debug("no executable program")
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
    
    logging.debug("process_tokens (parent_type = %s, index = %d)" % (type(parent), index))
    result = parent # construct the result of specified type
    prev_token = tokens[index]
    rule = Rule() # dirty workaround to parsing rules recursively
    
    while (index < len(tokens)):
        token = tokens[index]
        logging.debug("token = '%s'" % token.value)

        if (type(parent) == XPcolony):
            if (token.type == 'ASSIGN'):
                if (prev_token.value == 'global_env'):
                    logging.info("building list");
                    index, objects = process_tokens(tokens, list(), index + 1);
                    # make sure that 1 simbolic e object is in env
                    if ('e' not in objects):
                        objects.append('e')
                    result.global_env = collections.Counter(objects)

        # XPcolony descends from Pswarm so it has all of Pswarms' member variables
        if (type(parent) == Pswarm or type(parent) == XPcolony):
            # process the following tokens as members of a Pcolony class
            logging.debug("processing as Pswarm")
            
            if (token.type == 'ASSIGN'):
                if (prev_token.value == 'C'):
                    logging.info("building list");
                    index, result.C = process_tokens(tokens, result.C, index + 1);

                # if the previout token was an colony name found in C
                elif (prev_token.value in result.C): 
                    logging.debug("building colony")
                    index, colony = process_tokens(tokens, Pcolony(), index + 1);
                    result.colonies[prev_token.value] = colony # store newly parsed agent indexed by name
                    logging.info("Constructed %s colony" % prev_token.value)

        elif (type(parent) == Pcolony):
            # process the following tokens as members of a Pcolony class
            logging.debug("processing as Pcolony")
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
            logging.debug("processing as Agent")
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
            logging.debug("processing as Program")
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
            logging.debug("processing as List")
            if (token.type == 'ID'):
                result.append(token.value);

        elif (type(parent) == str):
            logging.debug("processing as Str")
            if (token.type == 'ID'):
                result = token.value;

        elif (type(parent) == int):
            logging.debug("processing as Int")
            if (token.type == 'NUMBER'):
                result = int(token.value);

        else:
            logging.debug("processing as GENERAL")
            # process the token generally
            if (token.type == 'ASSIGN'):
                if (prev_token.value == 'pswarm'): 
                    logging.info("building Pswarm")
                    index, result = process_tokens(tokens, Pswarm(), index + 1);
                elif (prev_token.value == 'xp'): 
                    logging.info("building XPcolony")
                    index, result = process_tokens(tokens, XPcolony(), index + 1);
                else: 
                    logging.info("building Pcolony")
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

def readInputFile(filename, printTokens=False):
    """Parses the given input file and produces a Pcolony tree structure

    :filename: string path to the file that will be parsed
    :returns: Pcolony tree structure (Pcolony, Agent, Program, Rule)

    """
    logging.info("Reading input file")

    with open(filename) as file_in:
        lines = "".join(file_in.readlines());

    # construct array of tokens for later use
    tokens = [token for token in tokenize(lines)];

    if (printTokens):
        print_token_by_line(tokens);
        print("\n\n");

    index, end_result = process_tokens(tokens, None, 0)

    print("\n\n");
    if (type(end_result) == Pswarm or type(end_result) == XPcolony):
        end_result.print_colonies()
    elif (type(end_result == Pcolony)):
        end_result.print_colony_components()
    print("\n\n");

    return end_result
#end readInputFile()

##########################################################################
#   MAIN
if (__name__ == "__main__"):
    import sys # for argv

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
    if ('--debug' in sys.argv):
        colorlog.basicConfig(stream = sys.stdout, level = logging.DEBUG)
    else:
        colorlog.basicConfig(stream = sys.stdout, level = logging.INFO) # default log level
    stream = colorlog.root.handlers[0]
    stream.setFormatter(formatter);

    if (len(sys.argv) < 2):
        logging.error("Expected input file path as parameter")
        exit(1)
    
    # step by step simulation
    step = False
    if ('--step' in sys.argv):
        step = True

    end_result = readInputFile(sys.argv[1])

    end_result.simulate(stepByStepConfirm = step)

    print("\n\n");
