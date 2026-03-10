import io # Added for in-memory file operations
from PIL import Image, ImageDraw, ImageSequence


def ellipse(x, y, offset):
	image = Image.new("RGB", (400, 400), "blue")
	draw = ImageDraw.Draw(image)
	draw.ellipse((x, y, x+offset, y+offset), fill="red")
	return image
def make_gif():
	frames = []
	x = 0
	y = 0
	offset = 50
	for number in range(20):
		frames.append(ellipse(x, y, offset))
		x += 35
		y += 35
		
	frame_one = frames[0]
	frame_one.save("circle.gif", format="GIF", append_images=frames,
				   save_all=True, duration=100, loop=0)

def place_gif_behind_image(gif_bytes, png_path, top_left, bottom_right):
	"""
	Places a GIF behind a PNG image within a specific coordinate window.
	
	:param gif_bytes: The raw bytes of the input GIF.
	:param png_path: Path to the static foreground PNG image.
	:param top_left: Tuple (x1, y1) for the top-left corner of the GIF placement.
	:param bottom_right: Tuple (x2, y2) for the bottom-right corner of the GIF placement.
	:return: The raw bytes of the processed GIF.
	"""
	# Load the static foreground PNG
	foreground = Image.open(png_path).convert("RGBA")
	bg_width, bg_height = foreground.size
	
	# Calculate the required size for the GIF based on coordinates
	target_width = bottom_right[0] - top_left[0]
	target_height = bottom_right[1] - top_left[1]
	
	# Open the GIF
	gif = Image.open(io.BytesIO(gif_bytes)) # Open GIF from bytes
	
	frames = []
	
	for frame in ImageSequence.Iterator(gif):
		# 1. Create a transparent base the size of the total image
		canvas = Image.new("RGBA", (bg_width, bg_height), (0, 0, 0, 0))
		
		# 2. Resize and prepare the GIF frame
# Updated resizing line
		frame_resized = frame.convert("RGBA").resize(
			(target_width, target_height), 
			Image.Resampling.LANCZOS
		)
		# 3. Paste the GIF frame onto the canvas at the target location
		canvas.paste(frame_resized, top_left)
		
		# 4. Composite the PNG on TOP of the canvas
		# alpha_composite requires both images to be the same size
		combined = Image.alpha_composite(canvas, foreground)
		frames.append(combined)

	# Save the result to an in-memory BytesIO object
	output_buffer = io.BytesIO()
	frames[0].save(
		output_buffer,
		format="GIF", # Specify format when saving to BytesIO
		save_all=True,
		append_images=frames[1:],
		optimize=False,
		duration=gif.info.get('duration', 100),
		loop=gif.info.get('loop', 0),
		disposal=2
	)
	output_buffer.seek(0) # Rewind to the beginning of the buffer
	return output_buffer.getvalue() # Return the bytes

# def main():
# 	# make_gif()
# 	place_gif_behind_image("./ralsei.gif", "./toilet.png", "./output.gif", 
# 	(1310, 1630), 
# 	(1900, 2200))
