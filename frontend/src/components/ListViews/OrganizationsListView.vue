<template>
  <!-- Mobile: compact list (tap opens the organization; Preview opens the drawer). -->
  <ul v-if="isMobileView" class="flex-1 overflow-y-auto bg-[var(--kb-card)]">
    <li v-for="row in rows" :key="row.name">
      <router-link :to="orgRoute(row)" class="ct-mobile-row">
        <KanbanAvatar
          :image="row.organization_name?.logo"
          :label="row.organization_name?.label || row.name"
          square
        />
        <span class="flex min-w-0 flex-1 flex-col">
          <span class="ct-name truncate">{{ row.organization_name?.label || row.name }}</span>
          <span class="ct-sub truncate">
            {{ [row.__industry, row.__website].filter(Boolean).join(' · ') }}
          </span>
        </span>
        <button
          type="button"
          class="ct-preview"
          :aria-label="__('Preview {0}', [row.organization_name?.label || row.name])"
          @click.stop.prevent="emit('preview', row.name)"
        >
          <LucidePanelRight class="size-3.5" />
        </button>
      </router-link>
    </li>
  </ul>

  <ListView
    v-else
    class="ct-table"
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: orgRoute,
      rowHeight: 56,
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader
      class="sm:mx-5 mx-3"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="(e) => onColumnWidthUpdated(e, column)"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghost"
          class="!h-4"
          @click="() => emit('applyLikeFilter')"
        >
          <HeartIcon
            class="h-4 w-4"
            :class="isLikeFilterApplied ? 'fill-red-500 text-red-500' : ''"
          />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows
      v-slot="{ idx, column, item, row }"
      :rows="rows"
      doctype="CRM Organization"
    >
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <template #default="{ label }">
          <!-- Organization: logo, name, website underneath, Preview on hover -->
          <div
            v-if="column.key === 'organization_name'"
            class="relative flex w-full min-w-0 items-center gap-3"
          >
            <KanbanAvatar
              :image="item?.logo"
              :label="item?.label || row.name"
              size="md"
              square
            />
            <div class="flex min-w-0 flex-col">
              <span class="ct-name truncate">{{ item?.label || row.name }}</span>
              <span v-if="row.__website" class="ct-sub truncate">{{ row.__website }}</span>
            </div>
            <button
              type="button"
              class="ct-preview is-floating"
              :aria-label="__('Preview {0}', [item?.label || row.name])"
              @click.stop.prevent="emit('preview', row.name)"
            >
              <LucidePanelRight class="size-3.5" />
              {{ __('Preview') }}
            </button>
          </div>

          <div
            v-else-if="column.key === 'industry'"
            class="ct-cell"
            @click="(event) => filterBy(event, idx, column, item)"
          >
            <span v-if="label" class="kb-badge">
              <span class="size-1.5 rounded-full" :style="{ background: industryDot(label) }" />
              {{ __(label) }}
            </span>
          </div>

          <!-- Counts open the preview, which lists the contacts / deals -->
          <div
            v-else-if="column.key === '__contacts' || column.key === '__open_deals'"
            class="ct-cell"
          >
            <button
              v-if="item"
              type="button"
              class="ov-count-btn"
              :aria-label="
                column.key === '__contacts'
                  ? __('{0} contacts at {1}, show', [item, row.organization_name?.label || row.name])
                  : __('{0} open deals with {1}, show', [item, row.organization_name?.label || row.name])
              "
              @click.stop.prevent="emit('preview', row.name)"
            >
              <component :is="column.key === '__contacts' ? LucideUsers : LucideHandshake" />
              {{ item }}
            </button>
            <span v-else-if="item === 0" class="is-muted" style="color: var(--kb-ink-3)">0</span>
          </div>

          <div
            v-else-if="column.key === 'annual_revenue'"
            class="ct-cell justify-end tabular-nums"
            :class="{ 'is-muted': !row.__revenue }"
            @click="(event) => filterBy(event, idx, column, item)"
          >
            <Tooltip v-if="!row.__revenue" :text="__('Not set (or 0)')">
              <span>—</span>
            </Tooltip>
            <span v-else>{{ row.__revenue }}</span>
          </div>

          <div
            v-else-if="['modified', 'creation'].includes(column.key)"
            class="ct-cell is-muted"
            @click="(event) => filterBy(event, idx, column, item)"
          >
            <Tooltip :text="item.label">
              <div class="truncate">{{ item.timeAgo }}</div>
            </Tooltip>
          </div>

          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-ink-gray-9"
            />
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              variant="ghost"
              @click.stop.prevent="
                () => emit('likeDoc', { name: row.name, liked: isLiked(item) })
              "
            >
              <HeartIcon
                class="h-4 w-4"
                :class="isLiked(item) ? 'fill-red-500 text-red-500' : ''"
              />
            </Button>
          </div>
          <RatingInput
            v-else-if="column.type === 'Rating'"
            :value="item"
            class="!opacity-100 flex-nowrap overflow-auto"
            :disabled="true"
            :max="column.options || 5"
            @click="(event) => filterBy(event, idx, column, item)"
          />
          <div
            v-else-if="label"
            class="ct-cell"
            @click="(event) => filterBy(event, idx, column, item)"
          >
            <span class="truncate">{{ getLabel(label, column) }}</span>
          </div>
        </template>
      </ListRowItem>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
        >
          <Button icon="lucide-more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    v-if="pageLengthCount"
    v-model="pageLengthCount"
    class="border-t sm:px-5 px-3 py-2"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    doctype="CRM Organization"
    :options="{
      hideAssign: true,
    }"
  />
</template>
<script setup>
import '@/components/Kanban/kanban.css'
import '@/components/Contacts/contacts.css'
import '@/components/Organizations/organizations.css'
import LucidePanelRight from '~icons/lucide/panel-right'
import LucideUsers from '~icons/lucide/users'
import LucideHandshake from '~icons/lucide/handshake'
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import RatingInput from '@/components/Controls/RatingInput.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import KanbanAvatar from '@/components/Kanban/KanbanAvatar.vue'
import { getStageTone } from '@/components/Kanban/stageTones'
import { isMobileView } from '@/composables/settings'
import { isTranslatable, formatDuration } from '@/utils'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Dropdown,
  Tooltip,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
  'preview',
])

const route = useRoute()

const pageLengthCount = defineModel({ type: Number })
const list = defineModel('list', { type: Object })

function orgRoute(row) {
  return {
    name: 'Organization',
    params: { organizationId: row.name },
    query: { view: route.query.view, viewType: route.params.viewType },
  }
}

function filterBy(event, idx, column, item) {
  emit('applyFilter', { event, idx, column, item, firstColumn: props.columns[0] })
}

function onColumnWidthUpdated({ width, save }, column) {
  column.width = width
  // Display columns can be relabelled copies; keep the saved view's in sync.
  if (column.__source) column.__source.width = width
  if (save) emit('columnWidthUpdated', column)
}

function industryDot(name) {
  return getStageTone('CRM Organization', { name }).dot
}

function getLabel(label, column) {
  if (column.type === 'Duration') return formatDuration(label)
  if (column.options && isTranslatable(column.options)) return __(label)
  return label
}

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>
