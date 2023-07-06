package com.lindsaylevine.magiccardbuyer

import com.lindsaylevine.magiccardbuyer.scryfall.ScryfallApi
import kotlin.math.ceil

class DraftSet(val setName: String) {
    companion object {
        const val NUM_PLAYERS = 16
        const val BOOSTERS_PER_DRAFT = 3
    }

    private val scryfallApi = ScryfallApi()

    /**
     * Returns the cards and quantities necessary to make up a draft set for this set.
     */
    fun cards(): List<Pair<Card, Int>> = slots().flatMap { cardsForSlot(it) }

    private fun cardsForSlot(slot: PackSlot): List<Pair<Card, Int>> {
        val cards = scryfallApi.cards(setName, slot.rarities)
        val uniqueCardCount = cards.size
        val cardsNecessary = slot.quantity * BOOSTERS_PER_DRAFT * NUM_PLAYERS
        val countPerCard = ceil(cardsNecessary.toDouble() / uniqueCardCount).toInt()
        return cards.map { it to countPerCard }
    }

    private fun slots(): List<PackSlot> = listOf(
        PackSlot(11, "common"),
        PackSlot(3, "uncommon"),
        PackSlot(1, "rare", "mythic")
    )
}

private class PackSlot(val quantity: Int, val rarities: List<String>) {
    constructor(quantity: Int, vararg rarities: String) : this(quantity, rarities.toList())
}

fun main() {
    val set = DraftSet("Ikoria: Lair of Behemoths")
    set.cards().forEach(::println)
}