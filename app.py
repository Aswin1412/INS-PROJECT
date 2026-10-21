"""
app.py — Tkinter GUI for the Secure File Encryption Tool.

Simplified workflow:
    1. Encrypt → pick a file, set a password → produces <file>.enc
    2. Decrypt → pick a .enc file, enter the password → restores original

Usage:
    python app.py
"""

from __future__ import annotations

import datetime
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

import crypto_utils
from cryptography.fernet import InvalidToken


# -----------------------------------------------------------------------
# Colour palette
# -----------------------------------------------------------------------
_BG           = "#1e1e2e"
_BG_SECONDARY = "#282840"
_FG           = "#cdd6f4"
_FG_DIM       = "#7f849c"
_ACCENT       = "#89b4fa"
_ACCENT_HOVER = "#74c7ec"
_SUCCESS      = "#a6e3a1"
_ERROR        = "#f38ba8"
_WARN         = "#fab387"
_BUTTON_BG    = "#313244"
_ENTRY_BG     = "#45475a"
_BORDER       = "#585b70"

_FONT_FAMILY  = "Segoe UI"
_FONT_TITLE   = (_FONT_FAMILY, 20, "bold")
_FONT_SUB     = (_FONT_FAMILY, 10)
_FONT_BTN     = (_FONT_FAMILY, 11, "bold")
_FONT_LOG     = ("Consolas", 9)

_WIN_WIDTH  = 540
_WIN_HEIGHT = 460


# -----------------------------------------------------------------------
# Password dialog
# -----------------------------------------------------------------------
class _PasswordDialog(tk.Toplevel):
    """Modal dialog that asks the user for a password."""

    def __init__(
        self,
        parent: tk.Tk,
        title: str = "Enter Password",
        prompt: str = "Password:",
        confirm: bool = False,
    ) -> None:
        super().__init__(parent)
        self.result: Optional[str] = None
        self._confirm = confirm

        self.title(title)
        self.configure(bg=_BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Centre on parent
        self.update_idletasks()
        pw, ph = 380, 240 if confirm else 190
        px = parent.winfo_x() + (parent.winfo_width() - pw) // 2
        py = parent.winfo_y() + (parent.winfo_height() - ph) // 2
        self.geometry(f"{pw}x{ph}+{px}+{py}")

        frame = tk.Frame(self, bg=_BG, padx=24, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Prompt
        tk.Label(
            frame, text=prompt, bg=_BG, fg=_FG,
            font=(_FONT_FAMILY, 10, "bold"), anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 6))

        # Password entry
        pw_frame = tk.Frame(frame, bg=_BG)
        pw_frame.pack(fill=tk.X)

        self._pw_var = tk.StringVar()
        self._pw_entry = tk.Entry(
            pw_frame, textvariable=self._pw_var, show="●",
            font=(_FONT_FAMILY, 11), bg=_ENTRY_BG, fg=_FG,
            insertbackground=_FG, relief=tk.FLAT, bd=6,
        )
        self._pw_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._pw_entry.focus_set()

        self._show_btn = tk.Button(
            pw_frame, text="👁", bg=_BUTTON_BG, fg=_FG,
            font=(_FONT_FAMILY, 10), relief=tk.FLAT, bd=0, width=3,
            activebackground=_ENTRY_BG, activeforeground=_FG,
            command=self._toggle_show,
        )
        self._show_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self._showing = False

        # Confirm entry (only for encryption)
        if confirm:
            tk.Label(
                frame, text="Confirm Password:", bg=_BG, fg=_FG,
                font=(_FONT_FAMILY, 10, "bold"), anchor=tk.W,
            ).pack(fill=tk.X, pady=(10, 6))

            self._confirm_var = tk.StringVar()
            self._confirm_entry = tk.Entry(
                frame, textvariable=self._confirm_var, show="●",
                font=(_FONT_FAMILY, 11), bg=_ENTRY_BG, fg=_FG,
                insertbackground=_FG, relief=tk.FLAT, bd=6,
            )
            self._confirm_entry.pack(fill=tk.X)

        # Buttons
        btn_frame = tk.Frame(frame, bg=_BG)
        btn_frame.pack(fill=tk.X, pady=(16, 0))

        tk.Button(
            btn_frame, text="Cancel", bg=_BUTTON_BG, fg=_FG,
            font=_FONT_BTN, relief=tk.FLAT, padx=16, pady=6,
            activebackground=_ENTRY_BG, activeforeground=_FG,
            command=self._on_cancel,
        ).pack(side=tk.RIGHT)

        tk.Button(
            btn_frame, text="  OK  ", bg=_ACCENT, fg="#11111b",
            font=_FONT_BTN, relief=tk.FLAT, padx=16, pady=6,
            activebackground=_ACCENT_HOVER, activeforeground="#11111b",
            command=self._on_ok,
        ).pack(side=tk.RIGHT, padx=(0, 8))

        # Bind Enter key
        self.bind("<Return>", lambda _: self._on_ok())
        self.bind("<Escape>", lambda _: self._on_cancel())

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_window()

    def _toggle_show(self) -> None:
        self._showing = not self._showing
        char = "" if self._showing else "●"
        self._pw_entry.configure(show=char)
        self._show_btn.configure(text="🔒" if self._showing else "👁")

    def _on_ok(self) -> None:
        pw = self._pw_var.get()
        if not pw:
            messagebox.showwarning("Empty Password", "Please enter a password.", parent=self)
            return
        if self._confirm:
            if pw != self._confirm_var.get():
                messagebox.showwarning(
                    "Mismatch", "Passwords do not match. Please try again.", parent=self
                )
                return
        self.result = pw
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


# -----------------------------------------------------------------------
# Main application
# -----------------------------------------------------------------------
class SecureFileEncryptorApp:
    """Main GUI window."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._configure_window()
        self._build_styles()
        self._build_ui()
        self._log("Ready. Choose an action below to get started.")

    # -------------------------------------------------------------------
    # Window
    # -------------------------------------------------------------------
    def _configure_window(self) -> None:
        self.root.title("🔐 SecureVault — File Encryption Tool")
        self.root.configure(bg=_BG)
        self.root.resizable(False, False)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - _WIN_WIDTH) // 2
        y = (sh - _WIN_HEIGHT) // 2
        self.root.geometry(f"{_WIN_WIDTH}x{_WIN_HEIGHT}+{x}+{y}")

    # -------------------------------------------------------------------
    # Styles
    # -------------------------------------------------------------------
    def _build_styles(self) -> None:
        s = ttk.Style(self.root)
        s.theme_use("clam")

        s.configure("App.TFrame", background=_BG)
        s.configure("Title.TLabel", background=_BG, foreground=_ACCENT, font=_FONT_TITLE)
        s.configure("Sub.TLabel", background=_BG, foreground=_FG_DIM, font=_FONT_SUB)
        s.configure("Sep.TSeparator", background=_BORDER)

        for name, bg, fg in [
            ("Accent.TButton", _ACCENT, "#11111b"),
            ("Secondary.TButton", _BUTTON_BG, _FG),
        ]:
            s.configure(name, background=bg, foreground=fg, font=_FONT_BTN,
                        padding=(18, 12), borderwidth=0)
            s.map(name,
                  background=[("active", _ACCENT_HOVER if "Accent" in name else _ENTRY_BG)],
                  foreground=[("disabled", _FG_DIM)])

    # -------------------------------------------------------------------
    # UI
    # -------------------------------------------------------------------
    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, style="App.TFrame", padding=24)
        outer.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(outer, text="🔐  SecureVault", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(
            outer,
            text="Password-based file encryption  •  AES-128-CBC + HMAC-SHA256",
            style="Sub.TLabel",
        ).pack(anchor=tk.W, pady=(2, 8))

        ttk.Separator(outer, orient=tk.HORIZONTAL, style="Sep.TSeparator").pack(
            fill=tk.X, pady=(0, 16)
        )

        # Instructions
        tk.Label(
            outer,
            text="Select a file and set a password to encrypt it.\n"
                 "Use the same password later to decrypt.",
            bg=_BG, fg=_FG, font=(_FONT_FAMILY, 10), justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 14))

        # Action buttons
        btn_frame = ttk.Frame(outer, style="App.TFrame")
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            btn_frame, text="🔒  Encrypt a File",
            style="Accent.TButton", command=self._on_encrypt,
        ).pack(side=tk.LEFT, padx=(0, 12))

        ttk.Button(
            btn_frame, text="🔓  Decrypt a File",
            style="Secondary.TButton", command=self._on_decrypt,
        ).pack(side=tk.LEFT)

        ttk.Separator(outer, orient=tk.HORIZONTAL, style="Sep.TSeparator").pack(
            fill=tk.X, pady=(14, 10)
        )

        # Activity log
        ttk.Label(outer, text="Activity Log", style="Sub.TLabel").pack(anchor=tk.W, pady=(0, 4))

        log_frame = tk.Frame(outer, bg=_BG_SECONDARY, bd=1, relief=tk.FLAT)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self._log_text = tk.Text(
            log_frame, bg=_BG_SECONDARY, fg=_FG, font=_FONT_LOG,
            wrap=tk.WORD, state=tk.DISABLED, borderwidth=0,
            highlightthickness=0, padx=10, pady=8,
            insertbackground=_FG, selectbackground=_ACCENT,
            selectforeground="#11111b",
        )
        self._log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self._log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._log_text.configure(yscrollcommand=scrollbar.set)

        self._log_text.tag_configure("INFO", foreground=_FG)
        self._log_text.tag_configure("SUCCESS", foreground=_SUCCESS)
        self._log_text.tag_configure("ERROR", foreground=_ERROR)
        self._log_text.tag_configure("WARN", foreground=_WARN)

    # -------------------------------------------------------------------
    # Log helper
    # -------------------------------------------------------------------
    def _log(self, message: str, level: str = "INFO") -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}
        line = f"[{ts}]  {icons.get(level, '')}  {message}\n"

        self._log_text.configure(state=tk.NORMAL)
        self._log_text.insert(tk.END, line, level)
        self._log_text.see(tk.END)
        self._log_text.configure(state=tk.DISABLED)

    # -------------------------------------------------------------------
    # Encrypt
    # -------------------------------------------------------------------
    def _on_encrypt(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Select File to Encrypt",
            filetypes=[("All Files", "*.*")],
        )
        if not filepath:
            return

        dlg = _PasswordDialog(
            self.root,
            title="Set Encryption Password",
            prompt="Choose a password for this file:",
            confirm=True,
        )
        if dlg.result is None:
            return

        try:
            enc_path = crypto_utils.encrypt_file(filepath, dlg.result)
            name = os.path.basename(enc_path)
            self._log(f"Encrypted → {name}\n           {enc_path}", "SUCCESS")
            messagebox.showinfo(
                "Encryption Complete",
                f"File encrypted successfully!\n\nSaved as:\n{enc_path}\n\n"
                "⚠️  Remember your password — it cannot be recovered.",
            )
        except FileNotFoundError:
            messagebox.showerror("File Not Found", f"File not found:\n{filepath}")
            self._log(f"File not found: {filepath}", "ERROR")
        except PermissionError:
            messagebox.showerror("Permission Denied", "Cannot read/write the file.")
            self._log("Permission denied during encryption.", "ERROR")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self._log(f"Error: {exc}", "ERROR")

    # -------------------------------------------------------------------
    # Decrypt
    # -------------------------------------------------------------------
    def _on_decrypt(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Select File to Decrypt",
            filetypes=[("Encrypted Files", "*.locked"), ("All Files", "*.*")],
        )
        if not filepath:
            return

        dlg = _PasswordDialog(
            self.root,
            title="Enter Decryption Password",
            prompt="Enter the password used to encrypt this file:",
            confirm=False,
        )
        if dlg.result is None:
            return

        try:
            dec_path = crypto_utils.decrypt_file(filepath, dlg.result)
            name = os.path.basename(dec_path)
            self._log(f"Decrypted → {name}\n           {dec_path}", "SUCCESS")
            messagebox.showinfo(
                "Decryption Complete",
                f"File decrypted successfully!\n\nRestored as:\n{dec_path}",
            )
        except FileNotFoundError:
            messagebox.showerror("File Not Found", f"File not found:\n{filepath}")
            self._log(f"File not found: {filepath}", "ERROR")
        except PermissionError:
            messagebox.showerror("Permission Denied", "Cannot read/write the file.")
            self._log("Permission denied during decryption.", "ERROR")
        except InvalidToken:
            messagebox.showerror(
                "Decryption Failed",
                "Incorrect password or corrupted file.\n\n"
                "Make sure you're using the exact same password\n"
                "that was used to encrypt this file.",
            )
            self._log("Decryption failed — wrong password or corrupted file.", "ERROR")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self._log(f"Error: {exc}", "ERROR")


# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------
def main() -> None:
    root = tk.Tk()
    SecureFileEncryptorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
