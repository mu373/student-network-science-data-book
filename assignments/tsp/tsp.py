import networkx as nx
# import numpy as np
import acopy
import time
import pickle
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--jobid', required=True, help='The job ID')
    parser.add_argument('--data', required=True, help='The data to process')
    
    args = parser.parse_args()

file_name = "{}.gml".format(args.data)
job_id = args.jobid

G = nx.read_gml('data/tsp2/{}'.format(file_name))


solver = acopy.Solver(rho=0.03, q=1)
colony = acopy.Colony(alpha=1, beta=3)

start_time = time.time()
N = G.number_of_nodes()
tour = solver.solve(G, colony, limit=100, gen_size=int(0.01*N))
result = "foo"
end_time = time.time()
elapsed_time = end_time - start_time

result = {"time": elapsed_time, "acopy_solution": tour}

with open('out/{}_job{}.pkl'.format(args.data, job_id), 'wb') as f:
    pickle.dump(result, f)
