<template>
  <p v-if="!items.length" class="cp-empty">{{ __('No activity yet.') }}</p>
  <ol v-else class="cp-tl">
    <li v-for="(a, i) in items" :key="a.type + (a.name || i)" class="cp-tl-item">
      <span
        class="cp-tl-icon"
        :class="{ 'is-outline': KIND[a.type].outline }"
        :style="KIND[a.type].outline ? {} : { background: KIND[a.type].color }"
      >
        <component :is="KIND[a.type].icon" />
      </span>
      <div class="min-w-0 flex-1">
        <div class="flex items-start justify-between gap-4">
          <p class="cp-tl-title min-w-0">
            <!-- eslint-disable-next-line vue/no-v-html -->
            <span v-html="titleOf(a)" />
          </p>
          <Tooltip :text="dayjsLocal(a.time).format('ddd, MMM D, YYYY h:mm A')">
            <span class="cp-tl-time">{{ formatTime(a.time) }}</span>
          </Tooltip>
        </div>

        <!-- Call: duration + outcome -->
        <p v-if="a.type === 'call'" class="cp-tl-detail">
          <span v-if="a.duration">{{ formatDuration(a.duration) }}</span>
          <span v-if="a.duration && a.status"> · </span>
          <span v-if="a.status">{{ __(a.status) }}</span>
        </p>

        <!-- Meeting: when + description -->
        <p v-else-if="a.type === 'meeting'" class="cp-tl-detail">
          {{ __('On {0}', [dayjsLocal(a.starts_on).format('MMM D, YYYY [at] h:mm A')]) }}
          <template v-if="a.text"> · {{ a.text }}</template>
        </p>

        <!-- Task: checkbox card with priority and due state -->
        <div v-else-if="a.type === 'task'" class="cp-task">
          <input
            type="checkbox"
            :checked="a.status === 'Done'"
            :aria-label="__('Mark {0} as done', [a.title])"
            @change="emit('toggleTask', a, $event.target.checked)"
          />
          <button
            type="button"
            class="truncate text-left hover:underline"
            :class="{ 'line-through opacity-60': a.status === 'Done' }"
            @click="emit('openTask', a)"
          >
            {{ a.title || __('Untitled task') }}
          </button>
          <span v-if="a.priority" class="cp-pill is-dot" :class="`is-${a.priority.toLowerCase()}`">
            {{ __(a.priority) }}
          </span>
          <span v-if="isOverdue(a)" class="cp-pill is-overdue">{{ __('Overdue') }}</span>
          <span v-else-if="a.status === 'Done'" class="cp-pill is-done">{{ __('Done') }}</span>
          <span v-if="a.due_date" class="whitespace-nowrap text-[12.5px]" style="color: var(--kb-ink-2)">
            {{ dayjsLocal(a.due_date).format('MMM D, YYYY') }}
          </span>
        </div>

        <!-- Note / comment text -->
        <p v-else-if="a.text" class="cp-tl-detail line-clamp-3">{{ a.text }}</p>

        <router-link
          v-if="a.ref_doctype === 'CRM Deal' && a.ref_name"
          :to="{ name: 'Deal', params: { dealId: a.ref_name } }"
          class="mt-1 inline-block text-[12px] hover:underline"
          style="color: var(--kb-ink-3)"
        >
          {{ __('on deal {0}', [dealLabel(a.ref_name)]) }}
        </router-link>
      </div>
    </li>
  </ol>
</template>

<script setup>
import LucidePhone from '~icons/lucide/phone'
import LucideCalendar from '~icons/lucide/calendar'
import LucideSquareCheck from '~icons/lucide/square-check'
import LucidePlus from '~icons/lucide/plus'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucideMail from '~icons/lucide/mail'
import LucideMessageSquare from '~icons/lucide/message-square'
import { usersStore } from '@/stores/users'
import { formatDuration } from '@/utils'
import { Tooltip, dayjs, dayjsLocal } from 'frappe-ui'

const props = defineProps({
  items: { type: Array, default: () => [] },
  contactName: { type: String, default: '' },
  deals: { type: Array, default: () => [] },
})
const emit = defineEmits(['toggleTask', 'openTask'])

const { getUser } = usersStore()

const KIND = {
  call: { icon: LucidePhone, color: '#3b82f6' },
  meeting: { icon: LucideCalendar, color: '#10b981' },
  task: { icon: LucideSquareCheck, color: '#111827' },
  note: { icon: LucideStickyNote, color: '#d97706' },
  email: { icon: LucideMail, color: '#4f46e5' },
  comment: { icon: LucideMessageSquare, color: '#7c3aed' },
  added: { icon: LucidePlus, outline: true },
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])
}
function who(user) {
  return esc(getUser(user)?.full_name || user || __('Someone'))
}

// Title line with the key names in bold (all values escaped).
function titleOf(a) {
  const name = `<b>${esc(props.contactName)}</b>`
  const by = a.by ? ` ${__('by')} <b>${who(a.by)}</b>` : ''
  switch (a.type) {
    case 'call':
      return a.direction === 'Incoming'
        ? `<b>${__('Incoming call')}</b> ${__('from')} ${name}${by}`
        : `<b>${__('Logged call')}</b> ${__('to')} ${name}${by}`
    case 'meeting':
      return `<b>${__('Meeting scheduled')}</b> ${__('with')} ${name}${by}${a.title ? ` · ${esc(a.title)}` : ''}`
    case 'task':
      return `<b>${__('Task created')}</b>${by}`
    case 'note':
      return `<b>${__('Note')}</b>${a.title ? ` · ${esc(a.title)}` : ''}${by}`
    case 'comment':
      return `<b>${__('Comment')}</b>${by}`
    case 'email':
      return a.direction === 'Received'
        ? `<b>${__('Email received')}</b> ${__('from')} <b>${esc(a.from)}</b>${a.title ? ` · ${esc(a.title)}` : ''}`
        : `<b>${__('Email sent')}</b>${a.title ? ` · ${esc(a.title)}` : ''}`
    case 'added':
      return `${name} ${__('was added to')} <b>${__('contacts')}</b>${by}`
  }
  return ''
}

function formatTime(t) {
  return dayjsLocal(t).format('MMM DD, YYYY [at] hh:mm A')
}

function isOverdue(a) {
  return a.status !== 'Done' && a.status !== 'Canceled' && a.due_date && dayjsLocal(a.due_date).isBefore(dayjs())
}

function dealLabel(name) {
  return props.deals.find((d) => d.name === name)?.organization || name
}
</script>
