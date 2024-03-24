import os
from collections import OrderedDict


def read_log(path):
   """Read a csv log and save it to a dictionary with events sorted by timestamp."""
   f = open(path, 'r')

   log = dict() 

   for line in f:
      line = line.strip()
      if len(line) == 0:
         continue
      parts = line.split(';')
      caseID = parts[0]
      task = parts[1]
      user = parts[2]
      timestamp = parts[3]

      if caseID not in log:
         log[caseID] = []
      event = (task, user, timestamp)
      log[caseID].append(event)

   for caseID in sorted(log.keys()):
      log[caseID].sort(key = lambda event: event[-1])

   f.close()

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