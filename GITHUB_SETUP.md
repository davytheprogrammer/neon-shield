# Pushing NEON-SHIELD to GitHub

## Setup (One-Time)

### 1. Create a GitHub Repository

1. Go to https://github.com/new
2. Name it: `neon-shield`
3. Description: "Advanced MITM Lab for Authorized Security Research (Educational Use Only)"
4. Make it **Private** (recommended) or Public (your choice)
5. Click **Create repository**

### 2. Add Remote & Push

```bash
# Navigate to neon-shield directory
cd /home/ogega/Projects/neon-shield

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/neon-shield.git

# Set main as default branch
git branch -M main

# Push to GitHub
git push -u origin main
```

### 3. (Optional) Configure GitHub Settings

In your repo settings:

**Protect main branch:**
- Settings → Branches → Add rule
- Apply to: `main`
- Require pull request reviews before merging
- Require status checks to pass (GitHub Actions tests)

**Enable GitHub Pages** (for documentation):
- Settings → Pages
- Source: `main` branch
- Deploy from `/docs` (optional)

---

## Ongoing Workflow

```bash
# Make changes
git add <files>
git commit -m "descriptive message"

# Push to GitHub
git push origin main

# Pull latest
git pull origin main
```

---

## GitHub Actions CI/CD

Tests automatically run on:
- Every push to `main`
- Every pull request

View results: **Actions** tab in your repo

---

## Adding Collaborators (Optional)

To allow others to contribute:

1. Settings → Collaborators
2. Add their GitHub username
3. They'll receive an invitation

---

## Release Checklist

Before tagging a release:

```bash
# Update version in main_cli.py
# Update CHANGELOG
# Ensure all tests pass locally:
pytest tests/ -v

# Tag release
git tag -a v2.0.0 -m "v2.0.0: Production-grade MITM lab"

# Push tags
git push origin --tags
```

---

That's it! Your NEON-SHIELD repo is now on GitHub. 🎉
