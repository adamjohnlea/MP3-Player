from tkinter import *
from tkinter import filedialog
import pygame
import time
from mutagen.mp3 import MP3
import tkinter.ttk as ttk
import os
import json
from pathlib import Path

root = Tk()

root.title("MP3 Player")
root.geometry("500x400")


class ThemeManager:
	"""Level-2 image-based skin loader and applier."""
	def __init__(self, root, widgets):
		self.root = root
		self.widgets = widgets  # dict of widget references
		self.current_skin = None
		self.images = {}
		self.skin_dir = None
		self.controls = {}
		self.use_text_buttons = False
		# For custom chrome dragging
		self._drag_enabled = False
		self._drag_start_root = (0, 0)
		self._drag_win_origin = (0, 0)

	def _enable_drag(self):
		if self._drag_enabled:
			return
		def _is_protected_widget(w):
			# Do not start/move drag if the event originated from song or volume sliders
			protected = [
				self.widgets.get('song_slider'),
				self.widgets.get('volume_slider'),
			]
			try:
				while w is not None:
					if w in protected:
						return True
					w = w.master
				return False
			except Exception:
				return False
		def _on_press(event):
			# Skip initiating drag if clicking on protected widgets
			if _is_protected_widget(event.widget):
				return
			self._drag_start_root = (event.x_root, event.y_root)
			self._drag_win_origin = (self.root.winfo_x(), self.root.winfo_y())
		def _on_motion(event):
			# Skip moving while interacting with protected widgets
			if _is_protected_widget(event.widget):
				return
			dx = event.x_root - self._drag_start_root[0]
			dy = event.y_root - self._drag_start_root[1]
			x = self._drag_win_origin[0] + dx
			y = self._drag_win_origin[1] + dy
			try:
				self.root.geometry(f"+{int(x)}+{int(y)}")
			except Exception:
				pass
		self.root.bind('<Button-1>', _on_press, add='+')
		self.root.bind('<B1-Motion>', _on_motion, add='+')
		self._drag_enabled = True

	def _disable_drag(self):
		if not self._drag_enabled:
			return
		try:
			self.root.unbind('<Button-1>')
			self.root.unbind('<B1-Motion>')
		except Exception:
			pass
		self._drag_enabled = False

	def load_skin(self, skin_name):
		base = Path(__file__).parent
		self.skin_dir = base / 'skins' / skin_name
		manifest_file = self.skin_dir / 'manifest.json'
		if not manifest_file.exists():
			raise FileNotFoundError(f"Skin manifest not found: {manifest_file}")
		with open(manifest_file, 'r', encoding='utf-8') as f:
			data = json.load(f)
		self.current_skin = data
		self._load_images(self.skin_dir, data.get('images', {}))
		self.apply()

	def _load_images(self, skin_dir, images_cfg):
		# Keep references so Tk doesn’t GC them
		self.images = {}
		for key, rel in images_cfg.items():
			path = skin_dir / rel
			if path.exists():
				try:
					self.images[key] = PhotoImage(file=str(path))
				except Exception:
					pass

	def apply(self):
		if not self.current_skin:
			return
		colors = self.current_skin.get('colors', {})
		fonts = self.current_skin.get('fonts', {})
		metrics = self.current_skin.get('metrics', {})
		window = self.current_skin.get('window', {})
		self.controls = self.current_skin.get('controls', {})
		self.use_text_buttons = bool(self.controls.get('use_text_buttons', False))

		# Window size and bg color
		if isinstance(window, dict) and 'width' in window and 'height' in window:
			try:
				self.root.geometry(f"{int(window['width'])}x{int(window['height'])}")
			except Exception:
				pass
		if 'root_bg' in colors:
			try:
				self.root.configure(bg=colors['root_bg'])
			except Exception:
				pass

		# Custom chrome handling (remove OS title bar/borders if requested)
		use_cc = False
		if isinstance(window, dict):
			use_cc = bool(window.get('use_custom_chrome', False))
		try:
			self.root.overrideredirect(True if use_cc else False)
			# Optional transparent color (mostly used on Windows)
			transparent_color = window.get('transparent_color') if isinstance(window, dict) else None
			if transparent_color:
				try:
					self.root.wm_attributes('-transparentcolor', transparent_color)
				except Exception:
					pass
			# Enable dragging when custom chrome is on; disable otherwise
			if use_cc:
				self._enable_drag()
			else:
				self._disable_drag()
		except Exception:
			pass

		# Playlist Listbox
		pl = self.widgets.get('playlist_box')
		if pl:
			cfg = {}
			if 'playlist_bg' in colors: cfg['bg'] = colors['playlist_bg']
			if 'playlist_fg' in colors: cfg['fg'] = colors['playlist_fg']
			if 'playlist_select_bg' in colors: cfg['selectbackground'] = colors['playlist_select_bg']
			if 'playlist_select_fg' in colors: cfg['selectforeground'] = colors['playlist_select_fg']
			if 'playlist_width' in metrics: cfg['width'] = metrics['playlist_width']
			if cfg:
				try:
					pl.config(**cfg)
				except Exception:
					pass

		# Frames / Status bar
		frame_bg = colors.get('frame_bg')
		if frame_bg:
			for key in ['main_frame', 'control_frame', 'volume_frame']:
				w = self.widgets.get(key)
				if w:
					try:
						w.config(bg=frame_bg)
					except Exception:
						pass
		status = self.widgets.get('status_bar')
		if status:
			s_cfg = {}
			if 'status_bg' in colors: s_cfg['bg'] = colors['status_bg']
			if 'status_fg' in colors: s_cfg['fg'] = colors['status_fg']
			if s_cfg:
				try:
					status.config(**s_cfg)
				except Exception:
					pass

		# Fonts (optional)
		try:
			from tkinter import font as tkfont
			if 'base' in fonts:
				base_font = tkfont.Font(family=fonts['base'][0], size=fonts['base'][1])
				self.root.option_add('*Font', base_font)
			if status and 'status' in fonts:
				status.config(font=tuple(fonts['status']))
		except Exception:
			pass

		# Slider styling (ttk) if provided by skin
		try:
			from tkinter import ttk as _ttk
			style = _ttk.Style()
			slider_cfg = self.current_skin.get('slider', {}) if isinstance(self.current_skin, dict) else {}
			trough = slider_cfg.get('trough_color')
			thumb = slider_cfg.get('slider_color') or slider_cfg.get('thumb_color')
			thickness = slider_cfg.get('thickness')
			force_theme = slider_cfg.get('force_theme')
			# Optionally force a theme that honors color options (clam is reliable across platforms)
			if force_theme:
				try:
					style.theme_use(force_theme)
				except Exception:
					pass
			# Create styles only if colors or thickness are provided
			if trough or thumb or thickness:
				# Horizontal (song scrubber)
				style_name_h = 'Themed.Horizontal.TScale'
				cfg_h = {}
				if trough: cfg_h['troughcolor'] = trough
				if thumb: cfg_h['background'] = thumb
				if thickness: cfg_h['thickness'] = int(thickness)
				if cfg_h:
					style.configure(style_name_h, **cfg_h)
					song = self.widgets.get('song_slider')
					if song:
						try:
							song.configure(style=style_name_h)
						except Exception:
							pass
				# Vertical (volume)
				style_name_v = 'Themed.Vertical.TScale'
				cfg_v = {}
				if trough: cfg_v['troughcolor'] = trough
				if thumb: cfg_v['background'] = thumb
				if thickness: cfg_v['thickness'] = int(thickness)
				if cfg_v:
					style.configure(style_name_v, **cfg_v)
					vol = self.widgets.get('volume_slider')
					if vol:
						try:
							vol.configure(style=style_name_v)
						except Exception:
							pass
		except Exception:
			pass

		# Controls: text-mode or image-mode
		if self.use_text_buttons:
			labels = self.controls.get('button_text', {})
			btn_cfg = {
				'fg': self.controls.get('button_fg', colors.get('playlist_fg', None)),
				'bg': self.controls.get('button_bg', colors.get('frame_bg', None)),
			}
			w = self.controls.get('button_width', 2)
			h = self.controls.get('button_height', 1)
			def set_text(btn_key, key, default_txt):
				btn = self.widgets.get(btn_key)
				if btn:
					try:
						btn.config(image='', text=labels.get(key, default_txt), width=w, height=h)
						# Apply optional fg/bg if present
						cfg = {k: v for k, v in btn_cfg.items() if v is not None}
						if cfg:
							btn.config(**cfg)
						btn.image = None
					except Exception:
						pass
			set_text('back_button', 'back', 'B')
			set_text('forward_button', 'forward', 'F')
			set_text('play_button', 'play', 'P')
			set_text('stop_button', 'stop', 'S')
		else:
			# Image-mode: optionally subsample icons
			subsample = int(metrics.get('icon_subsample', 1) or 1)
			def set_img(btn_key, img_key):
				btn = self.widgets.get(btn_key)
				img = self.images.get(img_key)
				if btn and img:
					try:
						scaled = img.subsample(subsample, subsample) if subsample > 1 else img
						# Reset size so the image defines the button size (important when switching from text mode)
						btn.config(image=scaled, text='', width=0, height=0)
						btn.image = scaled  # keep reference
					except Exception:
						pass
			set_img('back_button', 'back')
			set_img('forward_button', 'forward')
			# Play/Pause handled dynamically; set initial play image
			set_img('play_button', 'play')
			set_img('stop_button', 'stop')

		# Optional background image for the window (Level 2)
		bg_rel = window.get('background') if isinstance(window, dict) else None
		if bg_rel and self.skin_dir is not None:
			try:
				bg_path = self.skin_dir / bg_rel
				canvas = self.widgets.get('bg_canvas')
				if not canvas:
					canvas = Canvas(self.root, highlightthickness=0, bd=0)
					canvas.place(x=0, y=0, relwidth=1, relheight=1)
					self.widgets['bg_canvas'] = canvas
				img = PhotoImage(file=str(bg_path))
				canvas.bg_img = img
				canvas.delete('all')
				canvas.create_image(0, 0, anchor='nw', image=img)
				canvas.lower()  # behind everything
			except Exception:
				pass

# Initialize Pygame
pygame.mixer.init()

# Internal storage for full paths aligned with playlist_box indices
playlist_paths = []

# Cache for song lengths to avoid per-second disk I/O
song_lengths = {}

# Flag to indicate the user is scrubbing the time slider
is_scrubbing = False


def get_song_length(path):
	"""Return song length in seconds (float), cached to avoid repeated disk reads."""
	if path in song_lengths:
		return song_lengths[path]
	try:
		length = MP3(path).info.length
	except Exception:
		length = 0
	song_lengths[path] = length
	return length

# Helper to enable/disable back/forward buttons based on current selection

def update_nav_buttons():
	try:
		# Ensure UI elements exist
		if 'playlist_box' not in globals() or 'back_button' not in globals() or 'forward_button' not in globals():
			return
		n = playlist_box.size()
		state_back = NORMAL
		state_forward = NORMAL
		if n <= 1:
			# With 0 or 1 items, nothing to navigate
			state_back = DISABLED
			state_forward = DISABLED
		else:
			selection = playlist_box.curselection()
			if not selection:
				# No selection: allow both by default for 2+ items
				state_back = NORMAL
				state_forward = NORMAL
			else:
				idx = selection[0]
				state_back = DISABLED if idx == 0 else NORMAL
				state_forward = DISABLED if idx == n - 1 else NORMAL
		back_button.config(state=state_back)
		forward_button.config(state=state_forward)
	except Exception:
		pass

# Helper to fetch themed images with fallback
def themed_image(key, fallback_img):
	try:
		_theme = globals().get('THEME')
		# If the theme uses text buttons, handle play/pause by setting text and clearing image
		if _theme and getattr(_theme, 'use_text_buttons', False) and key in ('play', 'pause'):
			labels = getattr(_theme, 'controls', {}).get('button_text', {}) if hasattr(_theme, 'controls') else {}
			default_map = {'play': 'P', 'pause': 'II'}
			text = labels.get(key, default_map.get(key, ''))
			try:
				# Set text and clear image directly; caller will set image=None
				play_button.config(text=text, image='')
				play_button.image = None
			except Exception:
				pass
			return None
		if _theme and hasattr(_theme, 'images'):
			return _theme.images.get(key, fallback_img)
		return fallback_img
	except Exception:
		return fallback_img

# Create Function To Deal With Time
def play_time():
	# Check to see if song is stopped
	if stopped:
		return

	# Get the currently selected index and resolve full path
	selection = playlist_box.curselection()
	if not selection:
		return
	index = selection[0]
	if index < 0 or index >= len(playlist_paths):
		return
	song_path = playlist_paths[index]
	
	# Get Current Song Length from cache
	global song_length
	song_length = get_song_length(song_path)
	# Convert to time format
	converted_song_length = time.strftime('%M:%S', time.gmtime(song_length))
	
	# Use the slider as the single source of truth to avoid jitter/backward jumps
	current_sec = int(song_slider.get())

	# Check to see if song is over -> auto-advance if possible
	if current_sec >= int(song_length) and int(song_length) > 0:
		size = playlist_box.size()
		if index < size - 1:
			# Advance to the next track
			next_song()
			# Schedule next tick and return
			status_bar.after(1000, play_time)
			return
		else:
			# Last track: stop
			stop()
			return

	# If the user is scrubbing, only update the status (preview) and don't move the slider
	if is_scrubbing:
		converted_current_time = time.strftime('%M:%S', time.gmtime(current_sec))
		status_bar.config(text=f'Time Elapsed: {converted_current_time} of {converted_song_length}  ')
		status_bar.after(1000, play_time)
		return

	if paused:
		# If paused, freeze the display at the current slider position
		converted_current_time = time.strftime('%M:%S', time.gmtime(current_sec))
		status_bar.config(text=f'Time Elapsed: {converted_current_time} of {converted_song_length}  ')
	else:
		# Move slider along 1 second at a time
		next_time = current_sec + 1
		# Clamp to song length bounds
		if next_time > int(song_length):
			next_time = int(song_length)
		# Output new time value to slider, and to length of song
		song_slider.config(to=song_length, value=next_time)
		# Convert Slider position to time format
		converted_current_time = time.strftime('%M:%S', time.gmtime(next_time))
		# Output slider time
		status_bar.config(text=f'Time Elapsed: {converted_current_time} of {converted_song_length}  ')
	
	# Create Loop To Check the time every second
	status_bar.after(1000, play_time)

# Create Function To Add One Song To Playlist
def add_song():
	song = filedialog.askopenfilename(title="Choose A Song", filetypes=(("mp3 Files", "*.mp3" ), ))
	if not song:
		return
	# Display only filename without extension, store full path separately
	display_name = os.path.splitext(os.path.basename(song))[0]
	playlist_box.insert(END, display_name)
	playlist_paths.append(song)
	# Update nav buttons after adding
	try:
		update_nav_buttons()
	except Exception:
		pass

# Create Function To Add Many Songs to Playlist
def add_many_songs():
	songs = filedialog.askopenfilenames(title="Choose Songs", filetypes=(("mp3 Files", "*.mp3" ), ))
	
	# Loop through selected songs and add display names while storing full paths
	for song in songs:
		if song:
			display_name = os.path.splitext(os.path.basename(song))[0]
			playlist_box.insert(END, display_name)
			playlist_paths.append(song)
	# Update nav buttons after adding many
	try:
		update_nav_buttons()
	except Exception:
		pass

# Create Function To Delete One Song From Playlist
def delete_song():
	# Delete Highlighted Song From Playlist and keep paths in sync
	selection = playlist_box.curselection()
	if not selection:
		return
	index = selection[0]
	playlist_box.delete(index)
	if 0 <= index < len(playlist_paths):
		playlist_paths.pop(index)
	# Update nav buttons after deletion
	try:
		update_nav_buttons()
	except Exception:
		pass

# Create Function To Delete All Songs From Playlist
def delete_all_songs():
	# Delete ALL songs 
	playlist_box.delete(0, END)
	playlist_paths.clear()
	# Update nav buttons after clearing all
	try:
		update_nav_buttons()
	except Exception:
		pass

# Create Play Function
def play():
	global stopped, paused
	# Toggle behavior: if something is already playing or paused, toggle pause/unpause
	if pygame.mixer.music.get_busy():
		if paused:
			# Resume
			pygame.mixer.music.unpause()
			paused = False
			stopped = False
			# Update play button to show pause icon while playing
			try:
				img = themed_image('pause', pause_btn_img)
				play_button.config(image=img)
				play_button.image = img
			except Exception:
				pass
			try:
				update_nav_buttons()
			except Exception:
				pass
			return
		else:
			# Pause current playback
			pygame.mixer.music.pause()
			paused = True
			# Update play button to show play icon when paused
			try:
				img = themed_image('play', play_btn_img)
				play_button.config(image=img)
				play_button.image = img
			except Exception:
				pass
			try:
				update_nav_buttons()
			except Exception:
				pass
			return

	# If not busy, but we believe it's paused (edge case), try to unpause
	if paused:
		try:
			pygame.mixer.music.unpause()
			paused = False
			stopped = False
			# Update play button to show pause icon while playing
			try:
				img = themed_image('pause', pause_btn_img)
				play_button.config(image=img)
				play_button.image = img
			except Exception:
				pass
			try:
				update_nav_buttons()
			except Exception:
				pass
			return
		except Exception:
			pass

	# Otherwise start playing the selected song
	stopped = False
	# Get full path of the selected song via index mapping
	selection = playlist_box.curselection()
	if not selection:
		return
	index = selection[0]
	if index < 0 or index >= len(playlist_paths):
		return
	song_path = playlist_paths[index]
	
	#Load song with pygame mixer
	pygame.mixer.music.load(song_path)
	#Play song with pygame mixer
	pygame.mixer.music.play(loops=0)
	paused = False
	# Update play button to show pause icon while playing
	try:
		img = themed_image('pause', pause_btn_img)
		play_button.config(image=img)
		play_button.image = img
	except Exception:
		pass
	# Update nav buttons state
	try:
		update_nav_buttons()
	except Exception:
		pass

	# Get Song Time
	play_time()

# Create Stopped Variable
global stopped
stopped = False 
def stop():
	# Stop the song
	pygame.mixer.music.stop()
	# Clear Playlist Bar
	playlist_box.selection_clear(ACTIVE)

	status_bar.config(text='')

	# Set our slider to zero
	song_slider.config(value=0)

	# Set Stop Variable To True
	global stopped, paused
	stopped = True
	paused = False
	# Update play button to show play icon when stopped
	try:
		img = themed_image('play', play_btn_img)
		play_button.config(image=img)
		play_button.image = img
	except Exception:
		pass
	# Update nav buttons after stop (selection cleared)
	try:
		update_nav_buttons()
	except Exception:
		pass


	
# Create Function To Play The Next Song
def next_song():
	# Reset Slider position and status bar
	status_bar.config(text='')
	song_slider.config(value=0)

	#Get current song number
	next_one = playlist_box.curselection()
	if not next_one:
		return
	# Add One To The Current Song Number Tuple/list
	next_one = next_one[0] + 1

	# Resolve next song full path from mapping
	if next_one < 0 or next_one >= len(playlist_paths):
		return
	song_path = playlist_paths[next_one]
	#Load song with pygame mixer
	pygame.mixer.music.load(song_path)
	#Play song with pygame mixer
	pygame.mixer.music.play(loops=0)
	# Ensure not paused when moving to the next song
	global paused
	paused = False
	# Update play button to show pause icon while playing
	try:
		img = themed_image('pause', pause_btn_img)
		play_button.config(image=img)
		play_button.image = img
	except Exception:
		pass

	# Clear Active Bar in Playlist
	playlist_box.selection_clear(0, END)

	# Move active bar to next song
	playlist_box.activate(next_one)

	# Set Active Bar To next song
	playlist_box.selection_set(next_one, last=None)
	# Update nav buttons after moving to next
	try:
		update_nav_buttons()
	except Exception:
		pass

# Create function to play previous song
def previous_song():
	# Reset Slider position and status bar
	status_bar.config(text='')
	song_slider.config(value=0)

	#Get current song number
	next_one = playlist_box.curselection()
	if not next_one:
		return
	# Subtract One To Move To The Previous Song
	next_one = next_one[0] - 1

	# Resolve previous song full path from mapping
	if next_one < 0 or next_one >= len(playlist_paths):
		return
	song_path = playlist_paths[next_one]
	#Load song with pygame mixer
	pygame.mixer.music.load(song_path)
	#Play song with pygame mixer
	pygame.mixer.music.play(loops=0)
	# Ensure not paused when moving to the previous song
	global paused
	paused = False
	# Update play button to show pause icon while playing
	try:
		img = themed_image('pause', pause_btn_img)
		play_button.config(image=img)
		play_button.image = img
	except Exception:
		pass

	# Clear Active Bar in Playlist
	playlist_box.selection_clear(0, END)

	# Move active bar to previous song
	playlist_box.activate(next_one)

	# Set Active Bar To previous song
	playlist_box.selection_set(next_one, last=None)
	# Update nav buttons after moving to previous
	try:
		update_nav_buttons()
	except Exception:
		pass


# Create Paused Variable
global paused 
paused = False

# Create Pause Function
def pause(is_paused):
	global paused
	paused = is_paused

	if paused:
		#Unpause
		pygame.mixer.music.unpause()
		paused = False
	else:
		#Pause
		pygame.mixer.music.pause()
		paused = True

#Create Volume Function
def volume(x):
	pygame.mixer.music.set_volume(volume_slider.get())

# Create a Slide Function For Song Positioning
def slide(x):
	# Legacy function retained for compatibility; no-op to avoid feedback loop
	return


def on_scrub_start(event):
	"""Mark that the user started scrubbing; don't play while dragging."""
	global is_scrubbing
	is_scrubbing = True


def on_seek_release(event):
	"""Seek to the position set on the slider when the user releases the mouse."""
	global is_scrubbing, paused
	is_scrubbing = False
	selection = playlist_box.curselection()
	if not selection:
		return
	index = selection[0]
	if index < 0 or index >= len(playlist_paths):
		return
	target = int(song_slider.get())
	# Try seeking without reloading to avoid stutter; if it fails, reload then seek
	try:
		pygame.mixer.music.play(loops=0, start=target)
	except Exception:
		try:
			song_path = playlist_paths[index]
			pygame.mixer.music.load(song_path)
			pygame.mixer.music.play(loops=0, start=target)
		except Exception:
			return
	paused = False
	try:
		img = themed_image('pause', pause_btn_img)
		play_button.config(image=img)
		play_button.image = img
	except Exception:
		pass


# Create main Frame
main_frame = Frame(root)
main_frame.pack(pady=20)

# Create Playlist Box
playlist_box = Listbox(main_frame, bg="black", fg="green", width=60, selectbackground="green", selectforeground='black')
playlist_box.grid(row=0, column=0)
# Update navigation buttons when selection changes
playlist_box.bind('<<ListboxSelect>>', lambda e: update_nav_buttons())

# Create volume slider frame
volume_frame = LabelFrame(main_frame, text="Volume")
volume_frame.grid(row=0, column=1, padx=20)

# Create Volume Slider (inverted so bottom = mute, top = max)
volume_slider = ttk.Scale(volume_frame, from_=1, to=0, orient=VERTICAL, length=125, value=1, command=volume)
volume_slider.pack(pady=10)

# Create Song Slider
song_slider = ttk.Scale(main_frame, from_=0, to=100, orient=HORIZONTAL, length=360, value=0)
song_slider.grid(row=2, column=0, pady=20)
# Bind scrubbing start/end to avoid feedback loop
song_slider.bind('<ButtonPress-1>', lambda e: on_scrub_start(e))
song_slider.bind('<ButtonRelease-1>', lambda e: on_seek_release(e))

# Define Button Images For Controls (resolve robust paths)
base_dir = os.path.dirname(os.path.abspath(__file__))
back_btn_img = PhotoImage(file=os.path.join(base_dir, 'images', 'back50.png'))
forward_btn_img = PhotoImage(file=os.path.join(base_dir, 'images', 'forward50.png'))
play_btn_img = PhotoImage(file=os.path.join(base_dir, 'images', 'play50.png'))
pause_btn_img = PhotoImage(file=os.path.join(base_dir, 'images', 'pause50.png'))
stop_btn_img = PhotoImage(file=os.path.join(base_dir, 'images', 'stop50.png'))


# Create Button Frame
control_frame = Frame(main_frame)
control_frame.grid(row=1, column=0, pady=20)

# Create Play/Stop etc Buttons
back_button = Button(control_frame, image=back_btn_img, borderwidth=0, command=previous_song)
forward_button = Button(control_frame, image=forward_btn_img, borderwidth=0, command=next_song)
play_button = Button(control_frame, image=play_btn_img, borderwidth=0, command=play)
stop_button = Button(control_frame, image=stop_btn_img, borderwidth=0, command=stop)

back_button.grid(row=0, column=0, padx=10)
forward_button.grid(row=0, column=1, padx=10)
play_button.grid(row=0, column=2, padx=10)
stop_button.grid(row=0, column=3, padx=10)

# Initialize nav buttons state on startup
try:
	update_nav_buttons()
except Exception:
	pass

# Create Main Menu
my_menu = Menu(root)
root.config(menu=my_menu)

# Create Add Song Menu Dropdows
add_song_menu = Menu(my_menu, tearoff=0)
my_menu.add_cascade(label="Add Songs", menu=add_song_menu)
# Add One Song To Playlist
add_song_menu.add_command(label="Add One Song To Playlist", command=add_song)
# Add Many Songs to Playlist
add_song_menu.add_command(label="Add Many Songs To Playlist", command=add_many_songs)

# Create Delete Song Menu Dropdowns
remove_song_menu = Menu(my_menu, tearoff=0)
my_menu.add_cascade(label="Remove Songs", menu=remove_song_menu)
remove_song_menu.add_command(label="Delete A Song From Playlist", command=delete_song)
remove_song_menu.add_command(label="Delete All Songs From Playlist", command=delete_all_songs)

# Create Status Bar
status_bar = Label(root, text='', bd=1, relief=GROOVE, anchor=E)
status_bar.pack(fill=X, side=BOTTOM, ipady=2)

# Theme wiring (after widgets exist)
widgets = {
	'playlist_box': playlist_box,
	'main_frame': main_frame,
	'control_frame': control_frame,
	'volume_frame': volume_frame,
	'volume_slider': volume_slider,
	'song_slider': song_slider,
	'status_bar': status_bar,
	'back_button': back_button,
	'forward_button': forward_button,
	'play_button': play_button,
	'stop_button': stop_button,
}
THEME = ThemeManager(root, widgets)
# Load default skin; ignore failure to keep app working
try:
	THEME.load_skin('default')
except Exception as e:
	print('Skin load failed:', e)

# Skins menu to switch at runtime
skins_menu = Menu(my_menu, tearoff=0)
my_menu.add_cascade(label="Skins", menu=skins_menu)
# Discover available skins in ./skins
try:
	skins_dir = Path(__file__).parent / 'skins'
	available_skins = [p.name for p in skins_dir.iterdir() if p.is_dir()]
	if not available_skins:
		available_skins = ['default']
except Exception:
	available_skins = ['default']
for skin in available_skins:
	skins_menu.add_command(label=skin.title(), command=lambda s=skin: THEME.load_skin(s))





root.mainloop()