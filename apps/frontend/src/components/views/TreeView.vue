<script setup lang="ts">
import { ref } from 'vue'
import { usePreferences } from '@/composables/usePreferences'
import { useAuthStore } from '@/stores/auth'

const { sidebarCollapsed, toggleSidebar } = usePreferences()
const authStore = useAuthStore()

interface TreeNode {
  id: string
  name: string
  icon: string
  route?: string
  children?: TreeNode[]
  badge?: number
  locked?: boolean
}

const expandedNodes = ref<Set<string>>(new Set(['audits', 'checklists']))

const treeData: TreeNode[] = [
  {
    id: 'audits',
    name: 'Prüfungen',
    icon: 'clipboard',
    children: [
      { id: 'audits-operations', name: 'Vorhaben', icon: 'dot', route: '/audits/operations' },
      { id: 'audits-system', name: 'System', icon: 'dot', route: '/audits/system' },
      { id: 'audits-accounts', name: 'Rechnung', icon: 'dot', route: '/audits/accounts' }
    ],
    badge: 2
  },
  { id: 'reports', name: 'Auswertungen', icon: 'chart', route: '/reports', badge: 3 },
  { id: 'group', name: 'Konzern', icon: 'building', route: '/group-queries' },
  {
    id: 'checklists',
    name: 'Checklisten',
    icon: 'checklist',
    children: [
      { id: 'checklists-designer', name: 'Designer', icon: 'dot', route: '/checklists/designer' },
      { id: 'checklists-templates', name: 'Vorlagen', icon: 'dot', route: '/checklists/templates' },
      { id: 'checklists-textmodules', name: 'Textbausteine', icon: 'dot', route: '/checklists/textmodules' }
    ]
  },
  { id: 'documents', name: 'Dokumente', icon: 'folder', route: '/documents' },
  { id: 'sampling', name: 'Stichproben', icon: 'random', route: '/sampling' },
  { id: 'jkb', name: 'Berichte', icon: 'file', route: '/jkb' },
  { id: 'admin', name: 'Administration', icon: 'cog', route: '/admin' },
  { id: 'flowinvoice', name: 'FlowInvoice', icon: 'lock', route: '/flowinvoice', locked: true }
]

const recentActivities = [
  { id: 1, text: 'Stellungnahme eingegangen', subtext: 'VH-2024-0234', time: 'vor 2 Std' },
  { id: 2, text: 'Bericht freigegeben', subtext: 'VH-2024-0201', time: 'vor 5 Std' },
  { id: 3, text: 'Neue Dokumente verfügbar', subtext: 'VH-2024-0189', time: 'Gestern' }
]

function toggleNode(nodeId: string): void {
  if (expandedNodes.value.has(nodeId)) {
    expandedNodes.value.delete(nodeId)
  } else {
    expandedNodes.value.add(nodeId)
  }
}

function isExpanded(nodeId: string): boolean {
  return expandedNodes.value.has(nodeId)
}
</script>

<template>
  <div class="flex h-[calc(100vh-8rem)]">
    <!-- Sidebar Tree -->
    <aside
      :class="[
        'flex-shrink-0 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-y-auto transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-64'
      ]"
    >
      <!-- Logo -->
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <div v-if="!sidebarCollapsed" class="flex items-center gap-2">
          <div class="w-8 h-8 bg-accent-600 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="font-semibold text-gray-900 dark:text-white">FlowAudit</span>
        </div>
        <div v-else class="w-8 h-8 bg-accent-600 rounded-lg flex items-center justify-center mx-auto">
          <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>

      <!-- Search -->
      <div v-if="!sidebarCollapsed" class="p-3">
        <div class="relative">
          <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            class="input pl-8 py-1.5 text-sm"
            placeholder="Suchen..."
          />
        </div>
      </div>

      <!-- Tree Navigation -->
      <nav class="p-2 space-y-0.5">
        <template v-for="node in treeData" :key="node.id">
          <!-- Parent Node -->
          <div
            :class="[
              'flex items-center gap-2 px-3 py-2 rounded-lg text-sm cursor-pointer transition-colors',
              node.locked
                ? 'opacity-50 text-gray-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            ]"
            @click="node.children ? toggleNode(node.id) : null"
          >
            <!-- Expand Icon -->
            <svg
              v-if="node.children && !sidebarCollapsed"
              :class="[
                'w-4 h-4 transition-transform',
                isExpanded(node.id) ? 'rotate-90' : ''
              ]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            <span v-else-if="!sidebarCollapsed" class="w-4" />

            <!-- Icon -->
            <svg v-if="node.icon === 'clipboard'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <svg v-else-if="node.icon === 'chart'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <svg v-else-if="node.icon === 'building'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <svg v-else-if="node.icon === 'checklist'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            <svg v-else-if="node.icon === 'folder'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <svg v-else-if="node.icon === 'random'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <svg v-else-if="node.icon === 'file'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <svg v-else-if="node.icon === 'cog'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <svg v-else-if="node.icon === 'lock'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>

            <!-- Name -->
            <span v-if="!sidebarCollapsed" class="flex-1 truncate">{{ node.name }}</span>

            <!-- Badge -->
            <span
              v-if="node.badge && !sidebarCollapsed"
              class="px-1.5 py-0.5 text-xs font-medium bg-accent-100 text-accent-700 dark:bg-accent-900 dark:text-accent-300 rounded-full"
            >
              {{ node.badge }}
            </span>
          </div>

          <!-- Children -->
          <div
            v-if="node.children && isExpanded(node.id) && !sidebarCollapsed"
            class="ml-6 space-y-0.5"
          >
            <router-link
              v-for="child in node.children"
              :key="child.id"
              :to="child.route || '#'"
              class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <span class="w-4 border-l-2 border-gray-300 dark:border-gray-600 h-3" />
              <span>{{ child.name }}</span>
            </router-link>
          </div>
        </template>
      </nav>

      <!-- Collapse Toggle -->
      <div class="absolute bottom-4 left-0 right-0 px-3">
        <button
          class="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          @click="toggleSidebar"
        >
          <svg
            :class="['w-5 h-5 transition-transform', sidebarCollapsed ? 'rotate-180' : '']"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
          <span v-if="!sidebarCollapsed">Einklappen</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto p-6">
      <div class="max-w-3xl mx-auto space-y-6">
        <!-- Welcome Card -->
        <div class="card p-6 text-center">
          <h1 class="text-xl font-semibold text-gray-900 dark:text-white">
            Willkommen zurück, {{ authStore.user?.firstName }}! 👋
          </h1>
          <p class="mt-2 text-gray-500 dark:text-gray-400">
            Du hast 2 überfällige Prüfungen und 3 anstehende Termine diese Woche.
          </p>
          <button class="btn-primary mt-4">
            Los geht's →
          </button>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-3 gap-4">
          <div class="card p-4 text-center">
            <div class="text-2xl font-bold text-gray-900 dark:text-white">12</div>
            <div class="text-sm text-gray-500">aktiv</div>
          </div>
          <div class="card p-4 text-center">
            <div class="text-2xl font-bold text-amber-600">2</div>
            <div class="text-sm text-gray-500">⚠️ fällig</div>
          </div>
          <div class="card p-4 text-center">
            <div class="text-2xl font-bold text-green-600">8</div>
            <div class="text-sm text-gray-500">✅ fertig</div>
          </div>
        </div>

        <!-- Recent Activities -->
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-medium text-gray-900 dark:text-white">Letzte Aktivitäten</h2>
          </div>
          <div class="divide-y divide-gray-200 dark:divide-gray-700">
            <div
              v-for="activity in recentActivities"
              :key="activity.id"
              class="px-6 py-3 flex items-center justify-between"
            >
              <div>
                <p class="text-sm text-gray-900 dark:text-white">{{ activity.text }}</p>
                <p class="text-xs text-gray-500">{{ activity.subtext }}</p>
              </div>
              <span class="text-xs text-gray-400">{{ activity.time }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
