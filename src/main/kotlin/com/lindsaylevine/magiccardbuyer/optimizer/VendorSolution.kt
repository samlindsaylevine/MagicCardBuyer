package com.lindsaylevine.magiccardbuyer.optimizer

/**
 * A total solution.
 */
data class VendorSolution<T>(
        /**
         * This contains only purchases that should be made; i.e., quantity > 0.
         */
        val purchasesToMake: List<PurchaseToMake<T>>) {

    val totalCost: Int
        get() = purchasesToMake.sumOf { it.quantity * it.option.price }
}

/**
 * As part of a result, how many of the good should be purchased from this option.
 */
data class PurchaseToMake<T>(val quantity: Int,
                             val option: PurchaseOption<T>)