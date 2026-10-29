package org.example.project.platform

import org.example.project.models.AppSettings
import java.io.File
import kotlinx.serialization.json.Json

object JvmSettingsStore {
    private val json = Json {
        ignoreUnknownKeys = true
        prettyPrint = true
        encodeDefaults = true
    }

    private val settingsFile: File
        get() {
            val isWindows = System.getProperty("os.name").lowercase().contains("win")
            return if (isWindows) {
                val appData = System.getenv("APPDATA") ?: System.getProperty("user.home")
                File(appData, "MediaCrush/settings.json")
            } else {
                val home = System.getProperty("user.home")
                File(home, ".config/mediacrush/settings.json")
            }
        }

    fun loadSettings(): AppSettings {
        return try {
            val file = settingsFile
            if (file.exists()) {
                json.decodeFromString<AppSettings>(file.readText())
            } else {
                AppSettings()
            }
        } catch (_: Exception) {
            AppSettings()
        }
    }

    fun saveSettings(settings: AppSettings) {
        try {
            val file = settingsFile
            file.parentFile?.mkdirs()
            file.writeText(json.encodeToString(AppSettings.serializer(), settings))
        } catch (_: Exception) {}
    }
}
