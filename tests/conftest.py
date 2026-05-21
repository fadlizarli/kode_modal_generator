import sys
import os

# Tambah root project ke path tanpa melewati __init__.py Odoo
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
