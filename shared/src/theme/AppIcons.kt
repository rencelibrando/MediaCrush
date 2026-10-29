package org.example.project.theme

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.PathBuilder
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.unit.dp

object AppIcons {
    private fun vector(
        name: String,
        width: Float = 24f,
        height: Float = 24f,
        block: PathBuilder.() -> Unit
    ): ImageVector {
        return ImageVector.Builder(
            name = name,
            defaultWidth = width.dp,
            defaultHeight = height.dp,
            viewportWidth = width,
            viewportHeight = height
        ).apply {
            path(
                fill = null,
                stroke = SolidColor(Color.White),
                strokeLineWidth = 2f,
                strokeLineCap = StrokeCap.Round,
                strokeLineJoin = StrokeJoin.Round,
                pathBuilder = block
            )
        }.build()
    }

    private fun filledVector(
        name: String,
        width: Float = 24f,
        height: Float = 24f,
        block: PathBuilder.() -> Unit
    ): ImageVector {
        return ImageVector.Builder(
            name = name,
            defaultWidth = width.dp,
            defaultHeight = height.dp,
            viewportWidth = width,
            viewportHeight = height
        ).apply {
            path(
                fill = SolidColor(Color.White),
                stroke = null,
                pathBuilder = block
            )
        }.build()
    }

    // MediaCrush Brand Logo: Unique custom media compression mark (dual precision brackets compacting a media play core)
    val MediaCrushLogo = filledVector("MediaCrushLogo") {
        // Left compressive clamp
        moveTo(3f, 4f)
        lineTo(9f, 4f)
        lineTo(6f, 8.5f)
        lineTo(6f, 15.5f)
        lineTo(9f, 20f)
        lineTo(3f, 20f)
        close()

        // Right compressive clamp
        moveTo(21f, 4f)
        lineTo(15f, 4f)
        lineTo(18f, 8.5f)
        lineTo(18f, 15.5f)
        lineTo(15f, 20f)
        lineTo(21f, 20f)
        close()

        // Center media play core (compacted media unit)
        moveTo(9f, 7.5f)
        lineTo(15.5f, 12f)
        lineTo(9f, 16.5f)
        close()
    }

    // Play icon (filled)
    val Play = filledVector("Play") {
        moveTo(6f, 4f)
        lineTo(20f, 12f)
        lineTo(6f, 20f)
        close()
    }

    // Pause icon (filled two bars)
    val Pause = filledVector("Pause") {
        moveTo(6f, 5f)
        lineTo(10f, 5f)
        lineTo(10f, 19f)
        lineTo(6f, 19f)
        close()
        moveTo(14f, 5f)
        lineTo(18f, 5f)
        lineTo(18f, 19f)
        lineTo(14f, 19f)
        close()
    }

    // Stop icon (filled square)
    val Stop = filledVector("Stop") {
        moveTo(6f, 6f)
        lineTo(18f, 6f)
        lineTo(18f, 18f)
        lineTo(6f, 18f)
        close()
    }

    // Close / X icon
    val Close = vector("Close") {
        moveTo(18f, 6f)
        lineTo(6f, 18f)
        moveTo(6f, 6f)
        lineTo(18f, 18f)
    }

    // Plus icon
    val Plus = vector("Plus") {
        moveTo(12f, 5f)
        lineTo(12f, 19f)
        moveTo(5f, 12f)
        lineTo(19f, 12f)
    }

    // Folder icon
    val Folder = vector("Folder") {
        moveTo(2f, 7f)
        lineTo(2f, 19f)
        lineTo(22f, 19f)
        lineTo(22f, 9f)
        lineTo(12f, 9f)
        lineTo(10f, 7f)
        close()
    }

    // File icon
    val File = vector("File") {
        moveTo(14f, 2f)
        lineTo(6f, 2f)
        lineTo(6f, 22f)
        lineTo(18f, 22f)
        lineTo(18f, 6f)
        close()
        moveTo(14f, 2f)
        lineTo(14f, 6f)
        lineTo(18f, 6f)
    }

    // Video icon
    val Video = vector("Video") {
        moveTo(15f, 7f)
        lineTo(3f, 7f)
        lineTo(3f, 17f)
        lineTo(15f, 17f)
        close()
        moveTo(15f, 10f)
        lineTo(21f, 6f)
        lineTo(21f, 18f)
        lineTo(15f, 14f)
    }

    // Image icon
    val Image = vector("Image") {
        moveTo(3f, 5f)
        lineTo(21f, 5f)
        lineTo(21f, 19f)
        lineTo(3f, 19f)
        close()
        moveTo(8.5f, 10f)
        // small circle/dot for sun: center 8.5, 10
        moveTo(21f, 15f)
        lineTo(16f, 10f)
        lineTo(5f, 19f)
    }

    // Settings / Mechanical Cogwheel icon (Distinct 8-toothed gear with center bore)
    val Settings = vector("Settings") {
        // Continuous mechanical cog perimeter with square teeth
        moveTo(10.3f, 5.8f)
        lineTo(10.4f, 2.7f)
        lineTo(13.6f, 2.7f)
        lineTo(13.7f, 5.8f)
        lineTo(15.3f, 6.4f)
        lineTo(17.4f, 4.2f)
        lineTo(19.8f, 6.6f)
        lineTo(17.6f, 8.7f)
        lineTo(18.3f, 10.3f)
        lineTo(21.4f, 10.4f)
        lineTo(21.4f, 13.6f)
        lineTo(18.3f, 13.7f)
        lineTo(17.6f, 15.3f)
        lineTo(19.8f, 17.4f)
        lineTo(17.4f, 19.8f)
        lineTo(15.3f, 17.6f)
        lineTo(13.7f, 18.2f)
        lineTo(13.6f, 21.3f)
        lineTo(10.4f, 21.3f)
        lineTo(10.3f, 18.2f)
        lineTo(8.7f, 17.6f)
        lineTo(6.6f, 19.8f)
        lineTo(4.2f, 17.4f)
        lineTo(6.4f, 15.3f)
        lineTo(5.7f, 13.7f)
        lineTo(2.6f, 13.6f)
        lineTo(2.6f, 10.4f)
        lineTo(5.7f, 10.3f)
        lineTo(6.4f, 8.7f)
        lineTo(4.2f, 6.6f)
        lineTo(6.6f, 4.2f)
        lineTo(8.7f, 6.4f)
        close()

        // Center axle bore hole
        moveTo(12f, 8.8f)
        lineTo(14.3f, 9.7f)
        lineTo(15.2f, 12f)
        lineTo(14.3f, 14.3f)
        lineTo(12f, 15.2f)
        lineTo(9.7f, 14.3f)
        lineTo(8.8f, 12f)
        lineTo(9.7f, 9.7f)
        close()
    }

    // Sliders / Controls / Preferences icon
    val Sliders = vector("Sliders") {
        moveTo(3f, 6f); lineTo(21f, 6f)
        moveTo(8f, 3.5f); lineTo(8f, 8.5f)
        moveTo(3f, 12f); lineTo(21f, 12f)
        moveTo(16f, 9.5f); lineTo(16f, 14.5f)
        moveTo(3f, 18f); lineTo(21f, 18f)
        moveTo(11f, 15.5f); lineTo(11f, 20.5f)
    }

    // Activity / Pulse / Diagnostics icon
    val Diagnostics = vector("Diagnostics") {
        moveTo(3f, 12f)
        lineTo(7f, 12f)
        lineTo(10f, 4f)
        lineTo(14f, 20f)
        lineTo(17f, 12f)
        lineTo(21f, 12f)
    }

    // Sun icon
    val Sun = vector("Sun") {
        moveTo(12f, 8f)
        lineTo(14.8f, 9.2f)
        lineTo(16f, 12f)
        lineTo(14.8f, 14.8f)
        lineTo(12f, 16f)
        lineTo(9.2f, 14.8f)
        lineTo(8f, 12f)
        lineTo(9.2f, 9.2f)
        close()
        moveTo(12f, 2f); lineTo(12f, 4f)
        moveTo(12f, 20f); lineTo(12f, 22f)
        moveTo(2f, 12f); lineTo(4f, 12f)
        moveTo(20f, 12f); lineTo(22f, 12f)
        moveTo(4.93f, 4.93f); lineTo(6.34f, 6.34f)
        moveTo(17.66f, 17.66f); lineTo(19.07f, 19.07f)
        moveTo(19.07f, 4.93f); lineTo(17.66f, 6.34f)
        moveTo(6.34f, 17.66f); lineTo(4.93f, 19.07f)
    }

    // Moon icon
    val Moon = vector("Moon") {
        moveTo(21f, 12.79f)
        lineTo(19.5f, 14.8f)
        lineTo(17.2f, 16.2f)
        lineTo(14.7f, 16.7f)
        lineTo(12f, 16.5f)
        lineTo(9.5f, 15.5f)
        lineTo(7.5f, 13.8f)
        lineTo(6.2f, 11.5f)
        lineTo(5.8f, 9f)
        lineTo(6.3f, 6.5f)
        lineTo(7.7f, 4.3f)
        lineTo(8.5f, 3f)
        lineTo(8f, 5f)
        lineTo(8.5f, 8.5f)
        lineTo(10.5f, 11.5f)
        lineTo(13.5f, 13.5f)
        lineTo(17f, 14f)
        lineTo(20f, 13.5f)
        close()
    }

    // Refresh icon
    val Refresh = vector("Refresh") {
        moveTo(21f, 4f); lineTo(21f, 9f); lineTo(16f, 9f)
        moveTo(3f, 20f); lineTo(3f, 15f); lineTo(8f, 15f)
        moveTo(20.49f, 15f)
        lineTo(18.5f, 18.5f)
        lineTo(15f, 20.5f)
        lineTo(11f, 20.5f)
        lineTo(7.5f, 18.5f)
        lineTo(5.5f, 15f)
        moveTo(3.51f, 9f)
        lineTo(5.5f, 5.5f)
        lineTo(9f, 3.5f)
        lineTo(13f, 3.5f)
        lineTo(16.5f, 5.5f)
        lineTo(18.5f, 9f)
    }

    // Trash / Clear icon
    val Trash = vector("Trash") {
        moveTo(3f, 6f)
        lineTo(21f, 6f)
        moveTo(19f, 6f)
        lineTo(18f, 20f)
        lineTo(6f, 20f)
        lineTo(5f, 6f)
        moveTo(9f, 6f)
        lineTo(9f, 3f)
        lineTo(15f, 3f)
        lineTo(15f, 6f)
    }

    // Search icon
    val Search = vector("Search") {
        moveTo(16.65f, 16.65f)
        lineTo(21f, 21f)
        moveTo(10.5f, 17f)
        lineTo(13.5f, 16.2f)
        lineTo(16f, 14f)
        lineTo(17f, 10.5f)
        lineTo(16f, 7f)
        lineTo(13.5f, 4.8f)
        lineTo(10.5f, 4f)
        lineTo(7.5f, 4.8f)
        lineTo(5f, 7f)
        lineTo(4f, 10.5f)
        lineTo(5f, 14f)
        lineTo(7.5f, 16.2f)
        close()
    }

    // Check icon
    val Check = vector("Check") {
        moveTo(20f, 6f)
        lineTo(9f, 17f)
        lineTo(4f, 12f)
    }

    // CPU icon
    val Cpu = vector("Cpu") {
        moveTo(4f, 4f)
        lineTo(20f, 4f)
        lineTo(20f, 20f)
        lineTo(4f, 20f)
        close()
        moveTo(9f, 9f)
        lineTo(15f, 9f)
        lineTo(15f, 15f)
        lineTo(9f, 15f)
        close()
        moveTo(9f, 1f); lineTo(9f, 4f)
        moveTo(15f, 1f); lineTo(15f, 4f)
        moveTo(9f, 20f); lineTo(9f, 23f)
        moveTo(15f, 20f); lineTo(15f, 23f)
        moveTo(1f, 9f); lineTo(4f, 9f)
        moveTo(1f, 15f); lineTo(4f, 15f)
        moveTo(20f, 9f); lineTo(23f, 9f)
        moveTo(20f, 15f); lineTo(23f, 15f)
    }

    // Lightning / Bolt icon
    val Bolt = filledVector("Bolt") {
        moveTo(13f, 2f)
        lineTo(4f, 14f)
        lineTo(11f, 14f)
        lineTo(10f, 22f)
        lineTo(19f, 10f)
        lineTo(12f, 10f)
        close()
    }
}
