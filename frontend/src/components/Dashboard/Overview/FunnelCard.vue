<template>
  <section class="ov-card flex min-w-0 flex-col px-[18px] pb-4 pt-[15px]">
    <CardHeading
      :title="__('Funnel conversion')"
      :info="__('Leads and deals created in the period, by how far they have progressed.')"
    />
    <div class="flex items-center gap-[23px] pt-[23px]">
      <div
        class="relative h-[167px] w-[173px] min-w-[105px] shrink overflow-hidden"
        role="img"
        :aria-label="ariaLabel"
      >
        <div v-for="(layer, i) in LAYERS" :key="i" class="absolute" :style="layer.inset">
          <img :src="layer.src" alt="" class="absolute inset-0 block size-full max-w-none" />
        </div>
      </div>
      <div class="flex min-w-0 flex-1 flex-col gap-[17px]">
        <div
          v-for="(stage, i) in data"
          :key="stage.stage"
          class="grid grid-cols-[minmax(0,1fr)_28px_44px] items-center gap-3 text-[11px] leading-[16.5px]"
        >
          <span class="flex min-w-0 items-center gap-[10px]">
            <span class="size-[9px] shrink-0 rounded-full" :style="{ background: DOTS[i] }" />
            <span class="truncate">{{ __(stage.stage) }}</span>
          </span>
          <span style="color: var(--ov-ink-count)">{{ formatCount(stage.count) }}</span>
          <span class="text-right font-medium" style="color: var(--ov-ink-pct)">
            {{ pct(stage.count) }}%
          </span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import CardHeading from './CardHeading.vue'
import { formatCount } from './utils'
import funnel1 from './assets/funnel-1.svg'
import funnel2 from './assets/funnel-2.svg'
import funnel3 from './assets/funnel-3.svg'
import funnel4 from './assets/funnel-4.svg'
import funnel5 from './assets/funnel-5.svg'

const props = defineProps<{ data: { stage: string; count: number }[] }>()

const DOTS = ['#625bff', '#7e9aff', '#62adff', '#1ac894', '#1ac894']

// Layer positions from the Figma funnel image (173x167), as top/right/bottom/left insets.
const LAYERS = [
  { src: funnel1, inset: { top: '0', right: '0.25%', bottom: '80.24%', left: '-0.29%' } },
  { src: funnel2, inset: { top: '22.16%', right: '10.4%', bottom: '59.28%', left: '10.4%' } },
  { src: funnel3, inset: { top: '43.11%', right: '19.58%', bottom: '39.52%', left: '19.65%' } },
  { src: funnel4, inset: { top: '62.87%', right: '29.09%', bottom: '19.76%', left: '29.31%' } },
  { src: funnel5, inset: { top: '82.63%', right: '37.82%', bottom: '0', left: '37.82%' } },
]

const top = computed(() => props.data[0]?.count || 0)
function pct(count: number) {
  return top.value ? Math.round((count / top.value) * 100) : 0
}

const ariaLabel = computed(() => {
  const last = props.data[props.data.length - 1]
  return __('Conversion funnel, {0} leads to {1} won deals', [top.value, last?.count || 0])
})
</script>
