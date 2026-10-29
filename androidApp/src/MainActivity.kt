package org.example.project

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import org.example.project.platform.PlatformBridge

class MainActivity : ComponentActivity() {

    private var pendingFilesCallback: ((List<String>) -> Unit)? = null
    private var pendingFolderCallback: ((String?) -> Unit)? = null

    private val pickFilesLauncher = registerForActivityResult(
        ActivityResultContracts.OpenMultipleDocuments()
    ) { uris ->
        val results = uris.mapNotNull { uri ->
            PlatformBridge.copyUriToAppStorage(this, uri)
        }
        pendingFilesCallback?.invoke(results)
        pendingFilesCallback = null
    }

    private val pickFolderLauncher = registerForActivityResult(
        ActivityResultContracts.OpenDocumentTree()
    ) { uri ->
        val path = uri?.let { PlatformBridge.resolveTreeUri(this, it) }
        pendingFolderCallback?.invoke(path)
        pendingFolderCallback = null
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)

        PlatformBridge.init(
            context = applicationContext,
            onPickFiles = { _, callback ->
                pendingFilesCallback = callback
                pickFilesLauncher.launch(arrayOf("*/*"))
            },
            onPickFolder = { callback ->
                pendingFolderCallback = callback
                pickFolderLauncher.launch(null)
            }
        )

        setContent {
            App()
        }
    }
}

@Preview
@Composable
fun AppAndroidPreview() {
    App()
}
