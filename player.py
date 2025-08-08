from tkinter import *
from tkinter import filedialog
import pygame
import time
from mutagen.mp3 import MP3
import tkinter.ttk as ttk
import os

root = Tk()

root.title("MP3 Player")
root.geometry("500x400")

# Initialize Pygame
pygame.mixer.init()

# Internal storage for full paths aligned with playlist_box indices
playlist_paths = []

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
	
	# Find Current Song Length
	song_mut = MP3(song_path)
	global song_length
	song_length = song_mut.info.length
	# Convert to time format
	converted_song_length = time.strftime('%M:%S', time.gmtime(song_length))
	
	# Use the slider as the single source of truth to avoid jitter/backward jumps
	current_sec = int(song_slider.get())

	# Check to see if song is over
	if current_sec >= int(song_length):
		stop()
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
				play_button.config(image=pause_btn_img)
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
				play_button.config(image=play_btn_img)
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
				play_button.config(image=pause_btn_img)
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
		play_button.config(image=pause_btn_img)
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
		play_button.config(image=play_btn_img)
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
		play_button.config(image=pause_btn_img)
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
		play_button.config(image=pause_btn_img)
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
	# Resolve full path from selected index
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
	pygame.mixer.music.play(loops=0, start=song_slider.get())
	# Ensure not paused after seeking
	global paused
	paused = False
	# Update play button to show pause icon while playing
	try:
		play_button.config(image=pause_btn_img)
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

# Create Volume Slider
volume_slider = ttk.Scale(volume_frame, from_=0, to=1, orient=VERTICAL, length=125, value=1, command=volume)
volume_slider.pack(pady=10)

# Create Song Slider
song_slider = ttk.Scale(main_frame, from_=0, to=100, orient=HORIZONTAL, length=360, value=0, command=slide)
song_slider.grid(row=2, column=0, pady=20)

# Define Button Images For Controls
back_btn_img = PhotoImage(file='images/back50.png')
forward_btn_img = PhotoImage(file='images/forward50.png')
play_btn_img = PhotoImage(file='images/play50.png')
pause_btn_img = PhotoImage(file='images/pause50.png')
stop_btn_img = PhotoImage(file='images/stop50.png')


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


# Temporary Label
my_label = Label(root, text='')
my_label.pack(pady=20)




root.mainloop()