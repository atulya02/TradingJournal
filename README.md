# Trading Journal V26 — Premium Windows UI

Existing Python + PySide6 + SQLite trading journal, visually transformed into a dark, premium trading workspace while preserving the existing database schema, calculations, trade/account workflows and persistence model.

## What was changed
- Premium dark design system with restrained blue/green/red semantic accents.
- Redesigned application shell and compact modern sidebar.
- Global active-account selector in the sidebar, synchronized with Dashboard, History, Analytics and New Trade selectors.
- Global account balance / journal P&L indicator.
- More consistent inputs, buttons, tables, checklist controls, scrollbars, tooltips and dialogs.
- Tighter typography, spacing, hierarchy and surface treatment.
- More tactile button states and smoother page transitions.
- Preserved existing account balance adjustment behavior and centralized `refresh_all()` flow.
- No mock data and no replacement of SQLite business logic.

## Account management
Each account can be edited from the Accounts page, and the selected account can be edited directly from the Dashboard.

Editable:
- Account name
- Starting balance
- Current balance
- Daily loss limit
- Max loss

## Balance behavior
Current Balance is:

Starting Balance + Manual Balance Adjustment + Journal Net

Journal Net:
- PROFIT -> + Profit Amount entered in the trade
- LOSS -> - Amount Risked entered in the trade
- STILL RUNNING -> 0

Direct balance edits are preserved. A manual balance correction is stored as a persistent adjustment, so the next journal refresh does not reset the account to its original starting balance.

Example:
Starting = $15,000
Direct Current Balance = $15,500
Later +$200 PROFIT -> $15,700
Later -$100 LOSS -> $15,600

## Run
Use `run_windows.bat` on Windows.

## Build
Use `build_windows.bat` to build the Windows executable with PyInstaller.

Note: the supplied execution environment did not have PySide6 installed, so syntax/static validation was performed here but a live Qt window render could not be exercised in this environment. Run the application on Windows with the listed requirements installed for final visual QA.

## TradeLogix — Windows Installer

The application is branded **TradeLogix**, with a custom application icon and Windows installer configuration.

### Build the installer on Windows

1. Install Python 3.11+ and Inno Setup 6.
2. Open this folder in Command Prompt.
3. Run `build_windows.bat`.
4. The finished installer will be created at:
   `installer\\TradeLogix-Setup-1.0.0.exe`

The installer uses a per-user installation under `%LOCALAPPDATA%\\Programs\\TradeLogix`, so the application does not require administrator privileges. Journal data remains in the installed application data folders and is not intentionally deleted by the uninstaller.
