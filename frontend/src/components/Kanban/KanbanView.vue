<template>
  <div class="kb-board flex h-full overflow-x-auto" :class="{ 'is-dragging': dragging }">
    <Draggable
      v-if="columns"
      :list="columns"
      item-key="column"
      :delay="isTouchScreenDevice() ? 200 : 0"
      ghost-class="opacity-40"
      class="flex gap-3 px-4 pb-4 pt-4"
      @end="updateColumn"
    >
      <template #item="{ element: column }">
        <section
          v-if="!column.column.delete"
          class="kb-column"
          :class="{ 'is-drop-target': dragging && overColumn === column.column.name }"
          :aria-label="column.column.name"
        >
          <header
            class="kb-column-header"
            :style="{
              '--kb-tone-bg': toneOf(column).bg,
              '--kb-tone-ink': toneOf(column).ink,
              '--kb-tone-dot': toneOf(column).dot,
            }"
          >
            <Popover>
              <template #target="{ togglePopover }">
                <button
                  type="button"
                  class="kb-icon-btn !size-5 -ml-1"
                  :aria-label="__('Change {0} color', [column.column.name])"
                  @click="togglePopover"
                >
                  <span
                    class="size-2 rounded-full"
                    :style="{ background: toneOf(column).dot }"
                  />
                </button>
              </template>
              <template #body>
                <div
                  class="flex flex-col gap-3 px-3 py-2.5 min-w-40 rounded-lg bg-surface-elevation-2 shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
                >
                  <div class="flex gap-1">
                    <Button
                      v-for="color in colors"
                      :key="color"
                      variant="ghost"
                      @click="() => pickColor(column, color)"
                    >
                      <IndicatorIcon :class="parseColor(color)" />
                    </Button>
                  </div>
                  <div class="flex flex-row-reverse">
                    <Button
                      variant="solid"
                      :label="__('Apply')"
                      @click="updateColumn"
                    />
                  </div>
                </div>
              </template>
            </Popover>
            <span class="kb-column-name">{{ __(column.column.name) }}</span>
            <span class="kb-count" :aria-label="__('{0} records', [countOf(column)])">
              {{ countOf(column) }}
            </span>
            <span class="flex-1" />
            <Dropdown :options="actions(column)">
              <template #default>
                <button
                  type="button"
                  class="kb-icon-btn kb-reveal"
                  :aria-label="__('{0} column options', [column.column.name])"
                >
                  <LucideMoreHorizontal class="size-4" />
                </button>
              </template>
            </Dropdown>
            <button
              type="button"
              class="kb-icon-btn"
              :aria-label="__('Add to {0}', [column.column.name])"
              @click="options.onNewClick(column)"
            >
              <LucidePlus class="size-4" />
            </button>
          </header>

          <div class="flex h-full flex-col overflow-y-auto">
            <Draggable
              :list="column.data"
              group="fields"
              item-key="name"
              class="kb-cards"
              :delay="isTouchScreenDevice() ? 200 : 0"
              :data-column="column.column.name"
              :force-fallback="true"
              :fallback-tolerance="4"
              ghost-class="kb-ghost"
              drag-class="kb-drag"
              fallback-class="kb-drag"
              :scroll-sensitivity="96"
              :scroll-speed="14"
              :bubble-scroll="true"
              :move="onMove"
              @start="onDragStart"
              @end="onDragEnd"
            >
              <template #item="{ element: fields }">
                <component
                  :is="options.getRoute ? 'router-link' : 'div'"
                  class="kb-card"
                  :data-name="fields.name"
                  v-bind="{
                    to: options.getRoute ? options.getRoute(fields) : undefined,
                    onClick: options.onClick
                      ? () => options.onClick(fields)
                      : undefined,
                  }"
                >
                  <slot
                    v-if="$slots['card-header']"
                    name="card-header"
                    v-bind="{ fields, column, titleField, itemName: fields.name }"
                  />
                  <slot
                    v-else
                    name="title"
                    v-bind="{ fields, titleField, itemName: fields.name }"
                  >
                    <div class="kb-title truncate">
                      {{ fields[titleField] || __('No Title') }}
                    </div>
                  </slot>

                  <!-- Fields chosen in Kanban settings that the card header
                       doesn't already show, as a label / value list. -->
                  <div v-if="extraFields(column, fields).length" class="kb-props">
                    <template v-for="value in extraFields(column, fields)" :key="value">
                      <span class="kb-prop-label truncate">{{ fieldLabel(value) }}</span>
                      <span class="kb-prop-value truncate">
                        <slot
                          name="fields"
                          v-bind="{ fields, fieldName: value, itemName: fields.name }"
                        >
                          {{ fields[value] }}
                        </slot>
                      </span>
                    </template>
                  </div>

                  <slot
                    v-if="$slots['card-footer']"
                    name="card-footer"
                    v-bind="{ fields, column, itemName: fields.name }"
                  />
                  <slot v-else name="actions" v-bind="{ itemName: fields.name }" />
                </component>
              </template>
            </Draggable>
            <button
              v-if="column.column.count < column.column.all_count"
              type="button"
              class="kb-load-more mx-0.5 mb-2"
              @click="emit('loadMore', column.column.name)"
            >
              {{ __('Load more') }}
              <span class="text-[11.5px]" style="color: var(--kb-ink-3)">
                · {{ column.column.all_count - column.column.count }}
              </span>
            </button>
          </div>
        </section>
      </template>
    </Draggable>
    <div class="shrink-0 min-w-64 pt-4 pr-4">
      <Combobox
        :model-value="null"
        :options="deletedColumns"
        @update:selected-option="(e) => addColumn(e)"
      >
        <template #trigger="{ open, setOpen }">
          <button
            type="button"
            class="kb-load-more flex w-full items-center justify-center gap-1.5"
            @click="setOpen(!open)"
          >
            <LucidePlus class="size-3.5" />
            {{ __('Add Column') }}
          </button>
        </template>
        <template #footer>
          <Button
            class="w-full"
            :label="__('Reload Columns')"
            :iconLeft="RefreshIcon"
            @click="updateColumn(null, true)"
          />
        </template>
      </Combobox>
    </div>
  </div>
</template>
<script setup>
import './kanban.css'
import LucidePlus from '~icons/lucide/plus'
import LucideMoreHorizontal from '~icons/lucide/more-horizontal'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { isTouchScreenDevice, colors, parseColor } from '@/utils'
import Draggable from 'vuedraggable'
import { Combobox, Dropdown, Popover } from 'frappe-ui'
import { computed, ref } from 'vue'
import { getStageTone } from './stageTones'

const props = defineProps({
  options: {
    type: Object,
    default: () => ({
      getRoute: null,
      onClick: null,
      onNewClick: null,
      // 'CRM Lead' | 'CRM Deal', for stage colors
      doctype: '',
      // (column) => status record { type, position }, for stage colors
      getStatus: null,
      // Fields the page's card header/footer already shows
      cardFields: [],
    }),
  },
})

const emit = defineEmits(['update', 'loadMore'])

const kanban = defineModel({ type: Object })

const titleField = computed(() => {
  return kanban.value?.data?.title_field
})

const columns = computed(() => {
  if (!kanban.value?.data?.data || kanban.value.data.view_type != 'kanban')
    return []
  let _columns = kanban.value.data.data

  let has_color = _columns.some((column) => column.column?.color)
  if (!has_color) {
    _columns.forEach((column, i) => {
      column.column['color'] = colors[i % colors.length]
    })
  }
  return _columns
})

const deletedColumns = computed(() => {
  const _columns = kanban.value?.data?.kanban_columns || []
  return _columns
    ?.filter((col) => col['delete'])
    .map((col) => {
      return { label: col.name, value: col.name }
    })
})

// ---- Presentation helpers (custom) ----

function toneOf(column) {
  return getStageTone(
    props.options.doctype,
    column.column,
    props.options.getStatus?.(column.column.name),
  )
}

function countOf(column) {
  return column.column.all_count ?? column.data?.length ?? 0
}

function fieldLabel(fieldname) {
  const f = kanban.value?.data?.fields?.find((x) => x.fieldname === fieldname)
  if (fieldname === '_assign') return __('Assigned to')
  if (fieldname === 'modified') return __('Updated')
  return f?.label || fieldname
}

// Empty and zero values are skipped so cards don't fill up with "0,00" / "—".
function isEmpty(v) {
  return v == null || v === '' || v === 0 || v === '0' || v === '[]'
}

function extraFields(column, row) {
  const shown = new Set([titleField.value, ...(props.options.cardFields || [])])
  return (column.fields || []).filter((f) => !shown.has(f) && !isEmpty(row?.[f]))
}

// The color picker keeps working; a picked color overrides the stage color.
function pickColor(column, color) {
  column.column.color = color
  column.column.color_custom = true
}

// ---- Drag feedback (custom) ----

const dragging = ref(false)
const overColumn = ref(null)

function onDragStart(evt) {
  dragging.value = true
  overColumn.value = evt.from?.dataset.column || null
}
function onMove(evt) {
  overColumn.value = evt.to?.dataset.column || overColumn.value
  return true
}
function onDragEnd(evt) {
  dragging.value = false
  overColumn.value = null
  updateColumn(evt)
}

function actions(column) {
  return [
    {
      group: __('Options'),
      hideLabel: true,
      items: [
        {
          label: __('Use stage color'),
          icon: 'droplet',
          condition: () => Boolean(column.column.color_custom),
          onClick: () => {
            delete column.column.color_custom
            updateColumn()
          },
        },
        {
          label: __('Delete'),
          icon: 'trash-2',
          onClick: () => {
            column.column['delete'] = true
            updateColumn()
          },
        },
      ],
    },
  ]
}

function addColumn(e) {
  let column = columns.value.find((col) => col.column.name == e.value)
  column.column['delete'] = false
  columns.value.splice(columns.value.indexOf(column), 1)
  columns.value.push(column)
  updateColumn()
}

function updateColumn(d, fetchNewColumns = false) {
  let toColumn = d?.to?.dataset.column
  let fromColumn = d?.from?.dataset.column
  let itemName = d?.item?.dataset.name

  let _columns = []
  columns.value.forEach((col) => {
    col.column['order'] = col.data.map((d) => d.name)
    if (col.column.page_length) {
      delete col.column.page_length
    }
    _columns.push(col.column)
  })

  let data = { kanban_columns: _columns, fetchNewColumns }

  if (toColumn != fromColumn) {
    data = { item: itemName, to: toColumn, kanban_columns: _columns }
  }

  emit('update', data)
}
</script>
