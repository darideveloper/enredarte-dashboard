## ADDED Requirements

### Requirement: DRF app registration and settings
The system SHALL configure `REST_FRAMEWORK` in `settings.py` with: `DEFAULT_PERMISSION_CLASSES` set to `IsAuthenticated`, `DEFAULT_PAGINATION_CLASS` referencing `project.pagination.CustomPageNumberPagination`, `PAGE_SIZE=12`, `DEFAULT_AUTHENTICATION_CLASSES` including `TokenAuthentication` and `SessionAuthentication`, and `EXCEPTION_HANDLER` referencing `project.handlers.custom_exception_handler`.

#### Scenario: API requires authentication
- **WHEN** an unauthenticated request hits any API endpoint
- **THEN** DRF SHALL return HTTP 401 Unauthorized

#### Scenario: Paginated response uses custom paginator
- **WHEN** an API endpoint returns a list of items
- **THEN** the response SHALL be paginated with max 12 items per page by default

### Requirement: Custom pagination with metadata
The system SHALL create `project/pagination.py` with a `CustomPageNumberPagination` class extending `PageNumberPagination`. It SHALL support `page_size_query_param='page_size'` and `max_page_size=100`. The `get_paginated_response` method SHALL return a response containing: `count`, `next`, `previous`, `page` (current page number), `page_size`, `total_pages`, and `results`.

#### Scenario: Pagination metadata included
- **WHEN** an API call returns paginated results with 25 total items and page_size=12
- **THEN** the response SHALL include `count: 25`, `page: 1`, `page_size: 12`, `total_pages: 3`

### Requirement: Custom exception handler
The system SHALL create `project/handlers.py` with a `custom_exception_handler` function. It SHALL call DRF's default `exception_handler` first, then transform the response data to a uniform format: `{"status": "error", "message": "<detail or default>", "data": {<remaining fields>}}`. If the original response has a `detail` key, its value SHALL become `message` and `detail` SHALL be removed from `data`.

#### Scenario: Validation error formatted uniformly
- **WHEN** a POST request with invalid data receives a 400 response
- **THEN** the response body SHALL be `{"status": "error", "message": "Invalid data", "data": {"field_name": ["error text"]}}`

#### Scenario: Authentication error formatted uniformly
- **WHEN** an unauthenticated request receives a 401 response
- **THEN** the response body SHALL be `{"status": "error", "message": "Invalid data", "data": {}}` with `detail` text not duplicated in `data`

### Requirement: DRF router in URL configuration
The system SHALL initialize a `routers.DefaultRouter()` instance in `project/urls.py` and include it at `path("api/", include(router.urls))`. The API root view SHALL be accessible at `/api/`.

#### Scenario: API root accessible
- **WHEN** browser navigates to `/api/`
- **THEN** DRF's default API root SHALL render, showing no registered viewsets (empty router initially)

### Requirement: Global datetime formatting
The system SHALL set Django's `DATE_FORMAT="d/b/Y"`, `TIME_FORMAT="H:i"`, and `DATETIME_FORMAT=f"{DATE_FORMAT} {TIME_FORMAT}"` in `settings.py`. This SHALL be applied globally to DRF serializers and admin date displays.

#### Scenario: Date formatted as d/b/Y
- **WHEN** a date field is serialized or displayed
- **THEN** it SHALL render in `03/Abr/2026` format
