
from discover_occnets import *
from view_occnets import *


# ORDERMGMT
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/OCEL_OrderMgt/order-management.sqlite"
# path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/order-management.json" 



# LOGISTICS
# path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/OCEL_Logistics/ContainerLogistics.sqlite"
# path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/ContainerLogistics.sqlite" 



# P2P
# path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/ocel2-p2p.sqlite"

""" # Cargo (Amin's file)
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/CargoPickup.sqlite" 
"""

####################### This section allows OC-DFG and OCPN discovery ###########################

# ocel = pm4py.read_ocel2_sqlite(path)
# ocpn = pm4py.ocel.discover_oc_petri_net(ocel)
# # ocdfg = pm4py.ocel.discover_ocdfg(ocel)

# pm4py.view_ocpn(ocpn, format='svg', rankdir='TB')
# pm4py.view_ocdfg(ocdfg, format='svg', rankdir='TB')

####################### This section allows OCCN discovery ###########################

# FIRST, select a profile:

# For each log, the possible selected object types:

# ORDERMGMT OT: ['employees', 'customers', 'orders', 'items', 'products', 'packages']
# LOGISTICS OT: ['Customer Order', 'Transport Document', 'Vehicle', 'Container', 'Handling Unit', 'Truck', 'Forklift']
# P2P OT: ['purchase_requisition', 'quotation', 'purchase_order', 'goods receipt', 'invoice receipt', 'payment', 'material']
# Cargo OT: ['Truck', 'Cargo', 'Pickup Plan']
profile = ['customers', 'orders', 'items', 'packages']



# SECOND, RUN THE CODE TO DISCOVER THE MODEL:

ot_activities, ot_seq, subgraphs = subgraphs_dict(path) 

# FINALLY, RUN THE CODE TO VIEW THE MODEL:

OCCN_model = all_ot_visualization(ot_activities, ot_seq, subgraphs, profile=profile)