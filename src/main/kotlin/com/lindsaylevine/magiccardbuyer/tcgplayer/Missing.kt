package com.lindsaylevine.magiccardbuyer.tcgplayer

// As displayed in the message for when a vendor cancels an order.
val missingOrderProducts = """
    3	Magic - Strixhaven: Mystical Archives - Strategic Planning - Near Mint
    2	Magic - Strixhaven: School of Mages - Aether Helix - Near Mint
    5	Magic - Strixhaven: School of Mages - Arcane Subtraction - Near Mint
    2	Magic - Strixhaven: School of Mages - Ardent Dustspeaker - Near Mint
    1	Magic - Strixhaven: School of Mages - Blood Age General - Near Mint
    3	Magic - Strixhaven: School of Mages - Defend the Campus - Near Mint
    2	Magic - Strixhaven: School of Mages - Detention Vortex - Near Mint
    5	Magic - Strixhaven: School of Mages - Elemental Masterpiece - Near Mint
    5	Magic - Strixhaven: School of Mages - Exhilarating Elocution - Near Mint
    2	Magic - Strixhaven: School of Mages - Flunk - Near Mint
    5	Magic - Strixhaven: School of Mages - Heated Debate - Near Mint
    2	Magic - Strixhaven: School of Mages - Humiliate - Near Mint
    5	Magic - Strixhaven: School of Mages - Inkling Summoning - Near Mint
    5	Magic - Strixhaven: School of Mages - Lash of Malice - Near Mint
    5	Magic - Strixhaven: School of Mages - Mage Hunters' Onslaught - Near Mint
    5	Magic - Strixhaven: School of Mages - Oggyar Battle-Seer - Near Mint
    5	Magic - Strixhaven: School of Mages - Pilgrim of the Ages - Near Mint
    2	Magic - Strixhaven: School of Mages - Pillardrop Warden - Near Mint
    5	Magic - Strixhaven: School of Mages - Prismari Pledgemage - Near Mint
    5	Magic - Strixhaven: School of Mages - Promising Duskmage - Near Mint
    5	Magic - Strixhaven: School of Mages - Reckless Amplimancer - Near Mint
    2	Magic - Strixhaven: School of Mages - Reflective Golem - Near Mint
    2	Magic - Strixhaven: School of Mages - Shadewing Laureate - Near Mint
    2	Magic - Strixhaven: School of Mages - Snow Day - Near Mint
    5	Magic - Strixhaven: School of Mages - Specter of the Fens - Near Mint
    1	Magic - Strixhaven: School of Mages - Test of Talents - Near Mint
    2	Magic - Strixhaven: School of Mages - Wormhole Serpent - Near Mint
""".trimIndent()

private const val currentSet = "Kaldheim"

private fun convertLine(line: String): String {
    val toPurchase = parseCancelMessage(line) ?: parseOrderMessage(line) ?:
        throw IllegalArgumentException("$line did not match pattern")
    return "                Card(\"${toPurchase.name}\", \"${toPurchase.set}\") to ${toPurchase.count},"
}

/**
 * Parse a line as a line from a cancel message; returns null if not in that format.
 */
private fun parseCancelMessage(line: String): CardAndCount? {
    val regex = Regex("^\\s*(.*)\\s+(\\d+).*\$")
    val match = regex.matchEntire(line) ?: return null
    val (name, count) = match.destructured
    return CardAndCount(name, currentSet, count.toInt())
}

/**
 * Parse a line as a line from an original order message; returns null if not in that format.
 */
private fun parseOrderMessage(line: String): CardAndCount? {
    val regex = Regex("^\\s*(\\d+)\\s+Magic - (.*?) - (.*?) -.*\$")
    val match = regex.matchEntire(line) ?: return null
    val (count, set, name) = match.destructured
    return CardAndCount(name, set, count.toInt())
}

private data class CardAndCount(val name: String, val set: String, val count: Int)

/**
 * Takes a list of products from a message when a vendor cancels, or from the order details of the original message,
 * and transform it into entries for missing cards to include in the to-buy list within MagicCardBuyer.
 */
fun main() {
    val lines = missingOrderProducts.trim().lines()
    lines.map(::convertLine).forEach(::println)
}