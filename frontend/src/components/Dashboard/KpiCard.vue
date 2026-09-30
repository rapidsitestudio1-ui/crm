<template>
  <!-- Standalone: its own card, sized for a dashboard grid slot (h=3 ≈ 112px).
       Segment: one cell of KpiStrip, which draws the shared border/dividers. -->
  <div
    ref="cardRef"
    class="flex h-full w-full flex-col overflow-hidden bg-surface-base"
    :class="segment ? '' : 'rounded-lg shadow'"
  >
    <div
      class="flex min-h-0 flex-1 flex-col justify-center"
      :class="segment ? 'gap-2 px-5 py-4' : 'gap-0.5 px-4 py-1.5'"
    >
      <div class="flex h-[18px] items-center gap-1.5 text-sm-medium text-ink-gray-5">
        <span class="truncate">{{ config.title }}</span>
        <Tooltip v-if="tooltip" :text="__(tooltip)">
          <span
            class="lucide-info size-3.5 shrink-0 text-ink-gray-4"
            aria-hidden="true"
          />
        </Tooltip>
      </div>
      <div class="flex items-center justify-between gap-2">
        <div class="flex min-w-0 flex-col" :class="segment ? 'gap-1.5' : 'gap-0.5'">
          <div
            class="flex items-center gap-0.5 truncate text-[24px] font-semibold leading-7 tracking-[-0.02em] text-ink-gray-9"
          >
            <div v-if="config.prefix" v-html="config.prefix" class="size-4 table" />
            {{ formatValue(config.value) }}{{ config.suffix }}
          </div>
          <div class="flex h-[18px] items-center gap-1.5 text-xs text-ink-gray-4">
            <span class="truncate">{{ __('vs previous period') }}</span>
            <span
              v-if="hasDelta"
              class="inline-flex items-center gap-0.5 rounded-full px-1.5 py-px text-xs-medium"
              :class="
                isGood
                  ? 'bg-[var(--success-bg)] text-[color:var(--success-text)]'
                  : 'bg-[var(--danger-bg)] text-[color:var(--danger-text)]'
              "
            >
              {{ config.delta >= 0 ? '↑' : '↓' }}
              {{ config.deltaPrefix }}{{ formatValue(Math.abs(config.delta))
              }}{{ config.deltaSuffix }}
            </span>
          </div>
        </div>
        <MiniChart v-if="cardWidth >= 200" :type="chartType" />
      </div>
    </div>
    <button
      v-if="detailsRoute"
      class="flex shrink-0 items-center justify-center gap-1 border-t border-outline-gray-1 text-sm-medium text-ink-gray-8 transition-colors hover:bg-surface-gray-1"
      :class="segment ? 'h-10' : 'h-7'"
      @click.stop="router.push(detailsRoute)"
    >
      {{ __('See Details') }}
      <span class="lucide-arrow-right size-3.5" aria-hidden="true" />
    </button>
  </div>
</template>

<script setup>
import MiniChart from '@/components/Dashboard/MiniChart.vue'
import { Tooltip } from 'frappe-ui'
import { useElementSize } from '@vueuse/core'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  name: { type: String, default: '' },
  config: { type: Object, required: true },
  tooltip: { type: String, default: '' },
  index: { type: Number, default: 0 },
  segment: { type: Boolean, default: false },
})

const router = useRouter()

// Narrow cards drop the decorative chart so the value never truncates.
const cardRef = ref(null)
const { width: cardWidth } = useElementSize(cardRef)

// Which list "See Details" opens, and which glyph each metric shows.
const METRICS = {
  total_leads: { route: 'Leads', chart: 'bars' },
  average_time_to_close_a_lead: { route: 'Leads', chart: 'pulse' },
  ongoing_deals: { route: 'Deals', chart: 'line' },
  won_deals: { route: 'Deals', chart: 'donut' },
  average_won_deal_value: { route: 'Deals', chart: 'bars' },
  average_deal_value: { route: 'Deals', chart: 'line' },
  average_ongoing_deal_value: { route: 'Deals', chart: 'line' },
  average_time_to_close_a_deal: { route: 'Deals', chart: 'pulse' },
}
const CHART_CYCLE = ['bars', 'line', 'donut', 'pulse']

const metric = computed(() => METRICS[props.name] || {})
const chartType = computed(
  () => metric.value.chart || CHART_CYCLE[props.index % CHART_CYCLE.length],
)
const detailsRoute = computed(() =>
  metric.value.route ? { name: metric.value.route } : null,
)

const hasDelta = computed(
  () => props.config.delta !== undefined && props.config.delta !== null && props.config.delta !== 0,
)
const isGood = computed(() =>
  props.config.negativeIsBetter ? props.config.delta < 0 : props.config.delta >= 0,
)

// Same formatting as frappe-ui's NumberChart (compact, 1 decimal); that helper
// is not exported by frappe-ui.
function formatValue(value) {
  if (value === undefined || value === null || isNaN(value)) return value ?? ''
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)
}
</script>
