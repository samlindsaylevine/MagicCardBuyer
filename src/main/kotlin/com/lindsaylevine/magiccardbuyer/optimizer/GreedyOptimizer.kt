package com.lindsaylevine.magiccardbuyer.optimizer

/**
 * This represents the naive attempt to optimize a vendor problem by purchasing each good from the cheapest possible
 * vendor.
 *
 * This normally won't result in a good solution for us - you will get killed by shipping fees from different vendors -
 * but we are experimenting with whether this will work for TCG Player's "direct" option which claims to bundle all the
 * purchases together if the purchase options are all flagged as "direct".
 *
 * Ignores minimum purchase and cost per vendor and just blindly picks the cheapest options.
 */
class GreedyOptimizer : Optimizer {
    override fun <T> solve(problem: VendorProblem<T>): VendorSolution<T> {
        val goodsAndQuantities = problem.goodQuantitiesSought.entries

        val purchases =
            goodsAndQuantities.flatMap { (good, quantitySought) -> greedyPurchases(problem, good, quantitySought) }
        return VendorSolution(purchases)
    }

    private fun <T> greedyPurchases(problem: VendorProblem<T>, good: T, quantitySought: Int): List<PurchaseToMake<T>> {
        val options = problem.optionsByGood[good] ?: emptyList()
        val optionsByPrice = options.sortedBy { it.price }
        return selectGreedily(good, emptyList(), quantitySought, optionsByPrice)
    }

    private tailrec fun <T> selectGreedily(
        good: T,
        boughtSoFar: List<PurchaseToMake<T>>,
        amountRemaining: Int,
        options: List<PurchaseOption<T>>
    ): List<PurchaseToMake<T>> {
        val first = options.firstOrNull()
            ?: throw IllegalStateException("Not enough options for $good - found $boughtSoFar but require $amountRemaining more")
        return when {
            first.availableQuantity >= amountRemaining -> boughtSoFar + PurchaseToMake(amountRemaining, first)
            else -> selectGreedily<T>(
                good,
                boughtSoFar + PurchaseToMake(first.availableQuantity, first),
                amountRemaining - first.availableQuantity,
                options.drop(1)
            )
        }
    }
}