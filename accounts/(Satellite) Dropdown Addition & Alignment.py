import tkinter as tk
from tkinter import Entry, OptionMenu, StringVar, ttk
from PIL import Image, ImageTk


def delete_text(event):
    if location_entry.get() == "LL":
        location_entry.delete(0, tk.END)


def on_configure(event):
    img4_resized = img4.resize((event.width, event.height))
    img4_resized = ImageTk.PhotoImage(img4_resized)
    canvas4.itemconfig(chng2, image=img4_resized)


def on_canvas_resize(event):
    gui.geometry(f"{event.width}x{event.height}")


# Creating tkinter window
window = tk.Tk()
window.title("PlannerX Settings")

# Creating frame
frame = tk.Frame(window)
frame.pack(padx=20, pady=20)

# Creating label and entry for solar sail 1
label1 = tk.Label(frame, text="Solar Sail 1:")
label1.grid(row=0, column=0)

entry1 = Entry(frame, width=5)
entry1.grid(row=0, column=1)

# Creating label and entry for solar sail 2
label2 = tk.Label(frame, text="Solar Sail 2:")
label2.grid(row=1, column=0)

entry2 = Entry(frame, width=5)
entry2.grid(row=1, column=1)

# Creating label and entry for satellite drop-down addition
label3 = tk.Label(frame, text="Satellite:")
label3.grid(row=2, column=0)

satellite_dropdown_values = ["LL", "HH", "HL", "LH"]
satellite_dropdown_val = StringVar()
satellite_dropdown = OptionMenu(
    frame, satellite_dropdown_val, *satellite_dropdown_values)
satellite_dropdown.grid(row=2, column=1)

# Creating label and entry for location reference
label4 = tk.Label(frame, text="Location Reference:")
label4.grid(row=3, column=0)

location_entry = Entry(frame, width=5)
location_entry.grid(row=3, column=1)
location_entry.insert(0, "LL")

location_entry.bind("<FocusIn>", delete_text)

# Creating frame for buttons
button_frame = tk.Frame(window)
button_frame.pack(padx=20, pady=20)

# Creating button
button = tk.Button(button_frame, text="Save")
button.pack(side=tk.RIGHT)

# UI image
gui = tk.Tk()
gui.geometry('1250x1080')
gui.config(bg="grey")
gui.title('Planner X - Developer 1.0.1')

canvas4 = tk.Canvas(gui, width=1535, height=1100,
                    bg="Black", bd=0, highlightthickness=0)
canvas4.pack()

# Replace with the correct path
img4 = Image.open("C:/Users/91965/Downloads/Satellite.png")
img4_resized = img4.resize((1535, 800))
img4 = ImageTk.PhotoImage(img4_resized)

chng2 = canvas4.create_image(0, 0, anchor=tk.NW, image=img4)

node_map1_val = StringVar()
node_map1 = ttk.OptionMenu(canvas4, node_map1_val, "", *["a", "b", "c"])
node_map1.config(width=18)
node_map1.place(x=100, y=100)

canvas4.bind('<Configure>', on_configure)
canvas4.bind('<Configure>', on_canvas_resize)

window.mainloop()
