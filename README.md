# wow-armory-sync

A GitHub Action fetches public WoW character data from Blizzard's API every 2 hours and saves it to `characters.json`, which Dave's WoW Second Screen dashboard reads.

- Credentials live only in encrypted Actions secrets (`BNET_ID`, `BNET_SECRET`); nothing secret is written to the repo.
- To add a character, edit `CHARS` in `sync.py`.
- Run it now: Actions tab → "Sync WoW characters" → Run workflow.
