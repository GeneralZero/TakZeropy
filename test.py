import timeit
import numpy as np
import math
from generate_move_arrays import generate_move_arrays

if __name__ == '__main__':
	print("Main2:", timeit.timeit("math.pow(2, 1.0/300)", globals=globals()))
	print("Main3:", timeit.timeit("2 ** (1.0/300)", globals=globals()))
	print(2 ** (1.0/300))
	print(math.pow(2, 1.0/300))

