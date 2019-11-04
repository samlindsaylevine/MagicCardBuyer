import unittest

from magiccardbuyer.buy_optimizer import *


class TestBuyOptimizer(unittest.TestCase):
    def test_single_vendor(self):
        options = [PurchaseOption("apple", "Merchant1", 1, 30),
                   PurchaseOption("banana", "Merchant1", 1, 40),
                   PurchaseOption("coconut", "Merchant1", 1, 50)]
        problem = VendorProblem(minimumRequiredPurchase=100,
                                goodQuantitiesSought={'apple': 1, 'banana': 1, 'coconut': 1},
                                purchaseOptions=options)

        solution = BuyOptimizer().solve(problem)

        expected = VendorSolution(totalCost=120,
                                  purchasesToMake=[PurchaseToMake(1, option) for option in options])
        self.assertEqual(solution, expected)

    def test_two_vendors(self):
        options = [PurchaseOption("apple", "Merchant1", 100, 112),
                   PurchaseOption("banana", "Merchant1", 100, 95),
                   PurchaseOption("coconut", "Merchant1", 15, 9),
                   PurchaseOption("date", "Merchant1", 1, 1000),
                   PurchaseOption("apple", "Merchant2", 1, 100000),
                   PurchaseOption("banana", "Merchant2", 1, 15),
                   PurchaseOption("coconut", "Merchant2", 1, 10),
                   PurchaseOption("date", "Merchant2", 1, 199)]
        problem = VendorProblem(minimumRequiredPurchase=200,
                                goodQuantitiesSought={'apple': 1, 'banana': 1, 'coconut': 1, 'date': 1},
                                purchaseOptions=options)

        solution = BuyOptimizer().solve(problem)

        # Note that Merchant1's price on coconuts is smaller, but we buy from Merchant2 to
        # reach the minimum required threshold.
        expected = VendorSolution(totalCost=112 + 95 + 10 + 199,
                                  purchasesToMake=[PurchaseToMake(1, PurchaseOption("apple", "Merchant1", 100, 112)),
                                                   PurchaseToMake(1, PurchaseOption("banana", "Merchant1", 100, 95)),
                                                   PurchaseToMake(1, PurchaseOption("coconut", "Merchant2", 1, 10)),
                                                   PurchaseToMake(1, PurchaseOption("date", "Merchant2", 1, 199))])
        self.assertEqual(solution, expected)

    def test_vendor_that_cannot_reach_minimum(self):
        options = [PurchaseOption("apple", "Merchant1", 100, 112),
                   PurchaseOption("banana", "Merchant1", 100, 95),
                   PurchaseOption("coconut", "Merchant1", 15, 9),
                   PurchaseOption("date", "Merchant1", 1, 1000),
                   PurchaseOption("apple", "Merchant2", 1, 100000),
                   PurchaseOption("banana", "Merchant2", 1, 15),
                   PurchaseOption("coconut", "Merchant2", 1, 10),
                   PurchaseOption("date", "Merchant2", 1, 199),
                   PurchaseOption("apple", "Merchant3", 1, 1)]
        problem = VendorProblem(minimumRequiredPurchase=200,
                                goodQuantitiesSought={'apple': 1, 'banana': 1, 'coconut': 1, 'date': 1},
                                purchaseOptions=options)

        solution = BuyOptimizer().solve(problem)

        # Note that we don't buy from Merchant3 because we can't reach a minimum threshold for
        # them.
        expected = VendorSolution(totalCost=112 + 95 + 10 + 199,
                                  purchasesToMake=[PurchaseToMake(1, PurchaseOption("apple", "Merchant1", 100, 112)),
                                                   PurchaseToMake(1, PurchaseOption("banana", "Merchant1", 100, 95)),
                                                   PurchaseToMake(1, PurchaseOption("coconut", "Merchant2", 1, 10)),
                                                   PurchaseToMake(1, PurchaseOption("date", "Merchant2", 1, 199))])
        self.assertEqual(solution, expected)

    def test_a_good_split_across_multiple_vendors(self):
        options = [PurchaseOption("apple", "Merchant1", 100, 112),
                   PurchaseOption("apple", "Merchant2", 4, 2),
                   PurchaseOption("apple", "Merchant3", 5, 3),
                   PurchaseOption("apple", "Merchant4", 6, 4)]
        problem = VendorProblem(minimumRequiredPurchase=1,
                                goodQuantitiesSought={'apple': 10},
                                purchaseOptions=options)

        solution = BuyOptimizer().solve(problem)

        # We skip Merchant1, who could fulfil the order on their own, as too expensive; and buy
        # from the other merchants.
        expected = VendorSolution(totalCost=(4 * 2) + (5 * 3) + (1 * 4),
                                  purchasesToMake=[PurchaseToMake(4, PurchaseOption("apple", "Merchant2", 4, 2)),
                                                   PurchaseToMake(5, PurchaseOption("apple", "Merchant3", 5, 3)),
                                                   PurchaseToMake(1, PurchaseOption("apple", "Merchant4", 6, 4))])
        self.assertEqual(solution, expected)

    def test_a_good_is_sought_with_no_purchase_options(self):
        options = [PurchaseOption("apple", "Merchant1", 100, 112)]
        problem = VendorProblem(minimumRequiredPurchase=1,
                                goodQuantitiesSought={'banana': 10},
                                purchaseOptions=options)

        self.assertRaises(UnsolvableError, BuyOptimizer().solve, problem)

    def test_cannot_make_viable_purchase_because_of_minimum(self):
        options = [PurchaseOption("apple", "Merchant1", 100, 5),
                   PurchaseOption("banana", "Merchant1", 100, 10),
                   PurchaseOption("apple", "Merchant2", 1, 20),
                   PurchaseOption("banana", "Merchant2", 1, 30)]
        problem = VendorProblem(minimumRequiredPurchase=200,
                                goodQuantitiesSought={'apple': 1, 'banana': 1},
                                purchaseOptions=options)

        self.assertRaises(UnsolvableError, BuyOptimizer().solve, problem)

    def test_many_goods_and_many_vendors(self):
        num_goods = 1000
        num_vendors = 20

        # The prices for each good vary across the vendors, with each good costing
        # 100 at a single individual vendor (and slightly more at the others).
        def options_for_good(good_number): return [PurchaseOption(f"good{good_number}",
                                                                  f"vendor{vendor_number}",
                                                                  1,
                                                                  (good_number + vendor_number) % num_vendors + 100) for
                                                   vendor_number in range(num_vendors)]

        purchase_options = ([option for goodNumber in range(num_goods) for option in options_for_good(goodNumber)]
                            + [PurchaseOption("good17", "IrrelevantVendor", 1, 12),
                               PurchaseOption("good24", "IrrelevantVendor", 1, 1)])
        good_quantities_sought = {f"good{number}": 1 for number in range(num_goods)}
        problem = VendorProblem(minimumRequiredPurchase=200,
                                goodQuantitiesSought=good_quantities_sought,
                                purchaseOptions=purchase_options)

        solution = BuyOptimizer().solve(problem)

        # Should have found the cheapest solution - minimum price for each good (except the
        # two that IrrelevantVendor has, which we can't purchase because of the minimum
        # required threshold.)
        self.assertEqual(solution.totalCost, 100 * num_goods)
        purchases_from_irrelevant_vendor = [purchase for purchase in solution.purchasesToMake if
                                            purchase.option.vendor == "IrrelevantVendor"]
        self.assertEqual(purchases_from_irrelevant_vendor, [])

    def test_good_is_a_dataclass(self):
        options = [PurchaseOption(Fish("carp", 10), "Merchant1", 1, 10),
                   PurchaseOption(Fish("carp", 20), "Merchant1", 1, 100),
                   PurchaseOption(Fish("sunfish", 10), "Merchant1", 1, 100),
                   PurchaseOption(Fish("sunfish", 20), "Merchant1", 1, 10),
                   PurchaseOption(Fish("carp", 10), "Merchant2", 1, 100),
                   PurchaseOption(Fish("carp", 20), "Merchant2", 1, 10),
                   PurchaseOption(Fish("sunfish", 10), "Merchant2", 1, 10),
                   PurchaseOption(Fish("sunfish", 20), "Merchant2", 1, 100)]
        problem = VendorProblem(minimumRequiredPurchase=1,
                                goodQuantitiesSought={Fish("carp", 10): 1, Fish("carp", 20): 1, Fish("sunfish", 10): 1,
                                                      Fish("sunfish", 20): 1},
                                purchaseOptions=options)

        solution = BuyOptimizer().solve(problem)

        expected = VendorSolution(totalCost=10 * 4,
                                  purchasesToMake=[
                                      PurchaseToMake(1, PurchaseOption(Fish("carp", 10), "Merchant1", 1, 10)),
                                      PurchaseToMake(1, PurchaseOption(Fish("sunfish", 20), "Merchant1", 1, 10)),
                                      PurchaseToMake(1, PurchaseOption(Fish("carp", 20), "Merchant2", 1, 10)),
                                      PurchaseToMake(1, PurchaseOption(Fish("sunfish", 10), "Merchant2", 1, 10))])
        self.assertEqual(solution, expected)


@dataclass(frozen=True)
class Fish:
    species: str
    weight: int


if __name__ == '__main__':
    unittest.main()
