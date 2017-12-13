import random, h5py, os
import numpy as np
from board import TakBoard
from time import time
import hashlib, requests
from Node import UCTNode
from train import TakZeroNetwork
#np.set_printoptions(threshold=np.nan)

class UCTTakGame():
	"""docstring for UCTGame"""
	def __init__(self, ai, ittermult=100):
		self.ittermult = ittermult
		self.verbose = False
		self.ai = ai

		self.game = TakBoard(5)
		self.rootnode = UCTNode(state = self.game)
		self.childNodes = None

	def main(self):
		train_data = []
		
		while (self.game.white_win == False and self.game.black_win == False):
			start_time = time()
			self.childNodes = self.search()

			m =  self.choose_move()
			print("Best Move: {}, Trys: {}, took {:.6f}s".format(m.move, m.visits, time() - start_time), flush=True)

			np_state = self.game.get_numpy_board()
			addition = np.full(1575, -1, dtype=int)
			for moves in self.childNodes:
				addition[moves.move["index"]] = moves.wins / moves.visits
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

			#Get Probs from AI
			x_input = state.get_input()
			probs, winner = self.ai.predict(x_input)

			prob = probs[m["index"]] * (1 - 0.25) + 0.25 * gamma[idx%count]
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
	

def save(training_data, network):
	#print(training_data)
	winner = training_data[-1]
	training_data = training_data[:-1]

	if not os.path.isdir(os.path.join(os.getcwd(), network)):
		os.makedirs(os.path.join(os.getcwd(), network))

	name = hashlib.md5(repr(training_data).encode('utf-8')).hexdigest()

	with h5py.File(os.path.join(os.getcwd(), network, "Game_{}.hdf5".format(name)), 'w') as hf:
		print("Game has {} moves".format(len(training_data)), flush=True)
		for index, gamedata in enumerate(training_data):
			hf.create_dataset("state_{}".format(index), data=gamedata["state"], compression="gzip", compression_opts=9)
			hf.create_dataset("probs_{}".format(index), data=gamedata["probs"], compression="gzip", compression_opts=9)

		hf.create_dataset("white_win", data=np.array([winner]), compression="gzip", compression_opts=9)

	#Upload Game to server
	try:
		r = requests.post("https://zero.generalzero.org/submit_game", data={"network": network}, files={"game": open(os.path.join(os.getcwd(), network, "Game_{}.hdf5".format(name)), 'rb')})
		if r.status_code == 200:
			print("Game saved to Server")
		else:
			print(r.status_code, r.text)
	except:
		print("Error uploading to server")


if __name__ == "__main__":
	ai = TakZeroNetwork()
	ai.generate_network()

	for x in range(50000):
		p = UCTTakGame(ai, 5)
		save(p.main(), ai.network)
