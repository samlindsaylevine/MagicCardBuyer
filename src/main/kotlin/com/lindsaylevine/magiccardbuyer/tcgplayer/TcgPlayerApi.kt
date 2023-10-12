package com.lindsaylevine.magiccardbuyer.tcgplayer

import cmonster.browsers.ChromeBrowser
import cmonster.cookies.Cookie
import com.fasterxml.jackson.databind.DeserializationFeature
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import com.lindsaylevine.magiccardbuyer.Card
import com.lindsaylevine.magiccardbuyer.optimizer.PurchaseOption
import java.net.*
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.charset.StandardCharsets

/**
 * TCG Player used to have a public API, but is no longer granting new access. (It required sign-up and human approval.)
 * So, instead we are just looking at requests made through the UI (via browser dev tools) and mimicking those.
 * I guess that's the public, unauthenticated interface...
 */
class TcgPlayerApi {
    companion object {
        const val MAX_STORES_PER_CARD = 15
    }

    private val cookies: Set<Cookie> = run {
        val chrome = ChromeBrowser()
        chrome.getCookiesForDomain("tcgplayer.com")
    }

    private val client: HttpClient = run {
        if (cookies.isEmpty()) {
            throw IllegalStateException("No cookies found for tcgplayer.com, will not be able to make purchases")
        }
        val cookieHandler = CookieManager()
        cookies.map { it.toHttpCookie() }
                .forEach {
                    cookieHandler.cookieStore.add(URI("https://tcgplayer.com"), it)
                    cookieHandler.cookieStore.add(URI("https://mpapi.tcgplayer.com"), it)
                }

        HttpClient.newBuilder()
                .cookieHandler(cookieHandler)
                .build()
    }

    private val mapper = jacksonObjectMapper().configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)


    private val cartKey: String = cartKeyFromCookie() ?: createCart()

    private fun cartKeyFromCookie(): String? {
        val cartCookie = cookies.firstOrNull { it.name == "StoreCart_PRODUCTION" }
                ?: return null
        val cookieValue = cartCookie.value
        val cookieContents = cookieValue.trim()
                .split("&")
                .associate { it.substringBefore("=") to it.substringAfter("=") }
        return cookieContents["CK"]
    }

    /**
     * Returns the cart key for the created cart.
     */
    private fun createCart(): String {
        val cartUrl = "https://mpapi.tcgplayer.com/v2/cart/create/usercart"
        val externalUserId = externalUserId()
        // Taken from a request in browser.
        val requestBody = """{"externalUserId":"$externalUserId"}"""
        val request = HttpRequest.newBuilder()
                .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                .uri(URI.create(cartUrl))
                .header("Content-Type", "application/json")
                .build()
        val response = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            throw IllegalStateException("Bad status ${response.statusCode()} on cart create response for $externalUserId; body ${response.body()}")
        }
        val apiResponse: ApiResponse<CartCreateResponse> = mapper.readValue(response.body())
        return apiResponse.results.first().cartKey
    }

    private fun externalUserId(): String {
        val userUrl = "https://mpapi.tcgplayer.com/v2/user"
        val request = HttpRequest.newBuilder()
                .GET()
                .uri(URI.create(userUrl))
                .build()
        val response = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            throw IllegalStateException("Bad status ${response.statusCode()} on user response; body ${response.body()}")
        }
        val apiResponse: ApiResponse<UserResult> = mapper.readValue(response.body())
        val result = apiResponse.results.first().externalUserId
        if (result.all { it == '0' || it == '-' }) {
            throw IllegalStateException("Bad response from user lookup; body ${response.body()}")
        }
        return result
    }

    private fun Cookie.toHttpCookie() = HttpCookie(this.name, this.value).apply {
        path = "/"
        version = 0
    }

    /**
     * Returns the purchase options available for card.
     */
    fun purchaseOptions(card: Card): List<TcgPlayerPurchaseOption> {
        val searchResult = search(card) ?: throw IllegalArgumentException("Unable to find card $card")
        val listings = listings(searchResult.productId, card, MAX_STORES_PER_CARD + BlacklistedVendors.names.size)

        return listings
                .filter { it.sellerName !in BlacklistedVendors.names }
                .take(MAX_STORES_PER_CARD)
                .map { TcgPlayerPurchaseOption(card, it, this) }
    }

    private fun search(card: Card): SearchResult? {
        // For double-faced cards just take the first part of the name.
        val searchName = card.name.substringBefore(" //").lowercase()
        val encoded = URLEncoder.encode(searchName.lowercase(), StandardCharsets.UTF_8)
        val searchUrl = "https://mp-search-api.tcgplayer.com/v1/search/request?q=$encoded&isList=false"
        // Taken from a request in browser.
        val requestBody =
                """{"algorithm":"sales_exp_fields_experiment","from":0,"size":100,"filters":{"term":{},"range":{},"match":{}},"listingSearch":{"context":{"cart":{}},"filters":{"term":{"sellerStatus":"Live","channelId":0},"range":{"quantity":{"gte":1}},"exclude":{"channelExclusion":0}}},"context":{"cart":{},"shippingCountry":"US"},"settings":{"useFuzzySearch":false,"didYouMean":{}},"sort":{}}"""
        val request = HttpRequest.newBuilder()
                .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                .uri(URI.create(searchUrl))
                .header("Content-Type", "application/json")
                .build()
        val response = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            throw IllegalStateException("Bad status ${response.statusCode()} on search response for ${card.name}; body ${response.body()}")
        }
        val apiResponse: ApiResponse<SearchResults> = mapper.readValue(response.body())
        val results = apiResponse.results.first().results
        return results.firstOrNull { it.productName.equals(searchName, ignoreCase = true) && it.setName == tcgPlayerSetName(card.set) }
        // Sometimes there are no exact name matches because there are multiple hits with different art. So, when that
        // happens, the name will be like "Command Tower (479)". Then we'll take the first one of those that hits.
                ?: results.firstOrNull { it.productName.isNumberOf(searchName) && it.setName == tcgPlayerSetName(card.set) }
    }

    private fun tcgPlayerSetName(scryfallSetName: String?) = when (scryfallSetName) {
        "Strixhaven Mystical Archive" -> "Strixhaven: Mystical Archives"
        else -> scryfallSetName
    }

    private fun String.isNumberOf(originalCardName: String): Boolean {
        val regex = Regex("""^(.*) \(\d+\)""")
        val matchingName = regex.matchEntire(this)?.groupValues?.let { it[1] } ?: return false
        return matchingName.equals(originalCardName, ignoreCase = true)
    }

    private fun listings(productId: Int, card: Card, maxAmount: Int): List<ListingResult> {
        val listingsUrl = "https://mp-search-api.tcgplayer.com/v1/product/$productId/listings"
        // Mostly taken from a browser request. Forces non-foil and also asks for the appropriate number of listings.
        val requestBody = """
            {
              "filters": {
                "term": {
                  "sellerStatus": "Live",
                  "channelId": 0,
                  "language": [
                    "English"
                  ],
                  "printing": [
                    "Normal"
                  ]
                },
                "range": {
                  "quantity": {
                    "gte": 1
                  }
                },
                "exclude": {
                  "channelExclusion": 0
                }
              },
              "from": 0,
              "size": $maxAmount,
              "sort": {
                "field": "price+shipping",
                "order": "asc"
              },
              "context": {
                "shippingCountry": "US",
                "cart": {}
              },
              "aggregations": [
                "listingType"
              ]
            }
        """.trimIndent()
        val request = HttpRequest.newBuilder()
                .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                .uri(URI.create(listingsUrl))
                .header("Content-Type", "application/json")
                .build()
        val response = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            throw IllegalStateException("Bad status ${response.statusCode()} on listings response for ${card.name}; body ${response.body()}")
        }
        val apiResponse: ApiResponse<ListingResults> = mapper.readValue(response.body())
        return apiResponse.results.first().results
    }


    fun purchase(requestBody: PurchaseRequest) {
        val addUrl = "https://mpapi.tcgplayer.com/v2/cart/$cartKey/item/add"
        val request = HttpRequest.newBuilder()
                .POST(HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(requestBody)))
                .uri(URI.create(addUrl))
                .header("Content-Type", "application/json")
                .build()
        val response = client.send(request, HttpResponse.BodyHandlers.ofString())
        when (response.statusCode()) {
            HttpURLConnection.HTTP_OK -> Unit
            422 -> throw UnavailableForPurchaseException(response.body())
            else -> throw IllegalStateException("Bad status ${response.statusCode()} adding to cart $cartKey; request body $requestBody, response body ${response.body()}")
        }
    }
}

/**
 * When the card is no longer available for purchase after we have run our calculations.
 */
class UnavailableForPurchaseException(val responseBody: String) : Exception("Couldn't make calculated purchase; response $responseBody")

private data class ApiResponse<T>(val results: List<T>)
private data class UserResult(val externalUserId: String)
private data class CartCreateResponse(val cartKey: String)
private data class SearchResults(val results: List<SearchResult>)
data class SearchResult(val productName: String, val setName: String, val productId: Int)
private data class ListingResults(val results: List<ListingResult>)
data class ListingResult(
        val quantity: Int,
        val price: Double,
        val sellerName: String,
        val listingId: Long,
        val productConditionId: Double,
        val directSeller: Boolean,
        val sellerKey: String,
        val channelId: Int
)

data class PurchaseRequest(
        val sku: Double,
        val sellerKey: String,
        val channelId: Int,
        val requestedQuantity: Int,
        val price: Double,
        val isDirect: Boolean
)

class TcgPlayerPurchaseOption(
        override val good: Card,
        private val listingResult: ListingResult,
        private val api: TcgPlayerApi
) : PurchaseOption<Card> {
    override val key = listingResult.listingId.toString()
    override val vendorName = listingResult.sellerName
    override val availableQuantity = listingResult.quantity
    override val price: Int = (listingResult.price * 100).toInt()

    /**
     * Execute this option, adding the provided amount of this card to the shopping cart.
     */
    override fun purchase(quantity: Int) {
        val request = PurchaseRequest(
                sku = listingResult.productConditionId,
                sellerKey = listingResult.sellerKey,
                channelId = listingResult.channelId,
                requestedQuantity = quantity,
                price = listingResult.price,
                isDirect = listingResult.directSeller
        )
        try {
            api.purchase(request)
        } catch (e: UnavailableForPurchaseException) {
            // If something isn't available for purchase after calculation time, we'll just have to do it by hand.
            println("  ERROR! Failed to purchase $quantity ${good.name}! Response body ${e.responseBody}")
        }
    }
}

fun main() {
    val tcgPlayer = TcgPlayerApi()
    val options = tcgPlayer.purchaseOptions(Card("Command Tower", "Commander Legends"))

    println(options.first().vendorName)
    println(options.first().price)
    options.first().purchase(1)
}