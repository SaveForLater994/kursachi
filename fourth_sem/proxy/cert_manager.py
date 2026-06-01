"""Управление сертификатами."""

import os
import shutil
import platform
from pathlib import Path


class CertManager:
    """Управляет корневым CA сертификатом mitmproxy."""
    
    MITM_CERT_DIR = Path.home() / ".mitmproxy"
    CA_CERT_FILE = "mitmproxy-ca-cert.pem"
    CA_KEY_FILE = "mitmproxy-ca.pem"
    
    @classmethod
    def get_ca_cert_path(cls) -> Path:
        """Путь к публичному CA сертификату."""
        return cls.MITM_CERT_DIR / cls.CA_CERT_FILE
    
    @classmethod
    def get_ca_key_path(cls) -> Path:
        """Путь к приватному ключу CA."""
        return cls.MITM_CERT_DIR / cls.CA_KEY_FILE
    
    @classmethod
    def ca_exists(cls) -> bool:
        """Проверяет, существует ли CA сертификат."""
        return cls.get_ca_cert_path().exists()
    
    @classmethod
    def export_ca_cert(cls, output_path: Path) -> bool:
        """Копирует CA сертификат в указанный файл."""
        src = cls.get_ca_cert_path()
        
        if not src.exists():
            raise FileNotFoundError(
                f"CA certificate not found at {src}.\n"
                f"Run the proxy at least once to generate it."
            )
        
        shutil.copy2(src, output_path)
        return True
    
    @classmethod
    def get_ca_cert_content(cls) -> str:
        """Читает содержимое CA сертификата."""
        cert_path = cls.get_ca_cert_path()
        
        if not cert_path.exists():
            return ""
        
        return cert_path.read_text()
    
    @classmethod
    def get_install_instructions(cls) -> str:
        """Возвращает инструкцию по установке CA сертификата."""
        
        cert_path = cls.get_ca_cert_path()
        system = platform.system()
        
        if system == "Windows":
            return f"""
Windows Installation:
1. Open Command Prompt as Administrator
2. Run: certutil -addstore Root "{cert_path}"

Or manually:
1. Double-click the certificate file: {cert_path}
2. Click "Install Certificate"
3. Select "Local Machine" → Next
4. Select "Place all certificates in the following store"
5. Browse → "Trusted Root Certification Authorities" → OK
6. Finish → Yes → OK
"""
        elif system == "Darwin":  # macOS
            return f"""
macOS Installation:
1. Open Terminal
2. Run: sudo security add-trusted-cert -d -r trustRoot \\
   -k /Library/Keychains/System.keychain "{cert_path}"

Or manually:
1. Open Keychain Access
2. File → Import Items → Select "{cert_path}"
3. Find "mitmproxy" certificate
4. Double-click → Trust → "Always Trust"
"""
        else:  # Linux
            return f"""
Linux Installation:
1. Open Terminal
2. Run:
   sudo cp "{cert_path}" /usr/local/share/ca-certificates/mitmproxy.crt
   sudo update-ca-certificates

For Firefox:
1. Settings → Privacy & Security
2. Certificates → View Certificates
3. Import → Select "{cert_path}"
4. Check "Trust this CA to identify websites" → OK
"""
    
    @classmethod
    def get_firefox_instructions(cls) -> str:
        """Инструкция специально для Firefox (использует свой сертификатный стор)."""
        cert_path = cls.get_ca_cert_path()
        return f"""
Firefox uses its own certificate store!

1. Open Firefox
2. Go to Settings → Privacy & Security
3. Scroll to "Certificates"
4. Click "View Certificates..."
5. Go to "Authorities" tab
6. Click "Import..."
7. Select: {cert_path}
8. Check "Trust this CA to identify websites"
9. Click OK
"""