import networkx as nx
import math
import pickle

n = 50  # Number of nodes
p = 0.2 # Initial connection probability
nu = 2/math.comb(n, 2) # Edge flip probability

G_FCS_original = nx.erdos_renyi_graph(n, p)

with open(f'out/graph_initial_{n}.pkl', 'wb') as f:
    pickle.dump(G_FCS_original, f)