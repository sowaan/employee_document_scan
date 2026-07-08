# Scanner Utility — Sequence Flow

End-to-end flow from launching `run_scanner.bat` to the "Load Latest Scan" button
in the Employee form.

```mermaid
sequenceDiagram
    autonumber
    actor User as Operator
    participant BAT as run_scanner.bat
    participant SUP as start_scanner.py
    participant TRAY as tray_ui.py
    participant WATCH as watcher.py
    participant CFG as scanner_control.json
    participant SCAN as Scanner + OutputWedge
    participant DIR as Watch Folder<br/>C:\Users\shama\Documents\Picture
    participant ERP as ERP Server<br/>daralburaq.sowaanerp.com
    participant FORM as Employee Form (Browser)

    %% ---------- Launch ----------
    User->>BAT: double-click
    BAT->>SUP: python start_scanner.py
    SUP->>SUP: verify tray_ui.py & watcher.py exist,<br/>open tray/watcher log files
    SUP->>TRAY: Popen(pythonw.exe) — cwd=BASE_DIR (no console)
    SUP->>WATCH: Popen(python.exe) — cwd=BASE_DIR
    loop supervisor every 5s
        SUP->>TRAY: poll()
        SUP->>WATCH: poll()
        Note over SUP: if either exits → log exit code & stop
    end

    %% ---------- Tray control ----------
    Note over TRAY,CFG: Tray is the only UI — writes config only
    User->>TRAY: pick mode (EID / PASSPORT) or Reset
    TRAY->>CFG: write { mode, reset }

    %% ---------- Watcher startup ----------
    WATCH->>DIR: ensure_folders() — folder exists?
    WATCH->>WATCH: cleanup_temp_folder()
    loop until logged in (retry 10s)
        WATCH->>ERP: POST /api/method/login (usr, pwd)
        alt Logged In
            ERP-->>WATCH: 200 + session cookie + CSRF token
        else failure
            ERP-->>WATCH: error → wait 10s, retry
        end
    end

    %% ---------- Scan → upload ----------
    loop main loop every 1s
        WATCH->>CFG: read mode / reset
        User->>SCAN: scan document
        SCAN->>DIR: write/overwrite ImageVis.png
        WATCH->>DIR: mtime of ImageVis.png changed?
        alt new image detected
            WATCH->>WATCH: wait 0.5s, copy to temp file
            alt mode = PASSPORT (1 side)
                WATCH->>ERP: POST /api/method/upload_file (front)
                ERP-->>WATCH: file_url
                WATCH->>ERP: POST /api/resource/Scanned Documents<br/>{front_image, is_single=1}
            else mode = EID (2 sides)
                Note over WATCH: capture front, then back
                WATCH->>ERP: upload_file(front) → upload_file(back)
                ERP-->>WATCH: front_url, back_url
                WATCH->>ERP: POST /api/resource/Scanned Documents<br/>{front_image, back_image, is_single=0}
            end
            alt created (200/201)
                ERP-->>WATCH: OK → delete temp files, log success
            else upload/create failed
                ERP-->>WATCH: error → log, keep looping
            end
        end
    end

    %% ---------- Consumer ----------
    Note over FORM,ERP: Fully decoupled from the scanner machinery
    User->>FORM: click "Load Latest Scan"
    FORM->>ERP: get latest Scanned Documents record
    ERP-->>FORM: front/back image URLs
    FORM->>User: preview scanned image(s)
```

## Why this design

- **`.bat` → `start_scanner.py` supervisor launching two processes** — the launcher's only
  job is to start and babysit two independent workers and surface crashes (exit codes + log
  files). Keeping the tray UI and the uploader in separate processes means one can fail or be
  restarted without taking down the other.
- **`tray_ui.py` via `pythonw.exe`, `watcher.py` via `python.exe`** — the tray is a GUI that
  should have no console window (`pythonw`), while the watcher's console/logs are useful for
  diagnosing scan/upload issues.
- **`scanner_control.json` as the IPC channel** — the tray and watcher never talk directly.
  The tray *writes* `mode`/`reset`; the watcher *reads* it once per loop. A plain JSON file is
  simple, restart-safe, and needs no sockets — at the cost of being poll-based, not event-driven.
- **Folder + mtime polling instead of talking to the scanner** — the OutputWedge hardware only
  knows how to *write an image file to disk*. So the watcher bridges "file appeared" → "record
  created in ERP." The filesystem path IS the integration contract.
- **Retry/guard logic on login, upload, and create** — this runs unattended on a kiosk PC, so
  every network step must fail safe and keep looping rather than crash.
- **The "Load Latest Scan" button is decoupled** — it just reads the most recent
  `Scanned Documents` record over HTTP, unaware of the scanner pipeline that produced it.

## Known gotcha

`tray_ui.py` uses a **relative** `CONTROL_FILE = "scanner_control.json"` while `watcher.py`
uses an **absolute** `os.path.join(BASE_DIR, "scanner_control.json")`. They resolve to the same
file only because `start_scanner.py` launches both with `cwd=BASE_DIR`. If the tray is ever
started from a different working directory, mode/reset changes silently write to a different
file and never reach the watcher. Making both absolute would remove this fragility.
