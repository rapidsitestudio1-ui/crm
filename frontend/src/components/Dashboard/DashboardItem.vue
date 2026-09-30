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
    <template v-else-if="['axis_chart', 'donut_chart'].includes(item.type)">
      <ChartCard
        v-if="item.data"
        :name="item.name"
        :type="item.type"
        :config="item.data"
      />
      <div v-else class="h-full w-full rounded-lg bg-surface-base shadow" />
    </template>
  </div>
</template>
<script setup>
import KpiCard from '@/components/Dashboard/KpiCard.vue'
import ChartCard from '@/components/Dashboard/ChartCard.vue'

defineProps({
  index: { type: Number, required: true },
  item: { type: Object, required: true },
  editing: { type: Boolean, default: false },
})
</script>
