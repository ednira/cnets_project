import pandas as pd

import pm4py

from subgraphs_dict import *
from vis_layer import *
from flatten_log import *


##############################   SOFTWARE USED   ##################################

# The tools used in this study to implement the algorithms, the visualization, and the evaluation are introduced as follows.

# • Visual Studio Code – Version: 1.91.1 (Universal), Commit: f1e16e1e6214d7c44d078b1f0607b2388f29d729, Date: 2024-07-09T22:07:54.982Z, Electron: 29.4.0, ElectronBuildId: 9728852, Chromium: 122.0.6261.156, Node.js: 20.9.0, V8: 12.2.281.27-electron.0, OS: Darwin arm64 23.5.0
# • Python 3.11.0 64-bit
# • PM4PY – Version: 2.7.11.3
# • Pandas – Version: 2.1.4
# • Numpy – Version: 1.26.2
# • Graphviz – Version: 0.20.1, Home-page: https://github.com/xflr6/graphviz, Author: Sebastian Bank, Author-email: sebastian.bank@uni-leipzig.de, License: MIT
# • Matplotlib – Version: 3.8.2
# • Seaborn – Version: 0.13.2


####################################  INSTRUCTIONS  #######################################


###### STEP 1: PROVIDE THE PATH OF THE OCEL LOG FILE TO BE USED

# Below are some examples of logs from the OCEL documentation site
# To use other logs, substitute the path in the variable 'path'
""" 
# ORDERMGMT
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/OCEL_OrderMgt/order-management.sqlite"
# path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/order-management.json" 
""" 

""" # LOGISTICS
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/OCEL_Logistics/ContainerLogistics.sqlite"
# path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/ContainerLogistics.sqlite"
""" 

""" # P2P
# path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/ocel2-p2p.sqlite"
"""

# CargoPickup
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/CargoPickup.sqlite"


###### STEP 2: SELECT THE OBJECT TYPES TO BE INCLUDED IN THE MODEL, USING THE VARIABLE 'PROFILE'

# For each log, the possible selected object types:

# ORDERMGMT OT: ['employees', 'customers', 'orders', 'items', 'products', 'packages']
# LOGISTICS OT: ['Customer Order', 'Transport Document', 'Vehicle', 'Container', 'Handling Unit', 'Truck', 'Forklift']
# P2P OT: ['purchase_requisition', 'quotation', 'purchase_order', 'goods receipt', 'invoice receipt', 'payment', 'material']

# CARGO PICK-UP: ['Truck', 'Pickup Plan', 'Cargo']

profile = ['Truck', 'Pickup Plan', 'Cargo']





###### STEP 3: RUN THE CODE TO DISCOVER THE MODEL

ocel, ot_activities, event_to_obj, obj_to_obj = import_log(path)

ot1_ot2_cardinalities, ot2_ot1_cardinalities = ot_cardinalities(obj_to_obj, event_to_obj, ot_activities) 

ot_seq = ot_sequence(ot_activities, ot1_ot2_cardinalities, ot2_ot1_cardinalities, event_to_obj)

subgraphs = subgraphs_dict(path) 

OCCN_model = all_ot_visualization(ot_activities, ot_seq, subgraphs, profile)