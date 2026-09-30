<template>
  <div class="flex-1 overflow-y-auto p-3">
    <!-- Outside edit mode, number charts render as one connected KPI strip
         (Figma "KPI Card" row) above the grid, in layout order. -->
    <div v-if="!editing && kpiItems.length" class="px-2 pb-5 pt-2.5">
      <KpiStrip :items="kpiItems" />
    </div>
    <GridLayout
      v-if="gridItems.length > 0"
      class="h-fit w-full"
      :class="[editing ? 'mb-[20rem] !select-none' : '']"
      :cols="20"
      :rowHeight="42"
      :disabled="!editing"
      :modelValue="gridItems.map((item) => item.layout)"
      @update:modelValue="
        (newLayout) => {
          gridItems.forEach((item, idx) => {
            item.layout = newLayout[idx]
          })
        }
      "
    >
      <template #item="{ index }">
        <div class="group relative flex h-full w-full p-2 text-ink-gray-8">
          <div
            class="flex h-full w-full items-center justify-center"
            :class="
              editing
                ? 'pointer-events-none  [&>div:first-child]:rounded [&>div:first-child]:group-hover:ring-2 [&>div:first-child]:group-hover:ring-outline-gray-2'
                : ''
            "
          >
            <DashboardItem
              :index="index"
              :item="gridItems[index]"
              :editing="editing"
            />
          </div>
          <div
            v-if="editing"
            class="flex absolute right-0 top-0 bg-surface-gray-9 rounded cursor-pointer opacity-0 group-hover:opacity-100"
          >
            <div
              class="rounded p-1 hover:bg-surface-gray-8"
              @click="items.splice(items.indexOf(gridItems[index]), 1)"
            >
              <span
                class="lucide-trash-2 size-3 text-ink-base"
                aria-hidden="true"
              />
            </div>
          </div>
        </div>
      </template>
    </GridLayout>
  </div>
</template>
<script setup>
import KpiStrip from '@/components/Dashboard/KpiStrip.vue'
import { GridLayout } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  editing: { type: Boolean, default: false },
})

const items = defineModel({ type: Array, default: () => [] })

const byPosition = (a, b) => a.layout.y - b.layout.y || a.layout.x - b.layout.x

const kpiItems = computed(() =>
  items.value
    .filter((item) => item.type === 'number_chart' && item.data)
    .sort(byPosition),
)

// Editing keeps every item in the grid so number cards can still be moved,
// resized and removed; otherwise they live in the strip above.
const gridItems = computed(() =>
  props.editing
    ? items.value
    : items.value.filter((item) => item.type !== 'number_chart'),
)
</script>
