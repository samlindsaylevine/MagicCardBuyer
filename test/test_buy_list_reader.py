import unittest
from io import StringIO
from magiccardbuyer.buy_list_reader import *

class TestBuyListReader(unittest.TestCase):
	def test_empty(self):
		input = StringIO()

		result = BuyListReader().read(input)

		self.assertEqual(result, [])

	def test_single_card(self):
		input = StringIO("Shivan Dragon")

		result = BuyListReader().read(input)

		expected = [CardToBuy("Shivan Dragon", 1, None)]
		self.assertEqual(result, expected)

	def test_multiple_cards(self):
		input = StringIO("""Shivan Dragon
							Swords to Plowshares
							Serra Angel""")

		result = BuyListReader().read(input)

		expected = [CardToBuy("Shivan Dragon", 1, None),
			CardToBuy("Swords to Plowshares", 1, None),
			CardToBuy("Serra Angel", 1, None)]
		self.assertEqual(result, expected)

	def test_empty_lines(self):
		input = StringIO("""Shivan Dragon



							Serra Angel""")

		result = BuyListReader().read(input)

		expected = [CardToBuy("Shivan Dragon", 1, None),
			CardToBuy("Serra Angel", 1, None)]
		self.assertEqual(result, expected)


	def test_specifying_set(self):
		input = StringIO("""Revised:
							Shivan Dragon""")

		result = BuyListReader().read(input)

		expected = [CardToBuy("Shivan Dragon", 1, "Revised")]
		self.assertEqual(result, expected)

	def test_specifying_quantities(self):
		input = StringIO("""15 Shivan Dragon
							122 Giant Growth""")

		result = BuyListReader().read(input)

		expected = [CardToBuy("Shivan Dragon", 15, None),
			CardToBuy("Giant Growth", 122, None)]
		self.assertEqual(result, expected)

	def test_specifying_different_sets(self):
		input = StringIO("""Revised:
							4 Giant Growth
							Ice Age:
							4 Giant Growth""")

		result = BuyListReader().read(input)

		expected = [CardToBuy("Giant Growth", 4, "Revised"),
			CardToBuy("Giant Growth", 4, "Ice Age")]
		self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()