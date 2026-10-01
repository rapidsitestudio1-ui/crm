<template>
  <section class="ov-card flex min-w-0 flex-col px-[18px] pb-[17px] pt-[17px]">
    <CardHeading
      :title="__('Sales trend')"
      :info="__('Leads and deals created, and deals won, per day.')"
    >
      <SelectButton v-model="days" :options="periodOptions" />
    </CardHeading>
    <p class="ov-subtitle -mt-[5px]">
      {{ __('New leads, deals and won deals over time.') }}
    </p>

    <div ref="wrap" class="relative pt-[15px]" @mouseleave="hover = null">
      <svg
        :width="width"
        height="164"
        class="block overflow-visible"
        role="img"
        :aria-label="__('Sales trend chart')"
        @mousemove="onMove"
      >
        <defs>
          <linearGradient
            v-for="s in SERIES"
            :id="`${uid}-${s.key}`"
            :key="s.key"
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <stop :stop-color="s.color" stop-opacity="0.22" />
            <stop offset="1" :stop-color="s.color" stop-opacity="0.015" />
          </linearGradient>
        </defs>

        <g stroke="var(--ov-grid)" stroke-width="0.7">
          <line v-for="t in yTicks" :key="`h${t}`" :x1="L" :x2="R" :y1="y(t)" :y2="y(t)" />
          <line v-for="(i, n) in xTickIdx" :key="`v${n}`" :x1="x(i)" :x2="x(i)" :y1="T" :y2="B" />
          <line :x1="R" :x2="R" :y1="T" :y2="B" />
        </g>

        <g v-for="s in SERIES" :key="s.key">
          <path :d="areas[s.key]" :fill="`url(#${uid}-${s.key})`" fill-opacity="0.6" />
          <path :d="lines[s.key]" :stroke="s.color" :stroke-width="s.width" fill="none" />
        </g>

        <g font-size="10" fill="var(--ov-ink-axis)">
          <text v-for="t in yTicks" :key="`yl${t}`" x="23" :y="y(t) + 3.5" text-anchor="end">
            {{ formatCompact(t) }}
          </text>
          <text
            v-for="(i, n) in xTickIdx"
            :key="`xl${n}`"
            :x="x(i)"
            y="155"
            text-anchor="middle"
          >
            {{ dayjs(data[i]?.date).format('MMM D') }}
          </text>
        </g>

        <g v-if="hover !== null">
          <line
            :x1="x(hover)"
            :x2="x(hover)"
            :y1="T"
            :y2="B"
            stroke="var(--ov-ink-axis)"
            stroke-dasharray="3 3"
            stroke-width="0.8"
          />
          <circle
            v-for="s in SERIES"
            :key="`dot${s.key}`"
            :cx="x(hover)"
            :cy="y(data[hover][s.key])"
            r="3"
            :fill="s.color"
            stroke="var(--ov-card)"
            stroke-width="1.5"
          />
        </g>
      </svg>

      <div
        v-if="hover !== null"
        class="ov-chart-tooltip"
        :style="{
          top: '8px',
          left: x(hover) > width / 2 ? 'auto' : `${x(hover) + 12}px`,
          right: x(hover) > width / 2 ? `${width - x(hover) + 12}px` : 'auto',
        }"
      >
        <div class="mb-1 font-semibold">{{ dayjs(data[hover].date).format('ddd, MMM D') }}</div>
        <div v-for="s in SERIES" :key="`tt${s.key}`" class="flex items-center gap-2">
          <span class="size-2 rounded-full" :style="{ background: s.color }" />
          <span class="flex-1">{{ s.label }}</span>
          <span class="font-semibold">{{ data[hover][s.key] }}</span>
        </div>
      </div>
    </div>

    <div class="flex h-[30px] items-center gap-8 pt-[13px] text-[11px] leading-[16.5px]">
      <div v-for="s in SERIES" :key="`lg${s.key}`" class="flex items-center gap-2">
        <span class="size-[10px] rounded-full" :style="{ background: s.color }" />
        <span>{{ s.label }}</span>
        <span class="pl-1 font-semibold">{{ formatCount(totals[s.key]) }}</span>
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
import { formatCompact, formatCount, monotonePath, niceTicks, type Point } from './utils'

type Row = { date: string; leads: number; deals: number; won_deals: number }
type Key = 'leads' | 'deals' | 'won_deals'

const props = defineProps<{ data: Row[] }>()
const days = defineModel<number>('days', { required: true })

const SERIES: { key: Key; label: string; color: string; width: number }[] = [
  { key: 'leads', label: __('Leads'), color: '#625bff', width: 1.7 },
  { key: 'deals', label: __('Deals'), color: '#4da5ff', width: 1.6 },
  { key: 'won_deals', label: __('Won Deals'), color: '#08c782', width: 1.6 },
]

const periodOptions = [7, 30, 60, 90].map((n) => ({ label: __('Last {0} days', [n]), value: n }))

const uid = `ov-trend-${useId()}`
const wrap = ref<HTMLElement>()
const { width: measured } = useElementSize(wrap)
const width = computed(() => Math.max(measured.value, 200))

// Plot frame from the Figma chart: 39px left gutter, 11px right, y 5..134.
const L = 39
const T = 5
const B = 134
const R = computed(() => width.value - 11)

const max = computed(() =>
  Math.max(0, ...props.data.flatMap((r) => [r.leads, r.deals, r.won_deals])),
)
const yTicks = computed(() => niceTicks(max.value, 4))
const yMax = computed(() => yTicks.value[yTicks.value.length - 1] || 1)

const x = (i: number) => {
  const n = props.data.length
  return n > 1 ? L + ((R.value - L) * i) / (n - 1) : (L + R.value) / 2
}
const y = (v: number) => B - ((B - T) * v) / yMax.value

// A tick every 7 days from the start, plus the last day (Sep 1, 8, 15, 22, 30).
const xTickIdx = computed(() => {
  const n = props.data.length
  if (!n) return []
  const step = n <= 8 ? 1 : n <= 31 ? 7 : n <= 62 ? 14 : 21
  const idx: number[] = []
  for (let i = 0; i < n - step / 2; i += step) idx.push(i)
  idx.push(n - 1)
  return idx
})

function points(key: Key): Point[] {
  return props.data.map((r, i) => [x(i), y(r[key])])
}
const lines = computed(() =>
  Object.fromEntries(SERIES.map((s) => [s.key, monotonePath(points(s.key))])),
)
const areas = computed(() =>
  Object.fromEntries(
    SERIES.map((s) => {
      const pts = points(s.key)
      if (!pts.length) return [s.key, '']
      return [s.key, `${monotonePath(pts)}L${pts[pts.length - 1][0]},${B}L${pts[0][0]},${B}Z`]
    }),
  ),
)
const totals = computed(() =>
  Object.fromEntries(
    SERIES.map((s) => [s.key, props.data.reduce((a, r) => a + (r[s.key] || 0), 0)]),
  ) as Record<Key, number>,
)

const hover = ref<number | null>(null)
function onMove(e: MouseEvent) {
  const n = props.data.length
  if (!n) return
  const box = (e.currentTarget as SVGElement).getBoundingClientRect()
  const px = e.clientX - box.left
  if (px < L - 4 || px > R.value + 4) return (hover.value = null)
  const i = Math.round(((px - L) / (R.value - L)) * (n - 1))
  hover.value = Math.min(n - 1, Math.max(0, i))
}
</script>
