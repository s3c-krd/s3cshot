import asyncio
import sys
import argparse
import os
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

# Conditional Flask import
try:
    from flask import Flask, render_template_string, url_for
except ImportError:
    Flask = None

def ensure_https(url: str) -> str:
    """Ensure the URL starts with 'http://' or 'https://'."""
    if not url.startswith(("http://", "https://")):
        return "http://" + url
    return url

async def screenshot_many(
    urls,
    output_dir="screenshots",
    width=1280,
    height=720,
    timeout=10000,
    max_concurrency=10
):
    """
    Capture screenshots concurrently with resource constraints.
    Uses a single browser instance and limits concurrent requests.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser with optimized settings
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--single-process",  # Reduces resource usage
                "--no-zygote",      # Disables zygote process
                "--no-sandbox"      # Only use in trusted environments
            ]
        )
        
        # Create a single browser context for all pages
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            java_script_enabled=False  # Reduces execution time
        )
        
        semaphore = asyncio.Semaphore(max_concurrency)

        async def process_url(url):
            async with semaphore:
                fixed_url = ensure_https(url)
                parsed = urlparse(fixed_url)
                domain = parsed.netloc or parsed.path
                safe_domain = "".join(c for c in domain if c.isalnum() or c in ("-", "."))
                output_path = os.path.join(output_dir, f"{safe_domain}.png")
                
                try:
                    page = await context.new_page()
                    # Faster loading strategy with fallback
                    try:
                        await page.goto(fixed_url, wait_until="load", timeout=timeout)
                    except Exception:
                        await page.goto(fixed_url, wait_until="domcontentloaded", timeout=timeout)
                    
                    await page.screenshot(
                        path=output_path,
                        full_page=False,  # Faster than full page
                        type="jpeg",      # Smaller file size
                        quality=80
                    )
                    print(f"Screenshot saved to {output_path}")
                    return output_path
                except Exception as e:
                    print(f"Error capturing {url}: {e}")
                    return None
                finally:
                    await page.close()

        # Process URLs with concurrency control
        tasks = [process_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # Cleanup resources
        await context.close()
        await browser.close()

    return [r for r in results if r]

def start_ui(output_dir):
    """Launch optimized Flask UI with production settings."""
    if Flask is None:
        print("Flask required: pip install flask")
        sys.exit(1)

    app = Flask(__name__, static_folder=output_dir)
    app.config['TEMPLATES_AUTO_RELOAD'] = False
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # Cache for 5 minutes

    # Simplified template
    template = '''<!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
      <!-- Bootstrap CSS -->
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
      <!-- PhotoSwipe CSS -->
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/photoswipe/4.1.3/photoswipe.min.css">
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/photoswipe/4.1.3/default-skin/default-skin.min.css">
      <title>Screenshots Gallery</title>
      <style>
        .my-gallery img { width: 100%; height: auto; }
        .my-gallery figure { margin: 0; }
      </style>
    </head>
    <body>
      <div class="container py-4">
        <h1 class="mb-4 text-center">Screenshots Gallery</h1>
        <div class="my-gallery row" itemscope itemtype="http://schema.org/ImageGallery">
          {% for image in images %}
          <figure class="col-sm-6 col-md-4 col-lg-3 mb-4" itemprop="associatedMedia" itemscope itemtype="http://schema.org/ImageObject">
            <a href="{{ url_for('static', filename=image) }}" itemprop="contentUrl" data-size="1024x768">
              <img src="{{ url_for('static', filename=image) }}" itemprop="thumbnail" alt="{{ image }}" class="img-thumbnail">
            </a>
            <figcaption class="mt-2 text-center">{{ image }}</figcaption>
          </figure>
          {% endfor %}
        </div>
      </div>
      
      <!-- Root element of PhotoSwipe. Must have class pswp. -->
      <div class="pswp" tabindex="-1" role="dialog" aria-hidden="true">
          <div class="pswp__bg"></div>
          <div class="pswp__scroll-wrap">
              <div class="pswp__container">
                  <div class="pswp__item"></div>
                  <div class="pswp__item"></div>
                  <div class="pswp__item"></div>
              </div>
              <div class="pswp__ui pswp__ui--hidden">
                  <div class="pswp__top-bar">
                      <div class="pswp__counter"></div>
                      <button class="pswp__button pswp__button--close" title="Close (Esc)"></button>
                      <button class="pswp__button pswp__button--share" title="Share"></button>
                      <button class="pswp__button pswp__button--fs" title="Toggle fullscreen"></button>
                      <button class="pswp__button pswp__button--zoom" title="Zoom in/out"></button>
                      <div class="pswp__preloader">
                          <div class="pswp__preloader__icn">
                            <div class="pswp__preloader__cut">
                              <div class="pswp__preloader__donut"></div>
                            </div>
                          </div>
                      </div>
                  </div>
                  <div class="pswp__share-modal pswp__share-modal--hidden pswp__single-tap">
                      <div class="pswp__share-tooltip"></div> 
                  </div>
                  <button class="pswp__button pswp__button--arrow--left" title="Previous (arrow left)"></button>
                  <button class="pswp__button pswp__button--arrow--right" title="Next (arrow right)"></button>
                  <div class="pswp__caption">
                      <div class="pswp__caption__center"></div>
                  </div>
              </div>
          </div>
      </div>
      
      <!-- Scripts -->
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
      <!-- PhotoSwipe JS -->
      <script src="https://cdnjs.cloudflare.com/ajax/libs/photoswipe/4.1.3/photoswipe.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/photoswipe/4.1.3/photoswipe-ui-default.min.js"></script>
      <script>
        // Initialize PhotoSwipe
        var initPhotoSwipeFromDOM = function(gallerySelector) {
          var parseThumbnailElements = function(el) {
            var thumbElements = el.childNodes,
                numNodes = thumbElements.length,
                items = [],
                figureEl,
                linkEl,
                size,
                item;
            for(var i = 0; i < numNodes; i++) {
              figureEl = thumbElements[i];
              if(figureEl.nodeType !== 1) {
                  continue;
              }
              linkEl = figureEl.children[0]; 
              size = linkEl.getAttribute('data-size').split('x');
              item = {
                  src: linkEl.getAttribute('href'),
                  w: parseInt(size[0], 10),
                  h: parseInt(size[1], 10),
                  title: figureEl.children[1] ? figureEl.children[1].innerHTML : ''
              };
              item.msrc = linkEl.children[0].getAttribute('src');
              item.el = figureEl;
              items.push(item);
            }
            return items;
          };
          
          var onThumbnailsClick = function(e) {
              e = e || window.event;
              e.preventDefault ? e.preventDefault() : e.returnValue = false;
              var eTarget = e.target || e.srcElement;
              var clickedListItem = eTarget.closest('figure');
              if(!clickedListItem) {
                  return;
              }
              var clickedGallery = clickedListItem.parentNode,
                  childNodes = clickedGallery.childNodes,
                  numChildNodes = childNodes.length,
                  index;
              for (index = 0; index < numChildNodes; index++) {
                  if(childNodes[index] === clickedListItem) {
                      break;
                  }
              }
              if(index >= numChildNodes) {
                  return;
              }
              openPhotoSwipe(index, clickedGallery);
              return false;
          };
          
          var openPhotoSwipe = function(index, galleryElement, disableAnimation, fromURL) {
              var pswpElement = document.querySelectorAll('.pswp')[0],
                  items = parseThumbnailElements(galleryElement),
                  options = {
                      index: index,
                      galleryUID: galleryElement.getAttribute('data-pswp-uid'),
                      getThumbBoundsFn: function(index) {
                          var thumbnail = items[index].el.getElementsByTagName('img')[0],
                              pageYScroll = window.pageYOffset || document.documentElement.scrollTop,
                              rect = thumbnail.getBoundingClientRect(); 
                          return {x:rect.left, y:rect.top + pageYScroll, w:rect.width};
                      }
                  };
              if(fromURL) {
                  options.index = parseInt(options.index, 10) - 1;
              }
              if(isNaN(options.index)) {
                  return;
              }
              if(disableAnimation) {
                  options.showAnimationDuration = 0;
              }
              var gallery = new PhotoSwipe(pswpElement, PhotoSwipeUI_Default, items, options);
              gallery.init();
          };
          
          var galleryElements = document.querySelectorAll(gallerySelector);
          for(var i = 0, l = galleryElements.length; i < l; i++) {
              galleryElements[i].setAttribute('data-pswp-uid', i+1);
              galleryElements[i].onclick = onThumbnailsClick;
          }
        };
        // Execute above function
        initPhotoSwipeFromDOM('.my-gallery');
      </script>
    </body>
    </html>'''

    @app.route("/")
    def index():
        try:
            files = [f for f in os.listdir(output_dir)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        except Exception as e:
            files = []
            print(f"Error listing images: {e}")
        return render_template_string(template, images=files)

    print("UI available at http://127.0.0.1:5000")
    app.run(debug=False, threaded=True)  # Use production server for real use

def main(urls, output_dir, ui_mode):
    results = asyncio.run(screenshot_many(
        urls,
        output_dir=output_dir,
        max_concurrency=os.cpu_count() * 2  # Optimal concurrency
    ))
    if ui_mode:
        start_ui(output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Optimized URL screenshot tool with resource constraints"
    )
    parser.add_argument(
        "urls", nargs="*", help="URLs to screenshot (space-separated)"
    )
    parser.add_argument(
        "-f", "--file", help="File containing URLs (one per line)"
    )
    parser.add_argument(
        "-o", "--output", default="screenshots", help="Output directory"
    )
    parser.add_argument(
        "-u", "--ui", action="store_true", help="Launch simple UI"
    )
    
    args = parser.parse_args()
    
    urls = args.urls
    if args.file:
        try:
            with open(args.file) as f:
                urls += [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"File error: {e}")
            sys.exit(1)
    
    if not urls:
        parser.print_help()
        sys.exit(1)
    
    main(urls, args.output, args.ui)