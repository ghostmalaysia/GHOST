# GHOST

GHOST ialah pembantu AI Python berasaskan terminal. Prototaip ini menyokong
sembang, memori tempatan, perancangan dan aliran kerjasama berbilang AI.

## Mula dalam Horus

1. Buka **Bare Terminal** dan masuk ke folder projek:

   ```sh
   cd /workspace/projects/GHOST
   ```

2. Sediakan konfigurasi AI (Qwen setempat digunakan secara lalai):

   ```sh
   mkdir -p config
   cp config/ai_providers.example.json config/ai_providers.json
   ```

3. Jalankan GHOST:

   ```sh
   python3 core/ghost.py
   ```

   Python 3 perlu tersedia dalam sesi Horus. `/providers` menyenaraikan
   konfigurasi, tetapi hanya panggilan sebenar menguji endpoint serta
   kelayakan penyedia API.

Untuk Qwen lalai, sediakan model GGUF dan server llama.cpp yang boleh dicapai
pada URL konfigurasi. Repo tidak membekalkan model atau akaun AI. AI awan
memerlukan akaun/API key penyedia sendiri.

## Arahan GHOST

- `/help` — paparkan arahan dalam terminal.
- `/providers` — senaraikan penyedia AI yang dikonfigurasi dan tersedia.
- `/model qwen` — pilih penyedia untuk sembang semasa.
- `/collab qwen,claude: Terangkan rancangan ini` — draf, semakan silang dan rumusan.
- `/plan OBJEKTIF` — bina pelan dan semak risiko; pelan tidak melaksanakan tindakan.
- `/remember`, `/memory`, `/search`, `/forget ID` — fungsi memori. `/remember`
  menyimpan secara setempat dahulu dan hanya menghantar salinan ke Supabase
  selepas persetujuan khusus; `/forget ID` memadam rekod tempatan sahaja.
- `/clear`, `/exit` — reset perbualan atau keluar.

Untuk penyedia API, `/providers` mengesahkan konfigurasi sahaja; endpoint
sebenar hanya diuji apabila model dipanggil.

Aliran `/collab` membuat satu panggilan draf, satu panggilan semakan bagi setiap
penyedia tambahan, kemudian satu panggilan rumusan. Jika hanya dua penyedia
dipilih, penyedia pertama juga menghasilkan rumusan akhir.
Teks tugasan, memori berkaitan yang melepasi penapis corak, draf dan semakan
dihantar kepada penyedia yang dipilih. Jangan gunakan penyedia awan jika anda
tidak mahu menghantar konteks itu kepada perkhidmatan tersebut.

## Penyedia AI

Konfigurasi sebenar berada dalam `config/ai_providers.json` (fail ini diabaikan
oleh Git). Salin contoh dan laraskan model, URL atau nama arahan mengikut
perkhidmatan yang anda gunakan. Jenis yang disokong:

- `openai_compatible`: servis seperti Qwen setempat atau endpoint API lain.
- `anthropic`: API Anthropic; simpan kunci dalam `config/ai_secrets.env`.
- `claude_cli` dan `opencode_cli`: arahan CLI hanya berfungsi jika binary itu
  tersedia dalam `PATH` proses GHOST. Dalam Horus, setiap ejen mempunyai sesi
  dan akaun Linux yang berasingan; arahan dalam sesi Claude/OpenCode mungkin
  tidak boleh dipanggil dari Bare Terminal. Gunakan API yang boleh dicapai GHOST
  jika arahan itu tidak tersenarai oleh `/providers`. OpenCode menggunakan ejen
  projek `ghost-collab` yang menolak semua alat (fail, shell dan rangkaian);
  ia memerlukan versi OpenCode yang menyokong agent Markdown dan permission V2.
  Claude CLI menggunakan argumen dalam fail konfigurasi; semak konfigurasi
  sebelum menggunakannya. CLI tidak menerima pemboleh ubah persekitaran rahsia
  secara lalai; tetapkan `pass_env` untuk membenarkan nama pemboleh ubah tertentu
  jika CLI anda memang memerlukannya. Ciri kolaborasi menghantar teks tugasan
  dan draf kepada penyedia yang dipilih.

Contoh `free_api` dalam fail konfigurasi ialah templat sahaja. Gantikan URL,
ID model dan nama pemboleh ubah kunci dengan nilai daripada penyedia yang anda
pilih. GHOST tidak membundel model atau akaun percuma; had dan bayaran ditetapkan
oleh penyedia.

Untuk rahsia API, salin `config/ai_secrets.env.example` ke
`config/ai_secrets.env`, isi kunci pada telefon, dan hadkan akses fail:

```sh
cp config/ai_secrets.env.example config/ai_secrets.env
chmod 600 config/ai_secrets.env
```

GHOST membaca fail rahsia itu secara setempat. Jangan tampal kunci API atau kata
laluan ke dalam perbualan. Model API mungkin mengenakan caj atau had penggunaan;
label “percuma” bergantung pada penyedia.

Memori SQLite tempatan tidak disulitkan. Penapis memori hanya menggugurkan
rekod yang sepadan dengan corak rahsia yang diketahui dan bukan jaminan
pengesanan menyeluruh. Jangan simpan kata laluan, token atau kunci peribadi
dalam memori GHOST.

## Supabase Cloud Memory

Cloud Memory pilihan. Tanpa konfigurasi Supabase, GHOST masih boleh berjalan
dengan memori SQLite tempatan. Apabila fail konfigurasi cloud tiada, GHOST
memaklumkan bahawa cloud tidak tersedia dan meneruskan dengan memori tempatan.
Untuk mengaktifkan Cloud Memory, salin
`config/supabase.env.example` ke `config/supabase.env`, masukkan URL dan
publishable/anon key projek Supabase, dan sediakan jadual `ghost_memories` serta
polisi akses yang mengehadkan rekod kepada pemilik. GHOST akan meminta e-mel dan
kata laluan Supabase secara interaktif; kata laluan tidak disimpan dalam kod.
Untuk automasi, tetapkan `SUPABASE_EMAIL` dan `SUPABASE_PASSWORD` dalam
persekitaran setempat sebelum menjalankan GHOST — jangan letak nilai itu dalam
repo.
Untuk membuat jadual dan polisi asas, jalankan `config/supabase_schema.sql`
sekali dalam SQL Editor projek Supabase anda.

### Mod memori

Salin `config/memory.example.json` ke `config/memory.json` dan pilih salah satu:

- `local` (lalai): SQLite pada peranti; salinan cloud hanya selepas persetujuan.
- `cloud`: Supabase dicuba dahulu. Jika gagal, GHOST menyimpan salinan
  setempat sebagai sandaran. Tiada pertindikan apabila cloud berjaya.
- `cloud_only`: SQLite tidak ditulis langsung — sesuai jika storan telefon
  terhad. Jika Supabase tidak tersedia, tiada memori disimpan.

`/forget ID` memadam rekod tempatan sahaja. `/forgetcloud UUID` memadam rekod
Supabase milik pemilik. Kandungan memori masih tertakluk kepada penapis
kredensial sebelum dihantar kepada mana-mana penyedia AI.

## Carian internet pilihan

Modul Tavily memerlukan akaun/API key Tavily dan akses rangkaian. Salin
`config/tavily.env.example` ke `config/tavily.env`, gantikan nilai contoh,
dan simpan fail itu secara peribadi. Carian internet/Web Reader tidak bermula
secara automatik ketika sembang; ia tersedia melalui modul `core/learning`.

### Belajar internet percuma

`/learn topik` menggunakan API awam Wikipedia (tanpa API key) melalui
`core/learning/free_web.py` dan `core/learning/learn_loop.py`. GHOST mencari
beberapa halaman, meringkaskan fakta melalui penyedia AI semasa, memaparkan
sumber URL, dan hanya menyimpan selepas pemilik meluluskan. Kandungan web
sentiasa dianggap data tidak dipercayai, bukan arahan, dan tidak disalin ke
cloud secara automatik.

## Konfigurasi Horus

Laluan konfigurasi dan memori biasanya berpunca daripada folder projek.
Pengecualian: jika folder legasi `~/GHOST` wujud dan berasingan daripada
checkout, GHOST menggunakannya untuk konfigurasi dan data lama. Tetapkan
`GHOST_HOME` untuk memilih folder data secara jelas; fail identiti serta kod
kekal di checkout projek.
Qwen lalai memerlukan endpoint OpenAI-compatible di
`http://127.0.0.1:8080/v1`; ubah `base_url` dan `model` dalam konfigurasi jika
servis anda menggunakan alamat atau nama lain.

### Menjalankan Qwen setempat di Termux

GHOST tidak memulakan model secara automatik. Pastikan `llama-server` daripada
llama.cpp sudah dibina atau dipasang, kemudian cari nama fail model:

```sh
find ~/GHOST/models/qwen -maxdepth 1 -type f -name '*.gguf' -print
```

Jalankan server menggunakan laluan executable dan model sebenar pada telefon:

```sh
llama-server -m /laluan/sebenar/qwen.gguf --alias qwen --host 127.0.0.1 --port 8080
```

Biarkan terminal server itu berjalan dan buka GHOST dalam persekitaran Termux
yang sama. LLaMA.cpp mendokumenkan `llama-server` sebagai server API
OpenAI-compatible; GHOST menggunakan `/v1/chat/completions` pada port 8080.
Horus dan Termux mempunyai persekitaran berasingan, jadi server yang berjalan
dalam Termux tidak automatik tersedia pada `127.0.0.1` dalam Horus. Salin repo
dan model ke persekitaran yang sama dengan GHOST, atau konfigurasi `base_url`
ke endpoint rangkaian yang memang boleh dicapai dari sesi GHOST.

### Menggunakan checkout GitHub dalam Termux

Dalam Termux, clone repo yang anda boleh akses dan jalankan GHOST daripada
folder checkout itu. Repo private memerlukan log masuk GitHub melalui Git;
gunakan aliran pengesahan rasmi GitHub dan jangan masukkan token ke URL atau
kongsi token dalam chat. Qwen dan server llama.cpp perlu disediakan berasingan.

## Android Security Center

Modul `android-companion` kini berada dalam repo. Versi 0.2.0 menyediakan Vault
tempatan dengan PIN 8 digit yang disahkan melalui Android Keystore
(AES-GCM). Rekod disulitkan pada peranti dan tidak dihantar kepada GHOST AI atau
perkhidmatan awan. Skrin Audit hanya merekodkan peristiwa antara muka setempat,
bukan audit log yang kalis gangguan. Skrin Devices memaparkan maklumat peranti
secara baca sahaja. Skrin GHOST AI Link hanya menyimpan alamat endpoint; tiada
ujian sambungan atau permintaan AI dibuat oleh APK ini. App PIN, pendaftaran
peranti jauh dan Owner Recovery kekal sebagai paparan reka bentuk kerana
memerlukan reka bentuk kebenaran pemilik dan backend yang belum tersedia.

Vault ini bukan pengurus kata laluan bertauliah dan belum diaudit secara
bebas. PIN tidak boleh dipulihkan tanpa memadam data aplikasi. Jangan simpan
rahsia bernilai tinggi di sini.

Skrin dashboard menyemak GitHub Releases secara automatik semasa aplikasi dibuka
dan mempunyai butang **CHECK FOR UPDATE** untuk semakan manual. Ia menyemak
Releases terkini untuk repositori `ghostmalaysia/GHOST`, membandingkan versi,
memuat turun APK dan fail `ghost-apk-sha256.txt`, serta mengesahkan SHA-256
sebelum membuka pemasang sistem. Android masih meminta pengesahan pemasangan;
kemas kini senyap tidak disokong untuk APK yang dipasang terus. Jika checksum
tidak sepadan, muat turun dibuang dan tiada pemasangan dibuka.

Workflow GitHub membina APK debug pada push ke `android-companion/**`. Aliran
release hanya berjalan secara manual dari branch
`feature/ghost-security-center` dan memerlukan keystore asal supaya tandatangan
APK sepadan dengan versi yang telah dipasang. Jangan hantar keystore, kata
laluan atau secrets ke dalam chat atau repo.

Langkah untuk APK release yang mengekalkan tandatangan lama:

1. Tukar keystore asal kepada Base64 pada komputer pemilik (bukan dalam chat),
   kemudian simpan sebagai GitHub Actions secret `GHOST_KEYSTORE_BASE64`.
2. Simpan juga `GHOST_KEYSTORE_PASSWORD`, `GHOST_KEY_ALIAS` dan
   `GHOST_KEY_PASSWORD` sebagai secrets repository.
3. Pastikan branch `feature/ghost-security-center` mengandungi kemas kini ini,
   kemudian jalankan workflow **GHOST Android Build** secara manual dari branch
   tersebut. Workflow itu juga menerbitkan APK dan checksum ke GitHub Release
    `v0.2.1` supaya butang **CHECK FOR UPDATE** dalam aplikasi dapat mengesannya.
4. Pasang APK release yang dihasilkan. Jika tandatangan berbeza daripada APK
   lama, Android akan menolak kemas kini — padam aplikasi lama dahulu. Untuk
   versi seterusnya, naikkan `versionCode`, `versionName`, tag release dalam
   workflow dan versi rujukan dalam `UpdateChecker`/`MainActivity` serentak.

Builds memerlukan rangkaian untuk memuat turun dependencies Android. Tiada
signing key disimpan dalam repo.

## Keperluan pilihan daripada pemilik

- **AI setempat:** model GGUF, llama.cpp server, Python 3 dan ruang storan.
- **AI awan:** akaun penyedia serta API key; caj dan had ikut penyedia.
- **Cloud Memory:** projek Supabase, URL, publishable/anon key, log masuk kata
  laluan diaktifkan, serta jadual dan polisi SQL di atas.
- **Carian web:** akaun/API key Tavily.
- **APK release bertandatangan:** keystore pemilik dan GitHub Actions secrets
  `GHOST_KEYSTORE_BASE64`, `GHOST_KEYSTORE_PASSWORD`, `GHOST_KEY_ALIAS` dan
  `GHOST_KEY_PASSWORD`. Jangan hantar rahsia ini dalam chat.
