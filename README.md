# MagicCardBuyer
A hand-rolled tool for automatically making optimal Magic the Gathering purchases.

The problem statement is that we have a list of named cards for the hobby game Magic the Gathering, and we want to purchase them for as little as possible. Assuming a minimum order is required to purchase from each individual store, this tool calculates the optimal buy order from among any number of stores, and adds the items to your shopping cart so that your order is ready to place.

If you're building a practice deck, you can also define a maximum cost you are willing to pay, and then get the output of all the cards that are "too expensive" on standard out. Then you can make proxies to playtest with until you are ready to buy the real cards.

This repo used to have a proxies.py script; it was based on magiccards.info which has since gone under. Furthermore, since it built an HTML page, it had a problem with scaling differently on different printers. Consider using other existing utilities such as http://magiccardprices.info/PlaytestUtility or http://www.mtgpress.net/ to generate PDFs with card images.

To run the tool:
* Python 3.7 or later is required.
* `pip install -r requirements.txt` to install the dependencies.
* The tool reads from standard input, prints logging information to standard error, and outputs "too expensive" cards to standard out.
** So, a sample invocation might look like `cat ToBuy | python magiccardbuyer.py > tooExpensive`

To run the tests:
* `python -m unittest discover -v`