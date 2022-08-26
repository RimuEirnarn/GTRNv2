from lib import Player, SinglePlayer, Bot

level = 5

x = Bot("Bot-0", level)
you = Player("Archaent")

game = SinglePlayer(x, you, level=5)
game.start()
