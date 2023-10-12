package com.lindsaylevine.magiccardbuyer.optimizer

import org.assertj.core.api.Assertions.assertThat
import org.junit.Test

class GreedyOptimizerTest {

    @Test
    fun `solve -- item available from a vendor -- buy it`() {
        val options = listOf(
            SimplePurchaseOption("apple", "Merchant1", 100, 112)
        )
        val problem = VendorProblem(
            minimumRequiredPurchase = 0,
            goodQuantitiesSought = mapOf("apple" to 1),
            purchaseOptions = options
        )

        val solution = GreedyOptimizer().solve(problem)

        val expected = VendorSolution(
            purchasesToMake = listOf(
                PurchaseToMake(1, SimplePurchaseOption("apple", "Merchant1", 100, 112))
            )
        )
        assertThat(solution).isEqualTo(expected)
    }

    @Test
    fun `solve -- two vendors -- just buys each thing from the cheapest vendor`() {
        val options = listOf(
            SimplePurchaseOption("apple", "Merchant1", 100, 112),
            SimplePurchaseOption("banana", "Merchant1", 100, 95),
            SimplePurchaseOption("coconut", "Merchant1", 15, 9),
            SimplePurchaseOption("date", "Merchant1", 1, 1000),
            SimplePurchaseOption("apple", "Merchant2", 1, 100000),
            SimplePurchaseOption("banana", "Merchant2", 1, 15),
            SimplePurchaseOption("coconut", "Merchant2", 1, 10),
            SimplePurchaseOption("date", "Merchant2", 1, 199)
        )
        val problem = VendorProblem(
            minimumRequiredPurchase = 200, costPerVendor = 1_000_000,
            goodQuantitiesSought = mapOf("apple" to 1, "banana" to 1, "coconut" to 1, "date" to 1),
            purchaseOptions = options
        )

        val solution = GreedyOptimizer().solve(problem)

        // Note that we make each purchase from the cheapest vendor for that good, ignoring any minimum threshold or
        // price per vendor.
        val expected = VendorSolution(
            purchasesToMake = listOf(
                PurchaseToMake(1, SimplePurchaseOption("apple", "Merchant1", 100, 112)),
                PurchaseToMake(1, SimplePurchaseOption("banana", "Merchant2", 1, 15)),
                PurchaseToMake(1, SimplePurchaseOption("coconut", "Merchant1", 15, 9)),
                PurchaseToMake(1, SimplePurchaseOption("date", "Merchant2", 1, 199))
            )
        )

        assertThat(solution).isEqualTo(expected)
    }


    @Test
    fun `solve -- not enough from cheapest vendors -- buys amounts in cheapest order`() {
        val options = listOf(
            SimplePurchaseOption("apple", "Merchant1", 100, 112),
            SimplePurchaseOption("apple", "Merchant2", 1, 1),
            SimplePurchaseOption("apple", "Merchant3", 3, 2)
        )
        val problem = VendorProblem(
            minimumRequiredPurchase = 0,
            goodQuantitiesSought = mapOf("apple" to 10),
            purchaseOptions = options
        )

        val solution = GreedyOptimizer().solve(problem)

        val expected = VendorSolution(
            purchasesToMake = listOf(
                PurchaseToMake(1, SimplePurchaseOption("apple", "Merchant2", 1, 1)),
                PurchaseToMake(3, SimplePurchaseOption("apple", "Merchant3", 3, 2)),
                PurchaseToMake(6, SimplePurchaseOption("apple", "Merchant1", 100, 112))
            )
        )

        assertThat(solution).isEqualTo(expected)
    }
}