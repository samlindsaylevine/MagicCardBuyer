package com.lindsaylevine.magiccardbuyer.tcgplayer

import com.lindsaylevine.magiccardbuyer.Card
import com.lindsaylevine.magiccardbuyer.optimizer.PurchaseOption

/**
 * TCG Player used to have a public API, but is no longer granting new access. (It required sign-up and human approval.)
 * So, instead it is just HTML scraping ahoy. I guess that's the public, unauthenticated interface...
 */
class TcgPlayerApi {
    fun purchaseOptions(card: Card): List<TcgPlayerPurchaseOption> {
        TODO()
    }
}

data class TcgPlayerPurchaseOption(override val good: Card,
                                   override val vendorName: String,
                                   override val availableQuantity: Int,
                                   override val price: Int,
                                   val purchaseId: String
): PurchaseOption<Card> {
    override val key = purchaseId

    /**
     * Execute this option, adding the provided amount of this card to the shopping cart.
     */
    fun purchase(quantity: Int) {
        TODO()
    }
}