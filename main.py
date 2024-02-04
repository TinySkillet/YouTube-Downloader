import ttkbootstrap as tb
import requests
from tkinter.filedialog import askdirectory
from datetime import datetime
from ttkbootstrap.constants import *
from ttkbootstrap.toast import ToastNotification
from PIL import Image, ImageTk, ImageSequence
from tkinter import messagebox
from pytube import YouTube
from pytube.exceptions import VideoPrivate, VideoRegionBlocked, VideoUnavailable, AgeRestrictedError, LiveStreamError, MembersOnly, RegexMatchError
from pathlib import Path
from itertools import cycle
from threading import Thread
from screeninfo import get_monitors


class MyThread(Thread):
    
    def __init__(self, target, args=(), callback=None):
        super().__init__(target=target, args=args, daemon=True)
        self._callback = callback

    def run(self):
        # The target function will be executed in the thread
        result = self._target(*self._args)
        if self._callback:
            self._callback(result)


class YTDownloader(tb.Frame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # retrieving monitor height & width in pixels
        self.screen_width = get_monitors()[0].width
        self.screen_height = get_monitors()[0].height

        original_logo = Image.open('app_logo.png')

        # scaling factor to scale images based on screen height & width
        scaling_factor = min(self.screen_width / 2880, self.screen_height / 1800)

        # resizing image
        resized_image = original_logo.resize((int(original_logo.width * scaling_factor), int(original_logo.height * scaling_factor)))

        # image to be placed at the top of frame
        self.app_logo = ImageTk.PhotoImage(resized_image)

        # min size of window
        self.master.minsize(
            width=int(self.screen_width * 0.75),
            height= int(self.screen_height * 0.75)    
        )
        self.master.resizable(True, True)

        self.header_var = tb.StringVar()
        self.pack(fill=BOTH)
        self.animation_running = True

        gif_path = Path('ripple_animation.gif')

        with Image.open(gif_path) as image:
            sequence = ImageSequence.Iterator(image)
            images = [ImageTk.PhotoImage(s) for s in sequence]
            self.image_cycle = cycle(images)
            self.framerate = image.info['duration']
        

        self.set_logo()
        self.create_header()
        self.create_search_widget()
        # self.fill_container('')


    # packing image on frame
    def set_logo(self):
        lbl = tb.Label(
            self, 
            image=self.app_logo
        )
        lbl.pack()


    def create_header(self):
        self.header_var.set('ENTER VIDEO URL')
        lbl = tb.Label(
            self,
            textvariable=self.header_var,
            padding=10,
            bootstyle=SECONDARY,
            anchor=CENTER, 
            font=('Comic Sans MS', 12)
        )
        lbl.pack(
            fill=X, 
            expand=YES, 
            pady=(0, 10)
        )


    # search entry
    def create_search_widget(self):

        frm = tb.Frame(self)
        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)

        self.search_bar = tb.Entry(
            frm,
            font=('Arial', 10),
            width=50
        )
        self.search_bar.focus_set()
        self.search_bar.grid()

        self.okbutton = tb.Button(
            frm, 
            text='  OK  ',
            command=self.ok_on_click,
        )
        self.okbutton.grid(row=0, column=1, padx=10)

        frm.pack(expand=True)



    # loading animation
    def start_loading_animation(self):
        if not self.animation_running:
            self.animation_running = True

        self.after(self.framerate, self.next_frame)
        self.image_container = tb.Label(self, image=next(self.image_cycle), anchor=CENTER)
        self.image_container.pack(fill=BOTH, expand=YES)


    def next_frame(self):
        self.image_container.configure(image=next(self.image_cycle))
        self.after(self.framerate, self.next_frame)


    def stop_loading_animation(self):
        self.animation_running = False
        if hasattr(self, 'image_container'):
            self.image_container.pack_forget()


    def get_video_details(self, yt):
        print(yt.streams.filter(progressive=True))

    

    def ok_on_click(self):
        url = self.search_bar.get().strip()

        if url == '':
            messagebox.showerror(title='Error', message=f'Please enter a valid youtube video url!')
            return

        try:
            self.yt = YouTube(url)
        
        except VideoPrivate:
            messagebox.showerror(title='Error', message=f'Unable to access {url}! The video is private.')
        
        except VideoRegionBlocked:
            messagebox.showerror(title='Error', message=f'Unable to access {url}! The video is region-blocked.')

        except AgeRestrictedError:
            messagebox.showerror(title='Error', message=f'Unable to access {url}! The video is age-restricted.')

        except LiveStreamError:
            messagebox.showerror(title='Error', message=f'Unable to access {url}! The video is a livestream.')

        except MembersOnly:
            messagebox.showerror(title='Error', message=f'Unable to access {url}! The video is for members only.')
        
        except VideoUnavailable:
            messagebox.showerror(title='Error', message=f'Video at {url} is unavailable!')

        except RegexMatchError:
            messagebox.showerror(title='Error', message=f'Invalid URL!')

        except Exception as e:
            messagebox.showerror(title='Error', message=str(e))

        else:
           self.start_loading_animation()
           self.okbutton.configure(state=DISABLED)

           self.my_thread = MyThread(
               target=self.load_video_details,
               args=(self.yt,),
               callback=self.fill_container,
           )
           self.my_thread.start()
           


    def load_video_details(self, yt: YouTube):

        streams = yt.streams.filter(progressive=True)
        self.streams = []
        for stream in streams:
            self.streams.append(stream)
    
        self.stop_loading_animation()



    def convert_time_format(self, video_length_seconds):

        seconds = video_length_seconds

        # total minutes
        minutes = seconds // 60
        
        # remaining seconds
        seconds = seconds % 60

        if minutes > 59:
            hours = minutes // 60
            
            # remaining minutes
            minutes = minutes % 60        
            if seconds == 0:
                return f'{hours}h {minutes}m'
            else:
                return f'{hours}h {minutes}m {seconds}s'
        
        elif seconds == 0:
            return f'{minutes}m'

        else:
            return f'{minutes}m {seconds}s'            



    def read_download_path(self):
        
        try:
            with open('config.txt', 'r') as f:
                download_path = f.readline().strip()

                if download_path.startswith('SAVE_DIR:'):
                    return download_path.replace('SAVE_DIR: ', '')
                else:
                    return ''
        except FileNotFoundError:
            return ''
            
            

    def save_download_path(self, path):
        
        existing_path = self.read_download_path()
        
        try:
            with open('config.txt', 'w') as w:
                if existing_path != path:
                    w.write(f'SAVE_DIR: {path}')
        except Exception as e:
            print(f"Error saving download path: {e}")
        
                
                
    def get_save_path(self):
        
        self.download_path_entry.configure(state=ACTIVE)
        
        path = askdirectory(mustexist=True, title='YT Downloader')     
        if path:   
            self.save_download_path(path)
            
            self.download_path_entry.delete(0, END)
            self.download_path_entry.insert(0, path)
        
        self.download_path_entry.configure(state=READONLY)


    def reset_screen(self):
        
        self.container.destroy()
        self.okbutton.configure(state=ACTIVE)
        
    
    def download(self):
        
        if self.read_download_path == '':
            return False
        
        selected_index = self.formats_combobox['values'].index(self.formats_combobox.get())
        stream = self.streams[selected_index]
        save_path = self.read_download_path()
        self.show_download_started_notification()
        stream.download(output_path=save_path)
        self.show_download_completed_notification()
    
    
    def show_download_started_notification(self):
        ToastNotification(
            title='Download Started',
            duration=5000,
            message=self.title,
            alert=True,
            bootstyle=DANGER
        ).show_toast()
    
    def show_download_completed_notification(self):
        ToastNotification(
            title='Download Completed',
            duration=5000,
            message=self.title,
            alert=True,
            bootstyle=DANGER
        ).show_toast()
    
    def run_download_thread(self):
        MyThread(
            target=self.download,
        ).start()
      

    def fill_container(self, _):
       
        self.container = tb.Frame(self)
        self.container.rowconfigure(0, weight=2)
        self.container.rowconfigure(1, weight=1)
        self.container.columnconfigure(0, weight=1)
        self.container.pack(fill=BOTH, expand=True)
        
        self.upper_frame = tb.LabelFrame(self.container, text='Video Information')
       
        self.upper_frame.grid(sticky=NSEW, pady=80)
        # self.upper_frame.grid_propagate(False
        
        self.upper_frame.columnconfigure(0, weight=1)
        self.upper_frame.columnconfigure(1, weight=1)
        self.upper_frame.columnconfigure(2, weight=1)
        self.upper_frame.columnconfigure(3, weight=1)
        self.upper_frame.columnconfigure(4, weight=1)
        self.upper_frame.columnconfigure(5, weight=1)
        self.upper_frame.columnconfigure(6, weight=1)

        tb.Label(
            self.upper_frame,
            text='Video Details',
            font=("Comic Sans MS", 12),
            bootstyle=(INFO, INVERSE),
            anchor=CENTER    
        ).grid(sticky=EW, padx=10, pady=10, columnspan=5)
        
        tb.Label(
            self.upper_frame,
            text='Available Formats',
            font=("Comic Sans MS", 12),
            bootstyle=(INFO, INVERSE),
            anchor=CENTER
        ).grid(sticky=EW, padx=10, pady=10, row=0, column=5, columnspan=2)
        
        # Video details
        self.title = self.yt.title
        thumbnail_url = self.yt.thumbnail_url
        author = self.yt.author
        video_duration = self.convert_time_format(self.yt.length)
        published_date = self.yt.publish_date
        published_date = published_date.strftime('%Y-%m-%d')        
        views = self.yt.views
        
        lbl_font = ('Comic Sans MS', 9)

        # Labels
        tb.Label(
            self.upper_frame,
            text='Title: ',
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=1, column=0, padx=10, pady=20, sticky="w")

        tb.Label(
            self.upper_frame,
            text='Author: ',
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=2, column=0, padx=10, pady=20, sticky="w")

        tb.Label(
            self.upper_frame,
            text='Video Duration: ',
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=3, column=0, padx=10, pady=20, sticky="w")

        tb.Label(
            self.upper_frame,
            text='Published Date: ',
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=4, column=0, padx=10, pady=20, sticky="w")

        tb.Label(
            self.upper_frame,
            text='Views: ',
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=5, column=0, padx=10, pady=20, sticky="w")
        
        
        # display title
        tb.Label(
            self.upper_frame,
            text=self.title,
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=1, column=1, columnspan=4, padx=10, pady=20, sticky="w")

        # display author
        tb.Label(
            self.upper_frame,
            text=author,
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=2, column=1, columnspan=4, padx=10, pady=20, sticky="w")

        # display video duration
        tb.Label(
            self.upper_frame,
            text=video_duration,
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=3, column=1, padx=10, pady=20, sticky="w")

        # display published date
        tb.Label(
            self.upper_frame,
            text=published_date,
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=4, column=1, padx=10, pady=20, sticky="w")

        # display views
        tb.Label(
            self.upper_frame,
            text=views,
            font=lbl_font,
            bootstyle=PRIMARY,
        ).grid(row=5, column=1, padx=10, pady=20, sticky="w")
          
          
        formats = []
        for stream in self.streams:
            format = f'{stream.resolution}{stream.fps}'
            if format not in formats:
                formats.append(format)
        
        self.formats_combobox = tb.Combobox(
            self.upper_frame, 
            values=formats,   
            state='readonly'
        )
        self.formats_combobox.current(0)
        self.formats_combobox.grid(row=1, column=5, columnspan=2)
        
        self.lower_frame = tb.LabelFrame(self.container, text='Download Options')
        self.lower_frame.grid(sticky=NSEW)
        self.lower_frame.columnconfigure(0, weight=1)
        self.lower_frame.columnconfigure(1, weight=1)
        self.lower_frame.columnconfigure(2, weight=1)
        
        tb.Label(
            self.lower_frame,
            text='Downloads folder: ',
            bootstyle=DANGER,
            font=lbl_font,
        ).grid(padx=10, pady=20, sticky=E)
        
        self.download_path_entry = tb.Entry(
            self.lower_frame,
            font=lbl_font,
            bootstyle=DARK
        )
        self.download_path_entry.grid(row=0, column=1, padx=10, pady=20, sticky=EW)
        self.download_path_entry.insert(0, self.read_download_path())
        self.download_path_entry.configure(state=READONLY)
    
        
        browse_btn = tb.Button(
            self.lower_frame,
            text=' Browse ',
            bootstyle=(PRIMARY, OUTLINE),
            command=self.get_save_path)
        
        browse_btn.grid(row=0, column=2, sticky=W)

        self.download_button = tb.Button(self.lower_frame, text=' Download ', bootstyle=INFO, command=self.run_download_thread)
        self.download_button.grid(row=1, column=1, pady=20)
        
        self.download_more_button = tb.Button(self.lower_frame, text='Download more', bootstyle=SUCCESS, command=self.reset_screen)
        self.download_more_button.grid(row=2, column=1, pady=20)
        
            
            
if __name__ == '__main__':

    app = tb.Window('YTdownloader', themename='morph', resizable=(False, False)) 
    YTDownloader(app)     
    app.mainloop()   




