; Retro Vault — Inno Setup installer script (PHASE6-2a)
; Requires Inno Setup 6.x  https://jrsoftware.org/isinfo.php
;
; Build: run after `build.ps1` so dist\RetroVault\ is populated.
;   iscc installer\RetroVault.iss
;
; Output: installer\Output\RetroVaultSetup-0.1.0.exe

#define AppName      "Retro Vault"
#define AppVersion   "0.1.0"
#define AppPublisher "Rcerezo-dev"
#define AppExeName   "RetroVault.exe"
#define AppURL       "https://github.com/Rcerezo-dev/Retro-gaming-companion"
#define SrcDir       "..\dist\RetroVault"

[Setup]
AppId={{A7E2B3D1-9F4C-4A1E-8B3F-6D2C0E1A5F7B}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Single output installer executable
OutputDir=Output
OutputBaseFilename=RetroVaultSetup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
; Require UAC elevation for Program Files
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
; Windows 10 minimum (needed for our Python 3.12 exe)
MinVersion=10.0
; Uninstaller metadata shown in Add/Remove Programs
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
; Sign the installer when a cert is available (uncomment and set path)
;SignTool=signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a $f
WizardStyle=modern
SetupIconFile=

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy the entire PyInstaller COLLECT output directory
Source: "{#SrcDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Copy example config only if the user has no existing config (first install)
Source: "{#SrcDir}\config.toml"; DestDir: "{userappdata}\RetroVault"; DestName: "config.toml"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
; Start Menu shortcut — launches tray mode
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Parameters: "serve --tray"; WorkingDir: "{app}"; Comment: "Retro Vault ROM Manager"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
; Optional desktop shortcut (only if task selected)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Parameters: "serve --tray"; WorkingDir: "{app}"; Tasks: desktopicon; Comment: "Retro Vault ROM Manager"

[Run]
; Offer to launch the app at the end of install (non-admin token so tray works normally)
Filename: "{app}\{#AppExeName}"; Parameters: "serve --tray"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[UninstallRun]
; Kill any running instance before uninstall
Filename: "taskkill.exe"; Parameters: "/f /im {#AppExeName}"; Flags: runhidden; RunOnceId: "KillRetroVault"

[Code]
// ── Upgrade detection ──────────────────────────────────────────────────────
// If an older version is already installed, offer to remove it first.
function InitializeSetup(): Boolean;
var
  UninstPath, UninstExe: String;
  ResultCode: Integer;
begin
  Result := True;
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A7E2B3D1-9F4C-4A1E-8B3F-6D2C0E1A5F7B}_is1',
    'UninstallString', UninstExe) then
  begin
    if MsgBox('An older version of Retro Vault is already installed.'#13#10 +
              'It is recommended to uninstall it first.'#13#10#13#10 +
              'Would you like to uninstall the previous version now?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec(RemoveQuotes(UninstExe), '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
