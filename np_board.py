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
		self.board = np.full((self.board_size, self.board_size, self.max_height), 0, dtype='B')

		self.encode = {"w": 2, "b": 3, "sw": 4, "sb": 5, "cw": 6, "cb": 7}

		self.white_top = np.full((self.board_size, self.board_size), False, dtype=bool)
		self.black_top = np.full((self.board_size, self.board_size), False, dtype=bool)

		self.white_win = False
		self.black_win = False

		self.distance_table = [0,5,15,25,30]

	###Monte Carlo Functions

	def clone(self):
		new_ret = TakBoard(self.board_size)
		new_ret.capstone_player1 = self.capstone_player1
		new_ret.capstone_player2 = self.capstone_player2
		new_ret.player1_turn = self.player1_turn
		new_ret.move_number = self.move_number
		new_ret.board_size = self.board_size
		new_ret.board = np.copy(self.board)
		new_ret.white_top = np.copy(self.white_top)

		new_ret.black_top = np.copy(self.black_top)

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
						offset2 += index -1
						break

			elif play_obj["direction"] == "right":
				offset2 = moves_up
				for index, item in enumerate(generate_move_arrays(self.board_size -1 - x, self.board_size,False)):
					if item == play_obj["order"]:
						offset2 += index -1
						break

			elif play_obj["direction"] == "down":
				offset2 = moves_up + moves_right
				for index, item in enumerate(generate_move_arrays(self.board_size -1 - y, self.board_size,False)):
					if item == play_obj["order"]:
						offset2 += index -1
						break

			elif play_obj["direction"] == "left":
				offset2 = moves_up + moves_right + moves_down
				for index, item in enumerate(generate_move_arrays(x, self.board_size,False)):
					if item == play_obj["order"]:
						offset2 += index -1
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
			for x,y in np.ndindex(self.board.shape[:2]):
				if np.count_nonzero(self.board[x,y]) == 0:
					temp_move = {"movetype": "p", "piece":"", "placement":self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1)}
					temp_move["index"] = self.get_play_index(temp_move)
					play_array.append(temp_move)
			return play_array

		else:
			##Add placements
			for x,y in np.ndindex(self.board.shape[:2]):
				cell = self.board[x,y]
				if np.count_nonzero(cell) == 0:
					temp_move = {"movetype": "p", "piece":"", "placement":self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1)}
					temp_move["index"] = self.get_play_index(temp_move)
					play_array.append(temp_move)

					temp_move1 = {"movetype": "p", "piece":"S", "placement": temp_move["placement"], "index": temp_move["index"] + 1}
					play_array.append(temp_move1)
					
					if (self.player1_turn == True and self.capstone_player1 == True) or (self.player1_turn == False and self.capstone_player2 == True):
						temp_move2 = {"movetype": "p", "piece":"C", "placement": temp_move1["placement"], "index": temp_move1["index"] + 1}
						play_array.append(temp_move2)

				else:
					##Add moves
					last_index = np.argmax(cell==0) -1
					cap = (np.bitwise_and(cell[last_index],6) == 6)
					start_index = self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1)
					if self.player1_turn == True:
						if (np.bitwise_and(cell[last_index],1) == 0):
							distance = 0
							s_distance = 0
							to_move = min(self.board_size, last_index+1)

							#Down
							for move_x in range(x+1, self.board_size):
								cell_m = self.board[move_x,y]
								last_new_index = np.argmax(cell_m==0) -1
								if last_new_index < 0:
									last_new_index = 0
								if np.count_nonzero(cell_m) == 0 or (np.bitwise_and(cell_m[last_new_index],4) != 4):
									distance +=1
								elif cap and np.bitwise_and(cell_m[last_new_index],6) == 4:
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
								cell_m = self.board[move_x,y]
								last_new_index = np.argmax(cell_m==0) -1
								if last_new_index < 0:
									last_new_index = 0								
								if np.count_nonzero(cell_m) == 0 or (np.bitwise_and(cell_m[last_new_index],4) != 4):
									distance +=1
								elif cap and np.bitwise_and(cell_m[last_new_index],6) == 4:
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
								cell_m = self.board[x,move_y]
								last_new_index = np.argmax(cell_m==0) -1
								if last_new_index < 0:
									last_new_index = 0								
								if np.count_nonzero(cell_m) == 0 or (np.bitwise_and(cell_m[last_new_index],4) != 4):
									distance +=1
								elif cap and np.bitwise_and(cell_m[last_new_index],6) == 4:
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
								cell_m = self.board[x,move_y]
								last_new_index = np.argmax(cell_m==0) -1
								if last_new_index < 0:
									last_new_index = 0							
								if np.count_nonzero(cell_m) == 0 or (np.bitwise_and(cell_m[last_new_index],4) != 4):
									distance +=1
								elif cap and np.bitwise_and(cell_m[last_new_index],6) == 4:
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
						if (np.bitwise_and(cell[last_index],1) == 1):								
							distance = 0
							s_distance = 0
							to_move = min(self.board_size, last_index+1)

							#Down
							for move_x in range(x+1, self.board_size):
								cell_m = self.board[move_x,y]
								last_new_index = np.argmax(cell_m==0) -1
								if last_new_index < 0:
									last_new_index = 0
								if np.count_nonzero(cell_m) == 0 or (np.bitwise_and(cell_m[last_new_index],4) != 4):
									distance +=1
								elif cap and np.bitwise_and(cell_m[last_new_index],6) == 4:
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
								cell_m = self.board[move_x,y]
								last_new_index = np.argmax(cell_m==0) -1
								if last_new_index < 0:
									last_new_index = 0
								if np.count_nonzero(cell_m) == 0 or (np.bitwise_and(cell_m[last_new_index],4) != 4):
									distance +=1
								elif cap and np.bitwise_and(cell_m[last_new_index],6) == 4:
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
								cell_m = self.board[x,move_y]
								last_new_index = np.argmax(cell_m==0) -1
								if last_new_index < 0:
									last_new_index = 0
								if np.count_nonzero(cell_m) == 0 or (np.bitwise_and(cell_m[last_new_index],4) != 4):
									distance +=1
								elif cap and np.bitwise_and(cell_m[last_new_index],6) == 4:
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
								cell_m = self.board[x,move_y]
								last_new_index = np.argmax(cell_m==0) -1
								if last_new_index < 0:
									last_new_index = 0
								if np.count_nonzero(cell_m) == 0 or (np.bitwise_and(cell_m[last_new_index],4) != 4):
									distance +=1
								elif cap and np.bitwise_and(cell_m[last_new_index],6) == 4:
									s_distance = distance+1
									break
								else:
									break

							move_arrays = generate_move_arrays(distance, to_move, cap and s_distance)
							for move in move_arrays:
								temp_move = {"movetype": "m", "start":start_index, "end":self.get_index_from_ints(self.board_size - x -1, self.board_size - y -1-len(move)), "order": move, "direction": "right"}
								temp_move["index"] = self.get_play_index(temp_move)
								play_array.append(temp_move)

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

	###Game Functions

	def place(self, piece, grid_location):
		x,y = self.get_x_y_from_grid(grid_location)
		#last_new_index = (self.board[move_x][y]!=0).cumsum().argmax()
		cell = self.board[y,x]
		if np.count_nonzero(cell) != 0:
			raise Exception("Invalid Placement Location: gridlocation={}, currentsquare={}".format(grid_location, cell))

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

		elif piece.lower() == "w" or piece.lower() == "s":
			place_peice = "S"+ color

		elif piece.lower() == "c":
			place_peice = "C"+ color
			if self.player1_turn == True:
				self.capstone_player1 = False
			else:
				self.capstone_player2 = False
		
		else:
			raise ValueError("Invalid piece: {}".format(piece))

		#Place on board
		cell[0] = self.encode[place_peice.lower()]

		#Update
		if place_peice[0] != "S":
			if color == "w":
				self.white_top[y][x] = True
			else:
				self.black_top[y][x] = True

			#Check Winner
			self.winner_place(place_peice, grid_location)

		if piece.lower() != 'C':
			if color == "w":
				self.white_piece_count -= 1
				if self.white_piece_count == 0:
					self.black_win = True
					return

			else:
				self.black_piece_count -= 1
				if self.black_piece_count == 0:
					self.white_win = True
					return
		#Change turn
		self.player1_turn = not self.player1_turn
		self.move_number +=1


	def move(self, start, end, move_array):
		#Valid Size
		if np.sum(move_array) > self.board_size:
			raise Exception("Moving more tiles than board size")

		count = np.sum(move_array)
		current_square = start
		to_check = [start]

		#print("Move: s:{}, e:{}".format(start, end))

		#Valid Move
		if start[0] == end[0]:
			#Up and Down
			if int(start[1:]) > int(end[1:]):
				#Down

				#Set Start
				x,y = self.get_x_y_from_grid(start)
				cell = self.board[y,x]
				last_index = np.argmax(cell==0) -1
				if last_index < 0:
					last_index = 0
				pop_array = cell[last_index-count+1:last_index+1].tolist()
				#print(last_index-count+1,last_index+1, cell[last_index-count+1:last_index+1])

				#Remove from stack
				for a in range(count):
					cell[last_index-a] = 0

				for index, pops in enumerate(move_array):
					current_square = current_square[0] + str(int(current_square[1:]) -1)

					to_check.append(current_square)

					if len(move_array) -1 == index and pops == 1 and len(pop_array) > 0:
						self.check_for_wall_crush(current_square, pop_array)

					x,y = self.get_x_y_from_grid(current_square)
					cell = self.board[y,x]
					last_index = np.argmax(cell==0) -1
					if last_index < 0:
						last_index = 0
					#print(x,y,current_square)
					for a in range(pops):
						if cell[last_index+a] == 0:
							cell[last_index+a] = pop_array.pop(0)
						else:
							cell[last_index+a+1] = pop_array.pop(0)

					last_index = np.argmax(cell==0) -1
					if last_index < 0:
						last_index = 0
					if np.bitwise_and(cell[last_index],6) != 4:
						if self.player1_turn == False:
							if np.bitwise_and(cell[last_index], 1) == 1:
								self.black_top[y][x] = True
							else:
								self.black_top[y][x] = False
						else:
							if np.bitwise_and(cell[last_index], 1) == 0:
								self.white_top[y][x] = True
							else:
								self.white_top[y][x] = False
					else:
						self.white_top[y][x] = False
						self.black_top[y][x] = False
			else:
				#Up

				#Set Start
				x,y = self.get_x_y_from_grid(start)
				cell = self.board[y,x]
				last_index = np.argmax(cell==0) -1
				if last_index < 0:
					last_index = 0
				pop_array = cell[last_index-count+1:last_index+1].tolist()
				#print(last_index-count+1,last_index+1, cell[last_index-count+1:last_index+1])

				#Remove from stack
				for a in range(count):
					cell[last_index-a] = 0

				for index, pops in enumerate(move_array):
					current_square = current_square[0] + str(int(current_square[1:]) +1)

					to_check.append(current_square)

					if len(move_array) -1 == index and pops == 1 and len(pop_array) > 0:
						self.check_for_wall_crush(current_square, pop_array)

					x,y = self.get_x_y_from_grid(current_square)
					cell = self.board[y,x]
					last_index = np.argmax(cell==0) -1
					if last_index < 0:
						last_index = 0
					#print(x,y,current_square)
					for a in range(pops):
						if cell[last_index+a] == 0:
							cell[last_index+a] = pop_array.pop(0)
						else:
							cell[last_index+a+1] = pop_array.pop(0)

					last_index = np.argmax(cell==0) -1
					if last_index < 0:
						last_index = 0
					if np.bitwise_and(cell[last_index],6) != 4:
						if self.player1_turn == False:
							if np.bitwise_and(cell[last_index], 1) == 1:
								self.black_top[y][x] = True
							else:
								self.black_top[y][x] = False
						else:
							if np.bitwise_and(cell[last_index], 1) == 0:
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
				x,y = self.get_x_y_from_grid(start)
				cell = self.board[y,x]
				last_index = np.argmax(cell==0) -1
				if last_index < 0:
					last_index = 0
				pop_array = cell[last_index-count+1:last_index+1].tolist()
				#print(last_index-count+1,last_index+1, cell[last_index-count+1:last_index+1])

				#Remove from stack
				for a in range(count):
					cell[last_index-a] = 0

				for index, pops in enumerate(move_array):
					current_square = chr(ord(current_square[0]) - 1) + current_square[1:]

					to_check.append(current_square)

					if len(move_array) -1 == index and pops == 1 and len(pop_array) > 0:
						self.check_for_wall_crush(current_square, pop_array)

					x,y = self.get_x_y_from_grid(current_square)
					cell = self.board[y,x]
					last_index = np.argmax(cell==0) -1
					if last_index < 0:
						last_index = 0
					#print(x,y,current_square)
					for a in range(pops):
						if cell[last_index+a] == 0:
							cell[last_index+a] = pop_array.pop(0)
						else:
							cell[last_index+a+1] = pop_array.pop(0)
					
					last_index = np.argmax(cell==0) -1
					if last_index < 0:
						last_index = 0
					if np.bitwise_and(cell[last_index],6) != 4:
						if self.player1_turn == False:
							if np.bitwise_and(cell[last_index], 1) == 1:
								self.black_top[y][x] = True
							else:
								self.black_top[y][x] = False
						else:
							if np.bitwise_and(cell[last_index], 1) == 0:
								self.white_top[y][x] = True
							else:
								self.white_top[y][x] = False	
					else:
						self.white_top[y][x] = False
						self.black_top[y][x] = False

			else:
				#Right
				
				#Set Start
				x,y = self.get_x_y_from_grid(start)
				cell = self.board[y,x]
				last_index = np.argmax(cell==0) -1
				if last_index < 0:
					last_index = 0
				pop_array = cell[last_index-count+1:last_index+1].tolist()
				#print(last_index-count+1,last_index+1, cell[last_index-count+1:last_index+1])

				#Remove from stack
				for a in range(count):
					cell[last_index-a] = 0

				for index, pops in enumerate(move_array):
					current_square = chr(ord(current_square[0]) + 1) + current_square[1:]

					to_check.append(current_square)

					if len(move_array) -1 == index and pops == 1 and len(pop_array) > 0:
						self.check_for_wall_crush(current_square, pop_array)

					x,y = self.get_x_y_from_grid(current_square)
					cell = self.board[y,x]
					last_index = np.argmax(cell==0) -1
					if last_index < 0:
						last_index = 0
					#print(x,y,current_square)
					for a in range(pops):
						if cell[last_index+a] == 0:
							cell[last_index+a] = pop_array.pop(0)
						else:
							cell[last_index+a+1] = pop_array.pop(0)
					
					last_index = np.argmax(cell==0) -1
					if last_index < 0:
						last_index = 0
					if np.bitwise_and(cell[last_index],6) != 4:
						if self.player1_turn == False:
							if np.bitwise_and(cell[last_index], 1) == 1:
								self.black_top[y][x] = True
							else:
								self.black_top[y][x] = False
						else:
							if np.bitwise_and(cell[last_index], 1) == 0:
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
			cell = self.board[x,y]
			last_index = np.argmax(cell==0) -1
			if last_index < 0:
				last_index = 0
			if np.count_nonzero(cell) == 0 or (np.bitwise_and(cell[last_index],6) == 4):
				self.white_top[x,y] = False
				self.black_top[x,y] = False
			elif (np.bitwise_and(cell[last_index],1) == 0):
				self.white_top[x,y] = True
				self.black_top[x,y] = False
			else:
				self.black_top[x,y] = True
				self.white_top[x,y] = False

	def check_for_wall_crush(self, current_square, pop_array):
		#If last move and pops is 1 
		#Check if has capstone in peice

		x,y = self.get_x_y_from_grid(current_square)

		piece = pop_array[0]
		cell = self.board[y,x]
		last_index = (cell!=0).cumsum().argmax()
		if not np.count_nonzero(cell) == 0:
			wall = cell[last_index]
		else:
			return
		if (np.bitwise_and(piece, 6) == 6) and np.bitwise_and(wall, 4) == 4:
			#print("Capstone wall crush")

			if np.count_nonzero(cell) == 0:
				cell[last_index+1] = (int(np.bitwise_and(wall, 1)) +2)
			else:
				cell[last_index] = (int(np.bitwise_and(wall, 1)) +2)

	###Helper Functions
	def get_index_from_ints(self, x, y):
		index = chr(ord("E") - y)
		index += str(x+1)
		return index

	def get_index_from_int(self, z):
		y = z // self.board_size
		x = z % self.board_size
		index = chr(ord("A") + y)
		index += str(self.board_size - x)
		return index

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

	def get_x_y_from_grid(self, grid_location):
		#X is A-E
		#Y is 1-5
		x = (ord(grid_location[0].upper()) - ord("A"))
		y =  self.board_size - int(grid_location[1:])
		return [x,y]

	###Deep Learning Functions

	def get_string_board(self):
		board_array=[]
		
		for row_index, rows in enumerate(self.board):
			row_array = []
			for cel_index, cell in enumerate(rows):
				last_index = np.argmax(cell==0) -1
				if last_index < 0:
					last_index = 0
				row_array.append(list(cell[:last_index]))
			board_array.append(row_array)

		return board_array

	def set_np_game_board(self, move_board, player1_turn):
		self.player1_turn = player1_turn
		count = 0
		#Get Rows
		for x, row in enumerate(self.board):
			for y, cell in enumerate(row):
				move_cell = self.get_internal_cell(move_board[x][y])
				count += len(move_cell)
				self.board[x,y] = move_cell

		self.move_number = count

	def pack_move(self, move):
		out = [0,0,0,0,0,0,0,0,0,0,0,0]

		if move["movetype"] == "p":
			#Move Type
			out[0] = 1

			#Piece
			out[1] = self.encode[move["piece"].lower()]

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

	def get_result_from_new_board(self, move_board):
		move = self.get_move_from_new_board(move_board)

		return self.pack_move(move)

	def get_direction_from_start_end(self, start, end):
		size = 5

		#direction lowest is bottom left
		start_int = size * int(start[1:]) + (ord('a') - ord(start[0].lower()))
		end_int = size * int(end[1:]) + (ord('a') - ord(end[0].lower())) 

		if start_int > end_int:
			# Move Down or Left
			if end_int > start_int - size:
				#Move Down
				return 3
			else:
				#Move Left
				return 4
		else:
			#Move Up or Right
			if end_int >= start_int + size:
				#Move Up
				return 1
			else:
				#Move Right
				return 2

	def get_move_from_new_board(self, move_board):
		changes = []
		#Get Rows
		for x, row in enumerate(self.board):
			for y, cell in enumerate(row):
				#Convert cell to be compared
				move_cell = self.get_internal_cell(move_board[x][y])



				if len(cell) == len(move_cell):
					if cell != move_cell:
						#print("Change in the elements at the index x:{}, y:{}".format(x, y))
						#print("MoveCell: {}".format(move_cell))
						#print("Cell: {}".format(cell))
						changes.append({'x':x,'y':y, "move_cell": move_cell, "cell": cell, "index": self.get_index_from_ints(x,y), "diff": len(cell) - len(move_cell)})
				else:
					#print("Change in number of elements at index x:{}, y:{}".format(x, y))
					#print("MoveCell: {}".format(move_cell))
					#print("Cell: {}".format(cell))
					changes.append({'x':x,'y':y, "move_cell": move_cell, "cell": cell, "index": self.get_index_from_ints(x,y), "diff": len(cell) - len(move_cell)})
		
		#Place 
		#print(changes)
		if len(changes) == 1:
			change = changes[0]

			if len(change["move_cell"]) == 1:
				#print("[Place] {} {}".format("", change["index"]))
				self.place("", change["index"])

			else:
				#print("[Place] {} {}".format(change["move_cell"][0], change["index"]))
				self.place(change["move_cell"][0], change["index"])

			return {"movetype": "p", "piece": change["move_cell"][0], "placement":change["index"]}

			
		else:
			#Move
			movement_array = [row for row in changes]

			start = ""
			end = ""

			reverse = False

			for index, change in enumerate(changes):
				if change["diff"] > 0:
					#print("Start is " + change["index"])

					start = change["index"]
					movement_array.pop(index)

					if index == 0:
						movement_array = movement_array[::-1] 
						end = changes[-1]["index"]
					else:
						end = changes[0]["index"]
						#print(changes[0])
					break

			count_array = []
			for elem in movement_array:
				count_array.append(abs(elem["diff"]))

			
			#print("[Move]  Start: {}, End: {}, Array: {}".format(start, end, count_array))
			self.move(start, end, count_array)

			return {"movetype": "m", "start": start, "end": end, "order": count_array}



###Tests
def game1():
	p= TakBoard(5)

	p.place("", "D4")
	p.place("", "C3")
	p.place("C", "D3")
	p.place("C", "C4")
	p.place("S", "D5")
	p.place("S", "B4")
	#for x in p.get_current_string_board():
	#	print(x)
	for x in p.get_plays():
		print(x)
	p.move("D5", "D4", [1])
	#for x in p.get_current_string_board():
	#	print(x)
	p.move("C4", "B4", [1])
	p.place("", "C4")
	p.move("B4", "D4", [1, 1])

	print(p.white_win)
	print(p.black_win)

def game2():
	p= TakBoard(5)
	p.place("", "E1")

	p.place("", "D1")
	p.place("", "D2")
	p.place("", "D3")
	p.place("", "C2")
	#for x in p.get_plays():
	#	print(x)
	p.place("", "E2")
	p.place("", "E3")
	p.place("", "D4")
	p.place("", "B2")
	for x in p.get_string_board():
		print(x)	
	print()
	p.move("D3", "E3", [1])
	for x in p.get_string_board():
		print(x)
	p.place("C", "D3")
	p.place("", "E4")
	p.move("D3", "E3", [1])

	p.place("", "A2")
	p.move("E3", "E1", [1, 2])
	#test = p.get_numpy_board()
	#print(test.shape)
	
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

	print(p.white_win)
	print(p.black_win)

if __name__ == '__main__':
	game2()
