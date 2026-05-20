# Service Naming Conventions

This document defines the naming standard for service methods in StreamSync.
The goal is to make service APIs predictable, readable, and easy to test.

## Core Rule

Use: `<clear_verb>_<domain_object>[_<qualifier>]`

Examples:
- `get_user_by_id`
- `create_profile_preferences`
- `update_user_avatar`
- `delete_review`
- `build_dashboard_context`
- `calculate_review_trend`

## Approved Verb Prefixes

Use these verbs as first choice:

- `get_`: fetch a single item or aggregate result
- `list_`: fetch a collection
- `create_`: create new records/resources
- `update_`: modify existing records/resources
- `delete_`: remove records/resources
- `build_`: assemble a complex response/context
- `calculate_`: compute derived metrics or analytics

Additional allowed verbs when they represent real domain actions:
- `publish_`, `register_`, `add_`, `remove_`, `sync_`, `enrich_`, `generate_`

## Method Intent by Verb

- `get_` should not mutate data.
- `list_` should not mutate data.
- `create_`, `update_`, `delete_` are write operations.
- `calculate_` should return computed values without persistence, unless explicitly required.
- `build_` can orchestrate multiple reads/calculations to return structured output.

## Naming Examples by App

### Users
- `get_user_profile`
- `create_user_with_preferences`
- `update_profile_preferences`
- `update_user_avatar`
- `delete_user_account`

### Contents
- `get_content_detail`
- `list_catalog_content`
- `calculate_community_rating`
- `build_recommendations_for_content`
- `sync_content_to_local_db`

### Lists
- `create_folder`
- `update_folder`
- `delete_folder`
- `add_content_to_list`
- `remove_content_from_list`
- `list_user_folders`

### Reviews
- `create_feedback`
- `publish_review`
- `delete_review`
- `get_user_review_for_content`
- `list_content_reviews`

### Analytics
- `register_view`
- `get_platform_metrics`
- `calculate_view_trend`
- `calculate_user_trend`
- `build_dashboard_context`
- `generate_dashboard_pdf`

## Anti-Patterns (Do Not Use)

Avoid generic and ambiguous method names:
- `process_data`
- `handle_logic`
- `do_task`
- `run`
- `execute`

Avoid unclear abbreviations:
- `get_usr`
- `calc_rev`
- `upd_prof`

## Consistency Rules

- Keep one naming style across all apps.
- Prefer English for service method names.
- Use singular nouns for single-object operations (`get_user_profile`).
- Use plural nouns for collection operations (`list_user_reviews`).
- Keep names specific to the business action and return value.
