import unittest
from magiccardbuyer.webpage_reader import WebpageReader
from magiccardbuyer.tcgplayer_interface import *
from unittest.mock import patch, call

class TestTcgPlayerInterface(unittest.TestCase):

	@patch.object(WebpageReader, 'read')
	def test_find_options_specifying_set(self, mock_read):
		bolt = Card(name = "Lightning Bolt", setName = "Masters 25")
		mock_read.side_effect = [ self.file_contents("test/webpages/mm25boltsearch.html"),
			self.file_contents("test/webpages/mm25boltpricetable.html") ]

		options = self.interface().find_options(bolt)

		mock_read.assert_has_calls([call("https://shop.tcgplayer.com/magic/masters-25?ProductName=lightning+bolt"),
			call("https://shop.tcgplayer.com/productcatalog/product/getpricetable?pageSize=50&productId=161480&gameName=magic")])

		self.assertEqual(len(options), 24)
		first_option = options[0]
		# First one with free shipping in the table.
		self.assertEqual(first_option.vendor, "MTG Rock")
		self.assertEqual(first_option.price, 302)
		self.assertEqual(first_option.availableQuantity, 1)
		self.assertEqual(first_option.minimumPurchase, 200)

	def file_contents(self, file_path):
		with open(file_path, 'r') as file:
			return file.read()

	def interface(self):
		interface = TcgPlayerInterface()
		interface.verbose = False
		return interface

if __name__ == '__main__':
    unittest.main()