{
    'name': 'Kode Modal Generator',
    'version': '17.0.1.0.2',
    'category': 'Inventory',
    'summary': 'Tombol generator kode modal Label 1 dan Label 2',
    'depends': ['product_kode_modal'],
    'data': [
        'views/product_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kode_modal_generator/static/src/css/kode_modal.css',
        ],
    },
    'installable': True,
    'auto_install': False,
}
