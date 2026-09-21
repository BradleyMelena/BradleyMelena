# Fantasy Draft War Room

Local draft app: ESPN league sync, keepers, multi-source consensus rankings (Sleeper, ESPN, Underdog, PFF), and a Claude-powered live draft assistant.

## Run it

```
cd fantasy-draft-app
python3 server.py
```

Open **http://localhost:8432**. Everything (settings, rankings, keepers, picks) saves in your browser automatically.

## One-time setup

**1. ESPN (Setup tab)**
- League ID: from your league URL (`leagueId=123456`).
- Private league? You need two cookies: log into espn.com in Chrome → View → Developer → Developer Tools → Application → Cookies → espn.com → copy **SWID** and **espn_s2**.
- Click *Connect to ESPN*, then select which team is yours.

**2. Claude API key**
- Go to console.anthropic.com → sign up → API Keys → create key (add ~$5 credit; a full draft's analysis costs well under $1 on Sonnet).
- Paste into the Setup tab and click *Test key*.

**3. Rankings tab**
- Click *Fetch Sleeper* and *Fetch ESPN ranks + ADP* (automatic).
- Underdog: Draft lobby → rankings export, or copy their board into a CSV with `Rank, Player` columns → upload.
- PFF: their draft rankings page has a CSV download → upload.
- Any CSV works if it has a player-name column; rank column is optional (row order is used).

**4. Keepers tab**
- Enter every team's keepers with round cost. Keeper slots are skipped automatically in the pick order and those players leave the board.

## Draft day

1. Open the **Live Draft** tab, click **▶ Start ESPN live sync** — picks flow in every 5 s automatically.
2. (Backup: type a name in the manual box + Enter, or click *drafted* on any row.)
3. **Analyze my pick now** sends your roster, keepers, picks-until-next-turn, and the top 45 available (with all four sources' ranks + ADP) to Claude, which returns top-3 picks, wait/don't-wait advice, and a sleeper.
4. Check **auto-analyze** to have it fire the moment you're on the clock.
5. The *Value* column = ADP minus current pick: green = falling value, red = reach.

## Notes

- `server.py` is a tiny proxy (Python stdlib only, no installs) because browsers can't call ESPN/Anthropic directly. It only talks to lm-api-reads.fantasy.espn.com, api.sleeper.app, and api.anthropic.com.
- Your API key and cookies never leave your machine except to those official APIs.
- If ESPN sync shows a player as "ESPN player #12345", fetch ESPN ranks first so IDs map to names.
