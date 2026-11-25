package com.ghost.keystore

import android.content.Context
import org.json.JSONObject
import java.io.BufferedInputStream
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest

data class UpdateInfo(val version: String, val apkUrl: String, val checksumUrl: String)

object UpdateChecker {
    private const val RELEASES_URL =
        "https://api.github.com/repos/ghostmalaysia/GHOST/releases/latest"
    private const val USER_AGENT = "GHOST-Security-Center/0.2.0"

    fun latest(): UpdateInfo? {
        val text = fetchText(RELEASES_URL) ?: return null
        val release = try {
            JSONObject(text)
        } catch (_: Exception) {
            return null
        }

        val version = release.optString("tag_name", "").removePrefix("v").trim()
        if (version.isBlank()) return null

        var apkUrl = ""
        var checksumUrl = ""
        val assets = release.optJSONArray("assets")
        if (assets != null) {
            for (index in 0 until assets.length()) {
                val asset = assets.optJSONObject(index) ?: continue
                val name = asset.optString("name", "")
                val url = asset.optString("browser_download_url", "")
                if (name.endsWith(".apk") && url.startsWith("https://")) apkUrl = url
                if (name.endsWith("-sha256.txt") && url.startsWith("https://")) checksumUrl = url
            }
        }

        if (apkUrl.isBlank() || checksumUrl.isBlank()) return null
        return UpdateInfo(version, apkUrl, checksumUrl)
    }

    fun isNewer(candidate: String, current: String): Boolean {
        val left = candidate.split(".").map { it.toIntOrNull() ?: 0 }
        val right = current.split(".").map { it.toIntOrNull() ?: 0 }
        for (index in 0 until maxOf(left.size, right.size)) {
            val first = left.getOrElse(index) { 0 }
            val second = right.getOrElse(index) { 0 }
            if (first != second) return first > second
        }
        return false
    }

    fun downloadAndVerify(context: Context, info: UpdateInfo): File? {
        val checksumText = fetchText(info.checksumUrl) ?: return null
        val expected = checksumText.lineSequence()
            .map { it.trim().split(Regex("\\s+")).firstOrNull().orEmpty() }
            .firstOrNull { it.length == 64 && it.all { c -> c in '0'..'9' || c in 'a'..'f' || c in 'A'..'F' } }
            ?: return null

        val target = File(context.cacheDir, "ghost-update.apk")
        val connection = URL(info.apkUrl).openConnection() as HttpURLConnection
        connection.requestMethod = "GET"
        connection.setRequestProperty("User-Agent", USER_AGENT)
        connection.connectTimeout = 15_000
        connection.readTimeout = 30_000
        connection.instanceFollowRedirects = true

        return try {
            if (connection.responseCode !in 200..299) return null
            val digest = MessageDigest.getInstance("SHA-256")
            BufferedInputStream(connection.inputStream).use { input ->
                FileOutputStream(target).use { output ->
                    val buffer = ByteArray(16 * 1024)
                    while (true) {
                        val read = input.read(buffer)
                        if (read < 0) break
                        output.write(buffer, 0, read)
                        digest.update(buffer, 0, read)
                    }
                }
            }
            val actual = digest.digest().joinToString("") { "%02x".format(it) }
            if (!actual.equals(expected, ignoreCase = true)) {
                target.delete()
                return null
            }
            target
        } catch (_: Exception) {
            target.delete()
            null
        } finally {
            connection.disconnect()
        }
    }

    private fun fetchText(urlText: String): String? {
        val connection = URL(urlText).openConnection() as HttpURLConnection
        connection.requestMethod = "GET"
        connection.setRequestProperty("User-Agent", USER_AGENT)
        connection.setRequestProperty("Accept", "application/vnd.github+json")
        connection.connectTimeout = 15_000
        connection.readTimeout = 20_000
        return try {
            if (connection.responseCode !in 200..299) null
            else connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
        } catch (_: Exception) {
            null
        } finally {
            connection.disconnect()
        }
    }
}
