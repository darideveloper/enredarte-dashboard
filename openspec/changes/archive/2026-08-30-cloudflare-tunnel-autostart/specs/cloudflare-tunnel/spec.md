## ADDED Requirements

### Requirement: dev.sh auto-starts a Cloudflare tunnel window
When `./dev.sh` runs and `cloudflared` is installed and a tunnel is configured, the script SHALL create a dedicated `tunnel` tmux window that runs the named Cloudflare tunnel, alongside the existing Django window.

#### Scenario: Tunnel starts with dev session
- **WHEN** `./dev.sh` is executed, `cloudflared` is on PATH, and both `CLOUDFLARE_TUNNEL_NAME` and `CLOUDFLARE_TUNNEL_HOST` are set
- **THEN** a tmux window named `tunnel` is created that runs `cloudflared tunnel --config <cfg> run <name>`

#### Scenario: No cloudflared installed
- **WHEN** `./dev.sh` runs on a machine without `cloudflared`
- **THEN** `dev.sh` proceeds with the existing Django/portless windows and does NOT start a tunnel window

### Requirement: Tunnel maps to the active Django port
The generated tunnel configuration SHALL set the ingress `service` to `http://localhost:$PORT` where `$PORT` is the same dynamically selected port used by `runserver`.

#### Scenario: Dynamic port reflected in tunnel
- **WHEN** the port-selection loop chooses port 8001 because 8000 is in use
- **THEN** the generated tunnel config points its ingress `service` at `http://localhost:8001`

#### Scenario: Generated config includes a mandatory catch-all
- **WHEN** `dev.sh` writes the tunnel configuration
- **THEN** the ingress list ends with a terminal catch-all rule `service: http_status:404` so `cloudflared` accepts the config

### Requirement: Tunnel configuration is read from environment with .env.dev fallback
The script SHALL obtain `CLOUDFLARE_TUNNEL_NAME` and `CLOUDFLARE_TUNNEL_HOST` from the shell environment if set, otherwise from `.env.dev` via safe extraction (no `source`), and SHALL resolve the credentials file path at runtime from `cloudflared tunnel list`.

#### Scenario: Vars provided via shell
- **WHEN** `CLOUDFLARE_TUNNEL_NAME` and `CLOUDFLARE_TUNNEL_HOST` are exported in the shell
- **THEN** `dev.sh` uses those values without reading `.env.dev`

#### Scenario: Vars missing from both sources
- **WHEN** neither the shell nor `.env.dev` defines the tunnel vars
- **THEN** `dev.sh` does not start a tunnel and behaves as before

#### Scenario: Credentials resolved without hardcoding
- **WHEN** the named tunnel exists in `cloudflared tunnel list -o json`
- **THEN** the config's `credentials-file` points to `~/.cloudflared/<resolved-id>.json`

### Requirement: Public tunnel host is allowed by Django
The configurable tunnel host (e.g. `enredarte-dashboard.<your-domain>`) SHALL be included in `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` via `.env.dev` so requests over the tunnel are accepted.

#### Scenario: Host accepted by Django
- **WHEN** a request arrives at the tunnel host over HTTPS
- **THEN** Django accepts it because the host is present in `ALLOWED_HOSTS` and CSRF/CORS origin lists

### Requirement: Tunnel failure keeps logs visible
If the tunnel process exits or errors, the tmux window SHALL remain open (e.g. via `read`) so the operator can inspect logs instead of the window closing immediately.

#### Scenario: Tunnel errors
- **WHEN** `cloudflared` exits with an error
- **THEN** the `tunnel` tmux window stays attached with the error output visible
