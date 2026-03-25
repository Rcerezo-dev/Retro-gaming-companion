"""Desktop toast notifications for Windows (10/11).

Uses PowerShell + Windows.UI.Notifications WinRT — no external modules needed.
On non-Windows or if PowerShell fails, does nothing (fire-and-forget).
"""
from __future__ import annotations

import subprocess
import sys

# PowerShell script template — two text lines (title + body)
_PS_TEMPLATE = r"""
[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]|Out-Null
$template=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$xml=[xml]$template.GetXml()
$xml.GetElementsByTagName('text')[0].AppendChild($xml.CreateTextNode({title}))|Out-Null
$xml.GetElementsByTagName('text')[1].AppendChild($xml.CreateTextNode({body}))|Out-Null
$doc=New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml.OuterXml)
$toast=[Windows.UI.Notifications.ToastNotification]::new($doc)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Retro Vault').Show($toast)
"""


def _ps_escape(s: str) -> str:
    """Escape a string for safe inclusion in a single-quoted PowerShell string."""
    return "'" + s.replace("'", "''") + "'"


def notify(title: str, body: str) -> None:
    """Show a Windows desktop toast notification.

    Safe to call from any thread. Returns immediately; the PowerShell
    process runs detached. No-op on non-Windows or if powershell.exe is
    unavailable.
    """
    if sys.platform != "win32":
        return
    script = _PS_TEMPLATE.format(
        title=_ps_escape(title),
        body=_ps_escape(body),
    )
    try:
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
             "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
    except Exception:
        pass  # Silently ignore — notifications are best-effort
