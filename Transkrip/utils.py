# Konversi nilai angka → huruf → bobot
GRADE_TABLE = [
    (85, "A",  4.0),
    (80, "A-", 3.7),
    (75, "B+", 3.3),
    (70, "B",  3.0),
    (65, "B-", 2.7),
    (60, "C+", 2.3),
    (55, "C",  2.0),
    (40, "D",  1.0),
    (0,  "E",  0.0),
]

def hitung_nilai_akhir(uts, uas, tes1, tes2):
    """Bobot: UTS 30%, UAS 40%, Tes1 15%, Tes2 15%"""
    return (uts * 0.30) + (uas * 0.40) + (tes1 * 0.15) + (tes2 * 0.15)

def nilai_ke_huruf(nilai_angka):
    for batas, huruf, bobot in GRADE_TABLE:
        if nilai_angka >= batas:
            return huruf, bobot
    return "E", 0.0

def hitung_ips(detail_nilai_list):
    """
    detail_nilai_list: list of dict {"sks": int, "bobot": float}
    Returns IPS (float)
    """
    total_sks    = sum(d["sks"] for d in detail_nilai_list)
    total_mutu   = sum(d["sks"] * d["bobot"] for d in detail_nilai_list)
    return round(total_mutu / total_sks, 2) if total_sks > 0 else 0.0

def semua_nilai_lengkap(nilai: dict) -> bool:
    """Cek apakah semua komponen nilai sudah terisi."""
    return all(
        nilai.get(k) is not None
        for k in ["nilai_uts", "nilai_uas", "nilai_tes1", "nilai_tes2"]
    )