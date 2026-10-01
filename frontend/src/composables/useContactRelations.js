import { call, dayjs, dayjsLocal } from 'frappe-ui'
import { reactive, ref } from 'vue'
import { statusesStore } from '@/stores/statuses'

/**
 * Contact <-> deal relationships, from existing data only:
 *  - `CRM Contacts` rows on CRM Deal (the contacts listed on a deal)
 *  - each deal's status type (Open / Ongoing / Won / Lost)
 *  - open CRM Tasks on those deals that are past their due date
 *
 * Read-only, through frappe.client.get_list, so the user's permissions apply.
 * Used for the contact "Relationship" badge and the Customers / Prospects /
 * Needs follow-up view tabs, which therefore always agree.
 */
export function useContactRelations() {
  const { getDealStatus } = statusesStore()

  // contact name -> { won, open, lost, followUp, deals: [dealName] }
  const byContact = reactive({})
  const loaded = ref(false)

  async function load() {
    const links = await call('frappe.client.get_list', {
      doctype: 'CRM Contacts',
      parent: 'CRM Deal',
      fields: ['contact', 'parent'],
      filters: { parenttype: 'CRM Deal' },
      limit_page_length: 0,
    }).catch(() => [])

    const dealNames = [...new Set(links.map((l) => l.parent))]
    let deals = []
    let overdue = []
    if (dealNames.length) {
      ;[deals, overdue] = await Promise.all([
        call('frappe.client.get_list', {
          doctype: 'CRM Deal',
          fields: ['name', 'status'],
          filters: { name: ['in', dealNames] },
          limit_page_length: 0,
        }).catch(() => []),
        call('frappe.client.get_list', {
          doctype: 'CRM Task',
          fields: ['reference_docname', 'due_date'],
          filters: {
            reference_doctype: 'CRM Deal',
            reference_docname: ['in', dealNames],
            status: ['not in', ['Done', 'Canceled']],
            due_date: ['is', 'set'],
          },
          limit_page_length: 0,
        }).catch(() => []),
      ])
    }

    const typeOf = Object.fromEntries(
      deals.map((d) => [d.name, getDealStatus(d.status)?.type]),
    )
    // Due dates are in the server's timezone; compare in the user's.
    const now = dayjs()
    const overdueDeals = new Set(
      overdue
        .filter((t) => dayjsLocal(t.due_date).isBefore(now))
        .map((t) => t.reference_docname),
    )

    Object.keys(byContact).forEach((k) => delete byContact[k])
    for (const { contact, parent } of links) {
      const type = typeOf[parent]
      if (!type) continue // deal not readable by this user
      const rel = (byContact[contact] ||= {
        won: false,
        open: false,
        lost: false,
        followUp: false,
        deals: [],
      })
      rel.deals.push(parent)
      if (type === 'Won') rel.won = true
      else if (type === 'Lost') rel.lost = true
      else {
        rel.open = true
        if (overdueDeals.has(parent)) rel.followUp = true
      }
    }
    loaded.value = true
  }

  /** Badge for a contact: Customer > Prospect > Lost, or null. */
  function relationship(contact) {
    const r = byContact[contact]
    if (!r) return null
    if (r.won) return { label: __('Customer'), tone: 'success' }
    if (r.open) return { label: __('Prospect'), tone: 'accent' }
    if (r.lost) return { label: __('Lost'), tone: 'neutral' }
    return null
  }

  /** Contact names for a view tab. */
  function namesFor(tab) {
    const test = {
      customers: (r) => r.won,
      prospects: (r) => r.open,
      followup: (r) => r.followUp,
    }[tab]
    if (!test) return null
    return Object.entries(byContact)
      .filter(([, r]) => test(r))
      .map(([name]) => name)
  }

  return { byContact, loaded, load, relationship, namesFor }
}
