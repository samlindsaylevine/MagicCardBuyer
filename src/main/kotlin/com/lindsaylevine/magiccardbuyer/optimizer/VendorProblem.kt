package com.lindsaylevine.magiccardbuyer.optimizer

/**
 * An optimization problem to be solved.
 *
 * @param T The type of good.
 */
class VendorProblem<T>(
    val goodQuantitiesSought: Map<T, Int>,
    val purchaseOptions: Collection<PurchaseOption<T>>,
    /**
     * Assumed to be the same for each vendor.
     */
    val minimumRequiredPurchase: Int,
    val costPerVendor: Int = 0
) {
    val optionsByGood = purchaseOptions.groupBy { it.good }
    val optionsByVendor = purchaseOptions.groupBy { it.vendorName }
}