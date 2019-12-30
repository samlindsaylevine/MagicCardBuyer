
# MagicCardBuyer
A hand-rolled tool for automatically making optimal Magic the Gathering purchases.

The problem statement is that we have a list of named cards for the hobby game Magic the Gathering, and we want to purchase them for as little as possible. Assuming a minimum order is required to purchase from each individual store, this tool calculates the optimal buy order from among any number of stores, and adds the items to your shopping cart so that your order is ready to place.

Beyond being a helpful tool for a hobby, this also turned out to be a somewhat interesting and not immediately obvious computer science problem. With a little cleverness, it could be reduced to an optimization problem in mixed-integer linear programming. See `buy_optimizer.py` for more details. We're using the Google OR Tools library to perform the mathematics of this optimization problem.

If you're building a practice deck, you can also define a maximum cost you are willing to pay, and then get the output of all the cards that are "too expensive" on standard out. Then you can make proxies to playtest with until you are ready to buy the real cards. This repo used to have a proxies.py script; it was based on magiccards.info which has since gone under. Furthermore, since it built an HTML page, it had a problem with scaling differently on different printers. Consider using other existing utilities such as http://magiccardprices.info/PlaytestUtility or http://www.mtgpress.net/ to generate PDFs with card images.

# Running the tool
* Python 3.7 or later is required.
  * The instructions below assume that your main Python version is 3; in some cases, such as if you have installed Python 3 separately on Mac OS, you may need to use `pip3` and`python3	` instead of `pip` and python.
* `pip install -r requirements.txt` to install the dependencies.
* You will need a `config.ini` file. A `config.ini.example` is provided. Options such as your maximum card cost (if you want one) and whether to cache price lookups are included here.
* The tool reads from standard input, prints logging information to standard error, and outputs "too expensive" cards to standard out.
  * So, a sample invocation might look like `cat ToBuy | python magiccardbuyer.py > tooExpensive`

# Buying from TCG Player
Right now the buyer purchases only from vendors on tcgplayer.com (although this is a site of possible future extendability). It goes as far as putting the items into your shopping cart, and you get to do the checkout yourself for safety.

In order to be able to add items to your shopping cart, you need to be logged into TCG Player in your primary browser. MagicCardBuyer will read your cookies from on disk and make the purchase requests as you.

If you are not logged in via your browser, it will prompt you to do so.

If you have multiple Chrome profiles, you will need to be logged in on the primary profile in order for the cookies to be found.

# Caching web requests
Looking up prices can be slow, so the `config.ini` provides an option to cache these requests between runs. If set to `False`, the cache will be wiped.

# Unit tests

A few unit tests are included, particularly of the price-optimizing logic. There aren't any meaningful integration tests. This does allow the tests to be run fully in isolation, but does mean that there is not much protection against TCG Player changing its front end or web API. I expect I will just run into that when I execute the script.

To run the tests:
* `python -m unittest discover -v`