"""Data for the contact profile page: deals, organization, location and a merged
activity timeline. Read-only; everything goes through frappe.get_list, so the
user's permissions apply to every source."""

import re

import frappe
from frappe import _
from frappe.utils import get_datetime, strip_html

LIMIT = 50


def _digits(phone: str | None) -> str:
	return re.sub(r"\D", "", phone or "")


def _phone_key(phone: str | None) -> str:
	# Compare on the last 9 digits so "+1 555 000 7890" matches "5550007890".
	d = _digits(phone)
	return d[-9:] if len(d) >= 7 else ""


@frappe.whitelist()
def get_contact_profile(contact: str):
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Contact", contact)

	deal_names = [
		d.parent
		for d in frappe.get_all(
			"CRM Contacts",
			filters={"contact": contact, "parenttype": "CRM Deal"},
			fields=["parent"],
			distinct=True,
		)
	]
	deals = (
		frappe.get_list(
			"CRM Deal",
			filters={"name": ["in", deal_names]},
			fields=[
				"name",
				"organization",
				"status",
				"deal_value",
				"currency",
				"probability",
				"expected_closure_date",
				"source",
				"deal_owner",
				"modified",
			],
			order_by="modified desc",
		)
		if deal_names
		else []
	)
	deal_names = [d.name for d in deals]  # only the ones this user can read
	for d in deals:
		d["status_type"] = frappe.db.get_value("CRM Deal Status", d.status, "type")

	return {
		"deals": deals,
		"organization": _organization(doc.company_name),
		"location": _location(doc.address),
		"activity": _activity(doc, deal_names),
	}


def _organization(name: str | None):
	if not name or not frappe.db.exists("CRM Organization", name):
		return None
	if not frappe.has_permission("CRM Organization", "read", name):
		return None
	return frappe.db.get_value(
		"CRM Organization",
		name,
		[
			"name",
			"organization_logo",
			"website",
			"industry",
			"territory",
			"no_of_employees",
			"annual_revenue",
			"currency",
		],
		as_dict=True,
	)


def _location(address: str | None):
	if not address or not frappe.has_permission("Address", "read", address):
		return None
	a = frappe.db.get_value("Address", address, ["city", "state", "country"], as_dict=True)
	if not a:
		return None
	tz = None
	if a.country:
		zones = frappe.db.get_value("Country", a.country, "time_zones") or ""
		tz = next((z.strip() for z in zones.split("\n") if z.strip()), None)
	return {
		"label": ", ".join([p for p in [a.city, a.state, a.country] if p]),
		"time_zone": tz,
	}


def _list_on(doctype, contact, deal_names, name_field, fields, extra_filters=None, order_by="creation desc"):
	"""Records referencing the contact itself, plus records on their deals."""
	out = frappe.get_list(
		doctype,
		filters={"reference_doctype": "Contact", name_field: contact, **(extra_filters or {})},
		fields=fields,
		order_by=order_by,
		limit=LIMIT,
	)
	if deal_names:
		out += frappe.get_list(
			doctype,
			filters={"reference_doctype": "CRM Deal", name_field: ["in", deal_names], **(extra_filters or {})},
			fields=fields,
			order_by=order_by,
			limit=LIMIT,
		)
	return out


def _activity(doc, deal_names):
	contact = doc.name
	items = [
		{
			"type": "added",
			"time": doc.creation,
			"by": doc.owner,
		}
	]

	for n in _list_on(
		"FCRM Note",
		contact,
		deal_names,
		"reference_docname",
		["name", "title", "content", "owner", "creation", "reference_doctype", "reference_docname"],
	):
		items.append(
			{
				"type": "note",
				"name": n.name,
				"title": n.title,
				"text": strip_html(n.content or "")[:280],
				"time": n.creation,
				"by": n.owner,
				"ref_doctype": n.reference_doctype,
				"ref_name": n.reference_docname,
			}
		)

	for t in _list_on(
		"CRM Task",
		contact,
		deal_names,
		"reference_docname",
		[
			"name",
			"title",
			"status",
			"priority",
			"due_date",
			"owner",
			"creation",
			"reference_doctype",
			"reference_docname",
		],
	):
		items.append(
			{
				"type": "task",
				"name": t.name,
				"title": t.title,
				"status": t.status,
				"priority": t.priority,
				"due_date": t.due_date,
				"time": t.creation,
				"by": t.owner,
				"ref_doctype": t.reference_doctype,
				"ref_name": t.reference_docname,
			}
		)

	for c in _list_on(
		"Comment",
		contact,
		deal_names,
		"reference_name",
		["name", "content", "owner", "creation", "reference_doctype", "reference_name"],
		extra_filters={"comment_type": "Comment"},
	):
		items.append(
			{
				"type": "comment",
				"name": c.name,
				"text": strip_html(c.content or "")[:280],
				"time": c.creation,
				"by": c.owner,
				"ref_doctype": c.reference_doctype,
				"ref_name": c.reference_name,
			}
		)

	# Emails: on the contact, on their deals, or linked to the contact by
	# Frappe's timeline links (set automatically from the email address).
	email_fields = [
		"name",
		"subject",
		"sent_or_received",
		"sender",
		"sender_full_name",
		"recipients",
		"communication_date",
		"content",
		"reference_doctype",
		"reference_name",
	]
	linked = [
		r.parent
		for r in frappe.get_all(
			"Communication Link",
			filters={"link_doctype": "Contact", "link_name": contact},
			fields=["parent"],
		)
	]
	emails = {}
	sources = [
		{"reference_doctype": "Contact", "reference_name": contact},
	]
	if deal_names:
		sources.append({"reference_doctype": "CRM Deal", "reference_name": ["in", deal_names]})
	if linked:
		sources.append({"name": ["in", linked]})
	for f in sources:
		for e in frappe.get_list(
			"Communication",
			filters={**f, "communication_medium": "Email"},
			fields=email_fields,
			order_by="communication_date desc",
			limit=LIMIT,
		):
			emails[e.name] = e
	for e in emails.values():
		items.append(
			{
				"type": "email",
				"name": e.name,
				"title": e.subject,
				"direction": e.sent_or_received,
				"from": e.sender_full_name or e.sender,
				"text": strip_html(e.content or "")[:280],
				"time": e.communication_date,
				"ref_doctype": e.reference_doctype,
				"ref_name": e.reference_name,
			}
		)

	# Calls: logs on their deals, or to / from one of their phone numbers.
	phones = {_phone_key(p.phone) for p in doc.phone_nos} | {
		_phone_key(doc.mobile_no),
		_phone_key(doc.phone),
	}
	phones.discard("")
	calls = {}
	if deal_names:
		for c in frappe.get_list(
			"CRM Call Log",
			filters={"reference_doctype": "CRM Deal", "reference_docname": ["in", deal_names]},
			fields=["*"],
			order_by="creation desc",
			limit=LIMIT,
		):
			calls[c.name] = c
	if phones:
		for c in frappe.get_list("CRM Call Log", fields=["*"], order_by="creation desc", limit=200):
			if _phone_key(c.get("from")) in phones or _phone_key(c.get("to")) in phones:
				calls[c.name] = c
	for c in calls.values():
		items.append(
			{
				"type": "call",
				"name": c.name,
				"direction": c.type,
				"status": c.status,
				"duration": c.duration,
				"time": c.get("start_time") or c.creation,
				"by": c.get("caller") or c.get("receiver") or c.owner,
			}
		)

	# Meetings: Frappe Events with this contact as a participant.
	event_names = [
		r.parent
		for r in frappe.get_all(
			"Event Participants",
			filters={"reference_doctype": "Contact", "reference_docname": contact},
			fields=["parent"],
		)
	]
	if event_names:
		for ev in frappe.get_list(
			"Event",
			filters={"name": ["in", event_names]},
			fields=["name", "subject", "starts_on", "ends_on", "description", "owner", "creation"],
			order_by="starts_on desc",
			limit=LIMIT,
		):
			items.append(
				{
					"type": "meeting",
					"name": ev.name,
					"title": ev.subject,
					"starts_on": ev.starts_on,
					"ends_on": ev.ends_on,
					"text": strip_html(ev.description or "")[:280],
					"time": ev.creation,
					"by": ev.owner,
				}
			)

	items.sort(key=lambda i: get_datetime(i["time"]) if i.get("time") else get_datetime("1900-01-01"), reverse=True)
	return items[:150]


@frappe.whitelist()
def schedule_meeting(contact: str, subject: str, starts_on: str, ends_on: str | None = None, description: str | None = None):
	"""Create a Frappe Event with this contact as a participant."""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	ev = frappe.get_doc(
		{
			"doctype": "Event",
			"subject": subject,
			"starts_on": starts_on,
			"ends_on": ends_on or None,
			"event_type": "Private",
			"event_category": "Meeting",
			"description": description,
			"event_participants": [{"reference_doctype": "Contact", "reference_docname": contact}],
		}
	)
	ev.insert()
	return ev.name
