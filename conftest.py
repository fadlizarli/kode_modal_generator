import sys
from unittest.mock import MagicMock

# Diperlukan agar Package.setup() bisa memuat __init__.py tanpa instalasi Odoo
sys.modules.setdefault('odoo', MagicMock())
sys.modules.setdefault('odoo.models', MagicMock())
