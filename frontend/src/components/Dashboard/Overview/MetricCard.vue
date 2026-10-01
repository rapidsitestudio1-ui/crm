<template>
  <div class="ov-card flex h-[122px] min-w-0 flex-col justify-center px-[18px]">
    <div class="flex h-8 items-center gap-3 pb-1">
      <div class="ov-chip size-7" :style="{ background: chipBg }">
        <img :src="icon" alt="" class="size-4" />
      </div>
      <span class="truncate text-[12px] leading-[18px]">{{ title }}</span>
    </div>
    <div class="flex items-end justify-between gap-3">
      <div class="flex min-w-0 flex-col">
        <p class="ov-big-value">{{ value }}</p>
        <div class="flex items-center gap-1 pt-[5px] text-[10px] leading-[15px]">
          <span
            class="flex items-center font-medium"
            :style="{ color: delta < 0 ? 'var(--ov-down)' : 'var(--ov-up)' }"
          >
            <img v-if="delta >= 0" :src="trendUpIcon" alt="" class="size-[11px]" />
            <LucideArrowDown v-else class="size-[11px]" />
            {{ Math.abs(delta) }}%
          </span>
          <span class="truncate" style="color: var(--ov-ink-muted)">
            {{ __('vs previous {0} days', [days]) }}
          </span>
        </div>
      </div>
      <Sparkline :series="series" :color="color" class="shrink-0" />
    </div>
  </div>
</template>

<script setup lang="ts">
import LucideArrowDown from '~icons/lucide/arrow-down'
import Sparkline from './Sparkline.vue'
import trendUpIcon from './assets/trend-up.svg'

defineProps<{
  title: string
  value: string
  delta: number
  days: number
  series: number[]
  icon: string
  chipBg: string
  color: string
}>()
</script>
