<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template v-if="!errorTitle" #right-header>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <AssignTo v-model="assignees.data" doctype="CRM Lead" :docname="leadId" />
      <Dropdown
        v-if="doc && document.statuses"
        :options="statuses"
        placement="right"
      >
        <template #default="{ open }">
          <Button
            v-if="doc.status"
            :label="statusLabel(doc.status)"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          >
            <template #prefix>
              <IndicatorIcon :class="getLeadStatus(doc.status).color" />
            </template>
          </Button>
        </template>
      </Dropdown>
      <Tooltip
        :disabled="!isLeadConversionDisabled"
        :text="__('Cannot convert a lost lead to deal')"
      >
        <div class="inline-flex">
          <Button
            :label="__('Convert to Deal')"
            variant="solid"
            :disabled="isLeadConversionDisabled"
            @click="showConvertToDealModal = true"
          />
        </div>
      </Tooltip>
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="cp-root rp-page flex h-full overflow-hidden">
    <Resizer class="cp-side flex flex-col justify-between">
      <FileUploader
        :validateFile="validateIsImageFile"
        @success="(file) => updateField('image', file.file_url)"
      >
        <template #default="{ openFileSelector, error: uploadError }">
          <div class="flex items-center gap-3.5 px-5 pt-5">
            <div class="group relative size-14 shrink-0">
              <KanbanAvatar :image="doc.image" :label="title" size="xl" />
              <component
                :is="doc.image ? Dropdown : 'div'"
                v-bind="
                  doc.image
                    ? {
                        options: [
                          { icon: 'upload', label: __('Change Image'), onClick: openFileSelector },
                          { icon: 'trash-2', label: __('Remove Image'), onClick: () => updateField('image', '') },
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
              <Tooltip :text="doc.lead_name || __('Set First Name')">
                <h1 class="cp-name truncate">{{ title }}</h1>
              </Tooltip>
              <p v-if="headerSubtitle" class="cp-sub line-clamp-2">{{ headerSubtitle }}</p>
              <button
                type="button"
                class="cp-id"
                :title="__('Copy ID')"
                @click="copyToClipboard(leadId)"
              >
                {{ leadId }}
              </button>
              <ErrorMessage :message="__(uploadError)" />
            </div>
          </div>
        </template>
      </FileUploader>
      <!-- Quick actions (same row as the contact page) -->
      <div class="cp-actions px-5 pb-5 pt-4">
        <button
          type="button"
          class="cp-action"
          :class="{ 'opacity-50': !doc.email }"
          :title="doc.email ? __('Write an email') : __('No email address')"
          @click="
            doc.email
              ? openEmailBox()
              : toast.error(__('Please set an email address to send emails'))
          "
        >
          <span class="cp-action-icon"><LucideMail /></span>
          {{ __('Email') }}
        </button>
        <button
          v-if="callEnabled"
          type="button"
          class="cp-action"
          @click="() => doc.mobile_no ? makeCall(doc.mobile_no) : toast.error(__('Please set a mobile number to make calls'))"
        >
          <span class="cp-action-icon"><LucidePhone /></span>
          {{ __('Call') }}
        </button>
        <button type="button" class="cp-action" @click="activities?.showNote()">
          <span class="cp-action-icon"><LucideSquarePen /></span>
          {{ __('Note') }}
        </button>
        <button type="button" class="cp-action" @click="activities?.showTask()">
          <span class="cp-action-icon"><LucideClipboardList /></span>
          {{ __('Task') }}
        </button>
        <Dropdown :options="headerMoreActions" placement="left">
          <button type="button" class="cp-action">
            <span class="cp-action-icon"><LucideEllipsis /></span>
            {{ __('More') }}
          </button>
        </Dropdown>
      </div>
      <SLASection
        v-if="doc.sla_status"
        v-model="doc"
        @updateField="updateField"
      />
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="CRM Lead"
          :docname="leadId"
          @reload="sections.reload"
          @beforeFieldChange="beforeStatusChange"
          @afterFieldChange="reloadResources"
        />
      </div>
    </Resizer>
    <Tabs
      v-model="tabIndex"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel>
        <Activities
          ref="activities"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          doctype="CRM Lead"
          :docname="leadId"
          :tabs="tabs"
          @beforeSave="beforeStatusChange"
          @afterSave="reloadResources"
        />
      </template>
    </Tabs>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <ConvertToDealModal
    v-if="showConvertToDealModal"
    v-model="showConvertToDealModal"
    :lead="doc"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Lead"
    :docname="leadId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Lead'"
    :docname="leadId"
    :title="doc.lead_name"
    name="Leads"
  />
  <LostReasonModal
    v-if="showLostReasonModal"
    v-model="showLostReasonModal"
    doctype="CRM Lead"
    :document="document"
  />
</template>
<script setup>
import '@/components/Kanban/kanban.css'
import '@/components/ContactProfile/profile.css'
import KanbanAvatar from '@/components/Kanban/KanbanAvatar.vue'
import LucideMail from '~icons/lucide/mail'
import LucidePhone from '~icons/lucide/phone'
import LucideSquarePen from '~icons/lucide/square-pen'
import LucideClipboardList from '~icons/lucide/clipboard-list'
import LucideEllipsis from '~icons/lucide/ellipsis'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LostReasonModal from '@/components/Modals/LostReasonModal.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'
import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
  validateIsImageFile,
  isTranslatable,
} from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { whatsappEnabled } from '@/composables/whatsapp'
import { callEnabled } from '@/composables/telephony'
import {
  createResource,
  FileUploader,
  Dropdown,
  Tooltip,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import { useUnsavedChangesWarning } from '@/composables/useUnsavedChangesWarning'
import { useVisitedRecords } from '@/composables/useVisitedRecords'
import { usePipelineSurface } from '@/composables/usePipelineSurface'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { statusOptions, getLeadStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Lead')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  leadId: { type: String, required: true },
})

const reload = ref(false)
const activities = ref(null)
const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showConvertToDealModal = ref(false)
const showFilesUploader = ref(false)

const {
  triggerOnChange,
  triggerOnRender,
  assignees,
  permissions,
  document,
  scripts,
  error,
} = useDocument('CRM Lead', props.leadId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const doc = computed(() => document.doc || {})
const isLeadConversionDisabled = computed(
  () => doc.value.status && getLeadStatus(doc.value.status)?.type === 'Lost',
)

useUnsavedChangesWarning(() => document.isDirty)

const { markVisited } = useVisitedRecords('CRM Lead')
usePipelineSurface()

onMounted(async () => {
  if (document.doc) await triggerOnRender()
  markVisited(props.leadId)
})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? __('Document not found')
        : __('Error occurred'),
    )
    errorMessage.value = __(err.messages?.[0] || __('An error occurred'))
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField,
        createToast: toast.create,
        deleteDoc: deleteLead,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: {
      name: 'Lead',
      params: { leadId: props.leadId },
      query: route.query,
    },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return doc.value?.[t] || props.leadId
})

const statuses = computed(() => {
  let customStatuses = document.statuses?.length
    ? document.statuses
    : document._statuses || []
  return statusOptions('lead', customStatuses, triggerStatusChange)
})

usePageMeta(() => {
  return { title: title.value, icon: brand.favicon }
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'Emails',
      label: __('Emails'),
      icon: EmailIcon,
    },
    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },
    {
      name: 'Data',
      label: __('Data'),
      icon: DetailsIcon,
    },
    {
      name: 'Calls',
      label: __('Calls'),
      icon: PhoneIcon,
    },
    {
      name: 'Tasks',
      label: __('Tasks'),
      icon: TaskIcon,
    },
    {
      name: 'Notes',
      label: __('Notes'),
      icon: NoteIcon,
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastLeadTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Lead'],
  params: { doctype: 'CRM Lead' },
  auto: true,
})

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  setLostReason()
}

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: () => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
    },
  })
}

function deleteLead() {
  showDeleteLinkedDocModal.value = true
}

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activities'].includes(currentTab.name)) {
    activities.value.changeTabTo('emails')
  }
  nextTick(() => (activities.value.emailBox.show = true))
}

function statusLabel(status) {
  if (isTranslatable('CRM Lead Status')) return __(status)
  return status
}

const showLostReasonModal = ref(false)

function setLostReason() {
  if (
    getLeadStatus(document.doc.status).type !== 'Lost' ||
    (document.doc.lost_reason && document.doc.lost_reason !== 'Other') ||
    (document.doc.lost_reason === 'Other' && document.doc.lost_notes)
  ) {
    document.save.submit(null, {
      onSuccess: () => sections.reload(),
    })
    return
  }

  showLostReasonModal.value = true
}

function beforeStatusChange(data) {
  if (
    Object.hasOwn(data ?? {}, 'status') &&
    getLeadStatus(data.status).type == 'Lost'
  ) {
    setLostReason()
  } else {
    document.save.submit(null, {
      onSuccess: () => reloadResources(data),
    })
  }
}

function reloadResources(data) {
  if (Object.hasOwn(data ?? {}, 'lead_owner')) {
    assignees.reload()
  }
  if (
    Object.hasOwn(data ?? {}, 'status') &&
    getLeadStatus(data.status).type != 'Lost'
  ) {
    sections.reload()
  }
}

// ---- Profile-style header (custom, matches the contact page) ----

const headerSubtitle = computed(() => {
  const d = doc.value || {}
  if (d.job_title && d.organization) return __('{0} at {1}', [d.job_title, d.organization])
  return d.job_title || d.organization || ''
})

const headerMoreActions = computed(() => [
  {
    group: __('Actions'),
    hideLabel: true,
    items: [
      doc.value?.website && {
        label: __('Go to website'),
        icon: 'external-link',
        onClick: () => openWebsite(doc.value.website),
      },
      {
        label: __('Attach a file'),
        icon: 'paperclip',
        onClick: () => (showFilesUploader.value = true),
      },
      {
        label: __('Copy ID'),
        icon: 'copy',
        onClick: () => copyToClipboard(props.leadId),
      },
      canDelete.value && {
        label: __('Delete'),
        icon: 'trash-2',
        theme: 'red',
        onClick: deleteLead,
      },
    ].filter(Boolean),
  },
])
</script>
