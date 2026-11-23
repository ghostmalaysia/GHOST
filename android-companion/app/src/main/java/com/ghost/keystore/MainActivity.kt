package com.ghost.keystore

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
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
    HOME, APP_PIN, VAULT_HOME, VAULT_PIN_SETUP,
    VAULT_UNLOCK, DEVICES, AUDIT, RECOVERY
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
            "GHOST",
            color = ElectricBlue,
            fontSize = 30.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            "SECURITY CENTER",
            color = SoftText,
            fontSize = 12.sp,
            letterSpacing = 3.sp
        )

        Spacer(Modifier.height(24.dp))

        when (screen) {
            GhostScreen.HOME -> HomeScreen {
                screen = it
            }

            GhostScreen.APP_PIN -> PlaceholderScreen(
                "APP PIN",
                "Dedicated authentication for opening GHOST Security Center.",
                "Authentication is not implemented yet."
            )

            GhostScreen.VAULT_HOME -> VaultHomeScreen(
                onSetup = { screen = GhostScreen.VAULT_PIN_SETUP },
                onUnlock = { screen = GhostScreen.VAULT_UNLOCK }
            )

            GhostScreen.VAULT_PIN_SETUP -> VaultPinSetupScreen()

            GhostScreen.VAULT_UNLOCK -> VaultUnlockScreen()

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
            "UI PROTOTYPE • SECURITY FEATURES NOT ACTIVE",
            color = SoftText,
            fontSize = 10.sp,
            letterSpacing = 1.sp
        )
    }
}

@Composable
private fun HomeScreen(onOpen: (GhostScreen) -> Unit) {
    Text(
        "OWNER CONTROL",
        color = Color.White,
        fontSize = 20.sp,
        fontWeight = FontWeight.Bold
    )
    Spacer(Modifier.height(12.dp))

    StatusCard(
        "MOTHER OF GHOST",
        "NOT CONNECTED",
        "No live connection has been configured."
    )

    Spacer(Modifier.height(12.dp))

    StatusCard(
        "SECURE VAULT",
        "NOT CONFIGURED",
        "Encrypted storage is not active in this prototype."
    )

    Spacer(Modifier.height(20.dp))
    Text("SECURITY MODULES", color = ElectricBlue, fontWeight = FontWeight.Bold)
    Spacer(Modifier.height(10.dp))

    ModuleButton("APP PIN", "App authentication") {
        onOpen(GhostScreen.APP_PIN)
    }

    ModuleButton("SECURE VAULT", "Open Vault management") {
        onOpen(GhostScreen.VAULT_HOME)
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
private fun VaultHomeScreen(
    onSetup: () -> Unit,
    onUnlock: () -> Unit
) {
    Text(
        "GHOST SECURE VAULT",
        color = ElectricBlue,
        fontSize = 21.sp,
        fontWeight = FontWeight.Bold
    )

    Spacer(Modifier.height(8.dp))
    Text(
        "PRIVATE CREDENTIAL MANAGEMENT",
        color = SoftText,
        fontSize = 11.sp,
        letterSpacing = 1.sp
    )

    Spacer(Modifier.height(20.dp))

    StatusCard(
        "VAULT STATUS",
        "NOT CONFIGURED",
        "No credentials are stored. Encryption is not active."
    )

    Spacer(Modifier.height(14.dp))

    StatusCard(
        "AUTHENTICATION",
        "8-DIGIT VAULT PIN",
        "Independent from the GHOST App PIN."
    )

    Spacer(Modifier.height(14.dp))

    StatusCard(
        "AI ACCESS POLICY",
        "OWNER APPROVAL",
        "GHOST AI cannot access credentials without specific Owner approval."
    )

    Spacer(Modifier.height(22.dp))

    Button(
        onClick = onSetup,
        modifier = Modifier.fillMaxWidth()
    ) {
        Text("VAULT PIN SETUP")
    }

    Spacer(Modifier.height(10.dp))

    OutlinedButton(
        onClick = onUnlock,
        modifier = Modifier.fillMaxWidth()
    ) {
        Text("VIEW VAULT UNLOCK SCREEN")
    }

    Spacer(Modifier.height(12.dp))

    Text(
        "DESIGN PREVIEW ONLY. No PIN or credentials are accepted or stored.",
        color = SoftText,
        fontSize = 11.sp
    )
}

@Composable
private fun VaultPinSetupScreen() {
    Text(
        "VAULT PIN SETUP",
        color = ElectricBlue,
        fontSize = 21.sp,
        fontWeight = FontWeight.Bold
    )

    Spacer(Modifier.height(18.dp))

    StatusCard(
        "PIN CONFIGURATION",
        "8 DIGITS",
        "Your Vault PIN will be independent from your App PIN."
    )

    Spacer(Modifier.height(14.dp))

    StatusCard(
        "SECURITY DESIGN",
        "OWNER CONTROLLED",
        "PIN verification, attempt limits and secure key protection must be implemented before activation."
    )

    Spacer(Modifier.height(14.dp))

    StatusCard(
        "CURRENT STATUS",
        "NOT ACTIVE",
        "This preview does not accept or save a PIN."
    )

    Spacer(Modifier.height(18.dp))

    Text(
        "Planned security controls",
        color = ElectricBlue,
        fontWeight = FontWeight.Bold
    )

    Spacer(Modifier.height(10.dp))

    Text("• Separate Vault authentication")
    Text("• Secure PIN verification")
    Text("• Failed-attempt protection")
    Text("• Android Keystore integration")
    Text("• Encrypted Vault key protection")
}

@Composable
private fun VaultUnlockScreen() {
    Text(
        "VAULT UNLOCK",
        color = ElectricBlue,
        fontSize = 21.sp,
        fontWeight = FontWeight.Bold
    )

    Spacer(Modifier.height(18.dp))

    StatusCard(
        "AUTHENTICATION",
        "8-DIGIT VAULT PIN",
        "The Vault will require its own authentication."
    )

    Spacer(Modifier.height(14.dp))

    StatusCard(
        "ACCESS STATUS",
        "LOCKED",
        "Vault authentication has not been implemented."
    )

    Spacer(Modifier.height(14.dp))

    Text(
        "Unlock interface preview only.",
        color = SoftText,
        fontSize = 12.sp
    )

    Spacer(Modifier.height(10.dp))

    Text(
        "No PIN entry is available in this prototype. No credentials can be accessed.",
        color = SoftText,
        fontSize = 12.sp
    )
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
            Text(title, color = SoftText, fontSize = 12.sp)
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
        "MODULE DESCRIPTION",
        "PLANNED",
        description
    )

    Spacer(Modifier.height(12.dp))

    StatusCard(
        "IMPLEMENTATION STATUS",
        "NOT ACTIVE",
        status
    )
}
