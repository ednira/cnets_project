import os
from collections import OrderedDict
import csv


def read_log(path):
   """Read a csv log and save it to a dictionary with events sorted by timestamp."""
   log = dict() 

   with open(path, 'r', newline='') as csvfile:
      reader = csv.DictReader(csvfile)

      for row in reader:
         case_col = next((col for col in reader.fieldnames if col.lower() == 'case:concept:name'), None)
         task_col = next((col for col in reader.fieldnames if col.lower() == 'concept:name'), None)
         user_col = next((col for col in reader.fieldnames if col.lower() == 'user'), None)
         time_col = next((col for col in reader.fieldnames if 'timestamp' in col.lower()), None)

         caseID = row.get(case_col)
         task = row.get(task_col)
         user = row.get(user_col)
         timestamp = row.get(time_col)

         if caseID not in log:
            log[caseID] = []
         event = (task, user, timestamp)
         log[caseID].append(event)

      for caseID in sorted(log.keys()):
         log[caseID].sort(key = lambda event: event[-1])

   return log



def traces(log):
   """Return dictionary with traces of a log
   Key is CaseID and value is the trace"""

   traces = {}
   tasks = list()

   for caseID in log:
      if caseID not in traces:
         traces[caseID] = list()
      events = log[caseID]
      for event in events:
         tasks.append(event[0])
      traces[caseID] = tasks
      tasks = []
      
   return traces

def traces_list(log):
   """Return list with traces of a log"""

   traces = list()
   tasks = list()

   for caseID in log:
      events = log[caseID]
      for event in events:
         tasks.append(event[0])
      traces.append(tasks)
      tasks = []
      
   return traces


def top_traces (traces):
   """Take a dictionary of traces and return dictionary with trace as key and trace count in log as value
   Ordered from highest to lowest counts
   """
   tracelist = []
   trace_counts = {}

   for trace in traces:
      trace = tuple(traces[trace])
      tracelist.append(trace)

   for trace in tracelist:
      count = tracelist.count(trace)
      if trace not in trace_counts.keys():
         trace_counts[trace] = {}
      trace_counts[trace] = count
      

   highest_traces = OrderedDict(sorted(trace_counts.items(), key=lambda t: t[1], reverse=True))

   return highest_traces