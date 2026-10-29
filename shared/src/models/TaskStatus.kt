package org.example.project.models

enum class TaskStatus(val label: String) {
    QUEUED("Queued"),
    RUNNING("Running"),
    DONE("Done"),
    ERROR("Error"),
    SKIPPED("Skipped"),
    CANCELLED("Cancelled"),
    PAUSED("Paused")
}
