<template>
  <section
    class="ov-card flex min-w-0 flex-col overflow-hidden p-[18px]"
    style="box-shadow: 0 1px 4px rgba(24, 32, 56, 0.04)"
  >
    <CardHeading :title="__('Recent leads')" align="center">
      <ViewAllLink :to="{ name: 'Leads' }" />
    </CardHeading>
    <div class="overflow-x-auto pt-[5px]">
      <table class="w-full min-w-[760px] table-fixed border-collapse text-left text-[11px] leading-[16.5px]">
        <colgroup>
          <col style="width: 44.67px" />
          <col style="width: 25.2%" />
          <col style="width: 14.8%" />
          <col style="width: 14%" />
          <col style="width: 18.3%" />
          <col style="width: 18.5%" />
          <col />
        </colgroup>
        <thead>
          <tr style="background: var(--ov-th-bg); color: var(--ov-ink-table)">
            <th class="h-7 px-[14px] font-normal">
              <input
                type="checkbox"
                class="ov-checkbox block"
                :checked="allSelected"
                :aria-label="__('Select all leads')"
                @change="toggleAll"
              />
            </th>
            <th class="px-3 font-normal">{{ __('Name') }}</th>
            <th class="px-3 font-normal">{{ __('Company') }}</th>
            <th class="px-3 font-normal">{{ __('Source') }}</th>
            <th class="px-3 font-normal">{{ __('Status') }}</th>
            <th class="px-3 font-normal">{{ __('Last activity') }}</th>
            <th class="px-3 font-normal">{{ __('Actions') }}</th>
          </tr>
        </thead>
        <tbody style="color: var(--ov-ink-table)">
          <tr v-if="!leads.length">
            <td colspan="7" class="ov-empty h-[33px] border-t px-[14px]" style="border-color: var(--ov-row-border)">
              {{ __('No leads yet') }}
            </td>
          </tr>
          <tr
            v-for="lead in leads"
            :key="lead.name"
            class="h-[33px] border-t"
            style="border-color: var(--ov-row-border)"
          >
            <td class="px-[14px]">
              <input
                v-model="selected"
                type="checkbox"
                class="ov-checkbox block"
                :value="lead.name"
                :aria-label="__('Select {0}', [lead.lead_name || lead.name])"
              />
            </td>
            <td class="px-3">
              <button type="button" class="flex max-w-full items-center gap-[14px]" @click="open(lead)">
                <span
                  class="ov-chip size-[26px] text-[10px] font-medium leading-[15px]"
                  style="background: var(--ov-avatar-bg); color: var(--ov-avatar-ink)"
                >
                  {{ initials(lead.lead_name || lead.name) }}
                </span>
                <span class="truncate hover:underline">{{ lead.lead_name || lead.name }}</span>
              </button>
            </td>
            <td class="truncate px-3">{{ lead.organization || '—' }}</td>
            <td class="truncate px-3">{{ lead.source || '—' }}</td>
            <td class="px-3">
              <span class="ov-pill" :class="pillClass(lead.status)">{{ __(lead.status) }}</span>
            </td>
            <td class="px-3">{{ shortAgo(lead.modified) }}</td>
            <td class="px-3">
              <Dropdown :options="actions(lead)" placement="right">
                <button
                  type="button"
                  class="flex size-[25px] items-center justify-center rounded hover:bg-[var(--ov-hover)]"
                  :aria-label="__('Open {0}', [lead.lead_name || lead.name])"
                >
                  <img :src="moreIcon" alt="" class="size-[17px]" />
                </button>
              </Dropdown>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Dropdown } from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import CardHeading from './CardHeading.vue'
import ViewAllLink from './ViewAllLink.vue'
import { initials, shortAgo } from './utils'
import moreIcon from './assets/more.svg'

type Lead = {
  name: string
  lead_name: string
  organization: string
  source: string
  status: string
  modified: string
}

const props = defineProps<{ leads: Lead[] }>()

const router = useRouter()
const selected = ref<string[]>([])

const allSelected = computed(
  () => props.leads.length > 0 && selected.value.length === props.leads.length,
)
function toggleAll() {
  selected.value = allSelected.value ? [] : props.leads.map((l) => l.name)
}

// Figma pill colors, mapped onto the CRM's lead statuses.
const PILLS: Record<string, string> = {
  New: 'ov-pill-blue',
  Contacted: 'ov-pill-orange',
  Nurture: 'ov-pill-orange',
  Qualified: 'ov-pill-violet',
  Proposal: 'ov-pill-green',
  Converted: 'ov-pill-green',
  Unqualified: 'ov-pill-gray',
  Junk: 'ov-pill-red',
}
const pillClass = (status: string) => PILLS[status] || 'ov-pill-gray'

function open(lead: Lead) {
  router.push({ name: 'Lead', params: { leadId: lead.name } })
}

function actions(lead: Lead) {
  return [
    { label: __('Open lead'), icon: 'arrow-up-right', onClick: () => open(lead) },
    {
      label: __('Add task'),
      icon: 'check-square',
      onClick: () =>
        router.push({ name: 'Lead', params: { leadId: lead.name }, hash: '#tasks' }),
    },
  ]
}
</script>
