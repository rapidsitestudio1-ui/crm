import { call } from 'frappe-ui'
import { reactive, watch } from 'vue'

/**
 * Card-only data the board query doesn't return (e.g. a deal's value and close
 * date). Read-only: one frappe.client.get_list per board load for the cards on
 * screen, respecting the user's permissions. Nothing is written.
 *
 * @param {string} doctype
 * @param {() => string[] | null} getNames  card names; re-read whenever the
 *   getter's result changes identity (i.e. every board (re)load)
 * @param {string[]} fields  extra fields to read
 * @returns {Record<string, object>} reactive map: name -> { field: value }
 */
export function useKanbanExtras(doctype, getNames, fields) {
  const extras = reactive({})
  let request = 0

  watch(
    getNames,
    async (names) => {
      if (!names?.length) return
      const id = ++request
      try {
        const rows = await call('frappe.client.get_list', {
          doctype,
          filters: { name: ['in', names] },
          fields: ['name', ...fields],
          limit_page_length: names.length,
        })
        if (id !== request) return
        for (const row of rows || []) extras[row.name] = row
      } catch {
        // Cards still render from the board data; extras are optional.
      }
    },
    { immediate: true },
  )

  return extras
}
