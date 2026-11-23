package com.ghost.keystore

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val Navy = Color(0xFF071426)
private val Panel = Color(0xFF10243D)
private val ElectricBlue = Color(0xFF35A7FF)
private val SoftText = Color(0xFFB8C9DC)

private enum class GhostScreen {
    HOME, APP_PIN, VAULT_PIN, DEVICES, AUDIT, RECOVERY
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = ElectricBlue,
                    background = Navy,
                    surface = Panel,
                    onPrimary = Navy,
                    onBackground = Color.White,
                    onSurface = Color.White
                )
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = Navy
                ) {
                    GhostApp()
                }
            }
        }
    }
}

@Composable
private fun GhostApp() {
    var screen by remember { mutableStateOf(GhostScreen.HOME) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Navy)
            .verticalScroll(rememberScrollState())
            .padding(20.dp)
    ) {
        Text(
            text = "GHOST",
            color = ElectricBlue,
            fontSize = 30.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = "SECURITY CENTER",
            color = SoftText,
            fontSize = 12.sp,
            letterSpacing = 3.sp
        )

        Spacer(Modifier.height(24.dp))

        when (screen) {
            GhostScreen.HOME -> HomeScreen(
                onOpen = { screen = it }
            )
            GhostScreen.APP_PIN -> PlaceholderScreen(
                "APP PIN",
                "Dedicated authentication for opening GHOST Security Center.",
                "Authentication is not implemented yet."
            )
            GhostScreen.VAULT_PIN -> PlaceholderScreen(
                "VAULT PIN",
                "Separate authentication for opening the Secure Vault.",
                "Vault protection is not implemented yet."
            )
            GhostScreen.DEVICES -> PlaceholderScreen(
                "DEVICE MANAGEMENT",
                "Manage enrolled GHOST devices and synchronization.",
                "No device connection has been configured."
            )
            GhostScreen.AUDIT -> PlaceholderScreen(
                "SECURITY AUDIT",
                "Review security events and owner approvals.",
                "Audit event storage is not implemented yet."
            )
            GhostScreen.RECOVERY -> PlaceholderScreen(
                "OWNER RECOVERY",
                "Recovery Key and new-device registration.",
                "Recovery flow is not implemented yet."
            )
        }

        if (screen != GhostScreen.HOME) {
            Spacer(Modifier.height(24.dp))
            OutlinedButton(
                onClick = { screen = GhostScreen.HOME },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("BACK TO DASHBOARD")
            }
        }

        Spacer(Modifier.height(24.dp))
        Text(
            text = "PROTOTYPE • SECURITY FEATURES NOT ACTIVE",
            color = SoftText,
            fontSize = 10.sp,
            letterSpacing = 1.sp
        )
    }
}

@Composable
private fun HomeScreen(onOpen: (GhostScreen) -> Unit) {
    Text(
        text = "OWNER CONTROL",
        color = Color.White,
        fontSize = 20.sp,
        fontWeight = FontWeight.Bold
    )
    Spacer(Modifier.height(12.dp))

    StatusCard(
        title = "MOTHER OF GHOST",
        status = "NOT CONNECTED",
        detail = "No live connection has been configured."
    )

    Spacer(Modifier.height(12.dp))

    StatusCard(
        title = "SECURE VAULT",
        status = "NOT CONFIGURED",
        detail = "Encrypted storage is not active in this prototype."
    )

    Spacer(Modifier.height(20.dp))

    Text(
        text = "SECURITY MODULES",
        color = ElectricBlue,
        fontWeight = FontWeight.Bold
    )
    Spacer(Modifier.height(10.dp))

    ModuleButton("APP PIN", "Open app authentication setup") {
        onOpen(GhostScreen.APP_PIN)
    }
    ModuleButton("VAULT PIN", "Separate Vault authentication") {
        onOpen(GhostScreen.VAULT_PIN)
    }
    ModuleButton("DEVICE MANAGEMENT", "Phone and laptop enrollment") {
        onOpen(GhostScreen.DEVICES)
    }
    ModuleButton("SECURITY AUDIT", "Owner approvals and event history") {
        onOpen(GhostScreen.AUDIT)
    }
    ModuleButton("OWNER RECOVERY", "Recovery Key and device recovery") {
        onOpen(GhostScreen.RECOVERY)
    }
}

@Composable
private fun StatusCard(
    title: String,
    status: String,
    detail: String
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Panel)
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(
                title,
                color = SoftText,
                fontSize = 12.sp,
                letterSpacing = 1.sp
            )
            Spacer(Modifier.height(6.dp))
            Text(
                status,
                color = ElectricBlue,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp
            )
            Spacer(Modifier.height(4.dp))
            Text(detail, color = SoftText, fontSize = 12.sp)
        }
    }
}

@Composable
private fun ModuleButton(
    title: String,
    description: String,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 5.dp),
        colors = CardDefaults.cardColors(containerColor = Panel)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(3.dp))
                Text(description, color = SoftText, fontSize = 11.sp)
            }
            Button(
                onClick = onClick,
                colors = ButtonDefaults.buttonColors(
                    containerColor = ElectricBlue,
                    contentColor = Navy
                )
            ) {
                Text("OPEN")
            }
        }
    }
}

@Composable
private fun PlaceholderScreen(
    title: String,
    description: String,
    status: String
) {
    Text(
        title,
        color = ElectricBlue,
        fontSize = 20.sp,
        fontWeight = FontWeight.Bold
    )
    Spacer(Modifier.height(16.dp))
    StatusCard(
        title = "MODULE DESCRIPTION",
        status = "PLANNED",
        detail = description
    )
    Spacer(Modifier.height(12.dp))
    StatusCard(
        title = "IMPLEMENTATION STATUS",
        status = "NOT ACTIVE",
        detail = status
    )
}
