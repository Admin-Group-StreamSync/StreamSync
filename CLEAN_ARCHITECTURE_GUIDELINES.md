# Clean Architecture Guidelines

This document defines the target architecture for the StreamSync Django monolith refactor.
Its purpose is to keep business logic out of views and make behavior easier to test, maintain, and evolve.

## 1. Layer Responsibilities

### Views (`apps/*/views.py`)
Views are responsible for:
- HTTP request parsing
- HTTP-level validation (required fields, basic format/type checks)
- Calling service methods
- Mapping service outcomes/exceptions to HTTP responses
- Rendering templates or returning JSON

Views must not:
- Perform direct ORM queries (`Model.objects...`) for business use cases
- Contain domain rules, filtering algorithms, recommendation logic, or aggregation logic

### Services (`apps/*/services/`)
Services are responsible for:
- Business and domain logic
- Use-case orchestration across models and external APIs
- Data access coordination (direct ORM or repository wrapper)
- Returning clear, reusable results for views

Services should:
- Expose small, intention-revealing methods
- Be reusable across multiple views/endpoints
- Raise explicit domain-level exceptions when needed

### Models (`apps/*/models/`)
Models are responsible for:
- Data schema and relationships
- Persistence structure

Models should not orchestrate request-driven workflows.

## 2. Folder Strategy for This Repository

This repository is organized by Django apps (`apps/users`, `apps/contents`, etc.).
To match the current structure and avoid cross-app coupling, use app-local services:

- `apps/users/services/`
- `apps/contents/services/`
- `apps/lists/services/`
- `apps/reviews/services/`
- `apps/analytics/services/`

For each app:
- Keep service files focused by use case (example: `profile_service.py`, `catalog_service.py`)
- Avoid one large `services.py` file when responsibility grows

## 3. Naming Conventions

Service method names must be easy to read and understand.
Use clear verbs + domain nouns:

- `get_user_profile`
- `update_user_avatar`
- `create_personal_folder`
- `add_content_to_list`
- `publish_review`
- `build_dashboard_context`
- `generate_dashboard_pdf`

Avoid generic names such as:
- `process_data`
- `handle_request`
- `do_action`

For full service naming rules, see [SERVICE_NAMING_CONVENTIONS.md](SERVICE_NAMING_CONVENTIONS.md).

## 4. Data and Error Flow

### Data Flow
`View -> Service -> Model/External API -> Service -> View -> HTTP response`

### Error Flow
- Services raise domain-oriented exceptions (for example: not found, permission denied, invalid operation)
- Views translate these exceptions into HTTP responses/messages (`404`, `403`, `400`, etc.)
- Views should not inspect low-level ORM details for control flow

## 5. Validation Split

### View Validation (HTTP-level)
- Missing request fields
- Basic type coercion
- JSON parsing errors

### Service Validation (Business-level)
- Ownership checks
- State transitions
- Domain invariants
- Cross-entity consistency

## 6. Refactor Rules

During refactor:
- Move behavior incrementally by domain (lists -> reviews -> contents -> users -> analytics cleanup)
- Keep endpoint behavior stable unless change is explicitly requested
- Add/adjust tests before and after each extraction
- Do not mix unrelated cleanup in architecture commits

## 7. Definition of Done (Per Refactored View)

A refactored view is complete when:
- No direct ORM query remains in the view for business operations
- Domain/business logic moved to service layer
- Method names are intention-revealing
- Error handling follows the service-to-view contract
- Relevant tests pass for both service behavior and HTTP response mapping
