# 🎰 botyaracasino

> **A modern, neon-styled fake casino web app built with Flask** 🚀
> Full-featured casino simulator with 14 mini-games, admin panel, real-time chat, and achievements system!

---

## ✨ Features

### 🎮 **14 Mini-Games**
- 🎰 **Slots** — Spin the reels (up to x100)
- 🎲 **Dice** — Guess the outcome (up to x8)
- 🎡 **Roulette** — Red or black (up to x40)
- 🪙 **Coinflip** — Heads or tails (x2.0)
- 📈 **Crash** — Cash out before crash (up to x200)
- 🃏 **Blackjack** — Beat the dealer (x3)
- 💣 **Mines** — Avoid the bombs (up to ∞)
- 🎱 **Hi-Lo** — Higher or lower (∞)
- 🏇 **Horse Racing** — Pick your horse (up to x9)
- 🎯 **Wheel of Fortune** — Spin to win (up to x50)
- 🗼 **Tower** — Climb the floors (up to ∞)
- 🎯 **Limbo** — Set your target (up to x1000)
- ⚽ **Penalty** — Score past the keeper (up to x3.5)
- 🎱 **Keno** — Pick your numbers (up to x5000)

### 🛡️ **Admin Panel**
- 👑 **Multi-level access** (User → Admin → Super Admin → Owner)
- 💰 **Manage user balances** (add/set/remove)
- 🚫 **Ban/unban/kick users**
- 📊 **Real-time server stats** (users, games, balances)
- 🎮 **Enable/disable games**
- 📢 **Broadcast messages** to all users
- 📜 **Full admin action logs**
- 🔧 **Server settings** (maintenance mode, deposit limits, bet limits)
- 📦 **Database export**

### 💬 **Real-Time Chat**
- 💬 Live chat for all players
- 🎉 System notifications for big wins
- 🔄 Auto-refresh every 3 seconds
- 📱 Mobile-friendly chat panel

### 🏆 **Player Features**
- 📊 **Detailed statistics** (balance, profit, ROI, win rate)
- 🏅 **Achievement system** (17 unlockable achievements)
- 📈 **Balance history charts**
- 📜 **Game history** (last 30 games)
- 🎯 **Per-game stats**
- 🏆 **Leaderboard** with live updates

### 🎨 **Modern UI**
- 🌌 **Neon cyberpunk theme**
- ✨ **Smooth animations** and transitions
- 📱 **Fully responsive** design
- 🎭 **Glassmorphism effects**
- 💫 **Win animations** and visual feedback

### 🔐 **Security & Sessions**
- 🔑 **Secure authentication** (password hashing)
- 🍪 **Persistent sessions** (7 days)
- 🚪 **Auto-login after registration**
- 👥 **Online user tracking**
- 🔒 **Ban system** with reasons
- 🛡️ **Admin action logging**

---

## 🚀 Quick Start

### 📋 Prerequisites
- Python 3.8+ 🐍
- pip (Python package manager)

### ⚡ Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/botyaracasino.git
cd botyaracasino
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Open in browser** 🌐
```
http://127.0.0.1:14651
```

---

## 📁 Project Structure

```
botyaracasino/
├── app.py              # 🎯 Main Flask application + all game logic
├── admin.py            # 🛡️ Admin panel routes and logic
├── models.py           # 💾 Database models and functions
├── requirements.txt    # 📦 Python dependencies
├── casino.db           # 🗄️ SQLite database (auto-created)
├── .secret_key         # 🔑 Flask session secret (auto-generated)
└── templates/          # 🎨 HTML templates
    ├── base.html           # Base template with navbar & chat
    ├── dashboard.html      # Main dashboard with game grid
    ├── login.html          # Login page
    ├── register.html       # Registration page (auto-login)
    ├── profile.html        # User profile & stats
    ├── leaderboard.html    # Global leaderboard
    ├── admin.html          # Admin dashboard
    ├── admin_logs.html     # Admin action logs
    ├── admin_settings.html # Server settings
    ├── admin_user.html     # User management page
    └── game_*.html         # 14 game templates
```

---

## 🎮 Game Details

### Win Rates (Generous!) 🎁
All games have **boosted win rates** with minimal house edge (0.5-1.5%):

| Game | House Edge | Max Multiplier |
|------|-----------|---------------|
| Slots | ~1% | x100 |
| Dice | ~1% | x8 |
| Roulette | ~1% | x40 |
| Coinflip | 0% | x2 |
| Crash | ~1.5% | x200 |
| Blackjack | ~1% | x3 |
| Mines | ~1% | ∞ |
| Hi-Lo | ~1% | ∞ |
| Races | ~1% | x9 |
| Wheel | ~1% | x50 |
| Tower | ~1% | ∞ |
| Limbo | ~0.5% | x1000 |
| Penalty | ~1% | x3.5 |
| Keno | ~1% | x5000 |

---

## 🛡️ Admin Access Levels

### 👤 **User** (Level 0)
- Play games
- View leaderboard & profile
- Use chat

### 👮 **Admin** (Level 1)
- All user permissions
- Kick users
- Manage balances
- Send broadcasts
- View admin panel

### 🦸 **Super Admin** (Level 2)
- All admin permissions
- Ban/unban users
- Reset user stats
- Change server settings
- View admin logs

### 👑 **Owner** (Level 3)
- **Full access to everything**
- Delete users
- Grant/revoke admin rights
- Export database
- Automatically granted to:
  - Username: `dimasbotyara`
  - Connections from `localhost` (127.0.0.1)

---

## 🎨 Customization

### 🌈 Changing Colors
Edit `templates/base.html` CSS variables:
```css
/* Neon colors */
--violet: #7c3aed;
--emerald: #10b981;
--amber: #f59e0b;
```

### 🎰 Adjusting Win Rates
Edit game logic in `app.py`:
```python
# Example: Slots (line ~XXX)
weights = [22, 20, 18, 16, 13, 8, 5]  # Adjust symbol weights
mults = {'🍒':5,'🍋':7,...}           # Adjust multipliers
```

### ⚙️ Server Settings
Change via **Admin Panel → Settings** or edit `models.py`:
```python
SERVER_SETTINGS = {
    'deposit_limit': 150000,
    'min_bet': 1,
    'max_bet': 0,  # 0 = unlimited
    'welcome_bonus': 0,
    ...
}
```

---

## 📊 Database Schema

### Tables
- **users** — User accounts, balances, stats
- **game_history** — All game records
- **transactions** — Deposits & game results
- **user_achievements** — Unlocked achievements
- **admin_logs** — Admin actions log
- **server_settings** — Dynamic settings
- **broadcast_messages** — Active broadcasts
- **chat_messages** — Chat history (last 200)

---

## 🎯 Achievement List

| Icon | Name | Description |
|------|------|-------------|
| 🎮 | First Game | Play your first game |
| 🏆 | First Win | Win your first game |
| 💎 | High Roller | Bet 10,000₽ in one game |
| 🐋 | Whale | Bet 50,000₽ in one game |
| 🔥 | Win Streak 3 | Win 3 games in a row |
| 🔥🔥 | On Fire! | Win 5 games in a row |
| ☄️ | Unstoppable | Win 10 games in a row |
| 🎲 | Regular | Play 10 games |
| ⭐ | Veteran | Play 50 games |
| 👑 | Legend | Play 100 games |
| 💰 | Big Win | Win 5,000₽ in one game |
| 🤑 | Jackpot! | Win 50,000₽ in one game |
| 💎👑 | MEGA JACKPOT | Win 100,000₽ in one game |
| 😢 | Bankrupt | Reach 0₽ balance |
| 🏦 | Millionaire | Reach 1,000,000₽ balance |
| 🎯 | Jack of All Trades | Play all 14 games |
| 📈 | Profit King | Total profit +100,000₽ |
| 🏧 | Investor | Deposit 10 times |

---

## 🖥️ Console Features

Beautiful **colored console logs** with real-time tracking:

```
🎰 ══════════════════════════════════════════════════════
   b o t y a r a c a s i n o
   by dimasbotyara
══════════════════════════════════════════════════════ 🎰

   📍 Локально:  http://127.0.0.1:14651
   📍 LAN:       http://192.168.1.100:14651
   📍 Админка:   http://127.0.0.1:14651/admin
   Запущен: 2025-01-15 14:30:00
   ⏳ Ожидание подключений...
────────────────────────────────────────────────────────

  [14:30:15] 🟢 CONNECT    192.168.1.50 (Chrome)
  [14:30:18] 🔑 LOGIN      player123 (192.168.1.50) → Баланс: 5,000₽
             👥 Онлайн: 1 | player123
  [14:30:25] 💰 DEPOSIT    player123 +10,000₽ → Баланс: 15,000₽
  [14:30:30] 🚪 ENTER      player123 → 🎰 Слоты
  [14:30:35] 🎰 GAME       player123 → Слоты | Ставка: 500₽ | WIN +2,500₽ | Баланс: 17,500₽
```

---

## 🔧 Configuration

### Port & Host
Edit `app.py` (bottom):
```python
if __name__ == '__main__':
    HOST, PORT = '0.0.0.0', 14651  # Change port here
    app.run(host=HOST, port=PORT, debug=False)
```

### Session Duration
Edit `app.py`:
```python
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days
```

### Developer Tag
Change in `app.py` and `models.py`:
```python
DEVELOPER = "dimasbotyara"  # Change to your name
OWNER_USERNAME = 'dimasbotyara'  # Owner account
```

---

## 📱 Browser Compatibility

✅ Chrome/Edge (recommended)
✅ Firefox
✅ Safari
✅ Mobile browsers

---

## 🐛 Known Issues

- ⚠️ Chat doesn't persist after server restart (by design)
- ⚠️ No HTTPS (use reverse proxy for production)
- ⚠️ No rate limiting (add for production)

---

## 🚧 Future Plans

- [ ] 🎨 Theme switcher (neon/classic/dark)
- [ ] 🌐 Multi-language support
- [ ] 📊 Advanced analytics dashboard
- [ ] 🎁 Daily bonuses & quests
- [ ] 🏪 Shop system
- [ ] 🤝 PvP games
- [ ] 📲 Progressive Web App (PWA)
- [ ] 🔔 Push notifications

---

## 📄 License

**MIT License** — Free to use, modify, and distribute!

```
MIT License

Copyright (c) 2026 dimasbotyara

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 👨‍💻 Author

**dimasbotyara** 🚀  
- Created with ❤️ and ☕
- Built using Flask + SQLite + Tailwind CSS

---

## 🙏 Acknowledgments

- 🎨 **Tailwind CSS** — For the amazing utility-first framework
- 🐍 **Flask** — For the lightweight yet powerful web framework
- 🎰 **Casino game math** — Inspired by real casino mechanics

---

## 📞 Support

Found a bug? Have a suggestion? 💡

1. Open an issue on GitHub
2. Contact via Telegram: `@dimasbotyara`
3. Or just enjoy the casino! 🎰

---

<div align="center">

### 🎰 **Happy Gaming!** 🎰

Made with 💜 by **dimasbotyara**

⭐ **Star this repo** if you like it! ⭐

</div>
