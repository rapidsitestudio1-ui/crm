import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

STAGES = ["New", "Contacted", "Prospect", "Customer", "Inactive"]


def execute():
	"""Contact Stage: the column field of the Contacts Kanban board."""
	create_custom_fields(
		{
			"Contact": [
				{
					"fieldname": "contact_stage",
					"label": "Stage",
					"fieldtype": "Select",
					"options": "\n".join(STAGES),
					"default": "New",
					"insert_after": "status",
					"in_standard_filter": 1,
				}
			]
		},
		ignore_validate=True,
	)
	# Existing contacts start in the first column.
	frappe.db.sql("UPDATE `tabContact` SET contact_stage = 'New' WHERE IFNULL(contact_stage, '') = ''")
