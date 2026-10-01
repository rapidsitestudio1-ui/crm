<template>
  <router-link :to="to" class="ov-link hover:underline">
    {{ __('View all') }}
    <img :src="arrowIcon" alt="" class="size-[13px]" />
  </router-link>
</template>

<script setup lang="ts">
import arrowIcon from './assets/arrow-right.svg'

defineProps<{ to: string | Record<string, unknown> }>()
</script>
