<template>
  <div class="h-full w-full">
    <KpiCard
      v-if="item.type == 'number_chart' && item.data"
      :key="index"
      :index="index"
      :name="item.name"
      :config="item.data"
      :tooltip="item.data.tooltip || item.tooltip"
    />
    <div
      v-else-if="item.type == 'spacer'"
      class="rounded bg-surface-base h-full overflow-hidden text-ink-gray-5 flex items-center justify-center"
      :class="editing ? 'border border-dashed border-outline-gray-2' : ''"
    >
      {{ editing ? __('Spacer') : '' }}
    </div>
    <div
      v-else-if="item.type == 'axis_chart'"
      class="h-full w-full rounded-md bg-surface-base shadow"
    >
      <AxisChart v-if="item.data" :config="withThemeColors(item.data)" />
    </div>
    <div
      v-else-if="item.type == 'donut_chart'"
      class="h-full w-full rounded-md bg-surface-base shadow overflow-hidden"
    >
      <DonutChart v-if="item.data" :config="withThemeColors(item.data)" />
    </div>
  </div>
</template>
<script setup>
import KpiCard from '@/components/Dashboard/KpiCard.vue'
import { AxisChart, DonutChart } from 'frappe-ui'

defineProps({
  index: { type: Number, required: true },
  item: { type: Object, required: true },
  editing: { type: Boolean, default: false },
})

// Chart palette comes from the theme (--chart-1..6 in theme.css); colors a
// chart config already sets still win.
function withThemeColors(config) {
  const style = getComputedStyle(document.documentElement)
  const colors = [1, 2, 3, 4, 5, 6]
    .map((i) => style.getPropertyValue(`--chart-${i}`).trim())
    .filter(Boolean)
  return colors.length ? { colors, ...config } : config
}
</script>
