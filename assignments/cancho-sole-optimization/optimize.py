import numpy as np
import networkx as nx
import math
import os
import pickle

# ==== MODEL PARAMETERS ====
n = 50  # Number of nodes
p = 0.2 # Initial connection probability
nu = 2/math.comb(n, 2) # Edge flip probability
max_rejections = min(500, math.comb(n, 2)) # Stopping criterion
num_iterations = 50 # Number of iterations for each lambda

lambdas = [i / 100 for i in range(0, 100+1, 5)] # 0 to 1 in 0.05 increments
lam_iterations = np.array([[lam] * num_iterations for lam in lambdas]).reshape(-1).tolist()


# ==== JOB PARAMETERS====
num_array = int(os.getenv("SLURM_ARRAY_TASK_COUNT", 50))
tasks_per_array = int(np.ceil(len(lam_iterations) / num_array)) # One job array will process this many tasks with for loop

slurm_array_task_id = int(os.getenv("SLURM_ARRAY_TASK_ID", 1))

# Calculate the start and end index for the current job array
start_idx = (slurm_array_task_id - 1) * tasks_per_array
end_idx = min(start_idx + tasks_per_array, len(lam_iterations))

# Helper function to calculate normalized number of links (ρ)
def calculate_rho(G, n=None):
    """
    Calculate normalized number of links rho. This is equivalent to network density.

    rho = ( 1 / (nC2) ) * sum_{i<j} a_{ij}
        = (langle k rangle) / (n-1)
    
    Parameters
    ----------
        G : networkx.Graph
            Input graph.
        n: int, optional
            Number of nodes in the graph (default is None). If None, it will be calculated from the graph.
    
    Returns
    ----------
        rho : float
            Normalized vertex-vertex distance d.
    """

    # Calculate number of node if not provided
    if n is None:
        n = G.number_of_nodes()
    
    num_links = G.number_of_edges()
    max_links = n * (n - 1) / 2

    rho = num_links / max_links

    return rho

def calculate_d(G, n=None):
    """
    Calculate the normalized vertex-vertex distance (d) for a graph. This is calculated from following formula:
    d = D / D_linear
    where
    - D is the average minimum distance between nodes
        D = (1 / nC2 ) * sum_{i<j} D_{ij}
    - D_{ij} is the shortest path length between nodes i and j
    - D_linear is the maximum value of D that can be achieved by a connected network
        D_linear = (n + 1) / 3

    Parameters
    ----------
        G : networkx.Graph
            Input graph.
        n: int, optional
            Number of nodes in the graph (default is None). If None, it will be calculated from the graph.
    
    Returns
    ----------
        d : float
            Normalized vertex-vertex distance d.
    """

    from itertools import combinations

    if n is None:
        n = G.number_of_nodes()

    # Calculate D (average minimum distance between nodes)
    if nx.is_connected(G):

        # D_ij for all node pairs
        distances = dict(nx.all_pairs_shortest_path_length(G))

        total_distance = 0
        num_pairs = 0 # This is equal to nC2 (all possible pairs)

        for u, v in combinations(G.nodes, 2):
            total_distance += distances[u][v]
            num_pairs += 1

        D = total_distance / num_pairs
    else:
        # If the graph is disconnected, D is infinite
        return float('inf')

    # Calculate D_linear (max possible D)
    D_linear = (n + 1) / 3

    # Calculate normalized distance d
    d = D / D_linear

    return d

def calculate_energy_from_graph(G, lam):
    """
    Calculate the energy from a graph, given lambda.

    Parameters
    ----------
        G : networkx.Graph
            The input graph for which the energy is to be calculated.
        lam : float
            Lambda parameter controlling the tradeoff between distance and density.


    Returns
    -------
        energy: float
            The calculated energy value based on the input graph and parameters.
    """

    d = calculate_d(G)
    rho = calculate_rho(G)
    energy = ((lam * d) + ((1 - lam) * rho))
    return energy
def calculate_energy_from_d(lam, d, rho):
    """
    Calculate the energy from a graph based on given parameters.

    Parameters
    ----------
        lam : float
            Lambda parameter controlling the tradeoff between distance and density.
        d : float
            The normalized vertex-vertex distance of the graph.
        rho : float
            A parameter that represents an additional factor in the energy calculation.

    Returns
    -------
        energy: float
            The calculated energy value based on the input graph and parameters.
    """
    energy = ((lam * d) + ((1 - lam) * rho))
    return energy

def calculate_degree_entropy(G):
    """
    Calculate the degree entropy of a graph.
    
    Parameters
    ----------
        G : networkx.Graph
            Input graph to calculate degree entropy
    
    Returns
    -------
        entropy : float
            Degree entropy H({p_k}).
    """
    
    # Get degree distribution
    degrees = list(dict(G.degree()).values())

    # Calculate the frequency of each degree
    from collections import Counter

    degree_counts = Counter(degrees)
    
    # Calculate probability for degree distribution
    total_nodes = G.number_of_nodes()
    p_k = np.array(list(degree_counts.values())) / total_nodes
    
    # Extract p_k > 0 since log(0) is undefined
    nonzero_p_k = p_k[p_k > 0]

    # Calculate entropy
    entropy = -np.sum( nonzero_p_k * np.log(nonzero_p_k) )

    return entropy

def ferrer_cancho_sole_optimization(lam, nu, max_rejections, n=None, p=None, G=None):
    """
    Optimize a graph using the Ferrer i Cancho and Solé model.
    
    Parameters
    -------
        lam : float
            Lambda parameter controlling the tradeoff between distance and density.
        nu : float
            Probability of flipping an edge during each iteration.
        max_rejections : int
            Maximum number of consecutive rejections before stopping.
        n : int
            Number of nodes in the graph. Used to generate initial ER graph (Required if G is not provided).
        p : float
            Initial connection probability for the random graph. Used to generate initial ER graph (Required if G is not provided).
        G : networkx.Graph, optional
            Initial graph to optimize. You can either pass pre-generated G or and n and p pairs to generate a random graph inside this function.

    Returns
    -------
        optimized_G : networkx.Graph
            Optimized graph.
        interations : int
            Number of iterations until reaching the maximum number of rejections.
    """

    # Generate the initial ER graph
    # Initial graph follows a Poisson degree distribution
    if G is None:
        G = nx.erdos_renyi_graph(n, p)

    # Step 2: Calculate initial energy
    rho = calculate_rho(G)
    # print(f'initial rho: {rho}')
    d = calculate_d(G)
    energy = calculate_energy_from_d(lam=lam, d=d, rho=rho)

    # Step 3: Simulated annealing optimization
    consecutive_rejections = 0

    # pbar = tqdm(total=10000000)
    iterations = 0

    # Repeat until consecutive rejections reach the maximum
    while consecutive_rejections < max_rejections:
        # pbar.update()

        # Create a modified copy of the graph by flipping edges with probability ν
        modified_G = G.copy()

        # Add or remove edges with probability "nu"
        for u, v in nx.non_edges(G):
            if np.random.rand() < nu:
                modified_G.add_edge(u, v)
        for u, v in list(G.edges):
            if np.random.rand() < nu:
                modified_G.remove_edge(u, v)

        # Calculate new energy
        new_rho = calculate_rho(modified_G, n)
        new_d = calculate_d(modified_G, n)
        new_energy = calculate_energy_from_d(lam=lam, d=new_d, rho=new_rho)

        # Accept the new graph if energy is lower than the current energy
        if new_energy < energy:
            G = modified_G
            energy = new_energy
            consecutive_rejections = 0
        else:
            consecutive_rejections += 1

        iterations += 1
    
    optimized_G = G

    return optimized_G, iterations


# Load initial graph
with open(f'out/graph_initial_{n}.pkl', 'rb') as f:
    G_init = pickle.load(f)

# Run optimization for each lambda within the job array
for task_id in range(start_idx, end_idx):
    lam = lam_iterations[task_id]
    iteration = task_id % num_iterations + 1

    optimized_G, it = ferrer_cancho_sole_optimization(
        lam=lam,
        nu=nu,
        max_rejections=max_rejections,
        G=G_init
    )

    lam_txt = f'{lam:.2f}'

    # Save optimized G
    output_dir = f'out/n_{n}/optimized_G/{lam_txt}/'
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f'{task_id}.pkl')
    with open(output_path, 'wb') as f:
        pickle.dump(optimized_G, f)

    # Save iteration count
    output_dir = f'out/n_{n}/iter/{lam_txt}'
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f'{task_id}.txt')
    with open(output_path, 'w') as f:
        f.write(str(it) + '\n')