package com.lindsaylevine.magiccardbuyer

import com.lindsaylevine.magiccardbuyer.scryfall.ScryfallApi
import com.lindsaylevine.magiccardbuyer.tcgplayer.TcgPlayerApi
import kotlin.math.ceil

class DraftSet(private val setName: String) {
    companion object {
        const val NUM_PLAYERS = 16
        const val BOOSTERS_PER_DRAFT = 3
    }

    private val scryfallApi = ScryfallApi()

    /**
     * Returns the cards and quantities necessary to make up a draft set for this set.
     */
    fun cards(): List<Pair<Card, Int>> {
        val definition = SetDefinition.of(setName)
        return definition.slots.flatMap { cardsForSlot(it) } + definition.extraCards(scryfallApi)
    }

    private fun cardsForSlot(slot: PackSlot): List<Pair<Card, Int>> {
        val cards = scryfallApi.cards(setName = setName, rarities = slot.rarities, extraParameters = slot.extraParameters, omitBasics = slot.omitBasics)
        val uniqueCardCount = cards.size
        val cardsNecessary = slot.quantity * BOOSTERS_PER_DRAFT * NUM_PLAYERS
        val countPerCard = ceil(cardsNecessary.toDouble() / uniqueCardCount).toInt()
        return cards.map { it to countPerCard }
    }
}

private enum class SetDefinition(val setName: String?,
                                 val slots: List<PackSlot>) {
    DEFAULT(setName = null,
            slots = listOf(
                    PackSlot(11, "common"),
                    PackSlot(3, "uncommon"),
                    PackSlot(1, "rare", "mythic")
            )),

    COMMANDER_LEGENDS(setName = "Commander Legends",
            slots = listOf(
                    PackSlot(14, "common"),
                    // Should exclude legendary creatures
                    PackSlot(3, listOf("uncommon"), "(-type:creature OR -type:legendary)"),
                    PackSlot(1, listOf("rare", "mythic"), "(-type:creature OR -type:legendary)")
            )) {
        override fun extraCards(scryfallApi: ScryfallApi): List<Pair<Card, Int>> {
            // Extra cards -
            // 2 of each uncommon legendary creature
            // 1 of each rare or mythic legendary creature
            // this preserves a 3:1 uncommon to rare ratio when encountered in packs
            // These all get shuffled together and put into 2 of the extra slots in a pack for a total
            // of 20 cards per pack.
            val uncommonLegendaryCreatures = scryfallApi.cards(setName!!, listOf("uncommon"), "(type:creature type:legendary)")
            val rareLegendaryCreatures = scryfallApi.cards(setName, listOf("rare", "mythic"), "(type:creature type:legendary)")
            // This guy is available for free like basic lands.
            val prismaticPiper = Card(name = "The Prismatic Piper", set = setName)

            return uncommonLegendaryCreatures.map { it to 2 } +
                    rareLegendaryCreatures.map { it to 1 } +
                    (prismaticPiper to DraftSet.NUM_PLAYERS)
        }
    },

    KALDHEIM(setName = "Kaldheim",
            slots = listOf(
                    PackSlot(10, listOf("common"), extraParameters = "(-type:snow OR -type:land)"),
                    PackSlot(3, "uncommon"),
                    PackSlot(1, "rare", "mythic"),
                    PackSlot(1, listOf("common"), "(type:snow type:land)", omitBasics = false)
            )),

    STRIXHAVEN(setName = "Strixhaven: School of Mages",
            slots = listOf(
                    PackSlot(9, listOf("common"), extraParameters = "-type:lesson"),
                    PackSlot(3, listOf("uncommon"), extraParameters = "-type:lesson"),
                    PackSlot(1, listOf("rare", "mythic"), extraParameters = "-type:lesson"),
            )) {
        override fun extraCards(scryfallApi: ScryfallApi): List<Pair<Card, Int>> {
            // Extra cards! One slot has the mystical archive cards and one has the lessons.
            val commonLessons = scryfallApi.cards(setName!!, listOf("common"), "type:lesson")
            val uncommonLessons = scryfallApi.cards(setName, listOf("uncommon"), "type:lesson")
            val rareLessons = scryfallApi.cards(setName, listOf("rare", "mythic"), "type:lesson")
// There are 6 rares, 5 uncommons, and 9 commons. We need to get >=48 in total and want to roughly match normal
            // booster rarity distribution. This seems OK.
            val lessons =
                    rareLessons.map { it to 1 } +
                            uncommonLessons.map { it to 3 } +
                            commonLessons.map { it to 5 }

            // Mystical archive cards - these are all either rare or uncommon. You are supposed to be 2/3 to have
            // an uncommon. There are 45 rares (!) and 18 uncommons. 3 uncommons puts us at "meh, close enough" level
            // to the correct rarity.
            val archiveSetName = "Strixhaven Mystical Archive"
            val rareArchives = scryfallApi.cards(archiveSetName, listOf("rare", "mythic"), isBooster = false)
            val uncommonArchives = scryfallApi.cards(archiveSetName, listOf("uncommon"), isBooster = false)

            val archives = rareArchives.map { it to 1 } + uncommonArchives.map { it to 3 }

            return lessons + archives
        }
    };

    companion object {
        private val byName: Map<String?, SetDefinition> = values().associateBy { it.setName }

        fun of(setName: String): SetDefinition = byName[setName] ?: DEFAULT
    }

    open fun extraCards(scryfallApi: ScryfallApi): List<Pair<Card, Int>> = emptyList()
}

private class PackSlot(val quantity: Int,
                       val rarities: List<String>,
                       val extraParameters: String? = null,
                       val omitBasics: Boolean = true) {
    constructor(quantity: Int, vararg rarities: String) : this(quantity, rarities.toList())
}

fun main() {
    val set = DraftSet("Adventures in the Forgotten Realms")
    val cards = set.cards()
    cards.forEach(::println)

    val tcgPlayer = TcgPlayerApi()
    val options = tcgPlayer.purchaseOptions(cards.last().first)
    options.first().purchase(1)
}