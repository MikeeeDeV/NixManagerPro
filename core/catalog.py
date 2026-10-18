"""
core.catalog
~~~~~~~~~~~~

Curated catalog of top Nix packages for zero-latency browsing and instant installation.
Provides fast offline discovery without waiting for full nix-env evaluation.
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


CURATED_PACKAGES: List[CatalogItem] = [
    # Developer Essentials
    CatalogItem("Git", "nixpkgs.git", "Developer Tools", "Fast, scalable, distributed revision control system", "https://git-scm.com/"),
    CatalogItem("Neovim", "nixpkgs.neovim", "Developer Tools", "Vim-fork focused on extensibility and usability", "https://neovim.io/"),
    CatalogItem("Ripgrep", "nixpkgs.ripgrep", "Developer Tools", "Fastest line-oriented search tool and grep replacement", "https://github.com/BurntSushi/ripgrep"),
    CatalogItem("Fzf", "nixpkgs.fzf", "Developer Tools", "General-purpose command-line fuzzy finder", "https://github.com/junegunn/fzf"),
    CatalogItem("Tmux", "nixpkgs.tmux", "Developer Tools", "Terminal multiplexer with multiple panes and sessions", "https://github.com/tmux/tmux"),
    CatalogItem("GitHub CLI", "nixpkgs.gh", "Developer Tools", "Official GitHub CLI command-line tool", "https://cli.github.com/"),
    CatalogItem("JQ", "nixpkgs.jq", "Developer Tools", "Lightweight and flexible command-line JSON processor", "https://jqlang.github.io/jq/"),
    CatalogItem("Bat", "nixpkgs.bat", "Developer Tools", "A cat clone with syntax highlighting and Git integration", "https://github.com/sharkdp/bat"),
    CatalogItem("Eza (Exa)", "nixpkgs.eza", "Developer Tools", "Modern, maintained replacement for ls with colors and icons", "https://github.com/eza-community/eza"),

    # Shells & System Monitors
    CatalogItem("Htop", "nixpkgs.htop", "System & Shell", "Interactive process viewer and system activity monitor", "https://htop.dev/"),
    CatalogItem("Btop", "nixpkgs.btop", "System & Shell", "Modern and beautiful resource monitor that shows usage and stats", "https://github.com/aristocratos/btop"),
    CatalogItem("Fastfetch", "nixpkgs.fastfetch", "System & Shell", "Extremely fast system information fetch tool like neofetch", "https://github.com/fastfetch-cli/fastfetch"),
    CatalogItem("Zsh", "nixpkgs.zsh", "System & Shell", "Advanced programmable command interpreter and shell", "https://www.zsh.org/"),
    CatalogItem("Fish", "nixpkgs.fish", "System & Shell", "Smart and user-friendly command line shell", "https://fishshell.com/"),
    CatalogItem("Starship", "nixpkgs.starship", "System & Shell", "Minimal, blazing-fast, and customizable cross-shell prompt", "https://starship.rs/"),
    CatalogItem("Tree", "nixpkgs.tree", "System & Shell", "Recursive directory listing command with depth tree display", "http://mama.indstate.edu/users/ice/tree/"),

    # Languages & Runtimes
    CatalogItem("Node.js (LTS)", "nixpkgs.nodejs_20", "Runtimes", "JavaScript runtime built on Chrome's V8 engine", "https://nodejs.org/"),
    CatalogItem("Python 3", "nixpkgs.python3", "Runtimes", "High-level programming language with extensive standard library", "https://www.python.org/"),
    CatalogItem("Go", "nixpkgs.go", "Runtimes", "Open source programming language for simple, fast software", "https://go.dev/"),
    CatalogItem("Rust (Cargo)", "nixpkgs.cargo", "Runtimes", "Rust package manager and compiler suite", "https://www.rust-lang.org/"),
    CatalogItem("Bun", "nixpkgs.bun", "Runtimes", "Fast all-in-one JavaScript runtime & package manager", "https://bun.sh/"),

    # Networking & Utilities
    CatalogItem("Curl", "nixpkgs.curl", "Networking", "Command line tool for transferring data with URLs", "https://curl.se/"),
    CatalogItem("Wget", "nixpkgs.wget", "Networking", "Tool for retrieving files using HTTP, HTTPS, and FTP", "https://www.gnu.org/software/wget/"),
    CatalogItem("HTTPie", "nixpkgs.httpie", "Networking", "User-friendly CLI HTTP client for API testing", "https://httpie.io/"),
    CatalogItem("Nmap", "nixpkgs.nmap", "Networking", "Network exploration tool and security / port scanner", "https://nmap.org/"),

    # Media & Productivity
    CatalogItem("FFmpeg", "nixpkgs.ffmpeg", "Media", "Complete, cross-platform solution to record, convert and stream audio and video", "https://ffmpeg.org/"),
    CatalogItem("ImageMagick", "nixpkgs.imagemagick", "Media", "Software suite to create, edit, compose, or convert bitmap images", "https://imagemagick.org/"),
    CatalogItem("7-Zip (p7zip)", "nixpkgs.p7zip", "Utilities", "High compression ratio file archiver", "https://www.7-zip.org/"),
    CatalogItem("GnuPG", "nixpkgs.gnupg", "Utilities", "Complete and free implementation of the OpenPGP standard", "https://gnupg.org/"),
    CatalogItem("GNU Hello", "nixpkgs.hello", "Utilities", "GNU hello-world testing derivation for Nix installations", "https://www.gnu.org/software/hello/"),
]


def search_catalog(query: str, category: Optional[str] = None) -> List[CatalogItem]:
    """Search the fast in-memory curated catalog."""
    q = query.strip().lower()
    results = []

    for item in CURATED_PACKAGES:
        if category and category != "All" and item.category != category:
            continue

        if not q or q in item.name.lower() or q in item.attr.lower() or q in item.description.lower():
            results.append(item)

    return results
