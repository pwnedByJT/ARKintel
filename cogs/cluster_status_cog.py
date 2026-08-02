"""
Cog: cogs/cluster_status_cog.py
Description: /cluster-status slash command — displays live Pod health and resource
             info for the ARKintel K3s workload by querying the Kubernetes in-cluster
             API via aiohttp (no kubectl required in the container).

Prerequisites (apply before using this command):
    kubectl apply -f k8s/rbac.yaml
    # Then add serviceAccountName: arkintel to your deployment.yaml and redeploy.

Author: pwnedByJT
"""

import os
import ssl
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# MODULE-LEVEL PROCESS START TIME
# Used as an uptime fallback when K8s startTime is unavailable.
# ---------------------------------------------------------------------------
_BOT_START_TIME: datetime = datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# IN-CLUSTER CONSTANTS
# ---------------------------------------------------------------------------
_K8S_SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount"
_K8S_API    = "https://kubernetes.default.svc"


def _in_cluster() -> bool:
    """True when the service-account directory is present (inside a Pod)."""
    return os.path.isdir(_K8S_SA_DIR)


def _format_uptime(start_iso: str) -> str:
    """Return a human-readable uptime string from a K8s ISO-8601 timestamp."""
    try:
        start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        delta     = datetime.now(timezone.utc) - start_dt
        total     = int(delta.total_seconds())
        hours, r  = divmod(total, 3600)
        return f"{hours}h {r // 60}m"
    except Exception:
        return "N/A"


async def _query_pod(pod_name: str, namespace: str) -> tuple[dict | None, str]:
    """
    Hit the K8s in-cluster API and return (pod_json, error_message).
    Returns (None, reason) on any failure so the caller can surface a clean embed.
    """
    token_path = os.path.join(_K8S_SA_DIR, "token")
    ca_path    = os.path.join(_K8S_SA_DIR, "ca.crt")

    try:
        with open(token_path) as f:
            token = f.read().strip()
    except OSError as exc:
        return None, f"Cannot read service-account token: {exc}"

    ssl_ctx = ssl.create_default_context()
    try:
        ssl_ctx.load_verify_locations(cafile=ca_path)
    except (ssl.SSLError, OSError):
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode    = ssl.CERT_NONE

    url     = f"{_K8S_API}/api/v1/namespaces/{namespace}/pods/{pod_name}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, ssl=ssl_ctx, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 403:
                    return None, (
                        "**403 Forbidden** — the Pod's ServiceAccount lacks `get pods` permission.\n"
                        "Apply `k8s/rbac.yaml` and add `serviceAccountName: arkintel` to your deployment, then redeploy."
                    )
                if resp.status != 200:
                    return None, f"K8s API returned HTTP {resp.status}."
                return await resp.json(), ""
    except aiohttp.ClientConnectorError:
        return None, "Cannot reach `kubernetes.default.svc` — is this Pod running inside K3s?"
    except Exception as exc:
        return None, f"Unexpected error: {exc}"


def _parse_pod(data: dict) -> dict:
    """Extract the 8 display fields from a raw pod JSON response."""
    meta       = data.get("metadata", {})
    spec       = data.get("spec", {})
    status     = data.get("status", {})
    containers = spec.get("containers", [{}])
    cs_list    = status.get("containerStatuses", [{}])

    container  = containers[0] if containers else {}
    cs         = cs_list[0]    if cs_list    else {}
    resources  = container.get("resources", {})
    limits     = resources.get("limits", {})
    requests   = resources.get("requests", {})

    return {
        "pod_name":  meta.get("name",       "N/A"),
        "namespace": meta.get("namespace",  "N/A"),
        "phase":     status.get("phase",    "N/A"),
        "restarts":  cs.get("restartCount", "N/A"),
        "uptime":    _format_uptime(status.get("startTime", "")),
        "pod_ip":    status.get("podIP",    "N/A"),
        "node":      spec.get("nodeName",   "N/A"),
        "mem":       f"{requests.get('memory', 'N/A')} / {limits.get('memory', 'N/A')}",
        "cpu":       f"{requests.get('cpu',    'N/A')} / {limits.get('cpu',    'N/A')}",
    }


def _build_status_embed(fields: dict) -> discord.Embed:
    phase = fields["phase"]
    color = 0x57F287 if phase == "Running" else (0xFEE75C if phase == "Pending" else 0xED4245)

    embed = discord.Embed(
        title="[CLUSTER-STATUS]  ARKintel K3s Workload",
        color=discord.Color(color),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  K3s on Raspberry Pi")

    embed.add_field(name="Pod Name",   value=f"```{fields['pod_name']}```", inline=False)
    embed.add_field(name="Namespace",  value=f"`{fields['namespace']}`",    inline=True)
    embed.add_field(name="Status",     value=f"`{fields['phase']}`",        inline=True)
    embed.add_field(name="Restarts",   value=f"`{fields['restarts']}`",     inline=True)
    embed.add_field(name="Uptime",     value=f"`{fields['uptime']}`",       inline=True)
    embed.add_field(name="Cluster IP", value=f"`{fields['pod_ip']}`",       inline=True)
    embed.add_field(name="Node",       value=f"`{fields['node']}`",         inline=True)
    embed.add_field(
        name="Memory  (req / limit)",
        value=f"`{fields['mem']}`",
        inline=True,
    )
    embed.add_field(
        name="CPU  (req / limit)",
        value=f"`{fields['cpu']}`",
        inline=True,
    )
    return embed


def _build_error_embed(reason: str) -> discord.Embed:
    embed = discord.Embed(
        title="[CLUSTER-STATUS]  Unable to Reach K8s API",
        description=reason,
        color=discord.Color(0xED4245),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  K3s on Raspberry Pi")
    return embed


def _build_not_in_cluster_embed() -> discord.Embed:
    # Fall back to process uptime when running outside K3s (local dev / CI)
    delta = datetime.now(timezone.utc) - _BOT_START_TIME
    hours, r = divmod(int(delta.total_seconds()), 3600)
    uptime   = f"{hours}h {r // 60}m"

    embed = discord.Embed(
        title="[CLUSTER-STATUS]  Running Outside Kubernetes",
        description=(
            "No service-account directory found — ARKintel is not running inside a K3s Pod.\n"
            f"Process uptime: `{uptime}`"
        ),
        color=discord.Color(0xFEE75C),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel")
    return embed


# ---------------------------------------------------------------------------
# COG
# ---------------------------------------------------------------------------

class ClusterStatusCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="cluster-status",
        description="Displays live status and uptime for the ARKintel K3s workload.",
    )
    async def cluster_status(self, itxn: discord.Interaction) -> None:
        await itxn.response.defer()

        if not _in_cluster():
            return await itxn.followup.send(embed=_build_not_in_cluster_embed())

        pod_name  = os.environ.get("HOSTNAME", "unknown")
        namespace = "default"
        ns_path   = os.path.join(_K8S_SA_DIR, "namespace")
        try:
            with open(ns_path) as f:
                namespace = f.read().strip()
        except OSError:
            pass

        pod_data, err = await _query_pod(pod_name, namespace)

        if pod_data is None:
            return await itxn.followup.send(embed=_build_error_embed(err))

        fields = _parse_pod(pod_data)
        await itxn.followup.send(embed=_build_status_embed(fields))

    @cluster_status.error
    async def cluster_status_error(self, itxn: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await itxn.response.send_message(f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ClusterStatusCog(bot))
