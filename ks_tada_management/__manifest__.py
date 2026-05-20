{
    "name": "KS TADA Management",
    "version": "1.0",
    "category": "Human Resources",
    "summary": "TADA rules for residential and local travel",
    "depends": ["base", "mail", "hr"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/menu.xml",
        "views/tada_request_views.xml",
    ],
    "application": True,
    "installable": True,
}