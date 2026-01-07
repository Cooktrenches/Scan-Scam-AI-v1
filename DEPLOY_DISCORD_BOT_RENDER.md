# Déployer le Bot Discord sur Render (24/7)

Ce guide explique comment déployer le bot Discord sur Render pour qu'il soit en ligne 24/7.

## Prérequis

- Compte Render (gratuit): https://render.com
- Ton repository GitHub doit être public ou connecté à Render
- Token Discord Bot configuré

## Étapes de Déploiement

### 1. Créer un nouveau Web Service sur Render

1. Va sur https://dashboard.render.com/
2. Clique sur **"New +"** → **"Web Service"**
3. Connecte ton repository GitHub: `TheMasterPump/Scan-Beta-V1`
4. Configure le service:

**Settings:**
- **Name**: `scam-ai-discord-bot`
- **Region**: `Frankfurt (EU Central)` (ou le plus proche de tes utilisateurs)
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python discord_bot.py`
- **Instance Type**: `Free` (pour commencer)

### 2. Ajouter les Variables d'Environnement

Dans la section **Environment Variables**, ajoute:

| Key | Value |
|-----|-------|
| `DISCORD_BOT_TOKEN` | `YOUR_DISCORD_BOT_TOKEN_HERE` |
| `API_URL` | `https://scan-beta-v1.onrender.com` (or your custom domain) |

**IMPORTANT: ⚠️ NEVER PUT REAL TOKENS IN CODE OR DOCUMENTATION!**
- Get your token from Discord Developer Portal
- Add it ONLY in Render Environment Variables
- NEVER commit real tokens to GitHub!

### 3. Déployer

1. Clique sur **"Create Web Service"**
2. Render va automatiquement:
   - Clone ton repo
   - Installer les dépendances
   - Démarrer le bot
3. Attends 2-3 minutes pour le déploiement

### 4. Vérifier que ça fonctionne

Une fois déployé, tu verras dans les logs:
```
==================================================
   SCAM AI DISCORD BOT - ONLINE
==================================================
Bot: SCAM AI
Servers: X
Synced 3 slash commands
```

### 5. Tester le Bot

Dans Discord, tape:
```
/scan BDuWXaAcs88guisXQWvdiDGDVNn7eR7Wxw3Q5KLgpump
```

Le bot devrait répondre avec l'analyse complète!

---

## Avec un Nom de Domaine Personnalisé

### Quand tu achèteras ton domaine (ex: `scamai.fun`)

1. **Dans Render** (ton app web):
   - Va dans Settings → Custom Domain
   - Ajoute `scamai.fun` et `www.scamai.fun`
   - Copie les DNS records

2. **Chez ton registrar** (Namecheap, Google Domains):
   - Ajoute les DNS records de Render
   - Attends 24-48h pour la propagation

3. **Met à jour l'API_URL**:
   - Sur Render, dans les Environment Variables du bot Discord
   - Change `API_URL` de `https://scan-beta-v1.onrender.com`
   - Vers `https://scamai.fun` (ou ton domaine)

4. **Redéploie le bot** pour appliquer les changements

---

## Avantages du Déploiement sur Render

✅ Bot en ligne **24/7**
✅ Pas besoin de laisser ton PC allumé
✅ Logs accessibles en temps réel
✅ Auto-redémarrage en cas d'erreur
✅ Mises à jour automatiques depuis GitHub
✅ Gratuit pour commencer (plan free)

---

## Conseils pour les Noms de Domaine

**Suggestions:**
- `scamai.fun` - Court et mémorable ⭐ (Recommandé)
- `scamai.fun` - Moderne
- `solanascam.ai` - Descriptif
- `rugscanner.io` - Clair

**Où acheter:**
- **Namecheap**: ~$12/an, facile à utiliser
- **Google Domains**: ~$12/an, intégration Google
- **Cloudflare**: ~$10/an, CDN gratuit inclus

**Extensions recommandées:**
- `.io` - Tech/Startups (très populaire)
- `.ai` - IA/Machine Learning
- `.app` - Applications web
- `.com` - Classique (plus cher)

---

## Déployer le Bot Telegram (Optionnel)

Même processus:
1. Créer un nouveau Web Service sur Render
2. Name: `scam-ai-telegram-bot`
3. Start Command: `python telegram_bot.py`
4. Ajouter les variables: `TELEGRAM_BOT_TOKEN` et `API_URL`

---

## Monitoring

**Render Dashboard** te permet de:
- Voir les logs en temps réel
- Monitorer les performances
- Redémarrer le bot si besoin
- Voir les métriques (CPU, RAM)

---

## Support

Si tu as des problèmes:
1. Vérifie les logs sur Render Dashboard
2. Assure-toi que ton app web est en ligne
3. Vérifie que les tokens sont corrects dans les env variables

©SCAM AI 2025
