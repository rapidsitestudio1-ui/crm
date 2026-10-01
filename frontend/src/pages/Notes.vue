<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Notes" />
    </template>
    <template #right-header>
      <Button
        class="crm-primary"
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="createNote"
      />
    </template>
  </LayoutHeader>

  <!-- Tabs + search: temporary page filters (never saved to the view). -->
  <div class="ct-bar">
    <div class="ct-tabs" role="tablist" :aria-label="__('Note views')">
      <button
        v-for="t in tabs"
        :key="t.key"
        type="button"
        role="tab"
        class="ct-tab"
        :aria-selected="tab === t.key"
        @click="tab = t.key"
      >
        {{ t.label }}
        <span v-if="counts[t.key] != null" class="ct-tab-count">{{ counts[t.key] }}</span>
      </button>
    </div>
    <label class="ct-search">
      <LucideSearch />
      <input
        ref="searchInput"
        v-model="search"
        type="search"
        :placeholder="__('Search notes')"
        :aria-label="__('Search notes')"
        @keydown.esc="search = ''"
      />
      <button
        v-if="search"
        type="button"
        class="ct-clear"
        :aria-label="__('Clear search')"
        @click="clearSearch"
      >
        <LucideX class="size-3.5" />
      </button>
      <kbd v-else class="max-sm:hidden">/</kbd>
    </label>
  </div>

  <ViewControls
    ref="viewControls"
    v-model="notes"
    v-model:loadMore="loadMore"
    v-model:updatedPageCount="updatedPageCount"
    doctype="FCRM Note"
    :filters="pageFilters"
    :options="{
      hideColumnsButton: true,
      defaultViewName: __('Notes View'),
    }"
  />

  <div class="nt-page flex-1 overflow-y-auto">
    <!-- Loading -->
    <div v-if="!notes.data" class="nt-grid">
      <div v-for="i in 8" :key="i" class="nt-skeleton" />
    </div>

    <!-- Notes -->
    <div v-else-if="notes.data.data?.length" class="nt-grid">
      <article
        v-for="note in notes.data.data"
        :key="note.name"
        class="nt-card"
        tabindex="0"
        :aria-label="note.title || __('Untitled note')"
        @click="editNote(note.name)"
        @keydown.enter.self="editNote(note.name)"
      >
        <div class="min-w-0 pr-8">
          <h3 class="nt-title truncate">{{ note.title || __('Untitled note') }}</h3>
          <router-link
            v-if="refRoute(note)"
            :to="refRoute(note)"
            class="nt-ref"
            @click.stop
          >
            <component :is="REF[note.reference_doctype].icon" />
            <span class="nt-ref-kind">{{ REF[note.reference_doctype].label }}</span>
            <span class="truncate">{{ refTitle(note) }}</span>
          </router-link>
        </div>

        <!-- content is passed through sanitizeHTML() (DOMPurify) before rendering, so v-html is safe here -->
        <!-- eslint-disable vue/no-v-html -->
        <div
          v-if="hasContent(note.content)"
          class="nt-body"
          v-html="sanitizeHTML(note.content)"
        />
        <!-- eslint-enable vue/no-v-html -->
        <div v-else class="nt-body nt-empty-body">{{ __('No content') }}</div>

        <div class="nt-foot">
          <span class="flex min-w-0 items-center gap-2">
            <KanbanAvatar
              :image="getUser(note.owner)?.user_image"
              :label="getUser(note.owner)?.full_name || note.owner"
              size="xs"
            />
            <span class="truncate">{{ getUser(note.owner)?.full_name || note.owner }}</span>
          </span>
          <Tooltip :text="formatDate(note.modified)">
            <span class="whitespace-nowrap" style="color: var(--kb-ink-3)">
              {{ __(timeAgo(note.modified)) }}
            </span>
          </Tooltip>
        </div>

        <div class="nt-menu" @click.stop>
          <Dropdown :options="noteActions(note)" placement="right">
            <button
              type="button"
              class="kb-icon-btn kb-reveal"
              :aria-label="__('Note actions')"
            >
              <LucideMoreHorizontal class="size-4" />
            </button>
          </Dropdown>
        </div>
      </article>
    </div>

    <!-- Empty states -->
    <div v-else class="ct-empty" role="status">
      <div class="ct-empty-icon">
        <component :is="empty.icon" class="size-5" />
      </div>
      <h2>{{ empty.title }}</h2>
      <p>{{ empty.text }}</p>
      <div class="mt-4 flex flex-wrap justify-center gap-2">
        <button
          v-for="a in empty.actions"
          :key="a.label"
          type="button"
          class="ct-btn"
          :class="{ 'is-primary': a.primary }"
          @click="a.onClick"
        >
          {{ a.label }}
        </button>
      </div>
    </div>
  </div>

  <ListFooter
    v-if="notes.data?.data?.length"
    v-model="notes.data.page_length_count"
    class="border-t px-3 py-2 sm:px-5"
    :options="{
      rowCount: notes.data.row_count,
      totalCount: notes.data.total_count,
    }"
    @loadMore="() => loadMore++"
  />
</template>

<script setup>
import '@/components/Kanban/kanban.css'
import '@/components/Contacts/contacts.css'
import '@/components/Notes/notes.css'
import LucideSearch from '~icons/lucide/search'
import LucideSearchX from '~icons/lucide/search-x'
import LucideFilterX from '~icons/lucide/filter-x'
import LucideX from '~icons/lucide/x'
import LucideMoreHorizontal from '~icons/lucide/more-horizontal'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucideUsers from '~icons/lucide/users'
import LucideHandshake from '~icons/lucide/handshake'
import LucideContact from '~icons/lucide/contact'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import KanbanAvatar from '@/components/Kanban/KanbanAvatar.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { timeAgo, formatDate, sanitizeHTML } from '@/utils'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { call, Dropdown, Tooltip, ListFooter, toast } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import {
  ref,
  reactive,
  computed,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import { useRouter } from 'vue-router'

const { getUser } = usersStore()
const { user: sessionUser } = sessionStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()
const router = useRouter()

const { showModal } = useDoctypeModal()

const notes = ref({})
const loadMore = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

watch(
  () => notes.value?.data?.page_length_count,
  (val, old_value) => {
    openNoteFromURL()
    if (!val || val === old_value) return
    updatedPageCount.value = val
  },
)

const noteCallbacks = {
  afterInsert: () => {
    notes.value.reload()
    loadCounts()
    updateOnboardingStep('create_first_note')
    capture('note_created')
  },
  afterUpdate: () => {
    notes.value.reload()
    capture('note_updated')
  },
}

function createNote() {
  showModal({
    doctype: 'FCRM Note',
    title: 'Note',
    callbacks: noteCallbacks,
  })
}

function editNote(noteName) {
  showModal({
    name: noteName,
    doctype: 'FCRM Note',
    title: 'Note',
    callbacks: noteCallbacks,
  })
}

async function deleteNote(name) {
  await call('frappe.client.delete', {
    doctype: 'FCRM Note',
    name,
  })
  notes.value.reload()
  loadCounts()
}

const openNoteFromURL = () => {
  const searchParams = new URLSearchParams(window.location.search)
  const noteName = searchParams.get('open')

  if (noteName && notes.value?.data?.data) {
    const foundNote = notes.value.data.data.find(
      (note) => note.name === noteName,
    )
    if (foundNote) {
      editNote(foundNote.name)
    }
    searchParams.delete('open')
    window.history.replaceState(null, '', window.location.pathname)
  }
}

// ---------------- Custom: tabs, search, linked records ----------------

const REF = {
  'CRM Lead': { label: __('Lead'), icon: LucideUsers, route: (n) => ({ name: 'Lead', params: { leadId: n } }) },
  'CRM Deal': { label: __('Deal'), icon: LucideHandshake, route: (n) => ({ name: 'Deal', params: { dealId: n } }) },
  Contact: { label: __('Contact'), icon: LucideContact, route: (n) => ({ name: 'Contact', params: { contactId: n } }) },
}

const TAB_FILTERS = {
  all: {},
  leads: { reference_doctype: 'CRM Lead' },
  deals: { reference_doctype: 'CRM Deal' },
  contacts: { reference_doctype: 'Contact' },
  mine: { owner: sessionUser },
}
const tabs = [
  { key: 'all', label: __('All notes') },
  { key: 'leads', label: __('Leads') },
  { key: 'deals', label: __('Deals') },
  { key: 'contacts', label: __('Contacts') },
  { key: 'mine', label: __('My notes') },
]
const tab = ref('all')

// Counts per tab (read-only get_count, user permissions apply).
const counts = reactive({})
async function loadCounts() {
  await Promise.all(
    Object.entries(TAB_FILTERS).map(async ([key, filters]) => {
      counts[key] = await call('frappe.client.get_count', {
        doctype: 'FCRM Note',
        filters,
      }).catch(() => null)
    }),
  )
}

// Search title OR content: resolve matching names first (get_list supports
// or_filters; the list endpoint only ANDs), then filter the view by name.
const search = ref('')
const searchQuery = ref('')
const searchNames = ref(null)
const searchInput = ref(null)
const applySearch = useDebounceFn(async (q) => {
  q = q.trim()
  searchQuery.value = q
  if (!q) return (searchNames.value = null)
  const rows = await call('frappe.client.get_list', {
    doctype: 'FCRM Note',
    fields: ['name'],
    or_filters: [
      ['title', 'like', `%${q}%`],
      ['content', 'like', `%${q}%`],
    ],
    limit_page_length: 500,
  }).catch(() => [])
  if (q === searchQuery.value) searchNames.value = rows.map((r) => r.name)
}, 250)
watch(search, (q) => applySearch(q))
function clearSearch() {
  search.value = ''
  searchQuery.value = ''
  searchNames.value = null
  searchInput.value?.focus()
}

const pageFilters = computed(() => {
  const f = { ...TAB_FILTERS[tab.value] }
  if (searchNames.value) {
    f.name = ['in', searchNames.value.length ? searchNames.value : ['__no_note__']]
  }
  return f
})
watch(
  pageFilters,
  async () => {
    await nextTick()
    for (let i = 0; i < 20 && notes.value?.loading; i++) {
      await new Promise((r) => setTimeout(r, 100))
    }
    viewControls.value?.reload()
  },
  { deep: true },
)

// Titles of the linked lead / deal / contact, for the card chip.
const refTitles = reactive({})
const REF_TITLE_FIELD = { 'CRM Lead': 'lead_name', 'CRM Deal': 'organization', Contact: 'full_name' }
watch(
  () => notes.value?.data?.data,
  async (rows) => {
    if (!rows?.length) return
    const byType = {}
    for (const n of rows) {
      if (REF_TITLE_FIELD[n.reference_doctype] && n.reference_docname) {
        ;(byType[n.reference_doctype] ||= new Set()).add(n.reference_docname)
      }
    }
    await Promise.all(
      Object.entries(byType).map(async ([doctype, names]) => {
        const field = REF_TITLE_FIELD[doctype]
        const res = await call('frappe.client.get_list', {
          doctype,
          fields: ['name', field],
          filters: { name: ['in', [...names]] },
          limit_page_length: names.size,
        }).catch(() => [])
        for (const r of res) refTitles[`${doctype}::${r.name}`] = r[field]
      }),
    )
  },
)

function refRoute(note) {
  const r = REF[note.reference_doctype]
  return r && note.reference_docname ? r.route(note.reference_docname) : null
}
function refTitle(note) {
  return refTitles[`${note.reference_doctype}::${note.reference_docname}`] || note.reference_docname
}

function hasContent(html) {
  return Boolean((html || '').replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').trim())
}

function noteActions(note) {
  const items = [
    { label: __('Edit'), icon: 'edit-2', onClick: () => editNote(note.name) },
  ]
  if (refRoute(note)) {
    items.push({
      label: __('Open {0}', [REF[note.reference_doctype].label.toLowerCase()]),
      icon: 'arrow-up-right',
      onClick: () => router.push(refRoute(note)),
    })
  }
  items.push(
    {
      label: __('Copy link'),
      icon: 'link',
      onClick: async () => {
        const url = `${window.location.origin}${window.location.pathname}?open=${encodeURIComponent(note.name)}`
        try {
          await navigator.clipboard.writeText(url)
          toast.success(__('Link copied'))
        } catch {
          toast.error(__('Could not copy'))
        }
      },
    },
    { label: __('Delete'), icon: 'trash-2', theme: 'red', onClick: () => deleteNote(note.name) },
  )
  return items
}

const TAB_EMPTY = {
  leads: __('No notes on leads yet.'),
  deals: __('No notes on deals yet.'),
  contacts: __('No notes on contacts yet.'),
  mine: __('You haven’t written any notes yet.'),
}

const empty = computed(() => {
  if (searchQuery.value) {
    return {
      icon: LucideSearchX,
      title: __('No notes match “{0}”', [searchQuery.value]),
      text: __('Search looks in note titles and text.'),
      actions: [{ label: __('Clear search'), onClick: clearSearch }],
    }
  }
  if (viewControls.value?.hasFilters) {
    return {
      icon: LucideFilterX,
      title: __('No notes match these filters'),
      text: __('Some notes are hidden by the filters on this view.'),
      actions: [{ label: __('Clear filters'), onClick: () => viewControls.value?.clearFilters() }],
    }
  }
  if (tab.value !== 'all') {
    return {
      icon: LucideStickyNote,
      title: __('Nothing here yet'),
      text: TAB_EMPTY[tab.value],
      actions: [
        { label: __('Show all notes'), onClick: () => (tab.value = 'all') },
        { label: __('New note'), primary: true, onClick: createNote },
      ],
    }
  }
  return {
    icon: LucideStickyNote,
    title: __('No notes yet'),
    text: __('Capture call summaries, meeting notes and ideas. Notes can be linked to a lead, deal or contact.'),
    actions: [{ label: __('New note'), primary: true, onClick: createNote }],
  }
})

// "/" focuses search; indigo accents like Leads / Deals / Contacts.
function onKeydown(e) {
  if (e.key !== '/' || e.metaKey || e.ctrlKey) return
  const t = e.target
  if (t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName)) return
  e.preventDefault()
  searchInput.value?.focus()
}
onMounted(() => {
  document.documentElement.dataset.surface = 'pipeline'
  window.addEventListener('keydown', onKeydown)
  loadCounts()
})
onBeforeUnmount(() => {
  delete document.documentElement.dataset.surface
  window.removeEventListener('keydown', onKeydown)
})
</script>
