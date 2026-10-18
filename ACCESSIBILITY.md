# Accessibility Statement for NixManager Pro

NixManager Pro is committed to ensuring digital accessibility for people of all abilities. We are continually improving the user experience for everyone and applying relevant accessibility standards across our desktop interface.

---

## Conformance Status

We aim to adhere to the [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/TR/WCAG21/) Level AA standards as applicable to desktop Graphical User Interfaces (GUIs).

---

## Accessibility Features & Ergonomics

### 1. Visual Ergonomics & Contrast
* **Dual Theme Support**: Full high-contrast Dark and Light modes tailored to prevent eye strain and maintain WCAG AA minimum contrast ratio (4.5:1) for body text and interactive controls.
* **Modern Typography**: High-legibility font hierarchies without condensed or decorative body typography.
* **Clear State Indicators**: Interactive elements feature distinct hover and active color changes, accompanied by text labels rather than color alone (e.g. status badges with icons and labels).

### 2. Keyboard Navigation
* Navigation between views (Discover, Installed, Updates, Generations, Channels, Console) is accessible via standardized keyboard focus and tab navigation.
* Tables support arrow key navigation (`Up` / `Down`) and standard selection toggles (`Return` / `Space`).
* Standard shortcut bindings:
  * `Ctrl+Q` / `Esc`: Close active modal dialog or dismiss context menu.
  * `Ctrl+F`: Focus search and filter input fields.
  * `Return`: Open App Details dialog for selected package.

### 3. Audio & Motion
* NixManager Pro does not use autoplaying audio or disruptive strobe flashing animations.
* Progress bars provide smooth, deterministic percentage values and status messages.

---

## Supported Environments

NixManager Pro is tested and validated on:
* **Operating Systems**: Linux distributions running X11 or Wayland display servers (Ubuntu, NixOS, Arch Linux, Fedora, Debian).
* **Desktop Environments**: GNOME 42+, KDE Plasma 5/6, XFCE, and tiling window managers.
* **Assistive Technologies**: Linux screen readers (such as Orca) with AT-SPI2 compatibility where supported by the underlying Tk/Tcl subsystem.

---

## Known Limitations

While we strive for comprehensive accessibility, some known limitations are being actively addressed:
1. **Screen Reader Integration**: Because CustomTkinter builds upon Tkinter/X11 canvas elements, some custom drawn widgets may not expose full semantic AT-SPI2 accessibility trees compared to native GTK4/Qt6 widgets. We are actively refining widget focus descriptors to improve screen reader feedback.
2. **Dynamic DPI Scaling**: While the application respects system scaling on standard displays, multi-monitor setups with mismatched fractional scaling may require manual geometry adjustment.

---

## Feedback & Reporting Accessibility Barriers

We welcome your feedback on the accessibility of NixManager Pro. If you encounter accessibility barriers, please let us know:

* **GitHub Issue**: Open an issue labeled with [`accessibility`](https://github.com/MikeeeDeV/NixManagerPro/labels/accessibility).
* **Email**: [alsghyrblhh@gmail.com](mailto:alsghyrblhh@gmail.com) with the subject `[ACCESSIBILITY] NixManager Pro Barrier`.

When reporting a barrier, please include:
* The screen, modal, or action where the issue occurred.
* The assistive technology or environment you are using (e.g. screen reader version, theme, scaling factor).
* A description of what happened and what you expected.

We aim to respond to accessibility reports within **3 business days**.
