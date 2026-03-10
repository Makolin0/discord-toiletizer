from flask import Flask, Response, abort
import requests
from bs4 import BeautifulSoup
import os # Added for path operations and file existence check
from gif_modifier import place_gif_behind_image # Import the GIF processing function

app = Flask(__name__)

# Define the path to toilet.png and the coordinates for GIF placement
PNG_PATH = os.path.join(os.path.dirname(__file__), "toilet.png")
TOP_LEFT = (1310, 1630)
BOTTOM_RIGHT = (1900, 2200)

@app.route('/view/<path:path>')
def proxy_tenor_gif(path):
    """
    This endpoint proxies a GIF from a tenor.com/view/ page.
    It fetches the Tenor page, finds the direct GIF URL, downloads it,
    and serves it to the client.
    This version also processes the GIF by placing it behind a static PNG image.
    """
    tenor_page_url = f"https://tenor.com/view/{path}"

    if not os.path.exists(PNG_PATH):
        return "Error: toilet.png not found. Please ensure it's in the same directory as main.py.", 500

    try:
        # Fetch the HTML content of the Tenor page.
        # A User-Agent header is added to mimic a browser.
        page_response = requests.get(tenor_page_url, headers={'User-Agent': 'Mozilla/5.0'})
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
        gif_response = requests.get(gif_url, stream=True) # Use stream=True for potentially large files
        gif_response.raise_for_status()
        gif_bytes = gif_response.content

        # Process the GIF using the gif_modifier function
        processed_gif_bytes = place_gif_behind_image(
            gif_bytes,
            PNG_PATH,
            TOP_LEFT,
            BOTTOM_RIGHT
        )

        # Serve the processed GIF content back to the client.
        return Response(processed_gif_bytes, mimetype='image/gif')

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to fetch GIF from Tenor: {e}")
        return f"Failed to fetch GIF from Tenor or process it: {e}", 500
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred during GIF processing: {e}", 500

if __name__ == "__main__":
    # Runs the Flask web server.
    # debug=True will auto-reload the server on code changes.
    app.run(host='0.0.0.0', port=8080, debug=True)