# MagicCardBuyer
A hand-rolled tool for automatically making optimal Magic the Gathering purchases.

The current state of this tool is honestly a HUGE mess - I made it while learning Python and it shows. It's not even meaningfully tested! It is not reasonably usable by non-developers at this point, but I uploaded it here to have somewhere to store it.

The problem statement is that we have a list of named cards for the hobby game Magic the Gathering, and we want to purchase them for as little as possible. Assuming a fixed shipping and handling fee for each store, this tool calculates the optimal buy order from among any number of stores, and adds the items to your shopping cart so that your order is ready to place.

It's broken into: 

1) the MagicCardBuyer, which manages the overall process
2) BuyListReader, which parses the input text file of cards to buy
3) BidWicketInterface, the only currently implemented interface to a number of web stores - other interfaces can be simply designed and added
4) BuyOptimizer, which calculates the optimal set of stores to buy from.

I couldn't solve the math problem of how to make this calculation in an intelligent fashion, if each store we add adds a fixed shipping fee... and neither could the other people I asked. I resorted to a mostly brute-force greedy algorithm, that checks combinations of stores, and for each combination checks how much that order would cost.

If you're building a practice deck, you can also define a maximum cost you are willing to pay, and then use proxies to generate a HTML page full of images suitable for printing, until you are ready to buy the real cards.

Improvements:
Better configuration, no hardcoding username & password into BidWicketInterface (!!)
Integration with more sellers
Testing & cleanup
Better optimization algorithm
Switch from gross manual HTML parsing in BidWicketInterface to BeautifulSoup