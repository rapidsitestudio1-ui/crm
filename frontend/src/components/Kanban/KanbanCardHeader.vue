<template>
  <div class="flex flex-col gap-2.5">
    <div class="flex items-center gap-3">
      <KanbanAvatar :image="image" :label="title || '?'" :square="square" />
      <div class="flex min-w-0 flex-1 flex-col">
        <span class="kb-title truncate">{{ title || __('No Title') }}</span>
        <span v-if="subtitle" class="kb-subtitle truncate">{{ subtitle }}</span>
      </div>
      <!-- Existing card actions (call / note / task), revealed on hover or focus. -->
      <div class="kb-reveal -mr-1.5 shrink-0 self-start" @click.stop.prevent>
        <slot name="actions" />
      </div>
    </div>

    <slot />

    <div v-if="email || phone" class="flex flex-col gap-1">
      <div v-if="email" class="kb-meta">
        <LucideMail />
        <span class="truncate">{{ email }}</span>
      </div>
      <div v-if="phone" class="kb-meta">
        <LucidePhone />
        <span class="truncate">{{ phone }}</span>
      </div>
    </div>

    <div v-if="$slots.badges" class="flex flex-wrap items-center gap-1.5">
      <slot name="badges" />
    </div>
  </div>
</template>

<script setup>
import LucideMail from '~icons/lucide/mail'
import LucidePhone from '~icons/lucide/phone'
import KanbanAvatar from './KanbanAvatar.vue'

defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  image: { type: String, default: '' },
  square: { type: Boolean, default: false },
  email: { type: String, default: '' },
  phone: { type: String, default: '' },
})
</script>
