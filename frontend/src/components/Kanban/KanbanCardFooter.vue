<template>
  <div v-if="hasCounts || people.length || time" class="kb-footer">
    <div class="kb-counts">
      <Tooltip v-for="c in visibleCounts" :key="c.key" :text="c.label">
        <span :aria-label="`${c.value} ${c.label}`">
          <component :is="c.icon" />
          {{ c.value }}
        </span>
      </Tooltip>
    </div>
    <div class="flex min-w-0 items-center gap-2">
      <Tooltip v-if="time" :text="timeTitle || time">
        <span class="truncate whitespace-nowrap">{{ shortTime }}</span>
      </Tooltip>
      <!-- Assignees (or the owner), as overlapping avatars; names on hover. -->
      <Tooltip v-if="people.length" :text="people.map((p) => p.label).join(', ')">
        <span class="flex shrink-0 -space-x-1.5">
          <KanbanAvatar
            v-for="p in people.slice(0, 3)"
            :key="p.label"
            :image="p.image"
            :label="p.label"
            size="xs"
            class="ring-2 ring-[var(--kb-card)] rounded-full"
          />
          <span
            v-if="people.length > 3"
            class="kb-avatar size-5 text-[9px] ring-2 ring-[var(--kb-card)]"
            style="background: var(--kb-hover); color: var(--kb-ink-2)"
          >
            +{{ people.length - 3 }}
          </span>
        </span>
      </Tooltip>
    </div>
  </div>
</template>

<script setup>
import LucideMail from '~icons/lucide/mail'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideMessageSquare from '~icons/lucide/message-square'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'
import KanbanAvatar from './KanbanAvatar.vue'

const props = defineProps({
  counts: { type: Object, default: () => ({}) }, // { email, note, task, comment }
  assignees: { type: Array, default: () => [] }, // [{ label, image }]
  owner: { type: Object, default: null }, // { label, image }
  time: { type: String, default: '' },
  timeTitle: { type: String, default: '' },
})

// "19 minutes ago" -> "19m ago", "a month ago" -> "1mo ago". Anything else
// (e.g. "yesterday", other languages) is shown as is.
const UNIT = { minute: 'm', hour: 'h', day: 'd', week: 'w', month: 'mo', year: 'y' }
const shortTime = computed(() => {
  const t = props.time || ''
  const m = t.match(/^(\d+|an?)\s+(minute|hour|day|week|month|year)s?\s+ago$/i)
  if (!m) return t
  const n = /^\d+$/.test(m[1]) ? m[1] : '1'
  return `${n}${UNIT[m[2].toLowerCase()]} ago`
})

const people = computed(() =>
  props.assignees.length ? props.assignees : props.owner ? [props.owner] : [],
)

// Only non-zero activity counts are shown, to keep cards quiet.
const visibleCounts = computed(() =>
  [
    { key: 'email', icon: LucideMail, label: __('Emails'), value: props.counts.email },
    { key: 'note', icon: LucideStickyNote, label: __('Notes'), value: props.counts.note },
    { key: 'task', icon: LucideCircleCheck, label: __('Tasks'), value: props.counts.task },
    { key: 'comment', icon: LucideMessageSquare, label: __('Comments'), value: props.counts.comment },
  ].filter((c) => Number(c.value) > 0),
)
const hasCounts = computed(() => visibleCounts.value.length > 0)
</script>
