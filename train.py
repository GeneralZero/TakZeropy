#!/usr/bin/python

from keras.models import Model
from keras.layers import Input, Dense
from keras.layers import Conv3D
from keras.layers import BatchNormalization
from keras.layers import Activation

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

		self.features_1 = 1024
		self.features_2 = 12
		self.features_3 = 1

		self.policy_output_size = 1575
		self.value_output_size = 1

		self.residual_blocks=17

	def generate_network(self):
		#Add Convlutional Block
		y = Conv3D(self.features_1, self.kernel_level_1, padding='same', data_format='channels_last')(input_layer)
		y = BatchNormalization()(y)
		activation = Activation('relu')(y)

		#Add Residue Blocks
		for i in range(self.residual_blocks):
			y = Conv3D(self.features_1, self.kernel_level_1, padding='same')(activation)
			y = BatchNormalization()(y)
			y = Activation('relu')(y)
			y = Conv3D(self.features, self.kernel_level_1, padding='same')(y)
			y = BatchNormalization()(y)
			y = keras.layers.add([activation, y])
			activation = Activation('relu')(y)

		#Add Policy Head
		#Probabilities for the move indexs
		y = Conv3D(self.features_2, self.kernel_level_2, padding='same')(activation)
		y = BatchNormalization()(y)
		y = Activation('relu')(y)
		policy_out = Dense(self.policy_output_size, activation='sigmoid')(y)

		#Add Value Head
		#This is who won the game
		y = Conv3D(self.features_3, self.kernel_level_2, padding='same')(activation)
		y = BatchNormalization()(y)
		y = Activation('relu')(y)
		y = Dense(self.features_1)(y)
		y = Activation('relu')(y)
		y = Dense(self.value_output_size)(y)
		value_out = Activation('tanh')(y)

		model = Model(inputs=[input_data], outputs=[policy_out, value_out])
