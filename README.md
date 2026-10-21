# 🔐 SecureVault — Secure File Encryption Tool

A lightweight desktop application that lets you **encrypt and decrypt any file** using a simple password. Built with Python, Tkinter, and the `cryptography` library.

No key files to manage. No complex setup. Just pick a file, set a password, and your data is locked with **military-grade AES encryption**.

---

## ✨ Features

- 🔒 **Password-based encryption** — no key files to lose or manage
- 🛡️ **AES-128-CBC + HMAC-SHA256** via Fernet (authenticated encryption)
- 🔑 **PBKDF2 key derivation** — 480,000 iterations (OWASP 2023 standard)
- 🧂 **Unique random salt per file** — identical files produce different ciphertext
- 👁️ **Show/hide password toggle** in the password dialog
- ✅ **Password confirmation** on encryption to prevent typos
- 🎨 **Modern dark-themed UI** built with Tkinter
- 📋 **Activity log** with timestamped status messages
- ⚠️ **Graceful error handling** — wrong password, missing files, permission issues

---

## 📸 Screenshots

<!-- Add screenshots of your app here -->
<!-- ![Main Window](screenshots/main.png) -->
<!-- ![Encryption Password](screenshots/encrypt.png) -->
<!-- ![Decryption Success](screenshots/decrypt.png) -->

*Screenshots coming soon.*

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+** installed on your system
- `pip` (Python package manager)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/SecureVault.git
   cd SecureVault
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**

   ```bash
   python app.py
   ```

---

## 📖 How to Use

### 🔒 Encrypting a File

1. Click the **"🔒 Encrypt a File"** button.
2. A file browser opens — **select any file** you want to encrypt (e.g., `report.pdf`).
3. A password dialog appears:
   - Enter your desired password.
   - Confirm the password (type it again).
   - Click **OK**.
4. The encrypted file is saved in the **same directory** as the original, with a `.locked` extension:
   ```
   report.pdf  →  report.pdf.locked
   ```
5. A success message confirms the encryption. **The original file is not deleted.**

> ⚠️ **Remember your password!** There is no way to recover it. If you forget the password, the encrypted file cannot be decrypted.

### 🔓 Decrypting a File

1. Click the **"🔓 Decrypt a File"** button.
2. A file browser opens (filtered to `.locked` files) — **select the encrypted file**.
3. A password dialog appears:
   - Enter the **exact same password** used during encryption.
   - Click **OK**.
4. The decrypted file is restored in the same directory, with the `.locked` extension removed:
   ```
   report.pdf.locked  →  report.pdf
   ```
5. A success message confirms the decryption.

### ❌ Wrong Password?

If the password is incorrect, the app will show a clear error:

> **"Decryption Failed: Incorrect password or corrupted file."**

No partial or corrupted output is created — decryption either fully succeeds or safely fails.

---

## 🏗️ Project Structure

```
SecureVault/
├── app.py              # Tkinter GUI — main application window
├── crypto_utils.py     # Core encryption/decryption logic
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── dist/
    └── SecureVault.exe # Standalone Windows executable (optional)
```

| File | Responsibility |
|------|---------------|
| `crypto_utils.py` | Key derivation (PBKDF2), file encryption, file decryption |
| `app.py` | GUI layout, password dialog, event handlers, activity logging |

---

## 🔧 Building a Standalone Executable

To distribute the app as a `.exe` (no Python needed on the target machine):

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name SecureVault app.py
```

The executable will be created at `dist/SecureVault.exe`.

---

## 🛡️ Security Details

| Aspect | Implementation |
|--------|---------------|
| **Encryption** | Fernet (AES-128-CBC + HMAC-SHA256) |
| **Key Derivation** | PBKDF2-HMAC-SHA256, 480,000 iterations |
| **Salt** | 16-byte random salt, unique per file |
| **Authentication** | HMAC-SHA256 ensures tamper detection |
| **Key Storage** | Keys are **never** stored — derived from password at runtime |

### How the encrypted file is structured

```
┌──────────────────┬──────────────────────────────────┐
│  16-byte salt    │  Fernet ciphertext (AES + HMAC)  │
└──────────────────┴──────────────────────────────────┘
```

The random salt is prepended to the ciphertext so that:
- The **same file + same password** produces **different ciphertext** each time.
- Only the salt and the password are needed to re-derive the decryption key.

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| [`cryptography`](https://pypi.org/project/cryptography/) | Fernet encryption, PBKDF2 key derivation |
| `tkinter` | GUI framework (included with Python) |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

---

<p align="center">
  Built with 🐍 Python &nbsp;•&nbsp; Secured with 🔐 AES-128 &nbsp;•&nbsp; Styled with 🎨 Tkinter
</p>
