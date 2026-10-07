# Deploying NUDGE Omnichannel

**Frontend** → Cloudflare Pages (free).
**Backend** → Oracle Cloud Always Free VM, reached through a free Cloudflare Tunnel.

The backend cannot run on Cloudflare Pages or Workers: it needs PyMC (compiles C
via PyTensor at runtime), cvxpy, psycopg against Postgres with pgvector, and
module runs that take minutes. Workers run Pyodide with a hard CPU ceiling and
have no Postgres. The tunnel is what keeps the public surface on Cloudflare
anyway — the API answers on a Cloudflare hostname, with no inbound port open on
the VM.

```
Browser ─► Cloudflare Pages (static SPA)
              └─ fetch ─► api.yourdomain.com ─► Cloudflare Tunnel ─► Oracle VM
                                                                      ├─ api (FastAPI)
                                                                      └─ postgres + pgvector
```

---

## 0. Prerequisites

- A Cloudflare account (free).
- **A domain on Cloudflare.** A named tunnel needs a zone in your account to
  attach a hostname to. Without one, see [No domain?](#no-domain) below.
- An Oracle Cloud account. Always Free needs a card to verify identity; the
  Ampere A1 shape used here is free indefinitely and is not charged.

---

## 1. Create the Oracle VM

Oracle Cloud console → **Compute → Instances → Create instance**:

| Setting | Value |
|---|---|
| Image | Ubuntu 22.04 or 24.04 |
| Shape | **VM.Standard.A1.Flex** (Ampere, arm64) |
| OCPUs / memory | 2 OCPU / 12 GB (within the 4 OCPU / 24 GB always-free allowance) |
| SSH key | Upload your public key |

If the A1 shape reports "out of capacity", retry in another availability domain
or region — it is a known Always Free constraint, not an account problem.

Note the public IP, then:

```bash
ssh ubuntu@<vm-public-ip>
```

No inbound ports need opening. `cloudflared` dials out to Cloudflare, so the
VM's default closed firewall is correct and should stay that way.

---

## 2. The Cloudflare Tunnel

**No domain (default).** Nothing to set up in the dashboard — compose runs a
free quick tunnel automatically. After Step 4 read the assigned URL with:

```bash
bash deploy/tunnel-url.sh      # -> https://<random>.trycloudflare.com
```

That hostname changes every time the `cloudflared` container restarts. When it
does, rebuild the frontend with the new value (Step 5) — the API's CORS config
is keyed to your *Pages* URL, which is stable, so only the frontend needs it.

**With a domain** (upgrade later, removes the churn): Cloudflare dashboard →
**Zero Trust → Networks → Tunnels → Create a tunnel**, type **Cloudflared**,
name it `nudge-api`. Copy the token from the install screen into `deploy/.env`
as `CLOUDFLARED_CMD=tunnel --no-autoupdate run --token <token>`, then under
**Public Hostname** add subdomain `api`, your domain, service **HTTP**, URL
`api:8000` (`api` is the compose service name, resolved on the internal
network — which is why nothing is published to the host).

---

## 3. Get the code onto the VM

With a Git remote (recommended — also enables Pages auto-deploy):

```bash
git clone https://github.com/<you>/nudge-kit.git && cd nudge-kit
```

Without one, from your laptop:

```bash
rsync -av --exclude .venv --exclude node_modules --exclude var/uploads \
  ~/Desktop/nudge-kit/ ubuntu@<vm-public-ip>:~/nudge-kit/
```

---

## 4. Configure and start the backend

On the VM:

```bash
cd ~/nudge-kit
cp deploy/.env.example deploy/.env
nano deploy/.env        # fill in every blank — see the comments in the file
bash deploy/setup-oracle.sh
```

`setup-oracle.sh` installs Docker, adds 4 GB of swap, and brings up
postgres + api + cloudflared. The first arm64 build takes 10–20 minutes
(PyMC and cvxpy compile from source). Alembic migrations run automatically on
every container start.

Set `CORS_ORIGINS` in `deploy/.env` to your Pages URL before starting, or the
browser will block the frontend's requests.

Check it:

```bash
sudo docker compose -f deploy/docker-compose.prod.yml logs -f api
bash deploy/tunnel-url.sh                      # your public API URL
curl "$(bash deploy/tunnel-url.sh)/system/status"
```

---

## 5. Deploy the frontend to Cloudflare Pages

### From a Git repo (auto-deploys on push)

Cloudflare dashboard → **Workers & Pages → Create → Pages → Connect to Git**:

| Setting | Value |
|---|---|
| Root directory | `frontend` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Environment variable | `VITE_API_BASE_URL` = `https://api.yourdomain.com` |

### Direct upload (no Git)

```bash
cd frontend
VITE_API_BASE_URL=https://api.yourdomain.com npm run deploy
```

Either way `public/_redirects` ships the SPA fallback, so deep links like
`/brands/<id>/brand-plan` resolve instead of 404ing.

> `VITE_API_BASE_URL` is inlined at **build** time. Changing it in the Pages
> dashboard requires a redeploy — a refresh will not pick it up.

---

## 6. Create the first account

The demo login is seeded on your local database, not the server's. On the
deployed site use **Create a workspace** to sign up; that account becomes the
tenant's platform admin.

---

## Redeploying

Backend (on the VM):

```bash
cd ~/nudge-kit && git pull
sudo docker compose -f deploy/docker-compose.prod.yml up -d --build
```

Frontend: push to the connected branch, or re-run `npm run deploy`.

---

## When the tunnel URL changes

On a quick tunnel, restarting `cloudflared` (or rebooting the VM) assigns a new
hostname. To recover:

```bash
# on the VM
bash deploy/tunnel-url.sh

# on your laptop
cd frontend
VITE_API_BASE_URL=<new-url> npm run deploy
```

`CORS_ORIGINS` does not need touching — it lists the frontend's Pages origin,
which never changes. A domain on Cloudflare (~$10/yr) removes this step
entirely; see Step 2.

---

## Costs

| Piece | Cost |
|---|---|
| Cloudflare Pages | Free (unlimited requests, 500 builds/mo) |
| Cloudflare Tunnel | Free |
| Oracle Ampere A1 VM | Free (Always Free tier) |
| Postgres + pgvector | Free (container on the VM) |
| Domain | ~$10/yr, only piece that is not free |
| Anthropic + Serper API | Metered by usage; capped per run by `NUDGE_RUN_BUDGET_USD` |
