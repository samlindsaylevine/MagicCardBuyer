package com.lindsaylevine.magiccardbuyer.scryfall

import com.fasterxml.jackson.databind.DeserializationFeature
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.lindsaylevine.magiccardbuyer.Card
import java.net.URI
import java.net.URLEncoder
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.charset.StandardCharsets

class ScryfallApi {
    private val httpClient = HttpClient.newHttpClient()
    private val mapper = jacksonObjectMapper()
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)

    /**
     * [rarities] As recognized by Scryfall, e.g., 'c', 'u', 'r', 'm'
     */
    fun cards(setName: String,
              rarities: List<String>?,
              extraParameters: String? = null): List<Card> {
        val setCode = setCode(setName)
        val rareParameter = rarities?.joinToString(separator = " or ", prefix = "(", postfix = ")") { "r:$it" }
                ?: ""
        val searchString = "set:$setCode not:pwdeck is:booster -t:basic $rareParameter ${extraParameters ?: ""}".trim()
        val encoded = URLEncoder.encode(searchString, StandardCharsets.UTF_8)
        val searchUrl = "https://api.scryfall.com/cards/search?q=$encoded"
        val searchResponse = get(searchUrl, SearchResponse::class.java)
        return searchResponse.data.map { Card(name = it.name, set = setName) }
    }

    private fun setCode(setName: String): String {
        val sets = get("https://api.scryfall.com/sets", SetsResponse::class.java)
        return sets.data.firstOrNull { it.name == setName }?.code
                ?: throw IllegalArgumentException("Set $setName not found")
    }

    private fun <T> get(url: String, targetClass: Class<T>): T {
        val request = HttpRequest.newBuilder(URI.create(url))
                .GET()
                .build()
        val response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())
        return mapper.readValue(response.body(), targetClass)
    }
}

private data class SetsResponse(val data: List<SetResponse>)

private data class SetResponse(val name: String, val code: String)

private data class SearchResponse(val data: List<CardResponse>)

private data class CardResponse(val name: String)

fun main() {
    val scryfall = ScryfallApi()

    val cards = scryfall.cards("Theros Beyond Death", listOf("c"))

    cards.map { it.name }.sorted().forEach(::println)

    println(cards.size)
}