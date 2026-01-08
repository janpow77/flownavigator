# Implementiere Staging Pipeline

## WICHTIG: Autonome Ausführung

**Arbeite OHNE Rückfragen!** Führe alle Schritte selbstständig aus:
1. Lies die bestehenden Services um den Kontext zu verstehen
2. Implementiere den StagingService vollständig
3. Integriere mit ModuleService
4. Erweitere die API-Endpoints
5. Implementiere die Frontend-Komponente
6. Behebe Fehler eigenständig
7. Führe die Validierung am Ende durch
8. Committe und pushe erst wenn alles funktioniert
9. Fahre dann mit `/implement-tests` fort

**Keine Fragen stellen - einfach machen!**

---

## Aufgabe
Erstelle die Staging-Pipeline für Module (DRAFT → DEV → TEST → FREIGABE → PROD) basierend auf `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md`.

## Pipeline-Übersicht

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐
│  DRAFT  │ ──▶│   DEV   │ ──▶│  TEST   │ ──▶│ FREIGABE │ ──▶│  PROD   │
│         │    │         │    │         │    │          │    │         │
│ Entwurf │    │ Entwickl│    │ QA-Test │    │ Approval │    │ Live    │
└─────────┘    └─────────┘    └─────────┘    └──────────┘    └─────────┘
     │              │              │               │              │
     └──────────────┴──────────────┴───────────────┴──────────────┘
                            Reject (zurück)
```

## Zu erstellende Dateien

### 1. Staging Service (`backend/app/services/staging_service.py`)
```python
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.module_template import ModuleTemplate, ModuleStatus
from app.models.user import User
from app.models.audit_log import AuditLog

class StagingTransition:
    """Definiert erlaubte Stage-Übergänge und Berechtigungen."""

    TRANSITIONS = {
        ModuleStatus.DRAFT: {
            "next": ModuleStatus.DEV,
            "required_role": "EDITOR",
            "requires_validation": True
        },
        ModuleStatus.DEV: {
            "next": ModuleStatus.TEST,
            "required_role": "EDITOR",
            "requires_validation": True,
            "requires_tests": True
        },
        ModuleStatus.TEST: {
            "next": ModuleStatus.FREIGABE,
            "required_role": "EDITOR",
            "requires_qa_approval": True
        },
        ModuleStatus.FREIGABE: {
            "next": ModuleStatus.PROD,
            "required_role": "ADMIN",
            "requires_final_approval": True
        },
        ModuleStatus.PROD: {
            "next": None,  # End-Status
            "can_archive": True
        }
    }

    REJECT_TO = {
        ModuleStatus.DEV: ModuleStatus.DRAFT,
        ModuleStatus.TEST: ModuleStatus.DEV,
        ModuleStatus.FREIGABE: ModuleStatus.TEST,
    }


class StagingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def can_promote(
        self,
        module: ModuleTemplate,
        user: User
    ) -> tuple[bool, List[str]]:
        """
        Prüft ob Modul promoted werden kann.
        Returns: (can_promote, list_of_blocking_reasons)
        """
        errors = []
        transition = StagingTransition.TRANSITIONS.get(module.status)

        if not transition or not transition.get("next"):
            errors.append(f"Modul in Status {module.status.value} kann nicht promoted werden")
            return False, errors

        # Rollenprüfung
        required_role = transition.get("required_role")
        if required_role and user.role.value < required_role:
            errors.append(f"Rolle {required_role} erforderlich")

        # Validierung
        if transition.get("requires_validation"):
            validation_errors = await self._validate_module_structure(module)
            if validation_errors:
                errors.extend(validation_errors)

        # Tests (für DEV → TEST)
        if transition.get("requires_tests"):
            if not await self._check_tests_passed(module):
                errors.append("Alle Tests müssen bestanden sein")

        # QA-Approval (für TEST → FREIGABE)
        if transition.get("requires_qa_approval"):
            if not await self._check_qa_approved(module):
                errors.append("QA-Freigabe erforderlich")

        # Final Approval (für FREIGABE → PROD)
        if transition.get("requires_final_approval"):
            if not await self._check_final_approved(module):
                errors.append("Finale Admin-Freigabe erforderlich")

        return len(errors) == 0, errors

    async def promote(
        self,
        module_id: int,
        user: User,
        comment: Optional[str] = None
    ) -> ModuleTemplate:
        """Befördert Modul in nächste Stage."""
        module = await self.db.get(ModuleTemplate, module_id)
        if not module:
            raise ValueError("Modul nicht gefunden")

        can_promote, errors = await self.can_promote(module, user)
        if not can_promote:
            raise ValueError(f"Promotion nicht möglich: {', '.join(errors)}")

        old_status = module.status
        new_status = StagingTransition.TRANSITIONS[module.status]["next"]

        module.status = new_status
        module.updated_at = datetime.utcnow()

        # Audit-Log
        await self._log_transition(
            module=module,
            user=user,
            action="promote",
            old_status=old_status,
            new_status=new_status,
            comment=comment
        )

        await self.db.commit()
        await self.db.refresh(module)

        return module

    async def reject(
        self,
        module_id: int,
        user: User,
        reason: str
    ) -> ModuleTemplate:
        """Weist Modul zurück zur vorherigen Stage."""
        module = await self.db.get(ModuleTemplate, module_id)
        if not module:
            raise ValueError("Modul nicht gefunden")

        if module.status not in StagingTransition.REJECT_TO:
            raise ValueError(f"Modul in Status {module.status.value} kann nicht rejected werden")

        old_status = module.status
        new_status = StagingTransition.REJECT_TO[module.status]

        module.status = new_status
        module.updated_at = datetime.utcnow()

        # Audit-Log
        await self._log_transition(
            module=module,
            user=user,
            action="reject",
            old_status=old_status,
            new_status=new_status,
            comment=reason
        )

        await self.db.commit()
        await self.db.refresh(module)

        return module

    async def get_stage_history(self, module_id: int) -> List[dict]:
        """Holt Stage-Verlauf für ein Modul."""
        query = select(AuditLog).where(
            AuditLog.entity_type == "module_template",
            AuditLog.entity_id == module_id,
            AuditLog.action.in_(["promote", "reject"])
        ).order_by(AuditLog.created_at.desc())

        result = await self.db.execute(query)
        logs = result.scalars().all()

        return [
            {
                "action": log.action,
                "old_status": log.details.get("old_status"),
                "new_status": log.details.get("new_status"),
                "comment": log.details.get("comment"),
                "user_id": log.user_id,
                "created_at": log.created_at
            }
            for log in logs
        ]

    async def _validate_module_structure(self, module: ModuleTemplate) -> List[str]:
        """Validiert Modul-Struktur."""
        errors = []
        tree = module.tree_structure

        if not tree or not tree.get("nodes"):
            errors.append("Modul hat keine Struktur")
            return errors

        # Prüfe auf leere Nodes
        def check_nodes(nodes, path=""):
            for i, node in enumerate(nodes):
                node_path = f"{path}/{i}"
                if not node.get("content"):
                    errors.append(f"Leerer Inhalt bei Node {node_path}")
                if node.get("type") == "DECISION":
                    if not node.get("ja_branch"):
                        errors.append(f"DECISION ohne JA-Branch bei {node_path}")
                    if not node.get("nein_branch"):
                        errors.append(f"DECISION ohne NEIN-Branch bei {node_path}")
                if node.get("children"):
                    check_nodes(node["children"], node_path)
                if node.get("ja_branch"):
                    check_nodes(node["ja_branch"], f"{node_path}/ja")
                if node.get("nein_branch"):
                    check_nodes(node["nein_branch"], f"{node_path}/nein")

        check_nodes(tree.get("nodes", []))
        return errors

    async def _check_tests_passed(self, module: ModuleTemplate) -> bool:
        """Prüft ob CI-Tests bestanden sind (via GitHub)."""
        if not module.github_pr_url:
            return True  # Kein GitHub = überspringen

        from app.services.github_service import GitHubService
        github = GitHubService()

        if not github.is_configured():
            return True

        # PR-Nummer aus URL extrahieren
        import re
        match = re.search(r'/pull/(\d+)', module.github_pr_url)
        if not match:
            return True

        pr_number = int(match.group(1))
        status = await github.get_pr_status(pr_number)

        return status.get("ci_status") == "success"

    async def _check_qa_approved(self, module: ModuleTemplate) -> bool:
        """Prüft QA-Approval (via GitHub PR-Review oder manuell)."""
        # Implementierung je nach Workflow
        return True  # Placeholder

    async def _check_final_approved(self, module: ModuleTemplate) -> bool:
        """Prüft finale Admin-Freigabe."""
        # Implementierung je nach Workflow
        return True  # Placeholder

    async def _log_transition(
        self,
        module: ModuleTemplate,
        user: User,
        action: str,
        old_status: ModuleStatus,
        new_status: ModuleStatus,
        comment: Optional[str]
    ):
        """Erstellt Audit-Log für Stage-Transition."""
        log = AuditLog(
            entity_type="module_template",
            entity_id=module.id,
            action=action,
            user_id=user.id,
            details={
                "old_status": old_status.value,
                "new_status": new_status.value,
                "comment": comment,
                "module_name": module.name,
                "version": f"{module.version_major}.{module.version_minor}.{module.version_patch}"
            }
        )
        self.db.add(log)
```

### 2. Staging Dashboard Komponente (`frontend/src/views/ModuleConverter/steps/StepStagingGitHub.vue`)
```vue
<template>
  <div class="step-staging">
    <h2>Staging & Deployment</h2>

    <!-- Aktuelle Stage -->
    <div class="current-stage">
      <h3>Aktuelle Stage</h3>
      <div class="stage-pipeline">
        <div
          v-for="stage in stages"
          :key="stage.value"
          class="stage-step"
          :class="{
            active: currentStage === stage.value,
            completed: isStageCompleted(stage.value),
            pending: isStagePending(stage.value)
          }"
        >
          <i :class="stage.icon"></i>
          <span>{{ stage.label }}</span>
        </div>
      </div>
    </div>

    <!-- GitHub Integration -->
    <div v-if="githubConfigured" class="github-section">
      <h3>GitHub Integration</h3>

      <div class="github-info">
        <div v-if="wizardData.githubBranch" class="info-item">
          <i class="pi pi-code-branch"></i>
          <span>Branch: {{ wizardData.githubBranch }}</span>
          <a :href="branchUrl" target="_blank" class="link">Öffnen</a>
        </div>

        <div v-if="wizardData.githubPrUrl" class="info-item">
          <i class="pi pi-github"></i>
          <span>Pull Request</span>
          <a :href="wizardData.githubPrUrl" target="_blank" class="link">Öffnen</a>
          <Tag :value="prStatus" :severity="prStatusSeverity" />
        </div>
      </div>

      <!-- PR erstellen (wenn noch keiner existiert) -->
      <div v-if="!wizardData.githubPrUrl && wizardData.githubBranch" class="create-pr">
        <h4>Pull Request erstellen</h4>
        <div class="form-field">
          <label>PR Titel</label>
          <InputText v-model="prTitle" />
        </div>
        <div class="form-field">
          <label>Reviewer</label>
          <MultiSelect
            v-model="selectedReviewers"
            :options="availableReviewers"
            optionLabel="name"
            optionValue="username"
            placeholder="Reviewer auswählen"
          />
        </div>
        <Button
          label="Pull Request erstellen"
          icon="pi pi-github"
          @click="createPullRequest"
          :loading="creatingPR"
        />
      </div>
    </div>

    <!-- Promotion Actions -->
    <div class="promotion-actions">
      <h3>Stage-Aktionen</h3>

      <div v-if="canPromote" class="action-card promote">
        <h4>Zur nächsten Stage befördern</h4>
        <p>{{ nextStageLabel }}</p>
        <div class="form-field">
          <label>Kommentar (optional)</label>
          <Textarea v-model="promoteComment" rows="2" />
        </div>
        <Button
          label="Befördern"
          icon="pi pi-arrow-right"
          class="p-button-success"
          @click="promoteModule"
          :loading="promoting"
        />
      </div>

      <div v-if="canReject" class="action-card reject">
        <h4>Zurückweisen</h4>
        <div class="form-field">
          <label>Begründung *</label>
          <Textarea v-model="rejectReason" rows="2" />
        </div>
        <Button
          label="Zurückweisen"
          icon="pi pi-arrow-left"
          class="p-button-danger"
          @click="rejectModule"
          :disabled="!rejectReason"
          :loading="rejecting"
        />
      </div>
    </div>

    <!-- Stage History -->
    <div class="stage-history">
      <h3>Verlauf</h3>
      <Timeline :value="stageHistory">
        <template #content="slotProps">
          <div class="history-item">
            <Tag
              :value="slotProps.item.action"
              :severity="slotProps.item.action === 'promote' ? 'success' : 'warning'"
            />
            <span>{{ slotProps.item.old_status }} → {{ slotProps.item.new_status }}</span>
            <small>{{ formatDate(slotProps.item.created_at) }}</small>
            <p v-if="slotProps.item.comment">{{ slotProps.item.comment }}</p>
          </div>
        </template>
      </Timeline>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import MultiSelect from 'primevue/multiselect'
import Timeline from 'primevue/timeline'
import { useModuleApi } from '@/services/moduleApi'
import { useGithubApi } from '@/services/githubApi'

const props = defineProps(['wizardData'])
const emit = defineEmits(['update'])

const moduleApi = useModuleApi()
const githubApi = useGithubApi()

const stages = [
  { value: 'draft', label: 'Entwurf', icon: 'pi pi-pencil' },
  { value: 'dev', label: 'Entwicklung', icon: 'pi pi-code' },
  { value: 'test', label: 'Test', icon: 'pi pi-check-square' },
  { value: 'freigabe', label: 'Freigabe', icon: 'pi pi-verified' },
  { value: 'prod', label: 'Produktion', icon: 'pi pi-globe' }
]

const currentStage = ref('draft')
const stageHistory = ref([])
const githubConfigured = ref(false)
const prStatus = ref('pending')

const promoting = ref(false)
const rejecting = ref(false)
const creatingPR = ref(false)

const promoteComment = ref('')
const rejectReason = ref('')
const prTitle = ref('')
const selectedReviewers = ref([])
const availableReviewers = ref([])

const canPromote = computed(() =>
  ['draft', 'dev', 'test', 'freigabe'].includes(currentStage.value)
)

const canReject = computed(() =>
  ['dev', 'test', 'freigabe'].includes(currentStage.value)
)

const nextStageLabel = computed(() => {
  const index = stages.findIndex(s => s.value === currentStage.value)
  return index < stages.length - 1
    ? `Nach "${stages[index + 1].label}" befördern`
    : ''
})

const isStageCompleted = (stage) => {
  const currentIndex = stages.findIndex(s => s.value === currentStage.value)
  const stageIndex = stages.findIndex(s => s.value === stage)
  return stageIndex < currentIndex
}

const isStagePending = (stage) => {
  const currentIndex = stages.findIndex(s => s.value === currentStage.value)
  const stageIndex = stages.findIndex(s => s.value === stage)
  return stageIndex > currentIndex
}

const promoteModule = async () => {
  promoting.value = true
  try {
    await moduleApi.promoteModule(props.wizardData.moduleId, {
      comment: promoteComment.value
    })
    await loadStageData()
  } finally {
    promoting.value = false
  }
}

const rejectModule = async () => {
  rejecting.value = true
  try {
    await moduleApi.rejectModule(props.wizardData.moduleId, {
      comment: rejectReason.value
    })
    await loadStageData()
  } finally {
    rejecting.value = false
  }
}

const createPullRequest = async () => {
  creatingPR.value = true
  try {
    const pr = await githubApi.createPullRequest({
      module_id: props.wizardData.moduleId,
      title: prTitle.value,
      description: props.wizardData.changeDescription,
      reviewers: selectedReviewers.value
    })
    emit('update', { githubPrUrl: pr.html_url })
  } finally {
    creatingPR.value = false
  }
}

const loadStageData = async () => {
  // Load current stage and history
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('de-DE')
}

onMounted(async () => {
  const status = await githubApi.getStatus()
  githubConfigured.value = status.configured
  await loadStageData()
})
</script>

<style scoped>
.stage-pipeline {
  display: flex;
  justify-content: space-between;
  margin: 2rem 0;
}

.stage-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  background: var(--surface-ground);
  min-width: 100px;
}

.stage-step.active {
  background: var(--primary-color);
  color: white;
}

.stage-step.completed {
  background: var(--green-100);
  color: var(--green-700);
}

.stage-step.pending {
  opacity: 0.5;
}

.github-section,
.promotion-actions,
.stage-history {
  margin-top: 2rem;
  padding: 1.5rem;
  background: var(--surface-card);
  border-radius: 8px;
}

.action-card {
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.action-card.promote {
  border-left: 4px solid var(--green-500);
}

.action-card.reject {
  border-left: 4px solid var(--red-500);
}

.history-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
</style>
```

## Schritte

1. Erstelle StagingService in `backend/app/services/staging_service.py`
2. Integriere mit ModuleService
3. Erstelle/erweitere API-Endpoints für Staging
4. Implementiere Frontend-Komponente
5. Füge Berechtigungsprüfungen hinzu
6. Schreibe Integration Tests

## Validierung
```bash
cd backend
pytest tests/test_staging_service.py -v

# API testen
curl -X POST http://localhost:8000/api/v1/modules/1/promote \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"comment": "Ready for DEV"}'
```

## Referenzen
- Planung: `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md`
- Audit-Log Model: `backend/app/models/audit_log.py`
