package com.lindsaylevine.magiccardbuyer.optimizer

/**
 * A single option for purchasing a particular good from a particular vendor.
 *
 * Goods can be basically anything but must have a consistent string representation and equals. (A data class is fine.
 * So is a string.) Note that the PurchaseOption *itself* does not have these requirements; they are uniquely defined
 * by their [key].
 *
 * Vendors are correlated by their string name.
 *
 * @param T The type of good.
 */
interface PurchaseOption<T> {
    val good: T
    val vendorName: String
    val availableQuantity: Int
    val price: Int

    // This must uniquely define this option, separating it from any other option being considered.
    val key: String
}

/**
 * A simple option with no other behavior.
 *
 * Assumes that each vendor has only one option for each good (i.e., that we can use "vendor,good" as a unique key).
 */
data class SimplePurchaseOption<T>(override val good: T,
                                   override val vendorName: String,
                                   override val availableQuantity: Int,
                                   override val price: Int) : PurchaseOption<T> {
    override val key: String
        get() = "${vendorName}_$good"
}