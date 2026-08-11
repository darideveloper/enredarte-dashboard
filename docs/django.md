---
created: 2026-04-21
updated: 2026-04-21
tags:
  - django
  - python
  - backend
  - hub
type: area-note
status: active
---

# Django

Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. It handles much of the complexity of web development, allowing you to focus on writing your app without needing to reinvent the wheel.

### **Internal Resources**
*   [[django-project-setup|Project Setup Guide]]
*   [[django-model-definitions|Model Definitions]]
*   [[django-media-storage|Media Storage Configuration]]
*   [[django-unfold-admin|Unfold Admin Theme]]
*   [[django-image-copy-link|Image Copy Link Utility]]
*   [[django-drf|DRF Implementation Guide]]
*   [[django-fixtures|Fixed Data Loading with Django Fixtures]]
*   [[django-redis|Redis in Django Integration Guide]]
*   [[django-local-subdomain-setup|Local Development & Subdomain Setup]]
*   [[django-i18n-es-admin|Spanish Django Admin]]
*   [[20-areas/work/mermaid/mermaid-diagram-generation|Mermaid Diagram Generation]]

### **Wikilinks & Portability**

These docs use Obsidian `[[wikilinks]]`. When copying them into a new Django
project, the agent MUST handle links as follows:

1. Short-form links (`[[django-project-setup|label]]`) point to sibling docs in
   the same folder — keep them as-is.
2. Vault-path links to sibling docs (e.g. `[[20-areas/work/django/django-foo]]`)
   → convert to short-form `[[django-foo|label]]`.
3. Vault-path links to external resources not included in the project (e.g.
   `[[30-resources/redis/redis|Redis]]`) have NO local equivalent — replace the
   link with a plain text label (e.g. `Redis (external)`).

This keeps a project copy self-contained so team members without the vault do
not see broken wikilinks.
