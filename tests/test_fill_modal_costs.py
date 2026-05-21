"""Unit test untuk fungsi decode di fill_modal_costs.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fill_modal_costs import decode_kode, _detect_cipher, decode_both


class TestDetectCipher:
    def test_mobilsedan_unik(self):
        # M, O, L, S, N hanya ada di MOBILSEDAN
        assert _detect_cipher('M') == 'mobilsedan'
        assert _detect_cipher('ON') == 'mobilsedan'
        assert _detect_cipher('MLN') == 'mobilsedan'

    def test_abcdefghiy_unik(self):
        # C, F, G, H, Y hanya ada di ABCDEFGHIY
        assert _detect_cipher('C') == 'abcdefghiy'
        assert _detect_cipher('GHY') == 'abcdefghiy'

    def test_ambiguous(self):
        # A, B, D, E, I ada di kedua cipher
        assert _detect_cipher('A') == 'ambiguous'
        assert _detect_cipher('ABDE') == 'ambiguous'
        assert _detect_cipher('I') == 'ambiguous'

    def test_invalid(self):
        # Gabungan huruf unik dari kedua cipher
        assert _detect_cipher('MC') == 'invalid'
        assert _detect_cipher('MY') == 'invalid'


class TestDecodeKode:
    # ---- Cipher MOBILSEDAN ----
    def test_mobilsedan_rb(self):
        price, cipher = decode_kode('M RB')
        assert price == 1_000
        assert cipher == 'mobilsedan'

    def test_mobilsedan_l_rb(self):
        price, _ = decode_kode('L RB')
        assert price == 5_000

    def test_mobilsedan_on_rb(self):
        price, _ = decode_kode('ON RB')
        assert price == 20_000

    def test_mobilsedan_mln_rb(self):
        price, _ = decode_kode('MLN RB')
        assert price == 150_000

    def test_mobilsedan_jt(self):
        price, _ = decode_kode('M JT')
        assert price == 1_000_000

    def test_mobilsedan_oln_rb(self):
        # 250.000 → encode: 250 × RB → O=2, L=5, N=0 → OLN RB
        price, _ = decode_kode('OLN RB')
        assert price == 250_000

    # ---- Cipher ABCDEFGHIY ----
    def test_abcdefghiy_rb(self):
        # A ada di kedua cipher → harus paksa cipher
        price, cipher = decode_kode('A RB', cipher='abcdefghiy')
        assert price == 1_000
        assert cipher == 'abcdefghiy'

    def test_abcdefghiy_e_rb(self):
        # E ada di kedua cipher → harus paksa cipher
        price, _ = decode_kode('E RB', cipher='abcdefghiy')
        assert price == 5_000

    def test_abcdefghiy_by_rb(self):
        price, _ = decode_kode('BY RB')
        assert price == 20_000

    def test_abcdefghiy_ael_rb(self):
        price, _ = decode_kode('AEY RB')
        # A=1, E=5, Y=0 → 150 × 1000 = 150_000
        assert price == 150_000

    def test_abcdefghiy_a_jt(self):
        # A ada di kedua cipher → harus paksa cipher
        price, _ = decode_kode('A JT', cipher='abcdefghiy')
        assert price == 1_000_000

    # ---- Force cipher ----
    def test_force_mobilsedan_on_ambiguous(self):
        # 'A' ambigu → paksa mobilsedan: A=9 → 9*1000=9000
        price, cipher = decode_kode('A RB', cipher='mobilsedan')
        assert price == 9_000
        assert cipher == 'mobilsedan'

    def test_force_abcdefghiy_on_ambiguous(self):
        # 'A' ambigu → paksa abcdefghiy: A=1 → 1*1000=1000
        price, cipher = decode_kode('A RB', cipher='abcdefghiy')
        assert price == 1_000
        assert cipher == 'abcdefghiy'

    # ---- Error cases ----
    def test_empty_kode(self):
        with pytest.raises(ValueError, match="kosong"):
            decode_kode('')

    def test_ambiguous_without_force(self):
        with pytest.raises(ValueError, match="ambigu"):
            decode_kode('A RB')

    def test_invalid_mixed_cipher(self):
        with pytest.raises(ValueError, match="dua cipher"):
            decode_kode('MC RB')

    def test_unknown_suffix(self):
        with pytest.raises(ValueError, match="Suffix"):
            decode_kode('M XY')

    # ---- Case insensitive ----
    def test_lowercase_input(self):
        price, cipher = decode_kode('m rb')
        assert price == 1_000
        assert cipher == 'mobilsedan'

    # ---- RT suffix ----
    def test_rt_suffix(self):
        # S = 6, RT = ×100 → 600
        price, _ = decode_kode('S RT')
        assert price == 600


class TestDecodeBoth:
    def test_ambiguous_returns_both(self):
        result = decode_both('A RB')
        assert 'mobilsedan' in result
        assert 'abcdefghiy' in result
        assert result['mobilsedan'] == 9_000   # A=9 in MOBILSEDAN
        assert result['abcdefghiy'] == 1_000   # A=1 in ABCDEFGHIY

    def test_clear_mobilsedan_returns_one(self):
        result = decode_both('M RB')
        assert 'mobilsedan' in result
        assert result['mobilsedan'] == 1_000
