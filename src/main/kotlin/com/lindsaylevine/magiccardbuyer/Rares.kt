package com.lindsaylevine.magiccardbuyer

import com.lindsaylevine.magiccardbuyer.scryfall.ScryfallApi

/**
 * A helper for looking up cards of a particular set and rarity, suitable for feeding into the main buyer.
 */
class Rares {
    private val scryfall = ScryfallApi()

    fun find(setName: String, rarities: List<String> = listOf("rare", "mythic")): List<Card> {
        return scryfall.cards(setName, rarities)
    }
}

fun main() {
    val rares = Rares().find("Theros Beyond Death")
    println(rares)
}