#!/usr/bin/python3

import collections  # for named tuple && Counter (multisets)
import re  # for regex
from enum import Enum # for enumerations (enum from C)
import logging # for logging functions
import random # for stochastic chosing of programs
import time # for time.time()
#from copy import deepcopy # for deepcopy (value not reference as = does for objects)
##########################################################################
# type definitions

logLevel = logging.INFO

class RuleType(Enum):

    """Enumeration of rule types """

    evolution = 1
    communication = 2
    conditional = 3
    exteroceptive = 4
    in_exteroceptive = 5
    out_exteroceptive = 6

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
        RuleType.exteroceptive : '<=>',
        RuleType.in_exteroceptive : '<I=>',
        RuleType.out_exteroceptive : '<=O>',
}

# tuple used to describe parsed data
Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

class Pswarm():

    """Pswarm class that holds all the components of an Pswarm (colony of colonies)"""

    def __init__(self, swarm = None):
       self.C = [] # list of colony names
       self.colonies = {} # colony dictionary (colony_name : Pcolony_object)
       self.simResult = {} # simulation step result dictionary (colony_name : SimStepResult object)
       self.global_env = collections.Counter() # store the objects from the global (swarm) environemnt
       self.in_global_env = collections.Counter() # store the objects from the INPUT global (swarm) environemnt
       self.out_global_env = collections.Counter() # store the objects from the OUTPUT global (swarm) environemnt

       if (swarm != None):
           self.copy_init(swarm)
    # end __init__()

    def copy_init(self, swarm):
        """Copies all of the members of the swarm object into this instance (copy contructor from C++)

        :swarm: source Pswarm object"""

        self.C = list(swarm.C)
        self.global_env = collections.Counter(swarm.global_env)
        self.in_global_env = collections.Counter(swarm.in_global_env)
        self.out_global_env = collections.Counter(swarm.out_global_env)

        for col_name in swarm.C:
            # deep copy each colony and set self as parent swarm
            self.colonies[col_name] = swarm.colonies[col_name].getDeepCopyOf(self)
            self.simResult[col_name] = swarm.simResult[col_name]

    # end copy_init()

    def getDeepCopyOf(self):
        """Returns a value copy of the Pswarm, similar to a copy constructor in C++
        :returns: identical value-copy of this Pswarm"""

        newSwarm = Pswarm(self)

        return newSwarm
    # end getDeepCopyOf()

    def print_swarm_components(self):
        """Print the contents of this Pswarm"""
        print("Pswarm = {")
        print("    global_env = %s" % self.global_env.most_common(None))
        print("    in_global_env = %s" % self.in_global_env.most_common(None))
        print("    out_global_env = %s" % self.out_global_env.most_common(None))
        print("    C = %s" % self.C)
        for colony_name in self.C:
            print() # add a line betwen colonies
            self.colonies[colony_name].print_colony_components(colony_name, indentSpacesNr = 8)
        print("}")
    # end print_swarm_components()

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

    def simulate(self, stepByStepConfirm = False, printEachSwarmState = True, maxSteps = -1, maxTime = -1):
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
            stepResult = self.runSimulationStep()
            if (stepResult == SimStepResult.error):
                return False # mark this simulation as failed because there was an error in this simulation step
            elif (stepResult == SimStepResult.no_more_executables):
                finished = True
            else:
                finished = False

            # store current time at simulation step end
            currentTime = time.time()

            if (printEachSwarmState):
                self.print_swarm_components()

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
        self.print_swarm_components()
        
        # if the simulation reaches this step it means that the it finished succesfully
        return True
    # end simulate()
# end class Pswarm

class Pcolony:

    """Pcolony class that holds all the components of a P colony."""

    # constructor (members are defined inside in order to avoid alteration caused by other objects of this type)
    def __init__(self):
        self.A = []  # alphabet (list of objects)
        self.e = 'e' # elementary object, 'e' by default
        self.f = 'f' # final object, 'f' by default (does not have any special meaning)
        self.n = 0   # capacity
        self.env = collections.Counter() # store objects found in the environement
        self.B = []  # list of agent names
        self.agents = {} # agent dictionary (agent_name : Agent_object)
        self.parentSwarm = None
    #end __init__

    def getDeepCopyOf(self, parent_swarm = None):
        """Returns a value copy of the Pcolony, similar to a copy constructor in C++
        :parent_swarm: Pswarm object that, if specified, will be assigned as parentSwarm for the new P colony
        :returns: identical value-copy of this Pcolony"""

        newColony = Pcolony()
        newColony.A = list(self.A)
        newColony.e = self.e
        newColony.f = self.f
        newColony.n = self.n
        newColony.env = collections.Counter(self.env)
        newColony.B = list(self.B)

        for ag_name in self.B:
            # deep copy each agent
            newColony.agents[ag_name] = self.agents[ag_name].getDeepCopyOf(newColony)

        if (parent_swarm != None):
            newColony.parentSwarm = parent_swarm
        else:
            newColony.parentSwarm = self.parentSwarm

        return newColony
    # end getDeepCopyOf()

    def processWildcards(self, suffixList, myId):
        """Recursively replaces wildcards with the appropriate replacements (from suffixList) in the
        alphabet A, environment and each agent
        :suffixList: list of strings that will replace the wildcard *
        :myId: string used to replace '%id' wildcard"""

        self.A = processObjectListWildcards(self.A, suffixList, myId)
        self.env = processObjectCounterWildcards(self.env, suffixList, myId)
        # process wildcards from all agents
        for ag_name in self.B:
            self.agents[ag_name].processWildcards(suffixList, myId)
    # end processWildcards()

    def print_colony_components(self, name = "Pcolony", indentSpacesNr = 0, printDetails = False):
        """Prints the given Pcolony as a tree, to aid in inspecting the internal structure of the parsed colony

        :colony: Pcolony type object used as input
        :indentSpaces: The number of indent spaces that are added for P swarm components or P colony components
        :printDetails: True / False, Whether or not to print P colony details (alphabet, capacity, programs)

        """

        print(" " * indentSpacesNr + "%s = {" % name)
        if (printDetails):
            print(" " * (indentSpacesNr + 4) + "A = %s" % self.A)
            print(" " * (indentSpacesNr + 4) + "e = %s" % self.e)
            print(" " * (indentSpacesNr + 4) + "f = %s" % self.f)
            print(" " * (indentSpacesNr + 4) + "n = %s" % self.n)
        # print out only a:3 b:5 (None is used for printing all objects, not just the most common n)
        print(" " * (indentSpacesNr + 4) + "env = %s" % self.env.most_common(None))
        if (printDetails):
            print(" " * (indentSpacesNr + 4) + "B = %s" % self.B)
        for ag_name in self.B:
            print(" " * (indentSpacesNr + 8) + "%s = (" % ag_name);
            # print out only a:3 b:5 (None is used for printing all objects, not just the most common n)
            print(" " * (indentSpacesNr + 12) + "obj = %s" % self.agents[ag_name].obj.most_common(None))

            if (not printDetails):
                continue

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
            logging.info("Running Agent %s  P%d = < %s >" % (agent_name, self.agents[agent_name].chosenProgramNr, self.agents[agent_name].programs[self.agents[agent_name].chosenProgramNr].print(onlyExecutable = True)))
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
        self.colony = parent_colony # reference to my parent colony (for acces to env, e, ...)
    #end __init__()

    def getDeepCopyOf(self, parent_colony):
        """Returns a value copy of the Agent, similar to a copy constructor in C++
        :returns: identical value-copy of this Agent"""

        newAgent = Agent(parent_colony)
        newAgent.obj = collections.Counter(self.obj)

        for program in self.programs:
            newAgent.programs.append(program.getDeepCopyOf())
        # newAgent.chosenProgramNr set at each sim step

        return newAgent
    # end getDeepCopyOf()

    def processWildcards(self, suffixList, myId):
        """Replaces * wildcards with each of suffixes provided in any program that contains wildcards or in obj
        When replacing wildcards in programs these are cloned and the rules edited accordingly, finally deleting
        the original wildcarded program; ex: < e->e, e->d_* > => < e->e, e->d_0 >; < e->e, e->d_1 >
        for suffixList = ['0', '1']

        Replaces %id wildcard with the value of myId in obj and programs

        :suffixList: list of strings
        :myId: string used to replace '%id' wildcard"""

        self.obj = processObjectCounterWildcards(self.obj, suffixList, myId)

        # processs %id wildcard first because it is shorter
        for program in self.programs[:]:
            if (program.hasWildcards('%id')):
                newProgram = program.getDeepCopyOf()
                for rule in newProgram:
                    # determine which rule has wildcards
                    if (rule.hasWildcards('%id')):
                        # replace '%id' wildcard with myId
                        rule.lhs = rule.lhs.replace('%id', myId)
                        rule.rhs = rule.rhs.replace('%id', myId)
                        rule.alt_lhs = rule.alt_lhs.replace('%id', myId)
                        rule.alt_rhs = rule.alt_rhs.replace('%id', myId)
                # end for rule
                self.programs.append(newProgram)
                # remove old wildcarded program
                self.programs.remove(program)

        # process * wildcard
        for program in self.programs[:]:
            if (program.hasWildcards('*')):
                for suffix in suffixList:
                    newProgram = program.getDeepCopyOf()
                    for rule in newProgram:
                        # determine which rule has wildcards
                        if (rule.hasWildcards('*')):
                            # replace '*' wildcard with the current suffix
                            rule.lhs = rule.lhs.replace('*', suffix)
                            rule.rhs = rule.rhs.replace('*', suffix)
                            rule.alt_lhs = rule.alt_lhs.replace('*', suffix)
                            rule.alt_rhs = rule.alt_rhs.replace('*', suffix)
                    # end for rule
                    self.programs.append(newProgram)
                # end for suffix
                self.programs.remove(program)
    # end processWildcards()

    def choseProgram(self):
        """Chose an executable program (or chose stochastically from a list of executable programs)
        : env - the objects from the environement
        : returns True / False depending on the availability of an executable program"""

       
        possiblePrograms = [] # used to store executable programs
        for nr, program in enumerate(self.programs):
           
            logging.debug("checking program %d of %d" % (nr, len(self.programs)))

            required_obj = collections.Counter()
            required_env = collections.Counter()
            required_global_env = collections.Counter()
            required_in_global_env = collections.Counter()
            required_out_global_env = collections.Counter()

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

                    # exteroceptive rules require the right hand side obj to be available in the global Pswarm environment
                    if (rule.main_type == RuleType.exteroceptive and rule.rhs not in self.colony.parentSwarm.global_env):
                        executable = False;
                        break;

                    # in_exteroceptive rules require the right hand side obj to be available in the INPUT global Pswarm environment
                    if (rule.main_type == RuleType.in_exteroceptive and rule.rhs not in self.colony.parentSwarm.in_global_env):
                        executable = False;
                        break;

                    # out_exteroceptive rules require the right hand side obj to be available in the OUTPUT global Pswarm environment
                    if (rule.main_type == RuleType.out_exteroceptive and rule.rhs not in self.colony.parentSwarm.out_global_env):
                        executable = False;
                        break;

                    rule.exec_rule_nr = RuleExecOption.first # the only option available

                    # if we reach this step, then the rule is executable
                    required_obj[rule.lhs] += 1 # all rules need the lhs to be in obj

                    if (rule.main_type == RuleType.communication):
                        required_env[rule.rhs] += 1 # rhs part of the rule has to be in the Pcolony environment

                    if (rule.main_type == RuleType.exteroceptive):
                        required_global_env[rule.rhs] += 1 # rhs part of the rule has to be in the Pswarm global environment

                    if (rule.main_type == RuleType.in_exteroceptive):
                        required_in_global_env[rule.rhs] += 1 # rhs part of the rule has to be in the Pswarm INPUT global environment

                    if (rule.main_type == RuleType.out_exteroceptive):
                        required_out_global_env[rule.rhs] += 1 # rhs part of the rule has to be in the Pswarm OUTPUT global environment

                # if this is a conditional rule
                else:
                    # all types of rules require the left hand side obj to be available in the agent
                    # if not in the prioritary rule then at least in the alternative rule
                    if ((rule.lhs not in self.obj) and (rule.alt_lhs not in self.obj)):
                        executable = False;
                        break; # stop checking
                    #if the first rule is of communication type and the right hand side object is not in the environement
                    #   or the first rule is of exteroceptive type and the right hand side object is not in the global environement
                    #   or the first rule is of in_exteroceptive type and the right hand side object is not in the INPUT global environement
                    #   or the first rule is of out_exteroceptive type and the right hand side object is not in the OUTPUT global environement
                    if ( (rule.type == RuleType.communication and rule.rhs not in self.colony.env)
                            or (rule.type == RuleType.exteroceptive and rule.rhs not in self.colony.parentSwarm.global_env)
                            or (rule.type == RuleType.in_exteroceptive and rule.rhs not in self.colony.parentSwarm.in_global_env)
                            or (rule.type == RuleType.out_exteroceptive and rule.rhs not in self.colony.parentSwarm.out_global_env) ):
                        # the first rule cannot be executed so we check the second rule

                        # if the second rule is of communication type then the right hand side object has to be in the environement
                        if (rule.alt_type == RuleType.communication and rule.alt_rhs not in self.colony.env):
                            executable = False;
                            break;

                        # if the second rule is of exteroceptive type then the right hand side object has to be in the global Pswarm environement
                        if (rule.alt_type == RuleType.exteroceptive and rule.alt_rhs not in self.colony.parentSwarm.global_env):
                            executable = False;
                            break;

                        # if the second rule is of in_exteroceptive type then the right hand side object has to be in the INPUT global Pswarm environement
                        if (rule.alt_type == RuleType.in_exteroceptive and rule.alt_rhs not in self.colony.parentSwarm.in_global_env):
                            executable = False;
                            break;

                        # if the second rule is of out_exteroceptive type then the right hand side object has to be in the OUTPUT global Pswarm environement
                        if (rule.alt_type == RuleType.out_exteroceptive and rule.alt_rhs not in self.colony.parentSwarm.out_global_env):
                            executable = False;
                            break;

                       # the second rule can be executed (and the first cannot)
                        else:
                            rule.exec_rule_nr = RuleExecOption.second # mark the second rule as executable

                            # if we reach this step, then the rule is executable
                            required_obj[rule.alt_lhs] += 1 # all rules need the alt_lhs to be in obj

                            if (rule.alt_type == RuleType.communication):
                                required_env[rule.alt_rhs] += 1 # alt_rhs part of the rule has to be in the Pcolony environment

                            if (rule.alt_type == RuleType.exteroceptive):
                                required_global_env[rule.alt_rhs] += 1 # alt_rhs part of the rule has to be in the Pswarm global environment

                            if (rule.alt_type == RuleType.in_exteroceptive):
                                required_in_global_env[rule.alt_rhs] += 1 # alt_rhs part of the rule has to be in the Pswarm INPUT global environment

                            if (rule.alt_type == RuleType.out_exteroceptive):
                                required_out_global_env[rule.alt_rhs] += 1 # alt_rhs part of the rule has to be in the Pswarm OUTPUT global environment

                    # the first rule can be executed
                    else:
                        rule.exec_rule_nr = RuleExecOption.first # mark the first rule as executable

                        # if we reach this step, then the rule is executable
                        required_obj[rule.lhs] += 1 # all rules need the lhs to be in obj

                        if (rule.type == RuleType.communication):
                            required_env[rule.rhs] += 1 # rhs part of the rule has to be in the Pcolony environment

                        if (rule.type == RuleType.exteroceptive):
                            required_global_env[rule.rhs] += 1 # rhs part of the rule has to be in the Pswarm global environment

                        if (rule.type == RuleType.in_exteroceptive):
                            required_in_global_env[rule.rhs] += 1 # rhs part of the rule has to be in the Pswarm INPUT global environment

                        if (rule.type == RuleType.out_exteroceptive):
                            required_out_global_env[rule.rhs] += 1 # rhs part of the rule has to be in the Pswarm OUTPUT global environment

            #end for rule

            # if all previous rule tests confirm that this program is executable
            if (executable):
                # check that the Agent obj requirements of the program are met
                for k, v in required_obj.items():
                    if (self.obj[k] < v):
                        logging.debug("required_obj check failed")
                        executable = False # this program is not executable, check another program

                # if e object is among the required objects in the Pcolony environment
                if ('e' in required_env):
                    # ignore this requirement because in theory, there are always enough e objects in the environment
                    del required_env['e']
                # check that the Pcolony env requirements of the program are met
                for k, v in required_env.items():
                    if (self.colony.env[k] < v):
                        logging.debug("required_env check failed")
                        executable = False # this program is not executable, check another program

                # if e object is among the required objects in the Pswarm global_environment
                if ('e' in required_global_env):
                    # ignore this requirement because in theory, there are always enough e objects in the global_environment
                    del required_global_env['e']
                # check that the Pswarm global_env requirements of the program are met
                for k, v in required_global_env.items():
                    if (self.colony.parentSwarm.global_env[k] < v):
                        logging.debug("required_global_env check failed")
                        executable = False # this program is not executable, check another program

                # if e object is among the required objects in the Pswarm INPUT global_environment
                if ('e' in required_in_global_env):
                    # ignore this requirement because in theory, there are always enough e objects in the INPUT global_environment
                    del required_in_global_env['e']
                # check that the Pswarm in_global_env requirements of the program are met
                for k, v in required_in_global_env.items():
                    if (self.colony.parentSwarm.in_global_env[k] < v):
                        logging.debug("required_in_global_env check failed")
                        executable = False # this program is not executable, check another program

                # if e object is among the required objects in the Pswarm OUTPUT global_environment
                if ('e' in required_out_global_env):
                    # ignore this requirement because in theory, there are always enough e objects in the OUTPUT global_environment
                    del required_out_global_env['e']
                # check that the Pswarm out_global_env requirements of the program are met
                for k, v in required_out_global_env.items():
                    if (self.colony.parentSwarm.out_global_env[k] < v):
                        logging.debug("required_out_global_env check failed")
                        executable = False # this program is not executable, check another program

            if (executable):
                # if we reach this step then this program is executable
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
                
                # if the rule.lhs object is not in obj any more
                if (self.obj[rule.lhs] <= 0):
                    # this is an error, there was a bug in choseProgram() that shouldn't have chosen this program
                    logging.error("Object %s was required in the agent by rule %s but was not found" % (rule.lhs, rule.print(toString = True)))
                    logging.error("Please file a bug report regarding Pcolony.choseProgram()")
                    return False

                # remove one instance of rule.lhs from obj
                # evolution and communication and exteroceptive need this part
                self.obj[rule.lhs] -= 1;
                # 0 counts are allowed so if this is the case
                if (self.obj[rule.lhs] == 0):
                    # remove the entry from the obj counter
                    del self.obj[rule.lhs]
                
                if (rule.type == RuleType.evolution):
                    # add the rule.rhs object to obj
                    self.obj[rule.rhs] += 1
                
                elif (rule.type == RuleType.communication):
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

                    # only modify the environment if the lhs object is not e
                    if (rule.lhs != self.colony.e): 
                        # transfer object from agent.obj to environment
                        self.colony.env[rule.lhs] += 1
            
                    # transfer object from environment to agent.obj
                    self.obj[rule.rhs] += 1

                elif (rule.type == RuleType.exteroceptive):
                    # if the rule.rhs object is not in the global swarm environement any more
                    if (self.colony.parentSwarm.global_env[rule.rhs] <= 0):
                        # this is an error, some other agent modified the environement
                        logging.error("Object %s was required in the global swarm environement by rule %s but was not found" % (rule.rhs, rule.print(toString = True)))
                        logging.error("Please check your rules and try again")
                        return False

                    # remove one instance of rule.rhs from global swarm env only if it not 'e'
                    # 'e' object should remain constant in the environment
                    if (rule.rhs != self.colony.e):
                        # remove one instance of rule.rhs from global swarm env
                        self.colony.parentSwarm.global_env[rule.rhs] -= 1;
                        # 0 counts are allowed so if this is the case
                        if (self.colony.parentSwarm.global_env[rule.rhs] == 0):
                            # remove the entry from the env counter
                            del self.colony.parentSwarm.global_env[rule.rhs]

                    # only modify the global swarm environment if the lhs object is not e
                    if (rule.lhs != self.colony.e): 
                        # transfer object from agent.obj to global swarm environment
                        self.colony.parentSwarm.global_env[rule.lhs] += 1
 
                    # transfer object from global environment to agent.obj
                    self.obj[rule.rhs] += 1
                #endif RuleType.exteroceptive

                elif (rule.type == RuleType.in_exteroceptive):
                    # if the rule.rhs object is not in the INPUT global swarm environement any more
                    if (self.colony.parentSwarm.in_global_env[rule.rhs] <= 0):
                        # this is an error, some other agent modified the environement
                        logging.error("Object %s was required in the INPUT global swarm environement by rule %s but was not found" % (rule.rhs, rule.print(toString = True)))
                        logging.error("Please check your rules and try again")
                        return False

                    # remove one instance of rule.rhs from INPUT global swarm env only if it not 'e'
                    # 'e' object should remain constant in the environment
                    if (rule.rhs != self.colony.e):
                        # remove one instance of rule.rhs from INPUT global swarm env
                        self.colony.parentSwarm.in_global_env[rule.rhs] -= 1;
                        # 0 counts are allowed so if this is the case
                        if (self.colony.parentSwarm.in_global_env[rule.rhs] == 0):
                            # remove the entry from the env counter
                            del self.colony.parentSwarm.in_global_env[rule.rhs]

                    # only modify the INPUT global swarm environment if the lhs object is not e
                    if (rule.lhs != self.colony.e):
                        # transfer object from agent.obj to INPUT global swarm environment
                        self.colony.parentSwarm.in_global_env[rule.lhs] += 1

                    # transfer object from INPUT global environment to agent.obj
                    self.obj[rule.rhs] += 1
                #endif RuleType.in_exteroceptive

                elif (rule.type == RuleType.out_exteroceptive):
                        # if the rule.rhs object is not in the OUTPUT global swarm environement any more
                    if (self.colony.parentSwarm.out_global_env[rule.rhs] <= 0):
                        # this is an error, some other agent modified the environement
                        logging.error("Object %s was required in the OUTPUT global swarm environement by rule %s but was not found" % (rule.rhs, rule.print(toString = True)))
                        logging.error("Please check your rules and try again")
                        return False

                    # remove one instance of rule.rhs from OUTPUT global swarm env only if it not 'e'
                    # 'e' object should remain constant in the environment
                    if (rule.rhs != self.colony.e):
                        # remove one instance of rule.rhs from OUTPUT global swarm env
                        self.colony.parentSwarm.out_global_env[rule.rhs] -= 1;
                        # 0 counts are allowed so if this is the case
                        if (self.colony.parentSwarm.out_global_env[rule.rhs] == 0):
                            # remove the entry from the env counter
                            del self.colony.parentSwarm.out_global_env[rule.rhs]

                    # only modify the OUTPUT global swarm environment if the lhs object is not e
                    if (rule.lhs != self.colony.e):
                        # transfer object from agent.obj to OUTPUT global swarm environment
                        self.colony.parentSwarm.out_global_env[rule.lhs] += 1

                    # transfer object from OUTPUT global environment to agent.obj
                    self.obj[rule.rhs] += 1
                #endif RuleType.out_exteroceptive

            # if this is a conditional rule and the second rule was chosen for execution
            elif (rule.exec_rule_nr == RuleExecOption.second):

                # if the rule.alt_lhs object is not in obj any more
                if (self.obj[rule.alt_lhs] <= 0):
                    # this is an error, there was a bug in choseProgram() that shouldn't have chosen this program
                    logging.error("Object %s was required in the agent by rule %s but was not found" % (rule.alt_lhs, rule.print(toString = True)))
                    logging.error("Please file a bug report regarding Pcolony.choseProgram()")
                    return False

                # remove one instance of rule.alt_lhs from obj
                # evolution and communication and exteroceptive need this part
                self.obj[rule.alt_lhs] -= 1;
                # 0 counts are allowed so if this is the case
                if (self.obj[rule.alt_lhs] == 0):
                    # remove the entry from the obj counter
                    del self.obj[rule.alt_lhs]
                
                if (rule.alt_type == RuleType.evolution):
                    # add the rule.alt_rhs object to obj
                    self.obj[rule.alt_rhs] += 1
                
                elif (rule.alt_type == RuleType.communication):
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

                elif (rule.alt_type == RuleType.exteroceptive):
                    # if the rule.alt_rhs object is not in the global swarm environement any more
                    if (self.colony.parentSwarm.global_env[rule.alt_rhs] <= 0):
                        # this is an error, some other agent modified the environement
                        logging.error("Object %s was required in the global swarm environement by rule %s but was not found" % (rule.alt_rhs, rule.print(toString = True)))
                        logging.error("Please check your rules and try again")
                        return False

                    # remove one instance of rule.alt_rhs from global swarm env only if it not 'e'
                    # 'e' object should remain constant in the environment
                    if (rule.alt_rhs != self.colony.e):
                        # remove one instance of rule.alt_rhs from global swarm env
                        self.colony.parentSwarm.global_env[rule.alt_rhs] -= 1;
                        # 0 counts are allowed so if this is the case
                        if (self.colony.parentSwarm.global_env[rule.alt_rhs] == 0):
                            # remove the entry from the env counter
                            del self.colony.parentSwarm.global_env[rule.alt_rhs]

                    # transfer object from environment to agent.obj
                    self.obj[rule.alt_rhs] += 1

                    # only modify the global swarm environment if the alt_lhs object is not e
                    if (rule.alt_lhs != self.colony.e):
                        # transfer object from agent.obj to environment
                        self.colony.parentSwarm.global_env[rule.alt_lhs] += 1
                #end elif rule.alt_type == RuleType.exteroceptive

                elif (rule.alt_type == RuleType.in_exteroceptive):
                    # if the rule.alt_rhs object is not in the INPUT global swarm environement any more
                    if (self.colony.parentSwarm.in_global_env[rule.alt_rhs] <= 0):
                        # this is an error, some other agent modified the environement
                        logging.error("Object %s was required in the INPUT global swarm environement by rule %s but was not found" % (rule.alt_rhs, rule.print(toString = True)))
                        logging.error("Please check your rules and try again")
                        return False

                    # remove one instance of rule.alt_rhs from INPUT global swarm env only if it not 'e'
                    # 'e' object should remain constant in the environment
                    if (rule.alt_rhs != self.colony.e):
                        # remove one instance of rule.alt_rhs from INPUT global swarm env
                        self.colony.parentSwarm.in_global_env[rule.alt_rhs] -= 1;
                        # 0 counts are allowed so if this is the case
                        if (self.colony.parentSwarm.in_global_env[rule.alt_rhs] == 0):
                            # remove the entry from the env counter
                            del self.colony.parentSwarm.in_global_env[rule.alt_rhs]

                    # transfer object from environment to agent.obj
                    self.obj[rule.alt_rhs] += 1

                    # only modify the INPUT global swarm environment if the alt_lhs object is not e
                    if (rule.alt_lhs != self.colony.e):
                        # transfer object from agent.obj to environment
                        self.colony.parentSwarm.in_global_env[rule.alt_lhs] += 1
                #end elif rule.alt_type == RuleType.in_exteroceptive

                elif (rule.alt_type == RuleType.out_exteroceptive):
                    # if the rule.alt_rhs object is not in the OUTPUT global swarm environement any more
                    if (self.colony.parentSwarm.out_global_env[rule.alt_rhs] <= 0):
                        # this is an error, some other agent modified the environement
                        logging.error("Object %s was required in the OUTPUT global swarm environement by rule %s but was not found" % (rule.alt_rhs, rule.print(toString = True)))
                        logging.error("Please check your rules and try again")
                        return False

                    # remove one instance of rule.alt_rhs from OUTPUT global swarm env only if it not 'e'
                    # 'e' object should remain constant in the environment
                    if (rule.alt_rhs != self.colony.e):
                        # remove one instance of rule.alt_rhs from OUTPUT global swarm env
                        self.colony.parentSwarm.out_global_env[rule.alt_rhs] -= 1;
                        # 0 counts are allowed so if this is the case
                        if (self.colony.parentSwarm.out_global_env[rule.alt_rhs] == 0):
                            # remove the entry from the env counter
                            del self.colony.parentSwarm.out_global_env[rule.alt_rhs]

                    # transfer object from environment to agent.obj
                    self.obj[rule.alt_rhs] += 1

                    # only modify the OUTPUT global swarm environment if the alt_lhs object is not e
                    if (rule.alt_lhs != self.colony.e):
                        # transfer object from agent.obj to environment
                        self.colony.parentSwarm.out_global_env[rule.alt_lhs] += 1
                #end elif rule.alt_type == RuleType.out_exteroceptive
            # end elif exec_rule_nr == second
        
        # rule execution finished succesfully
        return True
#end class Agent

class Program(list):

    """Program class used to encapsulate a list o rules."""

    def __init__(self):
        """Initialize the underling list used to store rules"""
        list.__init__(self)

    def getDeepCopyOf(self):
        """Returns a value copy of the Program, similar to a copy constructor in C++
        :returns: identical value-copy of this Program"""

        newProgram = Program()

        for rule in self:
            newProgram.append(rule.getDeepCopyOf())

        return newProgram
    # end getDeepCopyOf()

    def print(self, onlyExecutable = False):
        """

        :returns: TODO """

        result = ""

        for rule in self:
                result += rule.print(toString = True, onlyExecutable = onlyExecutable) + ", "

        # delete last comma ',' from the program printing
        result = result[:result.rfind(",")]

        return result
    # end print()

    def hasWildcards(self, card):
        """Returns true or false depending on whether this program contains rules that use the card wildcard (such as * or %id) or not
        :card: string representing a wildcard to check for
        :returns: True / False """

        for rule in self:
            if (rule.hasWildcards(card)):
                return True

        # no rule was found to contain wildcards
        return False
    # end hasWildcards()
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

    def getDeepCopyOf(self):
        """Returns a value copy of the Rule, similar to a copy constructor in C++
        :returns: identical value-copy of this Rule"""

        newRule = Rule()
        newRule.main_type = self.main_type
        newRule.exec_rule_nr = self.exec_rule_nr

        newRule.type = self.type
        newRule.lhs = self.lhs
        newRule.rhs = self.rhs

        newRule.alt_type = self.alt_type
        newRule.alt_lhs = self.alt_lhs
        newRule.alt_rhs = self.alt_rhs

        return newRule
    # end getDeepCopyOf()

    def print(self, indentSpaces = 2, onlyExecutable = False, toString = False) :
        """Print a rule with a given indentation level

        :indentSpaces: number of spaces used for indentation
        :onlyExecutable: print the rule only if it is marked as executable
        :toString: write to a string instead of stdout
        :returns: string print of the rule if toString = True otherwise returns "" """
        
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
                        result = "%s %s %s" % (self.alt_lhs, ruleNames[self.alt_type], self.alt_rhs)
                    else:
                        print(" " * indentSpaces + "%s %s %s" % (self.alt_lhs, ruleNames[self.alt_type], self.alt_rhs))
        
        return result
    # end print()

    def hasWildcards(self, card):
        """Returns true or false depending on whether this rule contains the card wildcard (such as * or %id) or not
        :card: string representing a wildcard to check for
        :returns: True / False """

        if ((card in self.lhs) or (card in self.rhs)):
            return True

        # check the alternative fields if this rule is conditional
        if (self.main_type == RuleType.conditional):
            if ((card in self.alt_lhs) or (card in self.alt_rhs)):
                return True

        # no wildcard has been found
        return False
    # end hasWildcards()
#end class Rule

##########################################################################

def processObjectListWildcards(objectList, suffixList, myId):
    """Replaces all * wildcards with n copies that each have appended one element from the provided suffixList and replaces %id wildcards with myId
    ex: objectList = [a, b, c_3, d_*, e_%id], suffixList=['0', '1', '2'], myId=5 => objectList = [a, b, c_3, e_5, d_0, d_1, d_2]

    :objectList: list of objects
    :suffixList: list of strings that are going to be appended to each object that has the * wildcard
    :myId: string used to replace '%id' wildcard
    :returns: the new list"""

    # we iterate over a copy of the object list (in order to modify it)
    for item in objectList[:]:
        if ('*' in item):
            # append the new items
            for suffix in suffixList:
                objectList.append(item.replace("*", suffix))

            # delete the item that contains the wildcards
            objectList.remove(item)

        if ('%id' in item):
            # replace the id wildcard with the id parameter
            objectList.append(item.replace("%id", myId))
            # delete the item that contains the '%id' wildcard
            objectList.remove(item)

    return objectList
# end processObjectListWildcard()

def processObjectCounterWildcards(objectCounter, suffixList, myId):
    """Replaces all * wildcards with n copies that each have appended one element from the provided suffixList and replaces %id wildcards with myId
    ex: objectCounter = [a, b, c_3, d_*, e_%id], suffixList=['0', '1', '2'], myId=5 => objectCounter = [a, b, c_3, e_5, d_0, d_1, d_2]

    :objectCounter: collections.Counter of objects
    :suffixList: list of strings that are going to be appended to each object that has the * wildcard
    :myId: string used to replace '%id' wildcard
    :returns: the new counter"""

    newCounter = collections.Counter()
    # we iterate over the original counter
    # and create a secondary counter with the new data
    # because we are not alowed to modify a dictionary during a loop
    for item in objectCounter:
        if ('*' in item):
            # add the new items to newCounter
            for suffix in suffixList:
                newCounter[item.replace("*", suffix)] = objectCounter[item]
        if ('%id' in item):
            newCounter[item.replace("%id", myId)] = objectCounter[item]
        else:
            # store the original (non wildcarded) item in the newCounter
            newCounter[item] = objectCounter[item]

    return newCounter
# end processObjectCounterWildcard()

def tokenize(code):
    """ generate a token list of input text
        adapted from https://docs.python.org/3/library/re.html#writing-a-tokenizer"""
    token_specification = [
        ('NUMBER',        r'\d+'),         # Integer number
        ('ASSIGN',        r'='),           # Assignment operator '='
        ('END',           r';'),           # Statement terminator ';'
        ('ID',            r'[\w\*\%]+'),   # Identifiers (allows * and % for use as wildcards)
        ('L_BRACE',       r'\('),          # Left brace '('
        ('R_BRACE',       r'\)'),          # Right brace ')'
        ('L_CURLY_BRACE', r'{'),           # Left curly brace '{'
        ('R_CURLY_BRACE', r'}'),           # Right curly brace '}'
        ('COLUMN',        r','),           # column ','

        #order counts here (the more complex rules go first)
        ('COMMUNICATION', r'<->'),         # Communication rule sign '<->'
        ('EXTEROCEPTIVE', r'<=>'),         # Exteroceptive rule sign '<=>'
        ('IN_EXTEROCEPTIVE',  r'<I=>'),    # In_Exteroceptive rule sign '<I=>'
        ('OUT_EXTEROCEPTIVE', r'<=O>'),    # Out_Exteroceptive rule sign '<=O>'
        ('EVOLUTION',     r'->'),          # Evolution rule sign '->'
        ('SMALLER',       r'<'),           # Smaller sign '<'
        ('LARGER',        r'>'),           # Larger sign '>'

        ('CHECK_SIGN',    r'/'),           # Checking rule separator '/'
        ('NEWLINE',       r'\n'),          # Line endings
        ('COMMENT',       r'#'),           # Comment (anything after #, up to the end of the line is discarded)
        ('SKIP',          r'[ \t]+'),      # Skip over spaces and tabs
        ('MISMATCH',      r'.'),           # Any other character
    ]
    # join all groups into one regex expr; ex:?P<NUMBER>\d+(\.\d*)?) | ...
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    line_num = 1
    line_start = 0
    in_comment = False
    # iteratively search and return each match (for any of the groups)
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup # last group name matched
        value = mo.group(kind) # the last matched string (for group kind)
        #print("kind = %s, value = %s" % (kind, value))
        if kind == 'COMMENT':
            in_comment = True
        elif kind == 'NEWLINE':
            line_start = mo.end()
            line_num += 1
            in_comment = False # reset in_comment state
        elif kind == 'SKIP':
            pass
        elif (kind == 'MISMATCH') and (not in_comment):
            raise RuntimeError('%r unexpected on line %d' % (value, line_num))
        else:
            # skip normal tokens if in comment (cleared at the end of the line)
            if in_comment:
                continue
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

        if (type(parent) == Pswarm):
            # process the following tokens as members of a Pcolony class
            logging.debug("processing as Pswarm")

            if (token.type == 'ASSIGN'):
                if (prev_token.value == 'global_env'):
                    logging.info("building list");
                    index, objects = process_tokens(tokens, list(), index + 1);
                    # make sure that 1 simbolic e object is in env
                    if ('e' not in objects):
                        objects.append('e')
                    result.global_env = collections.Counter(objects)

                elif (prev_token.value == 'in_global_env'):
                    logging.info("building list");
                    index, objects = process_tokens(tokens, list(), index + 1);
                    # make sure that 1 simbolic e object is in env
                    if ('e' not in objects):
                        objects.append('e')
                    result.in_global_env = collections.Counter(objects)

                elif (prev_token.value == 'out_global_env'):
                    logging.info("building list");
                    index, objects = process_tokens(tokens, list(), index + 1);
                    # make sure that 1 simbolic e object is in env
                    if ('e' not in objects):
                        objects.append('e')
                    result.out_global_env = collections.Counter(objects)

                if (prev_token.value == 'C'):
                    logging.info("building list");
                    index, result.C = process_tokens(tokens, result.C, index + 1);

                # if the previout token was an colony name found in C
                elif (prev_token.value in result.C): 
                    logging.debug("building colony")
                    index, colony = process_tokens(tokens, Pcolony(), index + 1);
                    colony.parentSwarm = result # store a reference to the parent swarm
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
                    elif (token.type == 'EXTEROCEPTIVE'):
                        rule.type = RuleType.exteroceptive
                    elif (token.type == 'IN_EXTEROCEPTIVE'):
                        rule.type = RuleType.in_exteroceptive
                    elif (token.type == 'OUT_EXTEROCEPTIVE'):
                        rule.type = RuleType.out_exteroceptive
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
                    elif (token.type == 'EXTEROCEPTIVE'):
                        rule.alt_type = RuleType.exteroceptive
                    elif (token.type == 'IN_EXTEROCEPTIVE'):
                        rule.alt_type = RuleType.in_exteroceptive
                    elif (token.type == 'OUT_EXTEROCEPTIVE'):
                        rule.alt_type = RuleType.out_exteroceptive
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

    if (logLevel <= logging.WARNING):
        print("\n\n");
        if (type(end_result) == Pswarm):
            end_result.print_swarm_components(printDetails=True)
        elif (type(end_result == Pcolony)):
            end_result.print_colony_components(printDetails=True)
        print("\n\n");

    return end_result
#end readInputFile()

def writeRulesHeader(path):
    """Write a rules.h file at the given path that contains all of the rule types that can be processed by lulu.

    :path: The path of the file that will be written (only filename without extension)
    :returns: TRUE / FALSE depending on the success of the operation"""

    logging.info("Generating rules C header in %s" % path + ".h")
    with open(path + ".h", "w") as fout:
        fout.write("""// vim:filetype=c
/**
 * @file lulu.h
 * @brief Lulu P colony simulator rule types
 * This header defines all of the rule types that are accepted by the simulator.
 * This file was auto-generated by lulu_pcol_sim --ruleheader rules.h on %s
 * @author Andrei G. Florea
 * @author Catalin Buiu
 * @date 2016-02-08
 */
#ifndef RULES_H
#define RULES_H

#include <stdint.h>
typedef enum _rule_type {
    //non-conditional (single rules)
    RULE_TYPE_NONE = 0,
            """ % time.strftime("%d %h %Y at %H:%M"));

        # concatenated string representation of any type of rule
        # used only in the C pcol sim for debug purposes
        ruleNamesString = ""

        # write non-conditional rules
        for rule in RuleType:
            if (rule == RuleType.conditional):
                continue
            fout.write("\n    RULE_TYPE_%s," % rule.name.upper());
            ruleNamesString += """[RULE_TYPE_%s] = "%s", """ % (rule.name.upper(), ruleNames[rule])

        # lookup tables are concatenated strings
        lookup1 = ""
        lookup2 = ""

        fout.write("\n    //conditional (pair of rules)");
        # write conditional rules
        for rule1 in RuleType:
            for rule2 in RuleType:
                if (rule1 == RuleType.conditional or rule2 == RuleType.conditional):
                    continue
                # append lookup tables
                lookup1 += "RULE_TYPE_%s, " % rule1.name.upper();
                lookup2 += "RULE_TYPE_%s, " % rule2.name.upper();

                # conditional rules start at 10
                if (rule1 == RuleType.evolution and rule2 == RuleType.evolution):
                    fout.write("\n    RULE_TYPE_CONDITIONAL_%s_%s = 10," % (rule1.name.upper(), rule2.name.upper()));
                else:
                    fout.write("\n    RULE_TYPE_CONDITIONAL_%s_%s," % (rule1.name.upper(), rule2.name.upper()));

        # finish rule_type_t typedef
        fout.write("\n} rule_type_t;");

        fout.write("\n\n// the tables are generated according to the order of the rules defined in rule_type_t");
        #fout.write("\nrule_type_t lookupFirst[] = {%s};" % lookup1);
        #fout.write("\nrule_type_t lookupSecond[] = {%s};" % lookup2);
        fout.write("\nextern rule_type_t lookupFirst[];");
        fout.write("\nextern rule_type_t lookupSecond[];");

        fout.write("""\n\n#ifdef PCOL_SIM
    extern char* ruleNames[];
#endif""")

        fout.write("\n\n#endif");
    #end with header fout

    logging.info("Generating rules C source in %s" % path + ".c")
    with open(path + ".c", "w") as fout:
        fout.write("""\n#include "%s.h" """ % path.split("/")[-1]);
        fout.write("\nrule_type_t lookupFirst[] = {%s};" % lookup1);
        fout.write("\nrule_type_t lookupSecond[] = {%s};" % lookup2);
        fout.write("""\n\n#ifdef PCOL_SIM
    char* ruleNames[] = {%s};
#endif""" % ruleNamesString)
# end writeRulesHeader()

##########################################################################
#   MAIN
if (__name__ == "__main__"):
    import sys # for argv

    if ('--debug' in sys.argv or '-v' in sys.argv):
        logLevel = logging.DEBUG
    elif ('--error' in sys.argv or '-v0' in sys.argv):
        logLevel = logging.ERROR

    try:
        import colorlog # colors log output

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

        colorlog.basicConfig(stream = sys.stdout, level = logLevel)
        stream = colorlog.root.handlers[0]
        stream.setFormatter(formatter);

    # colorlog not available
    except ImportError:
        logging.basicConfig(format='%(levelname)s:%(message)s', level = logLevel)

    if (len(sys.argv) < 2):
        logging.error("Expected input file path as parameter")
        exit(1)

    # step by step simulation
    step = False
    if ('--step' in sys.argv):
        step = True

    # header generation
    headerPath = None
    if ("--ruleheader" in sys.argv):
        if (len(sys.argv) < 3):
            logging.error("Expected the path to the C header file that should be generated")
            exit(1)
        else:
            headerPath = sys.argv[sys.argv.index("--ruleheader") + 1];
            writeRulesHeader(headerPath);
            logging.info("Exiting after header generation")
            exit(0);

    end_result = readInputFile(sys.argv[1])

    end_result.simulate(stepByStepConfirm = step)

    print("\n\n");
