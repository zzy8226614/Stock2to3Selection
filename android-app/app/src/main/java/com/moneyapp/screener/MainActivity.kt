package com.moneyapp.screener

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.moneyapp.screener.ui.MoneyAppRoot
import com.moneyapp.screener.ui.theme.MoneyAppTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MoneyAppTheme {
                MoneyAppRoot()
            }
        }
    }
}
