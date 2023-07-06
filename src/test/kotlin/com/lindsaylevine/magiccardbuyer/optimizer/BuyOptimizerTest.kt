package com.lindsaylevine.magiccardbuyer.optimizer

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.catchThrowable
import kotlin.test.Test

class BuyOptimizerTest {

    @Test
    fun `solve -- single vendor -- buys from that vendor`() {
        val options = listOf(
                SimplePurchaseOption("apple", "Merchant1", 1, 30),
                SimplePurchaseOption("banana", "Merchant1", 1, 40),
                SimplePurchaseOption("coconut", "Merchant1", 1, 50))
        val problem = VendorProblem(minimumRequiredPurchase = 100,
                goodQuantitiesSought = mapOf("apple" to 1, "banana" to 1, "coconut" to 1),
                purchaseOptions = options)

        val solution = BuyOptimizer().solve(problem)

        val expected = VendorSolution(purchasesToMake = options.map { PurchaseToMake(1, it) })
        assertThat(solution).isEqualTo(expected)
    }

    @Test
    fun `solve -- two vendors -- finds optimal solution`() {
        val options = listOf(
                SimplePurchaseOption("apple", "Merchant1", 100, 112),
                SimplePurchaseOption("banana", "Merchant1", 100, 95),
                SimplePurchaseOption("coconut", "Merchant1", 15, 9),
                SimplePurchaseOption("date", "Merchant1", 1, 1000),
                SimplePurchaseOption("apple", "Merchant2", 1, 100000),
                SimplePurchaseOption("banana", "Merchant2", 1, 15),
                SimplePurchaseOption("coconut", "Merchant2", 1, 10),
                SimplePurchaseOption("date", "Merchant2", 1, 199))
        val problem = VendorProblem(minimumRequiredPurchase = 200,
                goodQuantitiesSought = mapOf("apple" to 1, "banana" to 1, "coconut" to 1, "date" to 1),
                purchaseOptions = options)

        val solution = BuyOptimizer().solve(problem)

        // Note that Merchant1's price on coconuts is smaller, but we buy from Merchant2 to
        // reach the minimum required threshold.
        val expected = VendorSolution(purchasesToMake = listOf(
                PurchaseToMake(1, SimplePurchaseOption("apple", "Merchant1", 100, 112)),
                PurchaseToMake(1, SimplePurchaseOption("banana", "Merchant1", 100, 95)),
                PurchaseToMake(1, SimplePurchaseOption("coconut", "Merchant2", 1, 10)),
                PurchaseToMake(1, SimplePurchaseOption("date", "Merchant2", 1, 199))))
        assertThat(solution).isEqualTo(expected)
    }

    @Test
    fun `solve -- a vendor that cannot reach minimum -- is not purchased from`() {
        val options = listOf(
                SimplePurchaseOption("apple", "Merchant1", 100, 112),
                SimplePurchaseOption("banana", "Merchant1", 100, 95),
                SimplePurchaseOption("coconut", "Merchant1", 15, 9),
                SimplePurchaseOption("date", "Merchant1", 1, 1000),
                SimplePurchaseOption("apple", "Merchant2", 1, 100000),
                SimplePurchaseOption("banana", "Merchant2", 1, 15),
                SimplePurchaseOption("coconut", "Merchant2", 1, 10),
                SimplePurchaseOption("date", "Merchant2", 1, 199),
                SimplePurchaseOption("apple", "Merchant3", 1, 1))
        val problem = VendorProblem(minimumRequiredPurchase = 200,
                goodQuantitiesSought = mapOf("apple" to 1, "banana" to 1, "coconut" to 1, "date" to 1),
                purchaseOptions = options)

        val solution = BuyOptimizer().solve(problem)

        // Note that we don't buy from Merchant3 because we can't reach a minimum threshold for
        // them.
        val expected = VendorSolution(purchasesToMake = listOf(
                PurchaseToMake(1, SimplePurchaseOption("apple", "Merchant1", 100, 112)),
                PurchaseToMake(1, SimplePurchaseOption("banana", "Merchant1", 100, 95)),
                PurchaseToMake(1, SimplePurchaseOption("coconut", "Merchant2", 1, 10)),
                PurchaseToMake(1, SimplePurchaseOption("date", "Merchant2", 1, 199))))
        assertThat(solution).isEqualTo(expected)
    }

    @Test
    fun `solve -- a good split across multiple vendors -- can be purchased from multiple vendors at once`() {
        val options = listOf(
                SimplePurchaseOption("apple", "Merchant1", 100, 112),
                SimplePurchaseOption("apple", "Merchant2", 4, 2),
                SimplePurchaseOption("apple", "Merchant3", 5, 3),
                SimplePurchaseOption("apple", "Merchant4", 6, 4))
        val problem = VendorProblem(minimumRequiredPurchase = 1,
                goodQuantitiesSought = mapOf("apple" to 10),
                purchaseOptions = options)

        val solution = BuyOptimizer().solve(problem)

        // We skip Merchant1, who could fulfil the order on their own, as too expensive; and buy
        // from the other merchants.
        val expected = VendorSolution(purchasesToMake = listOf(
                PurchaseToMake(4, SimplePurchaseOption("apple", "Merchant2", 4, 2)),
                PurchaseToMake(5, SimplePurchaseOption("apple", "Merchant3", 5, 3)),
                PurchaseToMake(1, SimplePurchaseOption("apple", "Merchant4", 6, 4))))

        assertThat(solution).isEqualTo(expected)
    }

    @Test
    fun `solve -- a good is sought with no purchase options -- throws UnsolvableException`() {
        val options = listOf(SimplePurchaseOption("apple", "Merchant1", 100, 112))
        val problem = VendorProblem(minimumRequiredPurchase = 1,
                goodQuantitiesSought = mapOf("banana" to 10),
                purchaseOptions = options)

        val t = catchThrowable { BuyOptimizer().solve(problem) }

        assertThat(t).isInstanceOf(UnsolvableException::class.java)
    }

    @Test
    fun `solve -- cannot make viable purchase because of minimum -- throws UnsolvableException`() {
        val options = listOf(
                SimplePurchaseOption("apple", "Merchant1", 100, 5),
                SimplePurchaseOption("banana", "Merchant1", 100, 10),
                SimplePurchaseOption("apple", "Merchant2", 1, 20),
                SimplePurchaseOption("banana", "Merchant2", 1, 30))
        val problem = VendorProblem(minimumRequiredPurchase = 200,
                goodQuantitiesSought = mapOf("apple" to 1, "banana" to 1),
                purchaseOptions = options)

        val t = catchThrowable { BuyOptimizer().solve(problem) }

        assertThat(t).isInstanceOf(UnsolvableException::class.java)
    }

    @Test
    fun `solve -- many goods and many vendors -- finds a solution`() {
        val numGoods = 1000
        val numVendors = 20
        // The prices for each good vary across the vendors, with each good costing
        // 100 at a single individual vendor (and slightly more at the others).
        fun optionsForGood(goodNumber: Int) = (1..numVendors).map { vendorNumber ->
            SimplePurchaseOption("good$goodNumber",
                    "vendor$vendorNumber",
                    1,
                    (goodNumber + vendorNumber) % numVendors + 100)
        }

        val purchaseOptions = (1..numGoods).flatMap { optionsForGood(it) } +
                SimplePurchaseOption("good17", "IrrelevantVendor", 1, 12) +
                SimplePurchaseOption("good24", "IrrelevantVendor", 1, 1)

        val goodQuantitiesSought = (1..numGoods).map { "good$it" to 1 }.toMap()
        val problem = VendorProblem(minimumRequiredPurchase = 200,
                goodQuantitiesSought = goodQuantitiesSought,
                purchaseOptions = purchaseOptions)

        val solution = BuyOptimizer().solve(problem)

        // Should have found the cheapest solution - minimum price for each good (except the
        // two that IrrelevantVendor has, which we can't purchase because of the minimum
        // required threshold.)
        assertThat(solution.totalCost).isEqualTo(100 * numGoods)
        assertThat(solution.purchasesToMake.filter { it.option.vendorName == "IrrelevantVendor" })
                .isEmpty()
    }

    @Test
    fun `solve -- good is a data class -- succeeds`() {
        val options = listOf(
                SimplePurchaseOption(Fish("carp", 10), "Merchant1", 1, 10),
                SimplePurchaseOption(Fish("carp", 20), "Merchant1", 1, 100),
                SimplePurchaseOption(Fish("sunfish", 10), "Merchant1", 1, 100),
                SimplePurchaseOption(Fish("sunfish", 20), "Merchant1", 1, 10),
                SimplePurchaseOption(Fish("carp", 10), "Merchant2", 1, 100),
                SimplePurchaseOption(Fish("carp", 20), "Merchant2", 1, 10),
                SimplePurchaseOption(Fish("sunfish", 10), "Merchant2", 1, 10),
                SimplePurchaseOption(Fish("sunfish", 20), "Merchant2", 1, 100))
        val problem = VendorProblem(minimumRequiredPurchase = 1,
                goodQuantitiesSought = mapOf(
                        Fish("carp", 10) to 1,
                        Fish("carp", 20) to 1,
                        Fish("sunfish", 10) to 1,
                        Fish("sunfish", 20) to 1),
                purchaseOptions = options)

        val solution = BuyOptimizer().solve(problem)

        val expected = VendorSolution(purchasesToMake = listOf(
                PurchaseToMake(1, SimplePurchaseOption(Fish("carp", 10), "Merchant1", 1, 10)),
                PurchaseToMake(1, SimplePurchaseOption(Fish("sunfish", 20), "Merchant1", 1, 10)),
                PurchaseToMake(1, SimplePurchaseOption(Fish("carp", 20), "Merchant2", 1, 10)),
                PurchaseToMake(1, SimplePurchaseOption(Fish("sunfish", 10), "Merchant2", 1, 10))))

        assertThat(solution).isEqualTo(expected)
    }

    private data class Fish(val species: String, val weight: Int)
}