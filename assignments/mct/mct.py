import random
import pandas as pd
import os
import pickle
import networkx as nx
import numpy as np

os.chdir('/work/netsi/ueda.m/network-science-data/assignments/assignment3')

# ====================
# Usage
# ====================
# python mct.py --graph_type "ER" --niter 2000 --items_per_task 1500


# ====================
# Arguments
# ====================

import argparse

parser = argparse.ArgumentParser(description="")
parser.add_argument("--graph_type", type=str,help="Type of graph (ER or BA)")
parser.add_argument("--niter", type=int, default=10, help="Number of iteration")
parser.add_argument("--items_per_task", type=int, default=100, help="Items per task")
args = parser.parse_args()

graph_type = args.graph_type
niter = args.niter
items_per_task = args.items_per_task


# ====================
# Data
# ====================
def read_pickle(file_path):
    """
    Reads an object from a pickle file.

    Parameters:
        file_path:
            Path to the pickle file.

    Returns:
        obj:
            The object read from the pickle file.
    """
    with open(file_path, 'rb') as f:
        obj = pickle.load(f)
    return obj

if graph_type == "ER":
    Gs = read_pickle("out/G_ERs_LCC.pkl")
    neighbors_dicts = read_pickle("out/neighbors_dict_ER.pkl")
    df_pairs = pd.read_csv("out/all_pairs_dicts_ER.csv")
else:
    Gs = read_pickle("out/G_BAs_LCC.pkl")
    neighbors_dicts = read_pickle("out/neighbors_dict_BA.pkl")
    df_pairs = pd.read_csv("out/all_pairs_dicts_BA.csv")

# Convert to array
graph_ids, i_list, j_list = df_pairs.values.T


# ====================
# Range
# ====================

def get_task_range(task_id, total_items, items_per_task):
    start_index = task_id * items_per_task
    end_index = min(start_index + items_per_task, total_items)
    return start_index, end_index

task_id = int(os.getenv("SLURM_ARRAY_TASK_ID", 0))
start_index, end_index = get_task_range(task_id, len(df_pairs), items_per_task)

# ====================
# Calculation logic
# ====================
def first_passage_time_between_nodes(G, i, j, neighbors_dict=None):
    """
    Computes the first passage time m_{ij} between two nodes in a graph.

    The first passage time is the number of steps required for a random walker 
    to move from node i to node j for the first time.

    Parameters
        i : node
            The starting node for the random walk.
        j : node
            The target node for the random walk.

    Returns
        first_passage_time : int
            The number of steps required for the walker to move from node i to node j.
    """
    # Initialize the starting node and the current node
    source = i
    current_node = i
    t = 0  # Initialize the step count
    
    # Continue walking until the target node is reached
    while current_node != j:

        if neighbors_dict is None:
            # Get the neighbors of the current node
            neighbors = list(G.neighbors(current_node))
        else:
            neighbors = neighbors_dict[current_node]
        
        # Choose a random neighbor and move there
        target = random.choice(neighbors)
        current_node = target  # Update the current node
        t += 1                 # Increment the step count
    
    return t  # Return the first passage time between the two nodes
def mean_first_passage_time(G, i, j, niter=100, neighbors_dict=None):

    fpt_array = []
    for t in range(niter):
        fpt = first_passage_time_between_nodes(G, i, j, neighbors_dict=neighbors_dict)
        fpt_array.append(fpt)

    return np.mean(fpt_array)
def mean_commute_time(G, i, j, niter=100, neighbors_dict=None):
    m_ij = mean_first_passage_time(G, i, j, niter=niter, neighbors_dict=neighbors_dict)
    m_ji = mean_first_passage_time(G, j, i, niter=niter, neighbors_dict=neighbors_dict)

    return np.sum([m_ij, m_ji])

# ====================
# Calculation loop
# ====================
result = []
for idx in range(start_index, end_index):

    graph_id = graph_ids[idx]
    i = i_list[idx]
    j = j_list[idx]

    G = Gs[graph_id]
    neighbors_dict = neighbors_dicts[graph_id]

    mct = mean_commute_time(G, i, j, niter=niter, neighbors_dict=neighbors_dict)
    result.append( [graph_id, i, j, mct] )

pd.DataFrame(result).to_csv(f"out/slurm/mct_{graph_type}_{niter}it_{task_id}.csv", index=False, header=False)