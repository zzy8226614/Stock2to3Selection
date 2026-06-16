package com.moneyapp.screener.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ScreeningRequest(
    @SerialName("trade_date") val tradeDate: String? = null,
    @SerialName("use_demo_on_failure") val useDemoOnFailure: Boolean = true,
    @SerialName("force_refresh") val forceRefresh: Boolean = false,
)

@Serializable
data class MarketSummary(
    val tradeDate: String,
    val limitUpCount: Int,
    val firstBoardCount: Int,
    val weakToStrongCount: Int,
    val secondBoardCount: Int = 0,
    val source: String,
    val notes: List<String> = emptyList(),
)

@Serializable
data class ScreeningItem(
    val stockName: String,
    val symbol: String,
    val latestPrice: String = "--",
    val floatMarketCap: String,
    val boardName: String,
    val boardRank: Int = 0,
    val boardLimitUpCount: Int,
    val ladderLevel: String = "--",
    val turnoverRate: String,
    val sealTime: String,
    val sealOrderLots: String = "--",
    val openBoardCount: Int = 0,
    val totalScore: Double? = null,
    val firstBoardEnergy: String = "--",
    val isLimitUp: Boolean = true,
    val strategyTag: String,
    val recommendReason: String,
)

@Serializable
data class ScreeningResponse(
    @SerialName("trade_date") val tradeDate: String,
    @SerialName("market_summary") val marketSummary: MarketSummary,
    val items: List<ScreeningItem> = emptyList(),
    val error: String? = null,
)

@Serializable
data class MarketSignalIndicator(
    val name: String,
    val todayValue: String,
    val standard: String,
    val status: String,
)

@Serializable
data class MarketSignalResponse(
    @SerialName("trade_date") val tradeDate: String,
    val weekday: String,
    val marketOverview: String,
    val turnoverOverview: String,
    val regime: String,
    val regimeLabel: String,
    val positionAdvice: String,
    val indicators: List<MarketSignalIndicator> = emptyList(),
    val notes: List<String> = emptyList(),
    val error: String? = null,
)

enum class ScreenDestination {
    HOME,
    MARKET_SIGNAL,
    SECOND_BOARD_ANALYSIS,
    BOARD_TOP10_LIMIT_UP,
}
