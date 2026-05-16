# Kode Modal Generator

Module Odoo 17 untuk generate kode modal produk secara otomatis dari harga HPP (Cost).

## Fitur

- Tombol **Label 1** → generate kode menggunakan cipher **MOBILSEDAN**
- Tombol **Label 2** → generate kode menggunakan cipher **ABCDEFGHIL**
- Unit suffix otomatis: **JT** (juta), **RB** (ribu), **RT** (ratus)
- Kode modal tampil di **POS** saat produk dibuka

## Tabel Cipher

| Angka | Label 1 (MOBILSEDAN) | Label 2 (ABCDEFGHIL) |
|-------|----------------------|----------------------|
| 1     | M                    | A                    |
| 2     | O                    | B                    |
| 3     | B                    | C                    |
| 4     | I                    | D                    |
| 5     | L                    | E                    |
| 6     | S                    | F                    |
| 7     | E                    | G                    |
| 8     | D                    | H                    |
| 9     | A                    | I                    |
| 0     | N                    | L                    |

## Contoh

| Harga (Rp) | Label 1  | Label 2  |
|------------|----------|----------|
| 1.000      | M RB     | A RB     |
| 5.000      | L RB     | E RB     |
| 20.000     | ON RB    | BL RB    |
| 150.000    | MLN RB   | AEL RB   |
| 1.000.000  | M JT     | A JT     |
| 2.500.000  | OLN RB   | BEL RB   |

## Dependensi

- `product_kode_modal`
- `point_of_sale`

## Instalasi

1. Copy folder `kode_modal_generator` ke direktori addons Odoo
2. Restart Odoo
3. Aktifkan Developer Mode
4. Apps → Update Apps List
5. Install **Kode Modal Generator**

## Cara Pakai

1. Buka produk di menu Inventory atau Point of Sale
2. Tab **General Information** → bagian **Cost**
3. Di bawah Cost terdapat field **Kode Modal**
4. Klik **Label 1** atau **Label 2** untuk generate kode otomatis dari HPP
5. Simpan produk
