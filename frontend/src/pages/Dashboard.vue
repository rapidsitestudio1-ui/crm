<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Dashboard" />
      </template>
      <template #right-header>
        <Link
          v-if="isAdmin() || isManager()"
          class="form-control w-48"
          variant="outline"
          :value="user && getUser(user).full_name"
          doctype="User"
          :filters="{
            name: ['in', users.data.crmUsers?.map((u) => u.name)],
            ignore_user_type: 1,
          }"
          :placeholder="__('Sales User')"
          :hideMe="true"
          @change="(v) => (user = v)"
        >
          <template #prefix>
            <UserAvatar v-if="user" class="mr-2" :user="user" size="sm" />
          </template>
          <template #item-prefix="{ option }">
            <UserAvatar class="mr-2" :user="option.value" size="sm" />
          </template>
          <template #item-label="{ option }">
            <Tooltip :text="option.value">
              <div class="cursor-pointer text-ink-gray-9">
                {{ getUser(option.value).full_name }}
              </div>
            </Tooltip>
          </template>
        </Link>
        <Button
          :label="__('Refresh')"
          :iconLeft="LucideRefreshCcw"
          @click="overview?.reload()"
        />
      </template>
    </LayoutHeader>

    <div class="w-full flex-1 overflow-y-auto">
      <OverviewDashboard ref="overview" :user="user" />
    </div>
  </div>
</template>

<script setup lang="ts">
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import OverviewDashboard from '@/components/Dashboard/Overview/OverviewDashboard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { usePageMeta, Tooltip } from 'frappe-ui'
import { ref } from 'vue'

const { users, getUser, isManager, isAdmin } = usersStore()

const user = ref<string | null>(null)
const overview = ref<InstanceType<typeof OverviewDashboard>>()

usePageMeta(() => {
  return { title: __('CRM Dashboard') }
})
</script>
