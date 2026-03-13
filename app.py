from flask import Flask, Response, abort, request
import requests
from bs4 import BeautifulSoup
import os # Added for path operations and file existence check
from gif_modifier import place_gif_behind_image # Import the GIF processing function

app = Flask(__name__)

# Define the path to toilet.png and the coordinates for GIF placement
PNG_PATH = os.path.join(os.path.dirname(__file__), "toilet.png")
TOP_LEFT = (178, 218)
BOTTOM_RIGHT = (254, 294)
TIMEOUT = 10

def get_gif(url):
    # Fetch the HTML content of the Tenor page.
    # A User-Agent header is added to mimic a browser.
    page_response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=TIMEOUT)
    page_response.raise_for_status()  # Raise an exception for bad status codes (like 404).

    # Parse the HTML to find the actual GIF URL.
    soup = BeautifulSoup(page_response.content, 'html.parser')

    # The GIF is usually inside a <div class="Gif">.
    gif_container = soup.find('div', class_='Gif')
    if not gif_container:
        return "Could not find GIF container on Tenor page.", 404

    img_tag = gif_container.find('img')
    if not img_tag or not img_tag.get('src'):
        return "Could not find img tag or src attribute in the container.", 404

    gif_url = img_tag['src']

    # Fetch the actual GIF content.
    gif_response = requests.get(gif_url, stream=True, timeout=TIMEOUT) # Use stream=True for potentially large files
    gif_response.raise_for_status()
    gif_bytes = gif_response.content
    
    return gif_bytes

@app.route('/')
def homepage():
    return "skibidi toilet"

@app.route('/view/<path:path>')
def proxy_tenor_gif(path):
    # Return HTML with Open Graph tags so Discord embeds the image
    gif_url = f"{request.host_url}gif/{path}.gif"
    return f"""<html>
<head>
    <meta property="og:title" content="Toiletized GIF" />
    <meta property="og:image" content="{gif_url}" />
    <meta property="twitter:image" content="{gif_url}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="theme-color" content="#00FF00">
</head>
<body>
    <img src="{gif_url}" />
</body>
</html>"""

@app.route('/gif/<path:path>')
def serve_gif(path):
    if path.endswith('.gif'):
        path = path[:-4]
        
    tenor_page_url = f"https://tenor.com/view/{path}"

    if not os.path.exists(PNG_PATH):
        return "Error: toilet.png not found. Please ensure it's in the same directory as main.py.", 500

    try:
        gif_bytes = get_gif(tenor_page_url)
        
        # Process the GIF using the gif_modifier function
        processed_gif_bytes = place_gif_behind_image(
            gif_bytes,
            PNG_PATH,
            TOP_LEFT,
            BOTTOM_RIGHT
        )

        return Response(processed_gif_bytes, mimetype='image/gif')

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to fetch GIF from Tenor: {e}. URL: {tenor_page_url}")
        return f"Failed to fetch GIF from Tenor or process it: {e}", 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred during GIF processing: {e}", 500
    
def save_to_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(data)

def main():
    tenor_page_url = f"https://tenor.com/view/rasiel-gif-4732260642365963979"
    gif_bytes = get_gif(tenor_page_url)
    processed_gif_bytes = place_gif_behind_image(gif_bytes, PNG_PATH, TOP_LEFT, BOTTOM_RIGHT)
    save_to_file(gif_bytes, "ralsei.gif")
    save_to_file(processed_gif_bytes, "output.gif")

if __name__ == '__main__':
    main()