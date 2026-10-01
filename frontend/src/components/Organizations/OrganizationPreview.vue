<template>
  <Teleport to="body">
    <Transition name="ct-fade">
      <div
        v-if="open"
        class="fixed inset-0 z-40 bg-[rgba(17,24,39,0.18)]"
        aria-hidden="true"
        @click="close"
      />
    </Transition>
    <Transition name="ct-slide">
      <aside
        v-if="open"
        class="ct-drawer"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        @keydown.esc.stop="close"
      >
        <div class="flex items-center justify-between gap-2 px-5 pt-4">
          <span class="text-[12px] font-medium" style="color: var(--kb-ink-3)">
            {{ __('Organization') }}
          </span>
          <div class="flex items-center gap-1">
            <router-link
              v-if="orgName"
              :to="{ name: 'Organization', params: { organizationId: orgName } }"
              class="ct-btn !h-7 !px-2.5 !text-[12.5px]"
              @click="close"
            >
              {{ __('Open') }}
              <LucideArrowUpRight />
            </router-link>
            <button
              ref="closeBtn"
              type="button"
              class="kb-icon-btn !size-7"
              :aria-label="__('Close preview')"
              @click="close"
            >
              <LucideX class="size-4" />
            </button>
          </div>
        </div>

        <div v-if="!doc && !loadError" class="flex flex-col gap-3 px-5 pt-6">
          <div class="h-12 w-12 animate-pulse rounded-lg bg-[var(--kb-hover)]" />
          <div class="h-4 w-40 animate-pulse rounded bg-[var(--kb-hover)]" />
        </div>
        <p v-else-if="loadError" class="ct-sub px-5 pt-6">
          {{ __('This organization could not be loaded.') }}
        </p>

        <div v-else class="flex min-h-0 flex-1 flex-col overflow-y-auto pb-6">
          <!-- Identity -->
          <div class="flex items-center gap-3.5 px-5 pt-4">
            <KanbanAvatar :image="doc.organization_logo" :label="doc.organization_name || doc.name" square />
            <div class="flex min-w-0 flex-col">
              <h2 :id="titleId" class="truncate text-[17px] font-semibold leading-6" style="color: var(--kb-ink)">
                {{ doc.organization_name || doc.name }}
              </h2>
              <a
                v-if="doc.website"
                :href="websiteUrl"
                target="_blank"
                rel="noopener"
                class="ct-sub truncate hover:underline"
              >
                {{ websiteLabel }}
              </a>
            </div>
          </div>
          <div v-if="relationship || doc.industry" class="flex flex-wrap gap-1.5 px-5 pt-3">
            <span v-if="relationship" class="kb-badge" :class="badgeClass">{{ relationship.label }}</span>
            <span v-if="doc.industry" class="kb-badge">
              <span class="size-1.5 rounded-full" :style="{ background: industryDot }" />
              {{ __(doc.industry) }}
            </span>
          </div>

          <!-- Details -->
          <section class="ct-section">
            <h3>{{ __('Details') }}</h3>
            <dl class="ct-dl">
              <dt>{{ __('Industry') }}</dt>
              <dd :class="{ 'is-muted': !doc.industry }">{{ doc.industry ? __(doc.industry) : '—' }}</dd>
              <template v-if="doc.territory">
                <dt>{{ __('Territory') }}</dt>
                <dd>{{ __(doc.territory) }}</dd>
              </template>
              <template v-if="doc.no_of_employees">
                <dt>{{ __('Employees') }}</dt>
                <dd>{{ doc.no_of_employees }}</dd>
              </template>
              <dt>{{ __('Annual revenue') }}</dt>
              <dd :class="{ 'is-muted': !doc.annual_revenue }">{{ revenue || '—' }}</dd>
              <template v-if="owner">
                <dt>{{ __('Added by') }}</dt>
                <dd>
                  <KanbanAvatar :image="owner.image" :label="owner.label" size="xs" />
                  <span class="truncate">{{ owner.label }}</span>
                </dd>
              </template>
              <dt>{{ __('Last updated') }}</dt>
              <dd class="is-muted">{{ timeAgo(doc.modified) }}</dd>
            </dl>
          </section>

          <!-- Contacts -->
          <section class="ct-section">
            <h3>
              {{ __('Contacts') }}
              <span v-if="contacts.length" class="ct-tab-count">{{ contacts.length }}</span>
            </h3>
            <p v-if="!contacts.length" class="ct-sub">{{ __('No contacts at this organization yet.') }}</p>
            <ul v-else class="flex flex-col gap-1">
              <li v-for="c in contacts" :key="c.name">
                <router-link
                  :to="{ name: 'Contact', params: { contactId: c.name } }"
                  class="flex items-center gap-2.5 rounded-lg px-2 py-1.5 hover:bg-[var(--kb-hover)]"
                  @click="close"
                >
                  <KanbanAvatar :image="c.image" :label="c.full_name || c.name" size="sm" />
                  <span class="flex min-w-0 flex-col">
                    <span class="truncate text-[13px] font-medium" style="color: var(--kb-ink)">{{ c.full_name || c.name }}</span>
                    <span v-if="c.designation || c.email_id" class="ct-sub truncate">
                      {{ c.designation || c.email_id }}
                    </span>
                  </span>
                </router-link>
              </li>
            </ul>
          </section>

          <!-- Deals -->
          <section class="ct-section">
            <h3>
              {{ __('Deals') }}
              <span v-if="deals.length" class="ct-tab-count">{{ deals.length }}</span>
            </h3>
            <p v-if="!deals.length" class="ct-sub">{{ __('No deals with this organization yet.') }}</p>
            <ul v-else class="flex flex-col gap-1.5">
              <li v-for="d in deals" :key="d.name">
                <router-link
                  :to="{ name: 'Deal', params: { dealId: d.name } }"
                  class="ct-deal"
                  @click="close"
                >
                  <span class="flex min-w-0 flex-col">
                    <span class="truncate text-[13px] font-medium" style="color: var(--kb-ink)">
                      {{ d.lead_name || d.name }}
                    </span>
                    <span class="ct-sub truncate">{{ money(d.deal_value, d.currency) || __('No value') }}</span>
                  </span>
                  <span class="kb-badge shrink-0">
                    <span class="size-1.5 rounded-full" :style="{ background: stageDot(d.status) }" />
                    {{ __(d.status) }}
                  </span>
                </router-link>
              </li>
            </ul>
          </section>

          <!-- Notes + recent activity on its deals -->
          <section class="ct-section">
            <h3>{{ __('Recent activity') }}</h3>
            <p v-if="activityLoading" class="ct-sub">{{ __('Loading…') }}</p>
            <p v-else-if="!activity.length" class="ct-sub">
              {{ deals.length ? __('No notes, emails or comments on its deals yet.') : __('Activity appears here once it has deals.') }}
            </p>
            <ul v-else class="flex flex-col">
              <li v-for="(a, i) in activity" :key="i" class="ct-activity">
                <span class="ct-activity-icon"><component :is="a.icon" /></span>
                <span class="flex min-w-0 flex-1 flex-col">
                  <span class="truncate text-[13px]" style="color: var(--kb-ink)">{{ a.title }}</span>
                  <span v-if="a.text" class="ct-sub line-clamp-2">{{ a.text }}</span>
                </span>
                <span class="shrink-0 text-[11.5px]" style="color: var(--kb-ink-3)">{{ timeAgo(a.time) }}</span>
              </li>
            </ul>
          </section>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
import '@/components/Kanban/kanban.css'
import '@/components/Contacts/contacts.css'
import LucideX from '~icons/lucide/x'
import LucideArrowUpRight from '~icons/lucide/arrow-up-right'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucideMessageSquare from '~icons/lucide/message-square'
import LucideInbox from '~icons/lucide/inbox'
import LucideSend from '~icons/lucide/send'
import KanbanAvatar from '@/components/Kanban/KanbanAvatar.vue'
import { getStageTone } from '@/components/Kanban/stageTones'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { timeAgo } from '@/utils'
import { call } from 'frappe-ui'
import { computed, nextTick, ref, useId, watch } from 'vue'

const props = defineProps({
  relationship: { type: Object, default: null },
})
const orgName = defineModel({ type: String, default: null })

const open = computed(() => Boolean(orgName.value))
const titleId = `org-preview-${useId()}`
const closeBtn = ref(null)
let returnFocusTo = null

const { getUser } = usersStore()
const { getDealStatus } = statusesStore()

const doc = ref(null)
const loadError = ref(false)
const contacts = ref([])
const deals = ref([])
const activity = ref([])
const activityLoading = ref(false)

watch(
  orgName,
  async (name) => {
    if (!name) return
    returnFocusTo = document.activeElement
    doc.value = null
    loadError.value = false
    contacts.value = []
    deals.value = []
    activity.value = []
    try {
      const [d, c, dl] = await Promise.all([
        call('frappe.client.get', { doctype: 'CRM Organization', name }),
        call('frappe.client.get_list', {
          doctype: 'Contact',
          fields: ['name', 'full_name', 'email_id', 'designation', 'image'],
          filters: { company_name: name },
          order_by: 'modified desc',
          limit_page_length: 20,
        }).catch(() => []),
        call('frappe.client.get_list', {
          doctype: 'CRM Deal',
          fields: ['name', 'lead_name', 'status', 'deal_value', 'currency', 'modified'],
          filters: { organization: name },
          order_by: 'modified desc',
          limit_page_length: 20,
        }).catch(() => []),
      ])
      if (name !== orgName.value) return
      doc.value = d
      contacts.value = c
      deals.value = dl
    } catch {
      loadError.value = true
      return
    }
    await nextTick()
    closeBtn.value?.focus()
    loadActivity(name)
  },
  { immediate: true },
)

function close() {
  orgName.value = null
  returnFocusTo?.focus?.()
}

const websiteUrl = computed(() => {
  const w = doc.value?.website || ''
  return /^https?:\/\//.test(w) ? w : `https://${w}`
})
const websiteLabel = computed(() => (doc.value?.website || '').replace(/^https?:\/\//, '').replace(/\/$/, ''))

function money(value, currency) {
  if (!value) return ''
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currency || 'USD',
      notation: value >= 1e6 ? 'compact' : 'standard',
      maximumFractionDigits: value >= 1e6 ? 1 : 0,
    }).format(value)
  } catch {
    return `${currency || ''} ${value}`
  }
}
const revenue = computed(() => money(doc.value?.annual_revenue, doc.value?.currency))

const owner = computed(() => {
  const u = doc.value?.owner && getUser(doc.value.owner)
  return u?.full_name ? { label: u.full_name, image: u.user_image } : null
})
const badgeClass = computed(
  () => ({ success: 'is-success', accent: 'is-accent' })[props.relationship?.tone] || '',
)
const industryDot = computed(() => getStageTone('CRM Organization', { name: doc.value?.industry }).dot)
function stageDot(status) {
  return getStageTone('CRM Deal', { name: status }, getDealStatus(status)).dot
}

function stripHtml(html) {
  const el = document.createElement('div')
  el.innerHTML = html || ''
  return (el.textContent || '').trim()
}

async function loadActivity(name) {
  const dealNames = deals.value.map((d) => d.name)
  if (!dealNames.length) {
    // A previous organization's load may still have the flag set.
    activityLoading.value = false
    return
  }
  activityLoading.value = true
  const onDeals = { reference_doctype: 'CRM Deal' }
  const [notes, emails, comments] = await Promise.all([
    call('frappe.client.get_list', {
      doctype: 'FCRM Note',
      fields: ['title', 'content', 'creation'],
      filters: { ...onDeals, reference_docname: ['in', dealNames] },
      order_by: 'creation desc',
      limit_page_length: 5,
    }).catch(() => []),
    call('frappe.client.get_list', {
      doctype: 'Communication',
      fields: ['subject', 'sent_or_received', 'communication_date'],
      filters: { ...onDeals, reference_name: ['in', dealNames], communication_medium: 'Email' },
      order_by: 'communication_date desc',
      limit_page_length: 5,
    }).catch(() => []),
    call('frappe.client.get_list', {
      doctype: 'Comment',
      fields: ['content', 'creation'],
      filters: { ...onDeals, reference_name: ['in', dealNames], comment_type: 'Comment' },
      order_by: 'creation desc',
      limit_page_length: 5,
    }).catch(() => []),
  ])
  if (name !== orgName.value) return
  activity.value = [
    ...notes.map((n) => ({ icon: LucideStickyNote, title: n.title || __('Note'), text: stripHtml(n.content), time: n.creation })),
    ...emails.map((e) => ({
      icon: e.sent_or_received === 'Received' ? LucideInbox : LucideSend,
      title: e.subject || __('Email'),
      text: e.sent_or_received === 'Received' ? __('Email received') : __('Email sent'),
      time: e.communication_date,
    })),
    ...comments.map((c) => ({ icon: LucideMessageSquare, title: __('Comment'), text: stripHtml(c.content), time: c.creation })),
  ]
    .sort((a, b) => new Date(b.time) - new Date(a.time))
    .slice(0, 6)
  activityLoading.value = false
}
</script>
