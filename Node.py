from math import *
import numpy as np
#TODO
#Add Probabilities
#	1. total Visit Count (Done) N(s,a)
#	2. Total Action Value   W(s,a)
#	3. Mean Action Value    Q(s,a)
#	4. Prob from Model		P(s,a)
#
#	s = board representation
#	a = move

class UCTNode:
	""" A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
		Crashes if state not specified.
	"""
	def __init__(self, move = None, parent = None, state = None, prev_score= None):
		self.move = move # the move that got us to this node - "None" for the root node
		self.parentNode = parent # "None" for the root node
		self.childNodes = []
		self.wins = 0
		self.visits = 0
		self.untriedMoves = state.get_plays() # future child nodes
		self.player1_turn = state.player1_turn # the only part of the state that the Node needs later
		self.puct_ratio = 2.8

		self.prev_score = prev_score

	def UCTSelectChild(self):
		""" Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
			lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
			exploration versus exploitation.
		"""
		s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + self.puct_ratio * c.prev_score * sqrt(self.visits)/(1+c.visits))[-1]
		return s

	def AddChild(self, m, s, p):
		""" Remove m from untriedMoves and add a new child node for this move.
			Return the added child node
		"""
		n = UCTNode(move = m, parent = self, state = s, prev_score = p)
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