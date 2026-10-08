from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "perpustakadb.db"
)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()

    # Tabel perangkat
    conn.execute("""
        CREATE TABLE IF NOT EXISTS perangkat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode TEXT UNIQUE NOT NULL,
            jenis TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Tersedia',
            kondisi TEXT NOT NULL DEFAULT 'Baik',
            aktif INTEGER NOT NULL DEFAULT 1
        )
    """)

    # Tabel penggunaan
    conn.execute("""
        CREATE TABLE IF NOT EXISTS penggunaan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            nim TEXT NOT NULL,
            jurusan TEXT NOT NULL,
            angkatan TEXT NOT NULL,
            perangkat_id INTEGER NOT NULL,
            tanggal_pemakaian TEXT NOT NULL,
            waktu_mulai TEXT NOT NULL,
            waktu_akhir TEXT,
            tujuan TEXT NOT NULL,
            kondisi_awal TEXT NOT NULL,
            kondisi_akhir TEXT,
            status TEXT NOT NULL DEFAULT 'Sedang Digunakan',
            FOREIGN KEY (perangkat_id)
                REFERENCES perangkat(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================
# DASHBOARD
# =========================

@app.route("/")
def dashboard():

    conn = get_db()

    perangkat = conn.execute("""
        SELECT *
        FROM perangkat
        WHERE aktif = 1
        ORDER BY id
    """).fetchall()

    penggunaan = conn.execute("""
        SELECT
            penggunaan.*,
            perangkat.kode,
            perangkat.jenis
        FROM penggunaan
        JOIN perangkat
            ON penggunaan.perangkat_id = perangkat.id
        WHERE penggunaan.status = 'Sedang Digunakan'
        ORDER BY penggunaan.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        perangkat=perangkat,
        penggunaan=penggunaan
    )


# =========================
# KELOLA PERANGKAT
# =========================

@app.route("/perangkat")
def perangkat():

    conn = get_db()

    data = conn.execute("""
        SELECT *
        FROM perangkat
        ORDER BY id
    """).fetchall()

    conn.close()

    return render_template(
        "perangkat.html",
        data=data
    )


@app.route("/perangkat/tambah", methods=["GET", "POST"])
def tambah_perangkat():

    if request.method == "POST":

        kode = request.form["kode"].strip().upper()
        jenis = request.form["jenis"]
        kondisi = request.form["kondisi"]

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO perangkat
                (
                    kode,
                    jenis,
                    status,
                    kondisi,
                    aktif
                )
                VALUES (?, ?, 'Tersedia', ?, 1)
            """, (
                kode,
                jenis,
                kondisi
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return """
            <script>
                alert("Kode perangkat sudah digunakan!");
                history.back();
            </script>
            """

        conn.close()

        return redirect(url_for("perangkat"))

    return render_template(
        "tambah_perangkat.html",
        edit=False
    )


@app.route("/perangkat/edit/<int:id>", methods=["GET", "POST"])
def edit_perangkat(id):

    conn = get_db()

    data = conn.execute("""
        SELECT *
        FROM perangkat
        WHERE id = ?
    """, (id,)).fetchone()

    if not data:

        conn.close()

        return "Perangkat tidak ditemukan", 404

    if request.method == "POST":

        kode = request.form["kode"].strip().upper()
        jenis = request.form["jenis"]
        kondisi = request.form["kondisi"]

        try:

            conn.execute("""
                UPDATE perangkat
                SET kode = ?,
                    jenis = ?,
                    kondisi = ?
                WHERE id = ?
            """, (
                kode,
                jenis,
                kondisi,
                id
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return """
            <script>
                alert("Kode perangkat sudah digunakan!");
                history.back();
            </script>
            """

        conn.close()

        return redirect(url_for("perangkat"))

    conn.close()

    return render_template(
        "tambah_perangkat.html",
        data=data,
        edit=True
    )


@app.route("/perangkat/nonaktif/<int:id>")
def nonaktif_perangkat(id):

    conn = get_db()

    data = conn.execute("""
        SELECT status
        FROM perangkat
        WHERE id = ?
    """, (id,)).fetchone()

    if not data:

        conn.close()

        return "Perangkat tidak ditemukan", 404

    if data["status"] == "Digunakan":

        conn.close()

        return """
        <script>
            alert("Perangkat sedang digunakan!");
            history.back();
        </script>
        """

    conn.execute("""
        UPDATE perangkat
        SET aktif = 0
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("perangkat"))


@app.route("/perangkat/aktif/<int:id>")
def aktif_perangkat(id):

    conn = get_db()

    conn.execute("""
        UPDATE perangkat
        SET aktif = 1
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("perangkat"))


@app.route("/perangkat/hapus/<int:id>")
def hapus_perangkat(id):

    conn = get_db()

    data = conn.execute("""
        SELECT *
        FROM perangkat
        WHERE id = ?
    """, (id,)).fetchone()

    if not data:

        conn.close()

        return "Perangkat tidak ditemukan", 404

    if data["status"] == "Digunakan":

        conn.close()

        return """
        <script>
            alert("Perangkat sedang digunakan dan tidak dapat dihapus!");
            history.back();
        </script>
        """

    riwayat = conn.execute("""
        SELECT COUNT(*) AS jumlah
        FROM penggunaan
        WHERE perangkat_id = ?
    """, (id,)).fetchone()

    if riwayat["jumlah"] > 0:

        conn.close()

        return """
        <script>
            alert("Perangkat sudah memiliki riwayat. Gunakan Nonaktifkan agar riwayat tetap aman.");
            history.back();
        </script>
        """

    conn.execute("""
        DELETE FROM perangkat
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("perangkat"))


# =========================
# PENGGUNAAN PERANGKAT
# =========================

@app.route("/penggunaan", methods=["GET", "POST"])
def penggunaan():

    conn = get_db()

    if request.method == "POST":

        nama = request.form["nama"].strip()
        nim = request.form["nim"].strip()
        jurusan = request.form["jurusan"].strip()
        angkatan = request.form["angkatan"].strip()

        perangkat_id = request.form["perangkat_id"]

        tanggal_pemakaian = request.form["tanggal_pemakaian"]

        tujuan = request.form["tujuan"].strip()

        kondisi_awal = request.form["kondisi_awal"]

        # Waktu mulai otomatis
        waktu_mulai = datetime.now().strftime("%H:%M:%S")

        perangkat_data = conn.execute("""
            SELECT *
            FROM perangkat
            WHERE id = ?
              AND aktif = 1
              AND status = 'Tersedia'
        """, (perangkat_id,)).fetchone()

        if not perangkat_data:

            conn.close()

            return """
            <script>
                alert("Perangkat tidak tersedia!");
                history.back();
            </script>
            """

        conn.execute("""
            INSERT INTO penggunaan
            (
                nama,
                nim,
                jurusan,
                angkatan,
                perangkat_id,
                tanggal_pemakaian,
                waktu_mulai,
                tujuan,
                kondisi_awal
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nama,
            nim,
            jurusan,
            angkatan,
            perangkat_id,
            tanggal_pemakaian,
            waktu_mulai,
            tujuan,
            kondisi_awal
        ))

        conn.execute("""
            UPDATE perangkat
            SET status = 'Digunakan',
                kondisi = ?
            WHERE id = ?
        """, (
            kondisi_awal,
            perangkat_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    perangkat_data = conn.execute("""
        SELECT *
        FROM perangkat
        WHERE aktif = 1
          AND status = 'Tersedia'
        ORDER BY id
    """).fetchall()

    conn.close()

    tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "penggunaan.html",
        perangkat=perangkat_data,
        tanggal_hari_ini=tanggal_hari_ini
    )


# =========================
# SELESAI PENGGUNAAN
# =========================

@app.route("/selesai/<int:id>", methods=["GET", "POST"])
def selesai(id):

    conn = get_db()

    data = conn.execute("""
        SELECT
            penggunaan.*,
            perangkat.kode,
            perangkat.jenis
        FROM penggunaan
        JOIN perangkat
            ON penggunaan.perangkat_id = perangkat.id
        WHERE penggunaan.id = ?
    """, (id,)).fetchone()

    if not data:

        conn.close()

        return "Data penggunaan tidak ditemukan", 404

    if data["status"] == "Selesai":

        conn.close()

        return redirect(url_for("riwayat"))

    if request.method == "POST":

        kondisi_akhir = request.form["kondisi_akhir"]

        # Waktu akhir otomatis
        waktu_akhir = datetime.now().strftime("%H:%M:%S")

        conn.execute("""
            UPDATE penggunaan
            SET waktu_akhir = ?,
                kondisi_akhir = ?,
                status = 'Selesai'
            WHERE id = ?
        """, (
            waktu_akhir,
            kondisi_akhir,
            id
        ))

        conn.execute("""
            UPDATE perangkat
            SET status = 'Tersedia',
                kondisi = ?
            WHERE id = ?
        """, (
            kondisi_akhir,
            data["perangkat_id"]
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    conn.close()

    return render_template(
        "selesai.html",
        data=data
    )


# =========================
# RIWAYAT
# =========================

@app.route("/riwayat")
def riwayat():

    kata_kunci = request.args.get("q", "").strip()

    conn = get_db()

    if kata_kunci:

        pencarian = f"%{kata_kunci}%"

        data = conn.execute("""
            SELECT
                penggunaan.*,
                perangkat.kode,
                perangkat.jenis
            FROM penggunaan
            JOIN perangkat
                ON penggunaan.perangkat_id = perangkat.id
            WHERE
                penggunaan.nama LIKE ?
                OR penggunaan.nim LIKE ?
                OR penggunaan.jurusan LIKE ?
                OR penggunaan.angkatan LIKE ?
                OR perangkat.kode LIKE ?
                OR perangkat.jenis LIKE ?
                OR penggunaan.tanggal_pemakaian LIKE ?
                OR penggunaan.tujuan LIKE ?
                OR penggunaan.kondisi_awal LIKE ?
                OR penggunaan.kondisi_akhir LIKE ?
            ORDER BY penggunaan.id DESC
        """, (
            pencarian,
            pencarian,
            pencarian,
            pencarian,
            pencarian,
            pencarian,
            pencarian,
            pencarian,
            pencarian,
            pencarian
        )).fetchall()

    else:

        data = conn.execute("""
            SELECT
                penggunaan.*,
                perangkat.kode,
                perangkat.jenis
            FROM penggunaan
            JOIN perangkat
                ON penggunaan.perangkat_id = perangkat.id
            ORDER BY penggunaan.id DESC
        """).fetchall()

    conn.close()

    return render_template(
        "riwayat.html",
        data=data,
        kata_kunci=kata_kunci
    )


# =========================
# HAPUS RIWAYAT
# =========================

@app.route("/riwayat/hapus/<int:id>")
def hapus_riwayat(id):

    conn = get_db()

    data = conn.execute("""
        SELECT perangkat_id, status
        FROM penggunaan
        WHERE id = ?
    """, (id,)).fetchone()

    if not data:

        conn.close()

        return "Data tidak ditemukan", 404

    if data["status"] == "Sedang Digunakan":

        conn.execute("""
            UPDATE perangkat
            SET status = 'Tersedia'
            WHERE id = ?
        """, (data["perangkat_id"],))

    conn.execute("""
        DELETE FROM penggunaan
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("riwayat"))


# =========================
# INISIALISASI DATABASE
# =========================

init_db()


# =========================
# MENJALANKAN APLIKASI
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        debug=True
    )