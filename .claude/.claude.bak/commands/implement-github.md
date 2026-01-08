# Implementiere GitHub Integration

## WICHTIG: Autonome Ausführung

**Arbeite OHNE Rückfragen!** Führe alle Schritte selbstständig aus:
1. Lies die bestehenden Dateien um den Kontext zu verstehen
2. Implementiere alle beschriebenen Komponenten vollständig
3. Installiere fehlende Packages (`pip install PyGithub`)
4. Erweitere die Config um GitHub-Variablen
5. Behebe Fehler eigenständig (Imports, Typen, Abhängigkeiten)
6. Führe die Validierung am Ende durch
7. Committe und pushe erst wenn alles funktioniert
8. Fahre dann mit `/implement-wizard` fort

**Keine Fragen stellen - einfach machen!**

---

## Aufgabe
Erstelle die GitHub-Integration für den Module Converter basierend auf `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md` (Sektion 1.4).

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Module    │ ──▶ │   Feature   │ ──▶ │     PR      │ ──▶ │   Merge &   │
│   ändern    │     │   Branch    │     │   Review    │     │   Deploy    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Zu erstellende Dateien

### 1. GitHub Service (`backend/app/services/github_service.py`)
```python
from github import Github, GithubException
from typing import Optional, List
import os

from app.core.config import settings

class GitHubService:
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.repo_name = settings.GITHUB_REPO  # z.B. "org/audit-designer"
        self.base_branch = settings.GITHUB_BASE_BRANCH or "main"

        if self.token:
            self.github = Github(self.token)
            self.repo = self.github.get_repo(self.repo_name)
        else:
            self.github = None
            self.repo = None

    def is_configured(self) -> bool:
        return self.github is not None

    async def create_branch(self, branch_name: str) -> str:
        """
        Erstellt einen Feature-Branch vom Base-Branch.
        Returns: Branch-URL
        """
        if not self.is_configured():
            return None

        try:
            # Hole Base-Branch SHA
            base_ref = self.repo.get_branch(self.base_branch)
            base_sha = base_ref.commit.sha

            # Erstelle neuen Branch
            ref = f"refs/heads/{branch_name}"
            self.repo.create_git_ref(ref=ref, sha=base_sha)

            return f"https://github.com/{self.repo_name}/tree/{branch_name}"
        except GithubException as e:
            if e.status == 422:  # Branch existiert bereits
                return f"https://github.com/{self.repo_name}/tree/{branch_name}"
            raise

    async def commit_module_changes(
        self,
        branch_name: str,
        module_slug: str,
        tree_structure: dict,
        commit_message: str
    ) -> str:
        """
        Committed Modul-Änderungen als JSON-Datei.
        Returns: Commit-SHA
        """
        if not self.is_configured():
            return None

        import json

        file_path = f"modules/{module_slug}.json"
        content = json.dumps(tree_structure, indent=2, ensure_ascii=False)

        try:
            # Versuche existierende Datei zu aktualisieren
            existing = self.repo.get_contents(file_path, ref=branch_name)
            result = self.repo.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=existing.sha,
                branch=branch_name
            )
        except GithubException:
            # Datei existiert nicht, neu erstellen
            result = self.repo.create_file(
                path=file_path,
                message=commit_message,
                content=content,
                branch=branch_name
            )

        return result["commit"].sha

    async def create_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
        labels: List[str] = None,
        reviewers: List[str] = None
    ) -> dict:
        """
        Erstellt einen Pull Request.
        Returns: PR-Daten (url, number, html_url)
        """
        if not self.is_configured():
            return None

        pr = self.repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base=self.base_branch
        )

        # Labels hinzufügen
        if labels:
            pr.add_to_labels(*labels)

        # Reviewer hinzufügen
        if reviewers:
            pr.create_review_request(reviewers=reviewers)

        return {
            "number": pr.number,
            "url": pr.url,
            "html_url": pr.html_url
        }

    async def get_pr_status(self, pr_number: int) -> dict:
        """
        Holt PR-Status inkl. CI-Status.
        """
        if not self.is_configured():
            return None

        pr = self.repo.get_pull(pr_number)
        commits = pr.get_commits()
        last_commit = list(commits)[-1] if commits.totalCount > 0 else None

        ci_status = "unknown"
        if last_commit:
            combined = last_commit.get_combined_status()
            ci_status = combined.state  # success, pending, failure

        return {
            "state": pr.state,
            "mergeable": pr.mergeable,
            "ci_status": ci_status,
            "reviews": [
                {"user": r.user.login, "state": r.state}
                for r in pr.get_reviews()
            ]
        }

    async def merge_pull_request(self, pr_number: int, merge_method: str = "squash") -> bool:
        """
        Merged einen PR nach Approval.
        merge_method: merge, squash, rebase
        """
        if not self.is_configured():
            return False

        pr = self.repo.get_pull(pr_number)

        if not pr.mergeable:
            raise ValueError("PR ist nicht mergeable")

        pr.merge(merge_method=merge_method)
        return True

    def generate_pr_body(
        self,
        module_name: str,
        version: str,
        change_description: str,
        changes_summary: List[str]
    ) -> str:
        """
        Generiert PR-Body im Standard-Format.
        """
        changes_list = "\n".join([f"- {c}" for c in changes_summary])

        return f"""## Modul-Änderung: {module_name}

### Version
`{version}`

### Beschreibung
{change_description}

### Änderungen
{changes_list}

### Checkliste
- [ ] Struktur validiert
- [ ] Entscheidungslogik geprüft
- [ ] Preview getestet
- [ ] Dokumentation aktualisiert

### Test Plan
1. Module im DEV-Modus laden
2. Alle Pfade durchspielen
3. Export-Funktion testen
"""

    def generate_commit_message(
        self,
        action: str,  # feat, fix, refactor
        module_name: str,
        description: str
    ) -> str:
        """
        Generiert Commit-Message im Conventional Commits Format.
        """
        return f"{action}(module): {module_name} - {description}"
```

### 2. Config erweitern (`backend/app/core/config.py`)
```python
# Zu Settings hinzufügen:
GITHUB_TOKEN: Optional[str] = None
GITHUB_REPO: Optional[str] = None  # "org/repo-name"
GITHUB_BASE_BRANCH: str = "main"
```

### 3. API Endpoints (`backend/app/api/endpoints/github.py`)
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.github_service import GitHubService
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/github", tags=["github"])

class CreateBranchRequest(BaseModel):
    module_id: int
    branch_name: str

class CreatePRRequest(BaseModel):
    module_id: int
    title: str
    description: str
    labels: Optional[List[str]] = None
    reviewers: Optional[List[str]] = None

@router.get("/status")
async def github_status(current_user: User = Depends(get_current_user)):
    """Prüft ob GitHub-Integration konfiguriert ist."""
    service = GitHubService()
    return {
        "configured": service.is_configured(),
        "repo": service.repo_name if service.is_configured() else None
    }

@router.post("/branches")
async def create_branch(
    request: CreateBranchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = GitHubService()
    if not service.is_configured():
        raise HTTPException(status_code=400, detail="GitHub nicht konfiguriert")

    branch_url = await service.create_branch(request.branch_name)
    return {"branch_url": branch_url}

@router.post("/pull-requests")
async def create_pull_request(
    request: CreatePRRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Hole Modul für PR-Body
    from app.models.module_template import ModuleTemplate
    module = await db.get(ModuleTemplate, request.module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Modul nicht gefunden")

    service = GitHubService()
    if not service.is_configured():
        raise HTTPException(status_code=400, detail="GitHub nicht konfiguriert")

    body = service.generate_pr_body(
        module_name=module.name,
        version=f"{module.version_major}.{module.version_minor}.{module.version_patch}",
        change_description=request.description,
        changes_summary=["Modul-Struktur aktualisiert"]  # TODO: Diff-Analyse
    )

    pr = await service.create_pull_request(
        branch_name=module.github_branch,
        title=request.title,
        body=body,
        labels=request.labels,
        reviewers=request.reviewers
    )

    # PR-URL am Modul speichern
    module.github_pr_url = pr["html_url"]
    await db.commit()

    return pr

@router.get("/pull-requests/{pr_number}/status")
async def get_pr_status(
    pr_number: int,
    current_user: User = Depends(get_current_user)
):
    service = GitHubService()
    if not service.is_configured():
        raise HTTPException(status_code=400, detail="GitHub nicht konfiguriert")

    return await service.get_pr_status(pr_number)
```

## Dependencies
Füge zu `backend/requirements.txt` hinzu:
```
PyGithub>=2.1.0
```

## Environment Variables
Füge zu `.env` hinzu:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=your-org/audit-designer
GITHUB_BASE_BRANCH=main
```

## Schritte

1. Installiere PyGithub: `pip install PyGithub`
2. Erweitere Config um GitHub-Variablen
3. Implementiere GitHubService
4. Erstelle API-Endpoints
5. Integriere mit ModuleService (bei Version-Erstellung)
6. Schreibe Tests (mit Mock-GitHub)

## Validierung
```bash
cd backend
# Unit Tests
pytest tests/test_github_service.py -v

# Manueller Test
curl -X POST http://localhost:8000/api/v1/github/status \
  -H "Authorization: Bearer $TOKEN"
```

## Referenzen
- Planung: `docs/PLAN_MODULE_CONVERSION_ENVIRONMENT.md` (Sektion 1.4)
- PyGithub Docs: https://pygithub.readthedocs.io/
