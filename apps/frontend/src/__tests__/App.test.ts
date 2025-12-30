import { describe, it, expect } from 'vitest'

describe('App', () => {
  it('should pass a basic test', () => {
    expect(1 + 1).toBe(2)
  })

  it('should handle string operations', () => {
    const appName = 'FlowAudit'
    expect(appName).toContain('Flow')
    expect(appName.toLowerCase()).toBe('flowaudit')
  })
})

describe('Environment', () => {
  it('should have access to import.meta', () => {
    expect(import.meta).toBeDefined()
  })
})
