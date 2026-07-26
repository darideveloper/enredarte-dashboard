## 1. Activate admin registration

- [x] 1.1 Add `import project.admin` to `project/urls.py`

## 2. Document the pattern

- [x] 2.1 Create note at `/home/daridev/Desktop/obsidian/daridev/20-areas/work/django` explaining that `admin.py` in a non-app package must be explicitly imported, with the `import project.admin` idiom as the solution

## 3. Verify

- [x] 3.1 Start the dev server, navigate to admin sidebar, confirm User shows `person` icon, Group shows `group` icon, Token shows `key` icon
