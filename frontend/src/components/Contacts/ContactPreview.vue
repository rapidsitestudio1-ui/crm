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
        ref="panel"
        class="ct-drawer"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        @keydown.esc.stop="close"
      >
        <!-- Header -->
        <div class="flex items-center justify-between gap-2 px-5 pt-4">
          <span class="text-[12px] font-medium" style="color: var(--kb-ink-3)">
            {{ __('Contact') }}
          </span>
          <div class="flex items-center gap-1">
            <router-link
              v-if="contactName"
              :to="{ name: 'Contact', params: { contactId: contactName } }"
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

        <div v-if="contact.loading && !doc" class="flex flex-col gap-3 px-5 pt-6">
          <div class="h-12 w-12 animate-pulse rounded-full bg-[var(--kb-hover)]" />
          <div class="h-4 w-40 animate-pulse rounded bg-[var(--kb-hover)]" />
          <div class="h-3 w-56 animate-pulse rounded bg-[var(--kb-hover)]" />
        </div>

        <div v-else-if="contact.error" class="px-5 pt-6">
          <p class="ct-sub">{{ __('This contact could not be loaded.') }}</p>
        </div>

        <div v-else-if="doc" class="flex min-h-0 flex-1 flex-col overflow-y-auto pb-6">
          <!-- Identity -->
          <div class="flex items-center gap-3.5 px-5 pt-4">
            <KanbanAvatar :image="doc.image" :label="doc.full_name || doc.name" />
            <div class="flex min-w-0 flex-col">
              <h2 :id="titleId" class="truncate text-[17px] font-semibold leading-6" style="color: var(--kb-ink)">
                {{ doc.full_name || doc.name }}
              </h2>
              <span v-if="subtitle" class="ct-sub truncate">{{ subtitle }}</span>
            </div>
          </div>
          <div v-if="relationship" class="px-5 pt-3">
            <span class="kb-badge" :class="badgeClass">{{ relationship.label }}</span>
          </div>

          <!-- Communication actions -->
          <div class="flex flex-wrap gap-2 px-5 pt-4">
            <a v-if="primaryEmail" :href="`mailto:${primaryEmail}`" class="ct-btn">
              <LucideMail />
              {{ __('Email') }}
            </a>
            <button
              v-if="primaryPhone && callEnabled"
              type="button"
              class="ct-btn"
              @click="makeCall(primaryPhone)"
            >
              <LucidePhone />
              {{ __('Call') }}
            </button>
            <a v-else-if="primaryPhone" :href="`tel:${primaryPhone}`" class="ct-btn">
              <LucidePhone />
              {{ __('Call') }}
            </a>
          </div>

          <!-- Details -->
          <section class="ct-section">
            <h3>{{ __('Details') }}</h3>
            <dl class="ct-dl">
              <template v-for="e in emails" :key="'e' + e.email_id">
                <dt>{{ e.is_primary ? __('Email') : __('Email (other)') }}</dt>
                <dd>
                  <span class="truncate">{{ e.email_id }}</span>
                  <button type="button" class="ct-copy" :aria-label="__('Copy email')" @click="copy(e.email_id)">
                    <LucideCopy />
                  </button>
                </dd>
              </template>
              <template v-for="p in phones" :key="'p' + p.phone">
                <dt>{{ p.label }}</dt>
                <dd>
                  <span class="truncate">{{ p.phone }}</span>
                  <button type="button" class="ct-copy" :aria-label="__('Copy phone number')" @click="copy(p.phone)">
                    <LucideCopy />
                  </button>
                </dd>
              </template>
              <template v-if="doc.company_name">
                <dt>{{ __('Organization') }}</dt>
                <dd>
                  <router-link
                    :to="{ name: 'Organization', params: { organizationId: doc.company_name } }"
                    class="flex min-w-0 items-center gap-2 hover:underline"
                    @click="close"
                  >
                    <KanbanAvatar :image="orgLogo" :label="doc.company_name" size="xs" square />
                    <span class="truncate">{{ doc.company_name }}</span>
                  </router-link>
                </dd>
              </template>
              <template v-if="owner">
                <dt>{{ __('Owner') }}</dt>
                <dd>
                  <KanbanAvatar :image="owner.image" :label="owner.label" size="xs" />
                  <span class="truncate">{{ owner.label }}</span>
                </dd>
              </template>
              <dt>{{ __('Created') }}</dt>
              <dd class="is-muted">{{ formatDate(doc.creation, 'MMM D, YYYY') }}</dd>
              <dt>{{ __('Last updated') }}</dt>
              <dd class="is-muted">{{ timeAgo(doc.modified) }}</dd>
            </dl>
            <p v-if="!emails.length && !phones.length" class="ct-sub pt-2">
              {{ __('No email or phone number on file.') }}
            </p>
          </section>

          <!-- Deals -->
          <section class="ct-section">
            <h3>
              {{ __('Deals') }}
              <span v-if="deals.data?.length" class="ct-tab-count">{{ deals.data.length }}</span>
            </h3>
            <p v-if="deals.loading && !deals.data" class="ct-sub">{{ __('Loading…') }}</p>
            <p v-else-if="!deals.data?.length" class="ct-sub">
              {{ __('Not linked to any deal yet.') }}
            </p>
            <ul v-else class="flex flex-col gap-1.5">
              <li v-for="d in deals.data" :key="d.name">
                <router-link
                  :to="{ name: 'Deal', params: { dealId: d.name } }"
                  class="ct-deal"
                  @click="close"
                >
                  <span class="flex min-w-0 flex-col">
                    <span class="truncate text-[13px] font-medium" style="color: var(--kb-ink)">
                      {{ d.organization || d.name }}
                    </span>
                    <span class="ct-sub truncate">{{ dealValue(d) }}</span>
                  </span>
                  <span class="kb-badge shrink-0">
                    <span class="size-1.5 rounded-full" :style="{ background: stageDot(d.status) }" />
                    {{ __(d.status) }}
                  </span>
                </router-link>
              </li>
            </ul>
          </section>

          <!-- Recent activity on the linked deals -->
          <section class="ct-section">
            <h3>{{ __('Recent activity') }}</h3>
            <p v-if="activity.loading" class="ct-sub">{{ __('Loading…') }}</p>
            <p v-else-if="!activity.items.length" class="ct-sub">
              {{
                deals.data?.length
                  ? __('No notes, emails or comments on their deals yet.')
                  : __('Activity appears here once they are on a deal.')
              }}
            </p>
            <ul v-else class="flex flex-col">
              <li v-for="(a, i) in activity.items" :key="i" class="ct-activity">
                <span class="ct-activity-icon"><component :is="a.icon" /></span>
                <span class="flex min-w-0 flex-1 flex-col">
                  <span class="truncate text-[13px]" style="color: var(--kb-ink)">{{ a.title }}</span>
                  <span v-if="a.text" class="ct-sub line-clamp-2">{{ a.text }}</span>
                </span>
                <span class="shrink-0 text-[11.5px]" style="color: var(--kb-ink-3)">
                  {{ timeAgo(a.time) }}
                </span>
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
import LucideMail from '~icons/lucide/mail'
import LucidePhone from '~icons/lucide/phone'
import LucideCopy from '~icons/lucide/copy'
import LucideStickyNote from '~icons/lucide/sticky-note'
import LucideMessageSquare from '~icons/lucide/message-square'
import LucideInbox from '~icons/lucide/inbox'
import LucideSend from '~icons/lucide/send'
import KanbanAvatar from '@/components/Kanban/KanbanAvatar.vue'
import { getStageTone } from '@/components/Kanban/stageTones'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { organizationsStore } from '@/stores/organizations.js'
import { callEnabled } from '@/composables/telephony'
import { formatDate, timeAgo } from '@/utils'
import { call, createResource, toast } from 'frappe-ui'
import { computed, nextTick, reactive, ref, useId, watch } from 'vue'

const props = defineProps({
  // Relationship badge for this contact ({ label, tone }), from the list page.
  relationship: { type: Object, default: null },
})
const contactName = defineModel({ type: String, default: null })

const open = computed(() => Boolean(contactName.value))
const titleId = `ct-preview-${useId()}`
const panel = ref(null)
const closeBtn = ref(null)
let returnFocusTo = null

const { makeCall } = globalStore()
const { getUser } = usersStore()
const { getDealStatus } = statusesStore()
const { getOrganization } = organizationsStore()

// Existing APIs: the Contact document, and the CRM's linked-deals endpoint
// (the same one the full contact page uses).
const contact = createResource({ url: 'frappe.client.get' })
const deals = createResource({ url: 'crm.api.contact.get_linked_deals' })
const activity = reactive({ loading: false, items: [] })

const doc = computed(() =>
  contact.data && contact.data.name === contactName.value ? contact.data : null,
)

watch(contactName, async (name) => {
  if (!name) return
  returnFocusTo = document.activeElement
  contact.submit({ doctype: 'Contact', name })
  await deals.submit({ contact: name }).catch(() => null)
  loadActivity(name)
  await nextTick()
  closeBtn.value?.focus()
}, { immediate: true })

function close() {
  contactName.value = null
  returnFocusTo?.focus?.()
}

const emails = computed(() => {
  const list = doc.value?.email_ids?.length
    ? doc.value.email_ids
    : doc.value?.email_id
      ? [{ email_id: doc.value.email_id, is_primary: 1 }]
      : []
  return [...list].sort((a, b) => (b.is_primary || 0) - (a.is_primary || 0))
})
const phones = computed(() => {
  const list = doc.value?.phone_nos?.length
    ? doc.value.phone_nos
    : [doc.value?.mobile_no, doc.value?.phone].filter(Boolean).map((phone) => ({ phone }))
  return list.map((p) => ({
    phone: p.phone,
    label: p.is_primary_mobile_no ? __('Mobile') : p.is_primary_phone ? __('Phone') : __('Phone'),
  }))
})
const primaryEmail = computed(() => emails.value[0]?.email_id || '')
const primaryPhone = computed(
  () => doc.value?.mobile_no || doc.value?.phone || phones.value[0]?.phone || '',
)
const subtitle = computed(() =>
  [doc.value?.designation, doc.value?.company_name].filter(Boolean).join(' · '),
)
const orgLogo = computed(() => getOrganization(doc.value?.company_name)?.organization_logo)
const owner = computed(() => {
  const o = doc.value?.owner && getUser(doc.value.owner)
  return o?.full_name ? { label: o.full_name, image: o.user_image } : null
})
const badgeClass = computed(
  () => ({ success: 'is-success', accent: 'is-accent' })[props.relationship?.tone] || '',
)

function stageDot(status) {
  return getStageTone('CRM Deal', { name: status }, getDealStatus(status)).dot
}

function dealValue(d) {
  if (!d.deal_value) return __('No value')
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: d.currency || 'USD',
      maximumFractionDigits: 0,
    }).format(d.deal_value)
  } catch {
    return `${d.currency || ''} ${d.deal_value}`
  }
}

function stripHtml(html) {
  const el = document.createElement('div')
  el.innerHTML = html || ''
  return (el.textContent || '').trim()
}

// Latest notes, emails and comments on the contact's deals (read-only).
async function loadActivity(name) {
  activity.items = []
  const dealNames = (deals.data || []).map((d) => d.name)
  if (!dealNames.length || name !== contactName.value) return
  activity.loading = true
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
  if (name !== contactName.value) return
  activity.items = [
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
  activity.loading = false
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    toast.success(__('Copied'))
  } catch {
    toast.error(__('Could not copy'))
  }
}
</script>
