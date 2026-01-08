# Implementiere Frontend Wizard

## WICHTIG: Autonome Ausführung

**Arbeite OHNE Rückfragen!** Führe alle Schritte selbstständig aus:
1. Lies die bestehenden Vue-Komponenten um den Stil zu verstehen
2. Erstelle alle Verzeichnisse und Dateien
3. Implementiere alle Steps vollständig
4. Erstelle den Module Store und API Service
5. Registriere die Routes
6. Teste mit `npm run dev` und behebe Fehler
7. Führe `npm run lint` aus und behebe Warnungen
8. Committe und pushe erst wenn alles funktioniert
9. Fahre dann mit `/implement-staging` fort

**Keine Fragen stellen - einfach machen!**

---

## Aufgabe
Erstelle den Module Converter Wizard als Vue 3 Komponente mit PrimeVue basierend auf `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md`.

## Wizard-Schritte

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  Modus  │ → │  Upload │ → │   LLM   │ → │  Review │ → │ Staging │
│  wählen │   │/Auswahl │   │ Convert │   │  & Edit │   │ & GitHub│
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

## Zu erstellende Dateien

### 1. Wizard Container (`frontend/src/views/ModuleConverter/ModuleConverterWizard.vue`)
```vue
<template>
  <div class="module-converter-wizard">
    <div class="wizard-header">
      <h1>Module Converter</h1>
      <p class="subtitle">Prüfkataloge in strukturierte Module umwandeln</p>
    </div>

    <!-- Stepper -->
    <Steps :model="steps" :activeIndex="currentStep" class="wizard-steps" />

    <!-- Step Content -->
    <div class="wizard-content">
      <component
        :is="currentStepComponent"
        :wizard-data="wizardData"
        @update="updateWizardData"
        @next="nextStep"
        @back="prevStep"
      />
    </div>

    <!-- Navigation -->
    <div class="wizard-navigation">
      <Button
        v-if="currentStep > 0"
        label="Zurück"
        icon="pi pi-arrow-left"
        class="p-button-secondary"
        @click="prevStep"
      />
      <Button
        v-if="currentStep < steps.length - 1"
        label="Weiter"
        icon="pi pi-arrow-right"
        iconPos="right"
        :disabled="!canProceed"
        @click="nextStep"
      />
      <Button
        v-if="currentStep === steps.length - 1"
        label="Abschließen"
        icon="pi pi-check"
        class="p-button-success"
        @click="finishWizard"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, shallowRef } from 'vue'
import Steps from 'primevue/steps'
import Button from 'primevue/button'

import StepModeSelection from './steps/StepModeSelection.vue'
import StepUploadOrSelect from './steps/StepUploadOrSelect.vue'
import StepLLMConversion from './steps/StepLLMConversion.vue'
import StepReviewEdit from './steps/StepReviewEdit.vue'
import StepStagingGitHub from './steps/StepStagingGitHub.vue'

const steps = ref([
  { label: 'Modus' },
  { label: 'Quelle' },
  { label: 'Konvertierung' },
  { label: 'Review' },
  { label: 'Staging' }
])

const stepComponents = [
  StepModeSelection,
  StepUploadOrSelect,
  StepLLMConversion,
  StepReviewEdit,
  StepStagingGitHub
]

const currentStep = ref(0)
const currentStepComponent = computed(() => stepComponents[currentStep.value])

const wizardData = ref({
  mode: null,                  // 'new' | 'update'
  existingModuleId: null,
  uploadedFile: null,
  moduleName: '',
  moduleDescription: '',
  layer: 'rahmen',
  konzernId: null,
  versionType: null,           // 'patch' | 'minor' | 'major'
  changeDescription: '',
  convertedStructure: null,
  validationErrors: [],
  llmProvider: null,
  tokensCost: null,
  githubBranch: null,
  githubPrUrl: null
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0: return wizardData.value.mode !== null
    case 1: return wizardData.value.mode === 'new'
      ? wizardData.value.uploadedFile && wizardData.value.moduleName
      : wizardData.value.existingModuleId && wizardData.value.versionType
    case 2: return wizardData.value.convertedStructure !== null
    case 3: return wizardData.value.validationErrors.length === 0
    default: return true
  }
})

const updateWizardData = (updates) => {
  wizardData.value = { ...wizardData.value, ...updates }
}

const nextStep = () => {
  if (currentStep.value < steps.value.length - 1) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const finishWizard = async () => {
  // TODO: Finalisierung und Redirect
}
</script>

<style scoped>
.module-converter-wizard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.wizard-header {
  text-align: center;
  margin-bottom: 2rem;
}

.subtitle {
  color: var(--text-color-secondary);
}

.wizard-steps {
  margin-bottom: 2rem;
}

.wizard-content {
  min-height: 400px;
  background: var(--surface-card);
  border-radius: 8px;
  padding: 2rem;
}

.wizard-navigation {
  display: flex;
  justify-content: space-between;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}
</style>
```

### 2. Step 1: Modus-Auswahl (`frontend/src/views/ModuleConverter/steps/StepModeSelection.vue`)
```vue
<template>
  <div class="step-mode-selection">
    <h2>Wie möchten Sie vorgehen?</h2>

    <div class="mode-cards">
      <Card
        class="mode-card"
        :class="{ selected: wizardData.mode === 'new' }"
        @click="selectMode('new')"
      >
        <template #header>
          <i class="pi pi-plus-circle mode-icon"></i>
        </template>
        <template #title>Neues Modul erstellen</template>
        <template #content>
          <p>Laden Sie einen Prüfkatalog (PDF, Word, Excel) hoch und konvertieren Sie ihn mit KI in ein strukturiertes Prüfschema.</p>
        </template>
      </Card>

      <Card
        class="mode-card"
        :class="{ selected: wizardData.mode === 'update' }"
        @click="selectMode('update')"
      >
        <template #header>
          <i class="pi pi-refresh mode-icon"></i>
        </template>
        <template #title>Bestehendes Modul überarbeiten</template>
        <template #content>
          <p>Wählen Sie ein bestehendes Modul aus und erstellen Sie eine neue Version mit Ihren Änderungen.</p>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import Card from 'primevue/card'

const props = defineProps(['wizardData'])
const emit = defineEmits(['update', 'next'])

const selectMode = (mode) => {
  emit('update', { mode })
}
</script>

<style scoped>
.mode-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2rem;
  margin-top: 2rem;
}

.mode-card {
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.mode-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

.mode-card.selected {
  border-color: var(--primary-color);
  background: var(--primary-50);
}

.mode-icon {
  font-size: 3rem;
  color: var(--primary-color);
  display: block;
  text-align: center;
  padding: 1.5rem;
}
</style>
```

### 3. Step 2: Upload/Auswahl (`frontend/src/views/ModuleConverter/steps/StepUploadOrSelect.vue`)
```vue
<template>
  <div class="step-upload-select">
    <!-- Neues Modul: Upload -->
    <template v-if="wizardData.mode === 'new'">
      <h2>Katalog hochladen</h2>

      <div class="form-grid">
        <div class="form-field">
          <label for="moduleName">Modul-Name *</label>
          <InputText
            id="moduleName"
            v-model="localData.moduleName"
            placeholder="z.B. Vorhabenprüfung 2024"
            @input="emitUpdate"
          />
        </div>

        <div class="form-field">
          <label for="layer">Ebene</label>
          <Dropdown
            id="layer"
            v-model="localData.layer"
            :options="layerOptions"
            optionLabel="label"
            optionValue="value"
            @change="emitUpdate"
          />
        </div>

        <div class="form-field full-width">
          <label for="description">Beschreibung</label>
          <Textarea
            id="description"
            v-model="localData.moduleDescription"
            rows="3"
            @input="emitUpdate"
          />
        </div>

        <div class="form-field full-width">
          <label>Katalog-Datei *</label>
          <FileUpload
            mode="basic"
            :auto="false"
            accept=".pdf,.docx,.xlsx"
            :maxFileSize="10000000"
            chooseLabel="Datei auswählen"
            @select="onFileSelect"
          />
          <small>Unterstützte Formate: PDF, Word (DOCX), Excel (XLSX)</small>
        </div>
      </div>
    </template>

    <!-- Bestehendes Modul: Auswahl -->
    <template v-else>
      <h2>Modul auswählen</h2>

      <div class="form-grid">
        <div class="form-field full-width">
          <label>Bestehendes Modul</label>
          <Dropdown
            v-model="localData.existingModuleId"
            :options="availableModules"
            optionLabel="displayName"
            optionValue="id"
            filter
            placeholder="Modul suchen..."
            @change="onModuleSelect"
          />
        </div>

        <div class="form-field">
          <label>Versionstyp *</label>
          <SelectButton
            v-model="localData.versionType"
            :options="versionOptions"
            optionLabel="label"
            optionValue="value"
            @change="emitUpdate"
          />
        </div>

        <div class="form-field full-width">
          <label>Änderungsbeschreibung *</label>
          <Textarea
            v-model="localData.changeDescription"
            rows="4"
            placeholder="Beschreiben Sie die geplanten Änderungen..."
            @input="emitUpdate"
          />
        </div>
      </div>

      <!-- Versionsinfo -->
      <div v-if="selectedModule" class="version-info">
        <h4>Neue Version:</h4>
        <Tag :value="newVersionString" severity="info" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import FileUpload from 'primevue/fileupload'
import SelectButton from 'primevue/selectbutton'
import Tag from 'primevue/tag'
import { useModuleStore } from '@/stores/modules'

const props = defineProps(['wizardData'])
const emit = defineEmits(['update'])

const moduleStore = useModuleStore()

const localData = ref({
  moduleName: props.wizardData.moduleName,
  moduleDescription: props.wizardData.moduleDescription,
  layer: props.wizardData.layer,
  existingModuleId: props.wizardData.existingModuleId,
  versionType: props.wizardData.versionType,
  changeDescription: props.wizardData.changeDescription,
  uploadedFile: props.wizardData.uploadedFile
})

const layerOptions = [
  { label: 'Rahmen (Global)', value: 'rahmen' },
  { label: 'Konzern', value: 'konzern' },
  { label: 'Organisation', value: 'orga' }
]

const versionOptions = [
  { label: 'Patch (Bugfix)', value: 'patch' },
  { label: 'Minor (Feature)', value: 'minor' },
  { label: 'Major (Breaking)', value: 'major' }
]

const availableModules = computed(() =>
  moduleStore.modules.map(m => ({
    ...m,
    displayName: `${m.name} (v${m.version})`
  }))
)

const selectedModule = computed(() =>
  availableModules.value.find(m => m.id === localData.value.existingModuleId)
)

const newVersionString = computed(() => {
  if (!selectedModule.value || !localData.value.versionType) return ''

  const [major, minor, patch] = selectedModule.value.version.split('.').map(Number)
  switch (localData.value.versionType) {
    case 'major': return `${major + 1}.0.0`
    case 'minor': return `${major}.${minor + 1}.0`
    case 'patch': return `${major}.${minor}.${patch + 1}`
    default: return ''
  }
})

const emitUpdate = () => {
  emit('update', { ...localData.value })
}

const onFileSelect = (event) => {
  localData.value.uploadedFile = event.files[0]
  emitUpdate()
}

const onModuleSelect = () => {
  emitUpdate()
}

onMounted(() => {
  moduleStore.fetchModules()
})
</script>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field.full-width {
  grid-column: span 2;
}

.version-info {
  margin-top: 2rem;
  padding: 1rem;
  background: var(--surface-ground);
  border-radius: 6px;
}
</style>
```

### 4. Step 3: LLM Konvertierung (`frontend/src/views/ModuleConverter/steps/StepLLMConversion.vue`)
```vue
<template>
  <div class="step-llm-conversion">
    <h2>KI-Konvertierung</h2>

    <!-- Status: Waiting -->
    <div v-if="status === 'idle'" class="conversion-start">
      <p>Klicken Sie auf "Konvertierung starten", um den Katalog mit KI zu analysieren.</p>
      <Button
        label="Konvertierung starten"
        icon="pi pi-play"
        @click="startConversion"
      />
    </div>

    <!-- Status: Processing -->
    <div v-else-if="status === 'processing'" class="conversion-progress">
      <ProgressSpinner />
      <h3>Konvertierung läuft...</h3>
      <p>{{ progressMessage }}</p>
      <ProgressBar :value="progress" />
    </div>

    <!-- Status: Success -->
    <div v-else-if="status === 'success'" class="conversion-success">
      <i class="pi pi-check-circle success-icon"></i>
      <h3>Konvertierung erfolgreich!</h3>

      <div class="stats">
        <div class="stat">
          <span class="stat-value">{{ stats.nodesCount }}</span>
          <span class="stat-label">Knoten erstellt</span>
        </div>
        <div class="stat">
          <span class="stat-value">{{ stats.provider }}</span>
          <span class="stat-label">LLM Provider</span>
        </div>
        <div class="stat">
          <span class="stat-value">{{ stats.tokens }}</span>
          <span class="stat-label">Tokens verwendet</span>
        </div>
        <div class="stat">
          <span class="stat-value">{{ stats.cost }} €</span>
          <span class="stat-label">Kosten</span>
        </div>
      </div>
    </div>

    <!-- Status: Error -->
    <div v-else-if="status === 'error'" class="conversion-error">
      <i class="pi pi-times-circle error-icon"></i>
      <h3>Fehler bei der Konvertierung</h3>
      <p>{{ errorMessage }}</p>
      <Button label="Erneut versuchen" icon="pi pi-refresh" @click="startConversion" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import ProgressBar from 'primevue/progressbar'
import { useModuleApi } from '@/services/moduleApi'

const props = defineProps(['wizardData'])
const emit = defineEmits(['update', 'next'])

const moduleApi = useModuleApi()

const status = ref('idle')
const progress = ref(0)
const progressMessage = ref('')
const errorMessage = ref('')

const stats = ref({
  nodesCount: 0,
  provider: '',
  tokens: 0,
  cost: 0
})

const startConversion = async () => {
  status.value = 'processing'
  progress.value = 0

  try {
    // Simulierte Progress-Updates
    progressMessage.value = 'Datei wird analysiert...'
    progress.value = 20
    await sleep(500)

    progressMessage.value = 'Struktur wird extrahiert...'
    progress.value = 40
    await sleep(500)

    progressMessage.value = 'KI-Konvertierung läuft...'
    progress.value = 60

    // API Call
    const formData = new FormData()
    if (props.wizardData.mode === 'new') {
      formData.append('file', props.wizardData.uploadedFile)
      formData.append('name', props.wizardData.moduleName)
      formData.append('description', props.wizardData.moduleDescription)
      formData.append('layer', props.wizardData.layer)
    }

    const result = await moduleApi.convertCatalog(formData)

    progress.value = 100
    progressMessage.value = 'Abgeschlossen!'

    // Stats aktualisieren
    stats.value = {
      nodesCount: countNodes(result.tree_structure),
      provider: result.llm_provider_used,
      tokens: result.tokens_used,
      cost: result.cost_eur.toFixed(4)
    }

    // Wizard-Daten aktualisieren
    emit('update', {
      convertedStructure: result.tree_structure,
      llmProvider: result.llm_provider_used,
      tokensCost: result.cost_eur,
      validationErrors: result.validation_errors
    })

    status.value = 'success'

  } catch (error) {
    status.value = 'error'
    errorMessage.value = error.message || 'Unbekannter Fehler'
  }
}

const countNodes = (structure) => {
  if (!structure?.nodes) return 0
  let count = 0
  const traverse = (nodes) => {
    for (const node of nodes) {
      count++
      if (node.children) traverse(node.children)
      if (node.ja_branch) traverse(node.ja_branch)
      if (node.nein_branch) traverse(node.nein_branch)
    }
  }
  traverse(structure.nodes)
  return count
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))
</script>

<style scoped>
.step-llm-conversion {
  text-align: center;
}

.conversion-progress,
.conversion-start,
.conversion-success,
.conversion-error {
  padding: 3rem;
}

.success-icon {
  font-size: 4rem;
  color: var(--green-500);
}

.error-icon {
  font-size: 4rem;
  color: var(--red-500);
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-top: 2rem;
}

.stat {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  background: var(--surface-ground);
  border-radius: 8px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--primary-color);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}
</style>
```

### 5. Weitere Steps
Erstelle analog:
- `StepReviewEdit.vue` - Tree-Editor für manuelle Anpassungen
- `StepStagingGitHub.vue` - Stage-Auswahl und GitHub-Integration

### 6. Module Store (`frontend/src/stores/modules.js`)
```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { moduleApi } from '@/services/moduleApi'

export const useModuleStore = defineStore('modules', () => {
  const modules = ref([])
  const loading = ref(false)

  const fetchModules = async (filters = {}) => {
    loading.value = true
    try {
      const response = await moduleApi.listModules(filters)
      modules.value = response.items
    } finally {
      loading.value = false
    }
  }

  return { modules, loading, fetchModules }
})
```

## Schritte

1. Erstelle Verzeichnisstruktur: `frontend/src/views/ModuleConverter/steps/`
2. Implementiere Wizard-Container
3. Implementiere Steps nacheinander (1-5)
4. Erstelle Module Store
5. Erstelle API Service
6. Registriere Routes
7. Teste jeden Step einzeln

## Validierung
```bash
cd frontend
npm run dev
# Öffne http://localhost:5173/admin/module-converter
```

## Referenzen
- Planung: `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md`
- PrimeVue Docs: https://primevue.org/
- Bestehende Komponenten: `frontend/src/components/`
