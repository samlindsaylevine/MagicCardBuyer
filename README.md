# MagicCardBuyer

A hand-rolled tool for automatically making optimal Magic the Gathering purchases.

The problem statement is that we have a list of named cards for the hobby game Magic the Gathering, and we want to
purchase them for as little as possible. Assuming a minimum order is required to purchase from each individual store,
this tool calculates the optimal buy order from among any number of stores, and adds the items to your shopping cart so
that your order is ready to place.

Beyond being a helpful tool for a hobby, this also turned out to be a somewhat interesting and not immediately obvious
computer science problem. With a little cleverness, it could be reduced to an optimization problem in mixed-integer
linear programming. See `BuyOptimizer.kt` for more details. We're using the Google OR Tools library to perform the
mathematics of this optimization problem.

If you're building a practice deck, you can also define a maximum cost you are willing to pay, and then get the output
of all the cards that are "too expensive" to the file `tooExpensive`. Then you can make proxies to playtest with until
you are ready to buy the real cards. This repo used to have a proxies.py script; it was based on magiccards.info which
has since gone under. Furthermore, since it built an HTML page, it had a problem with scaling differently on different
printers. Consider using other existing utilities such as https://mtgprint.net/ to generate PDFs with card images.

To run the tool:

* A JDK is required.
* Right now, you define which cards you want to purchase inside `MagicCardBuyer`, possibly using the helper
  utilities `DraftSet` or `Rares`.
* The tool readsprints logging information to standard error, and outputs "too expensive" cards to the
  file `tooExpensive`.

To run the tests:

* `./gradlew check`