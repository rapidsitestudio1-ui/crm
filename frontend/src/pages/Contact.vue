<template>
  <LayoutHeader v-if="contact.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <CustomActions
        v-if="contact._actions?.length"
        :actions="contact._actions"
      />
    </template>
  </LayoutHeader>

  <div v-if="contact.doc" ref="parentRef" class="cp-root flex h-full overflow-hidden">
    <!-- ================= Left column ================= -->
    <Resizer
      :parent="$refs.parentRef"
      class="cp-side flex h-full flex-col overflow-hidden"
    >
      <div class="flex-1 overflow-y-auto">
        <!-- Identity -->
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="changeContactImage"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex items-center gap-3.5 px-5 pt-5">
              <div class="group relative size-14 shrink-0">
                <KanbanAvatar
                  :image="contact.doc.image"
                  :label="contact.doc.full_name || contact.doc.name"
                  size="xl"
                />
                <component
                  :is="contact.doc.image ? Dropdown : 'div'"
                  v-bind="
                    contact.doc.image
                      ? {
                          options: [
                            { icon: 'upload', label: __('Change image'), onClick: openFileSelector },
                            { icon: 'trash-2', label: __('Remove image'), onClick: () => changeContactImage('') },
                          ],
                        }
                      : {
                          role: 'button',
                          tabindex: 0,
                          onClick: openFileSelector,
                          onKeydown: (e) => ['Enter', ' '].includes(e.key) && (e.preventDefault(), openFileSelector()),
                        }
                  "
                  class="!absolute inset-0 rounded-full"
                  :aria-label="__('Change photo')"
                >
                  <div
                    class="absolute inset-0 flex cursor-pointer items-center justify-center rounded-full bg-black/40 opacity-0 transition-opacity group-hover:opacity-100"
                  >
                    <CameraIcon class="size-5 text-white" />
                  </div>
                </component>
              </div>
              <div class="flex min-w-0 flex-col">
                <h1 class="cp-name truncate">
                  <span v-if="contact.doc.salutation">{{ contact.doc.salutation }} </span>
                  {{ contact.doc.full_name || contact.doc.name }}
                </h1>
                <p v-if="headline" class="cp-sub line-clamp-2">{{ headline }}</p>
                <ErrorMessage :message="__(error)" />
              </div>
            </div>
          </template>
        </FileUploader>

        <!-- Quick actions -->
        <div class="cp-actions px-5 pb-5 pt-4">
          <button type="button" class="cp-action" @click="addNote">
            <span class="cp-action-icon"><LucideSquarePen /></span>
            {{ __('Note') }}
          </button>
          <button
            type="button"
            class="cp-action"
            :class="{ 'opacity-50': !primaryEmail }"
            :title="primaryEmail ? __('Write an email') : __('No email address')"
            @click="openEmailComposer"
          >
            <span class="cp-action-icon"><LucideMail /></span>
            {{ __('Email') }}
          </button>
          <button type="button" class="cp-action" @click="addTask">
            <span class="cp-action-icon"><LucideClipboardList /></span>
            {{ __('Task') }}
          </button>
          <button type="button" class="cp-action" @click="showMeeting = true">
            <span class="cp-action-icon"><LucideCalendar /></span>
            {{ __('Meeting') }}
          </button>
          <Dropdown :options="moreActions" placement="left">
            <button type="button" class="cp-action">
              <span class="cp-action-icon"><LucideEllipsis /></span>
              {{ __('More') }}
            </button>
          </Dropdown>
        </div>

        <!-- Contact details -->
        <section class="cp-section">
          <button
            type="button"
            class="cp-section-head"
            :aria-expanded="open.details"
            @click="open.details = !open.details"
          >
            {{ __('Contact details') }}
            <LucideChevronDown />
          </button>
          <div v-show="open.details" class="cp-section-body">
            <div v-if="emails.length" class="cp-field">
              <span class="cp-label">{{ emails.length > 1 ? __('Emails') : __('Email') }}</span>
              <div class="flex flex-wrap gap-1.5">
                <a
                  v-for="e in emails"
                  :key="e.email_id"
                  :href="`mailto:${e.email_id}`"
                  class="cp-chip"
                >
                  <span class="truncate">{{ e.email_id }}</span>
                  <span v-if="emails.length > 1 && e.is_primary" class="cp-chip-tag">{{ __('Primary') }}</span>
                </a>
              </div>
            </div>
            <div v-if="phones.length" class="cp-field">
              <span class="cp-label">{{ phones.length > 1 ? __('Phones') : __('Phone') }}</span>
              <div class="flex flex-wrap gap-1.5">
                <component
                  :is="callEnabled ? 'button' : 'a'"
                  v-for="p in phones"
                  :key="p.phone"
                  :href="callEnabled ? undefined : `tel:${p.phone}`"
                  :type="callEnabled ? 'button' : undefined"
                  class="cp-chip"
                  @click="callEnabled && makeCall(p.phone)"
                >
                  {{ p.phone }}
                  <span v-if="p.tag" class="cp-chip-tag">{{ p.tag }}</span>
                </component>
              </div>
            </div>
            <div v-if="profile.data?.location?.label" class="cp-field">
              <span class="cp-label">{{ __('Location') }}</span>
              <span class="cp-value">{{ profile.data.location.label }}</span>
            </div>
            <div v-if="localTime" class="cp-field">
              <span class="cp-label">{{ __('Local time') }}</span>
              <span class="cp-value">{{ localTime }}</span>
            </div>
            <div v-if="firstInteraction" class="cp-field">
              <span class="cp-label">{{ __('First interaction') }}</span>
              <span class="cp-value">{{ firstInteraction }}</span>
            </div>
            <div class="cp-field">
              <span class="cp-label">{{ __('Added') }}</span>
              <span class="cp-value">{{ dayjsLocal(contact.doc.creation).format('MMM D, YYYY') }}</span>
            </div>
            <p v-if="!emails.length && !phones.length" class="cp-sub mt-3">
              {{ __('No email or phone yet. Add them under Edit fields.') }}
            </p>
          </div>
        </section>

        <!-- Communication preferences (Contact.unsubscribed) -->
        <section class="cp-section">
          <button
            type="button"
            class="cp-section-head"
            :aria-expanded="open.prefs"
            @click="open.prefs = !open.prefs"
          >
            {{ __('Communication preferences') }}
            <LucideChevronDown />
          </button>
          <div v-show="open.prefs" class="cp-section-body">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="cp-value">{{ __('Email updates') }}</p>
                <p class="cp-sub mt-0.5">
                  {{
                    contact.doc.unsubscribed
                      ? __('Unsubscribed. Newsletters and bulk emails are not sent to this contact.')
                      : __('Subscribed to newsletters and bulk emails.')
                  }}
                </p>
              </div>
              <button
                type="button"
                role="switch"
                class="cp-switch mt-0.5"
                :aria-checked="!contact.doc.unsubscribed"
                :aria-label="__('Receive email updates')"
                @click="toggleSubscribed"
              />
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
              :sections="parsedSections"
              doctype="Contact"
              :docname="contact.doc.name"
              @reload="sections.reload"
            />
          </div>
        </section>
      </div>
    </Resizer>

    <!-- ================= Main area ================= -->
    <div class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <div class="cp-tabs" role="tablist" :aria-label="__('Contact sections')">
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
            <h2 class="cp-h">{{ __('Profile overview') }}</h2>
            <dl class="cp-dl">
              <template v-for="row in overviewRows" :key="row.label">
                <dt>{{ row.label }}</dt>
                <dd>
                  <component :is="row.render" v-if="row.render" />
                  <span v-else class="truncate">{{ row.value }}</span>
                </dd>
              </template>
            </dl>
            <button
              v-if="moreRows.length"
              type="button"
              class="cp-more"
              :aria-expanded="showMoreRows"
              @click="showMoreRows = !showMoreRows"
            >
              {{ showMoreRows ? __('Less') : __('More') }}
              <LucideChevronDown />
            </button>
          </section>

          <section v-if="openDeals.length" class="cp-block">
            <h2 class="cp-h">{{ __('Open deals') }}</h2>
            <div
              v-for="d in openDeals"
              :key="d.name"
              class="cp-callout"
            >
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="truncate text-[13.5px] font-medium">{{ d.organization || d.name }}</span>
                  <span class="kb-badge">
                    <span class="size-1.5 rounded-full" :style="{ background: stageDot(d.status) }" />
                    {{ __(d.status) }}
                  </span>
                </div>
                <p class="cp-sub mt-0.5">
                  {{ [dealValue(d), d.probability ? __('{0}% probability', [Math.round(d.probability)]) : '', d.expected_closure_date ? __('closes {0}', [dayjsLocal(d.expected_closure_date).format('MMM D, YYYY')]) : ''].filter(Boolean).join(' • ') }}
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
              <h2 class="cp-h !mb-0">{{ __('Activity') }}</h2>
            </div>
            <ContactTimeline
              :items="activity.slice(0, 5)"
              :contactName="contact.doc.full_name || contact.doc.name"
              :deals="profile.data?.deals || []"
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
          <ContactTimeline
            :items="activity"
            :contactName="contact.doc.full_name || contact.doc.name"
            :deals="profile.data?.deals || []"
            @toggleTask="toggleTask"
            @openTask="openTask"
          />
        </div>

        <!-- Deals (existing list) -->
        <div v-else-if="tab === 'deals'" class="h-full">
          <DealsListView
            v-if="rows.length"
            class="mt-4"
            :rows="rows"
            :columns="columns"
            :options="{ selectable: false, showTooltip: false }"
          />
          <p v-else class="cp-main cp-empty">{{ __('Not linked to any deal yet.') }}</p>
        </div>

        <!-- Notes -->
        <div v-else-if="tab === 'notes'" class="cp-main max-w-[860px]">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="cp-h !mb-0">{{ __('Notes') }}</h2>
            <button type="button" class="cp-btn is-primary" @click="addNote">
              <LucidePlus /> {{ __('Add note') }}
            </button>
          </div>
          <p v-if="!notes.length" class="cp-empty">
            {{ __('No notes yet. Notes added here, or on their deals, show up in this list.') }}
          </p>
          <button
            v-for="n in notes"
            :key="n.name"
            type="button"
            class="cp-card block w-full text-left"
            @click="openNote(n)"
          >
            <div class="flex items-start justify-between gap-4">
              <span class="text-[13.5px] font-medium">{{ n.title || __('Untitled note') }}</span>
              <span class="cp-tl-time">{{ dayjsLocal(n.time).format('MMM D, YYYY') }}</span>
            </div>
            <p v-if="n.text" class="cp-tl-detail line-clamp-3">{{ n.text }}</p>
            <p class="mt-1.5 text-[12px]" style="color: var(--kb-ink-3)">
              {{ getUser(n.by)?.full_name || n.by }}
              <template v-if="n.ref_doctype === 'CRM Deal'"> · {{ __('on deal {0}', [dealLabel(n.ref_name)]) }}</template>
            </p>
          </button>
        </div>

        <!-- Tasks -->
        <div v-else-if="tab === 'tasks'" class="cp-main max-w-[860px]">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="cp-h !mb-0">{{ __('Tasks') }}</h2>
            <button type="button" class="cp-btn is-primary" @click="addTask">
              <LucidePlus /> {{ __('Add task') }}
            </button>
          </div>
          <p v-if="!tasks.length" class="cp-empty">
            {{ __('No tasks yet. Tasks added here, or on their deals, show up in this list.') }}
          </p>
          <ContactTimeline
            v-else
            :items="tasks"
            :contactName="contact.doc.full_name || contact.doc.name"
            :deals="profile.data?.deals || []"
            @toggleTask="toggleTask"
            @openTask="openTask"
          />
        </div>

        <!-- Emails -->
        <div v-else-if="tab === 'emails'" class="cp-main max-w-[860px]">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="cp-h !mb-0">{{ __('Emails') }}</h2>
            <button type="button" class="cp-btn is-primary" @click="openEmailComposer">
              <LucideMail /> {{ __('New email') }}
            </button>
          </div>
          <!-- The CRM's own email composer (same as on Leads and Deals):
               templates, attachments, CC/BCC, signature; sent from the user's
               email account and linked to this contact. -->
          <div class="cp-composer mb-6">
            <CommunicationArea
              ref="composer"
              v-model:reload="emailSent"
              :modelValue="emailDoc"
              doctype="Contact"
            />
          </div>
          <p v-if="!emailItems.length" class="cp-empty">
            {{ __('No emails yet. Emails with this contact, or on their deals, show up here.') }}
          </p>
          <ContactTimeline
            v-else
            :items="emailItems"
            :contactName="contact.doc.full_name || contact.doc.name"
            :deals="profile.data?.deals || []"
          />
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
    :doctype="'Contact'"
    :docname="contact.doc.name"
    name="Contacts"
  />
  <MeetingDialog
    v-if="contact.doc"
    v-model="showMeeting"
    :contact="contact.doc.name"
    @scheduled="profile.reload()"
  />
</template>

<script setup>
import '@/components/Kanban/kanban.css'
import '@/components/ContactProfile/profile.css'
import LucideSquarePen from '~icons/lucide/square-pen'
import LucideMail from '~icons/lucide/mail'
import LucideClipboardList from '~icons/lucide/clipboard-list'
import LucideCalendar from '~icons/lucide/calendar'
import LucideEllipsis from '~icons/lucide/ellipsis'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideChevronRight from '~icons/lucide/chevron-right'
import LucidePlus from '~icons/lucide/plus'
import LucideLayoutList from '~icons/lucide/layout-list'
import LucideActivity from '~icons/lucide/activity'
import LucideHandshake from '~icons/lucide/handshake'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucideSquareCheck from '~icons/lucide/square-check'
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import Icon from '@/components/Icon.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import CustomActions from '@/components/CustomActions.vue'
import KanbanAvatar from '@/components/Kanban/KanbanAvatar.vue'
import { getStageTone } from '@/components/Kanban/stageTones'
import ContactTimeline from '@/components/ContactProfile/ContactTimeline.vue'
import MeetingDialog from '@/components/ContactProfile/MeetingDialog.vue'
import CommunicationArea from '@/components/CommunicationArea.vue'
import { validateIsImageFile, setupCustomizations } from '@/utils'
import { useContactFields } from '@/composables/useContactFields'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { getView } from '@/utils/view'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/telephony'
import {
  Breadcrumbs,
  FileUploader,
  ErrorMessage,
  call,
  createResource,
  usePageMeta,
  Dropdown,
  toast,
  dayjs,
  dayjsLocal,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from 'frappe-ui/frappe'
import {
  ref,
  reactive,
  computed,
  watch,
  h,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { makeCall, $dialog, $socket } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()

const props = defineProps({
  contactId: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')

const {
  document: contact,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('Contact', props.contactId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const transformField = useContactFields(contact)

onMounted(async () => {
  if (contact.doc) await triggerOnRender()
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Contacts'), route: { name: 'Contacts' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'Contact')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Contacts',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: {
      name: 'Contact',
      params: { contactId: props.contactId },
      query: route.query,
    },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return contact.doc?.[t] || props.contactId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})
const showDeleteLinkedDocModal = ref(false)

async function deleteContact() {
  showDeleteLinkedDocModal.value = true
}

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact image updated'))
    },
  })
}

// ---------------- Profile data (custom) ----------------

const profile = createResource({
  url: 'crm.api.contact_profile.get_contact_profile',
  params: { contact: props.contactId },
  auto: true,
})

const tab = ref('overview')
const open = reactive({ details: true, prefs: true, fields: false })
const showMeeting = ref(false)
const showMoreRows = ref(false)

const activity = computed(() => profile.data?.activity || [])
const notes = computed(() => activity.value.filter((a) => a.type === 'note'))
const tasks = computed(() => activity.value.filter((a) => a.type === 'task'))
const emailItems = computed(() => activity.value.filter((a) => a.type === 'email'))

const tabs = computed(() => [
  { key: 'overview', label: __('Overview'), icon: LucideLayoutList },
  { key: 'activity', label: __('Activity'), icon: LucideActivity },
  { key: 'deals', label: __('Deals'), icon: LucideHandshake, count: deals.data?.length },
  { key: 'notes', label: __('Notes'), icon: LucideStickyNote, count: notes.value.length },
  { key: 'tasks', label: __('Tasks'), icon: LucideSquareCheck, count: tasks.value.length },
  { key: 'emails', label: __('Emails'), icon: LucideMail, count: emailItems.value.length },
])

const headline = computed(() => {
  const d = contact.doc
  if (!d) return ''
  if (d.designation && d.company_name) return __('{0} at {1}', [d.designation, d.company_name])
  return d.designation || d.company_name || ''
})

const emails = computed(() => {
  const d = contact.doc
  const list = d?.email_ids?.length
    ? d.email_ids
    : d?.email_id
      ? [{ email_id: d.email_id, is_primary: 1 }]
      : []
  return [...list].sort((a, b) => (b.is_primary || 0) - (a.is_primary || 0))
})
const primaryEmail = computed(() => emails.value[0]?.email_id || '')

const phones = computed(() => {
  const d = contact.doc
  const list = d?.phone_nos?.length
    ? d.phone_nos
    : [d?.mobile_no, d?.phone].filter(Boolean).map((phone) => ({ phone }))
  return list.map((p) => ({
    phone: p.phone,
    tag: p.is_primary_mobile_no ? __('Mobile') : p.is_primary_phone ? __('Phone') : '',
  }))
})

// Local time from the address country's time zone, ticking every 30s.
const now = ref(dayjs())
let clock
onMounted(() => (clock = setInterval(() => (now.value = dayjs()), 30000)))
onBeforeUnmount(() => clearInterval(clock))
const localTime = computed(() => {
  const tz = profile.data?.location?.time_zone
  if (!tz) return ''
  try {
    return now.value.tz(tz).format('MMM D, YYYY h:mm A')
  } catch {
    return ''
  }
})

const firstInteraction = computed(() => {
  const times = activity.value.filter((a) => a.type !== 'added' && a.time).map((a) => a.time)
  if (!times.length) return ''
  const first = times.reduce((a, b) => (a < b ? a : b))
  return dayjsLocal(first).format('MMM D, YYYY')
})

// ---- Overview ----

const org = computed(() => profile.data?.organization)
const openDeals = computed(() =>
  (profile.data?.deals || []).filter((d) => !['Won', 'Lost'].includes(d.status_type)),
)
const source = computed(() => (profile.data?.deals || []).find((d) => d.source)?.source)
const owner = computed(() => contact.doc?.owner && getUser(contact.doc.owner))

function formatMoney(value, currency) {
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
function dealValue(d) {
  return formatMoney(d.deal_value, d.currency) || __('No value')
}
function stageDot(status) {
  return getStageTone('CRM Deal', { name: status }, getDealStatus(status)).dot
}
function dealLabel(name) {
  return (profile.data?.deals || []).find((d) => d.name === name)?.organization || name
}

const allRows = computed(() => {
  const d = contact.doc || {}
  const rows = [
    d.designation && { label: __('Title'), value: d.designation },
    d.department && { label: __('Department'), value: d.department },
    d.company_name && {
      label: __('Associated company'),
      render: () =>
        h(
          'span',
          { class: 'flex min-w-0 items-center gap-2' },
          [
            h(KanbanAvatar, {
              image: org.value?.organization_logo || getOrganization(d.company_name)?.organization_logo,
              label: d.company_name,
              size: 'xs',
              square: true,
            }),
            org.value
              ? h(
                  'a',
                  {
                    class: 'truncate hover:underline',
                    href: router.resolve({ name: 'Organization', params: { organizationId: d.company_name } }).href,
                  },
                  d.company_name,
                )
              : h('span', { class: 'truncate' }, d.company_name),
          ],
        ),
    },
    org.value?.website && {
      label: __('Company website'),
      render: () =>
        h('a', { class: 'cp-chip', href: org.value.website, target: '_blank', rel: 'noopener' }, org.value.website.replace(/^https?:\/\//, '')),
    },
    org.value?.annual_revenue && {
      label: __('Company revenue'),
      value: formatMoney(org.value.annual_revenue, org.value.currency),
    },
    source.value && { label: __('Source'), value: __(source.value) },
    owner.value?.full_name && {
      label: __('Contact owner'),
      render: () =>
        h('span', { class: 'flex items-center gap-2' }, [
          h(KanbanAvatar, { image: owner.value.user_image, label: owner.value.full_name, size: 'xs' }),
          h('span', { class: 'truncate' }, owner.value.full_name),
        ]),
    },
    d.contact_stage && { label: __('Stage'), value: __(d.contact_stage), more: true },
    org.value?.industry && { label: __('Industry'), value: __(org.value.industry), more: true },
    org.value?.no_of_employees && { label: __('Company size'), value: __('{0} employees', [org.value.no_of_employees]), more: true },
    d.gender && { label: __('Gender'), value: __(d.gender), more: true },
    { label: __('Added'), value: dayjsLocal(d.creation).format('MMM D, YYYY'), more: true },
    { label: __('Last updated'), value: dayjsLocal(d.modified).format('MMM D, YYYY'), more: true },
  ]
  return rows.filter(Boolean)
})
const moreRows = computed(() => allRows.value.filter((r) => r.more))
const overviewRows = computed(() =>
  showMoreRows.value ? allRows.value : allRows.value.filter((r) => !r.more),
)

// ---- Actions ----

const { showModal } = useDoctypeModal()

function addNote() {
  showModal({
    doctype: 'FCRM Note',
    title: __('Note'),
    defaults: { reference_doctype: 'Contact', reference_docname: contact.doc.name },
    callbacks: { afterInsert: () => profile.reload(), afterUpdate: () => profile.reload() },
  })
}
function openNote(n) {
  showModal({
    doctype: 'FCRM Note',
    name: n.name,
    title: __('Note'),
    callbacks: { afterUpdate: () => profile.reload() },
  })
}
function addTask() {
  showModal({
    doctype: 'CRM Task',
    title: __('Task'),
    defaults: { reference_doctype: 'Contact', reference_docname: contact.doc.name, status: 'Todo' },
    callbacks: { afterInsert: () => profile.reload(), afterUpdate: () => profile.reload() },
  })
}
function openTask(t) {
  showModal({
    doctype: 'CRM Task',
    name: t.name,
    title: __('Task'),
    callbacks: { afterUpdate: () => profile.reload() },
  })
}
async function toggleTask(t, done) {
  const prev = t.status
  t.status = done ? 'Done' : 'Todo'
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Task',
      name: t.name,
      fieldname: 'status',
      value: t.status,
    })
  } catch {
    t.status = prev
    toast.error(__('Could not update the task'))
  }
}

// ---- Email: the CRM's own composer (CommunicationArea), for this contact ----

const composer = ref(null)
const emailSent = ref(false)
// The composer reads the recipient from `email`; Contact keeps it in email_id.
const emailDoc = computed(() => ({ ...contact.doc, email: primaryEmail.value }))
watch(emailSent, (sent) => {
  if (!sent) return
  emailSent.value = false
  profile.reload()
})

async function openEmailComposer() {
  if (!primaryEmail.value) {
    toast.error(__('Add an email address to this contact first'))
    open.fields = true
    return
  }
  tab.value = 'emails'
  await nextTick()
  if (composer.value) composer.value.show = true
}

function toggleSubscribed() {
  contact.doc.unsubscribed = contact.doc.unsubscribed ? 0 : 1
  contact.save.submit(null, {
    onSuccess: () =>
      toast.success(
        contact.doc.unsubscribed ? __('Unsubscribed from email updates') : __('Subscribed to email updates'),
      ),
  })
}

const moreActions = computed(() => [
  {
    group: __('Actions'),
    hideLabel: true,
    items: [
      callEnabled.value && phones.value.length && {
        label: __('Call'),
        icon: 'phone',
        onClick: () => makeCall(phones.value[0].phone),
      },
      primaryEmail.value && {
        label: __('Copy email'),
        icon: 'copy',
        onClick: () => copy(primaryEmail.value),
      },
      {
        label: __('Copy link'),
        icon: 'link',
        onClick: () => copy(window.location.href),
      },
      canDelete.value && {
        label: __('Delete contact'),
        icon: 'trash-2',
        theme: 'red',
        onClick: deleteContact,
      },
    ].filter(Boolean),
  },
])

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    toast.success(__('Copied'))
  } catch {
    toast.error(__('Could not copy'))
  }
}

// Live updates: anything that feeds the timeline refreshes it.
const LIVE = ['FCRM Note', 'CRM Task', 'Comment', 'Communication', 'CRM Call Log', 'Event', 'CRM Deal']
let liveTimer
function onListUpdate(data) {
  if (!LIVE.includes(data?.doctype)) return
  clearTimeout(liveTimer)
  liveTimer = setTimeout(() => profile.reload(), 600)
}
onMounted(() => {
  LIVE.forEach((dt) => $socket.emit('doctype_subscribe', dt))
  $socket.on('list_update', onListUpdate)
})
onBeforeUnmount(() => {
  clearTimeout(liveTimer)
  $socket.off('list_update', onListUpdate)
})

// ---------------- Existing: deals list, side panel fields ----------------

const deals = createResource({
  url: 'crm.api.contact.get_linked_deals',
  cache: ['deals', props.contactId],
  params: { contact: props.contactId },
  auto: true,
})

const rows = computed(() => {
  if (!deals.data || deals.data == []) return []

  return deals.data.map((row) => getDealRowObject(row))
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
})

const parsedSections = computed(() => {
  if (!sections.data) return []
  return sections.data.map((section) => ({
    ...section,
    columns: section.columns.map((column) => ({
      ...column,
      fields: column.fields.map((field) => {
        field.label = fieldLabelMap[field.fieldname] || field.label
        field.placeholder =
          fieldPlaceholderMap[field.fieldname] || field.placeholder
        return transformField(field, { showAddressModal })
      }),
    })),
  }))
})

const fieldLabelMap = {
  mobile_no: __('Mobile Number'),
  company_name: __('Organization'),
}

const fieldPlaceholderMap = {
  mobile_no: __('Add Mobile Number...'),
  company_name: __('Add Organization...'),
}

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
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

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        contact.doc.address = d.name
        contact.save.submit()
      },
    },
  })
}

// Setup custom actions from Form Scripts
watch(
  () => contact.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField: contact.setValue.submit,
        createToast: toast.create,
        deleteDoc: deleteContact,
        call,
      })
      contact._actions = s.actions || []
    }
  },
  { once: true },
)
</script>
