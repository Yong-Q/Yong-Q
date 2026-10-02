# Maintaining the profile

The profile uses only public repository metadata. No email or popularity counters are displayed.

- New original, nonempty public repositories appear automatically under Recently updated.
- Forks, archived repositories and the profile repository are excluded.
- Featured project descriptions follow the repository Description when set. With an empty Description, profile.json supplies a curated summary.
- Edit profile.json to change featured projects, research keywords or verified paper/data links. Publication records are not inferred from repository uploads.
- Edit README outside PROFILE:START and PROFILE:END to add your own content; the generator preserves it.
- Automatic refresh runs hourly through GitHub Actions; GitHub can delay scheduled runs. Use Actions → Refresh research profile → Run workflow to refresh manually.
- Scheduled workflows in public repositories may be disabled by GitHub after 60 days without repository activity. Re-enable the workflow from Actions if this occurs.
- index.html is a live local preview. Open it directly, or run `python -m http.server 8765 --bind 127.0.0.1` from the repository and visit http://127.0.0.1:8765. It reads public GitHub metadata every five minutes while visible. On failure, the last good snapshot remains visible.

Local refresh: `python -B scripts/update_profile.py`. Local checks: `python -B -m unittest discover -s tests -v`.

The GitHub sidebar Bio is an account setting, separate from this README. Suggested Bio:

`Porous materials · Classical DFT (cDFT) · Molecular simulation · AI for Science`

Change it at https://github.com/settings/profile. SSH repository access cannot modify account settings.
