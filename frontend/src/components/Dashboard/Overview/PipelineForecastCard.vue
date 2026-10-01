<template>
  <section class="ov-card flex min-w-0 flex-col px-[18px] pb-[17px] pt-[17px]">
    <CardHeading
      :title="__('Pipeline forecast')"
      :info="__('Open deals by expected close month, weighted by their probability.')"
    >
      <SelectButton v-model="months" :options="monthOptions" />
    </CardHeading>
    <p class="ov-subtitle -mt-[5px]">
      {{ __('Expected revenue based on current deals.') }}
    </p>
    <p class="ov-big-value pt-1">{{ formatMoney(total, currency) }}</p>
    <p class="ov-subtitle pt-px">{{ __('Total expected value') }}</p>

    <div ref="wrap" class="pt-[7px]">
      <svg :width="width" height="104" class="block overflow-visible" role="img" :aria-label="__('Pipeline forecast chart')">
        <defs>
          <linearGradient :id="gradientId" x1="0" y1="0" x2="0" y2="1">
            <stop stop-color="#8b80ff" />
            <stop offset="1" stop-color="#bfb8f4" />
          </linearGradient>
        </defs>
        <g stroke="var(--ov-grid)">
          <line
            v-for="t in gridTicks"
            :key="`g${t}`"
            :x1="L"
            :x2="width"
            :y1="y(t)"
            :y2="y(t)"
          />
        </g>
        <path
          v-for="(d, i) in data"
          :key="d.month"
          :d="barPath(i, d.value)"
          :fill="`url(#${gradientId})`"
        >
          <title>{{ dayjs(d.month + '-01').format('MMMM YYYY') }}: {{ formatMoney(d.value, currency) }}</title>
        </path>
        <g font-size="10" fill="var(--ov-ink-axis)">
          <text
            v-for="t in yTicks.slice(1)"
            :key="`l${t}`"
            x="27"
            :y="y(t) + 3.5"
            text-anchor="end"
          >
            {{ formatCompact(t) }}
          </text>
        </g>
      </svg>
    </div>

    <div class="pl-[35px]">
      <div
        class="flex border-t pt-2 text-[11px] leading-4"
        style="border-color: var(--ov-divider)"
      >
        <div v-for="d in data" :key="`m${d.month}`" class="flex min-w-0 flex-1 flex-col items-center">
          <span>{{ dayjs(d.month + '-01').format('MMM') }}</span>
          <span class="font-semibold">{{ formatCompact(d.value, currency) }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { dayjs } from 'frappe-ui'
import { useElementSize } from '@vueuse/core'
import { computed, ref, useId } from 'vue'
import CardHeading from './CardHeading.vue'
import SelectButton from './SelectButton.vue'
import { formatCompact, formatMoney, niceTicks } from './utils'

const props = defineProps<{ data: { month: string; value: number }[]; currency: string }>()
const months = defineModel<number>('months', { required: true })

const monthOptions = [3, 4, 6, 12].map((n) => ({ label: __('Next {0} months', [n]), value: n }))

const gradientId = `ov-forecast-${useId()}`
const wrap = ref<HTMLElement>()
const { width: measured } = useElementSize(wrap)
const width = computed(() => Math.max(measured.value - 6, 200))

// Plot frame from the Figma chart: 35px left gutter, y 3..104, 48px bars.
const L = 35
const T = 3
const B = 104
const BAR = 48

const total = computed(() => props.data.reduce((a, d) => a + (d.value || 0), 0))
const yTicks = computed(() => {
  const max = Math.max(0, ...props.data.map((d) => d.value))
  return max ? niceTicks(max, 4) : [0, 10000, 20000, 30000, 40000]
})
// Figma draws a grid line at every other tick (0, 20K, 40K).
const gridTicks = computed(() => yTicks.value.filter((_, i) => i % 2 === 0))
const yMax = computed(() => yTicks.value[yTicks.value.length - 1])
const y = (v: number) => B - ((B - T) * v) / yMax.value

function barPath(i: number, value: number) {
  const band = (width.value - L) / props.data.length
  const w = Math.min(BAR, band * 0.7)
  const x0 = L + band * i + (band - w) / 2
  const top = y(value)
  const h = B - top
  if (h <= 0) return ''
  const r = Math.min(3, h, w / 2)
  return `M${x0},${B}V${top + r}Q${x0},${top} ${x0 + r},${top}H${x0 + w - r}Q${x0 + w},${top} ${x0 + w},${top + r}V${B}Z`
}
</script>
