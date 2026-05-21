#!/usr/bin/env python3
"""
fill_modal_costs.py

Terminal app untuk mengisi standard_price (modal/cost) produk Odoo
berdasarkan kode_modal yang sudah terisi, menggunakan cipher MOBILSEDAN
atau ABCDEFGHIY.

Contoh penggunaan:
    python fill_modal_costs.py --db mydb --user admin --password secret
    python fill_modal_costs.py --db mydb --user admin --password secret --dry-run
    python fill_modal_costs.py --db mydb --user admin --password secret --interactive
"""

import argparse
import sys
import xmlrpc.client

# --------------------------------------------------------------------------- #
# Tabel cipher (sama dengan models/product_template.py)
# --------------------------------------------------------------------------- #
KODE_PERTAMA = {'1': 'M', '2': 'O', '3': 'B', '4': 'I', '5': 'L',
                '6': 'S', '7': 'E', '8': 'D', '9': 'A', '0': 'N'}
KODE_KEDUA   = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E',
                '6': 'F', '7': 'G', '8': 'H', '9': 'I', '0': 'Y'}

REVERSE_PERTAMA = {v: k for k, v in KODE_PERTAMA.items()}
REVERSE_KEDUA   = {v: k for k, v in KODE_KEDUA.items()}

# Huruf yang hanya ada di satu cipher (penanda unik)
MOBILSEDAN_ONLY = set('MOLSN')
ABCDEFGHIY_ONLY = set('CFGHY')

SUFFIX_MULT = {'JT': 1_000_000, 'RB': 1_000, 'RT': 100, '': 1}


# --------------------------------------------------------------------------- #
# Decode logic
# --------------------------------------------------------------------------- #
def _detect_cipher(letters: str) -> str:
    """Deteksi cipher dari huruf-huruf kode.

    Return: 'mobilsedan' | 'abcdefghiy' | 'ambiguous' | 'invalid'
    """
    ls = set(letters.upper())
    has_m = bool(ls & MOBILSEDAN_ONLY)
    has_a = bool(ls & ABCDEFGHIY_ONLY)
    if has_m and has_a:
        return 'invalid'
    if has_m:
        return 'mobilsedan'
    if has_a:
        return 'abcdefghiy'
    return 'ambiguous'


def decode_kode(kode: str, cipher: str | None = None) -> tuple[float, str]:
    """Decode kode_modal menjadi harga.

    Returns:
        (harga, nama_cipher)
    Raises:
        ValueError jika kode tidak bisa di-decode.
    """
    if not kode or not kode.strip():
        raise ValueError("Kode kosong")

    kode = kode.strip().upper()
    parts = kode.split()

    if len(parts) == 2:
        letters, suffix = parts[0], parts[1]
    elif len(parts) == 1:
        letters, suffix = parts[0], ''
        for sfx in ('JT', 'RB', 'RT'):
            if letters.endswith(sfx):
                letters = letters[:-len(sfx)]
                suffix = sfx
                break
    else:
        raise ValueError(f"Format tidak dikenal: {kode!r}")

    if suffix and suffix not in SUFFIX_MULT:
        raise ValueError(f"Suffix tidak dikenal: {suffix!r}")

    if not letters:
        raise ValueError(f"Bagian huruf kosong pada kode: {kode!r}")

    detected = cipher or _detect_cipher(letters)

    if detected == 'ambiguous':
        raise ValueError(
            f"Cipher ambigu (huruf {letters!r} ada di kedua cipher) — "
            "gunakan --cipher atau --interactive"
        )
    if detected == 'invalid':
        raise ValueError(f"Kode mengandung huruf dari dua cipher sekaligus: {kode!r}")

    mapping = REVERSE_PERTAMA if detected == 'mobilsedan' else REVERSE_KEDUA

    digits = ''
    for ch in letters:
        digit = mapping.get(ch)
        if digit is None:
            raise ValueError(f"Huruf {ch!r} tidak valid untuk cipher {detected!r}")
        digits += digit

    return int(digits) * SUFFIX_MULT.get(suffix, 1), detected


def decode_both(kode: str) -> dict:
    """Coba decode dengan kedua cipher. Berguna untuk kode ambigu."""
    result = {}
    for cipher_name in ('mobilsedan', 'abcdefghiy'):
        try:
            price, _ = decode_kode(kode, cipher_name)
            result[cipher_name] = price
        except ValueError:
            pass
    return result


# --------------------------------------------------------------------------- #
# Odoo XML-RPC helpers
# --------------------------------------------------------------------------- #
def odoo_connect(url: str, db: str, username: str, password: str):
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise ConnectionError("Autentikasi gagal. Periksa username/password.")
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    return models, uid


def fetch_products(models, uid: int, db: str, password: str) -> list[dict]:
    domain = [
        ['kode_modal', '!=', False],
        ['kode_modal', '!=', ''],
        ['standard_price', '=', 0],
    ]
    fields = ['id', 'name', 'kode_modal', 'standard_price']
    return models.execute_kw(db, uid, password,
                             'product.template', 'search_read',
                             [domain], {'fields': fields})


def update_product(models, uid: int, db: str, password: str,
                   product_id: int, price: float) -> None:
    models.execute_kw(db, uid, password,
                      'product.template', 'write',
                      [[product_id], {'standard_price': price}])


# --------------------------------------------------------------------------- #
# Terminal UI helpers
# --------------------------------------------------------------------------- #
def ask_cipher_for_ambiguous(product_name: str, kode: str) -> str | None:
    prices = decode_both(kode)
    if not prices:
        return None

    print(f"\n  Kode {kode!r} pada produk {product_name!r} ambigu:")
    options = list(prices.items())
    for i, (cipher, price) in enumerate(options, 1):
        print(f"    [{i}] {cipher:12s}  → Rp {price:,.0f}")
    print("    [s] Lewati (skip)")

    while True:
        choice = input("  Pilih cipher [1/2/s]: ").strip().lower()
        if choice == 's':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1][0]
        print("  Input tidak valid, coba lagi.")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Isi standard_price produk Odoo dari kode_modal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--url', default='http://localhost:8069',
                        help='URL Odoo server (default: http://localhost:8069)')
    parser.add_argument('--db', required=True, help='Nama database Odoo')
    parser.add_argument('--user', required=True, help='Username Odoo')
    parser.add_argument('--password', required=True, help='Password Odoo')
    parser.add_argument('--dry-run', action='store_true',
                        help='Tampilkan perubahan tanpa menyimpan')
    parser.add_argument('--cipher', choices=['mobilsedan', 'abcdefghiy'],
                        help='Paksa cipher tertentu untuk kode yang ambigu')
    parser.add_argument('--interactive', action='store_true',
                        help='Tanya cipher secara manual untuk kode ambigu')
    args = parser.parse_args()

    # Sambungkan ke Odoo
    print(f"\nMenyambungkan ke {args.url} (db={args.db}) ...")
    try:
        models, uid = odoo_connect(args.url, args.db, args.user, args.password)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    print("Koneksi berhasil.")

    # Ambil produk yang perlu diupdate
    print("\nMengambil produk dengan kode_modal terisi tapi standard_price = 0 ...")
    try:
        products = fetch_products(models, uid, args.db, args.password)
    except Exception as exc:
        print(f"ERROR saat mengambil data: {exc}", file=sys.stderr)
        sys.exit(1)

    if not products:
        print("Tidak ada produk yang perlu diupdate. Selesai.")
        return

    print(f"Ditemukan {len(products)} produk.\n")
    print(f"{'Nama Produk':<45} {'Kode Modal':<15} {'Status'}")
    print("-" * 80)

    updates: list[dict] = []
    skipped: list[dict] = []

    for p in products:
        name = p['name']
        kode = p['kode_modal']

        # Cek apakah kode ambigu dulu
        forced_cipher = args.cipher
        if not forced_cipher:
            detected = _detect_cipher(kode.split()[0] if ' ' in kode else kode.split('JT')[0].split('RB')[0].split('RT')[0])
            if detected == 'ambiguous' and args.interactive:
                forced_cipher = ask_cipher_for_ambiguous(name, kode)
                if not forced_cipher:
                    print(f"  {'[SKIP]':<8} {name:<45} {kode:<15} (dilewati)")
                    skipped.append({'name': name, 'kode': kode, 'reason': 'skip oleh user'})
                    continue

        try:
            price, cipher_used = decode_kode(kode, forced_cipher)
            status = f"→ Rp {price:>13,.0f}  [{cipher_used}]"
            print(f"  {'[OK]':<8} {name:<45} {kode:<15} {status}")
            updates.append({'id': p['id'], 'name': name, 'kode': kode,
                             'price': price, 'cipher': cipher_used})
        except ValueError as exc:
            reason = str(exc)
            print(f"  {'[ERROR]':<8} {name:<45} {kode:<15} {reason}")
            skipped.append({'name': name, 'kode': kode, 'reason': reason})

    print("-" * 80)
    print(f"\nRingkasan: {len(updates)} siap diupdate, {len(skipped)} dilewati.\n")

    if not updates:
        print("Tidak ada yang bisa diupdate.")
        return

    if args.dry_run:
        print("[DRY RUN] Tidak ada perubahan yang disimpan ke Odoo.")
        return

    confirm = input("Lanjutkan update ke Odoo? [y/N] ").strip().lower()
    if confirm != 'y':
        print("Dibatalkan.")
        return

    print("\nMengupdate ...")
    ok, fail = 0, 0
    for u in updates:
        try:
            update_product(models, uid, args.db, args.password, u['id'], u['price'])
            print(f"  OK  {u['name']!r} → Rp {u['price']:,.0f}")
            ok += 1
        except Exception as exc:
            print(f"  FAIL {u['name']!r} → {exc}")
            fail += 1

    print(f"\nSelesai: {ok} berhasil diupdate, {fail} gagal.")


if __name__ == '__main__':
    main()
