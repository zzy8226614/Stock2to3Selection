package com.moneyapp.screener.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.moneyapp.screener.model.MarketSignalIndicator
import com.moneyapp.screener.model.MarketSignalResponse
import com.moneyapp.screener.model.ScreenDestination
import com.moneyapp.screener.model.ScreeningItem
import com.moneyapp.screener.model.ScreeningResponse

@Composable
fun MoneyAppRoot(viewModel: ScreeningViewModel = viewModel()) {
    val state by viewModel.uiState.collectAsState()

    when (state.currentScreen) {
        ScreenDestination.HOME -> HomePage(
            state = state,
            onBaseUrlChanged = viewModel::updateBaseUrl,
            onTradeDateChanged = viewModel::updateTradeDate,
            onMarketSignalClick = viewModel::loadMarketSignal,
            onSecondBoardAnalysisClick = viewModel::loadSecondBoardAnalysis,
            onBoardTop10LimitUpClick = viewModel::loadBoardTop10LimitUp,
        )

        ScreenDestination.MARKET_SIGNAL -> MarketSignalPage(
            response = state.marketSignalResponse,
            isLoading = state.isLoading,
            errorMessage = state.errorMessage,
            onBack = viewModel::backToHome,
            onRefresh = viewModel::refreshMarketSignal,
        )

        ScreenDestination.SECOND_BOARD_ANALYSIS -> ScreeningResultPage(
            title = "二板解析",
            response = state.secondBoardAnalysisResponse,
            isLoading = state.isLoading,
            errorMessage = state.errorMessage,
            onBack = viewModel::backToHome,
            onRefresh = viewModel::refreshSecondBoardAnalysis,
            cardContent = { SecondBoardAnalysisItemCard(it) },
        )

        ScreenDestination.BOARD_TOP10_LIMIT_UP -> ScreeningResultPage(
            title = "板块个股排名",
            response = state.boardTop10LimitUpResponse,
            isLoading = state.isLoading,
            errorMessage = state.errorMessage,
            onBack = viewModel::backToHome,
            onRefresh = viewModel::refreshBoardTop10LimitUp,
            cardContent = { BoardTop10ItemCard(it) },
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HomePage(
    state: UiState,
    onBaseUrlChanged: (String) -> Unit,
    onTradeDateChanged: (String) -> Unit,
    onMarketSignalClick: () -> Unit,
    onSecondBoardAnalysisClick: () -> Unit,
    onBoardTop10LimitUpClick: () -> Unit,
) {
    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(title = { Text("二进三选股系统") })
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                text = "收盘后选股版",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            OutlinedTextField(
                value = state.baseUrl,
                onValueChange = onBaseUrlChanged,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("后端地址") },
                supportingText = { Text("模拟器可用 http://10.0.2.2:8081/，真机请改成电脑局域网 IP 或阿里云地址。") },
                singleLine = true,
            )
            OutlinedTextField(
                value = state.tradeDate,
                onValueChange = onTradeDateChanged,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("交易日（可选）") },
                supportingText = { Text("支持 YYYY-MM-DD 或 YYYYMMDD，为空则默认今天。") },
                singleLine = true,
            )
            Button(
                onClick = onMarketSignalClick,
                modifier = Modifier.fillMaxWidth(),
                enabled = !state.isLoading,
            ) {
                Text("情绪信号")
            }
            Button(
                onClick = onSecondBoardAnalysisClick,
                modifier = Modifier.fillMaxWidth(),
                enabled = !state.isLoading,
            ) {
                Text("二板解析")
            }
            Button(
                onClick = onBoardTop10LimitUpClick,
                modifier = Modifier.fillMaxWidth(),
                enabled = !state.isLoading,
            ) {
                Text("板块个股排名")
            }

            if (state.isLoading) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                ) {
                    CircularProgressIndicator()
                }
            }

            state.errorMessage?.let {
                Text(
                    text = it,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ScreeningResultPage(
    title: String,
    response: ScreeningResponse?,
    isLoading: Boolean,
    errorMessage: String?,
    onBack: () -> Unit,
    onRefresh: () -> Unit,
    cardContent: @Composable (ScreeningItem) -> Unit,
) {
    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(title) },
                navigationIcon = {
                    TextButton(onClick = onBack) { Text("返回") }
                },
                actions = {
                    TextButton(onClick = onRefresh, enabled = !isLoading) { Text("刷新") }
                },
            )
        },
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            when {
                isLoading -> CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                errorMessage != null -> ErrorState(errorMessage)
                response == null -> CenterText("暂无结果")
                response.items.isEmpty() -> EmptyState(response)
                else -> LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                    contentPadding = PaddingValues(12.dp),
                ) {
                    item { MarketSummaryCard(response) }
                    items(response.items) { item -> cardContent(item) }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MarketSignalPage(
    response: MarketSignalResponse?,
    isLoading: Boolean,
    errorMessage: String?,
    onBack: () -> Unit,
    onRefresh: () -> Unit,
) {
    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("情绪信号") },
                navigationIcon = {
                    TextButton(onClick = onBack) { Text("返回") }
                },
                actions = {
                    TextButton(onClick = onRefresh, enabled = !isLoading) { Text("刷新") }
                },
            )
        },
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            when {
                isLoading -> CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                errorMessage != null -> ErrorState(errorMessage)
                response == null -> CenterText("暂无结果")
                else -> LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                    contentPadding = PaddingValues(12.dp),
                ) {
                    item { MarketSignalSummaryCard(response) }
                    item { MarketSignalIndicatorTable(response.indicators) }
                    if (response.notes.isNotEmpty()) {
                        item {
                            NotesCard(response.notes)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun MarketSummaryCard(response: ScreeningResponse) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(
                text = "交易日：${response.marketSummary.tradeDate}",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
            )
            CompactInfoLine("涨停总数", response.marketSummary.limitUpCount.toString())
            CompactInfoLine("二板数量", response.marketSummary.secondBoardCount.toString())
            CompactInfoLine("数据来源", response.marketSummary.source)
            response.marketSummary.notes.forEach { note ->
                Text(note, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary)
            }
        }
    }
}

@Composable
private fun MarketSignalSummaryCard(response: MarketSignalResponse) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(
                text = "${response.tradeDate} ${response.weekday}",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
            )
            CompactInfoLine("大盘表现", response.marketOverview)
            CompactInfoLine("成交额", response.turnoverOverview)
            CompactInfoLine("情绪判定", response.regimeLabel)
            CompactInfoLine("仓位建议", response.positionAdvice)
        }
    }
}

@Composable
private fun MarketSignalIndicatorTable(indicators: List<MarketSignalIndicator>) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text("指标概览", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
            CompactIndicatorRow("指标", "今日数值", "系统标准", "是否达标", isHeader = true)
            indicators.forEach { indicator ->
                CompactIndicatorRow(
                    indicator.name,
                    indicator.todayValue,
                    indicator.standard,
                    indicator.status,
                    isHeader = false,
                )
            }
        }
    }
}

@Composable
private fun BoardTop10ItemCard(item: ScreeningItem) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(
                text = item.stockName,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
            )
            CompactMetricRow(
                listOf(
                    "流通市值" to item.floatMarketCap,
                    "所属板块" to item.boardName,
                    "连板天梯" to item.ladderLevel,
                    "板块排名" to formatBoardRank(item.boardRank),
                    "总分" to (item.totalScore?.let { "%.1f".format(it) } ?: "--"),
                ),
            )
            CompactMetricRow(
                listOf(
                    "封单时间" to item.sealTime,
                    "封单手数" to item.sealOrderLots,
                    "开板次数" to item.openBoardCount.toString(),
                    "换手率" to item.turnoverRate,
                    "板块涨停数" to item.boardLimitUpCount.toString(),
                ),
            )
            Text(item.recommendReason, style = MaterialTheme.typography.bodySmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
        }
    }
}

@Composable
private fun SecondBoardAnalysisItemCard(item: ScreeningItem) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(
                text = item.stockName,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
            )
            CompactMetricRow(
                listOf(
                    "股价" to item.latestPrice,
                    "流通市值" to item.floatMarketCap,
                    "所属板块" to item.boardName,
                    "板块排名" to formatBoardRank(item.boardRank),
                    "板块涨停数" to item.boardLimitUpCount.toString(),
                ),
            )
            CompactMetricRow(
                listOf(
                    "封单时间" to item.sealTime,
                    "封单手数" to item.sealOrderLots,
                    "开板次数" to item.openBoardCount.toString(),
                    "换手率" to item.turnoverRate,
                    "首板量能" to item.firstBoardEnergy,
                ),
            )
            Text(item.recommendReason, style = MaterialTheme.typography.bodySmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
        }
    }
}

@Composable
private fun CompactMetricRow(metrics: List<Pair<String, String>>) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
        metrics.forEach { (label, value) ->
            CompactMetricCell(label, value, Modifier.weight(1f))
        }
    }
}

@Composable
private fun CompactMetricCell(label: String, value: String, modifier: Modifier = Modifier) {
    Column(modifier = modifier) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.primary,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodySmall,
            fontSize = 12.sp,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun CompactInfoLine(label: String, value: String) {
    Text(text = "$label：$value", style = MaterialTheme.typography.bodySmall, fontSize = 12.sp)
}

@Composable
private fun CompactIndicatorRow(
    title: String,
    todayValue: String,
    standard: String,
    status: String,
    isHeader: Boolean,
) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        CompactIndicatorCell(title, Modifier.weight(1.0f), isHeader)
        CompactIndicatorCell(todayValue, Modifier.weight(1.4f), isHeader)
        CompactIndicatorCell(standard, Modifier.weight(1.5f), isHeader)
        CompactIndicatorCell(status, Modifier.weight(0.9f), isHeader)
    }
}

@Composable
private fun CompactIndicatorCell(text: String, modifier: Modifier, isHeader: Boolean) {
    Text(
        text = text,
        modifier = modifier,
        style = if (isHeader) MaterialTheme.typography.labelSmall else MaterialTheme.typography.bodySmall,
        fontWeight = if (isHeader) FontWeight.Bold else FontWeight.Normal,
        fontSize = if (isHeader) 11.sp else 12.sp,
        maxLines = 2,
        overflow = TextOverflow.Ellipsis,
    )
}

@Composable
private fun NotesCard(notes: List<String>) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text("备注", style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Bold)
            notes.forEach { note -> Text(note, style = MaterialTheme.typography.bodySmall) }
        }
    }
}

@Composable
private fun EmptyState(response: ScreeningResponse) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("当日无符合条件标的")
        Text("交易日：${response.tradeDate}", style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun ErrorState(message: String) {
    Text(
        text = message,
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        color = MaterialTheme.colorScheme.error,
    )
}

@Composable
private fun CenterText(message: String) {
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(message)
    }
}

private fun formatBoardRank(rank: Int): String {
    return if (rank > 0) "第${rank}名" else "--"
}
