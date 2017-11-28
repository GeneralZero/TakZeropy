import random, h5py, os, multiprocessing
import numpy as np

from board import TakBoard
from generate_move_arrays import generate_move_arrays


distance_table = [0,5,15,25,30]
board_size = 5
save_n_moves = 6

def transform_directon(direction, transformation):
	#No Transformation 
	if transformation == 0:
		return direction

	#Flip Vertical
	elif transformation == 1:
		if direction == "up": return "up"
		elif direction == "right": return "left"
		elif direction == "down": return "down"
		else: return "right"

	#Flip Horozontal and Vertical
	elif transformation == 2:
		if direction == "up": return "down"
		elif direction == "right": return "left"
		elif direction == "down": return "up"
		else: return "right"
	
	#Flip Horozontal
	elif transformation == 3:
		if direction == "up": return "down"
		elif direction == "right": return "right"
		elif direction == "down": return "up"
		else: return "left"

	#Rotate 90
	elif transformation == 4:
		if direction == "up": return "right"
		elif direction == "right": return "down"
		elif direction == "down": return "left"
		else: return "up"

	#Rotate 90 and Flip Vertical
	elif transformation == 5:
		if direction == "up": return "left"
		elif direction == "right": return "down"
		elif direction == "down": return "right"
		else: return "up"

	#Rotate 90 and Flip Horozontal and Vertical
	elif transformation == 6:
		if direction == "up": return "left"
		elif direction == "right": return "up"
		elif direction == "down": return "right"
		else: return "down"

	#Rotate 90 and Flip Horozontal
	elif transformation == 7:
		if direction == "up": return "right"
		elif direction == "right": return "up"
		elif direction == "down": return "left"
		else: return "down"

	else:
		raise ValueError("Error Parsing transformation {}".format(transformation))

def transform_pos(pos, transformation):
	ret =""

	#No Transformation 
	if transformation == 0:
		return pos

	#Flip Vertical
	elif transformation == 1:
		ret =  chr((ord("A") + board_size -1) - (ord(pos[0]) - ord("A") ))
		ret +=pos[1:]

	#Flip Horozontal and Vertical
	elif transformation == 2:
		#reflect Letter for 90 or 180
		ret =  chr((ord("A") + board_size -1) - (ord(pos[0]) - ord("A") ))
		ret += str( board_size - (int(pos[1:]) - 1 ))
	
	#Flip Horozontal
	elif transformation == 3:
		ret = pos[0]
		ret += str( board_size - (int(pos[1:]) - 1 ))

	#Rotate 90
	elif transformation == 4:
		ret = chr(int(pos[1:]) + ord("A") - 1)
		ret += str(board_size - (ord(pos[0]) - ord("A")))

	#Rotate 90 and Flip Vertical
	elif transformation == 5:
		ret = chr(int(pos[1:]) + ord("A") - 1)
		ret += str(board_size - (ord(pos[0]) - ord("A")))

		pos = ret

		ret =  chr((ord("A") + board_size -1) - (ord(pos[0]) - ord("A") ))
		ret +=pos[1:]

	#Rotate 90 and Flip Horozontal and Vertical
	elif transformation == 6:
		ret = chr(int(pos[1:]) + ord("A") - 1)
		ret += str(board_size - (ord(pos[0]) - ord("A")))

		pos = ret

		ret =  chr((ord("A") + board_size -1) - (ord(pos[0]) - ord("A") ))
		ret += str( board_size - (int(pos[1:]) - 1 ))

	#Rotate 90 and Flip Horozontal
	elif transformation == 7:
		ret = chr(int(pos[1:]) + ord("A") - 1)
		ret += str(board_size - (ord(pos[0]) - ord("A")))

		pos = ret

		ret = pos[0]
		ret += str( board_size - (int(pos[1:]) - 1 ))

	else:
		raise ValueError("Error Parsing transformation {}".format(transformation))

	return ret

def get_cell_array():
	all_array = []
	for x in range(board_size):
		for y in range(board_size):
			all_array.append(chr(ord("A") + x) + str(y+1))

	return all_array

def get_x_y_from_grid(grid_location):
	#X is A-E
	#Y is 1-5
	x = (ord(grid_location[0].upper()) - ord("A"))
	y =  board_size - int(grid_location[1:])
	return [x,y]

def get_index_from_ints(x, y):
	index = chr(ord("E") - y)
	index += str(x+1)
	return index

def get_play_index(play_obj):
	if play_obj["movetype"] == "p":
		x,y = get_x_y_from_grid(play_obj["placement"])
		offset = (x + y*board_size) * 3
		if play_obj["piece"] == "S":
			return 1500 + offset + 1
		elif play_obj["piece"] == "C":
			return 1500 + offset + 2
		return 1500 + offset

	elif play_obj["movetype"] == "m":
		x,y = get_x_y_from_grid(play_obj["start"])
		offset = (x + y*board_size) * 60
		offset2 =0

		moves_up = distance_table[y]
		moves_right = distance_table[board_size -1 - x]
		moves_down = distance_table[board_size -1 - y]
		moves_left = distance_table[x]

		if play_obj["direction"] == "up":
			for index, item in enumerate(generate_move_arrays(y, board_size,False)):
				if item == play_obj["order"]:
					offset2 += index
					break

		elif play_obj["direction"] == "right":
			offset2 = moves_up
			for index, item in enumerate(generate_move_arrays(board_size -1 - x, board_size,False)):
				if item == play_obj["order"]:
					offset2 += index
					break

		elif play_obj["direction"] == "down":
			offset2 = moves_up + moves_right
			for index, item in enumerate(generate_move_arrays(board_size -1 - y, board_size,False)):
				if item == play_obj["order"]:
					offset2 += index
					break

		elif play_obj["direction"] == "left":
			offset2 = moves_up + moves_right + moves_down
			for index, item in enumerate(generate_move_arrays(x, board_size,False)):
				if item == play_obj["order"]:
					offset2 += index
					break

		else:
			raise ValueError("Invalid Direction")
		
		return offset + offset2			

	else:
		raise ValueError("Invalid Movetype")

def get_play_from_index(idx):
	move_obj = {}
	#Is placement
	if idx >= 1500: 
		idx -= 1500
		move_obj["movetype"] = "p"
		piece = idx % 3

		if piece == 0:
			move_obj["piece"] = ""
		elif piece == 1:
			move_obj["piece"] = "S"
		else:
			move_obj["piece"] = "C"

		loc = idx // 3
		
		x = board_size - (loc // board_size) -1
		y = board_size - (loc % board_size) -1
	
		move_obj["placement"] = get_index_from_ints(x, y)
		#print(idx, loc, move_obj["placement"], x,y)
	else:
		move_obj["movetype"] = "m"

		start = idx//60
		x = board_size - (start // board_size) -1
		y = board_size - (start % board_size) -1
		move_obj["start"] = get_index_from_ints(x,y)



		move_num = idx % 60

		
		moves_up = distance_table[board_size -1 - x]
		moves_right = distance_table[y]
		moves_down = distance_table[x]
		moves_left = distance_table[board_size -1 - y]
		
		#print(x,y, move_obj["start"], move_num, [moves_up, moves_right, moves_down, moves_left])

		#Is move up
		if move_num < moves_up:
			move_obj["direction"] = "up"
			for index, item in enumerate(generate_move_arrays(board_size -1 - x, board_size,False)):
				if index == move_num:
					move_obj["order"] = item
					move_obj["end"] = get_index_from_ints(x + len(item), y)
					break

		#Is move right
		elif move_num < moves_up + moves_right:
			move_obj["direction"] = "right"
			for index, item in enumerate(generate_move_arrays(y, board_size,False)):
				if index == move_num - moves_up:
					move_obj["order"] = item
					move_obj["end"] = get_index_from_ints(x, y-len(item))
					break

		#Is move down
		elif move_num < moves_up + moves_right + moves_down:
			move_obj["direction"] = "down"
			for index, item in enumerate(generate_move_arrays(x, board_size,False)):
				if index == move_num - moves_up - moves_right:
					move_obj["order"] = item
					move_obj["end"] = get_index_from_ints(x - len(item), y)
					break

		#Is move left
		else:
			move_obj["direction"] = "left"
			for index, item in enumerate(generate_move_arrays(board_size -1 - y, board_size,False)):
				if index == move_num - moves_up - moves_right - moves_down:
					move_obj["order"] = item
					move_obj["end"] = get_index_from_ints(x, y + len(item))
					break
	return move_obj

def open_game_file(filename, folder):

	gamedata = []
	probdata = []

	with h5py.File(os.path.join(os.getcwd(), folder, filename), 'r') as hf:
		count = (len(hf)-1)//2

		#Check win
		game = TakBoard(board_size)
		winner = hf["white_win"][0]

		for index in range(count):
			state = hf["state_{}".format(index)][:]
			probs = hf["probs_{}".format(index)][:]

			prev_board = [[np.full((board_size,board_size,64), 0, dtype="B") for y in range(save_n_moves)] for x in range(8)]
			new_probs = [np.full(1575, 0, dtype=int) for x in range(8)]

			#Mirror the game
			for rotate in range(8):
				#get roation of board state
				new_state = np.full((board_size,board_size,64), 0, dtype="B")
				
				
				#Get new rotated board
				for cell in get_cell_array():
					x,y = get_x_y_from_grid(cell)

					new_cell = transform_pos(cell,rotate)
					new_x, new_y = get_x_y_from_grid(new_cell)

					new_state[new_y][new_x] = state[y][x]


				#get indexes of the non 0 moves
				for idx in np.where(probs != 0)[0]:
					if idx == 1575:
						break

					old_move = get_play_from_index(idx)
					if old_move["movetype"] == "p":
						new_move = old_move
						new_move["placement"] = transform_pos(old_move["placement"], rotate)
					else:
						new_move = old_move
						new_move["start"] = transform_pos(old_move["start"], rotate)
						new_move["end"] = transform_pos(old_move["end"], rotate)
						new_move["direction"] = transform_directon(old_move["direction"], rotate)

						new_idx = get_play_index(new_move)
						new_probs[rotate][new_idx] = probs[idx]

				prev_board[rotate][index%save_n_moves] = new_state

				#Append
				build = [prev_board[rotate][(index+x)%save_n_moves] for x in range(save_n_moves)]
				if index == 1 or index % 2 ==0:
					#Black to place
					build.append(np.full((board_size,board_size,64), 1, dtype="B"))
					build.append(np.full((board_size,board_size,64), 0, dtype="B"))
				else:
					build.append(np.full((board_size,board_size,64), 0, dtype="B"))
					build.append(np.full((board_size,board_size,64), 1, dtype="B"))

				gamedata.append(np.array(build))
				probdata.append(new_probs[rotate])

	return gamedata, probdata


def save_game_file(gamedata, probdata, game_file, folder):
	#Save moves, probs with all rotations
	with h5py.File(os.path.join(os.getcwd(), folder, "out", game_file[:-5] + "_done.h5py"), 'w') as hf:
		hf.create_dataset("x_train", data=gamedata, compression="gzip", compression_opts=9)
		hf.create_dataset("y_train", data=probdata, compression="gzip", compression_opts=9)
	

if __name__ == '__main__':
	folder = "games"
	game_files = [filename for filename in os.listdir(os.path.join(os.getcwd(), folder)) if os.path.isfile(os.path.join(os.getcwd(), folder, filename))]
	for game_file in game_files:
		gamedata, probdata = open_game_file(game_file, folder)
		save_game_file(gamedata, probdata, game_file, folder)