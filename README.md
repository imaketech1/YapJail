# YapJail Discord Bot 🔒

A Discord bot that puts users in "yap jail" - preventing them from speaking in voice channels & chatting while allowing camera, screen sharing!

---

## ✨ Features

- 🔇 **Mute in Voice** - Server mute + channel permissions
- 💬 **Block Chat** - No messages in any text channel (including voice chat)
- 🎥 **Camera & Screen Share** - Still works while jailed
- ⏱️ **Auto-Release** - Automatically freed after timer expires
- 👤 **Self-Jail** - Users can jail themselves
- 🔓 **Self-Free** - Free yourself via DM or server
- 👑 **Admin Controls** - Force jail with no self-free option

---

## 📝 Commands

| Command | Description |
|---------|-------------|
| `/yapjail` | Put yourself in yap jail for a specified time. |
| `/yapfree` | Free yourself. Works in my DMs! |
| `/yapjail_status` | Check your current jail status. |
| `/yapjail_admin` | Jail another user. Set `forced: True` if forced timeout user cant free themselves. |
| `/yapfree_admin` | Admin: Free any user from jail. |
| `/yapjail_list` | Admin: List all currently jailed users. |

### Command Options

```
/yapjail <time> [reason]
  time    - Minutes to stay jailed (1-1440)
  reason  - Why you're going to jail

/yapjail_admin <user> <time> [reason] [forced]
  user    - @mention the user
  time    - Minutes to stay jailed
  reason  - Why they're being jailed
  forced  - true/false (default: false)
```

---

## 📄 License

MIT License - Free for personal and commercial use.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## ⭐ Show Your Support

If this bot helped you, give it a star on GitHub!

---
## 🔗 Links

- **Invite Bot**: [Click here to invite](https://discord.com/oauth2/authorize?client_id=1540997512394178570&permissions=8&scope=bot+applications.commands)

Made with ❤️ for all the yappers out there!