#!/usr/bin/python
import keras, os, random, h5py, requests
import numpy as np
from keras.models import Model
from keras.layers import Input, Dense, Conv3D, BatchNormalization, Activation, Flatten
from keras.callbacks import ModelCheckpoint, ProgbarLogger

class TakZeroNetwork():
	"""docstring for TakZeroNetwork"""
	def __init__(self):
		self.input_layer = Input(shape=(8, 5, 5, 64))
		#Level 1: Board Snapshot at T=0
		#Level 2: Board Snapshot at T=-1
		#Level 3: Board Snapshot at T=-2
		#Level 4: Board Snapshot at T=-3
		#Level 5: Board Snapshot at T=-4
		#Level 6: Board Snapshot at T=-5
		#Level 7: White Turn
		#Level 8: Black Turn

		self.kernel_level_1 = 3
		self.kernel_level_2 = 1

		self.features_1 = 256
		self.features_2 = 12
		self.features_3 = 1

		self.policy_output_size = 1575
		self.value_output_size = 1

		self.residual_blocks=10
		self.weights_save = "zero_{}".format(self.residual_blocks)
		self.network = None
		self.model = None
		self.number_of_samples = 64
		self.train_batch_size = 64
		self.validate_batch_size = 32
		self.epochs = 10

		self.opt = keras.optimizers.Nadam(lr=0.01, beta_1=0.9, beta_2=0.999, epsilon=1e-08, schedule_decay=0.004)

	def generate_network(self):
		#Add Convlutional Block
		y = Dense(15)(self.input_layer)
		y = Conv3D(self.features_1, self.kernel_level_1, padding='same', data_format='channels_first')(y)
		y = BatchNormalization()(y)
		activation = Activation('relu')(y)

		#Add Residue Blocks
		for i in range(self.residual_blocks):
			y = Conv3D(self.features_1, self.kernel_level_1, padding='same', data_format='channels_first')(activation)
			y = BatchNormalization()(y)
			y = Activation('relu')(y)
			y = Conv3D(self.features_1, self.kernel_level_1, padding='same', data_format='channels_first')(y)
			y = BatchNormalization()(y)
			y = keras.layers.add([activation, y])
			activation = Activation('relu')(y)

		#Add Policy Head
		#Probabilities for the move indexs
		y = Conv3D(self.features_2, self.kernel_level_2, padding='same', data_format='channels_first')(activation)
		y = BatchNormalization()(y)
		y = Activation('relu')(y)
		y = Flatten()(y)
		policy_out = Dense(self.policy_output_size, activation='sigmoid')(y)

		#Add Value Head
		#This is who won the game
		y = Conv3D(self.features_3, self.kernel_level_2, padding='same', data_format='channels_first')(activation)
		y = BatchNormalization()(y)
		y = Activation('relu')(y)
		y = Dense(self.features_1)(y)
		y = Activation('relu')(y)
		y = Flatten()(y)
		y = Dense(self.value_output_size)(y)
		value_out = Activation('tanh')(y)

		self.model = Model(inputs=[self.input_layer], outputs=[policy_out, value_out])
		
		self.load_weights()
		self.model.compile(loss='mean_squared_error', optimizer=self.opt, metrics=['accuracy'])
		#self.model.summary()

	def load_weights(self):
		if not os.path.exists(self.weights_save):
			os.makedirs(self.weights_save)

		#Save Config
		with open(os.path.join(os.getcwd(), self.weights_save, "model.json"), "w") as f:
			f.write(self.model.to_json())

		#Check for new network
		r = requests.get("https://zero.generalzero.org/newest_network")
		if r.status_code == 200:
			new_net = r.text
			self.network = new_net

			#Download new network
			if not os.path.exists(os.path.join(os.getcwd(), self.weights_save, new_net)):
				r = requests.get("https://zero.generalzero.org/networks/{}".format(new_net), stream=True)
				with open(new_net, 'wb') as fd:
					for chunk in r.iter_content(chunk_size=128):
						fd.write(chunk)
		else:
			#Setup Model
			if os.path.exists(os.path.join(os.getcwd(), self.weights_save, "best.hdf5")):
				print("Loading previous weights file best.hd5f")
				self.model.load_weights(os.path.join(os.getcwd(), self.weights_save, "best.hdf5"))
			else:
				training_files = [filename for filename in os.listdir(os.path.join(os.getcwd(), self.weights_save)) if filename.endswith(".hdf5")]
				if len(training_files) != 0:
					training_files = sorted(training_files)
					print("Loading previous weights file " + training_files[-1])
					self.network = training_files[-1]
					self.model.load_weights(os.path.join(os.getcwd(), self.weights_save, training_files[-1]))

		self.network = os.path.splitext(self.network)[0]


	def train(self, training_generator):
		#Make generator to return data from training file
		callback1 = ModelCheckpoint(os.path.join(os.getcwd(), self.weights_save, "best.hdf5"), monitor='val_dense_2_acc', verbose=2, save_best_only=True, mode='max')
		#callback2 = keras.callbacks.TensorBoard(log_dir=os.path.join(os.getcwd(), self.weights_save), histogram_freq=0, write_graph=True, write_images=True)

		history = self.model.fit_generator(training_generator, self.train_batch_size, epochs=self.epochs, callbacks=[callback1], validation_data=training_generator, validation_steps=self.validate_batch_size, verbose=1)

	def set_epoch(self, file_names):
		count = 0
		for file_name in file_names:
		#print("Getting Training data from {}".format(file_name))

			with h5py.File(os.path.join(os.getcwd(), "best_10", file_name), 'r') as hf:
				y_train_2 = hf["winner"][:]
				count += y_train_2.shape[0]

		self.epochs = (count / self.number_of_samples) // (15 + self.train_batch_size + self.validate_batch_size)
		print("Count {} Epochs {}".format(count, self.epochs))

	def training_files_generator(self, file_names):
		print("Start Training Generator")

		all_x_train   = None
		all_y_train_1 = None
		all_y_train_2 = None

		left_overs = False
		start_index = 0
		end_index = 0
		left_over_size = 0

		for file_name in file_names:
			#print("Getting Training data from {}".format(file_name))

			with h5py.File(os.path.join(os.getcwd(), "best_10", file_name), 'r') as hf:
				x_train   = hf["x_train"][:]
				y_train_1 = hf["y_train"][:]
				y_train_2 = hf["winner"][:]
				print(x_train.shape)

				#Shuffle data randomly but equally
				seed = np.random.randint(2**31)

				x_random = np.random.RandomState(seed)
				y_random_1 = np.random.RandomState(seed)
				y_random_2 = np.random.RandomState(seed)

				x_random.shuffle(x_train)
				y_random_1.shuffle(y_train_1)
				y_random_2.shuffle(y_train_2)

				#With New file Reset sizes
				array_size = x_train.shape[0]
				start_index = 0
				end_index = 0

				while (end_index + self.number_of_samples) < array_size:
					#Update indexes
					start_index = end_index
					end_index = start_index + self.number_of_samples - left_over_size
					left_over_size = 0

					#print("Start_index: {}, End_index: {}, Array_size: {}".format(start_index, start_index + self.number_of_samples, array_size))

					#Set Return Values
					if left_overs == True:
						all_x_train = np.concatenate((all_x_train, x_train[start_index:end_index]), axis=0)
						all_y_train_1 = np.concatenate((all_y_train_1, y_train_1[start_index:end_index]), axis=0)
						all_y_train_2 = np.concatenate((all_y_train_2, y_train_2[start_index:end_index]), axis=0)
						left_overs = False

					else:
						all_x_train   = x_train[start_index:end_index]
						all_y_train_1 = y_train_1[start_index:end_index]
						all_y_train_2 = y_train_2[start_index:end_index]

					#print("Returning (x_shape: {})".format(all_x_train.shape))

					yield (all_x_train, [all_y_train_1, all_y_train_2])

				#Check for leftover data and add to all_trains
				if array_size > end_index:
					all_x_train   = x_train[end_index:array_size]
					all_y_train_1 = y_train_1[end_index:array_size]
					all_y_train_2 = y_train_2[end_index:array_size]
					left_over_size = array_size - end_index
					left_overs = True

	def predict(self, x_input, batch_size=1):
		#print(x_input.shape)
		ret = self.model.predict(x_input, batch_size=batch_size)
		#print(ret[0][0].shape)
		#print(ret[1][0].shape)
		return ret[0][0], ret[1][0]

if __name__ == '__main__':
	ai = TakZeroNetwork()

	ai.generate_network()

	training_files = [filename for filename in os.listdir(os.path.join(os.getcwd(), "best_10")) if filename.startswith("train")]
	random.shuffle(training_files)

	ai.set_epoch(training_files)

	ai.train(ai.training_files_generator(training_files))