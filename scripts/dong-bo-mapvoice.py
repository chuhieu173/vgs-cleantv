#!/usr/bin/env python3
"""
Đồng bộ tự động Map Voice từ repo https://github.com/Circling5714/tivikit.git sang vgs-cleantv:
1. Chép nguyên bản 100% module mapvoice/ từ tivikit sang mapvoice/
2. Chép kenh-fpt.json, KenhFpt.kt, MapVoice.kt, MapVoiceTivi.kt, ManMapVoice.kt từ tivikit và ánh xạ sang package zone.vgs.tvsach
3. Gắn tự động (idempotent) các hook vào settings.gradle.kts, KetNoiAdb.kt, ThaoTacTv.kt, DuLieu.kt, KeHoach.kt, KichBanKhoiPhuc.kt, PhienLamViec.kt, UngDung.kt
4. Lưu mã commit của Map Voice trong tivikit vào app/src/main/assets/mapvoice-commit.txt
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TIVIKIT_URL = "https://github.com/Circling5714/tivikit.git"


def ensure_tivikit(path: Path) -> Path:
    if not (path / ".git").exists():
        subprocess.run(["git", "clone", "-q", "--depth", "50", TIVIKIT_URL, str(path)], check=True)
    else:
        subprocess.run(["git", "-C", str(path), "fetch", "-q", "origin", "main"], check=True)
        subprocess.run(["git", "-C", str(path), "reset", "-q", "--hard", "origin/main"], check=True)
    return path


def mapvoice_commit(tk: Path) -> str:
    out = subprocess.check_output(
        [
            "git", "-C", str(tk), "log", "-1", "--format=%H", "--",
            "mapvoice",
            "app/src/main/assets/mapvoice.apk",
            "app/src/main/java/vn/tivikit/dulieu/MapVoice.kt",
            "app/src/main/java/vn/tivikit/ui/MapVoiceTivi.kt",
            "app/src/main/java/vn/tivikit/ui/ManMapVoice.kt",
        ],
        text=True,
    ).strip()
    return out


def sync_module_verbatim(tk: Path):
    dst = ROOT / "mapvoice"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(tk / "mapvoice", dst, ignore=shutil.ignore_patterns("build", ".gradle"))


def transform_kenh_fpt(src_text: str) -> str:
    t = src_text.replace("package vn.tivikit.dulieu", "package zone.vgs.tvsach.dulieu")
    t = t.replace("vn.tivikit.CapNhat.moAsset", "zone.vgs.tvsach.CapNhat.moAsset")
    return t


def transform_mapvoice_kt(src_text: str) -> str:
    t = src_text.replace("package vn.tivikit.dulieu", "package zone.vgs.tvsach.dulieu")
    t = t.replace(
        "val SMARTTUBE = CastSmartTube.SMARTTUBE",
        'val SMARTTUBE = listOf("org.smarttube.stable", "org.smarttube.beta", "com.liskovsoft.smarttubetv", "com.liskovsoft.smarttubetv.beta")',
    )
    t = t.replace(
        "TiviKitLauncher.chiAscii(it)",
        'it.map { c -> if (c.code in 32..126) c.toString() else "\\\\u%04x".format(c.code) }.joinToString("")',
    )
    t = t.replace(
        "fun dsKenh(go: List<KenhVtvGo.Kenh>, tv360: List<KenhNhanh.Kenh>, fpt: List<KenhFpt.Kenh> = emptyList()): String {\n"
        "        val a360 = JSONArray()\n"
        "        tv360.filter { it.laTv360 && it.so.isNotEmpty() }.distinctBy { it.so }\n"
        "            .forEach { a360.put(JSONObject().put(\"ten\", KenhNhanh.tenSach(it.ten)).put(\"so\", it.so)) }\n"
        "        val aGo = JSONArray()\n"
        "        go.distinctBy { it.ma }.forEach { aGo.put(JSONObject().put(\"ten\", KenhNhanh.tenSach(it.tenO)).put(\"ma\", it.ma)) }\n"
        "        val j = JSONObject().put(\"tv360\", a360).put(\"vtvgo\", aGo)\n"
        "        if (fpt.isNotEmpty()) {\n"
        "            val aFpt = JSONArray()\n"
        "            fpt.distinctBy { it.ma }.forEach { aFpt.put(JSONObject().put(\"ten\", KenhNhanh.tenSach(it.ten)).put(\"ma\", it.ma)) }\n"
        "            j.put(\"fptplay\", aFpt)\n"
        "        }\n"
        "        return j.toString()\n"
        "    }",
        "fun dsKenh(go: List<KenhVtvGo.Kenh>, tv360: List<Tv360.K> = Tv360.KENH, fpt: List<KenhFpt.Kenh> = emptyList()): String {\n"
        "        val a360 = JSONArray()\n"
        "        tv360.distinctBy { it.id }\n"
        "            .forEach { a360.put(JSONObject().put(\"ten\", OKenh.tenGon(it.ten)).put(\"so\", it.id.toString())) }\n"
        "        val aGo = JSONArray()\n"
        "        go.distinctBy { it.ma }.forEach { aGo.put(JSONObject().put(\"ten\", OKenh.tenGon(it.ten)).put(\"ma\", it.ma)) }\n"
        "        val j = JSONObject().put(\"tv360\", a360).put(\"vtvgo\", aGo)\n"
        "        if (fpt.isNotEmpty()) {\n"
        "            val aFpt = JSONArray()\n"
        "            fpt.distinctBy { it.ma }.forEach { aFpt.put(JSONObject().put(\"ten\", OKenh.tenGon(it.ten)).put(\"ma\", it.ma)) }\n"
        "            j.put(\"fptplay\", aFpt)\n"
        "        }\n"
        "        return j.toString()\n"
        "    }",
    )
    return t


def transform_mapvoice_tivi_kt(src_text: str) -> str:
    t = src_text.replace("package vn.tivikit.ui", "package zone.vgs.tvsach.ui")
    t = t.replace("import vn.tivikit.dulieu.KenhNhanh\n", "import zone.vgs.tvsach.dulieu.Tv360\n")
    t = t.replace("import vn.tivikit.dulieu.", "import zone.vgs.tvsach.dulieu.")
    t = t.replace("import vn.tivikit.t", "import zone.vgs.tvsach.t")
    t = t.replace("vn.tivikit.CapNhat.moAsset", "zone.vgs.tvsach.CapNhat.moAsset")
    t = t.replace("KenhVtvGo.GOI", "GOI_VTVGO")
    t = t.replace("KenhNhanh.TV360", "Tv360.GOI")
    t = t.replace("KenhNhanh.M3U", '"com.m3u.smartphone"')
    t = t.replace("vn.tivikit.dulieu.Iptv.GOI", '"vn.tivikit.iptv"')
    t = t.replace("vm.damBaoKetNoi()", "vm.io { vm.tv.giuKetNoi() }")
    t = t.replace(
        "val tv360 = KenhNhanh.GOI_Y + vm.kenhNhanh.ds.mapNotNull { it.kenh }\n"
        "        val fpt = if (coFpt) vm.io { KenhFpt.ds(vm.ctx) } else emptyList()\n"
        "        return MapVoice.dsKenh(go, tv360, fpt)",
        "val fpt = if (coFpt) vm.io { KenhFpt.ds(vm.ctx) } else emptyList()\n"
        "        return MapVoice.dsKenh(go, Tv360.KENH, fpt)",
    )
    t = t.replace(
        "fun tenApp(goi: String): String = tenAppMv(goi) ?: vm.henGio.tenApp(goi)",
        "fun tenApp(goi: String): String = tenAppMv(goi) ?: tenDep(goi)",
    )
    t = t.replace("vm.veHub()", "")
    return t


def transform_man_mapvoice_kt(src_text: str) -> str:
    t = src_text.replace("package vn.tivikit.ui", "package zone.vgs.tvsach.ui")
    t = t.replace("import vn.tivikit.dulieu.MapVoice", "import zone.vgs.tvsach.dulieu.MapVoice")
    t = t.replace(
        "import vn.tivikit.t",
        "import androidx.compose.ui.graphics.Color\nimport androidx.compose.ui.text.TextStyle\nimport zone.vgs.tvsach.t\n\n"
        "private val KieuTieuDeLon = TextStyle(fontWeight = FontWeight.Black, fontSize = 22.sp)\n"
        "private val ChuChinh = Color.White\n"
        "private val NenCanhBao = Color(0xFF3A2A10)",
    )
    t = re.sub(
        r'\s*NutPhu\(t\("Mở Cài app", "Open Install apps"\).*?\{ vm\.moCaiApk\(\) \}',
        "",
        t,
    )
    t = t.replace(
        "vn.tivikit.dulieu.HenGio.gioCua(n.luc, java.time.ZoneId.systemDefault()).first",
        'java.time.Instant.ofEpochMilli(n.luc).atZone(java.time.ZoneId.systemDefault()).let { "%02d:%02d".format(it.hour, it.minute) }',
    )
    return t


def patch_file(path: Path, fn):
    orig = path.read_text(encoding="utf-8")
    updated = fn(orig)
    if updated != orig:
        path.write_text(updated, encoding="utf-8")


def hook_settings_gradle():
    def _fn(s: str) -> str:
        if 'include(":mapvoice")' not in s:
            s = s.rstrip() + '\ninclude(":mapvoice")\n'
        return s
    patch_file(ROOT / "settings.gradle.kts", _fn)


def hook_ket_noi_adb():
    def _fn(s: str) -> str:
        if "setApi(34)" in s:
            return s
        s = s.replace(
            "    init {\n        setTimeout(20, TimeUnit.SECONDS)\n    }",
            """    init {
        setTimeout(20, TimeUnit.SECONDS)
        setApi(34)
    }

    override fun openStream(destination: String): io.github.muntashirakon.adb.AdbStream {
        val f = MO_LUONG.submit(java.util.concurrent.Callable { super.openStream(destination) })
        return try {
            f.get(MO_TOI_DA_GIAY, TimeUnit.SECONDS)
        } catch (e: java.util.concurrent.TimeoutException) {
            f.cancel(true)
            throw java.io.IOException("Tivi không trả lời sau $MO_TOI_DA_GIAY giây (mở lệnh)")
        } catch (e: InterruptedException) {
            f.cancel(true); throw e
        } catch (e: java.util.concurrent.ExecutionException) {
            throw e.cause ?: e
        }
    }""",
        )
        s = s.replace(
            "    companion object {\n        @Volatile private var hienTai: KetNoiAdb? = null",
            """    companion object {
        private val MO_LUONG = java.util.concurrent.Executors.newCachedThreadPool { r ->
            Thread(r, "adb-mo").apply { isDaemon = true }
        }
        private const val MO_TOI_DA_GIAY = 20L

        @Volatile private var hienTai: KetNoiAdb? = null""",
        )
        return s
    patch_file(ROOT / "app/src/main/java/zone/vgs/tvsach/adb/KetNoiAdb.kt", _fn)


def hook_du_lieu_and_ke_hoach():
    def _dl(s: str) -> str:
        if '"vn.tivikit.mapvoice"' not in s:
            s = s.replace(
                '"com.ts.launcher" to "Home sạch (bản cho Xiaomi)",',
                '"com.ts.launcher" to "Home sạch (bản cho Xiaomi)",\n'
                '    "org.smarttube.stable" to "SmartTube",\n'
                '    "org.smarttube.beta" to "SmartTube Beta",\n'
                '    "com.liskovsoft.smarttubetv" to "SmartTube",\n'
                '    "com.liskovsoft.smarttubetv.beta" to "SmartTube Beta",\n'
                '    "io.gh.reisxd.tizentube.cobalt" to "TizenTube",\n'
                '    "vn.tivikit.mapvoice" to "Map Voice",\n'
                '    "zone.vgs.cleantv.keepalive" to "Sony KeepAlive",',
            )
        return s
    patch_file(ROOT / "app/src/main/java/zone/vgs/tvsach/dulieu/DuLieu.kt", _dl)

    def _kh(s: str) -> str:
        if '"vn.tivikit.mapvoice"' not in s:
            s = s.replace(
                '"com.gathin.tvhome", "com.ts.launcher",',
                '"com.gathin.tvhome", "com.ts.launcher", "vn.tivikit.mapvoice", "zone.vgs.cleantv.keepalive",',
            )
        return s
    patch_file(ROOT / "app/src/main/java/zone/vgs/tvsach/dulieu/KeHoach.kt", _kh)

    def _kb(s: str) -> str:
        if "MapVoice.GOI" not in s:
            s = s.replace(
                'dong += "adb uninstall $PKG_KHOA"',
                'dong += "adb uninstall $PKG_KHOA"\n        dong += "adb uninstall ${MapVoice.GOI}"',
            )
        return s
    patch_file(ROOT / "app/src/main/java/zone/vgs/tvsach/dulieu/KichBanKhoiPhuc.kt", _kb)


def hook_thao_tac_tv():
    def _fn(s: str) -> str:
        if "fun mapVoiceDaCai()" in s:
            return s
        s = s.replace(
            'if (khoaDaCai()) { bao(t("Gỡ Khoá trẻ em…", "Removing the Kids lock…")); runCatching { tatKhoa(go = true) } }',
            'if (khoaDaCai()) { bao(t("Gỡ Khoá trẻ em…", "Removing the Kids lock…")); runCatching { tatKhoa(go = true) } }\n'
            '        if (mapVoiceDaCai()) { bao(t("Gỡ Map Voice…", "Removing Map Voice…")); runCatching { goMapVoice() } }',
        )
        methods = """
    // ---------- Map Voice (đồng bộ từ Circling5714/tivikit) ----------

    fun mapVoiceDaCai(): Boolean = sh("pm path ${zone.vgs.tvsach.dulieu.MapVoice.GOI} 2>/dev/null").contains("package:")

    fun docMapVoice(): org.json.JSONObject? {
        if (!mapVoiceDaCai()) return null
        val out = sh("content call --uri content://${zone.vgs.tvsach.dulieu.MapVoice.GOI} --method doc 2>/dev/null")
        val a = out.indexOf("json="); val b = out.lastIndexOf("}]")
        return if (a < 0 || b <= a) null else runCatching { org.json.JSONObject(out.substring(a + 5, b)) }.getOrNull()
    }

    fun goiDangBat(): Set<String> = sh("pm list packages -e").lines().mapNotNull { l ->
        l.trim().removePrefix("package:").takeIf { TEN_GOI.matches(it) }
    }.toSet()

    fun goiDangTat(pkg: String): Boolean = sh("pm list packages -d").lines().any { it.trim() == "package:$pkg" }

    fun caiMapVoice(apk: ByteArray, cauHinh: zone.vgs.tvsach.dulieu.MapVoice.CauHinh, kenh: String, bao: (String) -> Unit) {
        bao(t("Cài app Map Voice lên tivi…", "Installing Map Voice on the TV…"))
        adb.ghiFile("/data/local/tmp/mapvoice.apk", apk)
        val out = sh("pm install -r /data/local/tmp/mapvoice.apk; rm -f /data/local/tmp/mapvoice.apk")
        if (!out.contains("Success")) error(t("Cài không được: ${out.trim().lines().lastOrNull()}", "Install failed: ${out.trim().lines().lastOrNull()}"))
        sh("cmd appops set ${zone.vgs.tvsach.dulieu.MapVoice.GOI} AUTO_START allow 2>/dev/null; cmd appops set ${zone.vgs.tvsach.dulieu.MapVoice.GOI} TURN_SCREEN_ON allow 2>/dev/null; true")
        bao(t("Gửi cài đặt…", "Sending the settings…"))
        if (!datMapVoice(cauHinh)) error(t("Tivi không nhận cài đặt của Map Voice.", "The TV rejected the Map Voice settings."))
        if (kenh.isNotEmpty()) guiKenhMapVoice(kenh)
        bao(t("Bật dịch vụ Map Voice…", "Turning the Map Voice service on…"))
        val dv = zone.vgs.tvsach.dulieu.MapVoice.DICH_VU
        sh("s=\\$(settings get secure enabled_accessibility_services); case \\"\\$s\\" in *$dv*) ;; null|'') settings put secure enabled_accessibility_services $dv ;; *) settings put secure enabled_accessibility_services \\"\\$s:$dv\\" ;; esac; settings put secure accessibility_enabled 1")
    }

    fun datMapVoice(c: zone.vgs.tvsach.dulieu.MapVoice.CauHinh): Boolean = sh(zone.vgs.tvsach.dulieu.MapVoice.lenhDat(c)).contains("ok=1")

    fun guiKenhMapVoice(json: String): Boolean = sh(zone.vgs.tvsach.dulieu.MapVoice.lenhKenh(json)).contains("ok=1")

    fun xemMapVoice(cau: String): Pair<zone.vgs.tvsach.dulieu.MapVoice.Viec?, String> =
        sh(zone.vgs.tvsach.dulieu.MapVoice.lenhXem(cau)).let { zone.vgs.tvsach.dulieu.MapVoice.viecTrong(it) to zone.vgs.tvsach.dulieu.MapVoice.loiTrong(it) }

    fun thuMapVoice(cau: String): Pair<zone.vgs.tvsach.dulieu.MapVoice.Viec?, String> =
        sh(zone.vgs.tvsach.dulieu.MapVoice.lenhThu(cau)).let { zone.vgs.tvsach.dulieu.MapVoice.viecTrong(it) to zone.vgs.tvsach.dulieu.MapVoice.loiTrong(it) }

    fun noiLaiMapVoice(): Boolean = sh(zone.vgs.tvsach.dulieu.MapVoice.LENH_NOI_LAI).contains("ok=1")

    fun goMapVoice() {
        if (!mapVoiceDaCai()) return
        val dv = zone.vgs.tvsach.dulieu.MapVoice.DICH_VU
        val tc = sh("settings get secure enabled_accessibility_services").trim()
        if (tc.contains(dv)) {
            val con = tc.split(':').filter { it.isNotBlank() && it != dv && it != "null" }.joinToString(":")
            if (con.isBlank()) sh("settings delete secure enabled_accessibility_services") else sh("settings put secure enabled_accessibility_services '$con'")
        }
        sh("pm uninstall ${zone.vgs.tvsach.dulieu.MapVoice.GOI}")
    }
"""
        s = s.replace("    // ---------- Đóng ADB ----------", methods + "\n    // ---------- Đóng ADB ----------")
        return s
    patch_file(ROOT / "app/src/main/java/zone/vgs/tvsach/adb/ThaoTacTv.kt", _fn)


def hook_phien_lam_viec():
    def _fn(s: str) -> str:
        if "MAP_VOICE" in s:
            return s
        s = s.replace(
            "enum class Man { CHINH, KET_NOI, THONG_TIN, CHON_GOI, DANG_TAT, HOME_SACH, XONG, KHOI_PHUC, HUONG_DAN, GIAY_PHEP, KHOA_TRE, REMOTE }",
            "enum class Man { CHINH, KET_NOI, THONG_TIN, CHON_GOI, DANG_TAT, HOME_SACH, XONG, KHOI_PHUC, HUONG_DAN, GIAY_PHEP, KHOA_TRE, REMOTE, MAP_VOICE }",
        )
        s = s.replace("    private val ctx: Context get() = getApplication()", "    internal val ctx: Context get() = getApplication()")
        s = s.replace("    private val tv by lazy { ThaoTacTv(adb, kho) }", "    internal val tv by lazy { ThaoTacTv(adb, kho) }")
        s = s.replace(
            '    private val prefs by lazy { ctx.getSharedPreferences("tvsach", Context.MODE_PRIVATE) }',
            '    private val prefs by lazy { ctx.getSharedPreferences("tvsach", Context.MODE_PRIVATE) }\n'
            '    val mapVoice by lazy { MapVoiceTivi(this) }\n'
            '    fun moMapVoice() = mapVoice.mo()',
        )
        s = s.replace("    private var getprop = \"\"", "    internal var getprop = \"\"")
        s = s.replace("    private fun chay(viec: String, khoi: suspend () -> Unit) {", "    internal fun chay(viec: String, khoi: suspend () -> Unit) {")
        s = s.replace("    private suspend fun <T> io(khoi: () -> T): T = withContext(Dispatchers.IO) { khoi() }", "    internal suspend fun <T> io(khoi: () -> T): T = withContext(Dispatchers.IO) { khoi() }")
        s = s.replace(
            "        dsTatTv = null; chonBatLai.clear(); batLaiBao = \"\"",
            "        dsTatTv = null; chonBatLai.clear(); batLaiBao = \"\"\n        mapVoice.quen()",
        )
        return s
    patch_file(ROOT / "app/src/main/java/zone/vgs/tvsach/ui/PhienLamViec.kt", _fn)


def hook_ung_dung():
    def _fn(s: str) -> str:
        if "Man.MAP_VOICE" in s:
            return s
        for v in ["Xanh", "Cam", "The1", "The2", "ChuPhu"]:
            s = s.replace(f"private val {v} =", f"internal val {v} =")
        for f in ["Cuon(", "The(", "NutChinh(", "NutPhu(", "Phu(", "Gap(", "LuaChon(", "ChonChip(", "Hang("]:
            s = s.replace(f"private fun {f}", f"internal fun {f}")
        s = s.replace(
            "                        Man.REMOTE -> ManRemote(vm)",
            "                        Man.REMOTE -> ManRemote(vm)\n                        Man.MAP_VOICE -> ManMapVoice(vm)",
        )
        s = s.replace(
            "        Man.KHOA_TRE, Man.REMOTE -> Man.THONG_TIN",
            "        Man.KHOA_TRE, Man.REMOTE, Man.MAP_VOICE -> Man.THONG_TIN",
        )
        s = s.replace(
            '    else NutPhu(t("Remote trên điện thoại", "Phone remote"), Icons.Rounded.SettingsRemote) { vm.moRemote() }',
            '    else NutPhu(t("Remote trên điện thoại", "Phone remote"), Icons.Rounded.SettingsRemote) { vm.moRemote() }\n'
            '    NutPhu(t("Map Voice (giọng nói mở SmartTube / TizenTube)", "Map Voice (voice opens SmartTube / TizenTube)"), Icons.Rounded.Mic) { vm.moMapVoice() }',
        )
        s = s.replace(
            '            if (!zone.vgs.tvsach.ManHinh.laTv) NutPhu(t("Giữ ADB và dùng remote trên điện thoại", "Keep ADB and use the phone remote"), Icons.Rounded.SettingsRemote) { vm.chonGiuAdb { vm.moRemote() } }',
            '            if (!zone.vgs.tvsach.ManHinh.laTv) NutPhu(t("Giữ ADB và dùng remote trên điện thoại", "Keep ADB and use the phone remote"), Icons.Rounded.SettingsRemote) { vm.chonGiuAdb { vm.moRemote() } }\n'
            '            NutPhu(t("Giữ ADB và bật Map Voice (SmartTube / TizenTube)", "Keep ADB and turn on Map Voice"), Icons.Rounded.Mic) { vm.chonGiuAdb { vm.moMapVoice() } }',
        )
        return s
    patch_file(ROOT / "app/src/main/java/zone/vgs/tvsach/ui/UngDung.kt", _fn)


def hook_cap_nhat():
    def _fn(s: str) -> str:
        s = s.replace(
            '    const val GOC = "https://cleantv.alexvgs.tech"',
            '    const val KHO = "chuhieu173/vgs-cleantv"\n    const val GOC = "https://github.com/$KHO/releases/latest/download"',
        )
        s = s.replace(
            'val bytes = tai(GOC + o.getString("url"), 60)',
            'val u = o.getString("url").let { if (it.startsWith("http")) it else "$GOC/${it.removePrefix("/").removePrefix("ota/")}" }\n                    val bytes = tai(u, 60)',
        )
        s = s.replace(
            'app.getString("apk").let { if (it.startsWith("http")) it else GOC + it }',
            'app.getString("apk").let { if (it.startsWith("http")) it else "$GOC/${it.removePrefix("/")}" }',
        )
        return s
    patch_file(ROOT / "app/src/main/java/zone/vgs/tvsach/CapNhat.kt", _fn)


def main():
    tk_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else (ROOT / "tivikit")
    ensure_tivikit(tk_dir)
    commit = mapvoice_commit(tk_dir)

    sync_module_verbatim(tk_dir)

    # Copy mapvoice.apk nguyên bản từ tivikit (giữ nguyên chữ ký gốc để cài đè -r trên TV không mất quyền ADB)
    mv_apk = tk_dir / "app/src/main/assets/mapvoice.apk"
    if mv_apk.is_file():
        shutil.copyfile(mv_apk, ROOT / "app/src/main/assets/mapvoice.apk")

    # Copy kenh-fpt.json & KenhFpt.kt
    shutil.copyfile(
        tk_dir / "app/src/main/assets/kenh-fpt.json",
        ROOT / "app/src/main/assets/kenh-fpt.json",
    )
    (ROOT / "app/src/main/java/zone/vgs/tvsach/dulieu/KenhFpt.kt").write_text(
        transform_kenh_fpt((tk_dir / "app/src/main/java/vn/tivikit/dulieu/KenhFpt.kt").read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    (ROOT / "app/src/main/java/zone/vgs/tvsach/dulieu/MapVoice.kt").write_text(
        transform_mapvoice_kt((tk_dir / "app/src/main/java/vn/tivikit/dulieu/MapVoice.kt").read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    (ROOT / "app/src/main/java/zone/vgs/tvsach/ui/MapVoiceTivi.kt").write_text(
        transform_mapvoice_tivi_kt((tk_dir / "app/src/main/java/vn/tivikit/ui/MapVoiceTivi.kt").read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    (ROOT / "app/src/main/java/zone/vgs/tvsach/ui/ManMapVoice.kt").write_text(
        transform_man_mapvoice_kt((tk_dir / "app/src/main/java/vn/tivikit/ui/ManMapVoice.kt").read_text(encoding="utf-8")),
        encoding="utf-8",
    )

    hook_settings_gradle()
    hook_ket_noi_adb()
    hook_du_lieu_and_ke_hoach()
    hook_thao_tac_tv()
    hook_phien_lam_viec()
    hook_ung_dung()
    hook_cap_nhat()

    (ROOT / "app/src/main/assets/mapvoice-commit.txt").write_text(commit + "\n", encoding="utf-8")
    print(f"Đã đồng bộ Map Voice từ tivikit commit {commit[:7]}")


if __name__ == "__main__":
    main()
