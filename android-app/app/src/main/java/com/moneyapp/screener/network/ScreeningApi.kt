package com.moneyapp.screener.network

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.moneyapp.screener.model.MarketSignalResponse
import com.moneyapp.screener.model.ScreeningRequest
import com.moneyapp.screener.model.ScreeningResponse
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.http.Body
import retrofit2.http.POST
import java.util.concurrent.TimeUnit

interface ScreeningApi {
    @POST("screen/market-signal")
    suspend fun marketSignal(@Body request: ScreeningRequest): MarketSignalResponse

    @POST("screen/board-top10-limit-up")
    suspend fun screenBoardTop10LimitUp(@Body request: ScreeningRequest): ScreeningResponse

    @POST("screen/second-board-analysis")
    suspend fun screenSecondBoardAnalysis(@Body request: ScreeningRequest): ScreeningResponse

    companion object {
        @OptIn(ExperimentalSerializationApi::class)
        fun create(baseUrl: String): ScreeningApi {
            val contentType = "application/json".toMediaType()
            val json = Json {
                ignoreUnknownKeys = true
                explicitNulls = false
            }
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
            }
            val client = OkHttpClient.Builder()
                .addInterceptor(logging)
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(90, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .callTimeout(120, TimeUnit.SECONDS)
                .build()

            return Retrofit.Builder()
                .baseUrl(ensureTrailingSlash(baseUrl))
                .client(client)
                .addConverterFactory(json.asConverterFactory(contentType))
                .build()
                .create(ScreeningApi::class.java)
        }

        private fun ensureTrailingSlash(baseUrl: String): String {
            return if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
        }
    }
}
