# Training data

This directory stores presimulated training scenarios and related static assets, such as the tone database. The files are shared repository data rather than frontend source code or database records.

`sample-scenario.json` contains the scenario currently used by the frontend prototype.

`numberbatch-en-19.08.txt.gz` contains the word embeddings used by the backend to find similar words. This file can be downloaded, uploaded to the database, and can be renamed within the tone folder (using `manage.py`).
