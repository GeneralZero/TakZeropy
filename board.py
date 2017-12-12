import numpy as np
from queue import Queue
from generate_move_arrays import generate_move_arrays
#Flat White = 2 010
#Flat Black = 3 011
#Wall White = 4 100
#Wall Black = 5 101
#Caps White = 6 110
#Caps Black = 7 111

#Count as road     & 2
#Cant play on top  & 4
#Color             & 1

class TakBoard():
	"""docstring for TakBoard"""
	def __init__(self, size):
		self.capstone_player1 = True
		self.capstone_player2 = True

		self.player1_turn = True
		self.move_number = 0
		
		self.board_size = size
		self.max_height = 64
		self.black_piece_count = 21
		self.white_piece_count = 21
		self.board = [[[] for x in range(self.board_size)] for x in range(self.board_size)]

		self.encode = {"w": 2, "b": 3, "Sw": 4, "Sb": 5, "Cw": 6, "Cb": 7}

		self.white_top = [[False for x in range(self.board_size)] for x in range(self.board_size)]
		self.black_top = [[False for x in range(self.board_size)] for x in range(self.board_size)]

		self.white_win = False
		self.black_win = False

		self.distance_table = [0,5,15,25,30]

		self.prev_boards = [self.get_numpy_board() for x in range(6)]

	###Monte Carlo Functions

	def clone(self):
		new_ret = TakBoard(self.board_size)
		new_ret.capstone_player1 = self.capstone_player1
		new_ret.capstone_player2 = self.capstone_player2
		new_ret.player1_turn = self.player1_turn
		new_ret.move_number = self.move_number
		new_ret.board_size = self.board_size
		new_ret.board = [[x[:] for x in row] for row in self.board]
		new_ret.white_top = [x[:] for x in self.white_top]

		new_ret.black_top = [y[:] for y in self.black_top]
		#print(new_ret.black_top)
		new_ret.white_win = self.white_win
		new_ret.black_win = self.black_win

		new_ret.black_piece_count = self.black_piece_count
		new_ret.white_piece_count = self.white_piece_count

		return new_ret

	def exec_move(self, move_obj):
		#print(move_obj)
		if move_obj["movetype"] == "m":
			self.move(move_obj["start"], move_obj["end"], move_obj["order"])
		elif move_obj["movetype"] == "p":
			self.place(move_obj["piece"], move_obj["placement"])
		else:
			raise ValueError("Invalid movetype")

		self.prev_boards.append(self.get_numpy_board())


	def get_play_index(self, play_obj):
		if play_obj["movetype"] == "p":
			x,y = self.get_x_y_from_grid(play_obj["placement"])
			offset = (x + y*self.board_size) * 3
			if play_obj["piece"] == "S":
				return 1500 + offset + 1
			elif play_obj["piece"] == "C":
				return 1500 + offset + 2
			return 1500 + offset

		elif play_obj["movetype"] == "m":
			x,y = self.get_x_y_from_grid(play_obj["start"])
			offset = (x + y*self.board_size) * 60
			offset2 =0

			moves_up = self.distance_table[y]
			moves_right = self.distance_table[self.board_size -1 - x]
			moves_down = self.distance_table[self.board_size -1 - y]
			moves_left = self.distance_table[x]

			if play_obj["direction"] == "up":
				for index, item in enumerate(generate_move_arrays(y, self.board_size,False)):
					if item == play_obj["order"]:
						offset2 += index
						break

			elif play_obj["direction"] == "right":
				offset2 = moves_up
				for index, item in enumerate(generate_move_arrays(self.board_size -1 - x, self.board_size,False)):
					if item == play_obj["order"]:
						offset2 += index
						break

			elif play_obj["direction"] == "down":
				offset2 = moves_up + moves_right
				for index, item in enumerate(generate_move_arrays(self.board_size -1 - y, self.board_size,False)):
					if item == play_obj["order"]:
						offset2 += index
						break

			elif play_obj["direction"] == "left":
				offset2 = moves_up + moves_right + moves_down
				for index, item in enumerate(generate_move_arrays(x, self.board_size,False)):
					if item == play_obj["order"]:
						offset2 += index
						break

			else:
				raise ValueError("Invalid Direction")
			
			return offset + offset2			

		else:
			raise ValueError("Invalid Movetype")


	def get_plays(self):
		play_array = []

		#First or second play
		if self.move_number <= 1:
			for x,rows in enumerate(self.board):
				for y,cells in enumerate(rows):
					if len(cells) == 0:
						temp_move = {"movetype": "p", "piece":"", "placement":self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1)}
						temp_move["index"] = self.get_play_index(temp_move)
						play_array.append(temp_move)
			return play_array

		else:
			##Add placements
			for x,rows in enumerate(self.board):
				for y,cells in enumerate(rows):
					if len(cells) != 0:
						##Add moves
						cap = cells[-1][0] == "C"
						start_index = self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1)
						if self.player1_turn == True:
							if cells[-1][-1] == "w":
								distance = 0
								s_distance = 0
								to_move = min(self.board_size, len(cells))

								#Down
								for move_x in range(x+1, self.board_size):
									if self.board[move_x][y] == [] or (self.board[move_x][y][-1][0] != "C" and self.board[move_x][y][-1][0] != "S"):
										distance +=1
									elif cap and self.board[move_x][y][-1][0] == "S":
										s_distance = distance+1
										break
									else:
										break

								move_arrays = generate_move_arrays(distance, to_move, cap and s_distance)
								for move in move_arrays:
									temp_move = {"movetype": "m", "start":start_index, "end":self.get_index_from_ints(self.board_size - x -1-len(move), self.board_size - y -1), "order": move, "direction": "down"}
									temp_move["index"] = self.get_play_index(temp_move)
									play_array.append(temp_move)


								distance = 0
								s_distance = 0
								#Up
								for move_x in range(x-1, -1, -1):
									if self.board[move_x][y] == [] or (self.board[move_x][y][-1][0] != "C" and self.board[move_x][y][-1][0] != "S"):
										distance +=1
									elif cap and self.board[move_x][y][-1][0] == "S":
										s_distance = distance+1
										break
									else:
										break

								move_arrays = generate_move_arrays(distance, to_move, cap and s_distance)
								for move in move_arrays:
									temp_move = {"movetype": "m", "start":start_index, "end":self.get_index_from_ints(self.board_size - x -1+len(move), self.board_size - y -1), "order": move, "direction": "up"}
									temp_move["index"] = self.get_play_index(temp_move)
									play_array.append(temp_move)
				

								distance = 0
								s_distance = 0
								#Left
								for move_y in range(y-1, -1, -1):	
									if self.board[x][move_y] == [] or (self.board[x][move_y][-1][0] != "C" and self.board[x][move_y][-1][0] != "S"):
										distance +=1
									elif cap and self.board[x][move_y][-1][0] == "S":
										s_distance = distance+1
										break
									else:
										break

								move_arrays = generate_move_arrays(distance, to_move, cap and s_distance)
								for move in move_arrays:
									temp_move = {"movetype": "m", "start":start_index, "end":self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1+len(move)), "order": move, "direction": "left"}
									temp_move["index"] = self.get_play_index(temp_move)
									play_array.append(temp_move)
								
								distance = 0
								s_distance = 0								
								#Right
								for move_y in range(y+1, self.board_size):
									if self.board[x][move_y] == [] or (self.board[x][move_y][-1][0] != "C" and self.board[x][move_y][-1][0] != "S"):
										distance +=1
									elif cap and self.board[x][move_y][-1][0] == "S":
										s_distance = distance+1
										break
									else:
										break

								move_arrays = generate_move_arrays(distance, to_move, cap and s_distance)
								for move in move_arrays:
									temp_move = {"movetype": "m", "start":start_index, "end":self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1-len(move)), "order": move, "direction": "right"}
									temp_move["index"] = self.get_play_index(temp_move)
									play_array.append(temp_move)

						else:
							#Get top of players color
							if cells[-1][-1] == "b":								
								distance = 0
								s_distance = 0
								to_move = min(self.board_size, len(cells))

								#Down
								for move_x in range(x+1, self.board_size):
									if self.board[move_x][y] == [] or (self.board[move_x][y][-1][0] != "C" and self.board[move_x][y][-1][0] != "S"):
										distance +=1
									elif cap and self.board[move_x][y][-1][0] == "S":
										s_distance = distance+1
										break
									else:
										break

								move_arrays = generate_move_arrays(distance, to_move, cap and s_distance)
								for move in move_arrays:
									temp_move = {"movetype": "m", "start":start_index, "end":self.get_index_from_ints(self.board_size - x -1-len(move), self.board_size - y -1), "order": move, "direction": "down"}
									temp_move["index"] = self.get_play_index(temp_move)
									play_array.append(temp_move)

								distance = 0
								s_distance = 0
								#Up
								for move_x in range(x-1, -1, -1):
									if self.board[move_x][y] == [] or (self.board[move_x][y][-1][0] != "C" and self.board[move_x][y][-1][0] != "S"):
										distance +=1
									elif cap and self.board[move_x][y][-1][0] == "S":
										s_distance = distance+1
										break
									else:
										break

								move_arrays = generate_move_arrays(distance, to_move, cap and s_distance)
								for move in move_arrays:
									temp_move = {"movetype": "m", "start":start_index, "end":self.get_index_from_ints(self.board_size - x -1+len(move), self.board_size - y -1), "order": move, "direction": "up"}
									temp_move["index"] = self.get_play_index(temp_move)
									play_array.append(temp_move)

								distance = 0
								s_distance = 0
								#Left
								for move_y in range(y-1, -1, -1):	
									if self.board[x][move_y] == [] or (self.board[x][move_y][-1][0] != "C" and self.board[x][move_y][-1][0] != "S"):
										distance +=1
									elif cap and self.board[x][move_y][-1][0] == "S":
										s_distance = distance+1
										break
									else:
										break

								move_arrays = generate_move_arrays(distance, to_move, cap and s_distance)
								for move in move_arrays:
									temp_move = {"movetype": "m", "start":start_index, "end":self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1+len(move)), "order": move, "direction": "left"}
									temp_move["index"] = self.get_play_index(temp_move)
									play_array.append(temp_move)
								
								distance = 0
								s_distance = 0								
								#Right
								for move_y in range(y+1, self.board_size):
									if self.board[x][move_y] == [] or (self.board[x][move_y][-1][0] != "C" and self.board[x][move_y][-1][0] != "S"):
										distance +=1
									elif cap and self.board[x][move_y][-1][0] == "S":
										s_distance = distance+1
										break
									else:
										break

								move_arrays = generate_move_arrays(distance, to_move, cap and s_distance)
								for move in move_arrays:
									temp_move = {"movetype": "m", "start":start_index, "end":self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1-len(move)), "order": move, "direction": "right"}
									temp_move["index"] = self.get_play_index(temp_move)
									play_array.append(temp_move)
				
					else:
						temp_move = {"movetype": "p", "piece":"", "placement":self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1)}
						temp_move["index"] = self.get_play_index(temp_move)

						temp_move1 = {"movetype": "p", "piece":"S", "placement": temp_move["placement"], "index": temp_move["index"] + 1}

						if (self.player1_turn == True and self.capstone_player1 == True) or (self.player1_turn == False and self.capstone_player2 == True):
							if (self.player1_turn == True and self.white_piece_count == 0) or (self.player1_turn == False and self.black_piece_count == 0):
								temp_move["piece"] = "C"
								play_array.append(temp_move)
								continue
							temp_move2 = {"movetype": "p", "piece":"C", "placement": temp_move1["placement"], "index": temp_move1["index"] + 1}
							play_array.append(temp_move2)

						play_array.append(temp_move)
						play_array.append(temp_move1)

		return play_array

	def winner_place(self, piece, grid_location):
		if piece == "" or piece[0] != "S":
			#Start at grid location and map road.
			x,y = self.get_x_y_from_grid(grid_location)
			min_x = x
			max_x = x

			min_y = y
			max_y = y

			to_check = Queue()
			visited = []

			to_check.put([x,y])

			while not to_check.empty():
				##Add indexes to Queue
				x, y = to_check.get()
				visited.append([x,y])

				if (self.player1_turn == True and self.white_top[y][x] == True) or \
					(self.player1_turn == False and self.black_top[y][x] == True):

					if x -1 >= 0 and [x -1, y] not in visited:
						to_check.put([x -1, y])
						visited.append([x -1, y])
					if y -1 >= 0 and [x, y -1] not in visited:
						to_check.put([x, y -1])
						visited.append([x, y -1])
					if x +1 < self.board_size and [x +1, y] not in visited:
						to_check.put([x +1, y])
						visited.append([x +1, y])
					if y +1 < self.board_size and [x, y+1] not in visited:
						to_check.put([x, y +1])
						visited.append([x, y +1])

					min_x = min(min_x, x)
					min_y = min(min_y, y)

					max_x = max(max_x, x)
					max_y = max(max_y, y)

			#Check for Win
			if (max_x - min_x +1) == self.board_size or (max_y - min_y +1) == self.board_size:
				if self.player1_turn == True:
					self.white_win = True
				else:
					self.black_win = True

		#Placing a standing Stone cannot win
		return -1


	def winner_move(self, to_check):
		#Winner_place from start to end
		for x in to_check:
			self.winner_place("", x)

		self.player1_turn = not self.player1_turn

		for x in to_check:
			self.winner_place("", x)

		self.player1_turn = not self.player1_turn

	def winner_all(self):
		#Check Road
		all_array = []
		for x in range(self.board_size):
			for y in range(self.board_size):
				all_array.append(chr(ord("A") + x) + str(y+1))

		self.winner_move(all_array)

		black_count = 0
		white_count = 0

		#Check Out of stones
		for row in self.board:
			for cell in row:
				for piece in cell:
					if "w" in piece:
						white_count +=1
					if "b" in piece:
						black_count +=1

		if white_count >= self.white_piece_count:
			self.black_win = True
		if black_count >= self.black_piece_count:
			self.white_win = True

	###Game Functions

	def place(self, piece, grid_location):
		if self.get_square(grid_location) != []:
			raise Exception("Invalid Placement Location: gridlocation={}, currentsquare={}".format(grid_location, self.get_square(grid_location)))

		if self.move_number == 0:
			color = "b"
		elif self.move_number == 1:
			color = "w"
		elif self.player1_turn == True:
			#Is White
			color = "w"
		else:
			color = "b"

		if piece == None or piece == "":
			place_peice = color

		elif piece == "W" or piece == "S":
			place_peice = "S"+ color

		elif piece == "C":
			place_peice = "C"+ color
			if self.player1_turn == True:
				self.capstone_player1 = False
			else:
				self.capstone_player2 = False
		
		else:
			raise ValueError("Invalid piece: {}".format(piece))

		#Place on board
		x,y = self.get_x_y_from_grid(grid_location)
		self.board[y][x].append(place_peice)

		#Update
		if place_peice[0] != "S":
			if color == "w":
				self.white_top[y][x] = True
			else:
				self.black_top[y][x] = True

			#Check Winner
			self.winner_place(place_peice, grid_location)

		if piece != 'C':
			if color == "w":
				self.white_piece_count -= 1
				if self.white_piece_count == -1:
					self.black_win = True
					return

			else:
				self.black_piece_count -= 1
				if self.black_piece_count == -1:
					self.white_win = True
					return
		#Change turn
		self.player1_turn = not self.player1_turn
		self.move_number +=1


	def move(self, start, end, move_array):
		#Valid Size
		if np.sum(move_array) > self.board_size:
			raise Exception("Moving more tiles than board size")

		#print("Move: s:{}, e:{} square:{}".format(start, end, self.get_square(start)))

		count = np.sum(move_array)
		current_square = start
		to_check = [start]

		#Valid Move
		if start[0] == end[0]:
			#Up and Down
			if int(start[1:]) > int(end[1:]):
				#Down

				#Set Start
				pop_array = self.get_square(start)[-count:]
				self.set_square(start, self.get_square(start)[:-count])

				for index, pops in enumerate(move_array):
					current_square = current_square[0] + str(int(current_square[1:]) -1)

					to_check.append(current_square)

					if len(move_array) -1 == index and pops == 1 and len(pop_array) > 0:
						self.check_for_wall_crush(current_square, pop_array)

					for x in range(pops):
						self.append_square(current_square, pop_array.pop(0))

					x,y = self.get_x_y_from_grid(current_square)
					if self.get_square(current_square)[-1][0] != "S":
						if self.player1_turn == False:
							if self.get_square(current_square)[-1][-1] == "b":
								self.black_top[y][x] = True
							else:
								self.black_top[y][x] = False
						else:
							if self.get_square(current_square)[-1][-1] == "w":
								self.white_top[y][x] = True
							else:
								self.white_top[y][x] = False
					else:
						self.white_top[y][x] = False
						self.black_top[y][x] = False
			else:
				#Up

				#Set Start
				pop_array = self.get_square(start)[-count:]
				self.set_square(start, self.get_square(start)[:-count])

				for index, pops in enumerate(move_array):
					current_square = current_square[0] + str(int(current_square[1:]) +1)

					to_check.append(current_square)

					if len(move_array) -1 == index and pops == 1 and len(pop_array) > 0:
						self.check_for_wall_crush(current_square, pop_array)

					for x in range(pops):
						self.append_square(current_square, pop_array.pop(0))

					x,y = self.get_x_y_from_grid(current_square)
					if self.get_square(current_square)[-1][0] != "S":
						if self.player1_turn == False:
							if self.get_square(current_square)[-1][-1] == "b":
								self.black_top[y][x] = True
							else:
								self.black_top[y][x] = False
						else:
							if self.get_square(current_square)[-1][-1] == "w":
								self.white_top[y][x] = True
							else:
								self.white_top[y][x] = False	
					else:
						self.white_top[y][x] = False
						self.black_top[y][x] = False

		elif start[1:] == end[1:]:
			#left and right
			if start[0] > end[0]:
				#Left
				
				#Set Start
				pop_array = self.get_square(start)[-count:]
				self.set_square(start, self.get_square(start)[:-count])

				for index, pops in enumerate(move_array):
					current_square = chr(ord(current_square[0]) - 1) + current_square[1:]

					to_check.append(current_square)

					if len(move_array) -1 == index and pops == 1 and len(pop_array) > 0:
						self.check_for_wall_crush(current_square, pop_array)

					for x in range(pops):
						self.append_square(current_square, pop_array.pop(0))
					
					x,y = self.get_x_y_from_grid(current_square)
					if self.get_square(current_square)[-1][0] != "S":
						if self.player1_turn == False:
							if self.get_square(current_square)[-1][-1] == "b":
								self.black_top[y][x] = True
							else:
								self.black_top[y][x] = False
						else:
							if self.get_square(current_square)[-1][-1] == "w":
								self.white_top[y][x] = True
							else:
								self.white_top[y][x] = False						
					else:
						self.white_top[y][x] = False
						self.black_top[y][x] = False

			else:
				#Right
				
				#Set Start
				pop_array = self.get_square(start)[-count:]
				self.set_square(start, self.get_square(start)[:-count])

				for index, pops in enumerate(move_array):
					current_square = chr(ord(current_square[0]) + 1) + current_square[1:]

					to_check.append(current_square)

					if len(move_array) -1 == index and pops == 1 and len(pop_array) > 0:
						self.check_for_wall_crush(current_square, pop_array)

					for x in range(pops):
						self.append_square(current_square, pop_array.pop(0))

					x,y = self.get_x_y_from_grid(current_square)
					if self.get_square(current_square)[-1][0] != "S":
						if self.player1_turn == False:
							if self.get_square(current_square)[-1][-1] == "b":
								self.black_top[y][x] = True
							else:
								self.black_top[y][x] = False
						else:
							if self.get_square(current_square)[-1][-1] == "w":
								self.white_top[y][x] = True
							else:
								self.white_top[y][x] = False
					else:
						self.white_top[y][x] = False
						self.black_top[y][x] = False
		else:
			raise Exception("Move is not up, down, left, or right")

		self.update_tops(to_check)

		#Check for win
		self.winner_move(to_check)

		#Change turn
		self.player1_turn = not self.player1_turn
		self.move_number +=1

	def update_tops(self, update):
		for current_square in update:
			x,y = self.get_x_y_from_grid(current_square)
			cell = self.board[x][y]
			if len(cell) == 0 or cell[-1][0] == "S":
				self.white_top[x][y] = False
				self.black_top[x][y] = False
			elif cell[-1][-1] == "w":
				self.white_top[x][y] = True
				self.black_top[x][y] = False
			elif cell[-1][-1] == "b":
				self.black_top[x][y] = True
				self.white_top[x][y] = False

	def update_all_tops(self):
		for x,rows in enumerate(self.board):
			for y,cells in enumerate(rows):
				if len(cells) == 0 or cells[-1][0] == "S":
					self.white_top[x][y] = False
					self.black_top[x][y] = False
				elif cells[-1][-1] == "w":
					self.white_top[x][y] = True
					self.black_top[x][y] = False
				elif cells[-1][-1] == "b":
					self.black_top[x][y] = True
					self.white_top[x][y] = False


	def check_for_wall_crush(self, current_square, pop_array):
		#If last move and pops is 1 
		#Check if has capstone in peice

		piece = pop_array[0]
		wall = self.get_square(current_square)
		if len(wall) > 0:
			wall = self.get_square(current_square)[-1]
		else:
			return
		if piece[0] == 'C' and wall != None and wall[0] == 'S':
			#print("Capstone wall crush")
			square = self.get_square(current_square)

			if square == None:
				square.append(wall[1:])
			else:
				square = square[:-1]
				square.append(wall[1:])

			self.set_square(current_square, square)

	###Helper Functions
	def get_square(self, grid_location):
		x = (ord(grid_location[0].upper()) - ord("A"))
		y =  self.board_size - int(grid_location[1:])
		return self.board[y][x]

	def get_index_from_ints(self, x, y):
		index = chr(ord("E") - y)
		index += str(x+1)
		return index

	def set_square(self, grid_location, peices):
		x = (ord(grid_location[0].upper()) - ord("A"))
		y =  self.board_size - int(grid_location[1:])
		self.board[y][x] = peices

	def append_square(self, grid_location, peice):
		x = (ord(grid_location[0].upper()) - ord("A"))
		y =  self.board_size - int(grid_location[1:])
		self.board[y][x].append(peice)

	def get_current_string_board(self):
		return self.board

	def get_internal_cell(self, cell):
		out_list = []
		for element in cell:
			for key, value in self.encode.items():
				if value == element:
					out_list.append(key)
					break

		return out_list[::-1]

	def convert_piece_to_result(self, piece):
		return int(self.encode[piece])

	def get_x_y_from_grid(self, grid_location):
		#X is A-E
		#Y is 1-5
		x = (ord(grid_location[0].upper()) - ord("A"))
		y =  self.board_size - int(grid_location[1:])
		return [x,y]

	###Deep Learning Functions
	def set_np_game_board(self, move_board, player1_turn):
		self.player1_turn = player1_turn
		count = 0
		#Get Rows
		for x, row in enumerate(self.board):
			for y, cell in enumerate(row):
				move_cell = self.get_internal_cell(move_board[x][y])
				count += len(move_cell)
				self.board[x][y] = move_cell

		self.move_number = count

		#reset tops
		self.update_all_tops()
		#reset counts
		self.winner_all()


	def get_input(self):
		ret = self.prev_boards[-6:]
		ret = ret[::-1]
		if self.player1_turn == True:
			#White to place
			ret.append(np.full((self.board_size,self.board_size,64), 1, dtype="B"))
			ret.append(np.full((self.board_size,self.board_size,64), 0, dtype="B"))
		else:
			ret.append(np.full((self.board_size,self.board_size,64), 0, dtype="B"))
			ret.append(np.full((self.board_size,self.board_size,64), 1, dtype="B"))

		return np.array([ret])

	def get_numpy_board(self):
		board_array=[]
		
		for row_index, rows in enumerate(self.board):
			row_array = []
			for col_index, cols in enumerate(rows):
				cell = []
				for height in cols:
					cell.append(self.encode[height])

				#Top is lowest index
				cell = cell[::-1]
				cell = np.pad(np.array(cell, dtype=np.dtype('B')), (0, self.max_height - len(cell)), 'constant')
				row_array.append(cell)
			board_array.append(np.array(row_array))

		return np.array(board_array)

	def pack_move(self, move):
		out = [0,0,0,0,0,0,0,0,0,0,0,0]

		if move["movetype"] == "p":
			#Move Type
			out[0] = 1

			#Piece
			out[1] = self.convert_piece_to_result(move["piece"])

			temp_move = self.get_x_y_from_grid(move["placement"])

			#X,Y placement
			out[2] = temp_move[0]
			out[3] = temp_move[1]


		elif move["movetype"] == "m":
			#Move Type
			out[0] = 2

			temp_move = self.get_x_y_from_grid(move["start"])

			#X,Y Start stack
			out[4] = temp_move[0]
			out[5] = temp_move[1]

			#Direction
			out[6] = self.get_direction_from_start_end(move["start"], move["end"])

			#Number of pieces
			for x in range(len(move["order"])):
				out[7+x] = move["order"][x]

		else:
			raise Exception("Invalid Move Type Result")

		return out



###Tests
def game1():
	p= TakBoard(5)

	p.place("", "D4")
	p.place("", "C3")
	p.place("C", "D3")
	p.place("C", "C4")
	p.place("S", "D5")
	p.place("S", "B4")
	for x in p.get_current_string_board():
		print(x)
	for x in p.get_plays():
		print(x)
	p.move("D5", "D4", [1])
	#for x in p.get_current_string_board():
	#	print(x)
	p.move("C4", "B4", [1])
	p.place("", "C4")
	p.move("B4", "D4", [1, 1])



def game2():
	p= TakBoard(5)
	p.place("", "E1")

	p.place("", "D1")
	p.place("", "D2")
	p.place("", "D3")
	p.place("", "C2")
	for x in p.get_plays():
		print(x)
	p.place("", "E2")
	p.place("", "E3")
	p.place("", "D4")
	p.place("", "B2")
	p.move("D3", "E3", [1])
	p.place("C", "D3")
	p.place("", "E4")
	p.move("D3", "E3", [1])
	p.place("", "A2")
	p.move("E3", "E1", [1, 2])
	p.place("", "A3")
	p.place("", "A1")
	p.move("A2", "B2", [1])
	p.place("", "A2")
	p.move("A3", "A2", [1])
	p.place("", "C3")
	p.place("", "B3")
	p.place("", "B4")
	p.place("", "C4")
	p.place("", "B1")
	p.place("W", "C1")
	p.move("E1", "C1", [2, 1])

	for x in p.board:
		print(x)
	test = p.get_numpy_board()
	p.set_np_game_board(test, True)
	for x in p.board:
		print(x)


if __name__ == '__main__':
	game2()
