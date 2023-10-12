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
 * So, instead we are just mimicking all the requests that we see our browser make in the developer tools. I guess
 * that's at least one step up from scraping the HTML!
 */
class TcgPlayerApi {
    companion object {
        const val MAX_STORES_PER_CARD = 20
    }

    private val cookies: Set<Cookie> = run {
        val chrome = ChromeBrowser()
        chrome.getCookiesForDomain("tcgplayer.com")
    }

    private fun Cookie.toHttpCookie() = HttpCookie(this.name, this.value).apply {
        path = "/"
        version = 0
    }

    private val client: HttpClient = run {
        if (cookies.isEmpty()) {
            throw IllegalStateException("No cookies found for tcgplayer.com, will not be able to make purchases")
        }
        val cookieHandler = CookieManager()
        cookies.map { it.toHttpCookie() }
            .forEach { cookieHandler.cookieStore.add(URI("https://tcgplayer.com"), it) }

        HttpClient.newBuilder()
            .cookieHandler(cookieHandler)
            .build()
    }

    private val mapper = jacksonObjectMapper().configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)

    /**
     * Returns the purchase options available for card.
     */
    fun purchaseOptions(card: Card): List<TcgPlayerPurchaseOption> {
        val searchResult = search(card) ?: throw IllegalArgumentException("Unable to find card $card")
        val listings = listings(searchResult.productId, card)

        return listings.map { TcgPlayerPurchaseOption(card, it, this) }
    }

    private fun search(card: Card): SearchResult? {
        val encoded = URLEncoder.encode(card.name.lowercase(), StandardCharsets.UTF_8)
        val searchUrl = "https://mp-search-api.tcgplayer.com/v1/search/request?q=$encoded&isList=false"
        // Taken from a request in browser.
        val requestBody =
            """{"algorithm":"sales_exp_fields_experiment","from":0,"size":24,"filters":{"term":{},"range":{},"match":{}},"listingSearch":{"context":{"cart":{}},"filters":{"term":{"sellerStatus":"Live","channelId":0},"range":{"quantity":{"gte":1}},"exclude":{"channelExclusion":0}}},"context":{"cart":{},"shippingCountry":"US"},"settings":{"useFuzzySearch":false,"didYouMean":{}},"sort":{}}"""
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
        return apiResponse.results.first().results.firstOrNull { it.productName == card.name && it.setName == card.set }
    }

    private fun listings(productId: Int, card: Card): List<ListingResult> {
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
              "size": $MAX_STORES_PER_CARD,
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

    private val cartKey: String by lazy {
        val cartCookie = cookies.first { it.name == "StoreCart_PRODUCTION" }
        val cookieValue = cartCookie.value
        val cookieContents = cookieValue.trim()
            .split("&")
            .associate { it.substringBefore("=") to it.substringAfter("=") }
        cookieContents["CK"] ?: "Bad cookie contents $cookieValue"
    }

    fun purchase(requestBody: PurchaseRequest) {
        val addUrl = "https://mpapi.tcgplayer.com/v2/cart/$cartKey/item/add"
        val request = HttpRequest.newBuilder()
            .POST(HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(requestBody)))
            .uri(URI.create(addUrl))
            .header("Content-Type", "application/json")
            .build()
        val response = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (response.statusCode() != HttpURLConnection.HTTP_OK) {
            throw IllegalStateException("Bad status ${response.statusCode()} adding to cart $cartKey; request body $requestBody, response body ${response.body()}")
        }
    }
}

private data class ApiResponse<T>(val results: List<T>)
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
        api.purchase(request)
    }
}

fun main() {
    val tcgPlayer = TcgPlayerApi()
    val options = tcgPlayer.purchaseOptions(Card("Zenith Flare", "Ikoria: Lair of Behemoths"))

    options.first().purchase(1)
}