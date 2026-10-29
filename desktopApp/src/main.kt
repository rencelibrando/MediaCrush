package org.example.project

import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import androidx.compose.ui.window.rememberWindowState
import java.awt.Dimension

fun main() = application {
    val windowState = rememberWindowState(width = 1120.dp, height = 760.dp)
    Window(
        onCloseRequest = ::exitApplication,
        state = windowState,
        title = "MediaCrush"
    ) {
        window.minimumSize = Dimension(820, 560)
        App()
    }
}
