"""
core.catalog
~~~~~~~~~~~~

Extensive curated catalog of top Nix packages for zero-latency discovery and installation.
Provides rich WingetUI-style metadata: categories, descriptions, homepages, licenses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CatalogItem:
    """Represents a curated software package in the Nix ecosystem."""

    name: str
    attr: str
    category: str
    description: str
    homepage: str = ""
    license: str = "Open Source"


CURATED_PACKAGES: List[CatalogItem] = [
    # ─── Developer Tools & Editors ───────────────────────────────────────────
    CatalogItem("VS Code (VSCodium)", "nixpkgs.vscodium", "Development", "Community-driven, freely-licensed binary distribution of VS Code", "https://vscodium.com/", "MIT"),
    CatalogItem("Neovim", "nixpkgs.neovim", "Development", "Vim-fork focused on extensibility and modern Lua plugins", "https://neovim.io/", "Apache-2.0"),
    CatalogItem("Emacs", "nixpkgs.emacs", "Development", "Extensible, customizable, self-documenting real-time display editor", "https://www.gnu.org/software/emacs/", "GPL-3.0"),
    CatalogItem("Helix Editor", "nixpkgs.helix", "Development", "Post-modern modal text editor written in Rust with Tree-sitter", "https://helix-editor.com/", "MPL-2.0"),
    CatalogItem("Git", "nixpkgs.git", "Development", "Fast, scalable, distributed revision control system", "https://git-scm.com/", "GPL-2.0"),
    CatalogItem("GitHub CLI", "nixpkgs.gh", "Development", "Official command-line tool for GitHub PRs, issues and repos", "https://cli.github.com/", "MIT"),
    CatalogItem("Lazygit", "nixpkgs.lazygit", "Development", "Simple terminal UI for git commands written in Go", "https://github.com/jesseduffield/lazygit", "MIT"),
    CatalogItem("Ripgrep", "nixpkgs.ripgrep", "Development", "Ultra-fast line-oriented search tool combining grep with gitignore", "https://github.com/BurntSushi/ripgrep", "MIT"),
    CatalogItem("Fzf", "nixpkgs.fzf", "Development", "Blazingly fast command-line fuzzy finder for files and history", "https://github.com/junegunn/fzf", "MIT"),
    CatalogItem("Tmux", "nixpkgs.tmux", "Development", "Terminal multiplexer with workspaces, panes and session detach", "https://github.com/tmux/tmux", "ISC"),
    CatalogItem("JQ", "nixpkgs.jq", "Development", "Lightweight, powerful command-line JSON processor and filter", "https://jqlang.github.io/jq/", "MIT"),
    CatalogItem("YQ", "nixpkgs.yq-go", "Development", "Portable command-line YAML, JSON, XML, CSV and properties processor", "https://github.com/mikefarah/yq", "MIT"),
    CatalogItem("Bat", "nixpkgs.bat", "Development", "Cat clone with syntax highlighting and automatic paging", "https://github.com/sharkdp/bat", "MIT / Apache-2.0"),
    CatalogItem("Eza", "nixpkgs.eza", "Development", "Modern, maintained replacement for ls with colors and git status", "https://github.com/eza-community/eza", "EUPL-1.2"),
    CatalogItem("Zoxide", "nixpkgs.zoxide", "Development", "A smarter cd command that remembers your frequently visited folders", "https://github.com/ajeetdsouza/zoxide", "MIT"),
    CatalogItem("Direnv", "nixpkgs.direnv", "Development", "Environment switcher that loads and unloads shell variables per folder", "https://direnv.net/", "MIT"),
    CatalogItem("Meld", "nixpkgs.meld", "Development", "Visual visual diff and merge tool targeted at developers", "https://meldmerge.org/", "GPL-2.0"),
    CatalogItem("DBeaver", "nixpkgs.dbeaver-bin", "Development", "Universal Database Manager and SQL Client", "https://dbeaver.io/", "Apache-2.0"),

    # ─── DevOps, Cloud & Containers ──────────────────────────────────────────
    CatalogItem("Docker CLI", "nixpkgs.docker", "DevOps & Cloud", "Pack, ship and run any application as a lightweight container", "https://www.docker.com/", "Apache-2.0"),
    CatalogItem("Docker Compose", "nixpkgs.docker-compose", "DevOps & Cloud", "Define and run multi-container Docker applications", "https://docs.docker.com/compose/", "Apache-2.0"),
    CatalogItem("Podman", "nixpkgs.podman", "DevOps & Cloud", "Daemonless container engine for developing, managing OCI containers", "https://podman.io/", "Apache-2.0"),
    CatalogItem("Kubernetes CLI (kubectl)", "nixpkgs.kubectl", "DevOps & Cloud", "Production-Grade Container Scheduling and Management CLI", "https://kubernetes.io/", "Apache-2.0"),
    CatalogItem("Helm", "nixpkgs.kubernetes-helm", "DevOps & Cloud", "The Kubernetes package manager", "https://helm.sh/", "Apache-2.0"),
    CatalogItem("Terraform", "nixpkgs.terraform", "DevOps & Cloud", "Infrastructure as Code tool for building, changing cloud resources", "https://www.terraform.io/", "BSL-1.1"),
    CatalogItem("Ansible", "nixpkgs.ansible", "DevOps & Cloud", "Radically simple IT automation system for configuration management", "https://www.ansible.com/", "GPL-3.0"),

    # ─── Web Browsers & Internet ─────────────────────────────────────────────
    CatalogItem("Firefox", "nixpkgs.firefox", "Internet & Web", "Free and open-source web browser developed by Mozilla", "https://www.mozilla.org/firefox/", "MPL-2.0"),
    CatalogItem("Chromium", "nixpkgs.chromium", "Internet & Web", "Open-source browser project that powers Google Chrome", "https://www.chromium.org/", "BSD-3-Clause"),
    CatalogItem("Brave Browser", "nixpkgs.brave", "Internet & Web", "Privacy-oriented browser with built-in ad and tracker blocking", "https://brave.com/", "MPL-2.0"),
    CatalogItem("Tor Browser", "nixpkgs.tor-browser", "Internet & Web", "Protect your privacy and defend yourself against network surveillance", "https://www.torproject.org/", "BSD-3-Clause"),
    CatalogItem("Thunderbird", "nixpkgs.thunderbird", "Internet & Web", "Full-featured email, newsgroup and calendar desktop client", "https://www.thunderbird.net/", "MPL-2.0"),
    CatalogItem("FileZilla", "nixpkgs.filezilla", "Internet & Web", "Graphical FTP, FTPS and SFTP client", "https://filezilla-project.org/", "GPL-2.0"),
    CatalogItem("Curl", "nixpkgs.curl", "Internet & Web", "Universal command line tool and library for transferring URLs", "https://curl.se/", "curl"),
    CatalogItem("Wget", "nixpkgs.wget", "Internet & Web", "Tool for non-interactive download of files from HTTP and FTP", "https://www.gnu.org/software/wget/", "GPL-3.0"),
    CatalogItem("HTTPie", "nixpkgs.httpie", "Internet & Web", "Modern, user-friendly command-line HTTP client for API debugging", "https://httpie.io/", "BSD-3-Clause"),
    CatalogItem("Nmap", "nixpkgs.nmap", "Internet & Web", "Free and open source utility for network discovery and security auditing", "https://nmap.org/", "NPSL"),
    CatalogItem("Wireshark", "nixpkgs.wireshark", "Internet & Web", "World's foremost and widely-used network protocol analyzer", "https://www.wireshark.org/", "GPL-2.0"),

    # ─── System Monitors & Shells ────────────────────────────────────────────
    CatalogItem("Btop", "nixpkgs.btop", "System & Shell", "Gorgeous resource monitor showing CPU, memory, disks and network", "https://github.com/aristocratos/btop", "Apache-2.0"),
    CatalogItem("Htop", "nixpkgs.htop", "System & Shell", "Interactive process viewer and system activity monitor", "https://htop.dev/", "GPL-2.0"),
    CatalogItem("Fastfetch", "nixpkgs.fastfetch", "System & Shell", "Lightning-fast system information fetch tool written in C", "https://github.com/fastfetch-cli/fastfetch", "MIT"),
    CatalogItem("Neofetch", "nixpkgs.neofetch", "System & Shell", "Fast, highly customizable system info script", "https://github.com/dylanaraps/neofetch", "MIT"),
    CatalogItem("Zsh", "nixpkgs.zsh", "System & Shell", "Powerful UNIX shell designed for interactive command-line use", "https://www.zsh.org/", "MIT-like"),
    CatalogItem("Fish", "nixpkgs.fish", "System & Shell", "Smart and user-friendly command line shell with autosuggestions", "https://fishshell.com/", "GPL-2.0"),
    CatalogItem("Starship", "nixpkgs.starship", "System & Shell", "Blazing-fast, minimal, customizable cross-shell prompt", "https://starship.rs/", "ISC"),
    CatalogItem("Alacritty", "nixpkgs.alacritty", "System & Shell", "GPU-accelerated, fast terminal emulator written in Rust", "https://alacritty.org/", "Apache-2.0"),
    CatalogItem("Kitty", "nixpkgs.kitty", "System & Shell", "Modern, hackable, GPU-based terminal emulator with tabs and splits", "https://sw.kovidgoyal.net/kitty/", "GPL-3.0"),
    CatalogItem("WezTerm", "nixpkgs.wezterm", "System & Shell", "GPU-accelerated cross-platform terminal emulator and multiplexer", "https://wezfurlong.org/wezterm/", "MIT"),
    CatalogItem("Ranger", "nixpkgs.ranger", "System & Shell", "VIM-inspired file manager with a terminal-based curses interface", "https://ranger.github.io/", "GPL-3.0"),
    CatalogItem("Yazi", "nixpkgs.yazi", "System & Shell", "Blazing-fast terminal file manager written in Rust with async I/O", "https://yazi-rs.github.io/", "MIT"),

    # ─── Programming Runtimes & Compilers ────────────────────────────────────
    CatalogItem("Python 3", "nixpkgs.python3", "Runtimes & Languages", "High-level, interpreted scripting and application language", "https://www.python.org/", "PSF"),
    CatalogItem("Node.js (LTS)", "nixpkgs.nodejs", "Runtimes & Languages", "JavaScript runtime built on Chrome's V8 engine", "https://nodejs.org/", "MIT"),
    CatalogItem("Bun", "nixpkgs.bun", "Runtimes & Languages", "Incredibly fast JavaScript, TypeScript runtime, bundler and test runner", "https://bun.sh/", "MIT"),
    CatalogItem("Deno", "nixpkgs.deno", "Runtimes & Languages", "Secure runtime for JavaScript and TypeScript with built-in tooling", "https://deno.land/", "MIT"),
    CatalogItem("Rust (Cargo & Rustc)", "nixpkgs.rustc", "Runtimes & Languages", "Safe, concurrent, practical systems programming language", "https://www.rust-lang.org/", "MIT / Apache-2.0"),
    CatalogItem("Go", "nixpkgs.go", "Runtimes & Languages", "Open source programming language to build simple, fast, reliable software", "https://go.dev/", "BSD-3-Clause"),
    CatalogItem("GCC", "nixpkgs.gcc", "Runtimes & Languages", "The GNU Compiler Collection supporting C, C++, Fortran and more", "https://gcc.gnu.org/", "GPL-3.0"),
    CatalogItem("Clang / LLVM", "nixpkgs.clang", "Runtimes & Languages", "C language family frontend for LLVM compiler framework", "https://clang.llvm.org/", "Apache-2.0"),
    CatalogItem("OpenJDK (Java)", "nixpkgs.jdk", "Runtimes & Languages", "Open-source implementation of the Java Platform, Standard Edition", "https://openjdk.org/", "GPL-2.0"),
    CatalogItem("Ruby", "nixpkgs.ruby", "Runtimes & Languages", "Dynamic programming language with a focus on simplicity and productivity", "https://www.ruby-lang.org/", "Ruby License"),
    CatalogItem("PHP", "nixpkgs.php", "Runtimes & Languages", "Popular general-purpose scripting language suited for web development", "https://www.php.net/", "PHP-3.01"),

    # ─── Media, Audio & Graphics ─────────────────────────────────────────────
    CatalogItem("VLC Media Player", "nixpkgs.vlc", "Media & Audio", "Free and open source multimedia player for almost any codec", "https://www.videolan.org/vlc/", "GPL-2.0"),
    CatalogItem("mpv", "nixpkgs.mpv", "Media & Audio", "Free, open source, and cross-platform media player for the command line", "https://mpv.io/", "GPL-2.0+"),
    CatalogItem("FFmpeg", "nixpkgs.ffmpeg", "Media & Audio", "Complete cross-platform solution to record, convert and stream media", "https://ffmpeg.org/", "GPL-2.1+"),
    CatalogItem("GIMP", "nixpkgs.gimp", "Media & Audio", "GNU Image Manipulation Program for photo retouching and graphic design", "https://www.gimp.org/", "GPL-3.0"),
    CatalogItem("Inkscape", "nixpkgs.inkscape", "Media & Audio", "Professional vector graphics editor for illustration and design", "https://inkscape.org/", "GPL-2.0"),
    CatalogItem("OBS Studio", "nixpkgs.obs-studio", "Media & Audio", "Free and open source software for video recording and live streaming", "https://obsproject.com/", "GPL-2.0"),
    CatalogItem("Blender", "nixpkgs.blender", "Media & Audio", "3D creation suite supporting modeling, rigging, animation and simulation", "https://www.blender.org/", "GPL-2.0+"),
    CatalogItem("Audacity", "nixpkgs.audacity", "Media & Audio", "Easy-to-use, multi-track audio editor and recorder for Linux", "https://www.audacityteam.org/", "GPL-2.0"),
    CatalogItem("Kdenlive", "nixpkgs.kdenlive", "Media & Audio", "Powerful non-linear video editing software by KDE", "https://kdenlive.org/", "GPL-3.0"),
    CatalogItem("ImageMagick", "nixpkgs.imagemagick", "Media & Audio", "Command line suite to create, edit, compose and convert bitmap images", "https://imagemagick.org/", "Apache-2.0"),

    # ─── Utilities, Archiving & Security ─────────────────────────────────────
    CatalogItem("7-Zip (p7zip)", "nixpkgs.p7zip", "Utilities", "High compression ratio file archiver for 7z, zip, and tar formats", "https://www.7-zip.org/", "LGPL-2.1"),
    CatalogItem("Unrar", "nixpkgs.unrar", "Utilities", "Tool to unpack and extract RAR archives", "https://www.rarlab.com/", "Freeware"),
    CatalogItem("GnuPG (GPG)", "nixpkgs.gnupg", "Utilities", "Complete, free implementation of OpenPGP for encryption and signing", "https://gnupg.org/", "GPL-3.0"),
    CatalogItem("Age", "nixpkgs.age", "Utilities", "Simple, modern and secure encryption tool with small explicit keys", "https://github.com/FiloSottile/age", "BSD-3-Clause"),
    CatalogItem("Rclone", "nixpkgs.rclone", "Utilities", "Command-line program to sync files and directories to cloud storage", "https://rclone.org/", "MIT"),
    CatalogItem("Tree", "nixpkgs.tree", "Utilities", "Recursive directory listing command producing a depth-indented tree", "http://mama.indstate.edu/users/ice/tree/", "GPL-2.0"),
    CatalogItem("Tldr", "nixpkgs.tldr", "Utilities", "Simplified and community-driven man pages with practical examples", "https://tldr.sh/", "MIT"),
    CatalogItem("GNU Hello", "nixpkgs.hello", "Utilities", "Official GNU hello testing package for verifying Nix environments", "https://www.gnu.org/software/hello/", "GPL-3.0"),
]


CATEGORY_ALIASES = {
    "developer tools": "Development",
    "development": "Development",
    "dev": "Development",
    "devops": "DevOps & Cloud",
    "cloud": "DevOps & Cloud",
    "networking": "Internet & Web",
    "internet": "Internet & Web",
    "web": "Internet & Web",
    "system & shell": "System & Shell",
    "system": "System & Shell",
    "shell": "System & Shell",
    "runtimes": "Runtimes & Languages",
    "languages": "Runtimes & Languages",
    "media": "Media & Audio",
    "audio": "Media & Audio",
    "utilities": "Utilities",
}


def get_catalog_categories() -> List[str]:
    """Return all unique categories present in the curated catalog."""
    cats = sorted({item.category for item in CURATED_PACKAGES})
    return ["All"] + cats


def search_catalog(query: str = "", category: Optional[str] = None) -> List[CatalogItem]:
    """Instant in-memory catalog search with zero latency and alias normalization."""
    q = query.strip().lower()
    norm_cat = None
    if category and category != "All":
        clean_cat = category.strip().lower()
        norm_cat = CATEGORY_ALIASES.get(clean_cat, category)

    results = []

    for item in CURATED_PACKAGES:
        if norm_cat and item.category != norm_cat:
            continue

        if not q or (
            q in item.name.lower()
            or q in item.attr.lower()
            or q in item.description.lower()
            or q in item.category.lower()
        ):
            results.append(item)

    return results
