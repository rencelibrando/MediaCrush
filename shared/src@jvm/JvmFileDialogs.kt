package org.example.project.platform

import java.awt.FileDialog
import java.awt.Frame
import java.io.File
import javax.swing.JFileChooser
import javax.swing.SwingUtilities
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

object JvmFileDialogs {
    suspend fun pickFiles(title: String, extensions: List<String>): List<String> = withContext(Dispatchers.IO) {
        val isMac = System.getProperty("os.name").lowercase().contains("mac")
        val isWindows = System.getProperty("os.name").lowercase().contains("win")

        if (isMac || isWindows) {
            val frame: Frame? = null
            val dialog = FileDialog(frame, title, FileDialog.LOAD)
            dialog.isMultipleMode = true
            dialog.isVisible = true
            val files = dialog.files
            dialog.dispose()
            files?.map { it.absolutePath } ?: emptyList()
        } else {
            // Linux / Zenity or JFileChooser fallback
            var chosen = emptyList<String>()
            val r = JvmHardwareDetector.runCommand(listOf(
                "zenity", "--file-selection", "--multiple", "--separator=|",
                "--title=$title"
            ), timeoutSec = 60)
            if (r.exitCode == 0 && r.stdout.isNotBlank()) {
                chosen = r.stdout.split("|").map { it.trim() }.filter { it.isNotEmpty() }
            } else {
                SwingUtilities.invokeAndWait {
                    val chooser = JFileChooser()
                    chooser.dialogTitle = title
                    chooser.isMultiSelectionEnabled = true
                    val ret = chooser.showOpenDialog(null)
                    if (ret == JFileChooser.APPROVE_OPTION) {
                        chosen = chooser.selectedFiles.map { it.absolutePath }
                    }
                }
            }
            chosen
        }
    }

    suspend fun pickFolder(title: String): String? = withContext(Dispatchers.IO) {
        // Try zenity on Linux first for a modern desktop look
        val isLinux = !System.getProperty("os.name").lowercase().let { it.contains("win") || it.contains("mac") }
        if (isLinux) {
            val r = JvmHardwareDetector.runCommand(listOf("zenity", "--file-selection", "--directory", "--title=$title"), timeoutSec = 60)
            if (r.exitCode == 0 && r.stdout.isNotBlank()) {
                return@withContext r.stdout.trim()
            }
        }

        var chosen: String? = null
        SwingUtilities.invokeAndWait {
            val chooser = JFileChooser()
            chooser.dialogTitle = title
            chooser.fileSelectionMode = JFileChooser.DIRECTORIES_ONLY
            chooser.isAcceptAllFileFilterUsed = false
            val ret = chooser.showOpenDialog(null)
            if (ret == JFileChooser.APPROVE_OPTION) {
                chosen = chooser.selectedFile?.absolutePath
            }
        }
        chosen
    }

    fun scanFolder(folderPath: String, extensions: Set<String>): List<String> {
        val root = File(folderPath)
        if (!root.isDirectory) return emptyList()
        val results = mutableListOf<String>()
        root.walkTopDown().forEach { file ->
            if (file.isFile) {
                val idx = file.name.lastIndexOf('.')
                if (idx != -1) {
                    val ext = file.name.substring(idx).lowercase()
                    if (extensions.contains(ext)) {
                        results.add(file.absolutePath)
                    }
                }
            }
        }
        return results
    }
}
