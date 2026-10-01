<template>
  <div class="ov-root min-h-full px-6 pb-8 pt-6">
    <div v-if="!data" class="grid grid-cols-4 gap-5">
      <div v-for="i in 4" :key="i" class="ov-card h-[122px] animate-pulse" />
    </div>
    <div v-else class="flex flex-col gap-6">
      <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard v-for="m in metrics" :key="m.title" v-bind="m" :days="data.days" />
      </div>

      <div class="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,768fr)_minmax(0,531fr)]">
        <SalesTrendCard v-model:days="days" :data="data.trend" />
        <PipelineForecastCard
          v-model:months="forecastMonths"
          :data="data.forecast"
          :currency="data.currency"
        />
      </div>

      <div
        class="grid grid-cols-1 gap-5 lg:grid-cols-2 xl:grid-cols-[minmax(0,459fr)_minmax(0,419fr)_minmax(0,407fr)]"
      >
        <FunnelCard :data="data.funnel" />
        <TasksCard :tasks="data.tasks" />
        <ActivityCard :items="data.activity" />
      </div>

      <RecentLeadsCard :leads="data.leads" />
    </div>
  </div>
</template>

<script setup lang="ts">
import './overview.css'
import { createResource, dayjs } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { globalStore } from '@/stores/global'
import MetricCard from './MetricCard.vue'
import SalesTrendCard from './SalesTrendCard.vue'
import PipelineForecastCard from './PipelineForecastCard.vue'
import FunnelCard from './FunnelCard.vue'
import TasksCard from './TasksCard.vue'
import ActivityCard from './ActivityCard.vue'
import RecentLeadsCard from './RecentLeadsCard.vue'
import { formatCount, formatMoney } from './utils'
import leadsIcon from './assets/kpi-leads.svg'
import dealsIcon from './assets/kpi-deals.svg'
import wonIcon from './assets/kpi-won.svg'
import revenueIcon from './assets/kpi-revenue.svg'

const props = defineProps<{ user?: string | null }>()

const days = ref(30)
const forecastMonths = ref(4)

const overview = createResource({
  url: 'crm.api.overview.get_overview',
  makeParams: () => ({
    from_date: dayjs().subtract(days.value - 1, 'day').format('YYYY-MM-DD'),
    to_date: dayjs().format('YYYY-MM-DD'),
    user: props.user || null,
    forecast_months: forecastMonths.value,
  }),
  auto: true,
})

watch([days, forecastMonths, () => props.user], () => overview.reload())

// Live updates: Frappe emits "list_update" to everyone subscribed to a doctype
// whenever a record of it is created, changed or deleted. Any change to a
// doctype the dashboard reads refreshes it (debounced, so bulk edits cause one
// reload).
const LIVE_DOCTYPES = [
  'CRM Task',
  'CRM Lead',
  'CRM Deal',
  'FCRM Note',
  'Communication',
  'Comment',
  'CRM Call Log',
]
const { $socket } = globalStore()
let reloadTimer: ReturnType<typeof setTimeout> | undefined

function scheduleReload() {
  clearTimeout(reloadTimer)
  reloadTimer = setTimeout(() => overview.reload(), 500)
}
function onListUpdate(data: { doctype?: string }) {
  if (data?.doctype && LIVE_DOCTYPES.includes(data.doctype)) scheduleReload()
}
// Catch anything missed while the tab was in the background.
function onVisible() {
  if (document.visibilityState === 'visible') scheduleReload()
}

// Rooms are dropped when the socket reconnects (e.g. after a server restart),
// so subscribe again on every connect and catch up with a reload.
function subscribe() {
  LIVE_DOCTYPES.forEach((dt) => $socket.emit('doctype_subscribe', dt))
}
function onReconnect() {
  subscribe()
  scheduleReload()
}

// Rooms are left joined on unmount: the Leads/Deals pages share some of them.
onMounted(() => {
  subscribe()
  $socket.on('connect', onReconnect)
  $socket.on('list_update', onListUpdate)
  document.addEventListener('visibilitychange', onVisible)
})
onBeforeUnmount(() => {
  clearTimeout(reloadTimer)
  $socket.off('connect', onReconnect)
  $socket.off('list_update', onListUpdate)
  document.removeEventListener('visibilitychange', onVisible)
})

const data = computed(() => overview.data)

const metrics = computed(() => {
  const k = data.value.kpis
  return [
    {
      title: __('Total leads'),
      value: formatCount(k.total_leads.value),
      delta: k.total_leads.delta,
      series: k.total_leads.series,
      icon: leadsIcon,
      chipBg: 'var(--ov-chip-blue)',
      color: '#625bff',
    },
    {
      title: __('Active deals'),
      value: formatCount(k.active_deals.value),
      delta: k.active_deals.delta,
      series: k.active_deals.series,
      icon: dealsIcon,
      chipBg: 'var(--ov-chip-orange)',
      color: '#329dff',
    },
    {
      title: __('Won deals'),
      value: formatCount(k.won_deals.value),
      delta: k.won_deals.delta,
      series: k.won_deals.series,
      icon: wonIcon,
      chipBg: 'var(--ov-chip-amber)',
      color: '#08c782',
    },
    {
      title: __('Forecasted revenue'),
      value: formatMoney(k.forecasted_revenue.value, data.value.currency),
      delta: k.forecasted_revenue.delta,
      series: k.forecasted_revenue.series,
      icon: revenueIcon,
      chipBg: 'var(--ov-chip-violet)',
      color: '#8275ff',
    },
  ]
})

defineExpose({ reload: () => overview.reload() })
</script>
