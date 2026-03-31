package com.lenslogic.app.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.lenslogic.app.screens.*

@Composable
fun LensLogicNavGraph(navController: NavHostController) {
    NavHost(navController = navController, startDestination = "login") {
        composable("login") {
            LoginScreen(
                onLoginSuccess = { navController.navigate("intro") }
            )
        }
        composable("intro") {
            IntroScreen(
                onSkipOrStart = { 
                    navController.navigate("home") {
                        popUpTo("login") { inclusive = true }
                    } 
                }
            )
        }
        composable("home") {
            HomeScreen(
                onScanClick = { navController.navigate("camera") }
            )
        }
        composable("camera") {
            CameraScreen(
                onImageCaptured = { navController.navigate("processing") }
            )
        }
        composable("processing") {
            ProcessingScreen(
                onProcessingComplete = { 
                    navController.navigate("result") {
                        popUpTo("camera") { inclusive = true }
                    } 
                }
            )
        }
        composable("result") {
            ResultScreen(
                onScanAnother = { 
                    navController.navigate("home") {
                        popUpTo("home") { inclusive = true }
                    } 
                }
            )
        }
    }
}
