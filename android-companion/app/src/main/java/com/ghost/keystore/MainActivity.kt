package com.ghost.keystore

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.core.content.FileProvider
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val Navy = Color(0xFF071426)
private val Panel = Color(0xFF10243D)
private val ElectricBlue = Color(0xFF35A7FF)
private val SoftText = Color(0xFFB8C9DC)
private val Warning = Color(0xFFFFB74D)

private enum class GhostScreen {
    HOME, APP_PIN, VAULT_HOME, VAULT_PIN_SETUP, VAULT_UNLOCK,
    VAULT_ENTRIES, DEVICES, AUDIT, RECOVERY, AI_LINK
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
                Surface(modifier = Modifier.fillMaxSize(), color = Navy) {
                    GhostApp()
                }
            }
        }
    }
}

@Composable
private fun GhostApp() {
    val context = LocalContext.current
    var screen by remember { mutableStateOf(GhostScreen.HOME) }
    var unlockedPin by remember { mutableStateOf("") }
    var updateInfo by remember { mutableStateOf<UpdateInfo?>(null) }
    var updateStatus by remember { mutableStateOf("") }
    val events = remember { mutableStateListOf<String>() }

    fun log(message: String) {
        val stamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
            .format(Date())
        events.add(0, "$stamp  $message")
        if (events.size > 50) events.removeAt(events.size - 1)
    }

    fun open(next: GhostScreen) {
        log("Buka skrin ${next.name}")
        screen = next
    }

    fun back() {
        unlockedPin = ""
        log("Kembali ke dashboard")
        screen = GhostScreen.HOME
    }

    fun checkUpdate() {
        updateStatus = "Sedang menyemak kemas kini..."
        updateInfo = null
        Thread {
            val info = UpdateChecker.latest()
            Handler(Looper.getMainLooper()).post {
                if (info != null && UpdateChecker.isNewer(info.version, "0.2.0")) {
                    updateInfo = info
                    updateStatus = "Versi ${info.version} tersedia."
                } else {
                    updateStatus = "Tiada kemas kini baharu."
                }
            }
        }.start()
    }

    fun installUpdate(info: UpdateInfo) {
        updateStatus = "Memuat turun dan menyemak integriti..."
        Thread {
            val file = UpdateChecker.downloadAndVerify(context, info)
            Handler(Looper.getMainLooper()).post {
                if (file == null) {
                    updateStatus = "Muat turun gagal atau semakan integriti tidak lulus."
                } else {
                    try {
                        val uri = FileProvider.getUriForFile(
                            context,
                            "${context.packageName}.fileprovider",
                            file
                        )
                        val intent = Intent(Intent.ACTION_VIEW).apply {
                            setDataAndType(uri, "application/vnd.android.package-archive")
                            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        context.startActivity(intent)
                        updateStatus = "Sila sahkan pemasangan pada skrin sistem."
                        log("Pemasang APK dibuka")
                    } catch (_: Exception) {
                        updateStatus = "Tidak dapat membuka pemasang APK."
                        log("Pemasang APK gagal dibuka")
                    }
                }
            }
        }.start()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Navy)
            .verticalScroll(rememberScrollState())
            .padding(20.dp)
    ) {
        Text("GHOST", color = ElectricBlue, fontSize = 30.sp, fontWeight = FontWeight.Bold)
        Text("SECURITY CENTER", color = SoftText, fontSize = 12.sp, letterSpacing = 3.sp)
        Spacer(Modifier.height(6.dp))
        Text("v0.2.0 • LOCAL-DEVICE BUILD", color = Warning, fontSize = 10.sp)

        Spacer(Modifier.height(20.dp))

        when (screen) {
            GhostScreen.HOME -> HomeScreen(
                vaultConfigured = VaultStore.isConfigured(context),
                endpoint = VaultStore.getEndpoint(context),
                updateStatus = updateStatus,
                hasUpdate = updateInfo != null,
                onOpen = { next -> open(next) },
                onCheckUpdate = { checkUpdate() },
                onInstall = { updateInfo?.let { installUpdate(it) } },
            )

            GhostScreen.APP_PIN -> PlaceholderScreen(
                "APP PIN",
                "Dedicated authentication for opening GHOST Security Center.",
                "Screen lock is provided by Android. No separate App PIN is stored."
            )

            GhostScreen.VAULT_HOME -> VaultHomeScreen(
                configured = VaultStore.isConfigured(context),
                onSetup = { open(GhostScreen.VAULT_PIN_SETUP) },
                onUnlock = { open(GhostScreen.VAULT_UNLOCK) },
            )

            GhostScreen.VAULT_PIN_SETUP -> VaultPinSetupScreen(
                context = context,
                onDone = {
                    log("Vault PIN ditetapkan")
                    open(GhostScreen.VAULT_HOME)
                },
                onError = { log("Vault PIN setup gagal") },
            )

            GhostScreen.VAULT_UNLOCK -> VaultUnlockScreen(
                context = context,
                onUnlocked = { pin ->
                    unlockedPin = pin
                    log("Vault dibuka")
                    open(GhostScreen.VAULT_ENTRIES)
                },
                onError = { log("Vault unlock gagal") },
            )

            GhostScreen.VAULT_ENTRIES -> VaultEntriesScreen(
                context = context,
                pin = unlockedPin,
                onLog = { message -> log(message) },
            )

            GhostScreen.DEVICES -> DevicesScreen()
            GhostScreen.AUDIT -> AuditScreen(events)
            GhostScreen.RECOVERY -> RecoveryScreen()
            GhostScreen.AI_LINK -> AiLinkScreen(
                context = context,
                onLog = { message -> log(message) }
            )
        }

        if (screen != GhostScreen.HOME) {
            Spacer(Modifier.height(24.dp))
            OutlinedButton(onClick = { back() }, modifier = Modifier.fillMaxWidth()) {
                Text("BACK TO DASHBOARD")
            }
        }

        Spacer(Modifier.height(24.dp))
        Text(
            "LOCAL ONLY • VAULT DATA NEVER LEAVES THIS DEVICE",
            color = Warning,
            fontSize = 10.sp,
            letterSpacing = 1.sp
        )
    }
}

@Composable
private fun HomeScreen(
    vaultConfigured: Boolean,
    endpoint: String,
    updateStatus: String,
    hasUpdate: Boolean,
    onOpen: (GhostScreen) -> Unit,
    onCheckUpdate: () -> Unit,
    onInstall: () -> Unit,
) {
    Text("OWNER CONTROL", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold)
    Spacer(Modifier.height(12.dp))

    StatusCard(
        "MOTHER OF GHOST",
        if (endpoint.isBlank()) "NOT CONFIGURED" else "ENDPOINT SAVED",
        if (endpoint.isBlank()) {
            "No GHOST AI address has been saved on this device."
        } else {
            "Address is saved locally. Connection is not tested automatically."
        }
    )
    Spacer(Modifier.height(12.dp))

    StatusCard(
        "SECURE VAULT",
        if (vaultConfigured) "CONFIGURED" else "NOT CONFIGURED",
        if (vaultConfigured) {
            "Entries are encrypted with a key held by Android Keystore."
        } else {
            "Set an 8-digit PIN before storing any entry."
        }
    )
    Spacer(Modifier.height(12.dp))

    StatusCard(
        "GHOST UPDATE",
        if (hasUpdate) "UPDATE AVAILABLE" else "NOT CHECKED",
        if (updateStatus.isBlank()) {
            "Check GitHub Releases for a newer signed APK."
        } else {
            updateStatus
        }
    )
    Spacer(Modifier.height(10.dp))
    Button(onClick = onCheckUpdate, modifier = Modifier.fillMaxWidth()) {
        Text("CHECK FOR UPDATE")
    }
    if (hasUpdate) {
        Spacer(Modifier.height(10.dp))
        Button(onClick = onInstall, modifier = Modifier.fillMaxWidth()) {
            Text("DOWNLOAD & INSTALL")
        }
    }
    Spacer(Modifier.height(18.dp))

    Text("SECURITY MODULES", color = ElectricBlue, fontWeight = FontWeight.Bold)
    Spacer(Modifier.height(10.dp))

    ModuleButton("APP PIN", "Android screen lock / device PIN") { onOpen(GhostScreen.APP_PIN) }
    ModuleButton("SECURE VAULT", "Create PIN, unlock and manage entries") {
        onOpen(GhostScreen.VAULT_HOME)
    }
    ModuleButton("DEVICE MANAGEMENT", "Read-only information about this device") {
        onOpen(GhostScreen.DEVICES)
    }
    ModuleButton("SECURITY AUDIT", "Local UI event log") { onOpen(GhostScreen.AUDIT) }
    ModuleButton("OWNER RECOVERY", "Design preview (not active)") {
        onOpen(GhostScreen.RECOVERY)
    }
    ModuleButton("GHOST AI LINK", "Save an endpoint address") { onOpen(GhostScreen.AI_LINK) }
}

@Composable
private fun VaultHomeScreen(
    configured: Boolean,
    onSetup: () -> Unit,
    onUnlock: () -> Unit,
) {
    Title("GHOST SECURE VAULT")
    Spacer(Modifier.height(16.dp))

    StatusCard(
        "VAULT STATUS",
        if (configured) "CONFIGURED" else "NOT CONFIGURED",
        if (configured) {
            "No entry is shown until the 8-digit PIN is verified."
        } else {
            "No PIN or entry exists yet."
        }
    )
    Spacer(Modifier.height(12.dp))

    StatusCard(
        "AI ACCESS POLICY",
        "NEVER SENT",
        "Vault entries are not shared with GHOST AI or any cloud service."
    )
    Spacer(Modifier.height(20.dp))

    if (!configured) {
        Button(onClick = onSetup, modifier = Modifier.fillMaxWidth()) {
            Text("SET 8-DIGIT VAULT PIN")
        }
    } else {
        Button(onClick = onUnlock, modifier = Modifier.fillMaxWidth()) {
            Text("UNLOCK VAULT")
        }
    }
    Spacer(Modifier.height(12.dp))
    WarningText(
        "This is device-local storage. It is not a replacement for a dedicated "
            + "password manager and has not been independently audited."
    )
}

@Composable
private fun VaultPinSetupScreen(
    context: android.content.Context,
    onDone: () -> Unit,
    onError: () -> Unit,
) {
    var pin by remember { mutableStateOf("") }
    var confirm by remember { mutableStateOf("") }
    var message by remember { mutableStateOf("") }

    Title("VAULT PIN SETUP")
    Spacer(Modifier.height(16.dp))

    OutlinedTextField(
        value = pin,
        onValueChange = { pin = it.filter { c -> c.isDigit() }.take(8) },
        label = { Text("8-digit PIN") },
        visualTransformation = PasswordVisualTransformation(),
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(10.dp))
    OutlinedTextField(
        value = confirm,
        onValueChange = { confirm = it.filter { c -> c.isDigit() }.take(8) },
        label = { Text("Confirm PIN") },
        visualTransformation = PasswordVisualTransformation(),
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(14.dp))

    if (message.isNotBlank()) WarningText(message)
    Spacer(Modifier.height(10.dp))

    Button(
        onClick = {
            when {
                !VaultStore.isValidPin(pin) -> message = "PIN mesti 8 digit angka."
                pin != confirm -> message = "PIN tidak sepadan."
                VaultStore.setup(context, pin) -> {
                    pin = ""
                    confirm = ""
                    onDone()
                }
                else -> {
                    message = "Vault sudah dikonfigurasi."
                    onError()
                }
            }
        },
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text("SAVE PIN")
    }
    Spacer(Modifier.height(10.dp))
    WarningText("The PIN cannot be recovered without clearing this app's data.")
}

@Composable
private fun VaultUnlockScreen(
    context: android.content.Context,
    onUnlocked: (String) -> Unit,
    onError: () -> Unit,
) {
    var pin by remember { mutableStateOf("") }
    var message by remember { mutableStateOf("") }
    val attempts = VaultStore.failedAttempts(context)

    Title("VAULT UNLOCK")
    Spacer(Modifier.height(16.dp))

    StatusCard(
        "ACCESS STATUS",
        if (VaultStore.isLocked(context)) "TEMPORARILY LOCKED" else "LOCKED",
        if (VaultStore.isLocked(context)) {
            "Too many failed attempts. Wait about 30 seconds."
        } else {
            "Failed attempts so far: $attempts of 5."
        }
    )
    Spacer(Modifier.height(14.dp))

    OutlinedTextField(
        value = pin,
        onValueChange = { pin = it.filter { c -> c.isDigit() }.take(8) },
        label = { Text("8-digit Vault PIN") },
        visualTransformation = PasswordVisualTransformation(),
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(12.dp))

    if (message.isNotBlank()) WarningText(message)
    Spacer(Modifier.height(10.dp))

    Button(
        onClick = {
            val entered = pin
            if (VaultStore.unlock(context, entered)) {
                pin = ""
                onUnlocked(entered)
            } else {
                message = "PIN salah atau vault sedang dikunci."
                onError()
            }
        },
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text("UNLOCK")
    }
}

@Composable
private fun VaultEntriesScreen(
    context: android.content.Context,
    pin: String,
    onLog: (String) -> Unit,
) {
    var entries by remember { mutableStateOf(VaultStore.readEntries(context, pin)) }
    var label by remember { mutableStateOf("") }
    var value by remember { mutableStateOf("") }
    var message by remember { mutableStateOf("") }

    Title("VAULT ENTRIES")
    Spacer(Modifier.height(14.dp))

    if (entries.isEmpty()) {
        StatusCard("RECORDS", "EMPTY", "No entry has been saved in the vault.")
    } else {
        entries.forEach { entry ->
            StatusCard(entry.label, "SAVED", entry.value)
            Spacer(Modifier.height(8.dp))
        }
    }
    Spacer(Modifier.height(16.dp))

    OutlinedTextField(
        value = label,
        onValueChange = { label = it.take(80) },
        label = { Text("Label") },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(10.dp))
    OutlinedTextField(
        value = value,
        onValueChange = { value = it.take(500) },
        label = { Text("Value") },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(12.dp))

    if (message.isNotBlank()) WarningText(message)
    Button(
        onClick = {
            if (VaultStore.addEntry(context, pin, label, value)) {
                entries = VaultStore.readEntries(context, pin)
                label = ""
                value = ""
                message = "Rekod disimpan."
                onLog("Vault entry ditambah")
            } else {
                message = "Gagal menyimpan rekod."
                onLog("Vault entry gagal")
            }
        },
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text("ADD ENTRY")
    }
    Spacer(Modifier.height(10.dp))
    WarningText("Entries remain on this device and are never sent to GHOST AI.")
}

@Composable
private fun DevicesScreen() {
    Title("DEVICE MANAGEMENT")
    Spacer(Modifier.height(16.dp))
    StatusCard("DEVICE", "${Build.MANUFACTURER} ${Build.MODEL}", "Read-only information from this phone.")
    Spacer(Modifier.height(10.dp))
    StatusCard("ANDROID VERSION", Build.VERSION.RELEASE, "SDK ${Build.VERSION.SDK_INT}")
    Spacer(Modifier.height(10.dp))
    StatusCard("ENROLLMENT", "NOT AVAILABLE", "No remote device is enrolled or synchronized.")
}

@Composable
private fun AuditScreen(events: List<String>) {
    Title("SECURITY AUDIT")
    Spacer(Modifier.height(16.dp))
    WarningText("Local UI event log only. This is not a tamper-proof security audit trail.")
    Spacer(Modifier.height(12.dp))
    if (events.isEmpty()) {
        StatusCard("EVENTS", "EMPTY", "No interface event has been recorded yet.")
    } else {
        events.forEach { event ->
            StatusCard("EVENT", "RECORDED", event)
            Spacer(Modifier.height(8.dp))
        }
    }
}

@Composable
private fun RecoveryScreen() {
    Title("OWNER RECOVERY")
    Spacer(Modifier.height(16.dp))
    StatusCard(
        "RECOVERY KEY",
        "NOT IMPLEMENTED",
        "No recovery key is generated or stored by this build."
    )
    Spacer(Modifier.height(10.dp))
    StatusCard(
        "NEW DEVICE REGISTRATION",
        "NOT IMPLEMENTED",
        "Enrollment requires a backend and owner verification design."
    )
    Spacer(Modifier.height(12.dp))
    WarningText("Do not treat this screen as a recovery mechanism.")
}

@Composable
private fun AiLinkScreen(context: android.content.Context, onLog: (String) -> Unit) {
    var endpoint by remember { mutableStateOf(VaultStore.getEndpoint(context)) }
    var message by remember { mutableStateOf("") }

    Title("GHOST AI LINK")
    Spacer(Modifier.height(16.dp))
    StatusCard(
        "DATA POLICY",
        "VAULT EXCLUDED",
        "Only a saved address is kept here. Vault entries are never transmitted."
    )
    Spacer(Modifier.height(14.dp))

    OutlinedTextField(
        value = endpoint,
        onValueChange = { endpoint = it.take(300) },
        label = { Text("GHOST AI API base URL") },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(12.dp))

    if (message.isNotBlank()) WarningText(message)
    Button(
        onClick = {
            VaultStore.saveEndpoint(context, endpoint)
            message = if (endpoint.isBlank()) "Alamat dikosongkan." else "Alamat disimpan."
            onLog("GHOST AI endpoint disimpan")
        },
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text("SAVE ENDPOINT")
    }
    Spacer(Modifier.height(10.dp))
    WarningText("No connection test or AI request is performed by this build.")
}

@Composable
private fun Title(text: String) {
    Text(text, color = ElectricBlue, fontSize = 21.sp, fontWeight = FontWeight.Bold)
}

@Composable
private fun WarningText(text: String) {
    Text(text, color = Warning, fontSize = 11.sp)
}

@Composable
private fun StatusCard(title: String, status: String, detail: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Panel)
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(title, color = SoftText, fontSize = 12.sp)
            Spacer(Modifier.height(6.dp))
            Text(status, color = ElectricBlue, fontWeight = FontWeight.Bold, fontSize = 18.sp)
            Spacer(Modifier.height(4.dp))
            Text(detail, color = SoftText, fontSize = 12.sp)
        }
    }
}

@Composable
private fun ModuleButton(title: String, description: String, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp),
        colors = CardDefaults.cardColors(containerColor = Panel)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
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
private fun PlaceholderScreen(title: String, description: String, status: String) {
    Title(title)
    Spacer(Modifier.height(16.dp))
    StatusCard("MODULE DESCRIPTION", "PLANNED", description)
    Spacer(Modifier.height(12.dp))
    StatusCard("IMPLEMENTATION STATUS", "NOT ACTIVE", status)
}
