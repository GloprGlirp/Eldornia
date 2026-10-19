; Eldornia – Windows-Installer (Inno Setup 6)
; Erzeugt EldorniaSetup.exe mit Startmenü- und Desktopverknüpfung sowie Deinstallation.

#define AppName "Eldornia"
#ifndef AppVersion
  #define AppVersion "0.3.0"
#endif

[Setup]
AppId={{EC305EDD-7D53-48A9-B576-088A3FD8629A}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Eldornia
DefaultDirName={autopf}\Eldornia
DefaultGroupName=Eldornia
DisableProgramGroupPage=yes
OutputDir=..\build\installer
OutputBaseFilename=EldorniaSetup
SetupIconFile=..\client\assets\icon.ico
UninstallDisplayIcon={app}\Eldornia.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\build\windows\Eldornia.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\build\windows\*.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\README.md"; DestDir: "{app}"; DestName: "Liesmich.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\Eldornia"; Filename: "{app}\Eldornia.exe"
Name: "{group}\Eldornia deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Eldornia"; Filename: "{app}\Eldornia.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Eldornia.exe"; Description: "{cm:LaunchProgram,Eldornia}"; Flags: nowait postinstall skipifsilent
