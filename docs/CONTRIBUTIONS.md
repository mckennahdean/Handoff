# Team Contributions

Handoff was built by a three-person team for UMGC CMSC 495, Computer Science Capstone (Fall 2026).

| Member | Role |
|---|---|
| Thomas Dean | Lead Architect |
| McKenna Dean | Interface Designer |
| Renata Gabdrakhmanova | Integration Lead |

## How we worked

- **Branches and pull requests.** Work happened on feature branches and reached `main` only through pull requests. `main` is protected and requires an approving review before merging.
- **Automated checks.** Every pull request runs the CI pipeline (backend tests against a real database, frontend lint and build, and a Docker smoke test), and a failing check blocks the merge.
- **Incremental delivery.** The project grew in layers: McKenna's interface and Renata's first AI pipeline formed the working base, and later pull requests added authentication, capture gaps, the knowledge gap loop, evaluation, and deployment on top of it.

| Pull request | Contents | Author | Merged by |
|---|---|---|---|
| #1 `feature/frontend-backend-integration` | First end-to-end integration of every screen with the backend and AI pipeline | Renata Gabdrakhmanova | Renata Gabdrakhmanova |
| #2 `feature/backend` | Backend foundation, building on the initial database and API setup | Thomas Dean | Thomas Dean |
| #3 `feature/ci-cd` | First CI pipeline | Thomas Dean | Thomas Dean |
| #4 `hotfix/embedding-model-name-regression` | Fix for a renamed embedding model | Thomas Dean | Thomas Dean |
| #5 `q2-final-push` | Authentication, capture gaps, knowledge gaps, evaluation, Docker, CI/CD | Thomas Dean | McKenna Dean, after review |
| #6 `q3-docs-and-polish` | Documentation, security fixes, demo data, polish | Thomas Dean | [who merged], after review |
| #7 `feature/user-management-404` | User management and custom 404 page | McKenna Dean | Thomas Dean, after review |
| #8 `fix/user-management-followups` | Server-side role rules, tests, and user management fixes | Thomas Dean | In review |

## Thomas Dean, Lead Architect

- Designed the overall architecture and led the backend: FastAPI routes, database layer, and the single module that handles all AI calls.
- Created the original component diagram during the design phase (Week 4).
- Built authentication and roles: Argon2 password hashing, signed login tokens, invite codes, and a password policy chosen by comparing PCI DSS v4.0 with NIST SP 800-63B.
- Moved the Approval Gate into the database, so unapproved drafts can never be searched.
- Built capture gaps, including the insert-only guardrail that stops the AI from rewriting the owner's steps.
- Built the knowledge gap loop: grouping, "Also Asked As," auto-resolve, dismissal, and reopening on delete.
- Built the offline evaluation harness and used it to find and fix a retrieval problem (chunked retrieval: correct retrieval from 26 of 28 to 28 of 28), set the answer threshold from measurements, and prove the need for the second abstention gate.
- Grew the test suite with unit, integration, and route-protection tests, and built the Docker images and the CI/CD pipeline that publishes them.
- Wrote the project documentation.
- Reviewed pull request #7 and followed up with server-side enforcement of the role rules, tests, and fixes (PR #8).

> *Decision:* I chose to measure before tuning. Building the evaluation harness turned guessed thresholds into measured ones and exposed the retrieval problem. *Lesson:* passing tests is not the same as tested code. Our CORS test and the missing route guard both passed while the bug was live.

## McKenna Dean, Interface Designer

- Created and hosts the project repository, and set up its original README, `.gitignore`, and first Docker Compose configuration.
- Designed and built the original Vue 3 frontend: the navigation bar, login screen, owner and employee dashboards, and every core screen of the workflow (Capture a Procedure, Procedure Review, Procedures, Ask Handoff, and Knowledge Gaps).
- Established the visual design and page structure that the finished application still uses. Later work connected these screens to the backend and extended them; the interface users see today is built on her screens.
- Documented the frontend's structure in `frontend/README.md`.
- Reviewed and merged pull request #5, the project's largest.
- Built user management: an owner-only page and API for listing accounts, changing roles, and deleting employee accounts (PR #7).
- Built the custom 404 page with randomized team pet photos, removing embedded photo metadata (EXIF) before committing them.

> _[One decision and why, and one lesson learned.]_

## Renata Gabdrakhmanova, Integration Lead

- Set up PostgreSQL with the pgvector extension, the vector database Handoff still runs on.
- Wrote the first Gemini integration for structuring procedures and generating embeddings, and the first retrieval-augmented answering pipeline.
- Led the frontend-backend integration: connected the capture, approval, procedures, Ask Handoff, and gaps screens to the backend API; merged the AI and frontend branches; and fixed the resulting build and lint issues. This produced the first version of Handoff in which every screen worked against the real backend.
- Merged pull request #1.

> _[One decision and why, and one lesson learned.]_

## Commit summary

From `git shortlog -sn` on the final branch:

| Member | Commits |
|---|---|
| Thomas Dean | [86] |
| McKenna Dean | [14] |
| Renata Gabdrakhmanova | [14] |

Commit counts are shown for transparency, not as a measure of effort. Design, research, planning, and debugging often happen outside of commits, and a single commit can hold anything from a typo fix to an entire feature. Each member's early work was the foundation that later features were built on.