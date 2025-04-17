# S3cShot

**S3cShot** is a high-performance Python tool for capturing screenshots of multiple URLs concurrently using [Playwright](https://playwright.dev/python/). It also features a sleek gallery UI powered by [Flask](https://flask.palletsprojects.com/) and [PhotoSwipe](https://photoswipe.com/) for easy viewing and sharing.

> ⚡️ Built for speed. Designed for red teamers, testers, and devs who want screenshots—fast.

---

## 🚀 Features

- 🧠 **Concurrent Screenshotting** – Async-powered for blazing fast performance
- 🔐 **Smart URL Handling** – Automatically prepends `http://` if missing
- 📁 **Custom Output Directory** – Save screenshots in your preferred folder
- 🖼️ **Modern UI Gallery (Optional)** – View results in a zoomable gallery with keyboard navigation
- 🧪 **Command Line Interface** – Easy to use with URL args or a file input

---

## 📦 Requirements

- Python 3.7+
- [`playwright`](https://playwright.dev/python/)
- [`flask`](https://flask.palletsprojects.com/) (optional, for UI mode)

---

## ⚙️ Installation

```bash
# Clone the repo
git clone https://github.com/s3c-krd/s3cshot.git
cd s3cshot

# Install dependencies
pip install playwright flask

# Install browser binaries for Playwright
playwright install
```

## 🕹️ Usage

### 📸 Basic Screenshot Mode  
Screenshot multiple sites:

```bash
python s3cshot.py amazon.com apple.com twitter.com
```
### 📄 From a File  
Capture screenshots from a file (`urls.txt` with one URL per line):

```bash
python s3cshot.py -f urls.txt
```
### 📁 Custom Output Folder  
Save screenshots in a specific folder:

```bash
python s3cshot.py amazon.com -o results/

```
### 🖼️ Launch with Gallery UI
Take screenshots and instantly launch a modern zoomable gallery:

```bash
python s3cshot.py -f urls.txt -u



