# Grok Bot's computer, as described by Grok Bot itself (14 October 2026), for a labelled approximation.
# Self-reported and not yet verified: see ../../personal-agents.md. Missing from it: the desktop (Xfce/Thunar),
# CPU and memory limits (about 8 vCPU, 16 GB), and the agent itself (Grok model and harness).
# Comparable local test image: Debian 13.7 (trixie), x86_64, packages as of 2026-10-05
FROM --platform=linux/amd64 debian:trixie

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:2 \
    PIP_BREAK_SYSTEM_PACKAGES=1

# Freeze apt to the same Debian snapshot the box uses
RUN rm -f /etc/apt/sources.list.d/* && printf '%s\n' \
  'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261005T000000Z trixie main' \
  'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261005T000000Z trixie-updates main' \
  'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20261005T000000Z trixie-security main' \
  > /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates=20250419 \
    curl=8.14.1-2+deb13u7 \
    wget=1.25.0-2 \
    gnupg \
    git=1:2.47.3-0+deb13u1 \
    gh=2.46.0-3 \
    jq=1.7.1-6+deb13u4 \
    ripgrep=14.1.1-1+b4 \
    unzip=6.0-29+deb13u1 \
    poppler-utils=25.03.0-5+deb13u4 \
    python3=3.13.5-1 \
    python3-pip=25.1.1+dfsg-1 \
    nodejs=20.19.2+dfsg-1+deb13u3 \
    npm=9.2.0~ds1-3 \
    rustc=1.85.1+dfsg1-1+deb13u1 \
    cargo=1.85.1+dfsg1-1+deb13u1 \
    xvfb=2:21.1.16-1.3+deb13u4 \
    xauth=1:1.1.2-1.1 \
    x11vnc=0.9.17-1 \
    websockify=0.12.0+dfsg1-4+b1 \
    dbus-x11=1.16.2-2 \
    fonts-liberation=1:2.1.5-3 \
    fonts-noto-color-emoji=2.051-0+deb13u1 \
 && rm -rf /var/lib/apt/lists/*

# Google Chrome 154.0.8037.97
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
 && echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable=154.0.8037.97-1 \
 && rm -rf /var/lib/apt/lists/*

RUN npm install -g pnpm@10.34.6

RUN pip install --no-cache-dir \
    beautifulsoup4==4.15.0 lxml==6.1.3 requests==2.34.2 urllib3==2.8.0 certifi==2026.7.22 \
    numpy==2.5.4 pandas==3.0.6 openpyxl==3.1.5 xlsxwriter==3.2.9 \
    python-docx==1.2.0 python-pptx==1.0.2 mammoth==1.11.0 markdownify==1.2.3 markitdown==0.1.7 \
    pillow==12.3.0 fonttools==4.65.0 magika==0.6.3 onnxruntime==1.31.0 \
    cryptography==43.0.0 bcrypt==4.2.0 jwcrypto==1.5.6 \
    python-dateutil==2.9.0.post0 python-dotenv==1.2.4 click==8.5.0 redis==6.1.0

RUN useradd -m -s /bin/bash box && mkdir -p /workspace && chown box:box /workspace
USER box
WORKDIR /workspace
EXPOSE 5900 6080

# 1280x800 virtual desktop with VNC (5900) and a browser-based VNC view (6080). No password: local use only.
CMD ["bash", "-lc", "Xvfb :2 -screen 0 1280x800x24 -nolisten tcp & sleep 1; x11vnc -display :2 -forever -shared -nopw -rfbport 5900 -quiet & websockify 6080 localhost:5900 & exec bash"]
