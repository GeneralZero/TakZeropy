import multiprocessing, timeit
import setuptools
import pyximport; pyximport.install()
from MonteCarlo import UCTPlayGame, save

if __name__ == '__main__':
	save(UCTPlayGame(10))
	#pool = multiprocessing.Pool(processes=7)
	#for x in range(50000):
	#	pool.apply_async(UCTPlayGame, args=(10,), callback=save)
	#	game_index += 1
	#pool.close()
	#pool.join()