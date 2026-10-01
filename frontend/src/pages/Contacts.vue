<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Contacts" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="contactsListView?.customListActions"
        :actions="contactsListView.customListActions"
      />
      <Button
        class="crm-primary"
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showContactModal = true"
      />
    </template>
  </LayoutHeader>

  <!-- View tabs + search. Both are temporary filters for this page: sent as
       default_filters, never written into the saved view. -->
  <div class="ct-bar">
    <div class="ct-tabs" role="tablist" :aria-label="__('Contact views')">
      <button
        v-for="t in tabs"
        :key="t.key"
        type="button"
        role="tab"
        class="ct-tab"
        :aria-selected="tab === t.key"
        :disabled="t.key !== 'all' && !relations.loaded.value"
        :title="t.hint"
        @click="tab = t.key"
      >
        {{ t.label }}
        <span v-if="t.count != null" class="ct-tab-count">{{ t.count }}</span>
      </button>
    </div>
    <label class="ct-search">
      <LucideSearch />
      <input
        ref="searchInput"
        v-model="search"
        type="search"
        :placeholder="__('Search name, email or phone')"
        :aria-label="__('Search contacts')"
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
    v-model="contacts"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Contact"
    :filters="pageFilters"
  />
  <ContactsListView
    v-if="contacts.data && rows.length"
    ref="contactsListView"
    v-model="contacts.data.page_length_count"
    v-model:list="contacts"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: contacts.data.row_count,
      totalCount: contacts.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
    @preview="(name) => (previewName = name)"
  />

  <!-- Empty states: say why the list is empty and offer the way out. -->
  <div
    v-else-if="contacts.data && !rows.length"
    class="flex-1 overflow-y-auto bg-[var(--kb-card)]"
  >
    <div class="ct-empty" role="status">
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

  <ContactPreview
    v-model="previewName"
    :relationship="previewName ? relations.relationship(previewName) : null"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="{}"
  />
</template>

<script setup>
import '@/components/Kanban/kanban.css'
import '@/components/Contacts/contacts.css'
import LucideSearch from '~icons/lucide/search'
import LucideX from '~icons/lucide/x'
import LucideSearchX from '~icons/lucide/search-x'
import LucideFilterX from '~icons/lucide/filter-x'
import LucideUsers from '~icons/lucide/users'
import LucideBadgeCheck from '~icons/lucide/badge-check'
import LucideTarget from '~icons/lucide/target'
import LucideCalendarCheck from '~icons/lucide/calendar-check'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import ContactPreview from '@/components/Contacts/ContactPreview.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { organizationsStore } from '@/stores/organizations.js'
import { useContactRelations } from '@/composables/useContactRelations'
import { useKanbanExtras } from '@/composables/useKanbanExtras'
import { formatDate } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useDebounceFn } from '@vueuse/core'
import {
  ref,
  computed,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Contact')
const { getOrganization } = organizationsStore()

const showContactModal = ref(false)

const contactsListView = ref(null)

// contacts data is loaded in the ViewControls component
const contacts = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// ---- Relationship data, view tabs and search (custom) ----

const relations = useContactRelations()
const tab = ref('all')
const search = ref('')
const searchQuery = ref('')
const searchInput = ref(null)
const previewName = ref(null)

const tabs = computed(() => {
  const count = (key) =>
    relations.loaded.value ? relations.namesFor(key).length : null
  return [
    { key: 'all', label: __('All contacts'), count: null },
    {
      key: 'customers',
      label: __('Customers'),
      count: count('customers'),
      hint: __('Contacts on at least one won deal'),
    },
    {
      key: 'prospects',
      label: __('Prospects'),
      count: count('prospects'),
      hint: __('Contacts on an open deal'),
    },
    {
      key: 'followup',
      label: __('Needs follow-up'),
      count: count('followup'),
      hint: __('Contacts on an open deal with an overdue task'),
    },
  ]
})

// Search picks the field from what's typed: email, phone number or name.
function searchFilter(q) {
  if (!q) return {}
  if (q.includes('@')) return { email_id: ['like', `%${q}%`] }
  if (/^[+\d][\d\s().-]*$/.test(q)) {
    return { mobile_no: ['like', `%${q.replace(/[\s().-]+/g, '%')}%`] }
  }
  return { full_name: ['like', `%${q}%`] }
}

const pageFilters = computed(() => {
  const f = { ...searchFilter(searchQuery.value) }
  const names = relations.namesFor(tab.value)
  if (names) f.name = ['in', names.length ? names : ['__no_contact__']]
  return f
})

const applySearch = useDebounceFn((q) => (searchQuery.value = q.trim()), 250)
watch(search, (q) => applySearch(q))

function clearSearch() {
  search.value = ''
  searchQuery.value = ''
  searchInput.value?.focus()
}

// Re-query when the page filters change (ViewControls skips a reload while a
// request is in flight, so wait for it).
watch(
  pageFilters,
  async () => {
    await nextTick()
    for (let i = 0; i < 20 && contacts.value?.loading; i++) {
      await new Promise((r) => setTimeout(r, 100))
    }
    viewControls.value?.reload()
  },
  { deep: true },
)

// "/" focuses search (when not typing elsewhere).
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
  relations.load()
})
onBeforeUnmount(() => {
  delete document.documentElement.dataset.surface
  window.removeEventListener('keydown', onKeydown)
})

// Fields the table shows that a saved column layout may not fetch.
const extras = useKanbanExtras(
  'Contact',
  () =>
    contacts.value?.data?.data?.length
      ? contacts.value.data.data.map((c) => c.name)
      : null,
  ['owner', 'full_name', 'email_id', 'mobile_no', 'image'],
)

// ---- Rows ----

const rows = computed(() => {
  if (
    !contacts.value?.data?.data ||
    !['list', 'group_by'].includes(contacts.value.data.view_type)
  )
    return []
  return contacts.value?.data.data.map((contact) => {
    let _rows = {}
    const extra = extras[contact.name] || {}
    contacts.value?.data.rows.forEach((row) => {
      _rows[row] = contact[row]

      let fieldType = contacts.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(contact[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, contact)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, contact)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, contact)
      }

      if (row == 'full_name') {
        _rows[row] = {
          label: contact.full_name,
          image_label: contact.full_name,
          image: contact.image || extra.image,
        }
      } else if (row == 'company_name') {
        _rows[row] = {
          label: contact.company_name,
          logo: getOrganization(contact.company_name)?.organization_logo,
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(contact[row])
      }
    })
    _rows.name = contact.name
    // The Contact column is always shown (see columns), even when the saved
    // layout doesn't fetch full_name.
    if (!_rows.full_name?.label) {
      _rows.full_name = {
        label: contact.full_name || extra.full_name || contact.name,
        image_label: contact.full_name || extra.full_name || contact.name,
        image: contact.image || extra.image,
      }
    }
    _rows.__email = contact.email_id || extra.email_id || ''
    _rows.__phone = contact.mobile_no || extra.mobile_no || ''
    _rows.__relationship = relations.relationship(contact.name)
    _rows.__owner = contact.owner || extra.owner || ''
    return _rows
  })
})

// ---- Columns ----
// Display-only: the saved column layout is kept as is (and stays editable in
// Columns). The Contact column always comes first, with the email under the
// name (so a separate Email column is folded into it); Relationship and Owner
// are added.
const LABELS = {
  full_name: __('Contact'),
  mobile_no: __('Phone'),
  company_name: __('Organization'),
  owner: __('Owner'),
  modified: __('Last updated'),
}

const columns = computed(() => {
  const base = contacts.value?.data?.columns || []
  const keys = base.map((c) => c.key)

  const out = base
    .filter((c) => c.key !== 'email_id')
    .map((c) => (LABELS[c.key] ? { ...c, label: LABELS[c.key], __source: c } : c))

  if (!keys.includes('full_name')) {
    out.unshift({ label: LABELS.full_name, key: 'full_name', type: 'Data', width: '17rem' })
  }

  const added = [
    { label: __('Relationship'), key: '__relationship', type: 'Data', width: '9rem' },
  ]
  if (!keys.includes('owner')) {
    added.push({ label: __('Owner'), key: '__owner', type: 'Data', width: '11rem' })
  }
  const at = out.findIndex((c) => c.key === 'modified')
  out.splice(at === -1 ? out.length : at, 0, ...added)

  // Set align right for last column
  if (out.length) {
    out[out.length - 1] = { ...out[out.length - 1], align: 'right' }
  }
  return out
})

// ---- Empty states ----

const TAB_EMPTY = {
  customers: {
    icon: LucideBadgeCheck,
    title: __('No customers yet'),
    text: __('Contacts appear here once a deal they are on is won.'),
  },
  prospects: {
    icon: LucideTarget,
    title: __('No prospects right now'),
    text: __('Contacts on open deals appear here.'),
  },
  followup: {
    icon: LucideCalendarCheck,
    title: __('Nothing needs follow-up'),
    text: __('Contacts on deals with overdue tasks appear here.'),
  },
}

const empty = computed(() => {
  const hasFilters = viewControls.value?.hasFilters
  const clearFilters = {
    label: __('Clear filters'),
    onClick: () => viewControls.value?.clearFilters(),
  }
  if (searchQuery.value) {
    return {
      icon: LucideSearchX,
      title: __('No contacts match “{0}”', [searchQuery.value]),
      text: __('Try a name, an email address or a phone number.'),
      actions: [{ label: __('Clear search'), onClick: clearSearch }],
    }
  }
  if (tab.value !== 'all') {
    return {
      ...TAB_EMPTY[tab.value],
      actions: [
        { label: __('Show all contacts'), onClick: () => (tab.value = 'all') },
        ...(hasFilters ? [clearFilters] : []),
      ],
    }
  }
  if (hasFilters) {
    return {
      icon: LucideFilterX,
      title: __('No contacts match these filters'),
      text: __('Some contacts are hidden by the filters on this view.'),
      actions: [clearFilters],
    }
  }
  return {
    icon: LucideUsers,
    title: __('No contacts yet'),
    text: __('Contacts are added when you create them or convert a lead into a deal.'),
    actions: [
      {
        label: __('Create contact'),
        primary: true,
        onClick: () => (showContactModal.value = true),
      },
    ],
  }
})
</script>
