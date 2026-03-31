package com.lenslogic.app.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun ResultScreen(onScanAnother: () -> Unit) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Generation Complete", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))
        
        Surface(
            color = MaterialTheme.colorScheme.surfaceVariant,
            modifier = Modifier.weight(1f).fillMaxWidth(),
            shape = MaterialTheme.shapes.medium
        ) {
            Text(
                text = """
                    from fastapi import FastAPI
                    
                    app = FastAPI()
                    
                    @app.get("/")
                    def read_root():
                        return {"status": "ok"}
                """.trimIndent(),
                modifier = Modifier.padding(16.dp),
                style = MaterialTheme.typography.bodyMedium
            )
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Button(
            onClick = onScanAnother,
            modifier = Modifier.fillMaxWidth().height(50.dp)
        ) {
            Text("Scan Another")
        }
    }
}
