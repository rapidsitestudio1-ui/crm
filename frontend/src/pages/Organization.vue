<template>
  <LayoutHeader v-if="organization.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <CustomActions
        v-if="organization._actions?.length"
        :actions="organization._actions"
      />
    </template>
  </LayoutHeader>

  <div
    v-if="organization.doc"
    ref="parentRef"
    class="cp-root flex h-full overflow-hidden"
  >
    <!-- ================= Left column ================= -->
    <Resizer
      :parent="$refs.parentRef"
      class="cp-side flex h-full flex-col overflow-hidden"
    >
      <div class="flex-1 overflow-y-auto">
        <!-- Identity -->
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="changeOrganizationImage"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex items-center gap-3.5 px-5 pt-5">
              <div class="group relative size-14 shrink-0">
                <KanbanAvatar
                  :image="organization.doc.organization_logo"
                  :label="organization.doc.organization_name || organization.doc.name"
                  size="xl"
                  square
                />
                <component
                  :is="organization.doc.organization_logo ? Dropdown : 'div'"
                  v-bind="
                    organization.doc.organization_logo
                      ? {
                          options: [
                            { icon: 'upload', label: __('Change logo'), onClick: openFileSelector },
                            { icon: 'trash-2', label: __('Remove logo'), onClick: () => changeOrganizationImage('') },
                          ],
                        }
                      : {
                          role: 'button',
                          tabindex: 0,
                          onClick: openFileSelector,
                          onKeydown: (e) => ['Enter', ' '].includes(e.key) && (e.preventDefault(), openFileSelector()),
                        }
                  "
                  class="!absolute inset-0 rounded-[10px]"
                  :aria-label="__('Change logo')"
                >
                  <div
                    class="absolute inset-0 flex cursor-pointer items-center justify-center rounded-[10px] bg-black/40 opacity-0 transition-opacity group-hover:opacity-100"
                  >
                    <CameraIcon class="size-5 text-white" />
                  </div>
                </component>
              </div>
              <div class="flex min-w-0 flex-col">
                <h1 class="cp-name truncate">{{ organization.doc.name }}</h1>
                <p v-if="headline" class="cp-sub line-clamp-2">{{ headline }}</p>
                <ErrorMessage :message="__(error)" />
              </div>
            </div>
          </template>
        </FileUploader>

        <!-- Quick actions -->
        <div class="cp-actions px-5 pb-5 pt-4">
          <button
            type="button"
            class="cp-action"
            :class="{ 'opacity-50': !organization.doc.website }"
            :title="organization.doc.website ? __('Open website') : __('No website')"
            @click="openWebsite"
          >
            <span class="cp-action-icon"><LucideGlobe /></span>
            {{ __('Website') }}
          </button>
          <button type="button" class="cp-action" @click="showContactModal = true">
            <span class="cp-action-icon"><LucideUserPlus /></span>
            {{ __('Contact') }}
          </button>
          <button type="button" class="cp-action" @click="showDealModal = true">
            <span class="cp-action-icon"><LucideHandshake /></span>
            {{ __('Deal') }}
          </button>
          <Dropdown :options="moreActions" placement="left">
            <button type="button" class="cp-action">
              <span class="cp-action-icon"><LucideEllipsis /></span>
              {{ __('More') }}
            </button>
          </Dropdown>
        </div>

        <!-- Company details -->
        <section class="cp-section">
          <button
            type="button"
            class="cp-section-head"
            :aria-expanded="open.details"
            @click="open.details = !open.details"
          >
            {{ __('Company details') }}
            <LucideChevronDown />
          </button>
          <div v-show="open.details" class="cp-section-body">
            <div v-if="organization.doc.website" class="cp-field">
              <span class="cp-label">{{ __('Website') }}</span>
              <div class="flex flex-wrap gap-1.5">
                <a :href="websiteUrl" target="_blank" rel="noopener" class="cp-chip">
                  <span class="truncate">{{ websiteLabel }}</span>
                  <LucideArrowUpRight class="size-3 shrink-0" />
                </a>
              </div>
            </div>
            <div v-if="organization.doc.industry" class="cp-field">
              <span class="cp-label">{{ __('Industry') }}</span>
              <span class="cp-value">
                <span class="kb-badge">
                  <span class="size-1.5 rounded-full" :style="{ background: industryDot }" />
                  {{ __(organization.doc.industry) }}
                </span>
              </span>
            </div>
            <div v-if="organization.doc.territory" class="cp-field">
              <span class="cp-label">{{ __('Territory') }}</span>
              <span class="cp-value">{{ organization.doc.territory }}</span>
            </div>
            <div v-if="organization.doc.no_of_employees" class="cp-field">
              <span class="cp-label">{{ __('Employees') }}</span>
              <span class="cp-value">{{ organization.doc.no_of_employees }}</span>
            </div>
            <div v-if="revenue" class="cp-field">
              <span class="cp-label">{{ __('Annual revenue') }}</span>
              <span class="cp-value tabular-nums">{{ revenue }}</span>
            </div>
            <div class="cp-field">
              <span class="cp-label">{{ __('Added') }}</span>
              <span class="cp-value">
                {{ dayjsLocal(organization.doc.creation).format('MMM D, YYYY') }}
                <template v-if="addedBy"> · {{ __('by {0}', [addedBy]) }}</template>
              </span>
            </div>
          </div>
        </section>

        <!-- All editable fields (the CRM's side panel, unchanged) -->
        <section class="cp-section">
          <button
            type="button"
            class="cp-section-head"
            :aria-expanded="open.fields"
            @click="open.fields = !open.fields"
          >
            {{ __('Edit fields') }}
            <LucideChevronDown />
          </button>
          <div v-show="open.fields" class="pb-3">
            <SidePanelLayout
              v-if="sections.data"
              :sections="sections.data"
              doctype="CRM Organization"
              :docname="organization.doc.name"
              @reload="sections.reload"
              @beforeFieldChange="beforeFieldChange"
            />
          </div>
        </section>
      </div>
    </Resizer>

    <!-- ================= Main area ================= -->
    <div class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <div class="cp-tabs" role="tablist" :aria-label="__('Organization sections')">
        <button
          v-for="t in tabs"
          :key="t.key"
          type="button"
          role="tab"
          class="cp-tab"
          :aria-selected="tab === t.key"
          @click="tab = t.key"
        >
          <component :is="t.icon" />
          {{ t.label }}
          <span v-if="t.count" class="cp-tab-count">{{ t.count }}</span>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto">
        <!-- Overview -->
        <div v-if="tab === 'overview'" class="cp-main max-w-[860px]">
          <section class="cp-block">
            <h2 class="cp-h">{{ __('Company overview') }}</h2>
            <dl class="cp-dl">
              <template v-for="row in overviewRows" :key="row.label">
                <dt>{{ row.label }}</dt>
                <dd><span class="truncate">{{ row.value }}</span></dd>
              </template>
            </dl>
          </section>

          <section v-if="openDeals.length" class="cp-block">
            <h2 class="cp-h">{{ __('Open deals') }}</h2>
            <div v-for="d in openDeals" :key="d.name" class="cp-callout">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="truncate text-[13.5px] font-medium">{{ d.lead_name || d.name }}</span>
                  <span class="kb-badge">
                    <span class="size-1.5 rounded-full" :style="{ background: stageDot(d.status) }" />
                    {{ __(d.status) }}
                  </span>
                </div>
                <p class="cp-sub mt-0.5">
                  {{ [money(d.deal_value, d.currency), d.probability ? __('{0}% probability', [Math.round(d.probability)]) : '', d.expected_closure_date ? __('closes {0}', [dayjsLocal(d.expected_closure_date).format('MMM D, YYYY')]) : ''].filter(Boolean).join(' • ') }}
                </p>
              </div>
              <router-link :to="{ name: 'Deal', params: { dealId: d.name } }" class="cp-btn">
                {{ __('Details') }}
                <LucideChevronRight />
              </router-link>
            </div>
          </section>

          <section class="cp-block">
            <div class="mb-3.5 flex items-center justify-between">
              <h2 class="cp-h !mb-0">{{ __('People') }}</h2>
              <button type="button" class="cp-btn" @click="showContactModal = true">
                <LucidePlus /> {{ __('Add contact') }}
              </button>
            </div>
            <p v-if="!contacts.data?.length" class="cp-empty">
              {{ __('No contacts at this organization yet.') }}
            </p>
            <router-link
              v-for="c in (contacts.data || []).slice(0, 5)"
              :key="c.name"
              :to="{ name: 'Contact', params: { contactId: c.name } }"
              class="cp-card flex items-center gap-3"
            >
              <KanbanAvatar :image="c.image" :label="c.full_name || c.name" size="md" />
              <span class="flex min-w-0 flex-1 flex-col">
                <span class="truncate text-[13.5px] font-medium">{{ c.full_name || c.name }}</span>
                <span class="cp-sub truncate">{{ [c.designation, c.email_id].filter(Boolean).join(' · ') }}</span>
              </span>
              <LucideChevronRight class="size-4 shrink-0" style="color: var(--kb-ink-3)" />
            </router-link>
            <button
              v-if="(contacts.data?.length || 0) > 5"
              type="button"
              class="cp-more !mt-0"
              @click="tab = 'contacts'"
            >
              {{ __('View all {0} contacts', [contacts.data.length]) }}
              <LucideChevronRight />
            </button>
          </section>

          <section class="cp-block">
            <h2 class="cp-h">{{ __('Recent activity') }}</h2>
            <ContactTimeline
              :items="activity.slice(0, 5)"
              :contactName="organization.doc.name"
              @toggleTask="toggleTask"
              @openTask="openTask"
            />
            <button
              v-if="activity.length > 5"
              type="button"
              class="cp-more !mt-0"
              @click="tab = 'activity'"
            >
              {{ __('View all activity') }}
              <LucideChevronRight />
            </button>
          </section>
        </div>

        <!-- Activity -->
        <div v-else-if="tab === 'activity'" class="cp-main max-w-[860px]">
          <p class="cp-sub mb-4">
            {{ __('Notes, tasks, emails and comments on this organization’s deals.') }}
          </p>
          <ContactTimeline
            :items="activity"
            :contactName="organization.doc.name"
            @toggleTask="toggleTask"
            @openTask="openTask"
          />
        </div>

        <!-- Deals (existing list) -->
        <div v-else-if="tab === 'deals'" class="flex h-full flex-col">
          <div class="cp-main !pb-0 flex items-center justify-between">
            <h2 class="cp-h !mb-0">{{ __('Deals') }}</h2>
            <button type="button" class="cp-btn is-primary" @click="showDealModal = true">
              <LucidePlus /> {{ __('New deal') }}
            </button>
          </div>
          <DealsListView
            v-if="dealRows.length"
            class="mt-2"
            :rows="dealRows"
            :columns="dealColumns"
            :options="{ selectable: false, showTooltip: false }"
          />
          <p v-else class="cp-main cp-empty">{{ __('No deals with this organization yet.') }}</p>
        </div>

        <!-- Contacts (existing list) -->
        <div v-else-if="tab === 'contacts'" class="flex h-full flex-col">
          <div class="cp-main !pb-0 flex items-center justify-between">
            <h2 class="cp-h !mb-0">{{ __('Contacts') }}</h2>
            <button type="button" class="cp-btn is-primary" @click="showContactModal = true">
              <LucidePlus /> {{ __('New contact') }}
            </button>
          </div>
          <ContactsListView
            v-if="contactRows.length"
            class="mt-2"
            :rows="contactRows"
            :columns="contactColumns"
            :options="{ selectable: false, showTooltip: false }"
          />
          <p v-else class="cp-main cp-empty">{{ __('No contacts at this organization yet.') }}</p>
        </div>
      </div>
    </div>
  </div>

  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Organization'"
    :docname="props.organizationId"
    name="Organizations"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="{ company_name: props.organizationId }"
    :options="{ redirect: false, afterInsert: () => contacts.reload() }"
  />
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="{ organization: props.organizationId }"
  />
</template>

<script setup>
import '@/components/Kanban/kanban.css'
import '@/components/ContactProfile/profile.css'
import LucideGlobe from '~icons/lucide/globe'
import LucideUserPlus from '~icons/lucide/user-plus'
import LucideHandshake from '~icons/lucide/handshake'
import LucideEllipsis from '~icons/lucide/ellipsis'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideChevronRight from '~icons/lucide/chevron-right'
import LucideArrowUpRight from '~icons/lucide/arrow-up-right'
import LucidePlus from '~icons/lucide/plus'
import LucideLayoutGrid from '~icons/lucide/layout-grid'
import LucideActivity from '~icons/lucide/activity'
import LucideUsers from '~icons/lucide/users'
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import CustomActions from '@/components/CustomActions.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import KanbanAvatar from '@/components/Kanban/KanbanAvatar.vue'
import ContactTimeline from '@/components/ContactProfile/ContactTimeline.vue'
import { getStageTone } from '@/components/Kanban/stageTones'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { getView } from '@/utils/view'
import {
  validateIsImageFile,
  setupCustomizations,
  copyToClipboard,
  openWebsite as openExternalWebsite,
} from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import {
  Breadcrumbs,
  FileUploader,
  Dropdown,
  createListResource,
  usePageMeta,
  createResource,
  dayjsLocal,
  toast,
  call,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { usePipelineSurface } from '@/composables/usePipelineSurface'
import { useTelemetry } from 'frappe-ui/frappe'
import { computed, reactive, ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  organizationId: { type: String, required: true },
})

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { getUser } = usersStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Organization')
const { capture } = useTelemetry()

const route = useRoute()
const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')

const showDeleteLinkedDocModal = ref(false)
const showContactModal = ref(false)
const showDealModal = ref(false)
const open = reactive({ details: true, fields: false })
usePipelineSurface()

const {
  document: organization,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('CRM Organization', props.organizationId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

onMounted(async () => {
  if (organization.doc) await triggerOnRender()
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Organizations'), route: { name: 'Organizations' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(
      route.query.view,
      route.query.viewType,
      'CRM Organization',
    )
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Organizations',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: {
      name: 'Organization',
      params: { organizationId: props.organizationId },
      query: route.query,
    },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return organization.doc?.[t] || props.organizationId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

async function deleteOrganization() {
  showDeleteLinkedDocModal.value = true
}

function changeOrganizationImage(file) {
  organization.setValue.submit({
    organization_logo: file?.file_url || null,
  })
}

function beforeFieldChange(data) {
  if (Object.hasOwn(data ?? {}, 'organization_name')) {
    call('frappe.client.rename_doc', {
      doctype: 'CRM Organization',
      old_name: props.organizationId,
      new_name: data.organization_name,
    }).then(() => {
      router.push({
        name: 'Organization',
        params: { organizationId: data.organization_name },
      })
    })
  } else {
    organization.save.submit()
  }
}

function openWebsite() {
  if (!organization.doc.website) {
    toast.error(__('No Website Found'))
    return
  }

  openExternalWebsite(organization.doc.website)
}

// ---- Profile header / details (custom, matches the contact page) ----

const websiteUrl = computed(() => {
  const w = organization.doc?.website || ''
  return /^https?:\/\//.test(w) ? w : `https://${w}`
})
const websiteLabel = computed(() =>
  (organization.doc?.website || '')
    .replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
    .replace(/\/$/, ''),
)
const headline = computed(() =>
  [organization.doc?.industry && __(organization.doc.industry), websiteLabel.value]
    .filter(Boolean)
    .join(' · '),
)
const industryDot = computed(
  () => getStageTone('CRM Organization', { name: organization.doc?.industry }).dot,
)
const addedBy = computed(() => {
  const owner = organization.doc?.owner
  return owner ? getUser(owner)?.full_name || owner : ''
})

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
const revenue = computed(() =>
  money(organization.doc?.annual_revenue, organization.doc?.currency),
)

function stageDot(status) {
  return getStageTone('CRM Deal', { name: status }, getDealStatus(status)).dot
}

const moreActions = computed(() => [
  {
    group: __('Actions'),
    hideLabel: true,
    items: [
      {
        label: __('Copy name'),
        icon: 'copy',
        onClick: () => copyToClipboard(props.organizationId),
      },
      canDelete.value && {
        label: __('Delete'),
        icon: 'trash-2',
        theme: 'red',
        onClick: deleteOrganization,
      },
    ].filter(Boolean),
  },
])

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Organization'],
  params: { doctype: 'CRM Organization' },
  auto: true,
  transform: (data) => getParsedSections(data),
})

function getParsedSections(_sections) {
  return _sections.map((section) => {
    section.columns = section.columns.map((column) => {
      column.fields = column.fields.map((field) => {
        if (field.fieldname === 'address') {
          return {
            ...field,
            create: (value, close) => {
              showAddressModal()
              close()
            },
            edit: (address) => showAddressModal(address),
          }
        } else {
          return field
        }
      })
      return column
    })
    return section
  })
}

const deals = createListResource({
  type: 'list',
  doctype: 'CRM Deal',
  cache: ['deals', props.organizationId],
  fields: [
    'name',
    'organization',
    'lead_name',
    'currency',
    'deal_value',
    'probability',
    'expected_closure_date',
    'status',
    'email',
    'mobile_no',
    'deal_owner',
    'modified',
  ],
  filters: {
    organization: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const contacts = createListResource({
  type: 'list',
  doctype: 'Contact',
  cache: ['contacts', props.organizationId],
  fields: [
    'name',
    'full_name',
    'image',
    'email_id',
    'designation',
    'mobile_no',
    'company_name',
    'modified',
  ],
  filters: {
    company_name: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const statusType = (d) => getDealStatus(d.status)?.type
const openDeals = computed(() =>
  (deals.data || []).filter((d) => ['Open', 'Ongoing'].includes(statusType(d))),
)
const wonDeals = computed(() => (deals.data || []).filter((d) => statusType(d) === 'Won'))

function sumValues(list) {
  if (!list.length) return ''
  const total = list.reduce((s, d) => s + (d.deal_value || 0), 0)
  return money(total, list[0].currency)
}

const overviewRows = computed(() =>
  [
    { label: __('Contacts'), value: contacts.data?.length ?? 0 },
    { label: __('Open deals'), value: openDeals.value.length },
    { label: __('Pipeline value'), value: sumValues(openDeals.value) },
    { label: __('Won deals'), value: wonDeals.value.length },
    { label: __('Won value'), value: sumValues(wonDeals.value) },
  ].filter((r) => r.value !== ''),
)

// ---- Tabs ----

const tab = ref('overview')
const tabs = computed(() => [
  { key: 'overview', label: __('Overview'), icon: LucideLayoutGrid },
  { key: 'activity', label: __('Activity'), icon: LucideActivity },
  { key: 'deals', label: __('Deals'), icon: LucideHandshake, count: deals.data?.length },
  { key: 'contacts', label: __('Contacts'), icon: LucideUsers, count: contacts.data?.length },
])

// ---- Activity: notes, tasks, emails and comments on this organization's deals ----

const activity = ref([])

function stripHtml(html) {
  const el = window.document.createElement('div')
  el.innerHTML = html || ''
  return (el.textContent || '').trim()
}

async function loadActivity() {
  const dealNames = (deals.data || []).map((d) => d.name)
  if (!dealNames.length) {
    activity.value = []
    return
  }
  const onDeals = { reference_doctype: 'CRM Deal' }
  const list = (args) => call('frappe.client.get_list', { limit_page_length: 50, ...args }).catch(() => [])
  const [notes, tasks, emails, comments] = await Promise.all([
    list({
      doctype: 'FCRM Note',
      fields: ['name', 'title', 'content', 'owner', 'creation', 'reference_docname'],
      filters: { ...onDeals, reference_docname: ['in', dealNames] },
      order_by: 'creation desc',
    }),
    list({
      doctype: 'CRM Task',
      fields: ['name', 'title', 'status', 'priority', 'due_date', 'owner', 'creation', 'reference_docname'],
      filters: { ...onDeals, reference_docname: ['in', dealNames] },
      order_by: 'creation desc',
    }),
    list({
      doctype: 'Communication',
      fields: ['name', 'subject', 'sent_or_received', 'sender', 'communication_date', 'reference_name'],
      filters: { ...onDeals, reference_name: ['in', dealNames], communication_medium: 'Email' },
      order_by: 'communication_date desc',
    }),
    list({
      doctype: 'Comment',
      fields: ['name', 'content', 'owner', 'creation', 'reference_name'],
      filters: { ...onDeals, reference_name: ['in', dealNames], comment_type: 'Comment' },
      order_by: 'creation desc',
    }),
  ])
  const ref_doctype = 'CRM Deal'
  activity.value = [
    ...notes.map((n) => ({ type: 'note', name: n.name, title: n.title, text: stripHtml(n.content), by: n.owner, time: n.creation, ref_doctype, ref_name: n.reference_docname })),
    ...tasks.map((t) => ({ type: 'task', name: t.name, title: t.title, status: t.status, priority: t.priority, due_date: t.due_date, by: t.owner, time: t.creation, ref_doctype, ref_name: t.reference_docname })),
    ...emails.map((e) => ({ type: 'email', name: e.name, title: e.subject, direction: e.sent_or_received, from: e.sender, time: e.communication_date, ref_doctype, ref_name: e.reference_name })),
    ...comments.map((c) => ({ type: 'comment', name: c.name, text: stripHtml(c.content), by: c.owner, time: c.creation, ref_doctype, ref_name: c.reference_name })),
  ].sort((a, b) => new Date(b.time) - new Date(a.time))
}
watch(() => deals.data, loadActivity, { immediate: true })

async function toggleTask(task, done) {
  const status = done ? 'Done' : 'Todo'
  const prev = task.status
  task.status = status
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Task',
      name: task.name,
      fieldname: 'status',
      value: status,
    })
  } catch (e) {
    task.status = prev
    toast.error(e?.messages?.[0] || __('Could not update the task'))
  }
}

function openTask(task) {
  router.push({ name: 'Deal', params: { dealId: task.ref_name }, hash: '#tasks' })
}

// ---- Deals / contacts tables (unchanged list views) ----

const dealRows = computed(() => (deals.data || []).map(getDealRowObject))
const contactRows = computed(() => (contacts.data || []).map(getContactRowObject))

const { getFormattedCurrency } = getMeta('CRM Deal')

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: organization.doc?.organization_logo,
    },
    deal_value: getFormattedCurrency('deal_value', deal),
    status: {
      label: deal.status,
      color: getDealStatus(deal.status)?.color,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: timestampCell(deal.modified),
  }
}

function getContactRowObject(contact) {
  return {
    name: contact.name,
    full_name: {
      label: contact.full_name,
      image_label: contact.full_name,
      image: contact.image,
    },
    email: contact.email_id,
    mobile_no: contact.mobile_no,
    company_name: {
      label: contact.company_name,
      logo: organization.doc?.organization_logo,
    },
    modified: timestampCell(contact.modified),
  }
}

const dealColumns = [
  {
    label: __('Organization'),
    key: 'organization',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'deal_value',
    align: 'right',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Mobile Number'),
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: __('Deal Owner'),
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: __('Last Modified'),
    key: 'modified',
    width: '8rem',
  },
]

const contactColumns = [
  {
    label: __('Name'),
    key: 'full_name',
    width: '17rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Phone'),
    key: 'mobile_no',
    width: '12rem',
  },
  {
    label: __('Organization'),
    key: 'company_name',
    width: '12rem',
  },
  {
    label: __('Last Modified'),
    key: 'modified',
    width: '8rem',
  },
]

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        organization.doc.address = d.name
        organization.save.submit()
      },
    },
  })
}

// Setup custom actions from Form Scripts
watch(
  () => organization.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField: organization.setValue.submit,
        createToast: toast.create,
        deleteDoc: deleteOrganization,
        call,
      })
      organization._actions = s.actions || []
    }
  },
  { once: true },
)
</script>
