<script setup lang="ts">
/**
 * Customer Card Component
 */
import type { Customer } from '@/api/vendor'

interface Props {
  customer: Customer
  compact?: boolean
}

defineProps<Props>()

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  suspended: 'bg-yellow-100 text-yellow-800',
  trial: 'bg-blue-100 text-blue-800',
  terminated: 'bg-red-100 text-red-800',
}

const statusLabels: Record<string, string> = {
  active: 'Aktiv',
  suspended: 'Pausiert',
  trial: 'Testphase',
  terminated: 'Beendet',
}
</script>

<template>
  <div
    class="customer-card"
    :class="{ compact }"
    data-testid="customer-card"
  >
    <div class="card-header">
      <div class="flex items-center gap-3">
        <div class="avatar">
          {{ customer.contract_number.slice(0, 2).toUpperCase() }}
        </div>
        <div>
          <h4 class="card-title">{{ customer.contract_number }}</h4>
          <p v-if="!compact" class="text-sm text-gray-500">
            Tenant: {{ customer.tenant_id.slice(0, 8) }}...
          </p>
        </div>
      </div>
      <span
        class="status-badge"
        :class="statusColors[customer.status]"
        data-testid="status-badge"
        :data-status="customer.status"
      >
        {{ statusLabels[customer.status] }}
      </span>
    </div>

    <div v-if="!compact" class="card-body">
      <div class="license-info">
        <div class="license-item">
          <span class="license-label">Benutzer</span>
          <span class="license-value">{{ customer.licensed_users }}</span>
        </div>
        <div class="license-item">
          <span class="license-label">Behörden</span>
          <span class="license-value">{{ customer.licensed_authorities }}</span>
        </div>
      </div>

      <div v-if="customer.contract_start" class="text-sm text-gray-500 mt-2">
        Vertrag seit: {{ new Date(customer.contract_start).toLocaleDateString('de-DE') }}
      </div>
    </div>

    <div v-else class="compact-info">
      <span class="text-sm text-gray-500">
        {{ customer.licensed_users }} Benutzer · {{ customer.licensed_authorities }} Behörden
      </span>
    </div>
  </div>
</template>

<style scoped>
.customer-card {
  @apply bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow cursor-pointer;
}

.customer-card.compact {
  @apply p-3;
}

.card-header {
  @apply flex justify-between items-start;
}

.avatar {
  @apply w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-semibold;
}

.card-title {
  @apply font-semibold text-gray-900 dark:text-white;
}

.status-badge {
  @apply px-2 py-1 text-xs font-medium rounded-full;
}

.card-body {
  @apply mt-4;
}

.license-info {
  @apply flex gap-4;
}

.license-item {
  @apply flex flex-col;
}

.license-label {
  @apply text-xs text-gray-500;
}

.license-value {
  @apply text-lg font-semibold text-gray-900 dark:text-white;
}

.compact-info {
  @apply mt-2;
}
</style>
