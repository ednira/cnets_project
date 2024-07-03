import pandas as pd

from flt_import_ocel import *

""" 
# ORDERMGMT
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/OCEL_OrderMgt/order-management.sqlite"
path_complete = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/order-management.json" 
 """

""" 
# LOGISTICS
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/OCEL_Logistics/ContainerLogistics.sqlite"
path_complete = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/ContainerLogistics.sqlite" 

 """

# P2P
path = "/Users/ednira/Documents/My_Masters/0_THESIS/event_logs/OCEL2.0/Complete logs/ocel2-p2p.sqlite"


ocel_df, ot_activities, activity_to_object_types, obj_to_obj, event_to_obj = import_log(path)
# Sample data
data = event_to_obj

ot_same_obj_qty = []

for o_type1 in ot_activities.keys():
    for o_type2 in ot_activities.keys():
        if o_type1 != o_type2:
            # Group by event and activity, then count object types
            grouped = data.groupby(['ocel:eid', 'ocel:activity', 'ocel:type']).size().unstack(fill_value=0)
            # Check if the counts of OT1 and OT2 are the same for each activity
            compare_obj_qty = grouped.apply(lambda x: x[o_type1] == x[o_type2], axis=1)
            # Check if all values in the comparison are True
            all_true = compare_obj_qty.all()
            # Add tuple of OT1 and OT2 to list of OT with the same number of objects in all activities
            if all_true:
                if (o_type1,o_type2) not in ot_same_obj_qty and (o_type2,o_type1) not in ot_same_obj_qty:
                    ot_same_obj_qty.append((o_type1,o_type2))

print(ot_same_obj_qty)
