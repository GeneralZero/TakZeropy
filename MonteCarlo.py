import random, h5py, os, multiprocessing
import numpy as np
from board import TakBoard
from time import time
import hashlib
from Node import UCTNode
#np.set_printoptions(threshold=np.nan)

class UCTTakGame():
	"""docstring for UCTGame"""
	def __init__(self, ittermult=100):
		self.ittermult = ittermult
		self.verbose = False

		self.game = TakBoard(5)
		self.rootnode = UCTNode(state = self.game)
		self.childNodes = None

	def main(self):
		train_data = []
		
		while (self.game.white_win == False and self.game.black_win == False):
			start_time = time()
			self.childNodes = self.search()

			m =  self.choose_move()
			print("Random Move: {}, Trys: {}, took {:.6f}s".format(m.move, m.visits, time() - start_time), flush=True)

			np_state = self.game.get_numpy_board()
			addition = np.full(1576, 0, dtype=int)
			for moves in self.childNodes:
				addition[moves.move["index"]] = moves.visits
			addition[1575] = self.rootnode.visits
			#print(winrate)

			train_data.append({"probs":addition, "state":np_state})

			self.game.exec_move(m.move)
			self.change_root_node(m)


		if self.game.white_win == True:
			print("White Player wins!", flush=True)
			train_data.append(True)
		elif self.game.black_win == True:
			print("Black Player wins!", flush=True)
			train_data.append(False)
		else:
			print("Nobody wins!", flush=True)

		return train_data

	def change_root_node(self, childNode):
		#count = 0
		#for node in self.childNodes:
		#	count += node.visits 
		#print("Visits",count)
		self.rootnode = childNode

	def choose_move(self, randomChoice=True):
		return self.childNodes[-1]


	def search(self):
		itter = self.ittermult * (len(self.rootnode.untriedMoves) + len(self.rootnode.childNodes))
		#print(itter)
		for i in range(itter):
			self.rollout(self.game.clone(), self.rootnode)

		#print(self.rootnode.childNodes[0].visits, self.rootnode.visits)
		return sorted(self.rootnode.childNodes, key = lambda c: (c.visits, c.wins))

	def rollout(self, state, node):
		player1_turn = state.player1_turn

		# Select
		while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
			node = node.UCTSelectChild()
			state.exec_move(node.move)

		# Expand
		count = len(node.untriedMoves)
		gamma = np.random.gamma(0.03, 1.0, count)
		gamma = gamma / np.sum(gamma)
		idx = 0
		#print(count)

		if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
			m = random.choice(node.untriedMoves)
			state.exec_move(m)
			##TODO change actual probability to learned probability
			prob = 1.0/count * (1 - 0.25) + 0.25 * gamma[idx%count]
			idx += 1
			node = node.AddChild(m,state, prob) # add child and descend tree


		# Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
		while (state.white_win == False and state.black_win == False): # while state is non-terminal
			state.exec_move(random.choice(state.get_plays()))

		# Backpropagate
		while node != None: # backpropagate from the expanded node and work back to the root node
			#print(state.white_win - state.black_win)
			if player1_turn == True:
				node.Update(state.white_win) # state is terminal. Update node with result from POV of node.playerJustMoved
			else:
				node.Update(state.black_win)
			node = node.parentNode
	

def save(training_data):
	#print(training_data)
	winner = training_data[-1]
	training_data = training_data[:-1]

	with h5py.File(os.path.join(os.getcwd(), "best_10", "Game_{}.hdf5".format(hashlib.md5(repr(training_data).encode('utf-8')).hexdigest())), 'w') as hf:
		print("Game has {} moves".format(len(training_data)), flush=True)
		for index, gamedata in enumerate(training_data):
			hf.create_dataset("state_{}".format(index), data=gamedata["state"], compression="gzip", compression_opts=9)
			hf.create_dataset("probs_{}".format(index), data=gamedata["probs"], compression="gzip", compression_opts=9)

		hf.create_dataset("white_win", data=np.array([winner]), compression="gzip", compression_opts=9)

if __name__ == "__main__":
	#p = UCTTakGame(1)
	#save(p.main())
	pool = multiprocessing.Pool(processes=7)
	for x in range(50000):
		p = UCTTakGame(10)
		#save(p.main())
		pool.apply_async(p.main, callback=save)
	pool.close()
	pool.join()
