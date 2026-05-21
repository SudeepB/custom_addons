{
    "name": "KS TADA Management",
    "version": "1.0",
    "category": "Human Resources",
    "summary": "TADA rules for residential and local travel",
    "depends": ["base", "mail", "hr"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/ks_tada_settings_data.xml",
        "views/tada_settings_views.xml",
        "views/tada_config_views.xml",
        "views/menu.xml",
        "views/tada_request_views.xml",
        "report/tada_report.xml",
    ],
    "application": True,
    "installable": True,
}