# GitHub Stars Observatory

A static GitHub Pages site that turns public GitHub Stars into searchable, categorized dashboards.

It works well as a template repository:

1. Use this repository as a template or fork it.
2. Enable GitHub Pages from the `main` branch and `/ (root)` folder.
3. Edit `config.yml`.
4. Run the `Refresh GitHub Stars Dashboard` workflow, or wait for the daily schedule.

## Configuration

```yaml
site_title: GitHub Stars Observatory

# In GitHub Actions, "auto" resolves to the repository owner.
users:
  - username: auto
    label: 我的收藏

  - username: torvalds
    label: Linus Torvalds
```

If you configure one user, the site root is that user's Stars dashboard:

```text
/
```

If you configure three users, the site generates one landing page plus three direct user pages:

```text
/
/<user-1>/
/<user-2>/
/<user-3>/
```

## Privacy

This project only reads public GitHub starred repositories through GitHub's public API.

- It does not read private repositories.
- It does not require a personal GitHub token.
- It can view any user's public Stars if that username is configured.

## Automation

GitHub Actions refreshes the dashboard every day and commits updated generated pages when the data changes. You can also run the workflow manually from the Actions tab.
