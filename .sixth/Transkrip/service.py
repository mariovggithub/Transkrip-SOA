import nameko
from nameko.rpc import rpc, RpcProxy
from nameko_sqlalchemy import DatabaseSession
from .models import Base, KRS, KHS, KHSDetail, Nilai, Transkrip, DetailTranskrip, StatusNilai
from .utils import (
    hitung_nilai_akhir, nilai_ke_huruf,
    hitung_ips, semua_nilai_lengkap
)

class TranskripService:
    name = "transkrip_service"

    db     = DatabaseSession(Base)
    master = RpcProxy("master_service")
    prs    = RpcProxy("prs_service")

    # ──────────────────────────────────────────────
    # 1. PUSH PRS TERVALIDASI → KRS
    # Dipanggil oleh PRS service setelah approval
    # ──────────────────────────────────────────────
    @rpc
    def push_prs_ke_krs(self, id_prs: int):
        """
        Terima PRS yang sudah divalidasi dari service PRS.
        Buat record KRS dan inisialisasi Nilai kosong per matkul.
        """
        # Ambil detail PRS dari service PRS
        prs_data   = self.prs.get_prs_by_id(id_prs)
        prs_detail = self.prs.get_prs_detail_by_prs_id(id_prs)

        # Cek KRS belum dibuat untuk PRS ini
        existing = self.db.query(KRS).filter_by(id_prs=id_prs).first()
        if existing:
            return {"status": "error", "message": "KRS untuk PRS ini sudah ada"}

        krs = KRS(id_prs=id_prs, status_nilai=StatusNilai.BELUM_TERNILAI)
        self.db.add(krs)
        self.db.flush()  # dapat id_krs

        # Inisialisasi Nilai kosong untuk setiap matkul di PRS
        for detail in prs_detail:
            nilai = Nilai(
                id_matkul=detail["id_matkul"],
                id_krs=krs.id_krs,
                nilai_uts=None, nilai_uas=None,
                nilai_tes1=None, nilai_tes2=None,
            )
            self.db.add(nilai)

        self.db.commit()
        return {"status": "ok", "id_krs": krs.id_krs}

    # ──────────────────────────────────────────────
    # 2. INPUT NILAI (oleh Dosen)
    # ──────────────────────────────────────────────
    @rpc
    def input_nilai(self, id_nilai: int, komponen: str, nilai: float):
        """
        Dosen input nilai per komponen (uts/uas/tes1/tes2).
        Jika semua komponen lengkap → hitung nilai akhir,
        update status KRS → SUDAH_TERNILAI, masukkan ke KHS.
        """
        record = self.db.query(Nilai).filter_by(id_nilai=id_nilai).first()
        if not record:
            return {"status": "error", "message": "Nilai tidak ditemukan"}

        setattr(record, f"nilai_{komponen}", nilai)

        # Cek apakah semua komponen sudah terisi
        data = {
            "nilai_uts":  record.nilai_uts,
            "nilai_uas":  record.nilai_uas,
            "nilai_tes1": record.nilai_tes1,
            "nilai_tes2": record.nilai_tes2,
        }

        if semua_nilai_lengkap(data):
            # Hitung nilai akhir & huruf
            akhir          = hitung_nilai_akhir(**data)
            huruf, bobot   = nilai_ke_huruf(akhir)
            record.nilai_akhir = akhir
            record.nilai_huruf = huruf

            # Update status KRS
            krs = self.db.query(KRS).filter_by(id_krs=record.id_krs).first()
            krs.status_nilai = StatusNilai.SUDAH_TERNILAI

            # Masukkan ke KHS
            self._masukkan_ke_khs(krs, record)

        self.db.commit()
        return {"status": "ok", "nilai_huruf": record.nilai_huruf}

    def _masukkan_ke_khs(self, krs: KRS, nilai: Nilai):
        """Internal: buat/update KHS dan KHS_DETAIL, lalu hitung ulang IPS/IPK."""
        # Ambil info semester dari PRS service
        prs_data = self.prs.get_prs_by_id(krs.id_prs)
        semester     = prs_data["semester"]
        tahun_ajaran = prs_data["tahun_ajaran"]
        id_mahasiswa = prs_data["id_mahasiswa"]

        # Cari atau buat KHS untuk KRS ini
        khs = self.db.query(KHS).filter_by(id_krs=krs.id_krs).first()
        if not khs:
            khs = KHS(
                id_krs=krs.id_krs,
                semester=semester,
                tahun_ajaran=tahun_ajaran,
            )
            self.db.add(khs)
            self.db.flush()

        # Ambil SKS matkul dari Master service
        matkul_data = self.master.get_matkul_by_id(nilai.id_matkul)
        sks         = matkul_data["sks"]

        # Tambah KHS_DETAIL
        detail = KHSDetail(
            id_khs=khs.id_khs,
            id_nilai=nilai.id_nilai,
            sks=sks,
            nilai_huruf=nilai.nilai_huruf,
            nilai_akhir=nilai.nilai_akhir,
        )
        self.db.add(detail)
        self.db.flush()

        # Hitung ulang IPS semester & IPK
        self._hitung_ips_ipk(id_mahasiswa, semester, tahun_ajaran)

    def _hitung_ips_ipk(self, id_mahasiswa, semester, tahun_ajaran):
        """Hitung ulang IPS semester ini dan IPK keseluruhan."""
        from sqlalchemy import func

        # Ambil semua KRS mahasiswa di semester ini
        prs_ids_semester = self.prs.get_prs_ids_by_mahasiswa_semester(
            id_mahasiswa, semester, tahun_ajaran
        )

        detail_semester = []
        for pid in prs_ids_semester:
            krs = self.db.query(KRS).filter_by(id_prs=pid).first()
            if not krs or krs.status_nilai != StatusNilai.SUDAH_TERNILAI:
                continue
            khs = self.db.query(KHS).filter_by(id_krs=krs.id_krs).first()
            if not khs:
                continue
            details = self.db.query(KHSDetail).filter_by(id_khs=khs.id_khs).all()
            for d in details:
                _, bobot = nilai_ke_huruf(d.nilai_akhir)
                detail_semester.append({"sks": d.sks, "bobot": bobot})

        ips_semester = hitung_ips(detail_semester)

        # Update Transkrip
        transkrip = self.db.query(Transkrip).filter_by(
            id_mahasiswa=id_mahasiswa
        ).first()
        if not transkrip:
            transkrip = Transkrip(id_mahasiswa=id_mahasiswa)
            self.db.add(transkrip)

        # IPK = rata-rata berbobot semua semester
        semua_khs_detail = self._get_all_khs_detail_mahasiswa(id_mahasiswa)
        transkrip.total_sks = sum(d["sks"] for d in semua_khs_detail)
        transkrip.ips       = ips_semester
        transkrip.ipk       = hitung_ips(semua_khs_detail)

    def _get_all_khs_detail_mahasiswa(self, id_mahasiswa):
        """Ambil semua KHS_DETAIL mahasiswa lintas semester untuk IPK."""
        prs_ids = self.prs.get_all_prs_ids_by_mahasiswa(id_mahasiswa)
        result  = []
        for pid in prs_ids:
            krs = self.db.query(KRS).filter_by(id_prs=pid).first()
            if not krs or krs.status_nilai != StatusNilai.SUDAH_TERNILAI:
                continue
            khs = self.db.query(KHS).filter_by(id_krs=krs.id_krs).first()
            if not khs:
                continue
            for d in self.db.query(KHSDetail).filter_by(id_khs=khs.id_khs).all():
                _, bobot = nilai_ke_huruf(d.nilai_akhir)
                result.append({"sks": d.sks, "bobot": bobot})
        return result

    # ──────────────────────────────────────────────
    # 3. READ endpoints
    # ──────────────────────────────────────────────
    @rpc
    def get_khs_by_mahasiswa(self, id_mahasiswa: int, semester: str, tahun_ajaran: str):
        """Lihat KHS mahasiswa per semester (nilai matkul semester ini)."""
        prs_ids = self.prs.get_prs_ids_by_mahasiswa_semester(
            id_mahasiswa, semester, tahun_ajaran
        )
        hasil = []
        for pid in prs_ids:
            krs = self.db.query(KRS).filter_by(id_prs=pid).first()
            if not krs:
                continue
            khs = self.db.query(KHS).filter_by(id_krs=krs.id_krs).first()
            if not khs:
                continue
            details = self.db.query(KHSDetail).filter_by(id_khs=khs.id_khs).all()
            for d in details:
                nilai = self.db.query(Nilai).filter_by(id_nilai=d.id_nilai).first()
                matkul = self.master.get_matkul_by_id(nilai.id_matkul)
                hasil.append({
                    "nama_matkul":  matkul["nama_matkul"],
                    "sks":          d.sks,
                    "nilai_uts":    nilai.nilai_uts,
                    "nilai_uas":    nilai.nilai_uas,
                    "nilai_tes1":   nilai.nilai_tes1,
                    "nilai_tes2":   nilai.nilai_tes2,
                    "nilai_akhir":  d.nilai_akhir,
                    "nilai_huruf":  d.nilai_huruf,
                    "status":       krs.status_nilai,
                })
        return hasil

    @rpc
    def get_transkrip_mahasiswa(self, id_mahasiswa: int):
        """Lihat transkrip lengkap + IPS tiap semester + IPK."""
        transkrip = self.db.query(Transkrip).filter_by(
            id_mahasiswa=id_mahasiswa
        ).first()
        if not transkrip:
            return {"status": "error", "message": "Transkrip belum ada"}

        mahasiswa = self.master.get_mahasiswa_by_id(id_mahasiswa)
        details   = self.db.query(DetailTranskrip).filter_by(
            id_transkrip=transkrip.id_transkrip
        ).all()

        return {
            "mahasiswa":  mahasiswa,
            "total_sks":  transkrip.total_sks,
            "ipk":        transkrip.ipk,
            "detail":     [
                {
                    "sks":         d.sks,
                    "nilai_huruf": d.nilai_huruf,
                    "nilai_akhir": d.nilai_akhir,
                }
                for d in details
            ],
        }

    @rpc
    def get_ips_mahasiswa(self, id_mahasiswa: int, semester: str, tahun_ajaran: str):
        """Ambil IPS mahasiswa untuk semester tertentu."""
        transkrip = self.db.query(Transkrip).filter_by(
            id_mahasiswa=id_mahasiswa
        ).first()
        return {"ips": transkrip.ips if transkrip else 0.0}

    @rpc
    def get_ipk_mahasiswa(self, id_mahasiswa: int):
        """Ambil IPK terkini mahasiswa."""
        transkrip = self.db.query(Transkrip).filter_by(
            id_mahasiswa=id_mahasiswa
        ).first()
        return {"ipk": transkrip.ipk if transkrip else 0.0}