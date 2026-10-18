# Getting Support for NixManager Pro

Welcome! If you need help with **NixManager Pro**, here is where and how to find assistance.

---

## 🔍 Self-Service Diagnostics

Before reaching out, check whether our built-in diagnostics can resolve your issue:

1. **Live Console Stream**:
   * Open the **Live Console Stream** tab in NixManager Pro.
   * Review real-time subshell outputs and Nix error messages.
2. **Nix Daemon Health Check**:
   * Verify your daemon is running:
     ```bash
     systemctl status nix-daemon
     ```
   * Verify your user profile environment:
     ```bash
     nix-env -q
     ```
3. **Application Log Inspection**:
   * NixManager Pro logs application events to standard error. You can run the application directly from terminal to inspect full debug logs:
     ```bash
     nixmanager
     # or
     python3 main.py
     ```

---

## 💬 Community Channels

* **GitHub Discussions**:
  * [Ask a Question / Get Help](https://github.com/MikeeeDeV/NixManagerPro/discussions)
  * Share customized software stack templates or Nix shell environments.
* **Bug Reports**:
  * If you found a defect in NixManager Pro, please [Open an Issue](https://github.com/MikeeeDeV/NixManagerPro/issues/new/choose) using our structured form.
* **Feature Requests**:
  * Suggest UI improvements or package manager backend ideas on [GitHub Issues](https://github.com/MikeeeDeV/NixManagerPro/issues/new?template=feature_request.yml).

---

## ❓ Frequently Asked Questions (FAQ)

### Q: Why aren't some packages appearing in my Installed Packages tab?
**A:** NixManager Pro automatically scans your active user profile (`~/.nix-profile/bin`) as well as active Snap and Flatpak applications. If a Nix package was installed via a temporary `nix-shell`, it will not be listed in your permanent profile by design.

### Q: What is the difference between "Uninstall" and "Deep Purge"?
**A:**
* **Uninstall (مسح عادي)**: Unlinks the package from your profile without touching personal config directories or cache.
* **Deep Purge (مسح نهائي)**: Completely unlinks the package and removes application caches, user configurations from `~/.config` and `~/.cache`, and triggers Nix store garbage collection.

### Q: How do I backup my applications when moving to a new computer?
**A:**
1. In the **Installed Packages** tab, click **Export Stack**.
2. Save the `.json` or `shell.nix` file.
3. On your new computer, open NixManager Pro and click **Restore Stack** to install all packages in a single batch!

---

## 🌐 Upstream Nix Resources

* **Nix Official Documentation**: [https://nixos.org/learn](https://nixos.org/learn)
* **Nixpkgs Search Engine**: [https://search.nixos.org](https://search.nixos.org)
* **NixOS Discourse Community**: [https://discourse.nixos.org](https://discourse.nixos.org)
