{
    'name': 'Cotação',
    'version': '14.0.1.0.1',
    'summary': "",
    'description': "",
    'category': 'Sales',
    'author': 'Felipe Rocha Dias',
    'company': 'SUPERGLASS',
    'depends': ['base', 'sale_management', 'routes-main', 'product', 'account'],
    'data': [
        'wizard/cotacoes_wizard_view.xml',
        'wizard/pesquisa_de_produto.xml',
        'wizard/product_inherit.xml',
        'wizard/product_info.xml',
        'wizard/product_cotado_view.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
}
