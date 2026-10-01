<template>
  <!-- Mobile: compact contact list (tap opens the contact; Preview opens the drawer). -->
  <ul v-if="isMobileView" class="flex-1 overflow-y-auto bg-[var(--kb-card)]">
    <li v-for="row in rows" :key="row.name">
      <router-link :to="contactRoute(row)" class="ct-mobile-row">
        <KanbanAvatar
          :image="row.full_name?.image"
          :label="row.full_name?.label || row.name"
        />
        <span class="flex min-w-0 flex-1 flex-col">
          <span class="ct-name truncate">{{ row.full_name?.label || row.name }}</span>
          <span class="ct-sub truncate">
            {{ [row.company_name?.label, row.__email || row.__phone].filter(Boolean).join(' · ') }}
          </span>
        </span>
        <span
          v-if="row.__relationship"
          class="kb-badge"
          :class="badgeClass(row.__relationship)"
        >
          {{ row.__relationship.label }}
        </span>
        <button
          type="button"
          class="ct-preview"
          :aria-label="__('Preview {0}', [row.full_name?.label || row.name])"
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
      getRowRoute: contactRoute,
      // Two-line Contact cell (name + email) needs a taller row.
      rowHeight: 52,
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader
      class="mx-3 sm:mx-5"
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
      class="mx-3 sm:mx-5"
      :rows="rows"
      doctype="Contact"
    >
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <template #default="{ label }">
          <!-- Contact: avatar, name, email underneath, Preview on hover -->
          <div v-if="column.key === 'full_name'" class="relative flex w-full min-w-0 items-center gap-3">
            <KanbanAvatar
              :image="item?.image"
              :label="item?.label || row.name"
              size="sm"
            />
            <div class="flex min-w-0 flex-col">
              <span class="ct-name truncate">{{ item?.label || row.name }}</span>
              <span v-if="row.__email" class="ct-sub truncate">{{ row.__email }}</span>
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
            v-else-if="column.key === 'mobile_no' || column.key === 'phone'"
            class="ct-cell"
            @click="(event) => filterBy(event, idx, column, item)"
          >
            <template v-if="label">
              <LucidePhone />
              <span class="truncate">{{ label }}</span>
            </template>
          </div>

          <div
            v-else-if="column.key === 'company_name'"
            class="ct-cell"
            @click="(event) => filterBy(event, idx, column, item)"
          >
            <template v-if="item?.label">
              <KanbanAvatar :image="item.logo" :label="item.label" size="xs" square />
              <span class="truncate">{{ item.label }}</span>
            </template>
          </div>

          <div v-else-if="column.key === '__relationship'" class="ct-cell">
            <span v-if="item" class="kb-badge" :class="badgeClass(item)">
              {{ item.label }}
            </span>
          </div>

          <div v-else-if="column.key === '__owner' || column.key === 'owner'" class="ct-cell">
            <template v-if="ownerOf(item)">
              <KanbanAvatar
                :image="ownerOf(item).image"
                :label="ownerOf(item).label"
                size="xs"
              />
              <span class="truncate">{{ ownerOf(item).label }}</span>
            </template>
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
    class="border-t px-3 py-2 sm:px-5"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    doctype="Contact"
    :options="{
      hideAssign: true,
    }"
  />
</template>
<script setup>
import '@/components/Contacts/contacts.css'
import LucidePhone from '~icons/lucide/phone'
import LucidePanelRight from '~icons/lucide/panel-right'
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import RatingInput from '@/components/Controls/RatingInput.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import KanbanAvatar from '@/components/Kanban/KanbanAvatar.vue'
import { isMobileView } from '@/composables/settings'
import { isTranslatable, formatDuration } from '@/utils'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Tooltip,
  Dropdown,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
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
const { getUser } = usersStore()

const pageLengthCount = defineModel({ type: Number })
const list = defineModel('list', { type: Object })

function contactRoute(row) {
  return {
    name: 'Contact',
    params: { contactId: row.name },
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

function ownerOf(user) {
  if (!user) return null
  const u = typeof user === 'string' ? getUser(user) : user
  const label = u?.full_name || u?.label || user
  return label ? { label, image: u?.user_image || u?.image } : null
}

function badgeClass(rel) {
  return { success: 'is-success', accent: 'is-accent' }[rel?.tone] || ''
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
