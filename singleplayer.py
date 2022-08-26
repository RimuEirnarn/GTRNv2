from lib import Player, SinglePlayer, Bot

level = 5
try:
    name = input("Please input your name: ")
except KeyboardInterrupt:
    name = "Bill"

x = Bot("Bot-0", level)
you = Player(name)

game = SinglePlayer(x, you, level=5)
game.start()
