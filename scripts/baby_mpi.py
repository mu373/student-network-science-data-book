from mpi4py import MPI

rank = MPI.COMM_WORLD.Get_rank()
n_ranks = MPI.COMM_WORLD.Get_size()

print("Hello World! I'm rank", rank);
print("Total no. of ranks =", n_ranks);