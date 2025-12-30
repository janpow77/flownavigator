import { defineConfig } from 'tsup'

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['cjs', 'esm'],
  dts: true,
  clean: true,
  sourcemap: true,
  splitting: false,
  external: [
    'vue',
    '@flowaudit/common',
    '@flowaudit/checklists',
    '@flowaudit/group-queries',
    '@flowaudit/document-box',
  ],
})
