package com.lenslogic.app.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay

@Composable
fun ProcessingScreen(onProcessingComplete: () -> Unit) {
    LaunchedEffect(Unit) {
        // Simulate ML processing delay
        delay(3000)
        onProcessingComplete()
    }
    
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CircularProgressIndicator()
        Spacer(modifier = Modifier.height(24.dp))
        Text("Analyzing Architecture...", style = MaterialTheme.typography.titleLarge)
        Text("Running Vision AI Model", style = MaterialTheme.typography.bodyMedium)
    }
}
