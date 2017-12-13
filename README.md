# What

A Tak AI program with no human provided knowledge. Using MCTS (but without
Monte Carlo playouts) and a deep residual convolutional neural network stack.

This is a fairly faithful interpretation of the system described
in the Alpha Go Zero paper "Mastering the Game of Go without Human Knowledge".

# Gimme the weights

Recomputing the AlphaGo Zero weights will take about 1700 years on commodity
hardware, see for example: http://computer-go.org/pipermail/computer-go/2017-October/010307.html

One reason for publishing this program is that we are running a public,
distributed effort to repeat the work. Working together, and especially
when starting on a smaller scale, it will take less than 1700 years to get
a good network (which you can feed into this program, suddenly making it strong).

# I need help

You need a PC with a internet connection. Thats it. GPU support is in development.

## Windows

Head to the Github releases page at https://github.com/GeneralZero/TakZero/releases,
download the latest release and launch TakZero.exe. It will connect to
the server automatically and do its work in the background, uploading results
after each game. You can just close the window to stop it.

## macOS and Linux

Install the requirements from requirements.txt and run `python MonteCarlo.py`.

# I just want to play right now

This project is in its early stages and will update with information later.


# Training

## From Games to input data

## Training data format

## Running the training

# Todo

# License

The code is released under the GPLv3 or later.
