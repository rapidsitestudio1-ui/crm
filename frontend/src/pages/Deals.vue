<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Deals" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="dealsListView?.customListActions"
        :actions="dealsListView.customListActions"
      />
      <Button
        class="crm-primary"
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showDealModal = true"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="deals"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Deal"
    :options="{
      allowedViews: ['list', 'group_by', 'kanban'],
    }"
  />
  <KanbanView
    v-if="route.params.viewType == 'kanban'"
    v-model="deals"
    :options="{
      getRoute: (row) => ({
        name: 'Deal',
        params: { dealId: row.name },
        query: { view: route.query.view, viewType: route.params.viewType },
      }),
      onNewClick: (column) => onNewClick(column),
      doctype: 'CRM Deal',
      getStatus: (name) => getDealStatus(name),
      cardFields: dealCardFields,
    }"
    @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
  >
    <template #card-header="{ itemName, column, titleField }">
      <KanbanCardHeader
        :title="cardTitle(itemName, titleField)"
        :subtitle="cardSubtitle(itemName)"
        :image="getRow(itemName, 'organization').logo"
        square
        :email="column.fields?.includes('email') ? getRow(itemName, 'email').label : ''"
        :phone="
          column.fields?.includes('mobile_no')
            ? getRow(itemName, 'mobile_no').label
            : ''
        "
      >
        <template #actions>
          <Dropdown :options="actions(itemName)" placement="right">
            <button type="button" class="kb-icon-btn" :aria-label="__('Quick actions')">
              <LucidePlus class="size-4" />
            </button>
          </Dropdown>
        </template>
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between gap-2">
            <span v-if="dealValue(itemName)" class="kb-value truncate">
              {{ dealValue(itemName) }}
            </span>
            <span v-else class="kb-subtitle">{{ __('No value') }}</span>
            <span
              v-if="dealExtras[itemName]?.probability"
              class="kb-badge"
              :title="__('Probability')"
            >
              {{ Math.round(dealExtras[itemName].probability) }}%
            </span>
          </div>
          <div v-if="closeInfo(itemName)" class="kb-meta">
            <LucideCalendar />
            <span
              class="truncate"
              :class="{ 'text-[#B91C1C]': closeInfo(itemName).overdue }"
            >
              {{ closeInfo(itemName).label }}
            </span>
          </div>
        </div>
        <template v-if="slaBadge(itemName)" #badges>
          <span
            class="kb-badge"
            :class="slaBadge(itemName).cls"
            :title="slaBadge(itemName).title"
          >
            {{ slaBadge(itemName).label }}
          </span>
        </template>
      </KanbanCardHeader>
    </template>
    <template #fields="{ fieldName, itemName }">
      <div
        v-if="getRow(itemName, fieldName).label"
        class="truncate flex items-center gap-2"
      >
        <div v-if="fieldName === 'status'">
          <IndicatorIcon :class="getRow(itemName, fieldName).color" />
        </div>
        <div v-else-if="fieldName === 'organization'">
          <Avatar
            v-if="getRow(itemName, fieldName).label"
            class="flex items-center"
            :image="getRow(itemName, fieldName).logo"
            :label="getRow(itemName, fieldName).label"
            size="xs"
          />
        </div>
        <div v-else-if="fieldName === 'deal_owner'">
          <Avatar
            v-if="getRow(itemName, fieldName).full_name"
            class="flex items-center"
            :image="getRow(itemName, fieldName).user_image"
            :label="getRow(itemName, fieldName).full_name"
            size="xs"
          />
        </div>
        <div
          v-if="
            [
              'modified',
              'creation',
              'first_response_time',
              'first_responded_on',
              'response_by',
            ].includes(fieldName)
          "
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, fieldName).label">
            <div>{{ getRow(itemName, fieldName).timeAgo }}</div>
          </Tooltip>
        </div>
        <div v-else-if="fieldName === 'sla_status'" class="truncate text-base">
          <Badge
            v-if="getRow(itemName, fieldName).value"
            :variant="'subtle'"
            :theme="getRow(itemName, fieldName).color"
            size="md"
            :label="getRow(itemName, fieldName).value"
          />
        </div>
        <div
          v-else-if="fieldName === '_assign'"
          class="flex items-center truncate"
        >
          <MultipleAvatar
            :avatars="getRow(itemName, fieldName).label"
            size="xs"
          />
        </div>
        <div v-else class="truncate text-base">
          {{ getRow(itemName, fieldName).label }}
        </div>
      </div>
    </template>

    <template #card-footer="{ itemName, column }">
      <KanbanCardFooter
        :counts="{
          email: getRow(itemName, '_email_count').label,
          note: getRow(itemName, '_note_count').label,
          task: getRow(itemName, '_task_count').label,
          comment: getRow(itemName, '_comment_count').label,
        }"
        :assignees="
          column.fields?.includes('_assign')
            ? getRow(itemName, '_assign').label || []
            : []
        "
        :owner="cardOwner(itemName)"
        :time="
          column.fields?.includes('modified')
            ? getRow(itemName, 'modified').timeAgo
            : ''
        "
        :timeTitle="getRow(itemName, 'modified').label"
      />
    </template>
  </KanbanView>
  <DealsListView
    v-else-if="deals.data && rows.length"
    ref="dealsListView"
    v-model="deals.data.page_length_count"
    v-model:list="deals"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: deals.data.row_count,
      totalCount: deals.data.total_count,
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
  />
  <EmptyState
    v-else-if="deals.data && !rows.length"
    name="Deals"
    :icon="DealsIcon"
  />
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="defaults"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import CustomActions from '@/components/CustomActions.vue'
import EmailAtIcon from '@/components/Icons/EmailAtIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import KanbanCardHeader from '@/components/Kanban/KanbanCardHeader.vue'
import KanbanCardFooter from '@/components/Kanban/KanbanCardFooter.vue'
import { useKanbanExtras } from '@/composables/useKanbanExtras'
import LucidePlus from '~icons/lucide/plus'
import LucideCalendar from '~icons/lucide/calendar'
import DealModal from '@/components/Modals/DealModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/telephony'
import { formatDate, timeAgo, website, formatTime } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { Tooltip, Avatar, Dropdown } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { ref, reactive, computed, h, onMounted, onBeforeUnmount } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Deal')
const { makeCall } = globalStore()
const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()
const { showModal } = useDoctypeModal()

const route = useRoute()

const dealsListView = ref(null)
const showDealModal = ref(false)

const defaults = reactive({})

// deals data is loaded in the ViewControls component
const deals = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value
    }
    return { label: value }
  }
  return getValue(rows.value?.find((row) => row.name == name)[field])
}

// Rows
const rows = computed(() => {
  if (!deals.value?.data?.data) return []
  if (deals.value.data.view_type === 'group_by') {
    if (!deals.value?.data.group_by_field?.fieldname) return []
    return getGroupedByRows(
      deals.value?.data.data,
      deals.value?.data.group_by_field,
      deals.value.data.columns,
    )
  } else if (deals.value.data.view_type === 'kanban') {
    return getKanbanRows(deals.value.data.data, deals.value.data.fields)
  } else {
    return parseRows(deals.value?.data.data, deals.value.data.columns)
  }
})

const columns = computed(() => {
  let _columns = deals.value?.data?.columns || []

  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

function getGroupedByRows(listRows, groupByField, columns) {
  let groupedRows = []

  groupByField.options?.forEach((option) => {
    let filteredRows

    if (!option) {
      filteredRows = listRows.filter((row) => !row[groupByField.fieldname])
    } else {
      filteredRows = listRows.filter(
        (row) => row[groupByField.fieldname] == option,
      )
    }

    let groupDetail = {
      label: groupByField.label,
      group: option || __(' '),
      collapsed: false,
      rows: parseRows(filteredRows, columns),
    }
    if (groupByField.fieldname == 'status') {
      groupDetail.icon = () =>
        h(IndicatorIcon, {
          class: getDealStatus(option)?.color,
        })
    }
    groupedRows.push(groupDetail)
  })

  return groupedRows || listRows
}

function getKanbanRows(data, columns) {
  let _rows = []
  data.forEach((column) => {
    column.data?.forEach((row) => {
      _rows.push(row)
    })
  })
  return parseRows(_rows, columns)
}

function parseRows(rows, columns = []) {
  let view_type = deals.value.data.view_type
  let key = view_type === 'kanban' ? 'fieldname' : 'key'
  let type = view_type === 'kanban' ? 'fieldtype' : 'type'

  return rows.map((deal) => {
    let _rows = {}
    deals.value.data.rows.forEach((row) => {
      _rows[row] = deal[row]

      let fieldType = columns?.find((col) => (col[key] || col.value) == row)?.[
        type
      ]

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(deal[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, deal)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, deal)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, deal)
      }

      if (row == 'organization') {
        _rows[row] = {
          label: deal.organization,
          logo: getOrganization(deal.organization)?.organization_logo,
        }
      } else if (row === 'website') {
        _rows[row] = website(deal.website)
      } else if (row == 'status') {
        _rows[row] = {
          label: deal.status,
          color: getDealStatus(deal.status)?.color,
        }
      } else if (row == 'sla_status') {
        let value = deal.sla_status
        let tooltipText = value
        let color =
          deal.sla_status == 'Failed'
            ? 'red'
            : deal.sla_status == 'Fulfilled'
              ? 'green'
              : 'orange'
        if (value == 'First Response Due' || value == 'Rolling Response Due') {
          value = __(timeAgo(deal.response_by))
          tooltipText = formatDate(deal.response_by)
          if (new Date(deal.response_by) < new Date()) {
            color = 'red'
          }
        }
        _rows[row] = {
          label: tooltipText,
          value: value,
          color: color,
        }
      } else if (row == 'deal_owner') {
        _rows[row] = {
          label: deal.deal_owner && getUser(deal.deal_owner).full_name,
          ...(deal.deal_owner && getUser(deal.deal_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(deal._assign || '[]')
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(deal[row])
      } else if (
        ['first_response_time', 'first_responded_on', 'response_by'].includes(
          row,
        )
      ) {
        let field = row == 'response_by' ? 'response_by' : 'first_responded_on'
        _rows[row] = {
          label: deal[field] ? formatDate(deal[field]) : '',
          timeAgo: deal[row]
            ? row == 'first_response_time'
              ? formatTime(deal[row])
              : __(timeAgo(deal[row]))
            : '',
        }
      }
    })
    _rows['_email_count'] = deal._email_count
    _rows['_note_count'] = deal._note_count
    _rows['_task_count'] = deal._task_count
    _rows['_comment_count'] = deal._comment_count
    return _rows
  })
}

function onNewClick(column) {
  let column_field = deals.value.params.column_field

  if (column_field) {
    defaults[column_field] = column.column.name
  }

  showDealModal.value = true
}

function actions(itemName) {
  let mobile_no = getRow(itemName, 'mobile_no')?.label || ''
  let actions = [
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(mobile_no),
      condition: () => mobile_no && callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New Note'),
      onClick: () => showNote(itemName),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('New Task'),
      onClick: () => showTask(itemName),
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
}

function showNote(name) {
  showModal({
    doctype: 'FCRM Note',
    title: 'Note',
    defaults: {
      reference_doctype: 'CRM Deal',
      reference_docname: name,
    },
    callbacks: {
      afterInsert: (d) => after(d, true),
      afterUpdate: after,
    },
  })
}

function showTask(name) {
  showModal({
    doctype: 'CRM Task',
    title: 'Task',
    defaults: {
      reference_doctype: 'CRM Deal',
      reference_docname: name,
    },
    callbacks: {
      afterInsert: (d) => after(d, true),
      afterUpdate: after,
    },
  })
}

function after(d, isNew = false) {
  let a = d.doctype == 'CRM Task' ? 'task' : 'note'
  if (isNew) {
    updateOnboardingStep('create_first_' + a)
    capture(a + '_created')
  } else {
    capture(a + '_updated')
  }
}

// ---- Kanban card presentation (custom) ----

// Fields the card header/footer already shows; anything else picked in Kanban
// settings is listed on the card as label / value.
const dealCardFields = [
  'organization',
  'email',
  'mobile_no',
  '_assign',
  'modified',
  'status',
  'deal_owner',
  'sla_status',
  'deal_value',
  'probability',
  'expected_closure_date',
  'lead_name',
]

// The board query doesn't return these; read them for the cards on screen.
const dealExtras = useKanbanExtras(
  'CRM Deal',
  () =>
    deals.value?.data?.view_type === 'kanban'
      ? deals.value.data.data.flatMap((c) => (c.data || []).map((d) => d.name))
      : null,
  [
    'deal_value',
    'expected_deal_value',
    'probability',
    'expected_closure_date',
    'closed_date',
    'lead_name',
    'currency',
  ],
)

function labelOf(v) {
  if (v == null) return ''
  if (typeof v === 'object') return v.label || v.timeAgo || ''
  return String(v)
}

function cardTitle(itemName, titleField) {
  const org = getRow(itemName, 'organization').label
  if (!titleField || titleField === 'organization') {
    return org || dealExtras[itemName]?.lead_name || itemName
  }
  return labelOf(getRow(itemName, titleField)) || org || itemName
}

function cardSubtitle(itemName) {
  return dealExtras[itemName]?.lead_name || ''
}

function dealValue(itemName) {
  const d = dealExtras[itemName]
  if (!d) return ''
  const field = d.deal_value ? 'deal_value' : d.expected_deal_value ? 'expected_deal_value' : null
  if (!field) return ''
  // CRM currency formatting, without trailing zero decimals.
  return getFormattedCurrency(field, d).replace(/[.,]00(?=\D*$)/, '')
}

function closeInfo(itemName) {
  const d = dealExtras[itemName]
  const status = getRow(itemName, 'status').label
  const type = getDealStatus(status)?.type
  if (type === 'Won' && d?.closed_date) {
    return { label: __('Won {0}', [formatDate(d.closed_date, 'MMM D')]), overdue: false }
  }
  if (!d?.expected_closure_date || ['Won', 'Lost'].includes(type)) return null
  const overdue = new Date(d.expected_closure_date) < new Date(new Date().toDateString())
  return {
    label: overdue
      ? __('Close date passed · {0}', [formatDate(d.expected_closure_date, 'MMM D')])
      : __('Closes {0}', [formatDate(d.expected_closure_date, 'MMM D')]),
    overdue,
  }
}

function cardOwner(itemName) {
  const o = getRow(itemName, 'deal_owner')
  return o?.label ? { label: o.label, image: o.user_image } : null
}

function slaBadge(itemName) {
  const s = getRow(itemName, 'sla_status')
  if (!s?.value) return null
  const cls = { red: 'is-danger', green: 'is-success', orange: 'is-warning' }[s.color] || ''
  return { label: s.value, title: s.label, cls }
}

// Indigo accents for this page's toolbar and primary action (see kanban.css).
onMounted(() => (document.documentElement.dataset.surface = 'pipeline'))
onBeforeUnmount(() => delete document.documentElement.dataset.surface)
</script>
