"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

import os 
from time import sleep
from contextlib import contextmanager, suppress

from PIL import Image, ImageGrab

from ..utils import image, get_child_dir
from ..writer import CustomDisplay


class ScreenShot:
    def __init__(self, _instanceWidgets):
        "Instnace should be inside `Slides` class."
        self.widgets = _instanceWidgets
        self.btn_cap_all = self.widgets.buttons.cap_all
        self.btn_pdf = self.widgets.buttons.pdf
        self.btn_crop = self.widgets.buttons.crop
        self.btn_capture = self.widgets.buttons.capture
        self.btn_settings = self.widgets.buttons.setting
        
        self.__images = {} #Store screenshots
        self._cimage = None # cureent image
        self._crop_bbox = None
        self.__capture_settings = {'load_time':0.8,'quality':95}
        self._capturing = False
        
        self.btn_capture.on_click(self.capture)
        self.btn_pdf.on_click(self.__save_pdf)
        self.btn_cap_all.on_click(self.__capture_all)
        self.btn_crop.on_click(self.__toggle_crop_window)
        self.widgets.ddowns.clear.observe(self.__clear_images)
        self.widgets.sliders.crop_w.observe(self._crop_image, names="value")
        self.widgets.sliders.crop_h.observe(self._crop_image, names="value")

        with suppress(BaseException): # only on supportive systems silently
            im = ImageGrab.grab()
            self.widgets.sliders.crop_w.max = im.width
            self.widgets.sliders.crop_w.value = (0, im.width)
            self.widgets.sliders.crop_h.max = im.height
            self.widgets.sliders.crop_h.value = (0, im.height)

    def __toggle_crop_window(self, btn):
        if self.widgets.cropbox.layout.height == '0':
            self.widgets.cropbox.layout.height = '100%'
            self.btn_crop.description = 'Close'
            if self.__images:
                self._load_image(self.images[0]) # load from ordered images
            else:
                self.widgets.htmls.crop.value = 'Screenshot appears here for cropping!'
        else:
            self.widgets.cropbox.layout.height = '0'
            self.btn_crop.description = 'Set Crop Bounding Box'
    
    def _load_image(self, im):
        self._cimage = im
        self.widgets.htmls.crop.value = image(im,width='100%').value

    def _crop_image(self, change):
        if self._cimage is not None:
            x1,x2 = self.widgets.sliders.crop_w.value
            y2,y1 = [self.widgets.sliders.crop_h.max - v for v in self.widgets.sliders.crop_h.value]
            self._crop_bbox = [x1,y1,x2,y2]
            self.widgets.htmls.crop.value = image(self._cimage.crop([x1,y1,x2,y2]), width='100%').value
        elif self.__images:
            self._load_image(self.images[0]) 

    @contextmanager
    def capture_mode(self, *additional_widgets_to_hide):
        """Hide some widgets and while capturing a screenshot, show them back again.
        You can provide additional widgets to hide while capturing as well."""
        hide_widgets = [self.widgets.controls, # now other buttons are inside Menu-Box which gets hidden 
                        self.widgets.htmls.toast,
                        self.widgets.htmls.cursor,
                        *additional_widgets_to_hide
                        ]
        old_pref = self.widgets.htmls.toast.layout.visibility # To keep user prefernce back after screenshot
        for w in hide_widgets:
            w.layout.visibility = 'hidden'
        try:  
            self.widgets.mainbox.add_class('CaptureMode') # Used to hide other things on slide  
            self._capturing = True # Must be for main class to know
            yield
        finally:
            self.widgets.mainbox.remove_class('CaptureMode')
            self._capturing = False # Back to normal
            for w in hide_widgets:
                w.layout.visibility = 'visible' 
            self.widgets.htmls.toast.layout.visibility = old_pref 

    def capture_setup(self,load_time=0.5,quality=95):
        """Setting for screen capture. 
        - load_time: 0.5; time in seconds for each slide to load before print. 
        - quality: 95; In term of current screen. Will not chnage too much above 95."""
        if load_time < 0.1:
            return print("load_time must be greater than 0.1 to at least load the slide")
        
        self.__capture_settings = {'load_time':load_time,'quality':quality} 

    @property  
    def capture_settings(self):
        "See the settings applied for screenshot. Use `self.capture_setup` function to adjust settings."
        return self.__capture_settings    
    
    def __set_resolution(self,image):
        "Returns resolution to make PDF printable on letter/A4 page."
        w, h = image.size
        short, res = (h, w/11) if w > h else (w, h/11) # letter page size landscape else portrait
        
        if short/res > 8.25: # if short side out of page, bring inside A4 size so work for both A4/Letter
            return short/8.25  # change resolution to shrink pages size to fit for print,long side already inside page
        
        return res   # Return previous resolution
    
    def capture(self,btn):
        "Saves screenshot of current slide into self.__images dictionary when corresponding button clicked. Use in fullscreen mode or set bbox using `.capture_setup`."
        with self.capture_mode():
            sleep(0.05) # Just for above clearance of widgets views
            if self.widgets.sliders.progress.label not in self.__images:
                self.__images[self.widgets.sliders.progress.label] = [] # container to store images
            
            self._cimage = ImageGrab.grab(bbox = None) # keep for cropping
            self.__images[self.widgets.sliders.progress.label].append(self._cimage) # Append to existing list
    
    def __sort_images(self):
        ims = [] #sorting
        for label, _ in self.widgets.sliders.progress.options:
            if label in self.__images:
                ims = [*ims,*self.__images[label]]

        ims = [im.crop(self._crop_bbox) if self._crop_bbox else im for im in ims] # crop here, not in property images
        return tuple(ims)
            
    def save_pdf(self,filename='Slides.pdf'):
        "Converts saved screenshots to PDF!"
        ims = self.__sort_images()    
        if ims: # make sure not empty
            self.btn_pdf.description = 'Generatingting PDF...'
            ims[0].save(filename,'PDF',quality= self.capture_settings['quality'] ,save_all=True,append_images=ims[1:],
                        resolution=self.__set_resolution(ims[0]),subsampling=0)
            self.btn_pdf.description = 'Save PDF'
            self.widgets._push_toast(f'File "{filename}" is created')
        else:
            self.widgets._push_toast('No images found to convert. Take screenshots of slides, then use this option.')
    
    def __save_pdf(self,btn):
        self.save_pdf() # Runs on button
        
    def __capture_all(self,btn):
        "Quickly capture all slides and save them as images."
        self.btn_settings.click() # Close side panel
        for label, _ in self.widgets.sliders.progress.options:
            with self.capture_mode():
                self.widgets.sliders.progress.label = label # swicth to that slide
                sleep(self.capture_settings['load_time']) #keep waiting here until it almost loads 
                self.__images[label] = [ImageGrab.grab(bbox = None),] # Save image in a list on which we can add others
        
        self.widgets._push_toast("All slides captured. Use Save PDF button to save them.") 
         
    
    @property
    def images(self):
        "Get all captured screenshots in order."
        return self.__sort_images()
    
    def __clear_images(self,change):
        if 'Current' in self.widgets.ddowns.clear.value:
            _how_many = [img.close() for img in self.__images.get(self.widgets.sliders.progress.label,[])] # Close image to save mememory          
            self.__images[self.widgets.sliders.progress.label] = [] # Clear images at that slide       
            
            if _how_many:
                self.widgets._push_toast(f'Deleting screenshots of current slide. {len(_how_many)} images deleted.')
            else:
                self.widgets._push_toast('No screenshots found for to delete.',timeout=2)
            
        elif 'All' in self.widgets.ddowns.clear.value:
            flat_imgs = [img for imgs in self.__images.values() for img in imgs]
            _how_many = [img.close() for img in flat_imgs] # Close image to save mememory
            if _how_many:
                self.widgets._push_toast(f'Deleting screenshots of all slides. {len(_how_many)} images deleted.')
            else:
                self.widgets._push_toast('No screenshots found for to delete.', timeout=2)
            
            self.__images = {} # Cleaned up
            
        
        self.widgets.ddowns.clear.value = 'None' # important to get back after operation
    
    
    def clipboard_image(self, filename, quality = 95, overwrite = False):
        """Save image from clipboard to file with a given quality. 
        On next run, it loads from saved file under `notebook-dir/.ipyslides-assets/clips`. 
        Useful to add screenshots from system into IPython. You can use overwite to overwrite existing file.
        You can add saved clips using a "clip:" prefix in path in `Slides.image("clip:filename.png")` function and also in markdown.
        
        - Output can be directly used in `write` command.
        - Converts to PIL image using `.to_pil()`.
        - Convert to HTML representation using `.to_html()`.
        - Convert to Numpy array using `.to_numpy()` in RGB format that you can plot later.
        """
        directory = get_child_dir('.ipyslides-assets', 'clips', create = True)
        filepath = directory / filename
        
        class ClipboardImage(CustomDisplay):
            def __init__(self, path, quality, overwrite):
                self._path = path
                
                if overwrite or (not os.path.isfile(path)):
                    im = ImageGrab.grabclipboard()
                    if isinstance(im,Image.Image):
                        im.save(path, format= im.format,quality = quality)
                        im.close() # Close image to save mememory
                    else:
                        raise ValueError('No image on clipboard/file or not supported format.')
                    
            @property
            def path(self):
                "Return path of stored image."
                return self._path
            
            @property
            def value(self):
                "Return HTML string of image."
                return self.to_html().value # String
            
            def display(self):
                return self.to_html().display() # Display HTML to have in export
            
            def to_pil(self):
                "Return PIL image."
                return Image.open(self.path)
            
            def to_html(self, **kwargs):
                "Return HTML of image, with `**kwargs` passed to `ipyslides.utils.image`."
                return image(self.path, **kwargs)
            
            def to_numpy(self):
                "Return numpy array data of image. Useful for plotting."
                import numpy # Do not import at top, as it is not a dependency
                return numpy.asarray(self.to_pil())
            
        return ClipboardImage(filepath, quality, overwrite)
        