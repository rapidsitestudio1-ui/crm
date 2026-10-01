import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

export const viewsStore = defineStore('crm-views', (doctype) => {
  if (typeof doctype !== 'string') {
    doctype = null
  }

  let viewsByName = reactive({})
  let pinnedViews = ref([])
  let publicViews = ref([])
  let standardViews = ref({})
  // Keyed by route_name (e.g. 'Leads', 'Deals') so each doctype keeps its own default
  const defaultViews = reactive({})

  // Views
  const views = createResource({
    url: 'crm.api.views.get_views',
    params: { doctype: doctype || '' },
    cache: 'crm-views',
    initialData: [],
    auto: true,
    transform(views) {
      pinnedViews.value = []
      publicViews.value = []
      // Reset per-doctype defaults before repopulating
      Object.keys(defaultViews).forEach((k) => delete defaultViews[k])
      for (let view of views) {
        viewsByName[view.name] = view
        view.type = view.type || 'list'
        if (view.pinned) {
          pinnedViews.value?.push(view)
        }
        if (view.public) {
          publicViews.value?.push(view)
        }
        if (view.is_standard && view.dt) {
          // Custom: if a user ends up with duplicate standard views for the
          // same doctype + type, use the most recently saved one. Otherwise
          // the loaded view could be a stale copy while changes (e.g. clearing
          // filters) are saved to the other, and never appear to stick.
          const key = view.dt + ' ' + view.type
          const current = standardViews.value[key]
          if (
            !current ||
            current.name === view.name ||
            String(view.modified) >= String(current.modified)
          ) {
            standardViews.value[key] = view
          }
        }
        if (view.is_default && view.route_name) {
          defaultViews[view.route_name] = view
        }
      }
      return views
    },
  })

  const homeRoutePriority = [
    'Leads',
    'Deals',
    'Contacts',
    'Organizations',
    'Notes',
    'Tasks',
    'Call Logs',
  ]

  function getDefaultView(routeName = null) {
    if (routeName) return defaultViews[routeName] || null
    const candidates = [
      ...homeRoutePriority,
      ...Object.keys(defaultViews).sort(),
    ]
    const route = candidates.find((r) => defaultViews[r])
    return route ? defaultViews[route] : null
  }

  function getView(view, type, doctype = null) {
    type = type || 'list'
    if (!view && doctype) {
      return standardViews.value[doctype + ' ' + type] || null
    }
    return viewsByName[view]
  }

  function getPinnedViews() {
    if (!pinnedViews.value?.length) return []
    return pinnedViews.value
  }

  function getPublicViews() {
    if (!publicViews.value?.length) return []
    return publicViews.value
  }

  async function reload() {
    await views.reload()
  }

  return {
    views,
    defaultViews,
    standardViews,
    getDefaultView,
    getPinnedViews,
    getPublicViews,
    reload,
    getView,
  }
})
