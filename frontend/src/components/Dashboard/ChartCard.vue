<template>
  <!-- Figma "Card": header (title + info), chart body, optional footer -->
  <div
    class="flex h-full w-full flex-col overflow-hidden rounded-lg bg-surface-base shadow"
  >
    <div class="flex h-11 shrink-0 items-center gap-1.5 px-4">
      <span class="truncate text-base-medium text-ink-gray-9">
        {{ config.title }}
      </span>
      <Tooltip v-if="config.subtitle" :text="config.subtitle">
        <span
          class="lucide-info size-3.5 shrink-0 text-ink-gray-4"
          :aria-label="config.subtitle"
        />
      </Tooltip>
    </div>
    <div class="min-h-0 flex-1">
      <DonutChart v-if="type === 'donut_chart'" :config="chartConfig" />
      <AxisChart v-else :config="chartConfig" />
    </div>
    <button
      v-if="detailsRoute"
      class="flex h-8 shrink-0 items-center justify-center gap-1 border-t border-outline-gray-1 text-sm-medium text-ink-gray-8 transition-colors hover:bg-surface-gray-1"
      @click.stop="router.push(detailsRoute)"
    >
      {{ __('See Details') }}
      <span class="lucide-arrow-right size-3.5" aria-hidden="true" />
    </button>
  </div>
</template>

<script setup>
import { AxisChart, DonutChart, Tooltip } from 'frappe-ui'
import { useMutationObserver } from '@vueuse/core'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  name: { type: String, default: '' },
  type: { type: String, required: true },
  config: { type: Object, required: true },
})

const router = useRouter()

// Which list "See Details" opens for each standard chart.
const DETAILS = {
  sales_trend: 'Leads',
  funnel_conversion: 'Leads',
  leads_by_source: 'Leads',
  forecasted_revenue: 'Deals',
  deals_by_stage_axis: 'Deals',
  deals_by_stage_donut: 'Deals',
  lost_deal_reasons: 'Deals',
  deals_by_source: 'Deals',
  deals_by_territory: 'Deals',
  deals_by_salesperson: 'Deals',
}
const detailsRoute = computed(() =>
  DETAILS[props.name] ? { name: DETAILS[props.name] } : null,
)

// Re-read the palette when light/dark flips (ECharts needs concrete colors).
const theme = ref(document.documentElement.getAttribute('data-theme'))
useMutationObserver(
  document.documentElement,
  () => (theme.value = document.documentElement.getAttribute('data-theme')),
  { attributes: true, attributeFilter: ['data-theme'] },
)

// The card header renders title/subtitle, so drop them from the chart (frappe-ui
// then reclaims that space for the plot). Palette comes from theme.css
// (--chart-1..6); colors a chart config already sets still win.
const chartConfig = computed(() => {
  theme.value // dependency: recompute on theme change
  const style = getComputedStyle(document.documentElement)
  const colors = [1, 2, 3, 4, 5, 6]
    .map((i) => style.getPropertyValue(`--chart-${i}`).trim())
    .filter(Boolean)
  const config = {
    ...(colors.length ? { colors } : {}),
    ...props.config,
    title: '',
    subtitle: '',
  }
  if (props.type === 'axis_chart') {
    for (const axis of ['xAxis', 'yAxis', 'y2Axis']) {
      if (config[axis]) config[axis] = withReadableLabels(config[axis])
    }
  }
  return config
})

// ECharts' default tick-label gray (#6E7079) is 3.6:1 on dark surfaces; use
// the theme's ink-gray-5 (AA in both modes) unless the chart sets its own.
function withReadableLabels(axis) {
  const opts = axis.echartOptions || {}
  return {
    ...axis,
    echartOptions: {
      ...opts,
      axisLabel: { color: 'var(--ink-gray-5)', ...(opts.axisLabel || {}) },
    },
  }
}
</script>
