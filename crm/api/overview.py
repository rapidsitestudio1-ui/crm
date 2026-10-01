"""Data for the overview dashboard (Figma "CRM Dashboard" frame 593:1449).

One call returns every card on the page: KPI cards, sales trend, pipeline
forecast, funnel conversion, tasks due today, recent activity and recent leads.
"""

import frappe
from frappe.utils import add_days, add_months, date_diff, get_first_day, getdate, nowdate

from crm.api.dashboard import get_base_currency_symbol
from crm.utils import sales_user_only

OPEN_TYPES = ("Open", "Ongoing")

# Weighted (probability-adjusted) value of a deal in base currency.
WEIGHTED_VALUE = (
	"COALESCE(NULLIF(d.expected_deal_value, 0), d.deal_value, 0)"
	" * IFNULL(d.probability, 0) / 100 * IFNULL(d.exchange_rate, 1)"
)


@frappe.whitelist()
@sales_user_only
def get_overview(
	from_date: str | None = None,
	to_date: str | None = None,
	user: str | None = None,
	forecast_months: int = 4,
):
	to_date = getdate(to_date or nowdate())
	from_date = getdate(from_date or add_days(to_date, -29))

	roles = frappe.get_roles(frappe.session.user)
	if "Sales User" in roles and not ({"Sales Manager", "System Manager"} & set(roles)):
		user = frappe.session.user

	days = date_diff(to_date, from_date) + 1
	prev_from = add_days(from_date, -days)
	prev_to = add_days(from_date, -1)

	return {
		"currency": get_base_currency_symbol(),
		"days": days,
		"kpis": _kpis(from_date, to_date, prev_from, prev_to, user),
		"trend": _trend(from_date, to_date, user),
		"forecast": _forecast(int(forecast_months or 4), user),
		"funnel": _funnel(from_date, to_date, user),
		"tasks": _tasks_today(user),
		"activity": _activity(user),
		"leads": _recent_leads(user),
	}


def _owner(alias: str, field: str, user: str | None):
	return f" AND {alias}.{field} = %(user)s" if user else ""


def _daily(sql: str, params: dict) -> dict:
	return {str(r[0]): float(r[1] or 0) for r in frappe.db.sql(sql, params)}


def _series(daily: dict, from_date, to_date) -> list:
	return [daily.get(str(add_days(from_date, i)), 0) for i in range(date_diff(to_date, from_date) + 1)]


def _kpi(current: float, previous: float, series: list) -> dict:
	delta = (current - previous) / previous * 100 if previous else (100 if current else 0)
	return {"value": current, "delta": round(delta), "series": series}


def _kpis(from_date, to_date, prev_from, prev_to, user):
	p = {"from": from_date, "to": to_date, "user": user}
	pp = {"from": prev_from, "to": prev_to, "user": user}

	def total(sql, params):
		return float(frappe.db.sql(sql, params)[0][0] or 0)

	leads_daily = f"""
		SELECT DATE(l.creation), COUNT(*) FROM `tabCRM Lead` l
		WHERE DATE(l.creation) BETWEEN %(from)s AND %(to)s {_owner("l", "lead_owner", user)}
		GROUP BY DATE(l.creation)"""
	active_daily = f"""
		SELECT DATE(d.creation), COUNT(*) FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON s.name = d.status
		WHERE s.type IN {OPEN_TYPES} AND DATE(d.creation) BETWEEN %(from)s AND %(to)s
		{_owner("d", "deal_owner", user)} GROUP BY DATE(d.creation)"""
	won_daily = f"""
		SELECT COALESCE(d.closed_date, DATE(d.modified)) dt, COUNT(*) FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON s.name = d.status
		WHERE s.type = 'Won' AND COALESCE(d.closed_date, DATE(d.modified)) BETWEEN %(from)s AND %(to)s
		{_owner("d", "deal_owner", user)} GROUP BY dt"""
	revenue_daily = f"""
		SELECT DATE(d.creation), SUM({WEIGHTED_VALUE}) FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON s.name = d.status
		WHERE s.type IN {OPEN_TYPES} AND DATE(d.creation) BETWEEN %(from)s AND %(to)s
		{_owner("d", "deal_owner", user)} GROUP BY DATE(d.creation)"""

	out = {}
	for key, sql in (
		("total_leads", leads_daily),
		("active_deals", active_daily),
		("won_deals", won_daily),
		("forecasted_revenue", revenue_daily),
	):
		daily = _daily(sql, p)
		previous = sum(_daily(sql, pp).values())
		out[key] = _kpi(sum(daily.values()), previous, _series(daily, from_date, to_date))
	return out


def _trend(from_date, to_date, user):
	p = {"from": from_date, "to": to_date, "user": user}
	leads = _daily(
		f"""SELECT DATE(l.creation), COUNT(*) FROM `tabCRM Lead` l
		WHERE DATE(l.creation) BETWEEN %(from)s AND %(to)s {_owner("l", "lead_owner", user)}
		GROUP BY DATE(l.creation)""",
		p,
	)
	deals = _daily(
		f"""SELECT DATE(d.creation), COUNT(*) FROM `tabCRM Deal` d
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s {_owner("d", "deal_owner", user)}
		GROUP BY DATE(d.creation)""",
		p,
	)
	won = _daily(
		f"""SELECT COALESCE(d.closed_date, DATE(d.modified)) dt, COUNT(*) FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON s.name = d.status
		WHERE s.type = 'Won' AND COALESCE(d.closed_date, DATE(d.modified)) BETWEEN %(from)s AND %(to)s
		{_owner("d", "deal_owner", user)} GROUP BY dt""",
		p,
	)
	return [
		{
			"date": str(add_days(from_date, i)),
			"leads": leads.get(str(add_days(from_date, i)), 0),
			"deals": deals.get(str(add_days(from_date, i)), 0),
			"won_deals": won.get(str(add_days(from_date, i)), 0),
		}
		for i in range(date_diff(to_date, from_date) + 1)
	]


def _forecast(months: int, user):
	start = get_first_day(nowdate())
	end = add_days(add_months(start, months), -1)
	rows = frappe.db.sql(
		f"""SELECT DATE_FORMAT(d.expected_closure_date, '%%Y-%%m') m, SUM({WEIGHTED_VALUE})
		FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON s.name = d.status
		WHERE s.type IN {OPEN_TYPES} AND d.expected_closure_date BETWEEN %(from)s AND %(to)s
		{_owner("d", "deal_owner", user)} GROUP BY m""",
		{"from": start, "to": end, "user": user},
	)
	by_month = {r[0]: float(r[1] or 0) for r in rows}
	return [
		{"month": str(add_months(start, i))[:7], "value": by_month.get(str(add_months(start, i))[:7], 0)}
		for i in range(months)
	]


def _funnel(from_date, to_date, user):
	"""Cohort of leads and deals created in the period, by how far they got."""
	p = {"from": from_date, "to": to_date, "user": user}
	lead_where = f"DATE(l.creation) BETWEEN %(from)s AND %(to)s {_owner('l', 'lead_owner', user)}"
	deal_where = f"DATE(d.creation) BETWEEN %(from)s AND %(to)s {_owner('d', 'deal_owner', user)}"

	leads, contacted, qualified = frappe.db.sql(
		f"""SELECT COUNT(*),
			SUM(l.status != 'New' OR l.converted = 1),
			SUM(s.type = 'Won' OR l.converted = 1)
		FROM `tabCRM Lead` l LEFT JOIN `tabCRM Lead Status` s ON s.name = l.status
		WHERE {lead_where}""",
		p,
	)[0]

	proposal_pos = frappe.db.get_value("CRM Deal Status", "Proposal/Quotation", "position") or 3
	proposal, won = frappe.db.sql(
		f"""SELECT
			SUM(s.type != 'Lost' AND (s.position >= %(pos)s OR s.type = 'Won')),
			SUM(s.type = 'Won')
		FROM `tabCRM Deal` d JOIN `tabCRM Deal Status` s ON s.name = d.status
		WHERE {deal_where}""",
		{**p, "pos": proposal_pos},
	)[0]

	return [
		{"stage": "Leads", "count": int(leads or 0)},
		{"stage": "Contacted", "count": int(contacted or 0)},
		{"stage": "Qualified", "count": int(qualified or 0)},
		{"stage": "Proposal", "count": int(proposal or 0)},
		{"stage": "Won", "count": int(won or 0)},
	]


def _reference_labels(refs: list[tuple[str, str]]) -> dict:
	"""Map (doctype, name) -> {title, organization, source, status} for leads and deals."""
	out = {}
	leads = [n for dt, n in refs if dt == "CRM Lead" and n]
	deals = [n for dt, n in refs if dt == "CRM Deal" and n]
	if leads:
		for r in frappe.get_all(
			"CRM Lead",
			filters={"name": ["in", leads]},
			fields=["name", "lead_name", "organization", "source", "status"],
		):
			out[("CRM Lead", r.name)] = {
				"title": r.lead_name or r.name,
				"organization": r.organization,
				"source": r.source,
				"status": r.status,
			}
	if deals:
		for r in frappe.get_all(
			"CRM Deal",
			filters={"name": ["in", deals]},
			fields=["name", "organization", "lead_name", "source", "status"],
		):
			out[("CRM Deal", r.name)] = {
				"title": r.organization or r.lead_name or r.name,
				"organization": r.organization,
				"source": r.source,
				"status": r.status,
			}
	return out


def _tasks_today(user):
	filters = {"status": ["not in", ["Done", "Canceled"]], "due_date": ["between", [nowdate(), nowdate()]]}
	if user:
		filters["assigned_to"] = user
	tasks = frappe.get_all(
		"CRM Task",
		filters=filters,
		fields=["name", "title", "due_date", "status", "reference_doctype", "reference_docname"],
		order_by="due_date asc",
		limit=4,
	)
	labels = _reference_labels([(t.reference_doctype, t.reference_docname) for t in tasks])
	for t in tasks:
		ref = labels.get((t.reference_doctype, t.reference_docname))
		t["subtitle"] = (
			" • ".join([ref["organization"] or "No company", ref["source"] or ref["status"] or ""]).strip(" •")
			if ref
			else ""
		)
	return tasks


def _activity(user):
	events = []
	limit = 5

	lead_cond = "WHERE l.lead_owner = %(user)s" if user else ""
	for r in frappe.db.sql(
		f"""SELECT l.name, l.lead_name, l.organization, l.creation FROM `tabCRM Lead` l
		{lead_cond} ORDER BY l.creation DESC LIMIT {limit}""",
		{"user": user},
		as_dict=True,
	):
		sub = f"{r.lead_name} ({r.organization})" if r.organization else (r.lead_name or r.name)
		events.append(
			{
				"type": "lead",
				"title": "New lead received",
				"subtitle": sub,
				"time": r.creation,
				"doctype": "CRM Lead",
				"name": r.name,
			}
		)

	deal_cond = "AND d.deal_owner = %(user)s" if user else ""
	for r in frappe.db.sql(
		f"""SELECT c.parent, c.to, COALESCE(c.to_date, c.creation) t, d.organization
		FROM `tabCRM Status Change Log` c JOIN `tabCRM Deal` d ON d.name = c.parent
		WHERE c.parenttype = 'CRM Deal' AND IFNULL(c.from, '') != '' AND IFNULL(c.to, '') != ''
		{deal_cond}
		ORDER BY t DESC LIMIT {limit}""",
		{"user": user},
		as_dict=True,
	):
		events.append(
			{
				"type": "deal",
				"title": f"Deal moved to {r.to}",
				"subtitle": r.organization or r.parent,
				"time": r.t,
				"doctype": "CRM Deal",
				"name": r.parent,
			}
		)

	owner_cond = "AND owner = %(user)s" if user else ""
	notes = frappe.db.sql(
		f"""SELECT reference_doctype, reference_docname, creation FROM `tabFCRM Note`
		WHERE reference_doctype IN ('CRM Lead', 'CRM Deal') {owner_cond}
		ORDER BY creation DESC LIMIT {limit}""",
		{"user": user},
		as_dict=True,
	)
	emails = frappe.db.sql(
		f"""SELECT reference_doctype, reference_name, sent_or_received, read_by_recipient_on,
			COALESCE(read_by_recipient_on, communication_date, creation) t
		FROM `tabCommunication`
		WHERE communication_medium = 'Email' AND reference_doctype IN ('CRM Lead', 'CRM Deal')
		{owner_cond} ORDER BY t DESC LIMIT {limit}""",
		{"user": user},
		as_dict=True,
	)
	whatsapp = []
	if frappe.db.exists("DocType", "WhatsApp Message"):
		whatsapp = frappe.db.sql(
			f"""SELECT reference_doctype, reference_name, creation FROM `tabWhatsApp Message`
			WHERE type = 'Incoming' AND reference_doctype IN ('CRM Lead', 'CRM Deal')
			ORDER BY creation DESC LIMIT {limit}""",
			as_dict=True,
		)

	labels = _reference_labels(
		[(n.reference_doctype, n.reference_docname) for n in notes]
		+ [(e.reference_doctype, e.reference_name) for e in emails]
		+ [(w.reference_doctype, w.reference_name) for w in whatsapp]
	)

	def title_of(dt, name):
		return (labels.get((dt, name)) or {}).get("title") or name

	for n in notes:
		events.append(
			{
				"type": "note",
				"title": "Note added",
				"subtitle": title_of(n.reference_doctype, n.reference_docname),
				"time": n.creation,
				"doctype": n.reference_doctype,
				"name": n.reference_docname,
			}
		)
	for e in emails:
		if e.read_by_recipient_on:
			title = "Email opened"
		else:
			title = "Email received" if e.sent_or_received == "Received" else "Email sent"
		events.append(
			{
				"type": "email",
				"title": title,
				"subtitle": title_of(e.reference_doctype, e.reference_name),
				"time": e.t,
				"doctype": e.reference_doctype,
				"name": e.reference_name,
			}
		)
	for w in whatsapp:
		events.append(
			{
				"type": "whatsapp",
				"title": "New message in WhatsApp",
				"subtitle": title_of(w.reference_doctype, w.reference_name),
				"time": w.creation,
				"doctype": w.reference_doctype,
				"name": w.reference_name,
			}
		)

	events.sort(key=lambda e: e["time"], reverse=True)
	return events[:limit]


def _recent_leads(user):
	filters = {"converted": 0}
	if user:
		filters["lead_owner"] = user
	return frappe.get_all(
		"CRM Lead",
		filters=filters,
		fields=["name", "lead_name", "organization", "source", "status", "image", "modified"],
		order_by="modified desc",
		limit=5,
	)
