package com.lindsaylevine.magiccardbuyer.tcgplayer

// As displayed in the message for when a vendor cancels an order.
val missingOrderProducts = """
    Battlefield Raptor	2	${'$'}0.05	${'$'}0.10
    Brinebarrow Intruder	2	${'$'}0.05	${'$'}0.10
    Guardian Gladewalker	1	${'$'}0.05	${'$'}0.05
    Invoke the Divine	4	${'$'}0.05	${'$'}0.20
    Jaspera Sentinel	2	${'$'}0.05	${'$'}0.10
    Raise the Draugr	3	${'$'}0.05	${'$'}0.15
    Ascent of the Worthy	1	${'$'}0.05	${'$'}0.05
    Fearless Liberator	2	${'$'}0.05	${'$'}0.10
    Frost Augur	1	${'$'}0.05	${'$'}0.05
    Icebind Pillar	1	${'$'}0.05	${'$'}0.05
    Shepherd of the Cosmos	2	${'$'}0.05	${'$'}0.10
    Tergrid's Shadow	2	${'$'}0.05	${'$'}0.10
    The Three Seasons	1	${'$'}0.05	${'$'}0.05
    Ascendant Spirit	1	${'$'}0.23	${'$'}0.23
    Draugr Necromancer	1	${'$'}0.05	${'$'}0.05
    Glorious Protector	1	${'$'}0.12	${'$'}0.12
    Shimmerdrift Vale	1	${'$'}0.05	${'$'}0.05
    Woodland Chasm	1	${'$'}0.35	${'$'}0.35
""".trimIndent()

private const val currentSet = "Kaldheim"

private fun convertLine(line: String): String {
    val regex = Regex("^\\s*(.*)\\s+(\\d+).*\$")
    val match = regex.matchEntire(line) ?: throw IllegalArgumentException("$line did not match pattern")
    val (name, count) = match.destructured

    return "                Card(\"$name\", \"$currentSet\") to $count,"
}

/**
 * Takes a list of products from a message when a vendor cancels and transform it into entries for missing cards
 * to include in the to-buy list within MagicCardBuyer.
 */
fun main() {
    val lines = missingOrderProducts.trim().lines()
    lines.map(::convertLine).forEach(::println)
}