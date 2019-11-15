import unittest
from io import StringIO
from magiccardbuyer.buy_list_reader import *


class TestBuyListReader(unittest.TestCase):
    def test_empty(self):
        input_stream = StringIO()

        result = BuyListReader().read(input_stream)

        self.assertEqual(result, [])

    def test_single_card(self):
        input_stream = StringIO("Shivan Dragon")

        result = BuyListReader().read(input_stream)

        expected = [CardToBuy(Card("Shivan Dragon", None), 1)]
        self.assertEqual(result, expected)

    def test_multiple_cards(self):
        input_steram = StringIO("""Shivan Dragon
                                   Swords to Plowshares
                                   Serra Angel""")

        result = BuyListReader().read(input_steram)

        expected = [CardToBuy(Card("Shivan Dragon", None), 1),
                    CardToBuy(Card("Swords to Plowshares", None), 1),
                    CardToBuy(Card("Serra Angel", None), 1)]
        self.assertEqual(result, expected)

    def test_empty_lines(self):
        input_stream = StringIO("""Shivan Dragon



                            Serra Angel""")

        result = BuyListReader().read(input_stream)

        expected = [CardToBuy(Card("Shivan Dragon", None), 1),
                    CardToBuy(Card("Serra Angel", None), 1)]
        self.assertEqual(result, expected)

    def test_specifying_set(self):
        input_stream = StringIO("""Revised:
                                   Shivan Dragon""")

        result = BuyListReader().read(input_stream)

        expected = [CardToBuy(Card("Shivan Dragon", "Revised"), 1)]
        self.assertEqual(result, expected)

    def test_specifying_quantities(self):
        input_stream = StringIO("""15 Shivan Dragon
                                   122 Giant Growth""")

        result = BuyListReader().read(input_stream)

        expected = [CardToBuy(Card("Shivan Dragon", None), 15),
                    CardToBuy(Card("Giant Growth", None), 122)]
        self.assertEqual(result, expected)

    def test_specifying_different_sets(self):
        input_stream = StringIO("""Revised:
                                   4 Giant Growth
                                   Ice Age:
                                   4 Giant Growth""")

        result = BuyListReader().read(input_stream)

        expected = [CardToBuy(Card("Giant Growth", "Revised"), 4),
                    CardToBuy(Card("Giant Growth", "Ice Age"), 4)]
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
