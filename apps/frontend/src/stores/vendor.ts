/**
 * Vendor Store (Layer 0)
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Vendor,
  VendorUser,
  VendorRole,
  Customer,
  CustomerWithLicenses,
  Module,
  ModuleDeployment,
  LicenseAlert,
} from '@/api/vendor'
import * as vendorApi from '@/api/vendor'

export const useVendorStore = defineStore('vendor', () => {
  // State
  const vendor = ref<Vendor | null>(null)
  const currentUser = ref<VendorUser | null>(null)
  const vendorUsers = ref<VendorUser[]>([])
  const customers = ref<Customer[]>([])
  const selectedCustomer = ref<CustomerWithLicenses | null>(null)
  const modules = ref<Module[]>([])
  const selectedModule = ref<(Module & { deployments: ModuleDeployment[] }) | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const isAuthenticated = computed(() => !!currentUser.value)
  const isVendorAdmin = computed(() => currentUser.value?.role === 'vendor_admin')
  const isVendorDeveloper = computed(() =>
    ['vendor_admin', 'vendor_developer', 'vendor_qa'].includes(currentUser.value?.role || '')
  )
  const isVendorQA = computed(() =>
    ['vendor_admin', 'vendor_qa'].includes(currentUser.value?.role || '')
  )

  const activeCustomers = computed(() =>
    customers.value.filter((c) => c.status === 'active')
  )

  const customersWithAlerts = computed(() =>
    customers.value.filter(() => {
      const details = selectedCustomer.value
      return details?.license_alerts?.some((a: LicenseAlert) => !a.acknowledged) || false
    })
  )

  const releasedModules = computed(() =>
    modules.value.filter((m) => m.status === 'released')
  )

  // Actions
  async function login(email: string, password: string) {
    isLoading.value = true
    error.value = null
    try {
      const result = await vendorApi.vendorLogin(email, password)
      currentUser.value = result.user
      await fetchVendor()
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Login failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    vendorApi.clearVendorToken()
    currentUser.value = null
    vendor.value = null
    vendorUsers.value = []
    customers.value = []
    selectedCustomer.value = null
    modules.value = []
    selectedModule.value = null
  }

  async function fetchVendor() {
    isLoading.value = true
    try {
      vendor.value = await vendorApi.getVendor()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch vendor'
    } finally {
      isLoading.value = false
    }
  }

  async function updateVendor(data: Partial<Vendor>) {
    isLoading.value = true
    try {
      vendor.value = await vendorApi.updateVendor(data)
      return vendor.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update vendor'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  // Vendor Users
  async function fetchVendorUsers() {
    isLoading.value = true
    try {
      const result = await vendorApi.listVendorUsers()
      vendorUsers.value = result.users
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch users'
    } finally {
      isLoading.value = false
    }
  }

  async function createVendorUser(data: {
    email: string
    password: string
    first_name: string
    last_name: string
    role: VendorRole
  }) {
    isLoading.value = true
    try {
      const user = await vendorApi.createVendorUser(data)
      vendorUsers.value.push(user)
      return user
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create user'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function updateVendorUser(userId: string, data: Partial<VendorUser & { password?: string }>) {
    isLoading.value = true
    try {
      const user = await vendorApi.updateVendorUser(userId, data)
      const index = vendorUsers.value.findIndex((u) => u.id === userId)
      if (index !== -1) {
        vendorUsers.value[index] = user
      }
      return user
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update user'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function deactivateVendorUser(userId: string) {
    isLoading.value = true
    try {
      await vendorApi.deactivateVendorUser(userId)
      const index = vendorUsers.value.findIndex((u) => u.id === userId)
      if (index !== -1) {
        vendorUsers.value[index].is_active = false
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to deactivate user'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  // Customers
  async function fetchCustomers(params?: { status?: string }) {
    isLoading.value = true
    try {
      const result = await vendorApi.listCustomers(params as { status?: 'active' | 'suspended' | 'trial' | 'terminated' })
      customers.value = result.customers
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch customers'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCustomer(customerId: string) {
    isLoading.value = true
    try {
      selectedCustomer.value = await vendorApi.getCustomer(customerId)
      return selectedCustomer.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch customer'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function createCustomer(data: Parameters<typeof vendorApi.createCustomer>[0]) {
    isLoading.value = true
    try {
      const customer = await vendorApi.createCustomer(data)
      customers.value.push(customer)
      return customer
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create customer'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function updateCustomer(customerId: string, data: Partial<Customer>) {
    isLoading.value = true
    try {
      const customer = await vendorApi.updateCustomer(customerId, data)
      const index = customers.value.findIndex((c) => c.id === customerId)
      if (index !== -1) {
        customers.value[index] = customer
      }
      return customer
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update customer'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function terminateCustomer(customerId: string) {
    isLoading.value = true
    try {
      await vendorApi.terminateCustomer(customerId)
      const index = customers.value.findIndex((c) => c.id === customerId)
      if (index !== -1) {
        customers.value[index].status = 'terminated'
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to terminate customer'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function adjustLicenses(customerId: string, data: { licensed_users?: number; licensed_authorities?: number }) {
    isLoading.value = true
    try {
      const customer = await vendorApi.adjustLicenses(customerId, data)
      const index = customers.value.findIndex((c) => c.id === customerId)
      if (index !== -1) {
        customers.value[index] = customer
      }
      return customer
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to adjust licenses'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  // Modules
  async function fetchModules(params?: { status?: string }) {
    isLoading.value = true
    try {
      const result = await vendorApi.listModules(params as { status?: 'development' | 'testing' | 'released' | 'deprecated' })
      modules.value = result.modules
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch modules'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchModule(moduleId: string) {
    isLoading.value = true
    try {
      selectedModule.value = await vendorApi.getModule(moduleId)
      return selectedModule.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch module'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function createModule(data: Parameters<typeof vendorApi.createModule>[0]) {
    isLoading.value = true
    try {
      const module = await vendorApi.createModule(data)
      modules.value.push(module)
      return module
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create module'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function releaseModule(moduleId: string, releaseNote?: Parameters<typeof vendorApi.releaseModule>[1]) {
    isLoading.value = true
    try {
      const module = await vendorApi.releaseModule(moduleId, releaseNote)
      const index = modules.value.findIndex((m) => m.id === moduleId)
      if (index !== -1) {
        modules.value[index] = module
      }
      return module
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to release module'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function deployModule(moduleId: string, customerId: string) {
    isLoading.value = true
    try {
      const deployment = await vendorApi.deployModule(moduleId, customerId)
      if (selectedModule.value && selectedModule.value.id === moduleId) {
        selectedModule.value.deployments.push(deployment)
      }
      return deployment
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to deploy module'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    vendor,
    currentUser,
    vendorUsers,
    customers,
    selectedCustomer,
    modules,
    selectedModule,
    isLoading,
    error,
    // Computed
    isAuthenticated,
    isVendorAdmin,
    isVendorDeveloper,
    isVendorQA,
    activeCustomers,
    customersWithAlerts,
    releasedModules,
    // Actions
    login,
    logout,
    fetchVendor,
    updateVendor,
    fetchVendorUsers,
    createVendorUser,
    updateVendorUser,
    deactivateVendorUser,
    fetchCustomers,
    fetchCustomer,
    createCustomer,
    updateCustomer,
    terminateCustomer,
    adjustLicenses,
    fetchModules,
    fetchModule,
    createModule,
    releaseModule,
    deployModule,
  }
})
