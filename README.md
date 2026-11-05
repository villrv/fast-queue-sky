# FAST Queue Sky

All-sky map of the FAST spectrograph queue as seen from FLWO (Mt. Hopkins), with a time slider for the night, hover cards, and a light curve and altitude chart for each target.

Live page: https://villrv.github.io/fast-queue-sky/

- `refresh.py` rebuilds the page from the queue Google Sheet (public CSV export). Light curves come from `lc_cache.json` (YSE-PZ photometry, pulled separately) with Orcus photometry for new targets.
- `template.html` is the page; `index.html` is the built page with the queue embedded.
