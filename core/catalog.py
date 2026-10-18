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
    CatalogItem("Git", "nixpkgs.git", "Development", "Fast, scalable, distributed revision control system", "https://git-scm.com/", "GPL-2.0"),
    CatalogItem("GitHub CLI", "nixpkgs.gh", "Development", "Official command-line tool for GitHub PRs, issues and repos", "https://cli.github.com/", "MIT"),
    CatalogItem("Ripgrep", "nixpkgs.ripgrep", "Development", "Ultra-fast line-oriented search tool combining grep with gitignore", "https://github.com/BurntSushi/ripgrep", "MIT"),
    CatalogItem("Fzf", "nixpkgs.fzf", "Development", "Blazingly fast command-line fuzzy finder for files and history", "https://github.com/junegunn/fzf", "MIT"),
    CatalogItem("Tmux", "nixpkgs.tmux", "Development", "Terminal multiplexer with workspaces, panes and session detach", "https://github.com/tmux/tmux", "ISC"),
    CatalogItem("JQ", "nixpkgs.jq", "Development", "Lightweight, powerful command-line JSON processor and filter", "https://jqlang.github.io/jq/", "MIT"),
    CatalogItem("Bat", "nixpkgs.bat", "Development", "Cat clone with syntax highlighting and automatic paging", "https://github.com/sharkdp/bat", "MIT / Apache-2.0"),
    CatalogItem("Eza", "nixpkgs.eza", "Development", "Modern, maintained replacement for ls with colors and git status", "https://github.com/eza-community/eza", "EUPL-1.2"),
    CatalogItem("Zoxide", "nixpkgs.zoxide", "Development", "A smarter cd command that remembers your frequently visited folders", "https://github.com/ajeetdsouza/zoxide", "MIT"),
    CatalogItem("Direnv", "nixpkgs.direnv", "Development", "Environment switcher that loads and unloads shell variables per folder", "https://direnv.net/", "MIT"),

    # ─── Web Browsers & Internet ─────────────────────────────────────────────
    CatalogItem("Firefox", "nixpkgs.firefox", "Internet & Web", "Free and open-source web browser developed by Mozilla", "https://www.mozilla.org/firefox/", "MPL-2.0"),
    CatalogItem("Chromium", "nixpkgs.chromium", "Internet & Web", "Open-source browser project that powers Google Chrome", "https://www.chromium.org/", "BSD-3-Clause"),
    CatalogItem("Brave Browser", "nixpkgs.brave", "Internet & Web", "Privacy-oriented browser with built-in ad and tracker blocking", "https://brave.com/", "MPL-2.0"),
    CatalogItem("Thunderbird", "nixpkgs.thunderbird", "Internet & Web", "Full-featured email, newsgroup and calendar desktop client", "https://www.thunderbird.net/", "MPL-2.0"),
    CatalogItem("Curl", "nixpkgs.curl", "Internet & Web", "Universal command line tool and library for transferring URLs", "https://curl.se/", "curl"),
    CatalogItem("Wget", "nixpkgs.wget", "Internet & Web", "Tool for non-interactive download of files from HTTP and FTP", "https://www.gnu.org/software/wget/", "GPL-3.0"),
    CatalogItem("HTTPie", "nixpkgs.httpie", "Internet & Web", "Modern, user-friendly command-line HTTP client for API debugging", "https://httpie.io/", "BSD-3-Clause"),

    # ─── System Monitors & Shells ────────────────────────────────────────────
    CatalogItem("Btop", "nixpkgs.btop", "System & Shell", "Gorgeous resource monitor showing CPU, memory, disks and network", "https://github.com/aristocratos/btop", "Apache-2.0"),
    CatalogItem("Htop", "nixpkgs.htop", "System & Shell", "Interactive process viewer and system activity monitor", "https://htop.dev/", "GPL-2.0"),
    CatalogItem("Fastfetch", "nixpkgs.fastfetch", "System & Shell", "Lightning-fast system information fetch tool written in C", "https://github.com/fastfetch-cli/fastfetch", "MIT"),
    CatalogItem("Zsh", "nixpkgs.zsh", "System & Shell", "Powerful UNIX shell designed for interactive command-line use", "https://www.zsh.org/", "MIT-like"),
    CatalogItem("Fish", "nixpkgs.fish", "System & Shell", "Smart and user-friendly command line shell with autosuggestions", "https://fishshell.com/", "GPL-2.0"),
    CatalogItem("Starship", "nixpkgs.starship", "System & Shell", "Blazing-fast, minimal, customizable cross-shell prompt", "https://starship.rs/", "ISC"),
    CatalogItem("Alacritty", "nixpkgs.alacritty", "System & Shell", "GPU-accelerated, fast terminal emulator written in Rust", "https://alacritty.org/", "Apache-2.0"),
    CatalogItem("Kitty", "nixpkgs.kitty", "System & Shell", "Modern, hackable, GPU-based terminal emulator with tabs and splits", "https://sw.kovidgoyal.net/kitty/", "GPL-3.0"),

    # ─── Programming Languages & Runtimes ────────────────────────────────────
    CatalogItem("Node.js 20 (LTS)", "nixpkgs.nodejs_20", "Runtimes", "JavaScript runtime environment built on V8 engine", "https://nodejs.org/", "MIT"),
    CatalogItem("Python 3.12", "nixpkgs.python312", "Runtimes", "Versatile high-level programming language with broad ecosystem", "https://www.python.org/", "PSF"),
    CatalogItem("Go (Golang)", "nixpkgs.go", "Runtimes", "Fast, statically typed, compiled programming language by Google", "https://go.dev/", "BSD-3-Clause"),
    CatalogItem("Rust (Cargo)", "nixpkgs.cargo", "Runtimes", "Rust language package manager and compiler toolchain", "https://www.rust-lang.org/", "MIT / Apache-2.0"),
    CatalogItem("Bun", "nixpkgs.bun", "Runtimes", "All-in-one JavaScript runtime, bundler, test runner and package manager", "https://bun.sh/", "MIT"),
    CatalogItem("Docker CLI", "nixpkgs.docker", "Runtimes", "Pack, ship and run any application as a lightweight container", "https://www.docker.com/", "Apache-2.0"),
    CatalogItem("Docker Compose", "nixpkgs.docker-compose", "Runtimes", "Define and run multi-container applications with Docker", "https://docs.docker.com/compose/", "Apache-2.0"),
    CatalogItem("Kubectl", "nixpkgs.kubectl", "Runtimes", "Kubernetes command line tool for cluster orchestration", "https://kubernetes.io/", "Apache-2.0"),

    # ─── Media & Graphics ────────────────────────────────────────────────────
    CatalogItem("VLC Media Player", "nixpkgs.vlc", "Media & Audio", "Free and open source multimedia player for almost any codec", "https://www.videolan.org/vlc/", "GPL-2.0"),
    CatalogItem("FFmpeg", "nixpkgs.ffmpeg", "Media & Audio", "Complete cross-platform solution to record, convert and stream media", "https://ffmpeg.org/", "GPL-2.1+"),
    CatalogItem("GIMP", "nixpkgs.gimp", "Media & Audio", "GNU Image Manipulation Program for photo retouching and graphic design", "https://www.gimp.org/", "GPL-3.0"),
    CatalogItem("Inkscape", "nixpkgs.inkscape", "Media & Audio", "Professional vector graphics editor for illustration and design", "https://inkscape.org/", "GPL-2.0"),
    CatalogItem("OBS Studio", "nixpkgs.obs-studio", "Media & Audio", "Free and open source software for video recording and live streaming", "https://obsproject.com/", "GPL-2.0"),
    CatalogItem("ImageMagick", "nixpkgs.imagemagick", "Media & Audio", "Command line suite to create, edit, compose and convert bitmap images", "https://imagemagick.org/", "Apache-2.0"),

    # ─── Utilities & Productivity ────────────────────────────────────────────
    CatalogItem("7-Zip (p7zip)", "nixpkgs.p7zip", "Utilities", "High compression ratio file archiver for 7z, zip, and tar formats", "https://www.7-zip.org/", "LGPL-2.1"),
    CatalogItem("GnuPG (GPG)", "nixpkgs.gnupg", "Utilities", "Complete, free implementation of OpenPGP for encryption and signing", "https://gnupg.org/", "GPL-3.0"),
    CatalogItem("Tree", "nixpkgs.tree", "Utilities", "Recursive directory listing command producing a depth-indented tree", "http://mama.indstate.edu/users/ice/tree/", "GPL-2.0"),
    CatalogItem("GNU Hello", "nixpkgs.hello", "Utilities", "Official GNU hello testing package for verifying Nix environments", "https://www.gnu.org/software/hello/", "GPL-3.0"),
]


def search_catalog(query: str = "", category: Optional[str] = None) -> List[CatalogItem]:
    """Instant in-memory catalog search with zero latency."""
    q = query.strip().lower()
    results = []

    for item in CURATED_PACKAGES:
        if category and category != "All" and item.category != category:
            continue

        if not q or (
            q in item.name.lower()
            or q in item.attr.lower()
            or q in item.description.lower()
            or q in item.category.lower()
        ):
            results.append(item)

    return results
