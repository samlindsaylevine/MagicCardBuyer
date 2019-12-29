import unittest
from unittest.mock import patch, call

from magiccardbuyer.tcgplayer_interface import *


class TestTcgPlayerInterface(unittest.TestCase):

    @patch.object(WebpageReader, 'read')
    def test_find_options_specifying_set(self, mock_read):
        bolt = Card(name="Lightning Bolt", setName="Masters 25")
        mock_read.side_effect = [self.file_contents("test/webpages/mm25boltsearch.html"),
                                 self.file_contents("test/webpages/mm25boltpricetable.html")]

        purchase_options = self.interface().find_options(bolt)

        mock_read.assert_has_calls([call("https://shop.tcgplayer.com/magic/masters-25?ProductName=lightning+bolt"),
                                    call(
                                        "https://shop.tcgplayer.com/productcatalog/product/getpricetable?pageSize=50"
                                        "&productId=161480&gameName=magic")])

        self.assertEqual(len(purchase_options), 41)
        first_option = purchase_options[0]
        # First one in the table.
        self.assertEqual(first_option.vendor, "Capital City Gaming")
        self.assertEqual(first_option.price, 220)
        self.assertEqual(first_option.availableQuantity, 3)
        self.assertEqual(first_option.minimum_purchase, 500)

    @patch.object(WebpageReader, 'read')
    def test_find_options_does_not_match_on_name_substring(self, mock_read):
        light = Card(name="Light", setName="Masters 25")
        mock_read.side_effect = [self.file_contents("test/webpages/mm25boltsearch.html"),
                                 self.file_contents("test/webpages/mm25boltpricetable.html")]

        purchase_options = self.interface().find_options(light)

        self.assertEqual(len(purchase_options), 0)

    @staticmethod
    def file_contents(file_path):
        with open(file_path, 'r') as file:
            return file.read()

    @staticmethod
    def interface():
        interface = TcgPlayerInterface(WebpageReader(True), cookies=False)
        interface.verbose = False
        return interface


if __name__ == '__main__':
    unittest.main()
