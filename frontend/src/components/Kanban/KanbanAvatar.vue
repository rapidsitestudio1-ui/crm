<template>
  <Avatar
    v-if="image"
    :image="image"
    :label="label"
    :size="{ xl: '3xl', md: 'lg', sm: 'sm' }[size] || 'xs'"
    :shape="square ? 'square' : 'circle'"
  />
  <span
    v-else
    class="kb-avatar"
    :class="square ? 'rounded-[7px]' : ''"
    :style="{
      width: px + 'px',
      height: px + 'px',
      fontSize: fontPx + 'px',
      '--av-bg': tone[0],
      '--av-ink': tone[1],
    }"
    :title="label"
    aria-hidden="true"
  >
    {{ initialsOf(label) }}
  </span>
</template>

<script setup>
import { Avatar } from 'frappe-ui'
import { computed } from 'vue'
import { avatarTone, initialsOf } from './stageTones'

const props = defineProps({
  image: { type: String, default: '' },
  label: { type: String, default: '' },
  size: { type: String, default: 'md' }, // xl 56, md 32, sm 24, xs 20
  square: { type: Boolean, default: false },
})

const px = computed(() => ({ xl: 56, md: 32, sm: 24, xs: 20 })[props.size] || 32)
const fontPx = computed(() => ({ xl: 19, md: 12, sm: 10, xs: 9 })[props.size] || 12)
const tone = computed(() => avatarTone(props.label))
</script>
