import unittest

import json

from game import Game, Player
from utils import random_move

class TestConnection(object):
	def __init__(self, game):
		self.moves = None
		self.trade_offer = None
		self.player = Player(self, 'test_player1', game)

	def on_message(self, message):
		pass

	def write_message(self, message):
		message = json.loads(message)

		if message['type'] == 'moves':
			self.moves = message['moves']
		if message['type'] == 'trade_offer':
			self.trade_offer = message['trade']

class TestGame(Game):
	def __init__(self, max_players=2):
		super().__init__()
		self.max_players = max_players

class GameTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.game = TestGame()

		cls.c1 = TestConnection(cls.game)
		cls.c2 = TestConnection(cls.game)
		cls.player1 = cls.c1.player
		cls.player2 = cls.c2.player

	def test_1_started(self):
		self.assertFalse(self.game.started)
		# Add first player - shouldn't start
		self.game.add_player(self.player1)
		self.assertFalse(self.game.started)
		# Ready first player - shouldn't start
		self.game.set_ready(self.player1)
		self.assertFalse(self.game.started)
		# Add 2nd player - shouldn't start
		self.game.add_player(self.player2)
		self.assertFalse(self.game.started)
		# Ready 2nd player - should start
		self.game.set_ready(self.player2)
		self.assertTrue(self.game.started)

		self.assertTrue(self.c1.moves or self.c2.moves)

	def test_2_placement(self):
		conn = self.c1 if self.c1.moves else self.c2

		self.game.recv_move(conn.player, random_move(conn.moves))
		# Make sure we built a building
		self.assertEqual(conn.player.num_buildings, 1)
		self.assertEqual(conn.player.longest_road, 0)

		self.game.recv_move(conn.player, random_move(conn.moves))
		# Make sure we built a road
		self.assertEqual(conn.player.longest_road, 1)
		action = self.game.action_number

		# This move should be invalid, make sure nothing changes
		self.game.recv_move(conn.player, random_move(conn.moves))
		self.assertEqual(action, self.game.action_number)
		self.assertEqual(conn.player.num_buildings, 1)
		self.assertEqual(conn.player.longest_road, 1)

		conn.moves = None

	def test_3_placement2(self):
		conn = self.c1 if self.c1.moves else self.c2

		# Do all starting moves. Should build 2 houses and 2 roads
		self.game.recv_move(conn.player, random_move(conn.moves))
		self.game.recv_move(conn.player, random_move(conn.moves))
		self.game.recv_move(conn.player, random_move(conn.moves))
		self.game.recv_move(conn.player, random_move(conn.moves))
		self.assertEqual(conn.player.num_buildings, 2)
		self.assertIn(conn.player.longest_road, (1,2))

		# Check no more valid moves
		action = self.game.action_number
		self.game.recv_move(conn.player, random_move(conn.moves))
		self.game.recv_move(conn.player, random_move(conn.moves))
		self.game.recv_move(conn.player, random_move(conn.moves))
		self.assertEqual(action, self.game.action_number)

		conn.moves = None

	def test_4_cant_trade_yet(self):
		self.game.recv_trade(self.player1, {
			'give': { 'ore': 1 },
			'want': { 'wood': 1 },
			'player_id': None,
			'turn': self.game.action_number,
		})

		self.assertFalse(self.c2.trade_offer)

	def test_5_finish_placement(self):
		conn = self.c1 if self.c1.moves else self.c2

		self.game.recv_move(conn.player, random_move(conn.moves))
		self.game.recv_move(conn.player, random_move(conn.moves))
		self.assertEqual(conn.player.num_buildings, 2)
		self.assertIn(conn.player.longest_road, (1,2))


		self.assertEqual(random_move(conn.moves)['type'], 'roll')
		self.game.recv_move(conn.player, random_move(conn.moves))

	def test_6_can_trade(self):
		self.game.recv_trade(self.player1, {
			'give': self.player1.cards,
			'want': self.player2.cards,
			'player_id': self.player2.id,
			'turn': self.game.action_number,
		})
		self.assertTrue(self.c2.trade_offer)

	def test_7_trade(self):
		self.player1.cards['wheat'] += 1
		self.player2.cards['ore'] += 1

		p1_cards = dict(self.player1.cards)
		p2_cards = dict(self.player2.cards)
		action = self.game.action_number

		self.game.recv_trade(self.player1, {
			'give': {'wheat': 1},
			'want': {'ore': 1},
			'player_id': self.player2.id,
			'turn': self.game.action_number,
		})
		self.game.recv_trade(self.player2, {
			'give': {'ore': 1},
			'want': {'wheat': 1},
			'player_id': self.player1.id,
			'turn': self.game.action_number,
		})

		self.assertNotEqual(action, self.game.action_number)
		self.assertEqual(self.player2.cards['wheat'], p2_cards['wheat']+1)
		self.assertEqual(self.player2.cards['ore'], p2_cards['ore']-1)
		self.assertEqual(self.player1.cards['ore'], p1_cards['ore']+1)
		self.assertEqual(self.player1.cards['wheat'], p1_cards['wheat']-1)

if __name__ == '__main__':
	unittest.main()