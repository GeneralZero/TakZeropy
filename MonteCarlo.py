from math import *
import random, h5py, os, multiprocessing
import numpy as np
from board import TakBoard
from datetime import date
import cProfile
#np.set_printoptions(threshold=np.nan)

game_index = 0

class Node:
	""" A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
		Crashes if state not specified.
	"""
	def __init__(self, move = None, parent = None, state = None):
		self.move = move # the move that got us to this node - "None" for the root node
		self.parentNode = parent # "None" for the root node
		self.childNodes = []
		self.wins = 0
		self.visits = 0
		self.untriedMoves = state.get_plays() # future child nodes
		self.player1_turn = state.player1_turn # the only part of the state that the Node needs later

	def UCTSelectChild(self):
		""" Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
			lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
			exploration versus exploitation.
		"""
		s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
		return s

	def AddChild(self, m, s):
		""" Remove m from untriedMoves and add a new child node for this move.
			Return the added child node
		"""
		n = Node(move = m, parent = self, state = s)
		self.untriedMoves.remove(m)
		self.childNodes.append(n)
		return n

	def Update(self, result):
		""" Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
		"""
		self.visits += 1
		self.wins += result

	def __repr__(self):
		return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

	def TreeToString(self, indent):
		s = self.IndentString(indent) + str(self)
		for c in self.childNodes:
			 s += c.TreeToString(indent+1)
		return s

	def IndentString(self,indent):
		s = "\n"
		for i in range (1,indent+1):
			s += "| "
		return s

	def ChildrenToString(self):
		s = ""
		for c in self.childNodes:
			 s += str(c) + "\n"
		return s

def rollout(state,node):
	player1_turn = state.player1_turn
	# Select
	while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
		node = node.UCTSelectChild()
		state.exec_move(node.move)

	# Expand
	if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
		m = random.choice(node.untriedMoves)
		state.exec_move(m)
		node = node.AddChild(m,state) # add child and descend tree

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


def UCT(rootstate, itermax, verbose = False):
	""" Conduct a UCT search for itermax iterations starting from rootstate.
		Return the best move from the rootstate.
		Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""

	rootnode = Node(state = rootstate)

	for i in range(itermax * len(rootnode.untriedMoves)):
		node = rootnode
		state = rootstate.clone()

		rollout(state, node)

	# Output some information about the tree - can be omitted
	if (verbose):
		print(rootnode.TreeToString(0))

	return sorted(rootnode.childNodes, key = lambda c: c.visits), rootnode.wins/rootnode.visits

def UCTPlayGame():
	""" Play a sample game between two UCT players where each player gets a different number
		of UCT iterations (= simulations = tree nodes).
	"""
	train_data = []
	verbose = False

	game = TakBoard(5)
	while (game.white_win == False and game.black_win == False):
		childNodes, winrate = UCT(rootstate = game, itermax = 100, verbose = verbose) # play with values for itermax and verbose = True
		m =  random.choice(childNodes)
		#win = m.wins
		#trys = m.visits
		#print("Random Move: {}, Wins: {}, Trys: {}, Prob: {:.6f}".format(m.move, win, trys, win/trys))

		np_state = game.board
		addition = np.full(1576, -1.0, dtype=float)
		for moves in childNodes:
			addition[moves.move["index"]] = moves.wins/moves.visits
		addition[1575] = winrate
		#print(winrate)

		train_data.append({"probs":addition, "state":np_state})

		game.exec_move(m.move)

	if game.white_win == True:
		print("White Player wins!")
	elif game.black_win == True:
		print("Black Player wins!")
	else:
		print("Nobody wins!")

	return train_data

def main():
	return UCTPlayGame()


def save(training_data):
	#print(training_data)
	global game_index
	with h5py.File(os.path.join(os.getcwd(), "games", "Game_{}_{}".format(game_index, date.today())), 'w') as hf:
		print("Saving Game{}".format(game_index))
		print("Game has {} moves".format(len(training_data)))
		for index, gamedata in enumerate(training_data):
			hf.create_dataset("state_{}".format(index), data=gamedata["state"], compression="gzip", compression_opts=9)
			hf.create_dataset("probs_{}".format(index), data=gamedata["probs"], compression="gzip", compression_opts=9)

	game_index += 1


if __name__ == "__main__":
	""" Play a single game to the end using UCT for both players.
	"""
	#cProfile.run('main()')


	pool = multiprocessing.Pool(processes=8)
	for x in range(500):
		pool.apply_async(main, callback=save)
	pool.close()
	pool.join()

