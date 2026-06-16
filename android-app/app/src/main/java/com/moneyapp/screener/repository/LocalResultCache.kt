package com.moneyapp.screener.repository

import android.content.Context

class LocalResultCache(context: Context) {
    private val prefs = context.getSharedPreferences("screening_result_cache_v2", Context.MODE_PRIVATE)

    fun read(key: String, maxAgeMs: Long): String? {
        val cachedAt = prefs.getLong("${key}_ts", 0L)
        val payload = prefs.getString("${key}_payload", null) ?: return null
        val isExpired = cachedAt <= 0L || System.currentTimeMillis() - cachedAt > maxAgeMs
        if (isExpired) {
            remove(key)
            return null
        }
        return payload
    }

    fun write(key: String, payload: String) {
        prefs.edit()
            .putLong("${key}_ts", System.currentTimeMillis())
            .putString("${key}_payload", payload)
            .apply()
    }

    fun remove(key: String) {
        prefs.edit()
            .remove("${key}_ts")
            .remove("${key}_payload")
            .apply()
    }
}
