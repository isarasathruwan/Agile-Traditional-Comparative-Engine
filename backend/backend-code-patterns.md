My Reusable Backend Code Patterns (FastAPI)
This document captures reusable engineering patterns from this codebase so they can be reused in future projects.
It is intentionally domain-agnostic.
1. Root Directory Standard
   Use this root structure in every new project:
   project-root/
   |- main.py
   |- requirements.txt
   |- Dockerfile
   |- docker-compose.yml
   |- alembic.ini
   |- alembic/
   |  |- env.py
   |  |- script.py.mako
   |  \- versions/
   |- app/
   |  |- config/
   |  |- exceptions/
   |  |- model/
   |  |- entity/
   |  |- controller/
   |  |- service/
   |  |- repository/
   |  |- enum/
   |  \- util/
   |- tests/
   \- docs/
   Root file rules:
   main.py: app bootstrap only (no business logic).
   requirements.txt: exact pinned versions.
   Dockerfile: Python 3.12 runtime.
   docker-compose.yml: app + postgres for local deploy.
   alembic/: all DB migrations.
   tests/: integration/unit tests at root.
2. App Layer Responsibilities
   Use strict layer boundaries:
   controller: endpoint wiring only.
   service: business logic, try/catch, response creation.
   repository: database operations only.
   entity: SQLAlchemy ORM models.
   model: Pydantic request/response models (single-level files, no subfolders).
   exceptions: base exception + domain exceptions + global handlers.
   config: env settings, db, auth, logging, middleware, constants.
   enum: typed enums for states and action codes.
   util: pure helper functions.
3. Configuration Pattern
   3.1 Centralize Env in config.py
   Keep all env vars in one Settings class.
   Use aliases for env names (example: APP_NAME, POSTGRES_HOST).
   Validate values with Pydantic validators.
   Add runtime security validation for non-local environments.
   3.2 Build DB URL from Parts
   Do not pass a full postgres URL directly.
   Use:
   POSTGRES_HOST
   POSTGRES_PORT
   POSTGRES_USER
   POSTGRES_PASSWORD
   POSTGRES_DB
   POSTGRES_DRIVER (must be psycopg)
   Then build:
   postgresql+psycopg://<user>:<password>@<host>:<port>/<db>
   3.3 Dedicated Auth Config
   auth_config.py is used for:
   JWT related runtime values.
   Swagger bearer schema registration.
   auth whitelist paths.
   3.4 Database Config Module
   database_config.py provides:
   engine creation
   session factory creation
   get_db() dependency
   metadata getter for Alembic
4. Logging Pattern
   4.1 Single Logging Setup
   Configure once in startup:
   custom formatter with timestamp, level, module/function/line
   request ID in every log line
   4.2 Request ID Context
   generate/read X-Request-ID in middleware
   expose same header in response
   inject request ID into logs through logging filter
   4.3 Service/Repository Logging Rules
   Every service method:
   log start (info)
   log input/important internals (debug)
   log success end (info)
   log expected failures (warning or info)
   log unexpected failures with stack trace (exception)
   Repository methods:
   debug for query start + parameters
   info for write success
   warning for skipped operations (not found, conflict)
5. Response Contract Pattern
   5.1 Generic Response Model
   Use one envelope for all APIs:
   status_code
   success
   message
   error_code
   data
   Provide factory helpers:
   success_response(...)
   failed_response(...)
   5.2 Generic Pagination Response
   Pagination response inherits generic response and adds:
   page
   page_size
   total_records
   total_pages
   5.3 Status Code Propagation Rule
   service sets status_code in response model
   controller applies it to HTTP response using a helper (apply_status_code)
   This avoids all successful responses being forced to 200.
6. Exception Pattern
   6.1 Base Exception
   Use AppException with:
   message
   status_code
   error_code
   6.2 Domain Exceptions
   Create module-per-domain exceptions (auth/user/role/etc):
   frontend-friendly messages in exception text
   stable machine-readable error_code
   6.3 Global Handlers
   Register handlers for:
   AppException
   HTTPException
   RequestValidationError
   generic Exception
   All handlers must return the generic response envelope.
7. Controller Pattern
   Controller rules:
   endpoint definitions only
   input validation by Pydantic models
   inject dependencies (get_db, permissions)
   read current subject from request.state.user_subject
   call service method
   apply status code from service payload
   No business logic, no direct repository calls.
8. Service Pattern
   Service rules:
   every public method wrapped in try/except
   build success/failure using generic response helpers
   raise domain exceptions for business errors
   raise <Domain>ServiceException for unexpected failures
   include audit/event calls where applicable
   Error policy:
   frontend-friendly message in raised exception
   technical details only in logs
9. Repository Pattern
   Repository rules:
   only DB interactions
   extend BaseRepository for common CRUD
   custom queries in child repositories
   avoid business decisions in repository layer
   Query performance practices used:
   use existence queries (select(...).limit(1)) instead of count(*) when only checking presence
   combine related auth checks in one query when possible
   prefer single conditional update statements over read-then-update flows
   add composite indexes for common filter/sort paths
10. Entity and Schema Pattern
    Entity rules:
    one entity class per file
    shared Base + naming convention metadata
    shared TimestampMixin (created_at, updated_at)
    define constraints and indexes close to entity (__table_args__)
    explicit relationship names and cascade behavior
    Schema scale rules:
    unique constraints on business keys
    index foreign keys used in filters
    add composite indexes for heavy queries
11. Migration Pattern (Alembic)
    Migration rules:
    keep a clean initial schema migration
    keep separate seed migration(s) for default master data
    make migrations rerunnable in CI downgrade/upgrade cycles
    handle PostgreSQL enums safely with explicit create/drop and checkfirst=True
12. Auth + Authorization Pattern
    Auth runtime pattern:
    middleware validates bearer token for non-whitelisted paths
    decoded subject stored in request state
    JWT pattern:
    access token: stateless, short-lived
    refresh token: persisted by JTI in session table, rotated/revoked
    extra token types allowed for verification/reset flows
    Authorization pattern:
    route-level dependency require_permission("permission.name")
    service validates user status and RBAC mapping
    super-admin bypass supported by query rule
13. Constants Pattern
    Use constants only for:
    values reused in multiple files
    defaults that benefit from central control
    Do not move one-off route strings/messages/tags to constants unnecessarily.
14. Testing Pattern
    Test baseline:
    root tests/ folder
    pytest + fastapi.testclient
    DB override with isolated test session
    response contract assertions:
    status code
    success
    error_code
    payload shape
    Always include:
    auth-required tests
    happy-path flow tests
    permission-denied tests
    validation error tests
    lockout/token/session lifecycle tests
15. Runtime and Deployment Pattern
    Docker patterns:
    base image: python:3.12-slim
    non-root user in container
    healthcheck endpoint
    run with uvicorn
    Compose patterns:
    explicit env mapping for app settings
    postgres service with healthcheck
    app depends on postgres health
16. Reuse Checklist for New Projects
    When starting a new backend:
    Create root structure exactly.
    Copy Settings pattern with env aliases and validators.
    Keep controller/service/repository boundaries strict.
    Add generic response + pagination envelope.
    Add base exception + global handlers.
    Add request-id middleware + structured logging.
    Add DB base repository + entity conventions.
    Add initial + seed migrations.
    Add auth middleware and permission dependency.
    Add root tests for contract + auth + RBAC.
17. Quick Templates
    17.1 Service Method Template
    def do_something(self, db: Session, payload: InputModel) -> GenericResponse[OutputModel]:
    self._logger.info("MyService.do_something started.")
    self._logger.debug("MyService.do_something input: field=%s", payload.field)
    try:
    result = MyRepository(db).query(...)
    if result is None:
    raise MyNotFoundException()

        response = GenericResponse.success_response(
            message="Operation successful.",
            data=OutputModel(...),
            status_code=200,
        )
        self._logger.info("MyService.do_something completed successfully.")
        return response
    except MyNotFoundException:
    self._logger.info("MyService.do_something ended with business validation failure.")
    raise
    except Exception:
    self._logger.exception("MyService.do_something failed unexpectedly.")
    raise MyServiceException("Unable to process request right now.") from None
    17.2 Controller Endpoint Template
    @router.get("/{item_id}", response_model=GenericResponse[ItemResponse], status_code=200)
    def get_item(
    item_id: int,
    response: Response,
    db: Session = Depends(get_db),
    ) -> GenericResponse[ItemResponse]:
    service_response = item_service.get_item(db=db, item_id=item_id)
    return apply_status_code(response=response, payload=service_response)
    17.3 Repository Query Template
    def exists_for_user(self, user_id: int) -> bool:
    statement = select(MyEntity.id).where(MyEntity.user_id == user_id).limit(1)
    return self.db.execute(statement).scalar_one_or_none() is not None