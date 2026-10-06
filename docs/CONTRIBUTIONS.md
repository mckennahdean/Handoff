# Team Contributions

Handoff was built by a three-person team for UMGC CMSC 495, Computer Science Capstone (Fall 2026).

| Member | Role | GitHub |
|---|---|---|
| Thomas Dean | Lead Architect | [@aryante88](https://github.com/aryante88) |
| McKenna Dean | Interface Designer | [@mckennahdean](https://github.com/mckennahdean) |
| Renata Gabdrakhmanova | Integration Lead | [@renata110803](https://github.com/renata110803) |

Commits, pull requests, and reviews on GitHub appear under these usernames.

## How we worked

- **Branches and pull requests.** Work happened on feature branches and reached `main` only through pull requests. `main` is protected and requires an approving review before merging.
- **Automated checks.** Every pull request runs the CI pipeline (backend tests against a real database, frontend lint and build, and a Docker smoke test), and a failing check blocks the merge.
- **Incremental delivery.** The project grew in layers: McKenna's interface and Renata's first AI pipeline formed the working base, and later pull requests added authentication, capture gaps, the knowledge gap loop, evaluation, deployment, and a final account security redesign on top of it.

| Pull request | Contents | Author | Merged by |
|---|---|---|---|
| #1 `feature/frontend-backend-integration` | First end-to-end integration of every screen with the backend and AI pipeline | Renata Gabdrakhmanova | Renata Gabdrakhmanova |
| #2 `feature/backend` | Backend foundation, building on the initial database and API setup | Thomas Dean | Thomas Dean |
| #3 `feature/ci-cd` | First CI pipeline | Thomas Dean | Thomas Dean |
| #4 `hotfix/embedding-model-name-regression` | Fix for a renamed embedding model | Thomas Dean | Thomas Dean |
| #5 `q2-final-push` | Authentication, capture gaps, knowledge gaps, evaluation, Docker, CI/CD | Thomas Dean | McKenna Dean, after review |
| #6 `q3-docs-and-polish` | Documentation, security fixes, demo data, polish | Thomas Dean | Thomas Dean, after review |
| #7 `feature/user-management-404` | User management and custom 404 page | McKenna Dean | Thomas Dean, after review |
| #8 `fix/user-management-followups` | Server-side role rules, tests, and user management fixes | Thomas Dean | McKenna Dean, after review |
| #9 `test/coverage-accuracy` | Integration tests for migrations and authentication; coverage from 79% to 87% | Thomas Dean | Thomas Dean, after review |
| #10 `docs/final-polish` | Install guide fixes, UI polish, screenshots, a read-only procedure view for employees, and the account security redesign: owner approval, login throttling, recovery codes | Thomas Dean | McKenna Dean, after review |
| #11 `docs/security-and-contributions` | Security policy and threat model, test strategy, account lifecycle diagram, removal of an unused page and outdated code comments, and documentation fixes | Thomas Dean | McKenna Dean, after review |
| #12 `mckennahdean-contributions-1` | Interface Designer reflection | McKenna Dean | Thomas Dean, after review |
| #13 `docs/final-contributions` | Account lifecycle diagram fix, scaling design, resilience strategy, technical debt review, final contributions, reflections, and commit counts | Thomas Dean | McKenna Dean, after review |

## Acting on instructor feedback

Feedback on the Unit 3 design specification and the Unit 5 alpha release shaped the final system:

| Feedback | What we did | Where |
|---|---|---|
| Add authentication and authorization to the API contracts (Unit 3) | Built sign-in with signed tokens and owner and employee roles; every non-public route requires a login, enforced by a test that checks every route | [API reference](api/README.md), [SECURITY.md](../SECURITY.md) |
| Document a standardized error schema (Unit 3) | Every error returns the same `{"detail": ...}` shape, with each status code documented | [API reference: Errors](api/README.md#errors) |
| Add an external-service resilience strategy (Unit 3) | Retry with backoff for temporary AI outages, no retries on quota errors, clear `429` and `503` responses, and no lost work | [External-service resilience](architecture/README.md#external-service-resilience) |
| Show how the system reaches 10,000 concurrent users (Unit 3) | A scaling design covering load balancing, horizontal scaling, connection pooling, background jobs, caching, and provider limits, clearly marked as not yet load-tested | [At larger scale](architecture/README.md#at-larger-scale) |
| Separate repaid technical debt from deferred debt, with the cost of each deferral (Unit 5) | Two tables: debt repaid, with the pull request that repaid it, and debt deferred, with its reliability, security, maintenance, or deployment cost | [Technical debt](architecture/README.md#technical-debt-repaid-and-deferred) |

## Thomas Dean, Lead Architect

- Designed the overall architecture and led the backend: FastAPI routes, database layer, and the single module that handles all AI calls.
- Created the original component diagram during the design phase (Week 4).
- Built authentication and roles: Argon2 password hashing, signed login tokens, and a password policy chosen by comparing PCI DSS v4.0 with NIST SP 800-63B.
- Redesigned account security in the final week, after finding that the shared invite code was a long-lived secret: owner approval of every new account, a 15-minute pause after 5 failed sign-ins, Argon2-hashed one-time recovery codes, sessions that end when a password is reset, and a break-glass recovery command, with each choice checked against NIST SP 800-63B.
- Moved the Approval Gate into the database, so unapproved drafts can never be searched.
- Built capture gaps, including the insert-only guardrail that stops the AI from rewriting the owner's steps.
- Built the knowledge gap loop: grouping, "Also Asked As," auto-resolve, dismissal, and reopening on delete.
- Built the offline evaluation harness and used it to find and fix a retrieval problem (chunked retrieval: correct retrieval from 27 of 29 to 29 of 29), set the answer threshold from measurements, and prove the need for the second abstention gate.
- Grew the test suite from 8 to 110 tests (89% line coverage) with unit, integration, and route-protection tests, and built the Docker images and the CI/CD pipeline that publishes them.
- Wrote the project documentation, and tested the install guide with a clean install.
- Reviewed pull requests #7 and #12, and followed up on #7 with server-side enforcement of the role rules, tests, and fixes (PR #8).

> *Decision:* I chose to measure before tuning. Building the evaluation harness turned guessed thresholds into measured ones and exposed the retrieval problem. *Lesson:* passing tests is not the same as tested code. Our CORS test and the missing route guard both passed while the bug was live.

## McKenna Dean, Interface Designer

- Created and hosts the project repository, and set up its original README, `.gitignore`, and first Docker Compose configuration.
- Designed and built the original Vue 3 frontend: the navigation bar, login screen, owner and employee dashboards, and every core screen of the workflow (Capture a Procedure, Procedure Review, Procedures, Ask Handoff, and Knowledge Gaps).
- Established the visual design and page structure that the finished application still uses. Later work connected these screens to the backend and extended them; the interface users see today is built on her screens.
- Documented the frontend's structure in `frontend/README.md`.
- Built user management: an owner-only page and API for listing accounts, changing roles, and deleting employee accounts (PR #7).
- Built the custom 404 page with randomized team pet photos, removing embedded photo metadata (EXIF) before committing them.
- Reviewed pull requests #5, #6, #9, #10, and #11, and merged #5, #8, #10, and #11.

> *Decision:* I chose to build the frontend around a consistent Vue structure and reusable page patterns so the different parts of Handoff would feel like one application instead of separate screens. *Lesson:* I learned that establishing a solid interface structure early can make it much easier to extend an application later when backend functionality and new features are added.

## Renata Gabdrakhmanova, Integration Lead

- Set up PostgreSQL with the pgvector extension, the vector database Handoff still runs on.
- Wrote the first Gemini integration for structuring procedures and generating embeddings, and the first retrieval-augmented answering pipeline.
- Led the frontend-backend integration: connected the capture, approval, procedures, Ask Handoff, and gaps screens to the backend API; merged the AI and frontend branches; and fixed the resulting build and lint issues. This produced the first version of Handoff in which every screen worked against the real backend.
- Merged pull request #1.

> *Decision:* I chose to focus on connecting the backend services, database, and Gemini AI so the different parts of Handoff could work together instead of functioning separately. *Lesson:* I learned that integration requires a lot of testing and troubleshooting, because even when individual components work correctly, problems can still happen when they are connected.

## Commit summary

From `git shortlog -sn --no-merges` on the final branch. Merge commits are left out, because GitHub credits each merge to whoever clicks the button rather than to the work itself.

| Member | Commits |
|---|---|
| Thomas Dean | 137 |
| McKenna Dean | 15 |
| Renata Gabdrakhmanova | 11 |

Commit counts are shown for transparency, not as a measure of effort. Design, research, planning, and debugging often happen outside of commits, and a single commit can hold anything from a typo fix to an entire feature. Each member's early work was the foundation that later features were built on.
