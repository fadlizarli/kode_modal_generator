#!/usr/bin/env python3
"""
Isi kolom standard_price (modal/cost) dari kode_modal menggunakan cipher ABCDEFGHIY.
Konek ke Odoo via XML-RPC, cari produk yang kode_modal-nya terisi tapi standard_price = 0,
decode kode_modal, lalu update standard_price langsung ke Odoo.
"""

import sys
import argparse
import getpass
import xmlrpc.client


# Cipher ABCDEFGHIY (Label 2) - reverse mapping untuk decode
KODE_KEDUA_REVERSE = {
    'A': '1', 'B': '2', 'C': '3', 'D': '4', 'E': '5',
    'F': '6', 'G': '7', 'H': '8', 'I': '9', 'Y': '0',
}

SUFFIX_MULTIPLIER = {
    'JT': 1_000_000,
    'RB': 1_000,
    'RT': 100,
    '':   1,
}


def decode_kode_modal(kode_modal: str):
    """
    Decode kode_modal menggunakan cipher ABCDEFGHIY.
    Kembalikan harga (int) jika berhasil, atau None jika format tidak valid / bukan cipher ini.
    """
    kode_modal = kode_modal.strip().upper()
    if not kode_modal:
        return None

    parts = kode_modal.split()
    if len(parts) == 2:
        letters, suffix = parts[0], parts[1]
    elif len(parts) == 1:
        letters, suffix = parts[0], ''
    else:
        return None

    if suffix not in SUFFIX_MULTIPLIER:
        return None

    digits = ''
    for ch in letters:
        if ch not in KODE_KEDUA_REVERSE:
            # Mengandung huruf bukan dari cipher ABCDEFGHIY (misal dari MOBILSEDAN)
            return None
        digits += KODE_KEDUA_REVERSE[ch]

    try:
        number = int(digits)
    except ValueError:
        return None

    if number <= 0:
        return None

    return number * SUFFIX_MULTIPLIER[suffix]


def connect_odoo(url, db, username, password):
    """Konek ke Odoo via XML-RPC. Kembalikan (uid, models_proxy)."""
    url = url.rstrip('/')
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise ValueError("Autentikasi gagal. Periksa username/password.")
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    return uid, models


def get_products_to_fill(uid, models, db, password):
    """Ambil produk yang kode_modal terisi tapi standard_price masih 0."""
    domain = [
        ['kode_modal', '!=', False],
        ['kode_modal', '!=', ''],
        ['standard_price', '=', 0],
    ]
    return models.execute_kw(
        db, uid, password,
        'product.template', 'search_read',
        [domain],
        {'fields': ['id', 'name', 'kode_modal'], 'order': 'name asc'},
    )


def update_product_cost(uid, models, db, password, product_id, cost):
    """Update standard_price satu produk di Odoo."""
    return models.execute_kw(
        db, uid, password,
        'product.template', 'write',
        [[product_id], {'standard_price': float(cost)}],
    )


def rp(amount):
    return f"Rp {amount:,.0f}".replace(',', '.')


def sep(char='-', width=72):
    print(char * width)


def main():
    parser = argparse.ArgumentParser(
        description='Isi standard_price dari kode_modal (cipher ABCDEFGHIY) via Odoo XML-RPC'
    )
    parser.add_argument('--url',      help='URL Odoo (contoh: http://localhost:8069)')
    parser.add_argument('--db',       help='Nama database Odoo')
    parser.add_argument('--user',     help='Username / email Odoo')
    parser.add_argument('--dry-run',  action='store_true',
                        help='Tampilkan perubahan tanpa menyimpan ke Odoo')
    args = parser.parse_args()

    print()
    sep('=')
    print("  FILL MODAL COSTS  |  Cipher ABCDEFGHIY  |  Odoo XML-RPC")
    sep('=')
    print()

    # --- Input koneksi ---
    url      = args.url  or input("URL Odoo  (contoh: http://localhost:8069) : ").strip()
    db       = args.db   or input("Database                                  : ").strip()
    username = args.user or input("Username / email                          : ").strip()
    password = getpass.getpass("Password                                  : ")

    if args.dry_run:
        print("\n[DRY-RUN] Tidak ada perubahan yang akan disimpan ke Odoo.\n")

    # --- Koneksi ---
    print("\nMenghubungkan ke Odoo...", end=' ', flush=True)
    try:
        uid, models = connect_odoo(url, db, username, password)
        print(f"OK (UID {uid})")
    except Exception as exc:
        print(f"\nGagal: {exc}")
        sys.exit(1)

    # --- Ambil produk ---
    print("Mencari produk (kode_modal terisi, standard_price = 0)...", end=' ', flush=True)
    try:
        products = get_products_to_fill(uid, models, db, password)
    except Exception as exc:
        print(f"\nGagal mengambil data: {exc}")
        sys.exit(1)

    print(f"ditemukan {len(products)} produk.")

    if not products:
        print("\nTidak ada produk yang perlu diisi. Semua sudah lengkap!")
        sys.exit(0)

    # --- Decode ---
    to_update = []   # [(id, name, kode, decoded_price)]
    skipped   = []   # [(name, kode, alasan)]

    for p in products:
        price = decode_kode_modal(p['kode_modal'])
        if price:
            to_update.append((p['id'], p['name'], p['kode_modal'], price))
        else:
            alasan = "Format tidak valid atau bukan cipher ABCDEFGHIY"
            skipped.append((p['name'], p['kode_modal'], alasan))

    # --- Tampilkan tabel ---
    print()
    if to_update:
        sep()
        print(f"  {'#':<4} {'Nama Produk':<38} {'Kode':<10} {'Modal (Cost)'}")
        sep()
        for i, (_, name, kode, price) in enumerate(to_update, 1):
            name_short = name[:37] if len(name) > 37 else name
            print(f"  {i:<4} {name_short:<38} {kode:<10} {rp(price)}")
        sep()

    if skipped:
        print(f"\nDilewati ({len(skipped)} produk) — tidak dapat didecode:")
        for name, kode, alasan in skipped:
            print(f"  - {name[:40]!r:42}  kode: {kode!r}  ({alasan})")

    if not to_update:
        print("\nTidak ada produk yang bisa diupdate.")
        sys.exit(0)

    print(f"\nRingkasan: {len(to_update)} akan diupdate, {len(skipped)} dilewati.\n")

    if args.dry_run:
        print("[DRY-RUN] Selesai. Jalankan tanpa --dry-run untuk menyimpan.")
        sys.exit(0)

    # --- Konfirmasi ---
    confirm = input(f"Update {len(to_update)} produk ke Odoo? (ketik 'ya' untuk lanjut): ")
    if confirm.strip().lower() not in ('ya', 'y'):
        print("Dibatalkan.")
        sys.exit(0)

    # --- Update ---
    print()
    ok_count   = 0
    fail_count = 0

    for pid, name, kode, price in to_update:
        try:
            update_product_cost(uid, models, db, password, pid, price)
            name_short = name[:45] if len(name) > 45 else name
            print(f"  [OK]    {name_short:<45}  →  {rp(price)}")
            ok_count += 1
        except Exception as exc:
            print(f"  [GAGAL] {name[:45]}: {exc}")
            fail_count += 1

    print()
    sep('=')
    print(f"  Selesai: {ok_count} berhasil diupdate, {fail_count} gagal.")
    sep('=')
    print()


if __name__ == '__main__':
    main()
