package com.ghost.keystore

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.security.KeyStore
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

data class VaultEntry(val label: String, val value: String)

object VaultStore {
    private const val PREFS_NAME = "ghost_vault_prefs"
    private const val KEY_ALIAS = "ghost_vault_aes_gcm"
    private const val FIELD_DATA = "vault_data"
    private const val FIELD_IV = "vault_iv"
    private const val FIELD_ATTEMPTS = "failed_attempts"
    private const val FIELD_LOCK_UNTIL = "lock_until_ms"
    private const val FIELD_ENDPOINT = "ghost_endpoint"
    private const val MAX_ATTEMPTS = 5
    private const val LOCK_MS = 30_000L

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private fun key(): SecretKey {
        val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val existing = keyStore.getEntry(KEY_ALIAS, null) as? KeyStore.SecretKeyEntry
        if (existing != null) return existing.secretKey

        val spec = KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .build()

        val generator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            "AndroidKeyStore"
        )
        generator.init(spec)
        return generator.generateKey()
    }

    private fun encrypt(plain: ByteArray): Pair<ByteArray, ByteArray> {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        return Pair(cipher.doFinal(plain), cipher.iv)
    }

    private fun decrypt(cipherText: ByteArray, iv: ByteArray): ByteArray {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, iv))
        return cipher.doFinal(cipherText)
    }

    private fun pinHash(pin: String, salt: ByteArray): String {
        val digest = MessageDigest.getInstance("SHA-256")
        digest.update(salt)
        return Base64.encodeToString(
            digest.digest(pin.toByteArray(Charsets.UTF_8)),
            Base64.NO_WRAP
        )
    }

    private fun encode(payload: JSONObject): Pair<String, String> {
        val (cipherText, iv) = encrypt(payload.toString().toByteArray(Charsets.UTF_8))
        return Pair(
            Base64.encodeToString(cipherText, Base64.NO_WRAP),
            Base64.encodeToString(iv, Base64.NO_WRAP)
        )
    }

    private fun decode(context: Context): JSONObject? {
        val stored = prefs(context)
        val data = stored.getString(FIELD_DATA, null) ?: return null
        val iv = stored.getString(FIELD_IV, null) ?: return null
        return try {
            val plain = decrypt(
                Base64.decode(data, Base64.NO_WRAP),
                Base64.decode(iv, Base64.NO_WRAP)
            )
            JSONObject(String(plain, Charsets.UTF_8))
        } catch (_: Exception) {
            null
        }
    }

    private fun save(context: Context, payload: JSONObject) {
        val (data, iv) = encode(payload)
        prefs(context).edit()
            .putString(FIELD_DATA, data)
            .putString(FIELD_IV, iv)
            .apply()
    }

    private fun entriesFrom(payload: JSONObject): List<VaultEntry> {
        val array = payload.optJSONArray("entries") ?: JSONArray()
        return (0 until array.length()).mapNotNull { index ->
            val item = array.optJSONObject(index) ?: return@mapNotNull null
            val label = item.optString("label", "")
            val value = item.optString("value", "")
            if (label.isBlank() || value.isBlank()) null else VaultEntry(label, value)
        }
    }

    fun isValidPin(pin: String) = pin.length == 8 && pin.all { it.isDigit() }

    fun isConfigured(context: Context) =
        prefs(context).getString(FIELD_DATA, null) != null

    fun lockedUntil(context: Context): Long =
        prefs(context).getLong(FIELD_LOCK_UNTIL, 0L)

    fun isLocked(context: Context): Boolean {
        val stored = prefs(context)
        return stored.getLong(FIELD_LOCK_UNTIL, 0L) > System.currentTimeMillis() ||
            stored.getInt(FIELD_ATTEMPTS, 0) >= MAX_ATTEMPTS
    }

    fun failedAttempts(context: Context): Int =
        prefs(context).getInt(FIELD_ATTEMPTS, 0)

    private fun recordFailure(context: Context) {
        val stored = prefs(context)
        val attempts = stored.getInt(FIELD_ATTEMPTS, 0) + 1
        val editor = stored.edit().putInt(FIELD_ATTEMPTS, attempts)
        if (attempts >= MAX_ATTEMPTS) {
            editor.putLong(FIELD_LOCK_UNTIL, System.currentTimeMillis() + LOCK_MS)
        }
        editor.apply()
    }

    private fun clearFailures(context: Context) {
        prefs(context).edit()
            .putInt(FIELD_ATTEMPTS, 0)
            .putLong(FIELD_LOCK_UNTIL, 0L)
            .apply()
    }

    private fun verify(payload: JSONObject, pin: String): Boolean {
        val saltText = payload.optString("salt", "")
        val expected = payload.optString("pin_hash", "")
        if (saltText.isBlank() || expected.isBlank()) return false
        val salt = Base64.decode(saltText, Base64.NO_WRAP)
        return pinHash(pin, salt) == expected
    }

    fun setup(context: Context, pin: String): Boolean {
        if (!isValidPin(pin) || isConfigured(context)) return false
        val salt = ByteArray(16).also { SecureRandom().nextBytes(it) }
        val payload = JSONObject().apply {
            put("salt", Base64.encodeToString(salt, Base64.NO_WRAP))
            put("pin_hash", pinHash(pin, salt))
            put("entries", JSONArray())
        }
        save(context, payload)
        clearFailures(context)
        return true
    }

    fun unlock(context: Context, pin: String): Boolean {
        if (isLocked(context)) return false
        val payload = decode(context) ?: return false
        if (!verify(payload, pin)) {
            recordFailure(context)
            return false
        }
        clearFailures(context)
        return true
    }

    fun readEntries(context: Context, pin: String): List<VaultEntry> {
        if (isLocked(context)) return emptyList()
        val payload = decode(context) ?: return emptyList()
        if (!verify(payload, pin)) return emptyList()
        return entriesFrom(payload)
    }

    fun addEntry(context: Context, pin: String, label: String, value: String): Boolean {
        if (isLocked(context) || label.isBlank() || value.isBlank()) return false
        val payload = decode(context) ?: return false
        if (!verify(payload, pin)) return false

        val current = entriesFrom(payload).toMutableList()
        current.add(VaultEntry(label.trim(), value.trim()))
        val array = JSONArray()
        current.forEach { entry ->
            array.put(JSONObject().apply {
                put("label", entry.label)
                put("value", entry.value)
            })
        }
        payload.put("entries", array)
        save(context, payload)
        return true
    }

    fun getEndpoint(context: Context): String =
        prefs(context).getString(FIELD_ENDPOINT, "").orEmpty()

    fun saveEndpoint(context: Context, endpoint: String) {
        prefs(context).edit()
            .putString(FIELD_ENDPOINT, endpoint.trim())
            .apply()
    }
}
