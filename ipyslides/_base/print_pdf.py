"""
Author Notes: Classes in this module should only be instantiated in LiveSlide class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

import os 
from time import sleep
import itertools
from contextlib import contextmanager

from PIL import ImageGrab
import matplotlib.pyplot as plt

from .. import data_variables as dv
from ..writers import write


class PdfPrint:
    def __init__(self, _instanceWidgets):
        "Both instnaces should be inside `LiveSlide` class."
        self.widgets = _instanceWidgets
        self.btn_print = self.widgets.buttons.print
        self.btn_pdf = self.widgets.buttons.pdf
        self.btn_png = self.widgets.buttons.png
        self.btn_capture = self.widgets.buttons.capture
        self.btn_setting = self.widgets.buttons.setting
        self.bbox_input = self.widgets.inputs.bbox
        
        self.__images = {} #Store screenshots
        self.__print_settings = {'load_time':0.5,'quality':100,'bbox':None}
        
        self.btn_print.on_click(self.__print_pdf)
        self.btn_capture.on_click(self.capture_screen)
        self.btn_pdf.on_click(self.__save_pdf)
        self.btn_png.on_click(self.__save_images)
        self.btn_print.on_click(self.__print_pdf)
        self.widgets.ddowns.clear.observe(self.__clear_images)
        self.bbox_input.on_submit(self.__set_bbox)
    
    def __set_bbox(self,change):
        bbox = [int(v) for v in self.bbox_input.value.split(',')][:4]    
        print_settings = {**self.get_print_settings(), 'bbox':bbox}
        with self.widgets.outputs.intro:
            self.widgets.outputs.intro.clear_output(wait=True)
            self.set_print_settings(**print_settings)
            write(dv.settings_instructions) 
        self.widgets._push_toast(f'See Screenshot of your selected bbox = {bbox} 👇')
        
    @contextmanager
    def __print_context(self):
        hide_widgets = [self.widgets.controls,
                        self.widgets.buttons.setting,
                        self.btn_capture,
                        self.widgets.sliders.visible,
                        self.widgets.htmls.toast,
                        self.widgets.htmls.cursor
                        ]
        old_pref = self.widgets.htmls.toast.layout.visibility # To keep user prefernce back after screenshot
        for w in hide_widgets:
            w.layout.visibility = 'hidden'
        try:    
            yield
        finally:
            for w in hide_widgets:
                w.layout.visibility = 'visible' 
            self.widgets.htmls.toast.layout.visibility = old_pref 
                
    def screen_bbox(self):
        "Return screen's bounding box on windows, return None on other platforms which works as full screen too in screenshot."
        try:
            import ctypes
            user = ctypes.windll.user32
            user.SetProcessDPIAware()
            return (0, 0, user.GetSystemMetrics(0), user.GetSystemMetrics(1))
        except:
            return None

    def set_print_settings(self,load_time=0.5,quality=95,bbox = None):
        """Print settings. 
        - load_time: 0.5; time in seconds for each slide to load before print, only applied to Print PDF, not on manual screenshot. 
        - quality: 95; In term of current screen. Will not chnage too much above 95. 
        - bbox: None; None for full screen on any platform. Given screen position of slides in pixels as [left,top,right,bottom].
        > Note: Auto detection of bbox in frontends where javascript runs is under progress. """
        if bbox and len(bbox) != 4:
            return print("bbox expects [left,top,right,bottom] in integers")
        self.__print_settings = {'load_time':load_time,'quality':quality,'bbox':bbox if bbox else self.screen_bbox()} # better to get on windows
        # Display what user sets
        if bbox:
            img = ImageGrab.grab(bbox=bbox)
            _ = plt.figure(figsize = (3, 3*img.height/img.height), dpi=720) # For clear view
            _ = plt.imshow(img)
            plt.gca().set_axis_off()
            plt.subplots_adjust(left=0,bottom=0,top=1,right=1)
            plt.show() # Display in Output widget too.     
    
    def get_print_settings(self):
        return self.__print_settings    
    
    def __set_resolution(self,image):
        "Returns resolution to make PDF printable on letter/A4 page."
        w, h = image.size
        short, res = (h, w/11) if w > h else (w, h/11) # letter page size landscape else portrait
        
        if short/res > 8.25: # if short side out of page, bring inside A4 size so work for both A4/Letter
            return short/8.25  # change resolution to shrink pages size to fit for print,long side already inside page
        
        return res   # Return previous resolution
    
    def capture_screen(self,btn):
        "Saves screenshot of current slide into self.__images dictionary when corresponding button clicked. Use in fullscreen mode"
        with self.__print_context():
            sleep(0.05) # Just for above clearance of widgets views
            img = ImageGrab.grab(bbox=self.__print_settings['bbox']) 
        for i in itertools.count():
            if not f'im-{self.widgets.sliders.progress.value}-{i}' in self.__images:
                self.__images[f'im-{self.widgets.sliders.progress.value}-{i}'] =  img 
                return # Exit loop
    
    def __sort_images(self):
        ims = [] #sorting
        for i in range(self.widgets.sliders.progress.max + 1): # That's maximum number of slides
            for j in range(len(self.__images)): # To be on safe side, no idea how many captures
                if f'im-{i}-{j}' in self.__images:
                    ims.append(self.__images[f'im-{i}-{j}'])
        return tuple(ims)
            
    def save_pdf(self,filename='IPySlides.pdf'):
        "Converts saved screenshots to PDF!"
        ims = self.__sort_images()    
        if ims: # make sure not empty
            self.btn_pdf.description = 'Generatingting PDF...'
            ims[0].save(filename,'PDF',quality= self.__print_settings['quality'] ,save_all=True,append_images=ims[1:],
                        resolution=self.__set_resolution(ims[0]),subsampling=0)
            self.btn_pdf.description = 'Save PDF'
            self.widgets._push_toast(f'File "{filename}" is created')
        else:
            self.widgets._push_toast('No images found to convert. Take screenshots of slides, then use this option.')
    
    def __save_pdf(self,btn):
        self.save_pdf() # Runs on button
        
    def __print_pdf(self,btn):
        "Quick Print"
        self.btn_setting.click() # Close side panel
        imgs = []
        for i in range(self.widgets.sliders.progress.max + 1):  
            with self.__print_context():
                self.widgets.sliders.progress.value = i #keep inside context manger to avoid slide transitions
                sleep(self.__print_settings['load_time']) #keep waiting here until it almost loads 
                imgs.append(ImageGrab.grab(bbox=self.__print_settings['bbox']))
                  
        if imgs:
            imgs[0].save('IPySlides-Print.pdf','PDF',quality= self.__print_settings['quality'],save_all=True,append_images=imgs[1:],
                         resolution=self.__set_resolution(imgs[0]),subsampling=0)
            self.widgets._push_toast("File 'IPySlides-Print.pdf' saved.") 
        # Clear images at end
        for img in imgs:
            img.close()    
    
    @property
    def screenshots(self):
        "Get all captured screenshots in order."
        return self.__sort_images()
    
    def save_images(self,directory='ipyslides-images'):
        "Save all screenshots as PNG in given `directory`. Names are auto ordered"
        self.btn_png.description = 'Saving PNGs...'
        if not os.path.isdir(directory):
            os.mkdir(directory)
        
        ims = self.screenshots
        if ims:    
            for i,im in enumerate(ims):
                im.save(os.path.join(directory,f'Slide-{i:03}.png'),'PNG',quality= self.__print_settings['quality'],subsampling=0,optimize=True)  # Do not lose image quality at least here
            md_file = os.path.join(directory,'Make-PPT.md')
            with open(md_file,'w') as f:
                f.write(dv.how_to_ppt)
            self.widgets._push_toast(f'''All captured images are saved in "{directory}"<br/> 
                         <em>See file "{md_file}" as bonus option!</em>''',timeout=10)
        else:
            self.widgets._push_toast('No images found to save. Take screenshots of slides, then use this option.')
        
        self.btn_png.description = 'Save PNG'
        
    def __save_images(self,btn):
        "With Button call"
        self.save_images()
    
    def __clear_images(self,change):
        if 'Current' in self.dd_clear.value:
            self.__images = {k:v for k,v in self.__images.items() if f'-{self.widgets.sliders.progress.value}-' not in k}
            for k,img in self.__images.items():
                if f'-{self.widgets.sliders.progress.value}-' in k:
                    img.close() # Close image to save mememory
            self.widgets._push_toast('Deleted screenshots of current slide')
        elif 'All' in self.dd_clear.value:
            for k,img in self.__images.items():
                img.close() # Close image to save mememory
            self.__images = {} # Cleaned up
            self.widgets._push_toast('Deleted screenshots of all slides')
        
        self.dd_clear.value = 'None' # important to get back after operation
    