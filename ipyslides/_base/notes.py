
from contextlib import suppress

class Notes:
    "Notes are stored in `Slides` class for consistensy."
    def __init__(self,_insatanceSlides, _instanceWidgets):
        "Instance should be inside `Slides` class."
        # print(f'Inside: {self.__class__.__name__}')
        self.main = _insatanceSlides
        self.widgets = _instanceWidgets
        self.notes_check = self.widgets.checks.notes
        self.notes_check.observe(self.__open_close_notes, names=['value'])
        
    def insert(self, content):
        """Add notes to current slide. Content could be any object except javascript and interactive widgets.
        ::: note-tip     
            In markdown, you can use alert`notes\`notes content\``."""
        if self.main.running is None:
            raise RuntimeError('Notes can only be added inside a slide constructor.')
        
        with suppress(BaseException): # Would work on next run, may not first
            self.main.running._notes = self.main.format_html(content)._repr_html_()
    __call__ = insert # Can be called as function
    
    def _display(self, html_str):
        self.widgets.htmls.notes.value = 'Notes Preview' # Must be, so when no notes, should not be there
        if html_str and isinstance(html_str,str):            
            self.widgets.htmls.notes.value = html_str # show alaways inline
            
            # Next everything for Browser window case
            if self.notes_check.value:  # Only show on demand
                theme = self.widgets.htmls.theme.value.replace('FullWindow','') #important
                code_theme = '''<style> 
                                pre { display:flex; flex-direction:column; } 
                                .SlideBox { display:flex; flex-direction:row; justify-content:space-between;}
                                .SlideBox > div:first-child { margin:auto; }
                            </style>'''
                node = f'''{theme}<div class="SlidesWrapper"> 
                        <div class="SlideBox"> 
                            <div class="SlideArea"> {code_theme}{html_str} </div>
                        </div></div>'''
                    

                self.widgets._exec_js(f'''
                    let notes_win = window.open("","__Notes_Window__","popup");
                    notes_win.document.title = 'Notes';
                    notes_win.document.body.innerHTML = {node!r};
                    notes_win.document.body.style.background = 'var(--primary-bg)';
                    window.focus(); // Return focus to main window automatically
                    
                    setTimeout(() => {{
                        notes_win.document.body.innerHTML = '<h2 style="color:#D44;background:#444;"> Notes will show up here, do not close it manually, just navigate away!</h2>';
                    }}, 30000); // Close after 1/2 minute, so it should not mislead user on other slides, 1/2 minute is enough to read notes
                    ''')
    
    def __open_close_notes(self,change):
        if change['new'] == True:
            self.widgets._exec_js('''
                let notes_win = window.open("","__Notes_Window__","popup");
                notes_win.resizeTo(screen.width/2,screen.height/2);
                notes_win.moveTo(screen.width/4,screen.height*2/5);
                notes_win.document.title = 'Notes';
                notes_win.document.body.innerHTML = "<h2 style="color:#D44;background:#444;"> Notes will show up here, do not close it manually, just navigate away!</h2>";
                ''')
        else:
            self.widgets._exec_js('window.open("","__Notes_Window__","popup").close();')
