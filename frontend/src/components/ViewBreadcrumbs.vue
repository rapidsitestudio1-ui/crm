<template>
  <div class="flex items-center">
    <router-link
      :to="{ name: routeName }"
      class="px-0.5 py-1 text-lg-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
      :class="[
        viewControls && viewControls.viewsDropdownOptions
          ? 'text-ink-gray-5 hover:text-ink-gray-7'
          : 'text-ink-gray-7',
      ]"
    >
      {{ __(routeName) }}
    </router-link>
    <span
      v-if="viewControls && viewControls.viewsDropdownOptions"
      class="mx-0.5 text-base text-ink-gray-4"
      aria-hidden="true"
    >
      /
    </span>

    <!-- Segmented view-type switcher (Figma "Tabs"), shown when a page offers
         more than one standard view type. Saved views stay in the dropdown. -->
    <template v-if="useSegments">
      <div
        role="tablist"
        :aria-label="__('View type')"
        class="ml-1 flex items-center gap-0.5 rounded-md border border-outline-gray-1 bg-surface-gray-2 p-0.5"
      >
        <button
          v-for="view in standardViews"
          :key="view.name"
          role="tab"
          :aria-selected="isActiveSegment(view)"
          class="flex h-6 items-center gap-1.5 rounded-[6px] px-2.5 text-base-medium text-nowrap transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
          :class="
            isActiveSegment(view)
              ? 'bg-surface-base text-ink-gray-9 shadow-sm'
              : 'text-ink-gray-5 hover:text-ink-gray-8'
          "
          @click="view.onClick()"
        >
          <Icon :icon="view.icon" class="h-3.5" />
          {{ view.label }}
        </button>
      </div>
      <Dropdown :options="otherViewOptions">
        <template #default="{ open }">
          <Button
            variant="ghost"
            class="ml-1 text-base-medium text-nowrap"
            :label="customView ? customView.label : __('Views')"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          >
            <template v-if="customView" #prefix>
              <Icon :icon="customView.icon" class="h-4" />
            </template>
          </Button>
        </template>
        <template #item-suffix="{ item, close, selected }">
          <div v-if="item.name" class="flex flex-row-reverse gap-2 items-center">
            <Dropdown
              side="right"
              :offset="15"
              :options="viewControls.viewActions(item, close)"
            >
              <template #default>
                <Button
                  variant="ghost"
                  class="view-action-btn !size-5 opacity-0"
                  icon="lucide-more-horizontal"
                  @click.stop
                />
              </template>
            </Dropdown>
            <span
              v-if="selected"
              class="lucide-check size-4 text-ink-gray-7"
              aria-hidden="true"
            />
          </div>
        </template>
      </Dropdown>
    </template>

    <Dropdown
      v-else-if="viewControls && viewControls.viewsDropdownOptions"
      :options="viewControls.viewsDropdownOptions"
    >
      <template #default="{ open }">
        <Button
          variant="ghost"
          class="text-lg-medium text-nowrap"
          :label="__(viewControls.currentView?.label)"
          :iconRight="open ? 'chevron-up' : 'chevron-down'"
        >
          <template #prefix>
            <Icon :icon="viewControls.currentView?.icon" class="h-4" />
          </template>
        </Button>
      </template>
      <template #item-suffix="{ item, close, selected }">
        <div v-if="item.name" class="flex flex-row-reverse gap-2 items-center">
          <Dropdown
            side="right"
            :offset="15"
            :options="viewControls.viewActions(item, close)"
          >
            <template #default>
              <Button
                variant="ghost"
                class="view-action-btn !size-5 opacity-0"
                icon="lucide-more-horizontal"
                @click.stop
              />
            </template>
          </Dropdown>
          <span
            v-if="selected"
            class="lucide-check size-4 text-ink-gray-7"
            aria-hidden="true"
          />
        </div>
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import { Dropdown } from 'frappe-ui'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  routeName: { type: String, required: true },
})

const viewControls = defineModel({ type: Object, default: () => ({}) })
const route = useRoute()

// First group of viewsDropdownOptions is always the standard view types.
const standardViews = computed(
  () => viewControls.value?.viewsDropdownOptions?.[0]?.items || [],
)
const otherViewOptions = computed(
  () => viewControls.value?.viewsDropdownOptions?.slice(1) || [],
)
const useSegments = computed(() => standardViews.value.length > 1)

const customView = computed(() =>
  otherViewOptions.value
    .flatMap((group) => group.items || [])
    .find((item) => item.selected),
)

// A saved view still has a type; keep its type's segment highlighted.
function isActiveSegment(view) {
  if (view.selected) return true
  return (
    !standardViews.value.some((v) => v.selected) &&
    view.name === (route.params.viewType || 'list')
  )
}
</script>

<style scoped>
/* frappe-ui's Menu rewrite dropped the `group` class from item rows, so
   reveal the view actions on row hover/highlight instead of `group-hover`. */
[data-slot='item']:hover .view-action-btn,
[data-slot='item'][data-highlighted] .view-action-btn {
  opacity: 1;
}
</style>
