from santorinai.tester import Tester
from santorinai.player_examples.random_player import RandomPlayer
from santorinai.player_examples.first_choice_player import FirstChoicePlayer
from santorinai.player_examples.basic_player import BasicPlayer
from santorinai.player_examples.dpc_ai_1 import PlayerDPC1

# Init the tester
tester = Tester()
tester.verbose_level = 2  # 0: no output, 1: Each game results, 2: Each move summary
tester.delay_between_moves = 0.5  # Delay between each move in seconds
tester.display_board = True  # Display a graphical view of the board in a window

# Init the players
my_player = FirstChoicePlayer(1)
dpc1_player = PlayerDPC1(2)
basic_player = BasicPlayer(1)
random_payer = RandomPlayer(2)

# Play 100 games
tester.play_1v1(dpc1_player, basic_player, nb_games=100)
