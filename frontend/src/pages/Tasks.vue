<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Tasks" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="tasksListView?.customListActions"
        :actions="tasksListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="createTask"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="tasks"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Task"
    :options="{
      allowedViews: ['list', 'kanban'],
    }"
  />
  <KanbanView
    v-if="$route.params.viewType == 'kanban' && rows.length"
    v-model="tasks"
    :options="{
      onClick: (row) => showTask(row.name),
      onNewClick: (column) => createTask(column),
      doctype: 'CRM Task',
      cardFields: taskCardFields,
    }"
    @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
  >
    <!-- Custom: cards share the contact card's layout (kanban.css). -->
    <template #card-header="{ fields }">
      <div class="flex flex-col gap-2.5">
        <div class="flex items-start gap-2.5">
          <TaskStatusIcon
            class="mt-0.5 size-4 shrink-0"
            :status="task(fields).status"
          />
          <span class="kb-title line-clamp-2 min-w-0 flex-1">
            {{ task(fields).title || __('No Title') }}
          </span>
          <div class="kb-reveal -mr-1.5 -mt-0.5 shrink-0" @click.stop.prevent>
            <Dropdown :options="actions(fields.name)" placement="right">
              <button
                type="button"
                class="kb-icon-btn"
                :aria-label="__('Quick actions')"
              >
                <LucideMoreHorizontal class="size-4" />
              </button>
            </Dropdown>
          </div>
        </div>

        <p
          v-if="plainText(task(fields).description)"
          class="kb-subtitle line-clamp-2 -mt-1"
        >
          {{ plainText(task(fields).description) }}
        </p>

        <div
          v-if="task(fields).due_date || task(fields).reference_docname"
          class="flex flex-col gap-1"
        >
          <div
            v-if="task(fields).due_date"
            class="kb-meta"
            :class="{ 'is-overdue': isOverdue(task(fields)) }"
          >
            <LucideCalendar />
            <Tooltip :text="formatDate(task(fields).due_date, 'ddd, MMM D, YYYY h:mm a')">
              <span class="truncate">
                {{ dueLabel(task(fields)) }}
              </span>
            </Tooltip>
          </div>
          <button
            v-if="task(fields).reference_docname"
            type="button"
            class="kb-meta kb-ref"
            @click.stop.prevent="
              redirect(task(fields).reference_doctype, task(fields).reference_docname)
            "
          >
            <LucideArrowUpRight />
            <span class="truncate">
              {{ task(fields).reference_doctype == 'CRM Deal' ? __('Deal') : __('Lead') }}
              ·
              {{ referenceTitle(task(fields)) }}
            </span>
          </button>
        </div>

        <div v-if="task(fields).priority" class="flex flex-wrap items-center gap-1.5">
          <span class="kb-badge" :class="priorityClass(task(fields).priority)">
            <TaskPriorityIcon class="!size-2" :priority="task(fields).priority" />
            {{ __(task(fields).priority) }}
          </span>
        </div>
      </div>
    </template>
    <template #card-footer="{ fields }">
      <KanbanCardFooter
        :assignees="assigneesOf(task(fields).assigned_to)"
        :time="timestampCell(task(fields).modified).timeAgo"
        :timeTitle="timestampCell(task(fields).modified).label"
      />
    </template>
    <template #fields="{ fieldName, itemName }">
      {{ getRow(itemName, fieldName).timeAgo || getRow(itemName, fieldName).label }}
    </template>
  </KanbanView>
  <TasksListView
    v-else-if="tasks.data && rows.length"
    ref="tasksListView"
    v-model="tasks.data.page_length_count"
    v-model:list="tasks"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: tasks.data.row_count,
      totalCount: tasks.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @showTask="showTask"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="tasks.data && !rows.length"
    name="Tasks"
    :icon="Email2Icon"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteTaskModal"
    v-model="showDeleteTaskModal"
    name="Tasks"
    doctype="CRM Task"
    :docname="taskToDelete"
    :reload="() => tasks.reload()"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import TasksListView from '@/components/ListViews/TasksListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import KanbanCardFooter from '@/components/Kanban/KanbanCardFooter.vue'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import LucideMoreHorizontal from '~icons/lucide/more-horizontal'
import LucideCalendar from '~icons/lucide/calendar'
import LucideArrowUpRight from '~icons/lucide/arrow-up-right'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useKanbanExtras } from '@/composables/useKanbanExtras'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { Tooltip, Dropdown, call, dayjsLocal } from 'frappe-ui'
import {
  computed,
  ref,
  reactive,
  watch,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import { useRouter } from 'vue-router'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Task')
const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

const router = useRouter()

const tasksListView = ref(null)

// tasks data is loaded in the ViewControls component
const tasks = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const showDeleteTaskModal = ref(false)
const taskToDelete = ref(null)

// ---- Kanban cards (custom): same look as the contact cards ----

onMounted(() => (document.documentElement.dataset.surface = 'pipeline'))
onBeforeUnmount(() => delete document.documentElement.dataset.surface)

// Fields the card shows itself, so they're not repeated as label/value rows.
const taskCardFields = [
  'title',
  'description',
  'status',
  'priority',
  'due_date',
  'assigned_to',
  'reference_doctype',
  'reference_docname',
  'modified',
  'creation',
]

// The board only fetches the fields chosen in Kanban settings.
const extras = useKanbanExtras(
  'CRM Task',
  () => {
    const d = tasks.value?.data
    if (d?.view_type !== 'kanban' || !d.data?.length) return null
    return d.data.flatMap((col) => (col.data || []).map((t) => t.name))
  },
  taskCardFields,
)

function task(fields) {
  return { ...extras[fields.name], ...fields }
}

// Lead / deal names for the reference line.
const refTitles = reactive({})
watch(
  () => Object.values(extras),
  async (rows) => {
    const byDoctype = { 'CRM Lead': [], 'CRM Deal': [] }
    for (const t of rows) {
      const key = `${t.reference_doctype}:${t.reference_docname}`
      if (byDoctype[t.reference_doctype] && !(key in refTitles)) {
        byDoctype[t.reference_doctype].push(t.reference_docname)
        refTitles[key] = ''
      }
    }
    const fieldsFor = {
      'CRM Lead': ['name', 'lead_name', 'organization'],
      'CRM Deal': ['name', 'organization', 'lead_name'],
    }
    for (const [doctype, names] of Object.entries(byDoctype)) {
      if (!names.length) continue
      try {
        const docs = await call('frappe.client.get_list', {
          doctype,
          filters: { name: ['in', names] },
          fields: fieldsFor[doctype],
          limit_page_length: names.length,
        })
        for (const d of docs || []) {
          refTitles[`${doctype}:${d.name}`] =
            doctype === 'CRM Deal'
              ? d.organization || d.lead_name
              : d.lead_name || d.organization
        }
      } catch {
        // Falls back to the record ID.
      }
    }
  },
)

function referenceTitle(t) {
  return refTitles[`${t.reference_doctype}:${t.reference_docname}`] || t.reference_docname
}

function plainText(html) {
  if (!html) return ''
  const doc = new DOMParser().parseFromString(html, 'text/html')
  return (doc.body.textContent || '').replace(/\s+/g, ' ').trim()
}

function isOverdue(t) {
  return (
    t.due_date &&
    !['Done', 'Canceled'].includes(t.status) &&
    dayjsLocal(t.due_date).isBefore(dayjsLocal())
  )
}

function dueLabel(t) {
  const due = dayjsLocal(t.due_date)
  const today = dayjsLocal().startOf('day')
  const days = due.startOf('day').diff(today, 'day')
  const hasTime = due.format('HH:mm') !== '00:00'
  const time = hasTime ? `, ${due.format('h:mm a')}` : ''
  if (days === 0) return __('Today') + time
  if (days === 1) return __('Tomorrow') + time
  if (days === -1) return __('Yesterday') + time
  return due.format(due.year() === today.year() ? 'MMM D' : 'MMM D, YYYY') + time
}

function priorityClass(priority) {
  return { High: 'is-danger', Medium: 'is-warning' }[priority] || ''
}

function assigneesOf(user) {
  const u = user && getUser(user)
  return u?.full_name ? [{ label: u.full_name, image: u.user_image }] : []
}

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object') {
      return value
    }
    return { label: value }
  }
  return getValue(rows.value?.find((row) => row.name == name)[field])
}

const rows = computed(() => {
  if (!tasks.value?.data?.data) return []

  if (tasks.value.data.view_type === 'kanban') {
    return getKanbanRows(tasks.value.data.data, tasks.value.data.fields)
  }

  openTaskFromURL()
  return parseRows(tasks.value?.data.data, tasks.value?.data.columns)
})

const columns = computed(() => {
  let _columns = tasks.value?.data?.columns || []

  // Set align right for last column
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
  let view_type = tasks.value.data.view_type
  let key = view_type === 'kanban' ? 'fieldname' : 'key'
  let type = view_type === 'kanban' ? 'fieldtype' : 'type'

  return rows.map((task) => {
    let _rows = {}
    tasks.value?.data.rows.forEach((row) => {
      _rows[row] = task[row]

      let fieldType = columns?.find((col) => (col[key] || col.value) == row)?.[
        type
      ]

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation', 'due_date'].includes(row)
      ) {
        _rows[row] = formatDate(task[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, task)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, task)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, task)
      }

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(task[row])
      } else if (row == 'assigned_to') {
        _rows[row] = {
          label: task.assigned_to && getUser(task.assigned_to).full_name,
          ...(task.assigned_to && getUser(task.assigned_to)),
        }
      }
    })
    return _rows
  })
}

const { showModal } = useDoctypeModal()

const taskCallbacks = {
  afterInsert: () => {
    tasks.value.reload()
    updateOnboardingStep('create_first_task')
    capture('task_created')
  },
  afterUpdate: () => {
    tasks.value.reload()
    capture('task_updated')
  },
}

function showTask(name) {
  showModal({
    name,
    doctype: 'CRM Task',
    title: 'Task',
    callbacks: taskCallbacks,
  })
}

function createTask(column) {
  const defaults = { status: 'Backlog', priority: 'Low' }

  if (column?.column?.name) {
    let column_field = tasks.value.params.column_field
    if (column_field) {
      defaults[column_field] = column.column.name
    }
  }

  showModal({
    doctype: 'CRM Task',
    title: 'Task',
    defaults: defaults,
    callbacks: taskCallbacks,
  })
}

function actions(name) {
  return [
    {
      label: __('Edit'),
      icon: 'edit-2',
      onClick: () => showTask(name),
    },
    {
      label: __('Delete'),
      icon: 'trash-2',
      onClick: () => {
        taskToDelete.value = name
        showDeleteTaskModal.value = true
      },
    },
  ]
}

function redirect(doctype, docname) {
  if (!docname) return
  let name = doctype == 'CRM Deal' ? 'Deal' : 'Lead'
  let params = { leadId: docname }
  if (name == 'Deal') {
    params = { dealId: docname }
  }
  router.push({ name: name, params: params })
}

const openTaskFromURL = () => {
  const searchParams = new URLSearchParams(window.location.search)
  const taskName = searchParams.get('open')

  if (taskName && rows.value?.length) {
    showTask(parseInt(taskName))
    searchParams.delete('open')
    window.history.replaceState(null, '', window.location.pathname)
  }
}
</script>
