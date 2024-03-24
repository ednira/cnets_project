import pandas as pd
import numpy as np 
from import_log import read_log
import os


def activity_total(log):
   """Calculate total activity counts and store them in a dictionary. A total activity counts is how many times an activity happened"""
   
   act_total = dict()
   
   for caseID in log:
      for i in range(0, len(log[caseID])):
         ai = log[caseID] [i] [0]
         if ai not in act_total:
            act_total[ai] = 0
         act_total[ai] += 1

   return act_total



def activity_frequencies(log):
   """Calculate frequencies of activity ai followed by activity aj and store them in a dictionary"""
   
   act_frequencies = dict()

   for caseID in log:
      for i in range(0, len(log[caseID])-1): 
         ai = log[caseID] [i] [0]
         aj = log[caseID] [i+1] [0]
         if ai not in act_frequencies:
            act_frequencies[ai] = dict()
         if aj not in act_frequencies[ai]:
            act_frequencies[ai][aj] = 0
         act_frequencies[ai][aj] += 1
         if aj not in act_frequencies:
            act_frequencies[aj] = dict()
   

   for key in act_frequencies:
      if key not in act_frequencies[key]:
         act_frequencies[key][key] = 0
   
   return act_frequencies


def frequencies(act_frequencies):
   """Convert the activity frequencies dictionary into a dataframe in pandas with frequencies"""

   frequencies = pd.DataFrame.from_dict(act_frequencies, orient='index')
   frequencies = frequencies.fillna(0)
   
   return frequencies


def follows_direct(x):
   """Check if the given number of a dataframe cell is zero"""
   if x == 0:
      return 0
   return 1


def adjacency_matrix(frequencies):
   """Create the adjacency matrix as a Datraframe based on the activity frequencies"""
   frequencies = frequencies
   adjacency_matrix = pd.DataFrame(frequencies.applymap(lambda x: follows_direct(x)))

   return adjacency_matrix


def dependency_matrix(frequencies):
   """Generate the dependency matrix Dataframe"""

   freq = frequencies

   dependencies = {}

   for key in freq:
      dependencies[key] = {}
      for value in freq.keys(): 
         dependencies[key][value] = {}
         if value == key:
               dependencies[key][value] = freq[key][value]/(freq[key][value]+1)
         else:
               dependencies[key][value] = (freq[key][value] - freq[value][key])/(freq[key][value] + freq[value][key] + 1)
   
   dependency_matrix = pd.DataFrame.from_dict(dependencies)
   
   return dependency_matrix


def dependency_dict(dependency_matrix):
   """Convert a dependency matrix Dataframe into a dictionary"""
   
   dependency_dict = dependency_matrix.to_dict('index')

   return dependency_dict


def find_long_distance(lst, a, b):
   """Count successor activity occurrences"""
   pairs_count = 0
   last_a_index = None
   min_distance = 2

   for i, element in enumerate(lst):
      if element == a:
         last_a_index = i
      elif element == b and last_a_index is not None and i - last_a_index >= min_distance:
         pairs_count += 1

   return pairs_count


def long_distance_dependency(act_total, traces):
   """Calculate if one activity eventually follows another one"""
   act_total_list = list()
   
   successors_list = dict()
   long_dep = dict()

   counter = 0
   sum = 0
   
   for key in act_total:
      act_total_list.append(key)

   for activity in act_total_list:
      if activity not in successors_list:
         successors_list[activity] = dict()
      successors = [e for i, e in enumerate(act_total_list) if e != activity] 
      for successor in successors:
         for trace in traces.values():
            counter += find_long_distance(trace, activity, successor)
         sum += counter
         successors_list[activity][successor] = sum
         counter = 0
         sum = 0
   
   for activity in successors_list:
      long_dep[activity] = dict()
      for successor in successors_list[activity]:
         if successors_list[activity][successor] > 0:
            long_dep[activity][successor] = ((2*successors_list[activity][successor])/(act_total[activity]+act_total[successor]+1)) - ((2*abs(act_total[activity]-act_total[successor])/(act_total[activity]+act_total[successor]+1)))
         else:
            long_dep[activity][successor] = 0
   
   return long_dep