# 📧 Dagelijkse Beursupdate Setup

Dit script stuurt elke dag om **20:00 UTC** een e-mail met beursnieuws en portfolio-updates naar alfendirk@gmail.com.

## 🚀 Setup stappen

### 1. Push naar GitHub
```bash
git add .
git commit -m "Add daily stock news emailer"
git remote add origin https://github.com/YOUR_USERNAME/daily-stock-news.git
git push -u origin master
```

### 2. Gmail App Password aanmaken
Je moet een **App Password** (niet je gewone Gmail-wachtwoord) gebruiken voor veiligheid.

**Stappen:**
1. Ga naar: https://myaccount.google.com/security
2. Schakel "2-Step Verification" in (als niet al gedaan)
3. Ga naar "App passwords"
4. Selecteer: 
   - App: "Mail"
   - Device: "Windows/Mac/Linux"
5. Kopieer je 16-karakter app-wachtwoord

### 3. GitHub Secrets toevoegen
In je GitHub repo:
1. Ga naar **Settings** → **Secrets and variables** → **Actions**
2. Klik **New repository secret**
3. Voeg deze secrets toe:

| Secret name | Waarde |
|---|---|
| `GMAIL_USER` | `alfendirk@gmail.com` |
| `GMAIL_APP_PASSWORD` | `jouw-16-karakter-wachtwoord` |

### 4. Workflow time aanpassen (optioneel)
De workflow runt nu op **20:00 UTC**. Pas dit aan in `.github/workflows/daily-stock-news.yml`:

- **UTC+1 (Amsterdam)** → `0 19 * * *` (19:00)
- **UTC+2 (zomer)** → `0 18 * * *` (18:00)
- **Andere zone** → gebruik [crontab.guru](https://crontab.guru)

### 5. Test handmatig
GitHub biedt een **"Run workflow"** knop:
1. Ga naar **Actions** tab in je repo
2. Selecteer workflow: "Daily Stock News Email"
3. Klik **"Run workflow"**

## 📋 Wat krijg je?

Elke dag een e-mail met:
- ✅ Top 5 markt-/macronieuws
- ✅ Nieuws over je portfolio-aandelen
- ✅ Alerts en tips

Voorbeeld onderwerp: `📌 Dagelijkse beursupdate – 22 april 2026`

## 🔧 Troubleshooting

**Script runt niet?**
- Check GitHub Actions logs: repo → **Actions** tab
- Verifieer GMAIL_USER en GMAIL_APP_PASSWORD zijn correct ingesteld

**Geen e-mail ontvangen?**
- Check spam/promotions folder
- Verify app password (16 chars, niet je gewone wachtwoord)
- Zorg dat "Less secure app access" niet meer nodig is (dit zijn App Passwords)

**Ander tijdstip nodig?**
- Edit `.github/workflows/daily-stock-news.yml` en change de `cron` waarde

## 📝 Aanpassingen

Wil je aandelen toevoegen/verwijderen?
- Edit `daily_stock_news.py` → `PORTFOLIO` dict

Wil je filters strakker maken?
- Edit `fetch_portfolio_news()` → aanpassen van relevante keywords

---

Klaar! 🎉 Je krijgt voortaan elke dag beursnieuws.
