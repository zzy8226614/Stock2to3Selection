package com.moneyapp.screener.repository

import android.content.Context
import com.moneyapp.screener.model.MarketSignalResponse
import com.moneyapp.screener.model.ScreeningRequest
import com.moneyapp.screener.model.ScreeningResponse
import com.moneyapp.screener.network.ScreeningApi
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class ScreeningRepository(
    private val cacheStore: LocalResultCache,
    @OptIn(ExperimentalSerializationApi::class)
    private val json: Json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
    },
) {
    data class LoadResult<T>(
        val response: T,
        val fromCache: Boolean,
    )

    suspend fun loadMarketSignal(
        baseUrl: String,
        tradeDate: String,
        forceRefresh: Boolean = false,
    ): LoadResult<MarketSignalResponse> {
        return load(
            screenType = "market_signal",
            baseUrl = baseUrl,
            tradeDate = tradeDate,
            forceRefresh = forceRefresh,
            request = {
                api(baseUrl).marketSignal(
                    ScreeningRequest(
                        tradeDate = tradeDate.ifBlank { null },
                        useDemoOnFailure = true,
                        forceRefresh = forceRefresh,
                    ),
                )
            },
        )
    }

    suspend fun loadBoardTop10LimitUp(
        baseUrl: String,
        tradeDate: String,
        forceRefresh: Boolean = false,
    ): LoadResult<ScreeningResponse> {
        return load(
            screenType = "board_top10_limit_up",
            baseUrl = baseUrl,
            tradeDate = tradeDate,
            forceRefresh = forceRefresh,
            request = {
                api(baseUrl).screenBoardTop10LimitUp(
                    ScreeningRequest(
                        tradeDate = tradeDate.ifBlank { null },
                        useDemoOnFailure = true,
                        forceRefresh = forceRefresh,
                    ),
                )
            },
        )
    }

    suspend fun loadSecondBoardAnalysis(
        baseUrl: String,
        tradeDate: String,
        forceRefresh: Boolean = false,
    ): LoadResult<ScreeningResponse> {
        return load(
            screenType = "second_board_analysis",
            baseUrl = baseUrl,
            tradeDate = tradeDate,
            forceRefresh = forceRefresh,
            request = {
                api(baseUrl).screenSecondBoardAnalysis(
                    ScreeningRequest(
                        tradeDate = tradeDate.ifBlank { null },
                        useDemoOnFailure = true,
                        forceRefresh = forceRefresh,
                    ),
                )
            },
        )
    }

    private fun api(baseUrl: String): ScreeningApi = ScreeningApi.create(baseUrl)

    private fun cacheKey(screenType: String, baseUrl: String, tradeDate: String): String {
        val normalizedBaseUrl = baseUrl.trim().trimEnd('/')
        val normalizedTradeDate = tradeDate.trim().ifBlank { "__today__" }
        return "$screenType|$normalizedBaseUrl|$normalizedTradeDate"
    }

    private suspend inline fun <reified T> load(
        screenType: String,
        baseUrl: String,
        tradeDate: String,
        forceRefresh: Boolean,
        crossinline request: suspend () -> T,
    ): LoadResult<T> {
        val key = cacheKey(screenType, baseUrl, tradeDate)
        if (!forceRefresh) {
            cacheStore.read(key, CACHE_TTL_MS)?.let { payload ->
                return LoadResult(
                    response = json.decodeFromString(payload),
                    fromCache = true,
                )
            }
        }

        return runCatching { request() }
            .map { response ->
                cacheStore.write(key, json.encodeToString(response))
                LoadResult(response = response, fromCache = false)
            }
            .getOrElse { error ->
                cacheStore.read(key, CACHE_TTL_MS)?.let { payload ->
                    return LoadResult(
                        response = json.decodeFromString(payload),
                        fromCache = true,
                    )
                }
                throw error
            }
    }

    companion object {
        const val CACHE_TTL_MS: Long = 2 * 60 * 60 * 1000L

        fun create(context: Context): ScreeningRepository {
            return ScreeningRepository(LocalResultCache(context.applicationContext))
        }
    }
}
