<script setup lang="ts">
/**
 * Vendor Dashboard - Layer 0
 * Overview of customers, licenses, and modules
 */
import { ref, onMounted, computed } from 'vue'
import { useVendorStore } from '@/stores/vendor'
import CustomerCard from '@/components/vendor/CustomerCard.vue'
import ModuleCard from '@/components/vendor/ModuleCard.vue'

const vendorStore = useVendorStore()

const activeTab = ref<'overview' | 'customers' | 'modules'>('overview')

// Statistics
const totalLicenses = computed(() =>
  vendorStore.customers.reduce((sum, c) => sum + c.licensed_users, 0)
)

const totalAuthorities = computed(() =>
  vendorStore.customers.reduce((sum, c) => sum + c.licensed_authorities, 0)
)

onMounted(async () => {
  await Promise.all([
    vendorStore.fetchCustomers(),
    vendorStore.fetchModules(),
  ])
})
</script>

<template>
  <div class="vendor-dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ vendorStore.vendor?.name || 'Vendor Dashboard' }}
        </h1>
        <p class="text-gray-500 dark:text-gray-400">
          Willkommen, {{ vendorStore.currentUser?.first_name }}
        </p>
      </div>
      <div class="flex gap-2">
        <span
          class="px-3 py-1 text-sm rounded-full"
          :class="{
            'bg-purple-100 text-purple-800': vendorStore.currentUser?.role === 'vendor_admin',
            'bg-blue-100 text-blue-800': vendorStore.currentUser?.role === 'vendor_developer',
            'bg-green-100 text-green-800': vendorStore.currentUser?.role === 'vendor_qa',
            'bg-gray-100 text-gray-800': vendorStore.currentUser?.role === 'vendor_support',
          }"
        >
          {{ vendorStore.currentUser?.role?.replace('vendor_', '').toUpperCase() }}
        </span>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon bg-blue-100 text-blue-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
        </div>
        <div class="stat-content">
          <p class="stat-value">{{ vendorStore.customers.length }}</p>
          <p class="stat-label">Kunden</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-green-100 text-green-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
        </div>
        <div class="stat-content">
          <p class="stat-value">{{ totalLicenses }}</p>
          <p class="stat-label">Lizenzen (Benutzer)</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-purple-100 text-purple-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
        </div>
        <div class="stat-content">
          <p class="stat-value">{{ totalAuthorities }}</p>
          <p class="stat-label">Behörden</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bg-orange-100 text-orange-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
            />
          </svg>
        </div>
        <div class="stat-content">
          <p class="stat-value">{{ vendorStore.modules.length }}</p>
          <p class="stat-label">Module</p>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs-container">
      <nav class="tabs">
        <button
          @click="activeTab = 'overview'"
          :class="['tab', { active: activeTab === 'overview' }]"
        >
          Übersicht
        </button>
        <button
          @click="activeTab = 'customers'"
          :class="['tab', { active: activeTab === 'customers' }]"
        >
          Kunden
        </button>
        <button
          @click="activeTab = 'modules'"
          :class="['tab', { active: activeTab === 'modules' }]"
        >
          Module
        </button>
      </nav>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Overview Tab -->
      <div v-if="activeTab === 'overview'" class="overview-content">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Recent Customers -->
          <div class="panel">
            <h3 class="panel-title">Aktive Kunden</h3>
            <div class="space-y-3">
              <CustomerCard
                v-for="customer in vendorStore.activeCustomers.slice(0, 5)"
                :key="customer.id"
                :customer="customer"
                compact
              />
              <p v-if="vendorStore.activeCustomers.length === 0" class="text-gray-500 text-center py-4">
                Keine aktiven Kunden
              </p>
            </div>
          </div>

          <!-- Released Modules -->
          <div class="panel">
            <h3 class="panel-title">Released Module</h3>
            <div class="space-y-3">
              <ModuleCard
                v-for="module in vendorStore.releasedModules.slice(0, 5)"
                :key="module.id"
                :module="module"
                compact
              />
              <p v-if="vendorStore.releasedModules.length === 0" class="text-gray-500 text-center py-4">
                Keine released Module
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Customers Tab -->
      <div v-if="activeTab === 'customers'" class="customers-content">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold">Alle Kunden</h3>
          <button
            v-if="vendorStore.isVendorAdmin"
            class="btn btn-primary"
            @click="$router.push('/vendor/customers/new')"
          >
            Neuer Kunde
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <CustomerCard
            v-for="customer in vendorStore.customers"
            :key="customer.id"
            :customer="customer"
            @click="$router.push(`/vendor/customers/${customer.id}`)"
          />
        </div>
      </div>

      <!-- Modules Tab -->
      <div v-if="activeTab === 'modules'" class="modules-content">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold">Alle Module</h3>
          <button
            v-if="vendorStore.isVendorDeveloper"
            class="btn btn-primary"
            @click="$router.push('/vendor/modules/new')"
          >
            Neues Modul
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ModuleCard
            v-for="module in vendorStore.modules"
            :key="module.id"
            :module="module"
            @click="$router.push(`/vendor/modules/${module.id}`)"
          />
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="vendorStore.isLoading" class="loading-overlay">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<style scoped>
.vendor-dashboard {
  @apply p-6 max-w-7xl mx-auto;
}

.dashboard-header {
  @apply flex justify-between items-start mb-6;
}

.stats-grid {
  @apply grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6;
}

.stat-card {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow p-4 flex items-center gap-4;
}

.stat-icon {
  @apply p-3 rounded-lg;
}

.stat-content {
  @apply flex flex-col;
}

.stat-value {
  @apply text-2xl font-bold text-gray-900 dark:text-white;
}

.stat-label {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.tabs-container {
  @apply mb-6;
}

.tabs {
  @apply flex gap-1 border-b border-gray-200 dark:border-gray-700;
}

.tab {
  @apply px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 border-b-2 border-transparent -mb-px transition-colors;
}

.tab.active {
  @apply text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-400;
}

.panel {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow p-4;
}

.panel-title {
  @apply text-lg font-semibold text-gray-900 dark:text-white mb-4;
}

.btn {
  @apply px-4 py-2 rounded-lg font-medium transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.loading-overlay {
  @apply fixed inset-0 bg-black/30 flex items-center justify-center z-50;
}

.spinner {
  @apply w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin;
}
</style>
