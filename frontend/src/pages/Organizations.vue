<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Organizations" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="organizationsListView?.customListActions"
        :actions="organizationsListView.customListActions"
      />
      <Button
        class="crm-primary"
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showOrganizationModal = true"
      />
    </template>
  </LayoutHeader>

  <!-- Saved-view tabs, Industry / Territory filters, search. All are
       temporary page filters (default_filters), never written to the view. -->
  <div class="ct-bar">
    <div class="ct-tabs" role="tablist" :aria-label="__('Organization views')">
      <button
        v-for="t in tabs"
        :key="t.key"
        type="button"
        role="tab"
        class="ct-tab"
        :aria-selected="tab === t.key"
        :disabled="t.needsRelations && !stats.relationsLoaded.value"
        :title="t.hint"
        @click="tab = t.key"
      >
        {{ t.label }}
        <span v-if="t.count != null" class="ct-tab-count">{{ t.count }}</span>
      </button>
    </div>
    <Dropdown v-if="industryOptions.length" :options="industryMenu" placement="left">
      <button
        type="button"
        class="og-filter"
        :class="{ 'is-active': industry !== null }"
        :aria-label="__('Filter by industry')"
      >
        <LucideFactory />
        {{ industry === null ? __('Industry') : industry === '' ? __('No industry') : __(industry) }}
        <LucideChevronDown />
      </button>
    </Dropdown>
    <Dropdown v-if="territoryOptions.length" :options="territoryMenu" placement="left">
      <button
        type="button"
        class="og-filter"
        :class="{ 'is-active': territory !== null }"
        :aria-label="__('Filter by territory')"
      >
        <LucideMapPin />
        {{ territory === null ? __('Territory') : territory === '' ? __('No territory') : __(territory) }}
        <LucideChevronDown />
      </button>
    </Dropdown>
    <label class="ct-search !ml-0 sm:!ml-auto">
      <LucideSearch />
      <input
        ref="searchInput"
        v-model="search"
        type="search"
        :placeholder="__('Search name or website')"
        :aria-label="__('Search organizations')"
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
    v-model="organizations"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Organization"
    :filters="pageFilters"
    :options="{
      allowedViews: ['list', 'kanban'],
      kanbanColumnField: 'industry',
    }"
  />

  <!-- ===== Kanban ===== -->
  <KanbanView
    v-if="route.params.viewType == 'kanban'"
    v-model="organizations"
    :options="{
      getRoute: (row) => ({
        name: 'Organization',
        params: { organizationId: row.name },
        query: { view: route.query.view, viewType: route.params.viewType },
      }),
      onNewClick: (column) => newOrgIn(column),
      doctype: 'CRM Organization',
      cardFields: orgCardFields,
      columnLabel,
      hideEmptyColumns: true,
      canDrag: !groupFieldReadOnly,
      dragDisabledReason: groupFieldReadOnly
        ? __('{0} is read-only, so cards can’t be moved between columns.', [groupFieldLabel])
        : '',
    }"
    @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
  >
    <template #card-header="{ fields }">
      <KanbanCardHeader
        :title="fields.organization_name || fields.name"
        :subtitle="websiteLabel(fields.website)"
        :image="fields.organization_logo || ''"
        square
      >
        <template #actions>
          <Dropdown :options="cardActions(fields)" placement="right">
            <button type="button" class="kb-icon-btn" :aria-label="__('Quick actions')">
              <LucideMoreHorizontal class="size-4" />
            </button>
          </Dropdown>
        </template>
        <div class="og-stats">
          <span v-if="fields.annual_revenue" class="og-revenue">
            {{ money(fields.annual_revenue, fields.currency) }}
          </span>
          <span :title="__('Contacts')">
            <LucideUsers />
            {{ stats.counts[fields.name]?.contacts ?? '·' }}
          </span>
          <span :title="__('Open deals')">
            <LucideHandshake />
            {{ stats.counts[fields.name]?.openDeals ?? '·' }}
          </span>
        </div>
        <template
          v-if="stats.relationship(fields.name) || (groupField !== 'industry' && fields.industry)"
          #badges
        >
          <span
            v-if="stats.relationship(fields.name)"
            class="kb-badge"
            :class="badgeClass(stats.relationship(fields.name))"
          >
            {{ stats.relationship(fields.name).label }}
          </span>
          <span v-if="groupField !== 'industry' && fields.industry" class="kb-badge">
            {{ __(fields.industry) }}
          </span>
        </template>
      </KanbanCardHeader>
    </template>
    <template #card-footer="{ fields }">
      <KanbanCardFooter
        :time="timestampCell(fields.modified).timeAgo"
        :timeTitle="timestampCell(fields.modified).label"
      />
    </template>
  </KanbanView>

  <!-- ===== List ===== -->
  <OrganizationsListView
    v-else-if="organizations.data && rows.length"
    ref="organizationsListView"
    v-model="organizations.data.page_length_count"
    v-model:list="organizations"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: organizations.data.row_count,
      totalCount: organizations.data.total_count,
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

  <!-- Loading (list) -->
  <div
    v-else-if="!organizations.data"
    class="flex-1 overflow-hidden bg-[var(--kb-card)] px-5 pt-4"
    aria-busy="true"
  >
    <div v-for="i in 6" :key="i" class="mb-3 h-11 animate-pulse rounded-lg bg-[var(--kb-hover)]" />
  </div>

  <!-- Empty states -->
  <div v-else class="flex-1 overflow-y-auto bg-[var(--kb-card)]">
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

  <OrganizationPreview
    v-model="previewName"
    :relationship="previewName ? stats.relationship(previewName) : null"
  />
  <OrganizationModal
    v-if="showOrganizationModal"
    v-model="showOrganizationModal"
    :data="newOrgDefaults"
  />
</template>
<script setup>
import '@/components/Kanban/kanban.css'
import '@/components/Contacts/contacts.css'
import '@/components/Organizations/organizations.css'
import LucideSearch from '~icons/lucide/search'
import LucideSearchX from '~icons/lucide/search-x'
import LucideFilterX from '~icons/lucide/filter-x'
import LucideX from '~icons/lucide/x'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideFactory from '~icons/lucide/factory'
import LucideMapPin from '~icons/lucide/map-pin'
import LucideUsers from '~icons/lucide/users'
import LucideHandshake from '~icons/lucide/handshake'
import LucideBuilding from '~icons/lucide/building-2'
import LucideBadgeCheck from '~icons/lucide/badge-check'
import LucideTarget from '~icons/lucide/target'
import LucideSparkles from '~icons/lucide/sparkles'
import LucideMoreHorizontal from '~icons/lucide/more-horizontal'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import OrganizationsListView from '@/components/ListViews/OrganizationsListView.vue'
import OrganizationPreview from '@/components/Organizations/OrganizationPreview.vue'
import ViewControls from '@/components/ViewControls.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import KanbanCardHeader from '@/components/Kanban/KanbanCardHeader.vue'
import KanbanCardFooter from '@/components/Kanban/KanbanCardFooter.vue'
import { useOrganizationStats } from '@/composables/useOrganizationStats'
import { getMeta } from '@/stores/meta'
import { formatDate, website } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { call, dayjs, Dropdown } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import {
  ref,
  computed,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency, doctypeMeta } =
  getMeta('CRM Organization')

const route = useRoute()
const router = useRouter()

const organizationsListView = ref(null)
const showOrganizationModal = ref(false)

// organizations data is loaded in the ViewControls component
const organizations = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// ---------------- Related counts + relationships (custom) ----------------

const stats = useOrganizationStats(() => {
  const d = organizations.value?.data
  if (!d?.data?.length) return null
  return d.view_type === 'kanban'
    ? d.data.flatMap((col) => (col.data || []).map((o) => o.name))
    : d.data.map((o) => o.name)
})

// ---------------- Tabs, filters, search (custom) ----------------

const tab = ref('all')
const industry = ref(null) // null = any, '' = not set
const territory = ref(null)
const search = ref('')
const searchQuery = ref('')
const searchNames = ref(null)
const searchInput = ref(null)
const previewName = ref(null)

const recentSince = dayjs().subtract(30, 'day').format('YYYY-MM-DD')

const tabs = computed(() => [
  { key: 'all', label: __('All companies') },
  {
    key: 'customers',
    label: __('Customers'),
    needsRelations: true,
    count: stats.relationsLoaded.value ? stats.customers.value.size : null,
    hint: __('Organizations with at least one won deal'),
  },
  {
    key: 'prospects',
    label: __('Prospects'),
    needsRelations: true,
    count: stats.relationsLoaded.value ? stats.prospects.value.size : null,
    hint: __('Organizations with an open deal'),
  },
  {
    key: 'recent',
    label: __('Recently added'),
    hint: __('Added in the last 30 days'),
  },
])

// Industry / territory options: only values actually in use, with counts.
const industryOptions = ref([])
const territoryOptions = ref([])
async function loadFilterOptions() {
  const grouped = (field) =>
    call('frappe.client.get_list', {
      doctype: 'CRM Organization',
      fields: [field, 'count(name) as n'],
      group_by: field,
      order_by: 'n desc',
      limit_page_length: 0,
    }).catch(() => [])
  const [ind, terr] = await Promise.all([grouped('industry'), grouped('territory')])
  industryOptions.value = ind
  // Territory filter only makes sense once some organization has one.
  territoryOptions.value = terr.some((t) => t.territory) ? terr : []
}

function filterMenu(options, field, model, noneLabel) {
  // NULL and '' come back as separate groups; both mean "not set".
  const none = options.filter((o) => !o[field]).reduce((sum, o) => sum + o.n, 0)
  return [
    {
      group: __('Filter'),
      hideLabel: true,
      items: [
        { label: __('Any'), onClick: () => (model.value = null) },
        ...options
          .filter((o) => o[field])
          .map((o) => ({ label: `${__(o[field])} (${o.n})`, onClick: () => (model.value = o[field]) })),
        ...(none
          ? [{ label: `${noneLabel} (${none})`, onClick: () => (model.value = '') }]
          : []),
      ],
    },
  ]
}
const industryMenu = computed(() =>
  filterMenu(industryOptions.value, 'industry', industry, __('No industry')),
)
const territoryMenu = computed(() =>
  filterMenu(territoryOptions.value, 'territory', territory, __('No territory')),
)

// Search name OR website: resolve to names (or_filters), then filter by name.
const applySearch = useDebounceFn(async (q) => {
  q = q.trim()
  searchQuery.value = q
  if (!q) return (searchNames.value = null)
  const rows = await call('frappe.client.get_list', {
    doctype: 'CRM Organization',
    fields: ['name'],
    or_filters: [
      ['organization_name', 'like', `%${q}%`],
      ['website', 'like', `%${q}%`],
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

function intersect(a, b) {
  if (!a) return b
  if (!b) return a
  const set = new Set(b)
  return a.filter((x) => set.has(x))
}

const pageFilters = computed(() => {
  const f = {}
  if (tab.value === 'recent') f.creation = ['>=', recentSince]
  let names = null
  if (tab.value === 'customers') names = [...stats.customers.value]
  if (tab.value === 'prospects') names = [...stats.prospects.value]
  names = intersect(names, searchNames.value)
  if (names) f.name = ['in', names.length ? names : ['__no_organization__']]
  if (industry.value !== null) f.industry = industry.value === '' ? ['is', 'not set'] : industry.value
  if (territory.value !== null) f.territory = territory.value === '' ? ['is', 'not set'] : territory.value
  return f
})
watch(
  pageFilters,
  async () => {
    await nextTick()
    for (let i = 0; i < 20 && organizations.value?.loading; i++) {
      await new Promise((r) => setTimeout(r, 100))
    }
    viewControls.value?.reload()
  },
  { deep: true },
)

// ---------------- List rows / columns ----------------

function money(value, currency) {
  if (!value) return ''
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currency || 'USD',
      notation: value >= 1e6 ? 'compact' : 'standard',
      maximumFractionDigits: value >= 1e6 ? 1 : 0,
    }).format(value)
  } catch {
    return `${currency || ''} ${value}`
  }
}
function websiteLabel(w) {
  return (w || '').replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/$/, '')
}

const rows = computed(() => {
  if (
    !organizations.value?.data?.data ||
    !['list', 'group_by'].includes(organizations.value.data.view_type)
  )
    return []
  return organizations.value?.data.data.map((organization) => {
    let _rows = {}
    organizations.value?.data.rows.forEach((row) => {
      _rows[row] = organization[row]

      let fieldType = organizations.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(
          organization[row],
          '',
          true,
          fieldType == 'Datetime',
        )
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, organization)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, organization)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, organization)
      }

      if (row === 'organization_name') {
        _rows[row] = {
          label: organization.organization_name,
          logo: organization.organization_logo,
        }
      } else if (row === 'website') {
        _rows[row] = website(organization.website)
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(organization[row])
      }
    })
    _rows.name = organization.name
    if (!_rows.organization_name?.label) {
      _rows.organization_name = {
        label: organization.organization_name || organization.name,
        logo: organization.organization_logo,
      }
    }
    _rows.__website = websiteLabel(organization.website)
    _rows.__industry = organization.industry ? __(organization.industry) : ''
    _rows.__revenue = money(organization.annual_revenue, organization.currency)
    _rows.__contacts = stats.counts[organization.name]?.contacts
    _rows.__open_deals = stats.counts[organization.name]?.openDeals
    return _rows
  })
})

// Display-only columns: the saved layout stays as is (and editable in
// Columns). Organization always first with the website under it (a separate
// Website column folds into it); Contacts and Open deals are added.
const LABELS = {
  organization_name: __('Organization'),
  annual_revenue: __('Annual revenue'),
  modified: __('Last updated'),
}

const columns = computed(() => {
  const base = organizations.value?.data?.columns || []
  const keys = base.map((c) => c.key)
  const out = base
    .filter((c) => c.key !== 'website')
    .map((c) => {
      const label = LABELS[c.key]
      const align = c.key === 'annual_revenue' ? 'right' : c.align
      return label || align !== c.align ? { ...c, label: label || c.label, align, __source: c } : c
    })
  if (!keys.includes('organization_name')) {
    out.unshift({ label: LABELS.organization_name, key: 'organization_name', type: 'Data', width: '18rem' })
  }
  const added = [
    { label: __('Contacts'), key: '__contacts', type: 'Data', width: '7rem' },
    { label: __('Open deals'), key: '__open_deals', type: 'Data', width: '7rem' },
  ]
  const at = out.findIndex((c) => c.key === 'annual_revenue' || c.key === 'modified')
  out.splice(at === -1 ? out.length : at, 0, ...added)
  return out
})

// ---------------- Kanban (custom) ----------------

const orgCardFields = [
  'organization_name',
  'organization_logo',
  'website',
  'annual_revenue',
  'modified',
  'industry',
  'currency',
]

const groupField = computed(() => organizations.value?.data?.column_field || 'industry')
const groupFieldMeta = computed(() =>
  (doctypeMeta.value?.fields || []).find((f) => f.fieldname === groupField.value),
)
const groupFieldLabel = computed(() => __(groupFieldMeta.value?.label || groupField.value))
const groupFieldReadOnly = computed(() => Boolean(groupFieldMeta.value?.read_only))

function columnLabel(name) {
  return name ? __(name) : __('No {0}', [groupFieldLabel.value.toLowerCase()])
}

const newOrgDefaults = ref({})
function newOrgIn(column) {
  newOrgDefaults.value = column.column.name ? { [groupField.value]: column.column.name } : {}
  showOrganizationModal.value = true
}
watch(showOrganizationModal, (open) => {
  if (!open) newOrgDefaults.value = {}
})

function badgeClass(rel) {
  return { success: 'is-success', accent: 'is-accent' }[rel?.tone] || ''
}

function cardActions(fields) {
  return [
    { label: __('Preview'), icon: 'sidebar', onClick: () => (previewName.value = fields.name) },
    {
      label: __('Open organization'),
      icon: 'arrow-up-right',
      onClick: () => router.push({ name: 'Organization', params: { organizationId: fields.name } }),
    },
    ...(fields.website
      ? [
          {
            label: __('Visit website'),
            icon: 'external-link',
            onClick: () =>
              window.open(/^https?:\/\//.test(fields.website) ? fields.website : `https://${fields.website}`, '_blank', 'noopener'),
          },
        ]
      : []),
  ]
}

// ---------------- Empty states ----------------

const TAB_EMPTY = {
  customers: {
    icon: LucideBadgeCheck,
    title: __('No customers yet'),
    text: __('Organizations appear here once one of their deals is won.'),
  },
  prospects: {
    icon: LucideTarget,
    title: __('No prospects right now'),
    text: __('Organizations with an open deal appear here.'),
  },
  recent: {
    icon: LucideSparkles,
    title: __('Nothing added recently'),
    text: __('Organizations added in the last 30 days appear here.'),
  },
}

const empty = computed(() => {
  const hasFilters = viewControls.value?.hasFilters
  const clearFilters = { label: __('Clear filters'), onClick: () => viewControls.value?.clearFilters() }
  const clearPageFilters = () => {
    industry.value = null
    territory.value = null
  }
  if (searchQuery.value) {
    return {
      icon: LucideSearchX,
      title: __('No organizations match “{0}”', [searchQuery.value]),
      text: __('Search looks in organization names and websites.'),
      actions: [{ label: __('Clear search'), onClick: clearSearch }],
    }
  }
  if (industry.value !== null || territory.value !== null) {
    return {
      icon: LucideFilterX,
      title: __('No organizations match these filters'),
      text: __('Try another industry or territory.'),
      actions: [{ label: __('Clear industry / territory'), onClick: clearPageFilters }],
    }
  }
  if (tab.value !== 'all') {
    return {
      ...TAB_EMPTY[tab.value],
      actions: [
        { label: __('Show all companies'), onClick: () => (tab.value = 'all') },
        ...(hasFilters ? [clearFilters] : []),
      ],
    }
  }
  if (hasFilters) {
    return {
      icon: LucideFilterX,
      title: __('No organizations match these filters'),
      text: __('Some organizations are hidden by the filters on this view.'),
      actions: [clearFilters],
    }
  }
  return {
    icon: LucideBuilding,
    title: __('No organizations yet'),
    text: __('Add the companies you sell to. Deals and contacts can then be linked to them.'),
    actions: [
      { label: __('Create organization'), primary: true, onClick: () => (showOrganizationModal.value = true) },
    ],
  }
})

// ---------------- Page chrome ----------------

// Remember List / Kanban for next time (used when opening /organizations).
watch(
  () => route.params.viewType,
  (type) => {
    if (!['list', 'kanban'].includes(type)) return
    try {
      localStorage.setItem('crm-last-view:Organizations', type)
    } catch {
      // storage unavailable (private mode): fall back to the default view
    }
  },
  { immediate: true },
)

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
  stats.loadRelations()
  loadFilterOptions()
})
onBeforeUnmount(() => {
  delete document.documentElement.dataset.surface
  window.removeEventListener('keydown', onKeydown)
})
</script>
