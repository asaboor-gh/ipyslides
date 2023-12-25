"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

import os 
from time import sleep
from contextlib import contextmanager

from PIL import Image, ImageGrab

from ..utils import image
from ..writer import CustomDisplay
from . import intro


class ScreenShot:
    def __init__(self, _instanceWidgets):
        "Instnace should be inside `Slides` class."
        self.widgets = _instanceWidgets
        self.btn_cap_all = self.widgets.buttons.cap_all
        self.btn_pdf = self.widgets.buttons.pdf
        self.btn_png = self.widgets.buttons.png
        self.btn_capture = self.widgets.buttons.capture
        self.btn_settings = self.widgets.buttons.setting
        self.bbox_input = self.widgets.inputs.bbox
        
        self.__images = {} #Store screenshots
        self.__capture_settings = {'load_time':0.8,'quality':95,'bbox':None}
        self.capturing = False
        
        self.btn_capture.on_click(self.capture)
        self.btn_pdf.on_click(self.__save_pdf)
        self.btn_png.on_click(self.__save_images)
        self.btn_cap_all.on_click(self.__capture_all)
        self.widgets.ddowns.clear.observe(self.__clear_images)
        self.bbox_input.on_submit(self.__set_bbox)
    
    def __set_bbox(self,change):
        bbox = [int(v) for v in self.bbox_input.value.split(',')][:4]  
        img = self.capture_setup(**{**self.capture_settings, 'bbox':bbox})
        self.widgets._push_toast(img.value, timeout=20) # needs enough time to see result

    @contextmanager
    def capture_mode(self, *additional_widgets_to_hide):
        """Hide some widgets and while capturing a screenshot, show them back again.
        You can provide additional widgets to hide while capturing as well."""
        hide_widgets = [self.widgets.controls,
                        self.widgets.buttons.setting,
                        self.widgets.buttons.toc,
                        self.btn_capture,
                        self.widgets.sliders.visible,
                        self.widgets.htmls.toast,
                        self.widgets.htmls.cursor,
                        *additional_widgets_to_hide
                        ]
        old_pref = self.widgets.htmls.toast.layout.visibility # To keep user prefernce back after screenshot
        for w in hide_widgets:
            w.layout.visibility = 'hidden'
        try:  
            self.widgets.mainbox.add_class('CaptureMode') # Used to hide other things on slide  
            self.capturing = True # Must be for main class to know
            yield
        finally:
            self.widgets.mainbox.remove_class('CaptureMode')
            self.capturing = False # Back to normal
            for w in hide_widgets:
                w.layout.visibility = 'visible' 
            self.widgets.htmls.toast.layout.visibility = old_pref 
            
    @property           
    def screen_bbox(self):
        "Return screen's bounding box in pixels."
        img = ImageGrab.grab(bbox=None) # Just to get bounding box
        return (0,0, *img.size)

    def capture_setup(self,load_time=0.5,quality=95,bbox = None):
        """Setting for screen capture. 
        - load_time: 0.5; time in seconds for each slide to load before print, only applied to Capture All, not on manual screenshot. 
        - quality: 95; In term of current screen. Will not chnage too much above 95. 
        - bbox: None; None for full screen on any platform. Given screen position of slides in pixels as [left,top,right,bottom].
        > Note: Auto detection of bbox in frontends where javascript runs is under progress. """
        if load_time < 0.1:
            return print("load_time must be greater than 0.1 to at least load the slide")
        if bbox and len(bbox) != 4:
            return print("bbox expects [left,top,right,bottom] in integers")
        self.__capture_settings = {'load_time':load_time,'quality':quality,'bbox':bbox if bbox else self.screen_bbox} # get full if none given
        # Display what user sets
        if bbox:
            return image(ImageGrab.grab(bbox=bbox),width='100%')

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
            
            # Keep full image if in fullscreen
            bbox = None if "FullScreen" in self.widgets.mainbox._dom_classes else self.capture_settings['bbox']
            self.__images[self.widgets.sliders.progress.label].append(ImageGrab.grab(bbox = bbox)) # Append to existing list
    
    def __sort_images(self):
        ims = [] #sorting
        for label, _ in self.widgets.sliders.progress.options:
            if label in self.__images:
                ims = [*ims,*self.__images[label]]
        return tuple(ims)
            
    def save_pdf(self,filename='IPySlides.pdf'):
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
                self.__images[label] = [ImageGrab.grab(bbox = self.capture_settings['bbox']),] # Save image in a list on which we can add others
        
        self.widgets._push_toast("All slides captured. Use Save PDF/Save PNG buttons to save them.") 
         
    
    @property
    def images(self):
        "Get all captured screenshots in order."
        return self.__sort_images()
    
    def save_images(self,directory = None):
        "Save all screenshots as PNG in given `directory`. Names are auto ordered"
        self.btn_png.description = 'Saving PNGs...'
        if directory is None:
            directory = os.path.join(self.widgets.assets_dir,'images')
        
        if not os.path.isdir(directory):
            os.makedirs(directory)
        
        ims = self.images
        if ims:    
            for i,im in enumerate(ims):
                im.save(os.path.join(directory,f'Slide-{i:03}.png'),'PNG',quality= self.capture_settings['quality'],subsampling=0,optimize=True)  # Do not lose image quality at least here
            md_file = os.path.join(directory,'Make-PPT.md')
            with open(md_file,'w', encoding='utf-8') as f:
                f.write(intro.how_to_ppt)
            self.widgets._push_toast(f'''All captured images are saved in "{directory}"<br/> 
                         <em>See file "{md_file}" as bonus option!</em>''',timeout=10)
        else:
            self.widgets._push_toast('No images found to save. Take screenshots of slides, then use this option.')
        
        self.btn_png.description = 'Save PNG'
        
    def __save_images(self,btn):
        "With Button call"
        self.save_images()
    
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
        On next run, it loads from saved file under `notebook-dir/ipyslides-assets/screenshots`. 
        Useful to add screenshots from system into IPython. You can use overwite to overwrite existing file.
        
        - Output can be directly used in `write` command.
        - Converts to PIL image using `.to_pil()`.
        - Convert to HTML representation using `.to_html()`.
        - Convert to Numpy array using `.to_numpy()` in RGB format that you can plot later.
        """
        directory = os.path.join(self.widgets.assets_dir,'screenshots')
        
        if not os.path.isdir(directory):
            os.makedirs(directory)
        
        filepath = os.path.join(directory,filename)
        
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
        