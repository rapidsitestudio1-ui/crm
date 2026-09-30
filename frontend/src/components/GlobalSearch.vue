<template>
  <!-- Sidebar trigger (Figma "Search Input") -->
  <Tooltip v-if="isCollapsed" :text="__('Search') + ` (${shortcutLabel}K)`" placement="right">
    <button
      class="mx-auto flex size-7 items-center justify-center rounded text-ink-gray-7 hover:bg-surface-gray-2"
      :aria-label="__('Search')"
      @click="open = true"
    >
      <span class="lucide-search size-4" aria-hidden="true" />
    </button>
  </Tooltip>
  <button
    v-else
    class="flex h-8 w-full items-center gap-2 rounded bg-surface-gray-2 px-2.5 text-left text-sm text-ink-gray-4 transition-colors hover:bg-surface-gray-3"
    @click="open = true"
  >
    <span class="lucide-search size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
    <span class="flex-1 truncate">{{ __('Search') }}</span>
    <span class="flex gap-0.5">
      <kbd
        v-for="key in [shortcutLabel, 'K']"
        :key="key"
        class="flex h-[18px] min-w-[18px] items-center justify-center rounded-sm border border-outline-gray-1 bg-surface-base px-1 font-sans text-xs text-ink-gray-5"
        >{{ key }}</kbd
      >
    </span>
  </button>

  <Dialog v-model:open="open" :size="'xl'">
    <template #body>
      <div class="flex flex-col" @keydown="onKeydown">
        <div class="flex items-center gap-2 border-b border-outline-gray-1 px-4 py-3">
          <span class="lucide-search size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          <input
            ref="inputRef"
            v-model="query"
            type="text"
            class="w-full border-none bg-transparent p-0 text-base text-ink-gray-9 placeholder-ink-gray-4 focus:ring-0"
            :placeholder="__('Search leads, deals, contacts and organizations')"
          />
          <LoadingIndicator v-if="loading" class="size-4 text-ink-gray-5" />
        </div>
        <div class="max-h-[60vh] overflow-y-auto p-2">
          <div
            v-if="!query.trim()"
            class="px-2 py-6 text-center text-sm text-ink-gray-5"
          >
            {{ __('Type to search across your CRM') }}
          </div>
          <div
            v-else-if="!loading && !flatResults.length"
            class="px-2 py-6 text-center text-sm text-ink-gray-5"
          >
            {{ __('No results for "{0}"', [query.trim()]) }}
          </div>
          <template v-for="group in groups" :key="group.doctype">
            <div
              v-if="group.items.length"
              class="px-2 pb-1 pt-2 text-xs-medium uppercase tracking-wide text-ink-gray-4"
            >
              {{ __(group.label) }}
            </div>
            <button
              v-for="item in group.items"
              :key="group.doctype + item.value"
              class="flex w-full items-center gap-3 rounded px-2 py-2 text-left"
              :class="item.index === active ? 'bg-surface-gray-2' : 'hover:bg-surface-gray-1'"
              @mouseenter="active = item.index"
              @click="go(item)"
            >
              <component :is="group.icon" class="size-4 shrink-0 text-ink-gray-6" />
              <span class="min-w-0 flex-1">
                <span class="block truncate text-base text-ink-gray-9">{{ item.label }}</span>
                <span
                  v-if="item.description"
                  class="block truncate text-sm text-ink-gray-5"
                  >{{ item.description }}</span
                >
              </span>
            </button>
          </template>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import { call, Dialog, LoadingIndicator, Tooltip } from 'frappe-ui'
import { watchDebounced } from '@vueuse/core'
import { computed, markRaw, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

const router = useRouter()

const SOURCES = [
  { doctype: 'CRM Lead', label: 'Leads', icon: markRaw(LeadsIcon), route: 'Lead', param: 'leadId' },
  { doctype: 'CRM Deal', label: 'Deals', icon: markRaw(DealsIcon), route: 'Deal', param: 'dealId' },
  { doctype: 'Contact', label: 'Contacts', icon: markRaw(ContactsIcon), route: 'Contact', param: 'contactId' },
  { doctype: 'CRM Organization', label: 'Organizations', icon: markRaw(OrganizationsIcon), route: 'Organization', param: 'organizationId' },
]

const open = ref(false)
const query = ref('')
const loading = ref(false)
const active = ref(0)
const inputRef = ref(null)
const results = ref({})

const shortcutLabel = /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl'

const groups = computed(() => {
  let index = 0
  return SOURCES.map((source) => ({
    ...source,
    items: (results.value[source.doctype] || []).map((r) => ({
      ...r,
      source,
      index: index++,
    })),
  }))
})
const flatResults = computed(() => groups.value.flatMap((g) => g.items))

function stripHtml(html) {
  return (html || '').replace(/<[^>]*>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim()
}

let requestId = 0
async function search(txt) {
  const id = ++requestId
  if (!txt) {
    results.value = {}
    loading.value = false
    return
  }
  loading.value = true
  const settled = await Promise.allSettled(
    SOURCES.map((s) =>
      call('frappe.desk.search.search_link', { doctype: s.doctype, txt, page_length: 5 }),
    ),
  )
  if (id !== requestId) return // a newer query is in flight
  const next = {}
  settled.forEach((r, i) => {
    // A doctype the user can't read rejects; just leave its group empty.
    next[SOURCES[i].doctype] =
      r.status === 'fulfilled'
        ? (r.value || []).map((o) => ({
            value: o.value,
            label: o.label || o.value,
            description: stripHtml(o.description),
          }))
        : []
  })
  results.value = next
  active.value = 0
  loading.value = false
}

watchDebounced(query, (q) => search(q.trim()), { debounce: 200 })

watch(open, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    inputRef.value?.focus()
  } else {
    query.value = ''
    results.value = {}
  }
})

function go(item) {
  open.value = false
  router.push({ name: item.source.route, params: { [item.source.param]: item.value } })
}

function onKeydown(e) {
  const count = flatResults.value.length
  if (e.key === 'ArrowDown' && count) {
    e.preventDefault()
    active.value = (active.value + 1) % count
  } else if (e.key === 'ArrowUp' && count) {
    e.preventDefault()
    active.value = (active.value - 1 + count) % count
  } else if (e.key === 'Enter' && count) {
    e.preventDefault()
    go(flatResults.value[active.value])
  }
}

// Cmd/Ctrl+K opens search, except inside rich-text editors where Mod-K
// inserts a link.
function onGlobalKeydown(e) {
  if (!(e.metaKey || e.ctrlKey) || e.key.toLowerCase() !== 'k') return
  if (e.target?.closest?.('.ProseMirror, [contenteditable="true"]')) return
  e.preventDefault()
  open.value = true
}
onMounted(() => window.addEventListener('keydown', onGlobalKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onGlobalKeydown))
</script>
