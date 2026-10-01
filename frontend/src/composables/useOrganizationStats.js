import { call } from 'frappe-ui'
import { reactive, ref, watch } from 'vue'

/**
 * Related counts for organizations, from existing links only:
 *  - contacts: Contact.company_name = organization
 *  - open deals: CRM Deal.organization with an Open/Ongoing status
 * One grouped query per kind for the organizations on screen (never one
 * request per row). Read-only, through frappe.client.get_list, so the user's
 * permissions apply.
 *
 * Also loads, once, which organizations have a won deal (customers) or an
 * open deal (prospects), for the view tabs and badges.
 */
export function useOrganizationStats(getNames) {
  // Deal status types (Open / Ongoing / Won / Lost), fetched once.
  let statusTypes = null
  function loadStatusTypes() {
    statusTypes ||= call('frappe.client.get_list', {
      doctype: 'CRM Deal Status',
      fields: ['name', 'type'],
      limit_page_length: 0,
    }).catch(() => [])
    return statusTypes
  }
  const counts = reactive({}) // name -> { contacts, openDeals }
  const customers = ref(new Set())
  const prospects = ref(new Set())
  const relationsLoaded = ref(false)

  async function statusesOfType(types) {
    return (await loadStatusTypes()).filter((s) => types.includes(s.type)).map((s) => s.name)
  }

  async function grouped(doctype, field, filters) {
    const rows = await call('frappe.client.get_list', {
      doctype,
      fields: [field, 'count(name) as n'],
      filters,
      group_by: field,
      limit_page_length: 0,
    }).catch(() => [])
    return Object.fromEntries(rows.map((r) => [r[field], r.n]))
  }

  let request = 0
  watch(
    getNames,
    async (names) => {
      if (!names?.length) return
      const id = ++request
      const open = await statusesOfType(['Open', 'Ongoing'])
      const [contacts, deals] = await Promise.all([
        grouped('Contact', 'company_name', { company_name: ['in', names] }),
        open.length
          ? grouped('CRM Deal', 'organization', { organization: ['in', names], status: ['in', open] })
          : {},
      ])
      if (id !== request) return
      for (const n of names) {
        counts[n] = { contacts: contacts[n] || 0, openDeals: deals[n] || 0 }
      }
    },
    { immediate: true },
  )

  async function loadRelations() {
    const won = await statusesOfType(['Won'])
    const open = await statusesOfType(['Open', 'Ongoing'])
    const [w, o] = await Promise.all([
      won.length ? grouped('CRM Deal', 'organization', { status: ['in', won], organization: ['is', 'set'] }) : {},
      open.length ? grouped('CRM Deal', 'organization', { status: ['in', open], organization: ['is', 'set'] }) : {},
    ])
    customers.value = new Set(Object.keys(w))
    prospects.value = new Set(Object.keys(o))
    relationsLoaded.value = true
  }

  function relationship(name) {
    if (customers.value.has(name)) return { label: __('Customer'), tone: 'success' }
    if (prospects.value.has(name)) return { label: __('Prospect'), tone: 'accent' }
    return null
  }

  return { counts, customers, prospects, relationsLoaded, loadRelations, relationship }
}
