package com.lenslogic.app.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun CameraScreen(onImageCaptured: () -> Unit) {
    // Placeholder for CameraX implementation
    Box(
        modifier = Modifier.fillMaxSize().background(Color.Black),
        contentAlignment = Alignment.Center
    ) {
        Text("Camera Preview (CameraX)", color = Color.White)
        
        Button(
            onClick = onImageCaptured,
            modifier = Modifier.align(Alignment.BottomCenter).padding(32.dp)
        ) {
            Text("Capture")
        }
    }
}
