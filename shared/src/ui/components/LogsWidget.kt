package org.example.project.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.example.project.theme.AppColors
import org.example.project.theme.AppIcons

@Composable
fun LogsWidget(
    logs: List<String>,
    onClearLogs: () -> Unit,
    modifier: Modifier = Modifier,
    isDark: Boolean = true
) {
    var filterText by remember { mutableStateOf("") }
    var autoScroll by remember { mutableStateOf(true) }
    val listState = rememberLazyListState()

    val bg = if (isDark) AppColors.DarkBackground else AppColors.LightBackground
    val cardBg = if (isDark) AppColors.DarkCard else AppColors.LightCard
    val borderCol = if (isDark) AppColors.DarkBorder else AppColors.LightBorder
    val textPrimary = if (isDark) AppColors.DarkTextPrimary else AppColors.LightTextPrimary
    val textSecondary = if (isDark) AppColors.DarkTextSecondary else AppColors.LightTextSecondary

    val filteredLogs = remember(logs, filterText) {
        if (filterText.isBlank()) logs
        else logs.filter { it.contains(filterText, ignoreCase = true) }
    }

    LaunchedEffect(filteredLogs.size, autoScroll) {
        if (autoScroll && filteredLogs.isNotEmpty()) {
            listState.animateScrollToItem(filteredLogs.size - 1)
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .clip(RoundedCornerShape(8.dp))
            .background(cardBg)
            .border(1.dp, borderCol, RoundedCornerShape(8.dp))
            .padding(10.dp)
    ) {
        // Toolbar: Search + Auto-scroll + Clear
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = filterText,
                onValueChange = { filterText = it },
                placeholder = { Text("Filter logs...", fontSize = 12.sp) },
                leadingIcon = {
                    Icon(
                        imageVector = AppIcons.Search,
                        contentDescription = "Search",
                        modifier = Modifier.size(15.dp),
                        tint = textSecondary
                    )
                },
                singleLine = true,
                modifier = Modifier
                    .weight(1f)
                    .height(44.dp),
                shape = RoundedCornerShape(6.dp),
                textStyle = LocalTextStyle.current.copy(fontSize = 12.sp)
            )

            Spacer(modifier = Modifier.width(8.dp))

            FilterChip(
                selected = autoScroll,
                onClick = { autoScroll = !autoScroll },
                label = { Text("Auto-scroll", fontSize = 11.sp) },
                shape = RoundedCornerShape(6.dp),
                colors = FilterChipDefaults.filterChipColors(
                    selectedContainerColor = if (isDark) Color(0x1F3ECF8E) else Color(0x153ECF8E),
                    selectedLabelColor = AppColors.SupabaseGreen
                )
            )

            Spacer(modifier = Modifier.width(6.dp))

            SupabaseSecondaryButton(
                text = "Clear",
                onClick = onClearLogs,
                icon = AppIcons.Trash,
                isDark = isDark
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Logs console view
        SelectionContainer(
            modifier = Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(6.dp))
                .background(bg)
                .border(1.dp, borderCol, RoundedCornerShape(6.dp))
                .padding(8.dp)
        ) {
            LazyColumn(
                state = listState,
                modifier = Modifier.fillMaxSize()
            ) {
                if (filteredLogs.isEmpty()) {
                    item {
                        Text(
                            text = if (logs.isEmpty()) "No log entries yet." else "No matching log entries.",
                            fontSize = 12.sp,
                            color = textSecondary,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                } else {
                    items(filteredLogs) { line ->
                        val lineCol = when {
                            line.contains("[OK]", ignoreCase = true) -> AppColors.SupabaseGreen
                            line.contains("[ERR]", ignoreCase = true) || line.contains("error", ignoreCase = true) -> AppColors.StatusError
                            line.contains("[SKIP]", ignoreCase = true) -> AppColors.StatusWarning
                            line.contains("[GPU]", ignoreCase = true) -> AppColors.SupabaseGreen
                            line.contains("[CPU]", ignoreCase = true) -> AppColors.StatusRunning
                            line.contains("[CANCELLED]", ignoreCase = true) -> textSecondary
                            else -> textPrimary
                        }
                        Text(
                            text = line,
                            fontSize = 11.sp,
                            color = lineCol,
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 16.sp
                        )
                    }
                }
            }
        }
    }
}
