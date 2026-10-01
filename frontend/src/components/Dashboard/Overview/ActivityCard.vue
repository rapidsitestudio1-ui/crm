<template>
  <section class="ov-card flex min-w-0 flex-col px-[18px] pb-3 pt-[15px]">
    <CardHeading :title="__('Recent activity')" align="center">
      <ViewAllLink :to="{ name: 'Notifications' }" />
    </CardHeading>
    <div class="flex flex-col gap-[9px] pt-[13px]">
      <p v-if="!items.length" class="ov-empty px-[10px]">{{ __('No recent activity') }}</p>
      <button
        v-for="(item, i) in items"
        :key="i"
        type="button"
        class="flex w-full items-start gap-4 rounded-[6px] px-[10px] text-left hover:bg-[var(--ov-hover)]"
        @click="open(item)"
      >
        <span class="ov-chip size-[30px]" :style="{ background: KINDS[item.type].bg }">
          <img v-if="KINDS[item.type].icon" :src="KINDS[item.type].icon" alt="" class="size-[14px]" />
          <component
            :is="KINDS[item.type].component"
            v-else
            class="size-[14px]"
            :style="{ color: KINDS[item.type].color }"
          />
        </span>
        <span class="flex min-w-0 flex-1 flex-col">
          <span class="truncate text-[12px] font-medium leading-[17px]">{{ __(item.title) }}</span>
          <span class="truncate text-[12px] leading-[17px]" style="color: var(--ov-ink-muted)">
            {{ item.subtitle }}
          </span>
        </span>
        <span
          class="whitespace-nowrap pt-[3px] text-[10px] leading-[15px]"
          style="color: var(--ov-ink-time)"
        >
          {{ shortAgo(item.time) }}
        </span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import CardHeading from './CardHeading.vue'
import ViewAllLink from './ViewAllLink.vue'
import { shortAgo } from './utils'
import leadIcon from './assets/act-lead.svg'
import dealIcon from './assets/act-deal.svg'
import whatsappIcon from './assets/act-whatsapp.svg'
import emailIcon from './assets/act-email.svg'
import noteIcon from './assets/act-note.svg'

import LucideMessageSquare from '~icons/lucide/message-square'
import LucidePhone from '~icons/lucide/phone'
import type { Component } from 'vue'

type Kind = 'lead' | 'deal' | 'whatsapp' | 'email' | 'note' | 'comment' | 'call'
type Item = { type: Kind; title: string; subtitle: string; time: string; doctype: string; name: string }

defineProps<{ items: Item[] }>()

// Figma icons for the five designed kinds; Lucide (in matching tones) for the
// two the design doesn't cover.
const KINDS: Record<Kind, { icon?: string; component?: Component; color?: string; bg: string }> = {
  lead: { icon: leadIcon, bg: 'var(--ov-chip-lead)' },
  deal: { icon: dealIcon, bg: 'var(--ov-chip-deal)' },
  whatsapp: { icon: whatsappIcon, bg: 'var(--ov-chip-whatsapp)' },
  email: { icon: emailIcon, bg: 'var(--ov-chip-email)' },
  note: { icon: noteIcon, bg: 'var(--ov-chip-note)' },
  comment: { component: LucideMessageSquare, color: '#6d3fd6', bg: 'var(--ov-chip-violet)' },
  call: { component: LucidePhone, color: '#0a8f5a', bg: 'var(--ov-chip-whatsapp)' },
}

const router = useRouter()
const TAB: Record<Kind, string> = {
  lead: '#activity',
  deal: '#activity',
  whatsapp: '#whatsapp',
  email: '#emails',
  note: '#notes',
  comment: '#comments',
  call: '#calls',
}

function open(item: Item) {
  if (item.doctype === 'CRM Lead') {
    router.push({ name: 'Lead', params: { leadId: item.name }, hash: TAB[item.type] })
  } else if (item.doctype === 'CRM Deal') {
    router.push({ name: 'Deal', params: { dealId: item.name }, hash: TAB[item.type] })
  }
}
</script>
