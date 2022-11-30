
from contextlib import suppress
import time


class Notes:
    "Notes are stored in `LiveSlide` class for consistensy."
    def __init__(self,_insatanceSlides, _instanceWidgets):
        "Instance should be inside `LiveSlide` class."
        # print(f'Inside: {self.__class__.__name__}')
        self.main = _insatanceSlides
        self.widgets = _instanceWidgets
        
        self.notes_check = self.widgets.checks.notes
        self.btn_timer = self.widgets.toggles.timer
        
        self.start_time = None
        
        self.notes_check.observe(self.__open_close_notes, names=['value'])
        self.btn_timer.observe(self.__timeit,names=['value'])
        
    def insert(self, content):
        """Add notes to current slide. Content could be any object except javascript and interactive widgets.
        
        **New in 1.7.2**      
        In markdown, you can use alert`notes\`notes content\``."""
        if not self.main._running_slide:
            raise RuntimeError('Notes can only be added inside a slide constructor.')
        
        with suppress(BaseException): # Would work on next run, may not first time
            self.main._running_slide._notes = self.main.format_html(content)._repr_html_()
    
    def _display(self, html_str):
        self.widgets.htmls.notes.value = 'Notes Area: Time only updates while switching slides' # Must be, so when no notes, should not be there
        if html_str and isinstance(html_str,str):
            current_time = time.localtime()
            if current_time.tm_hour > 12:
                time_str = f'{current_time.tm_hour-12:0>2}:{current_time.tm_min:0>2} PM'
            else:
                time_str = f'{current_time.tm_hour:0>2}:{current_time.tm_min:0>2} AM'
            
            
            if self.start_time:
                spent = time.time() - self.start_time 
                h, sec = divmod(spent,3600) # Houres
                m, _ = divmod(sec,60) # Minutes
                spent_str = f'{int(h):0>2}:{int(m):0>2}' # They are floats by default
            else:
                spent_str = '00:00'

            _time = f'''<div style="border-radius:4px;padding:8px;background:var(--secondary-bg);min-width:max-content;">
                        <h2>Time: {time_str}</h2><hr/>
                        <h3>Elapsed Time: {spent_str}</h3><div>'''
                        
            self.widgets.htmls.notes.value = f'''<div style="margin:-4px;padding:4px;background:var(--secondary-bg);border-radius:4px 4px 0 0;">
                    <b style="font-size:110%;color:var(--accent-color);">Time: {time_str} | Elapsed Time: {spent_str}</b>
                    </div>''' + html_str # show alaways
            
            # Next everything for Browser window case
            if self.notes_check.value:  # Only show on demand
                theme = self.widgets.htmls.theme.value.replace('FullScreen','') #important
                code_theme = '''<style> 
                                pre { display:flex; flex-direction:column; } 
                                .SlideBox { display:flex; flex-direction:row; justify-content:space-between;}
                                .SlideBox > div:first-child { margin:auto; }
                            </style>'''
                node = f'''{theme}<div class="SlidesWrapper"> 
                        <div class="SlideBox"> 
                            <div class="SlideArea"> {code_theme}{html_str} </div> <div>{_time}</div>
                        </div></div>'''
                    

                self.widgets._exec_js(f'''
                    let notes_win = window.open("","__Notes_Window__","popup");
                    notes_win.document.title = 'Notes';
                    notes_win.document.body.innerHTML = {node!r};
                    notes_win.document.body.style.background = 'var(--primary-bg)';
                    ''')
    
    def __open_close_notes(self,change):
        if change['new'] == True:
            self.widgets._exec_js('''
                let notes_win = window.open("","__Notes_Window__","popup");
                notes_win.resizeTo(screen.width/2,screen.height/2);
                notes_win.moveTo(screen.width/4,screen.height*2/5);
                notes_win.document.title = 'Notes';
                notes_win.document.body.innerHTML = "<h1> Notes will show up here, do not close it manually, just navigate away!</h1>";
                ''')
        else:
            self.widgets._exec_js('window.open("","__Notes_Window__","popup").close();')
    
    def __timeit(self,change):
        if change['new'] == True:
            self.btn_timer.icon = 'pause'
            self.start_time = time.time() # Start time here
        else:
            self.btn_timer.icon = 'play'
            self.start_time = None
