import re
from urllib.parse import urlparse, urljoin
from proxy import Proxy
from bs4 import BeautifulSoup
from flask import Flask, request, render_template_string, Response
import requests

app = Flask(__name__)

HTML_FORM = '''
<!doctype html>
<title>Proxy URL Input</title>
<h1>Enter URL to Proxy</h1>
<form action="/proxy" method="post">
  <input type="text" name="url" placeholder="Enter URL here" style="width: 300px;">
  <input type="submit" value="Submit">
</form>
<hr>
{% if content %}
<h2>Content from {{ url }}</h2>
<div>{{ content|safe }}</div>
{% endif %}
'''

# Replace links in the HTML content to use the proxy server
def rewrite_links(html, base_url, proxy_url):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all(['a', 'img', 'script', 'link']):
        attr = 'href' if tag.name in ['a', 'link'] else 'src'
        if tag.has_attr(attr):
            original_url = tag[attr]
            parsed_url = urlparse(original_url)
            if not parsed_url.netloc:
                original_url = urljoin(base_url, original_url)
            tag[attr] = urljoin(proxy_url, f'/proxy?url={original_url}')
    return str(soup)

@app.route('/')
def index():
    return render_template_string(HTML_FORM)

@app.route('/proxy', methods=['POST'])
def proxy():
    url = request.form['url']
    proxy_url = request.host_url
    try:
        response = requests.get(url)
        content = response.text
        # Rewrite links in the content to use the proxy server
        content = rewrite_links(content, url, proxy_url)
    except requests.RequestException as e:
        content = f"Error fetching URL: {e}"

    return render_template_string(HTML_FORM, content=content, url=url)

class CustomProxyHandler(Proxy):
    def on_request(self, request):
        return request

    def on_response(self, response):
        return response

def run_proxy():
    proxy = CustomProxyHandler(
        hostname='127.0.0.1',
        port=8888
    )
    proxy.run()

if __name__ == '__main__':
    from threading import Thread
    # Run the proxy server in a separate thread
    proxy_thread = Thread(target=run_proxy)
    proxy_thread.start()
    # Run the Flask web server
    app.run(port=5000)
