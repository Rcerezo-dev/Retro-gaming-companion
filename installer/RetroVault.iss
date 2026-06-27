; PHASE6-2a: Inno Setup script for Retro Vault.
; Build order:
;   1. python installer\download_dats.py   (once; downloads bundled DATs)
;   2. pyinstaller RetroVault.spec
;   3. ISCC installer\RetroVault.iss
; Output: installer\output\RetroVault-Setup.exe

#define MyAppName "Retro Vault"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Rcerezo-dev"
#define MyAppURL "https://github.com/Rcerezo-dev/Retro-gaming-companion"
#define MyAppExeName "RetroVault.exe"

[Setup]
AppId={{B6F1B6C0-6B0F-4E7B-9A6B-0E6E6E6E6E6E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=RetroVault-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; The app keeps its own console-visible server log; no admin rights needed
; since everything lives under the user-chosen install dir + %APPDATA%.
PrivilegesRequired=lowest

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\RetroVault\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Bundled DATs: only installed if the file doesn't already exist (respects user-updated versions)
Source: "..\installer\bundled_dats\nointro\*"; DestDir: "{app}\.rommgr\catalogs\nointro"; Flags: ignoreversion onlyifdoesntexist uninsneveruninstall
Source: "..\installer\bundled_dats\redump\*"; DestDir: "{app}\.rommgr\catalogs\redump"; Flags: ignoreversion onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "serve"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "serve"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
; Closes a running instance before files are overwritten (PHASE6-3b handoff:
; the app launches this installer and exits itself, but cover the manual-run case too).
Filename: "{app}\{#MyAppExeName}"; Parameters: "serve"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
