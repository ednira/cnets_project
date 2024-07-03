import pandas as pd

from flt_bindings import *


def activity_total(log):
   """Calculate total activity counts and store them in a dictionary. A total activity count is how many times an activity occurs"""
   
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

   def calculate_dependency(pair):
      a, b = pair
      if b == a:
         return freq.loc[a,b]/(freq.loc[a,b] + 1)
      else:
         return (freq.loc[a,b] - freq.loc[b,a])/(freq.loc[a,b] + freq.loc[b,a] + 1)
                  
   
   dependency_matrix = pd.DataFrame(index=freq.index, columns=freq.columns)

   for col in freq.columns:
      for index in freq.index:
         dependency_matrix.loc[index,col] = calculate_dependency((index,col))

   return dependency_matrix


def dependency_dict(dependency_matrix):
   """Convert a dependency matrix Dataframe into a dictionary"""
   
   dependency_dict = dependency_matrix.to_dict('index')

   return dependency_dict



def original_start(act_total, activity_freq):
   """
   Identify the start activity(ies) in the log based on the inbindings of each activity
   """
   incoming = in_bindings(activity_freq)
   original_start = list()

   for act in act_total.keys():
      if act not in incoming.keys() and act not in original_start:
         original_start.append(act)

   return original_start



def original_end(act_total, activity_freq):
   """
   Identify the end activity(ies) in the log based on the outbindings of each activity
   """
   outgoing = out_bindings(activity_freq)
   original_end = list()

   for act in act_total.keys():
      if len(outgoing[act]) == 0 and act not in original_end:
         original_end.append(act)
   
   return original_end