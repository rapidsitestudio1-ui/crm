<template>
  <!-- One connected card: 1px gaps over a border-colored background draw the
       dividers, `shadow` (hairline ring + XS) draws the outer edge. Up to four
       per row; more wrap to a new row. -->
  <div
    class="grid gap-px overflow-hidden rounded-lg bg-[var(--outline-gray-1)] shadow"
    :style="{
      gridTemplateColumns: `repeat(${Math.min(items.length, 4)}, minmax(0, 1fr))`,
    }"
  >
    <KpiCard
      v-for="(item, i) in items"
      :key="item.name"
      segment
      :index="i"
      :name="item.name"
      :config="item.data"
      :tooltip="item.data.tooltip || item.tooltip"
    />
  </div>
</template>

<script setup>
import KpiCard from '@/components/Dashboard/KpiCard.vue'

defineProps({
  items: { type: Array, required: true },
})
</script>
